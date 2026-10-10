/* Live counters use relaxed atomics; sharded sampled-pointer records support cross-thread frees.
 * Socket I/O happens outside the statistics lock. One in-flight decision per site. */
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/resource.h>
#include <poll.h>
#include <fcntl.h>
#include <time.h>
typedef struct LiveSite {
 uint64_t key;
 _Atomic uint64_t allocs,bytes,frees,sampled_live,hist[65],next_check;
 _Atomic unsigned cls,answers; bool deciding;
 struct LiveSite* next;
} LiveSite;
typedef struct Sample {void* p;uint64_t birth,size;LiveSite* site;struct Sample* next;} Sample;
static LiveSite* live_sites[16384];
static Sample* samples[65536];
static atomic_uint sample_buckets[65536];
static pthread_mutex_t sample_mutex[64];
#define GET(x) atomic_load_explicit(&(x),memory_order_relaxed)
#define ADD(x,n) atomic_fetch_add_explicit(&(x),(n),memory_order_relaxed)
static pthread_mutex_t live_mutex=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t live_condition=PTHREAD_COND_INITIALIZER;
static _Atomic uint64_t live_clock,live_estimate,sampled_count;
static uint64_t live_site_count,blocked_ns,decisions,rechecks,timeouts,failures;
static unsigned sample_rate=64,timeout_ms=30000;
static atomic_bool circuit_open,live_closed;
static const char* socket_path;
static uint64_t nanos(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static uint64_t quant(uint64_t n) {return n?UINT64_C(1)<<(63-__builtin_clzll(n)):0;}
static void live_init(void) {
 for(unsigned i=0;i<64;i++)pthread_mutex_init(&sample_mutex[i],NULL);
 const char* s=getenv("JEVALLOC_SAMPLE");if(s){long n=strtol(s,NULL,10);if(n>0&&n<=1048576)sample_rate=(unsigned)n;}
 s=getenv("JEVALLOC_TIMEOUT_MS");if(s){long n=strtol(s,NULL,10);if(n>0&&n<=3600000)timeout_ms=(unsigned)n;}
 socket_path=getenv("JEVALLOC_SOCKET");
}
static int socket_wait(int fd,short events,uint64_t deadline) {
 for(;;){uint64_t now=nanos();if(now>=deadline){errno=ETIMEDOUT;return -1;}
  int ms=(int)((deadline-now+999999)/1000000);struct pollfd p={fd,events,0};
  int r=poll(&p,1,ms);if(r<0&&errno==EINTR)continue;if(r==0){errno=ETIMEDOUT;return -1;}if(r<0)return -1;
  if(p.revents&events)return 0;errno=ECONNRESET;return -1;
 }
}
static int exchange(const char* request,unsigned* cls,uint64_t* after) {
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
 if(!c||!a||sscanf(c,"\"class\" : %u",&v)!=1||v>2||sscanf(a,"\"recheck_after\" : %llu",&interval)!=1){errno=EPROTO;goto done;}
 *cls=v;*after=interval;rc=0;
 done: {int err=errno;close(fd);errno=err;}return rc;
}
static char* live_request(LiveSite* s,size_t size,Frame* frames,unsigned nf) {
 char* text=NULL;size_t length=0;FILE* f=open_memstream(&text,&length);if(!f)abort();
 fprintf(f,"{\"op\":\"decide\",\"key\":\"%016llx\",\"program\":",(unsigned long long)s->key);
#ifdef __APPLE__
 json_string(f,getprogname());
#else
 extern char* program_invocation_short_name;json_string(f,program_invocation_short_name);
#endif
 fputs(",\"frames\":[",f);
 for(unsigned i=0;i<nf;i++){fprintf(f,"%s{\"addr\":\"0x%llx\",\"image\":",i?",":"",(unsigned long long)frames[i].addr);json_string(f,images[frames[i].image].path);fputc('}',f);}
 fprintf(f,"],\"size\":%zu,\"site\":{\"allocs\":%llu,\"frees\":%llu,\"live\":%llu,\"bytes\":%llu,\"life_hist\":[",size,(unsigned long long)quant(s->allocs),(unsigned long long)quant(s->frees*sample_rate),(unsigned long long)quant(s->sampled_live*sample_rate),(unsigned long long)quant(s->bytes));
 uint64_t total=0;for(unsigned i=0;i<65;i++)total+=s->hist[i];
 for(unsigned i=0;i<65;i++)fprintf(f,"%s%llu",i?",":"",(unsigned long long)(total?quant((uint64_t)((long double)s->hist[i]*65536/total)):0));
 size_t rss=0,commit=0;mi_process_info(NULL,NULL,NULL,&rss,NULL,&commit,NULL,NULL);
 /* Upstream signed commit accounting can transiently be negative; zero means unavailable. */
 if(commit>PTRDIFF_MAX)commit=0;if(rss>PTRDIFF_MAX)rss=0;
 unsigned threads=1;
#ifndef __APPLE__
 FILE* status=fopen("/proc/self/status","r");if(status){char line[256];while(fgets(line,sizeof(line),status))if(sscanf(line,"Threads: %u",&threads)==1)break;fclose(status);}
#endif
 fprintf(f," ]},\"process\":{\"alloc_clock\":%llu,\"live_bytes\":%llu,\"committed\":%llu,\"rss\":%llu,\"threads\":%llu,\"sites\":%llu},\"prior\":",(unsigned long long)quant(live_clock),(unsigned long long)quant(live_estimate),(unsigned long long)quant(commit),(unsigned long long)quant(rss),(unsigned long long)quant(threads),(unsigned long long)quant(live_site_count));
 if(s->answers)fprintf(f,"%u",s->cls);else fputs("null",f);fputs("}\n",f);fclose(f);return text;
}
static LiveSite* live_before(uint64_t key,size_t n,Frame* frames,unsigned nf,unsigned* cls,bool* sample) {
 if(GET(live_closed)){*cls=default_class;*sample=false;return NULL;}
 LiveSite* s=context()->active_key->live_site;
 if(!s){
  pthread_mutex_lock(&live_mutex);
  size_t h=mix(key)&16383;s=live_sites[h];while(s&&s->key!=key)s=s->next;
  if(!s){s=metadata(sizeof(*s));s->key=key;s->cls=default_class;s->next=live_sites[h];live_sites[h]=s;live_site_count++;}
  context()->active_key->live_site=s;pthread_mutex_unlock(&live_mutex);
 }
 uint64_t count=ADD(s->allocs,1)+1;ADD(s->bytes,n);ADD(live_clock,n);*sample=count%sample_rate==0;
 uint64_t next=GET(s->next_check);
 if(!GET(circuit_open) && (!atomic_load_explicit(&s->answers,memory_order_acquire) || (next&&count>=next))){
  pthread_mutex_lock(&live_mutex);
  while(s->deciding){uint64_t begin=nanos();pthread_cond_wait(&live_condition,&live_mutex);blocked_ns+=nanos()-begin;}
  next=GET(s->next_check);
  if(!GET(circuit_open) && (!atomic_load_explicit(&s->answers,memory_order_acquire) || (next&&count>=next))){
   s->deciding=true;char* request=live_request(s,n,frames,nf);unsigned answer=default_class;uint64_t after=0;
   uint64_t decision_count=GET(s->allocs);
   if(GET(s->answers))rechecks++;decisions++;
   pthread_mutex_unlock(&live_mutex);uint64_t begin=nanos();int rc=exchange(request,&answer,&after);int error=errno;uint64_t elapsed=nanos()-begin;free(request);
   pthread_mutex_lock(&live_mutex);blocked_ns+=elapsed;
   if(rc){failures++;if(error==ETIMEDOUT)timeouts++;circuit_open=true;}
   s->cls=answer;s->next_check=after&&after<UINT64_MAX-decision_count?decision_count+after:0;s->answers++;s->deciding=false;pthread_cond_broadcast(&live_condition);
  }
  pthread_mutex_unlock(&live_mutex);
 }
 *cls=GET(s->cls);return s;
}
static void live_alloc(void* p,size_t n,LiveSite* s) {
 if(!s||GET(live_closed))return;Sample* record=metadata(sizeof(*record));size_t h=mix((uintptr_t)p)&65535;
 pthread_mutex_lock(&sample_mutex[h&63]);
 *record=(Sample){p,GET(live_clock),n,s,samples[h]};samples[h]=record;ADD(sample_buckets[h],1);ADD(s->sampled_live,1);ADD(live_estimate,n*sample_rate);ADD(sampled_count,1);
 pthread_mutex_unlock(&sample_mutex[h&63]);
}
static void live_free(void* p) {
 size_t h=mix((uintptr_t)p)&65535;if(!GET(sample_buckets[h]))return;
 pthread_mutex_lock(&sample_mutex[h&63]);Sample** pp=&samples[h];while(*pp&&(*pp)->p!=p)pp=&(*pp)->next;
 Sample* r=*pp;
 if(r){*pp=r->next;ADD(sample_buckets[h],-1);uint64_t life=GET(live_clock)-r->birth;unsigned bucket=life?64-__builtin_clzll(life):0;ADD(r->site->hist[bucket],1);ADD(r->site->frees,1);ADD(r->site->sampled_live,-1);ADD(live_estimate,-r->size*sample_rate);}
 pthread_mutex_unlock(&sample_mutex[h&63]);if(r)mi_free(r);
}
static void live_finish(void) {
 pthread_mutex_lock(&live_mutex);live_closed=true;const char* path=getenv("JEVALLOC_STATS_OUT");if(!path)path="jevalloc-stats.json";FILE* f=fopen(path,"w");
 if(f){fputs("{\"site_bytes\":{",f);bool first=true;
  for(unsigned h=0;h<16384;h++)for(LiveSite* s=live_sites[h];s;s=s->next){fprintf(f,"%s\"%016llx\":%llu",first?"":",",(unsigned long long)s->key,(unsigned long long)GET(s->bytes));first=false;}
  fprintf(f,"},\"blocked_ns\":%llu,\"decisions\":%llu,\"rechecks\":%llu,\"timeouts\":%llu,\"failures\":%llu,\"sites\":%llu,\"samples\":%llu,\"sample_rate\":%u,\"allocation_clock\":%llu}\n",(unsigned long long)blocked_ns,(unsigned long long)decisions,(unsigned long long)rechecks,(unsigned long long)timeouts,(unsigned long long)failures,(unsigned long long)live_site_count,(unsigned long long)sampled_count,sample_rate,(unsigned long long)live_clock);fclose(f);}
 pthread_mutex_unlock(&live_mutex);
}
