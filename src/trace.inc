/* All trace transitions linearize under this mutex. Metadata uses raw mimalloc.
 * Long candidates are retained exactly until the final allocation clock is known;
 * candidates that cannot possibly exceed half of the final clock are retired. */
#define SITE_BUCKETS 16384
#define PTR_BUCKETS 1048576
typedef struct Site {
 uint64_t key,count,bytes,live,live_bytes,hist[65],hist_bytes[65],classes[3];
 Frame frames[MAX_DEPTH]; unsigned nf; struct Site* next;
} Site;
typedef struct Live {void* p;uint64_t birth,size;Site* site;struct Live* next;} Live;
typedef struct Candidate {uint64_t life,size;Site* site;struct Candidate* next;} Candidate;
static Site* sites[SITE_BUCKETS];
static Live** pointers;
static Candidate* candidates;
static uint64_t allocation_clock,next_prune=1048576;
static pthread_mutex_t trace_mutex=PTHREAD_MUTEX_INITIALIZER;
static bool trace_closed;
static void* metadata(size_t n) {void* p=mi_zalloc(n);if(!p)abort();return p;}
static void prune(bool final) {
 Candidate** pp=&candidates;
 while(*pp){Candidate* c=*pp;if(final || c->life<=allocation_clock/2){c->site->classes[c->life>allocation_clock/2?2:(c->life<1048576?0:1)]+=c->size;*pp=c->next;mi_free(c);}else pp=&c->next;}
 next_prune=allocation_clock>UINT64_MAX/2?UINT64_MAX:allocation_clock*2;
}
static void trace_alloc(void* p,size_t n,uint64_t key,Frame* frames,unsigned nf) {
 pthread_mutex_lock(&trace_mutex);
 if(trace_closed){pthread_mutex_unlock(&trace_mutex);return;}
 if(!pointers)pointers=metadata(PTR_BUCKETS*sizeof(*pointers));
 size_t h=mix(key)&(SITE_BUCKETS-1);Site* s=sites[h];while(s&&s->key!=key)s=s->next;
 if(!s){s=metadata(sizeof(*s));s->key=key;s->nf=nf;memcpy(s->frames,frames,nf*sizeof(Frame));s->next=sites[h];sites[h]=s;}
 if(UINT64_MAX-allocation_clock<n)abort();allocation_clock+=n;s->count++;s->bytes+=n;s->live++;s->live_bytes+=n;
 h=mix((uintptr_t)p)&(PTR_BUCKETS-1);Live* l=metadata(sizeof(*l));*l=(Live){p,allocation_clock,n,s,pointers[h]};pointers[h]=l;
 if(allocation_clock>=next_prune)prune(false);
 pthread_mutex_unlock(&trace_mutex);
}
static void trace_free(void* p) {
 pthread_mutex_lock(&trace_mutex);
 if(trace_closed||!pointers){pthread_mutex_unlock(&trace_mutex);return;}
 size_t h=mix((uintptr_t)p)&(PTR_BUCKETS-1);Live** pp=&pointers[h];while(*pp&&(*pp)->p!=p)pp=&(*pp)->next;
 if(*pp){Live* l=*pp;*pp=l->next;Site* s=l->site;uint64_t life=allocation_clock-l->birth;unsigned bucket=life?64-__builtin_clzll(life):0;
   s->hist[bucket]++;s->hist_bytes[bucket]+=l->size;s->live--;s->live_bytes-=l->size;
   if(life>allocation_clock/2) {Candidate* c=metadata(sizeof(*c));*c=(Candidate){life,l->size,s,candidates};candidates=c;}
   else s->classes[life<1048576?0:1]+=l->size;
   mi_free(l);
 }
 pthread_mutex_unlock(&trace_mutex);
}
static void json_string(FILE* f,const char* s){fputc('"',f);for(;*s;s++){unsigned char c=*s;if(c=='"'||c=='\\')fprintf(f,"\\%c",c);else if(c<32)fprintf(f,"\\u%04x",c);else fputc(c,f);}fputc('"',f);}
static void array(FILE* f,uint64_t* a,unsigned n){fputc('[',f);for(unsigned i=0;i<n;i++)fprintf(f,"%s%llu",i?",":"",(unsigned long long)a[i]);fputc(']',f);}
static void trace_finish(void) {
 pthread_mutex_lock(&trace_mutex);trace_closed=true;prune(true);
 const char* path=getenv("JEVALLOC_TRACE_OUT");if(!path)path="jevalloc-trace.jsonl";
 FILE* f=fopen(path,"w");if(!f){perror(path);abort();}
 for(unsigned h=0;h<SITE_BUCKETS;h++)for(Site* s=sites[h];s;s=s->next){
  fprintf(f,"{\"schema\":1,\"key\":\"%016llx\",\"program\":",(unsigned long long)s->key);
#ifdef __APPLE__
  json_string(f,getprogname());
#else
  extern char* program_invocation_short_name;json_string(f,program_invocation_short_name);
#endif
  fprintf(f,",\"total_allocation_bytes\":%llu,\"count\":%llu,\"bytes\":%llu,\"never_freed\":%llu,\"never_freed_bytes\":%llu,\"lifetime_histogram\":",(unsigned long long)allocation_clock,(unsigned long long)s->count,(unsigned long long)s->bytes,(unsigned long long)s->live,(unsigned long long)s->live_bytes);
  array(f,s->hist,65);fputs(",\"lifetime_histogram_bytes\":",f);array(f,s->hist_bytes,65);s->classes[2]+=s->live_bytes;
  fputs(",\"class_bytes\":",f);array(f,s->classes,3);fputs(",\"frames\":[",f);
  for(unsigned i=0;i<s->nf;i++){fprintf(f,"%s{\"address\":\"0x%llx\",\"image\":",i?",":"",(unsigned long long)s->frames[i].addr);json_string(f,images[s->frames[i].image].path);fputc('}',f);}
  fputs("]}\n",f);
 }
 if(fclose(f))abort();pthread_mutex_unlock(&trace_mutex);
}
