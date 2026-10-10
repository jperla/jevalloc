#define _GNU_SOURCE
#include "jevalloc.h"
#include "mimalloc.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <dlfcn.h>
#ifdef __APPLE__
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <ptrauth.h>
#else
#include <link.h>
#endif
#define MAX_DEPTH 16
#define MAX_IMAGES 1024
static int depth=4, default_class=1, policy=0;
static bool ready, tracing, living;
typedef struct { uint64_t addr; unsigned image; } Frame;
typedef struct { uint64_t raw,key; unsigned cls,nf; void* live_site; Frame frames[MAX_DEPTH]; } KeyCache;
typedef struct { int busy; KeyCache keys[256]; KeyCache* active_key; mi_heap_t* heaps[3]; uintptr_t stack_lo,stack_hi; } Thread;
#ifndef __APPLE__
static __thread Thread tls_context __attribute__((tls_model("initial-exec")));
static inline Thread* context(void) { return &tls_context; }
#else
static pthread_key_t context_key;
static Thread* context(void) {
 Thread* t=pthread_getspecific(context_key);
 if(!t){ t=mi_zalloc(sizeof(*t));if(!t)abort();pthread_setspecific(context_key,t); }
 return t;
}
#endif
#define busy (context()->busy)
#define heaps (context()->heaps)
#define stack_lo (context()->stack_lo)
#define stack_hi (context()->stack_hi)
typedef struct { uintptr_t lo,hi,base; uint64_t hash; const char* path; bool own; } Image;
static Image images[MAX_IMAGES];
static atomic_uint image_count;
static uintptr_t own_lo,own_hi;
static char executable_path[4096];
typedef struct { uint64_t key; unsigned cls; } Entry;
static Entry* table; static size_t table_cap;
static uint64_t mix(uint64_t x) { x^=x>>30; x*=UINT64_C(0xbf58476d1ce4e5b9); x^=x>>27; x*=UINT64_C(0x94d049bb133111eb); return x^(x>>31); }
static uint64_t strhash(const char* p) { uint64_t h=1469598103934665603ULL; while(*p) { h^=(unsigned char)*p++; h*=1099511628211ULL; } return h; }
#ifdef __APPLE__
static void image_add(const struct mach_header* header,intptr_t slide) {
  if(header->magic!=MH_MAGIC_64) return;
  const struct mach_header_64* mh=(const void*)header;
  const struct load_command* cmd=(const void*)(mh+1);
  Dl_info di; if(!dladdr(header,&di)) return;
  for(unsigned j=0;j<mh->ncmds;j++,cmd=(const void*)((const char*)cmd+cmd->cmdsize)) {
    if(cmd->cmd==LC_SEGMENT_64) { const struct segment_command_64* s=(const void*)cmd;
      if(!(s->initprot&VM_PROT_EXECUTE)) continue;
      unsigned i=atomic_load(&image_count); if(i>=MAX_IMAGES) abort();
      images[i]=(Image){s->vmaddr+slide,s->vmaddr+slide+s->vmsize,(uintptr_t)slide,strhash(di.dli_fname),di.dli_fname,strstr(di.dli_fname,"libjevalloc")!=NULL};
      atomic_store(&image_count,i+1);
    }
  }
}
#else
static int image_add(struct dl_phdr_info* info,size_t size,void* data) {
  (void)size;(void)data;
  for(int j=0;j<info->dlpi_phnum;j++) if(info->dlpi_phdr[j].p_flags&PF_X) {
    const ElfW(Phdr)* p=&info->dlpi_phdr[j]; unsigned i=atomic_load(&image_count); if(i>=MAX_IMAGES) abort();
    const char* path=*info->dlpi_name?info->dlpi_name:executable_path;
    images[i]=(Image){info->dlpi_addr+p->p_vaddr,info->dlpi_addr+p->p_vaddr+p->p_memsz,info->dlpi_addr,strhash(path),path,strstr(path,"libjevalloc")!=NULL}; atomic_store(&image_count,i+1);
  } return 0;
}
#endif
static unsigned lookup(uint64_t);
static __attribute__((noinline)) uint64_t capture(Frame* frames,unsigned* count,unsigned* prediction) {
  if(!stack_hi) {
#ifdef __APPLE__
    stack_hi=(uintptr_t)pthread_get_stackaddr_np(pthread_self()); stack_lo=stack_hi-pthread_get_stacksize_np(pthread_self());
#else
    pthread_attr_t a; void* lo; size_t size; pthread_getattr_np(pthread_self(),&a); pthread_attr_getstack(&a,&lo,&size); pthread_attr_destroy(&a); stack_lo=(uintptr_t)lo;stack_hi=stack_lo+size;
#endif
  }
  uintptr_t pcs[MAX_DEPTH];
  uintptr_t* fp=__builtin_frame_address(0); unsigned n=0;
  uint64_t raw=0x6a09e667f3bcc909ULL;
  uintptr_t lo=stack_lo,hi=stack_hi;
  for(unsigned step=0;step<64 && n<(unsigned)depth;step++) {
    uintptr_t f=(uintptr_t)fp;
    if(f<lo || f>hi-2*sizeof(uintptr_t) || (f&(sizeof(uintptr_t)-1))) break;
    uintptr_t pc=fp[1];
#ifdef __APPLE__
    pc=(uintptr_t)ptrauth_strip((void*)pc,ptrauth_key_return_address);
#endif
    if(pc<own_lo || pc>=own_hi) {
      pcs[n++]=pc; raw=((raw<<13)|(raw>>51))^pc;
    }
    uintptr_t next=fp[0]; if(next<=f || next-f>8*1024*1024) break; fp=(uintptr_t*)next;
  }
  raw=raw?raw:1;
  KeyCache* cached=&context()->keys[(raw^(raw>>32))&255];
  if(living)context()->active_key=cached;
  if(cached->raw==raw) {if(count)*count=cached->nf;if(frames)memcpy(frames,cached->frames,cached->nf*sizeof(Frame));if(prediction)*prediction=cached->cls;return cached->key;}
  uint64_t h=0x6a09e667f3bcc909ULL; unsigned nf=0;
  unsigned ni=atomic_load_explicit(&image_count,memory_order_acquire);
  for(unsigned j=0;j<n;j++) {
    unsigned im=0;uintptr_t pc=pcs[j];
    for(;im<ni;im++)if(pc>=images[im].lo && pc<images[im].hi)break;
    if(im<ni && !images[im].own) {
      uint64_t addr=pc-images[im].base;
      cached->frames[nf]=(Frame){addr,im};
      h=mix(h^mix(addr)^images[im].hash);nf++;
    }
  }
  h=h?h:1;cached->raw=raw;cached->key=h;cached->live_site=NULL;cached->cls=lookup(h);cached->nf=nf;
  if(frames)memcpy(frames,cached->frames,nf*sizeof(Frame));
  if(count)*count=nf;
  if(prediction)*prediction=cached->cls;
  return h;
}
uint64_t jev_site_key(void) { busy++; uint64_t key=capture(NULL,NULL,NULL); busy--; return key; }
static unsigned lookup(uint64_t key) {
  if(!table_cap) return default_class;
  size_t i=mix(key)&(table_cap-1); while(table[i].key) {if(table[i].key==key) return table[i].cls;i=(i+1)&(table_cap-1);} return default_class;
}
static void load_table(const char* path) {
  if(!path || !*path) return; FILE* f=fopen(path,"r"); if(!f) {perror("JEVALLOC_TABLE");abort();}
  size_t count=0; unsigned cls; unsigned long long key;
  while(fscanf(f,"%llx %u",&key,&cls)==2) {if(!key || cls>2) abort();count++;}
  if(!feof(f)) abort(); rewind(f); table_cap=16;while(table_cap<count*2+1)table_cap*=2;
  size_t bytes=table_cap*sizeof(Entry); table=mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);if(table==MAP_FAILED)abort();
  while(fscanf(f,"%llx %u",&key,&cls)==2) {size_t i=mix(key)&(table_cap-1);while(table[i].key && table[i].key!=key)i=(i+1)&(table_cap-1);table[i]=(Entry){key,cls};}
  fclose(f); if(mprotect(table,bytes,PROT_READ))abort();
}
static void trace_alloc(void*,size_t,uint64_t,Frame*,unsigned);
static void trace_free(void*);
static void trace_finish(void);
typedef struct LiveSite LiveSite;
static void live_init(void);
static LiveSite* live_before(uint64_t,size_t,Frame*,unsigned,unsigned*,bool*);
static void live_alloc(void*,size_t,LiveSite*);
static void live_free(void*);
static void live_finish(void);
__attribute__((constructor)) static void init(void) {
#ifdef __APPLE__
  if(pthread_key_create(&context_key,mi_free))abort();
#else
  ssize_t path_len=readlink("/proc/self/exe",executable_path,sizeof(executable_path)-1);
  if(path_len>0)executable_path[path_len]=0;
#endif
  busy++;
  const char* s=getenv("JEVALLOC_DEPTH");if(s)depth=atoi(s);if(depth<1)depth=1;if(depth>MAX_DEPTH)depth=MAX_DEPTH;
  s=getenv("JEVALLOC_DEFAULT");if(s)default_class=atoi(s);if(default_class<0||default_class>2)abort();
  s=getenv("JEVALLOC_POLICY");if(s && !strcmp(s,"none"))policy=1;else if(s&&!strcmp(s,"keyonly"))policy=2;
  s=getenv("JEVALLOC_MODE");tracing=s&&!strcmp(s,"trace");living=s&&!strcmp(s,"live");if(living)live_init();
#ifdef __APPLE__
  _dyld_register_func_for_add_image(image_add);
#else
  dl_iterate_phdr(image_add,NULL);
#endif
  for(unsigned i=0;i<atomic_load(&image_count);i++)if(images[i].own){own_lo=images[i].lo;own_hi=images[i].hi;}
  load_table(getenv("JEVALLOC_TABLE"));ready=true;busy--;
}
__attribute__((destructor)) static void finish(void) { if(tracing || living) {busy++;if(tracing)trace_finish();if(living)live_finish();busy--;} }
static void* allocate(size_t n,size_t alignment,bool zero) {
  if(!ready || busy) return alignment?mi_zalloc_aligned(n,alignment):(zero?mi_zalloc(n):mi_malloc(n));
  if(n>PTRDIFF_MAX){errno=ENOMEM;return NULL;}
  busy++; Frame frames[MAX_DEPTH];unsigned nf=0;uint64_t key=0;unsigned cls=0;LiveSite* site=NULL;bool sampled=false;
  if(policy!=1 || tracing || living) {unsigned predicted;key=capture(tracing?frames:NULL,&nf,&predicted);if(policy==0)cls=predicted;else __asm__ volatile("" : : "r"(predicted));}
  if(living)site=live_before(key,n,context()->active_key->frames,nf,&cls,&sampled);
  if(!heaps[cls]) heaps[cls]=mi_heap_new();
  void* p=alignment?(zero?mi_heap_zalloc_aligned(heaps[cls],n,alignment):mi_heap_malloc_aligned(heaps[cls],n,alignment)):(zero?mi_heap_zalloc(heaps[cls],n):mi_heap_malloc(heaps[cls],n));
  if(tracing && p)trace_alloc(p,n,key,frames,nf);if(living&&p&&sampled)live_alloc(p,n,site); busy--;return p;
}
void* jev_malloc(size_t n) {if(policy==1&&!tracing&&!living)return mi_malloc(n);return allocate(n,0,false);}
void* jev_calloc(size_t n,size_t s) {if(policy==1&&!tracing&&!living)return mi_calloc(n,s);if(s && n>SIZE_MAX/s){errno=ENOMEM;return NULL;}return allocate(n*s,0,true);}
void jev_free(void* p) {if(!p)return;if((tracing||living) && ready && !busy){busy++;if(tracing)trace_free(p);if(living)live_free(p);busy--;}mi_free(p);}
void jev_cfree(void* p) {if(mi_is_in_heap_region(p))jev_free(p);}
void* jev_realloc(void* p,size_t n) {if(policy==1&&!tracing&&!living)return mi_realloc(p,n);if(!p)return jev_malloc(n);void* q=jev_malloc(n);if(q){memcpy(q,p,n<mi_usable_size(p)?n:mi_usable_size(p));jev_free(p);}return q;}
void* jev_malloc_aligned(size_t n,size_t a) {if(policy==1&&!tracing&&!living)return a?mi_malloc_aligned(n,a):mi_malloc(n);return allocate(n,a,false);}
void* jev_aligned_alloc(size_t a,size_t n) {if(!a||(a&(a-1))||n%a){errno=EINVAL;return NULL;}return allocate(n,a,false);}
int jev_posix_memalign(void** p,size_t a,size_t n) {if(a<sizeof(void*)||(a&(a-1)))return EINVAL;void* q=allocate(n,a,false);if(!q)return ENOMEM;*p=q;return 0;}
void* jev_valloc(size_t n){return allocate(n,(size_t)getpagesize(),false);}
void* jev_pvalloc(size_t n){size_t a=getpagesize();if(n>SIZE_MAX-a){errno=ENOMEM;return NULL;}return allocate((n+a-1)&~(a-1),a,false);}
void* jev_memalign(size_t a,size_t n){if(!a||(a&(a-1))){errno=EINVAL;return NULL;}return allocate(n,a,false);}
void* jev_reallocf(void* p,size_t n){void* q=jev_realloc(p,n);if(!q)jev_free(p);return q;}
void* jev_reallocarray(void* p,size_t n,size_t s){if(s&&n>SIZE_MAX/s){errno=ENOMEM;return NULL;}return jev_realloc(p,n*s);}
int jev_reallocarr(void* pp,size_t n,size_t s){void* p=jev_reallocarray(*(void**)pp,n,s);if(!p)return ENOMEM;*(void**)pp=p;return 0;}
char* jev_strndup(const char* s,size_t n){size_t k=strnlen(s,n);char* p=jev_malloc(k+1);if(p){memcpy(p,s,k);p[k]=0;}return p;}
char* jev_strdup(const char* s){return jev_strndup(s,strlen(s));}
void jev_free_size(void* p,size_t n){(void)n;jev_free(p);}
void jev_free_aligned(void* p,size_t a){(void)a;jev_free(p);}
void jev_free_size_aligned(void* p,size_t n,size_t a){(void)n;(void)a;jev_free(p);}
/* Trace implementation is kept in the same translation unit for private state. */
#include "trace.inc"

#include "live.inc"
