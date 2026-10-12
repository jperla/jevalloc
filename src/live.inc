/* Published/sample counters use relaxed atomics; allocation counters are private.
 * Sharded sampled-pointer records support cross-thread frees.
 * Unsampled allocations update only a thread-owned shard; merge every 4096 successes.
 * Socket I/O happens outside the statistics lock. One in-flight decision per site. */
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/resource.h>
#include <poll.h>
#include <fcntl.h>
#include <time.h>
#include <sched.h>
#include "hybrid.h"
#define COHORT_SIZE 128
typedef struct CohortEntry {uint64_t birth,size,serial;bool freed;} CohortEntry;
typedef struct LiveSite {
 uint64_t key,site_key,signature; char context[256];
 _Atomic uint64_t next_check;
 _Atomic unsigned cls,answers; bool deciding;
 _Alignas(128) _Atomic uint64_t allocs,bytes;
 _Alignas(128) _Atomic uint64_t frees,sampled_bytes,short_freed,hist[65];
 atomic_flag cohort_lock;
 uint64_t cohort_seen,hybrid_bytes,hybrid_freed_bytes,hybrid_frees;
 double prior_transient; bool has_prior;
 unsigned hybrid_promotions,hybrid_demotions;
 CohortEntry cohort[COHORT_SIZE];
 Frame frames[MAX_DEPTH]; unsigned nf;
 struct LiveSite* next;
} LiveSite;
typedef struct LiveShard {
 /* Only the owning thread reads/writes these counters. Cross-thread reporting
  * reads the published LiveSite totals, never these unmerged values. */
 _Alignas(128) uint64_t allocs,bytes,merged_allocs,merged_bytes;
 unsigned until_sample,sample_mask;
 _Atomic unsigned cls;
 uint64_t check_at,byte_check_at;
 LiveSite* site;
 _Atomic uint64_t sample_count,sample_bytes;
 _Alignas(128) _Atomic uint64_t refs,freed_bytes,frees,short_freed,hist[65];
 struct LiveShard *next,*global_next,*hash_next;
} LiveShard;
static LiveShard* all_shards;
typedef struct Sample {void* p;uint64_t birth,size;LiveShard* owner;struct Sample* next;uint64_t serial;unsigned slot;} Sample;
static LiveSite* live_sites[16384];
static Sample* samples[65536];
static atomic_uint sample_buckets[65536];
/* A spatial negative filter keeps unsampled frees away from the pointer table.
 * Sixteen 4-bit reference counts per 64 KiB address region (hashed). Saturated
 * nibbles stay positive forever: collisions/overflow can only add slow probes,
 * never lose a sample. Only sampled allocations/frees write this table. */
static _Atomic uint64_t sample_filter[65536];
_Static_assert(sizeof(void*)==8,"page-local sample filter requires a 64-bit target");
static unsigned filter_mode=2; /* 0: off, 1: spatial, 2: page-local */
static inline size_t filter_index(void* p){return (((uintptr_t)p>>16)^((uintptr_t)p>>32))&65535;}
static inline unsigned filter_shift(void* p){return (unsigned)((((uintptr_t)p>>4)^((uintptr_t)p>>9))&15)*4;}
/* mimalloc 2.2.4 reserves padding[0] in every page. It is unused by the
 * allocator and is cleared with the page after its last block is freed. Keep
 * the counting filter there so unsampled frees read page metadata they already
 * need, rather than a second global cache line. The page layout is unchanged.
 * GNU pointer atomics preserve the declared storage type; encoded bits are never
 * dereferenced. Retired/abandoned pages retain the filter with their live blocks. */
static inline bool filter_maybe_sampled_page(void* p,mi_page_t* page) {
 if(!filter_mode)return true;
 uintptr_t bits=filter_mode==2?(uintptr_t)__atomic_load_n(&page->padding[0],__ATOMIC_RELAXED):atomic_load_explicit(&sample_filter[filter_index(p)],memory_order_relaxed);
 return (bits>>filter_shift(p))&15;
}
static inline bool filter_maybe_sampled(void* p){return filter_maybe_sampled_page(p,filter_mode==2?_mi_ptr_page(p):NULL);}
static void filter_update(void* p,bool add) {
 unsigned shift=filter_shift(p);
 if(filter_mode==2) {
  void** word=&_mi_ptr_page(p)->padding[0];void* old=__atomic_load_n(word,__ATOMIC_RELAXED);
  for(;;){uintptr_t bits=(uintptr_t)old;unsigned count=(unsigned)((bits>>shift)&15);if(count==15)return;
   if(!add&&!count)abort();void* next=(void*)(add?bits+(UINT64_C(1)<<shift):bits-(UINT64_C(1)<<shift));
   if(__atomic_compare_exchange_n(word,&old,next,true,__ATOMIC_RELAXED,__ATOMIC_RELAXED))return;
  }
 }
 _Atomic uint64_t* word=&sample_filter[filter_index(p)];uint64_t old=atomic_load_explicit(word,memory_order_relaxed);
 for(;;){unsigned count=(unsigned)((old>>shift)&15);if(count==15)return;
  if(!add&&!count)abort();uint64_t next=add?old+(UINT64_C(1)<<shift):old-(UINT64_C(1)<<shift);
  if(atomic_compare_exchange_weak_explicit(word,&old,next,memory_order_relaxed,memory_order_relaxed))return;
 }
}
static struct { _Alignas(64) atomic_uint lock; Sample* pool; } sample_mutex[64];
static inline void sample_lock(size_t h) {
 atomic_uint* lock=&sample_mutex[h&63].lock;unsigned spins=0;
 for(;;) {
  unsigned expected=0;
  if(atomic_compare_exchange_weak_explicit(lock,&expected,1,memory_order_acquire,memory_order_relaxed))return;
  while(atomic_load_explicit(lock,memory_order_relaxed)) {
#if defined(__x86_64__)
   __asm__ volatile("pause");
#elif defined(__aarch64__)
   __asm__ volatile("yield");
#endif
   if(++spins==1024){sched_yield();spins=0;}
  }
 }
}
static inline void sample_unlock(size_t h){atomic_store_explicit(&sample_mutex[h&63].lock,0,memory_order_release);}
#define GET(x) atomic_load_explicit(&(x),memory_order_relaxed)
#define ADD(x,n) atomic_fetch_add_explicit(&(x),(n),memory_order_relaxed)
static pthread_mutex_t live_mutex=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t live_condition=PTHREAD_COND_INITIALIZER;
static struct { _Alignas(128) _Atomic uint64_t bytes; char pad[120]; } clock_sharing;
#define live_clock clock_sharing.bytes
static _Alignas(128) _Atomic uint64_t sampled_count;
static uint64_t live_site_count,blocked_ns,decisions,rechecks,timeouts,failures;
static int last_failure_errno;
static unsigned sample_rate=64,timeout_ms=30000;
static bool hybrid_mode;
static atomic_bool per_alloc_mode;
static uint64_t min_site_bytes=65536;
static _Alignas(128) atomic_bool circuit_open,live_closed;
static const char* socket_path;
static char socket_path_copy[sizeof(((struct sockaddr_un*)0)->sun_path)];
static uint64_t nanos(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static uint64_t quant(uint64_t n) {return n?UINT64_C(1)<<(63-__builtin_clzll(n)):0;}
static void live_init(void) {
 per_alloc_mode=getenv("JEVALLOC_PER_ALLOC") && !strcmp(getenv("JEVALLOC_PER_ALLOC"),"1");
 hybrid_mode=getenv("JEVALLOC_HYBRID") && !strcmp(getenv("JEVALLOC_HYBRID"),"1");
 for(unsigned i=0;i<64;i++)atomic_init(&sample_mutex[i].lock,0);
 const char* minimum=getenv("JEVALLOC_MIN_SITE_BYTES");if(minimum)min_site_bytes=strtoull(minimum,NULL,10);
 const char* s=getenv("JEVALLOC_SAMPLE");if(s){long n=strtol(s,NULL,10);if(n>0&&n<=1048576)sample_rate=(unsigned)n;}
 s=getenv("JEVALLOC_TIMEOUT_MS");if(s){long n=strtol(s,NULL,10);if(n>0&&n<=3600000)timeout_ms=(unsigned)n;}
 const char* filter=getenv("JEVALLOC_SAMPLE_FILTER");if(filter)filter_mode=*filter=='0'?0:!strcmp(filter,"spatial")?1:2;
 socket_path=getenv("JEVALLOC_SOCKET");
 /* Applications such as Redis relocate/overwrite environ for setproctitle. */
 if(socket_path){if(strlen(socket_path)>=sizeof(socket_path_copy))abort();strcpy(socket_path_copy,socket_path);socket_path=socket_path_copy;}
}
static int socket_wait(int fd,short events,uint64_t deadline) {
 for(;;){uint64_t now=nanos();if(now>=deadline){errno=ETIMEDOUT;return -1;}
  int ms=(int)((deadline-now+999999)/1000000);struct pollfd p={fd,events,0};
  int r=poll(&p,1,ms);if(r<0&&errno==EINTR)continue;if(r==0){errno=ETIMEDOUT;return -1;}if(r<0)return -1;
  if(p.revents&events)return 0;errno=ECONNRESET;return -1;
 }
}
static int exchange(const char* request,unsigned* cls,uint64_t* after,double* prior) {
 if(!socket_path){errno=ENOENT;return -1;}
 struct sockaddr_un address={0};address.sun_family=AF_UNIX;
 if(strlen(socket_path)>=sizeof(address.sun_path)){errno=ENAMETOOLONG;return -1;}
 strcpy(address.sun_path,socket_path);
 int fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0)return -1;
 fcntl(fd,F_SETFD,FD_CLOEXEC);fcntl(fd,F_SETFL,O_NONBLOCK);
#ifdef __APPLE__
 int one=1;setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&one,sizeof(one));
#endif
 uint64_t deadline=nanos()+(uint64_t)timeout_ms*1000000;int rc=-1;
 if(connect(fd,(struct sockaddr*)&address,sizeof(address))<0){
  if(errno!=EINPROGRESS||socket_wait(fd,POLLOUT,deadline))goto done;
  int err=0;socklen_t len=sizeof(err);if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&err,&len)||err){if(err)errno=err;goto done;}
 }
 size_t length=strlen(request),sent=0;
 while(sent<length){if(socket_wait(fd,POLLOUT,deadline))goto done;
#ifdef MSG_NOSIGNAL
  ssize_t n=send(fd,request+sent,length-sent,MSG_NOSIGNAL);
#else
  ssize_t n=send(fd,request+sent,length-sent,0);
#endif
  if(n<0&&(errno==EAGAIN||errno==EINTR))continue;if(n<=0)goto done;sent+=(size_t)n;
 }
 char reply[1024];size_t used=0;
 while(used<sizeof(reply)-1){if(socket_wait(fd,POLLIN,deadline))goto done;ssize_t n=recv(fd,reply+used,sizeof(reply)-1-used,0);
  if(n<0&&(errno==EAGAIN||errno==EINTR))continue;if(n<=0)goto done;used+=(size_t)n;reply[used]=0;if(strchr(reply,'\n'))break;
 }
 char *c=strstr(reply,"\"class\""),*a=strstr(reply,"\"recheck_after\"");
 unsigned v;unsigned long long interval;
 if(!c||!a||sscanf(c,"\"class\" : %u",&v)!=1||v>1||sscanf(a,"\"recheck_after\" : %llu",&interval)!=1){errno=EPROTO;goto done;}
 *cls=v;*after=interval;
 char* each=strstr(reply,"\"per_allocation\"");unsigned every=0;
 if(each && sscanf(each,"\"per_allocation\" : %u",&every)==1 && every)per_alloc_mode=true;
 char* prob=strstr(reply,"\"prior_transient\"");
 if(prob && sscanf(prob,"\"prior_transient\" : %lf",prior)!=1){errno=EPROTO;goto done;}
 if(*prior < -1 || *prior > 1){errno=EPROTO;goto done;}
 rc=0;
 done: {int err=errno;close(fd);errno=err;}return rc;
}
typedef struct LiveTotals {uint64_t frees,sampled_live,sampled_bytes,sampled_live_bytes,short_freed,hist[65],clock,estimate,samples,alive;} LiveTotals;
/* Called with live_mutex: retired owners with outstanding cross-thread objects
 * stay registered. The inspected counters are atomic for concurrent sampled frees. */
/* Allocation-owned totals need stores only. Derive survivors from successful
 * samples minus frees instead of two RMW pairs on every sampled object's path.
 * Concurrent snapshots are approximate, so guard subtraction against skew. */
static uint64_t live_survivors(LiveShard* sh){uint64_t all=GET(sh->sample_count),freed=GET(sh->frees);return all>freed?all-freed:0;}
static uint64_t live_surviving_bytes(LiveShard* sh){uint64_t all=GET(sh->sample_bytes),freed=GET(sh->freed_bytes);return all>freed?all-freed:0;}
static LiveTotals live_totals(LiveSite* site) {
 LiveTotals t={0};t.clock=GET(live_clock);t.samples=GET(sampled_count);
 if(site){t.short_freed=GET(site->short_freed);t.frees=GET(site->frees);t.sampled_bytes=GET(site->sampled_bytes);for(unsigned i=0;i<65;i++)t.hist[i]=GET(site->hist[i]);}
 for(LiveShard* sh=all_shards;sh;sh=sh->global_next) {
  t.alive+=live_survivors(sh);t.estimate+=live_surviving_bytes(sh)*sample_rate;t.samples+=GET(sh->sample_count);
  if(sh->site==site){t.short_freed+=GET(sh->short_freed);t.frees+=GET(sh->frees);t.sampled_live+=live_survivors(sh);t.sampled_bytes+=GET(sh->sample_bytes);t.sampled_live_bytes+=live_surviving_bytes(sh);for(unsigned i=0;i<65;i++)t.hist[i]+=GET(sh->hist[i]);}
 }
 return t;
}
/* Reservoir spans the observed history rather than just recent allocations.
 * Freed entries retain their birth so selection is independent of survival. */
static void cohort_lock(LiveSite* s){while(atomic_flag_test_and_set_explicit(&s->cohort_lock,memory_order_acquire))sched_yield();}
static void cohort_unlock(LiveSite* s){atomic_flag_clear_explicit(&s->cohort_lock,memory_order_release);}
/* Called with cohort_lock. Exact lifetime sample totals, including evicted and
 * freed reservoir entries, survive thread retirement. No writes on unsampled paths. */
static void hybrid_update_locked(LiveSite* s,uint64_t now) {
 if(!hybrid_mode || !s->has_prior)return;
 uint64_t oldest=0;
 unsigned count=s->cohort_seen<COHORT_SIZE?s->cohort_seen:COHORT_SIZE;
 for(unsigned i=0;i<count;i++)if(!s->cohort[i].freed && now>=s->cohort[i].birth && now-s->cohort[i].birth>oldest)oldest=now-s->cohort[i].birth;
 unsigned before=GET(s->cls);
 unsigned after=hybrid_class(before,s->prior_transient,s->cohort_seen,s->hybrid_bytes,s->hybrid_freed_bytes,s->hybrid_frees,oldest,now);
 if(before!=after){if(after)s->hybrid_promotions++;else s->hybrid_demotions++;atomic_store_explicit(&s->cls,after,memory_order_relaxed);}
}
static int cohort_birth_compare(const void* a,const void* b){uint64_t x=((const CohortEntry*)a)->birth,y=((const CohortEntry*)b)->birth;return (x>y)-(x<y);}
static void cohort_stats(LiveSite* s,uint64_t* bytes,uint64_t* freed,unsigned* count,uint64_t now,uint64_t* oldest) {
 CohortEntry copy[COHORT_SIZE];cohort_lock(s);
 *count=s->cohort_seen<COHORT_SIZE?(unsigned)s->cohort_seen:COHORT_SIZE;
 memcpy(copy,s->cohort,*count*sizeof(*copy));cohort_unlock(s);
 qsort(copy,*count,sizeof(*copy),cohort_birth_compare);*bytes=0;*freed=0;
 *oldest=0;
 for(unsigned i=0;i<*count;i++)if(!copy[i].freed && now>=copy[i].birth && now-copy[i].birth>*oldest)*oldest=now-copy[i].birth;
 if(*count<16)return;
 /* Strictly older than the count median age = strictly earlier birth. */
 uint64_t median=copy[*count/2].birth;
 for(unsigned i=0;i<*count;i++)if(copy[i].birth<median){*bytes+=copy[i].size;if(copy[i].freed)*freed+=copy[i].size;}
}
static char* live_request(LiveSite* s,size_t size,Frame* frames,unsigned nf) {
 LiveTotals totals=live_totals(s);
 uint64_t older_bytes,older_freed,oldest;unsigned cohort_count;cohort_stats(s,&older_bytes,&older_freed,&cohort_count,totals.clock,&oldest);
 /* Concurrent sampled allocations/frees can straddle this approximate snapshot.
  * Bound the partition before subtraction; never emit wrapped percentages. */
 if(totals.sampled_live_bytes>totals.sampled_bytes)totals.sampled_live_bytes=totals.sampled_bytes;
 uint64_t freed=totals.sampled_bytes-totals.sampled_live_bytes;
 if(totals.short_freed>freed)totals.short_freed=freed;
 char* text=NULL;size_t length=0;FILE* f=open_memstream(&text,&length);if(!f)abort();
 fprintf(f,"{\"op\":\"decide\",\"key\":\"%016llx\",\"program\":",(unsigned long long)s->key);
#ifdef __APPLE__
 json_string(f,getprogname());
#else
 extern char* program_invocation_short_name;json_string(f,program_invocation_short_name);
#endif
 fprintf(f,",\"site_key\":\"%016llx\",\"context_signature\":\"%016llx\",\"context\":",(unsigned long long)s->site_key,(unsigned long long)s->signature);json_string(f,s->context);
 if(per_alloc_mode)fputs(",\"per_alloc\":true",f);
 fputs(",\"frames\":[",f);
 for(unsigned i=0;i<nf;i++){fprintf(f,"%s{\"addr\":\"0x%llx\",\"image\":",i?",":"",(unsigned long long)frames[i].addr);json_string(f,images[frames[i].image].path);fputc('}',f);}
 fprintf(f,"],\"size\":%zu,\"site\":{\"allocs\":%llu,\"frees\":%llu,\"live\":%llu,\"bytes\":%llu,\"life_hist\":[",size,(unsigned long long)quant(s->allocs),(unsigned long long)quant(totals.frees*sample_rate),(unsigned long long)quant(totals.sampled_live*sample_rate),(unsigned long long)quant(s->bytes));
 uint64_t total=0;for(unsigned i=0;i<65;i++)total+=totals.hist[i];
 for(unsigned i=0;i<65;i++)fprintf(f,"%s%llu",i?",":"",(unsigned long long)(total?quant((uint64_t)((long double)totals.hist[i]*65536/total)):0));
 fprintf(f,"],\"sampled_bytes\":%llu,\"sampled_live_bytes\":%llu",(unsigned long long)quant(totals.sampled_bytes),(unsigned long long)quant(totals.sampled_live_bytes));
 fprintf(f,",\"short_share\":%u,\"long_freed_share\":%u,\"alive_share\":%u,\"short_bytes\":%llu",totals.sampled_bytes?(unsigned)(100* (long double)totals.short_freed/totals.sampled_bytes):0,totals.sampled_bytes?(unsigned)(100*(long double)(totals.sampled_bytes-totals.sampled_live_bytes-totals.short_freed)/totals.sampled_bytes):0,totals.sampled_bytes?(unsigned)(100*(long double)totals.sampled_live_bytes/totals.sampled_bytes):0,(unsigned long long)short_bytes);
 fprintf(f,",\"cohort_count\":%u,\"older_sampled_bytes\":%llu,\"older_freed_bytes\":%llu",cohort_count,(unsigned long long)older_bytes,(unsigned long long)older_freed);
 fprintf(f,",\"oldest_age_bytes\":%llu,\"eligible_bytes\":%llu",(unsigned long long)oldest,(unsigned long long)GET(s->bytes));
 size_t rss=0,commit=0;mi_process_info(NULL,NULL,NULL,&rss,NULL,&commit,NULL,NULL);
 /* Upstream signed commit accounting can transiently be negative; zero means unavailable. */
 if(commit>PTRDIFF_MAX)commit=0;if(rss>PTRDIFF_MAX)rss=0;
 unsigned threads=1;
#ifndef __APPLE__
 FILE* status=fopen("/proc/self/status","r");if(status){char line[256];while(fgets(line,sizeof(line),status))if(sscanf(line,"Threads: %u",&threads)==1)break;fclose(status);}
#endif
 fprintf(f," },\"process\":{\"alloc_clock\":%llu,\"live_bytes\":%llu,\"committed\":%llu,\"rss\":%llu,\"threads\":%llu,\"sites\":%llu},\"prior\":",(unsigned long long)totals.clock,(unsigned long long)quant(totals.estimate),(unsigned long long)quant(commit),(unsigned long long)quant(rss),(unsigned long long)quant(threads),(unsigned long long)quant(live_site_count));
 if(s->answers)fprintf(f,"%u",s->cls);else fputs("null",f);fputs("}\n",f);fclose(f);return text;
}
static void live_merge(LiveShard* shard) {
 uint64_t a=shard->allocs,b=shard->bytes;
 if(a!=shard->merged_allocs)ADD(shard->site->allocs,a-shard->merged_allocs);
 if(b!=shard->merged_bytes)ADD(shard->site->bytes,b-shard->merged_bytes);
 shard->merged_allocs=a;shard->merged_bytes=b;
}
static uint64_t live_now(void) {return GET(live_clock)+context()->clock_pending;}
static void live_clock_merge(Thread* t) {
 if(t->clock_pending){ADD(live_clock,t->clock_pending);t->clock_pending=0;}
}
static void live_release_shard(LiveShard* sh) {
 if(ADD(sh->refs,-1)!=1)return;
 pthread_mutex_lock(&live_mutex);
 atomic_store_explicit(&sh->site->short_freed,GET(sh->site->short_freed)+GET(sh->short_freed),memory_order_relaxed);
 atomic_store_explicit(&sh->site->frees,GET(sh->site->frees)+GET(sh->frees),memory_order_relaxed);
 atomic_store_explicit(&sh->site->sampled_bytes,GET(sh->site->sampled_bytes)+GET(sh->sample_bytes),memory_order_relaxed);
 atomic_store_explicit(&sampled_count,GET(sampled_count)+GET(sh->sample_count),memory_order_relaxed);
 for(unsigned i=0;i<65;i++){uint64_t bytes=GET(sh->hist[i]);if(bytes)atomic_store_explicit(&sh->site->hist[i],GET(sh->site->hist[i])+bytes,memory_order_relaxed);}
 LiveShard** pp=&all_shards;while(*pp&&*pp!=sh)pp=&(*pp)->global_next;
 if(*pp)*pp=sh->global_next;
 pthread_mutex_unlock(&live_mutex);mi_free(sh);
}
static void live_thread_finish(Thread* t) {
 for(LiveShard* sh=t->live_shards;sh;) {
  live_merge(sh);LiveShard* next=sh->next;live_release_shard(sh);sh=next;
 }
 t->live_shards=NULL;mi_free(t->live_index);t->live_index=NULL;live_clock_merge(t);
}
static LiveShard* live_before_slow(KeyCache* cached,size_t n,unsigned* cls) {
 unsigned individual=default_class;
 uint64_t key=cached->key;Frame* frames=cached->frames;unsigned nf=cached->nf;
 context()->allocation_decided=false;
 if(GET(live_closed)){*cls=default_class;return NULL;}
 LiveShard* shard=cached->live_site;
 if(!shard){
  /* A raw-cache collision must not scan every site seen by this thread. */
  if(!context()->live_index)context()->live_index=metadata(512*sizeof(LiveShard*));
  LiveShard** bucket=&((LiveShard**)context()->live_index)[mix(key)&511];
  for(shard=*bucket;shard&&shard->site->key!=key;shard=shard->hash_next){}
  if(!shard) {
   pthread_mutex_lock(&live_mutex);
   size_t h=mix(key)&16383;LiveSite* site=live_sites[h];while(site&&site->key!=key)site=site->next;
   if(!site){site=mi_zalloc_aligned(sizeof(*site),128);if(!site)abort();atomic_flag_clear(&site->cohort_lock);site->key=key;site->site_key=cached->site_key;site->signature=cached->signature;if(site->signature)memcpy(site->context,context()->request_context,256);site->nf=nf;memcpy(site->frames,frames,nf*sizeof(Frame));site->cls=default_class;site->next=live_sites[h];live_sites[h]=site;live_site_count++;}
   shard=mi_zalloc_aligned(sizeof(*shard),128);if(!shard)abort();shard->site=site;shard->cls=GET(site->cls);shard->refs=1;shard->until_sample=sample_rate;
   shard->sample_mask=(sample_rate&(sample_rate-1))?UINT32_MAX:sample_rate-1;
   shard->next=context()->live_shards;context()->live_shards=shard;
   shard->hash_next=*bucket;*bucket=shard;
   shard->global_next=all_shards;all_shards=shard;
   pthread_mutex_unlock(&live_mutex);
  }
  cached->live_site=shard;
 }
 LiveSite* s=shard->site;
 uint64_t local=shard->allocs;
 uint64_t count=GET(s->allocs)+shard->allocs-shard->merged_allocs;
 uint64_t next=GET(s->next_check);
 bool eligible=GET(s->bytes)+shard->bytes-shard->merged_bytes>=min_site_bytes;
 if(eligible && !GET(circuit_open) && (per_alloc_mode || !atomic_load_explicit(&s->answers,memory_order_acquire) || (next&&count>=next))){
  pthread_mutex_lock(&live_mutex);
  while(s->deciding){uint64_t begin=nanos();pthread_cond_wait(&live_condition,&live_mutex);blocked_ns+=nanos()-begin;}
  next=GET(s->next_check);
  if(!GET(circuit_open) && (per_alloc_mode || !atomic_load_explicit(&s->answers,memory_order_acquire) || (next&&count>=next))){
   live_merge(shard);live_clock_merge(context());
   s->deciding=true;char* request=live_request(s,n,s->frames,s->nf);unsigned answer=default_class;uint64_t after=0;
   double prior=-1;uint64_t decision_count=GET(s->allocs);
   if(GET(s->answers))rechecks++;decisions++;
   pthread_mutex_unlock(&live_mutex);uint64_t begin=nanos();int rc=exchange(request,&answer,&after,&prior);int error=errno;uint64_t elapsed=nanos()-begin;free(request);
   pthread_mutex_lock(&live_mutex);blocked_ns+=elapsed;
   if(rc){last_failure_errno=error;failures++;if(error==ETIMEDOUT)timeouts++;circuit_open=true;}
   individual=answer;context()->allocation_decided=!rc;context()->decision_ordinal=GET(s->answers);
   s->cls=answer;
   if(hybrid_mode && prior>=0){cohort_lock(s);s->prior_transient=prior;s->has_prior=true;hybrid_update_locked(s,GET(live_clock));cohort_unlock(s);}
   /* Publish infrequent policy changes to attached owners. Allocations then read
    * a class on their local counter line, without dependent shared-site loads. */
   for(LiveShard* sh=all_shards;sh;sh=sh->global_next)if(sh->site==s)atomic_store_explicit(&sh->cls,answer,memory_order_relaxed);
   s->next_check=after&&after<UINT64_MAX-decision_count?decision_count+after:0;
   atomic_fetch_add_explicit(&s->answers,1,memory_order_release);s->deciding=false;pthread_cond_broadcast(&live_condition);
  }
  pthread_mutex_unlock(&live_mutex);
 }
 next=GET(s->next_check);
 uint64_t remaining=next>count?next-count:64;
 if(!GET(s->answers)) {
  uint64_t bytes=GET(s->bytes)+shard->bytes-shard->merged_bytes;
  shard->check_at=local+64;
  shard->byte_check_at=shard->bytes+(bytes<min_site_bytes?min_site_bytes-bytes:0);
 } else {
  shard->check_at=next?local+(remaining<64?remaining:64):UINT64_MAX;
  shard->byte_check_at=UINT64_MAX;
 }
 *cls=per_alloc_mode&&context()->allocation_decided?individual:GET(s->cls);return shard;
}
static inline __attribute__((always_inline)) LiveShard* live_before(KeyCache* cached,size_t n,unsigned* cls) {
 LiveShard* shard=cached->live_site;
 if(!per_alloc_mode&&!GET(live_closed)&&shard&&shard->allocs<shard->check_at&&shard->bytes<shard->byte_check_at){*cls=hybrid_mode?GET(shard->site->cls):GET(shard->cls);return shard;}
 return live_before_slow(cached,n,cls);
}
/* Multiplicative hashing uses the high bits of the product, so aligned size
 * classes spread across lock shards without two rounds of integer mixing. */
static inline size_t sample_hash(const void* p){return (((uintptr_t)p>>3)*UINT64_C(0x9e3779b97f4a7c15))>>48;}
static void live_sample(void* p,size_t n,LiveShard* shard) {
 size_t h=sample_hash(p);
 sample_lock(h);
 Sample* record=sample_mutex[h&63].pool;
 if(record)sample_mutex[h&63].pool=record->next;else record=metadata(sizeof(*record));
 if(filter_mode)filter_update(p,true);
 *record=(Sample){.p=p,.birth=live_now(),.size=n,.owner=shard,.next=samples[h],.slot=COHORT_SIZE};
 LiveSite* site=shard->site;cohort_lock(site);record->serial=++site->cohort_seen;
 uint64_t slot=record->serial<=COHORT_SIZE?record->serial-1:mix(record->serial^site->key)%record->serial;
 if(slot<COHORT_SIZE){record->slot=(unsigned)slot;site->cohort[slot]=(CohortEntry){record->birth,n,record->serial,false};}
 site->hybrid_bytes+=n;hybrid_update_locked(site,record->birth);
 cohort_unlock(site);samples[h]=record;atomic_store_explicit(&sample_buckets[h],GET(sample_buckets[h])+1,memory_order_relaxed);ADD(shard->refs,1);atomic_store_explicit(&shard->sample_bytes,GET(shard->sample_bytes)+n,memory_order_relaxed);atomic_store_explicit(&shard->sample_count,GET(shard->sample_count)+1,memory_order_relaxed);
 sample_unlock(h);
}
static inline __attribute__((always_inline)) void live_alloc(void* p,size_t n,LiveShard* shard) {
 /* live_before admitted this allocation while open. Its owner reference stays
  * alive across the raw allocation even if the exit snapshot starts meanwhile. */
 if(!shard)return;
 uint64_t count=++shard->allocs;
 shard->bytes+=n;
 context()->clock_pending+=n;
 if(__builtin_expect(count%4096==0,0)){live_merge(shard);live_clock_merge(context());}
 if(__builtin_expect(shard->sample_mask!=UINT32_MAX,1)) {
  if(__builtin_expect((count&shard->sample_mask)==0,0))live_sample(p,n,shard);
 } else if(__builtin_expect(--shard->until_sample==0,0)){shard->until_sample=sample_rate;live_sample(p,n,shard);}
}
static __attribute__((noinline)) void live_free_sample(void* p,size_t h) {
 busy++;
 sample_lock(h);Sample** pp=&samples[h];while(*pp&&(*pp)->p!=p)pp=&(*pp)->next;
 Sample* r=*pp;LiveShard* owner=r?r->owner:NULL;
 if(r){if(filter_mode)filter_update(p,false);*pp=r->next;atomic_store_explicit(&sample_buckets[h],GET(sample_buckets[h])-1,memory_order_relaxed);uint64_t now=live_now();uint64_t life=now>=r->birth?now-r->birth:0;unsigned bucket=life?64-__builtin_clzll(life):0;ADD(owner->hist[bucket],r->size);if(life<short_bytes)ADD(owner->short_freed,r->size);ADD(owner->frees,1);ADD(owner->freed_bytes,r->size);}
 if(r){LiveSite* site=owner->site;cohort_lock(site);site->hybrid_frees++;site->hybrid_freed_bytes+=r->size;if(r->slot<COHORT_SIZE && site->cohort[r->slot].serial==r->serial)site->cohort[r->slot].freed=true;hybrid_update_locked(site,live_now());cohort_unlock(site);}
 if(r){r->next=sample_mutex[h&63].pool;sample_mutex[h&63].pool=r;}sample_unlock(h);if(owner)live_release_shard(owner);busy--;
}
static inline __attribute__((always_inline)) void live_free(void* p) {
 if(!filter_maybe_sampled(p))return;
 size_t h=sample_hash(p);
 if(GET(sample_buckets[h]))live_free_sample(p,h);
}
static void live_finish(void) {
 live_thread_finish(context());
 pthread_mutex_lock(&live_mutex);live_closed=true;const char* path=getenv("JEVALLOC_STATS_OUT");if(!path)path="jevalloc-stats.json";FILE* f=fopen(path,"w");
 if(f){LiveTotals totals=live_totals(NULL);uint64_t total_bytes=0;fputs("{\"site_bytes\":{",f);bool first=true;
  for(unsigned h=0;h<16384;h++)for(LiveSite* s=live_sites[h];s;s=s->next){uint64_t bytes=GET(s->bytes);total_bytes+=bytes;fprintf(f,"%s\"%016llx\":%llu",first?"":",",(unsigned long long)s->key,(unsigned long long)bytes);first=false;}
  fputs("},\"hybrid_sites\":{",f);first=true;
  if(hybrid_mode)for(unsigned h=0;h<16384;h++)for(LiveSite* s=live_sites[h];s;s=s->next){cohort_lock(s);if(s->has_prior){fprintf(f,"%s\"%016llx\":{\"prior_transient\":%.17g,\"class\":%u,\"promotions\":%u,\"demotions\":%u,\"samples\":%llu,\"sampled_bytes\":%llu,\"freed_bytes\":%llu}",first?"":",",(unsigned long long)s->key,s->prior_transient,GET(s->cls),s->hybrid_promotions,s->hybrid_demotions,(unsigned long long)s->cohort_seen,(unsigned long long)s->hybrid_bytes,(unsigned long long)s->hybrid_freed_bytes);first=false;}cohort_unlock(s);}
  fputs("},\"site_sampled_live\":{",f);first=true;
  for(unsigned h=0;h<16384;h++)for(LiveSite* s=live_sites[h];s;s=s->next){uint64_t alive=0;for(LiveShard* sh=all_shards;sh;sh=sh->global_next)if(sh->site==s)alive+=live_survivors(sh);fprintf(f,"%s\"%016llx\":%llu",first?"":",",(unsigned long long)s->key,(unsigned long long)alive);first=false;}
  fprintf(f,"},\"failure_errno\":%d",last_failure_errno);
  fprintf(f,",\"blocked_ns\":%llu,\"decisions\":%llu,\"rechecks\":%llu,\"timeouts\":%llu,\"failures\":%llu,\"sites\":%llu,\"samples\":%llu,\"sampled_live_objects\":%llu,\"sample_rate\":%u,\"allocation_clock\":%llu}\n",(unsigned long long)blocked_ns,(unsigned long long)decisions,(unsigned long long)rechecks,(unsigned long long)timeouts,(unsigned long long)failures,(unsigned long long)live_site_count,(unsigned long long)totals.samples,(unsigned long long)totals.alive,sample_rate,(unsigned long long)total_bytes);fclose(f);}
 pthread_mutex_unlock(&live_mutex);
}
