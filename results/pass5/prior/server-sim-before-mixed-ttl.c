#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <stdatomic.h>
#include <sys/resource.h>
#include <sys/mman.h>

/* Every allocation shares the same innermost wrapper. Depth 1 cannot classify it.
 * Workers remain alive at idle so the experiment includes page purging, not just
 * wholesale address-space release at thread exit. No allocator-specific collect. */
static _Thread_local size_t worker_live;
static struct { _Alignas(64) size_t bytes; } live_bytes[32];
static pthread_barrier_t boundary;
static int workers=1,mixed=0,settle_ms=250;
static size_t objects=80000;
static uint64_t random_next(uint64_t* x){*x^=*x<<13;*x^=*x>>7;*x^=*x<<17;return *x;}
__attribute__((noinline)) static void* xmalloc(size_t n) {
 void* p=malloc(n);if(!p)abort();memset(p,0xa5,n);worker_live+=n;return p;
}
__attribute__((noinline)) static void* parse_request_buffer(size_t n){return xmalloc(n);}
__attribute__((noinline)) static void* assemble_response_buffer(size_t n){return xmalloc(n);}
__attribute__((noinline)) static void* create_session_state(size_t n){return xmalloc(n);}
__attribute__((noinline)) static void* insert_cache_index(size_t n){return xmalloc(n);}
/* TTL is data, deliberately absent from the stack key: a per-site predictor must
 * give retained and temporary payloads one class. Its oracle is a majority label. */
__attribute__((noinline)) static void* store_request_payload(size_t n,unsigned ttl){
 void* p=xmalloc(n);((unsigned char*)p)[0]=(unsigned char)ttl;return p;
}
static void release(void* p,size_t n){free(p);worker_live-=n;}
static void phase(int cycle,const char* name) {
 pthread_barrier_wait(&boundary);
 if(!strcmp(name,"idle"))usleep(settle_ms*1000);
 pthread_barrier_wait(&boundary);
}
static void emit(int cycle,const char* name) {
 FILE* f=fopen("/proc/self/statm","r");unsigned long pages=0,resident=0;
 if(!f||fscanf(f,"%lu %lu",&pages,&resident)!=2)abort();fclose(f);
 struct rusage r;getrusage(RUSAGE_SELF,&r);
 size_t live=0;for(int i=0;i<workers;i++)live+=live_bytes[i].bytes;
 printf("{\"phase\":\"%s\",\"cycle\":%d,\"rss_bytes\":%lu,\"live_bytes\":%zu,\"fragmentation_ratio\":%.6f,\"peak_rss_bytes\":%ld}\n",name,cycle,resident*sysconf(_SC_PAGESIZE),live,live?(double)(resident*sysconf(_SC_PAGESIZE))/live:0,r.ru_maxrss*1024);fflush(stdout);
}
static void mark(size_t id,int cycle,const char* name){live_bytes[id].bytes=worker_live;phase(cycle,name);if(id==0)emit(cycle,name);pthread_barrier_wait(&boundary);}
static void* server_worker(void* arg) {
 size_t id=(size_t)arg,count=objects/workers;uint64_t rng=1729+id;
 /* Pointer bookkeeping uses the system mapping API so it doesn't enter the
  * allocator's live requested-byte metric or pin experimental object pages. */
 size_t bookkeeping=count*(sizeof(void*)+sizeof(size_t));
 void** slots=mmap(NULL,bookkeeping,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(slots==(void*)-1)abort();
 size_t* sizes=(size_t*)(slots+count);
 for(int cycle=0;cycle<2;cycle++) {
  for(size_t i=0;i<count;i++) {
   size_t n=(cycle?384:192)+(random_next(&rng)%4)*64;sizes[i]=n;
   /* Sessions last many operations; cache entries live until process exit.
    * The two paths allocate interleaved in exactly the same size classes. */
   if(mixed)slots[i]=store_request_payload(n,i%10==0?86400:1);
   else slots[i]=(i%10==0)?insert_cache_index(n):create_session_state(n);
   void* parse=parse_request_buffer(n);void* response=assemble_response_buffer(n);
   release(response,n);release(parse,n);
  }
  mark(id,cycle,"peak");
  for(size_t i=0;i<count;i++)if(i%10){release(slots[i],sizes[i]);slots[i]=NULL;}
  mark(id,cycle,"drop");
  /* Allocate/free after the purge deadline: mimalloc processes deferred purge
   * during allocator activity. Same pulse on all variants, counted in live bytes. */
  usleep(settle_ms*1000);
  for(int j=0;j<1024;j++){void* p=parse_request_buffer(64);release(p,64);}
  mark(id,cycle,"idle");
  /* Retained entries are deliberately never freed, including after cycle 1.
   * Their pointers need not remain in slots, but their requested bytes do. */
 }
 munmap(slots,bookkeeping);return NULL;
}
int main(int argc,char** argv) {
 if(argc>1)workers=atoi(argv[1]);if(argc>2)mixed=!strcmp(argv[2],"site-mixed");if(argc>3)objects=strtoull(argv[3],NULL,10);if(argc>4)settle_ms=atoi(argv[4]);
 if(workers<1||workers>32||objects<(size_t)workers||settle_ms<100)return 2;
 pthread_barrier_init(&boundary,NULL,workers);pthread_t threads[32];
 for(size_t i=0;i<(size_t)workers;i++)if(pthread_create(&threads[i],NULL,server_worker,(void*)i))abort();
 for(int i=0;i<workers;i++)pthread_join(threads[i],NULL);
 puts("fragbench OK");return 0;
}
