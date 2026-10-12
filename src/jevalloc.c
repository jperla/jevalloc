#define _GNU_SOURCE
#define JEVALLOC_IMPLEMENTATION
#include "jevalloc.h"
#include <stdarg.h>
#include "mimalloc.h"
#define MI_BUILD_RELEASE 1
#include "mimalloc/internal.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
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
#define KEY_CACHE_SIZE 64
#define MAX_IMAGES 1024
static uint64_t short_bytes=1048576;
static int depth=4, model_depth=12, default_class=0, policy=0;
static bool context_enabled=true;
static bool none_fast, instrumented, ready, tracing, living, legacy_heaps;
static atomic_bool fail_heaps;
typedef struct { uint64_t addr; unsigned image; } Frame;
typedef struct { _Alignas(64) uint64_t raw,key,site_key,signature; void* live_site; uint8_t cls,nf,raw_nf; uintptr_t pcs[MAX_DEPTH]; Frame* frames; } KeyCache;
typedef struct { char request_context[256]; uint64_t signature,decision_ordinal; bool allocation_decided; int recursion; bool main_thread; KeyCache* keys; KeyCache* active_key; mi_heap_t* class_heaps[2]; uintptr_t stack_lo,stack_hi; void* live_shards; void* live_index; uint64_t clock_pending; } Thread;
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
#define busy (context()->recursion)
#define heaps (context()->class_heaps)
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
void jev_context_set(const char* text) {
 if(none_fast)return;
 Thread* t=context();size_t n=0;
 if(text)while(n<sizeof(t->request_context)-1 && text[n]){t->request_context[n]=text[n];n++;}
 t->request_context[n]=0;t->signature=n?strhash(t->request_context):0;
}
void jev_context_clear(void){jev_context_set(NULL);}
void jev_context_setf(const char* format,...) {
 if(none_fast)return;
 char text[256];Thread* t=context();t->recursion++;
 va_list ap;va_start(ap,format);vsnprintf(text,sizeof(text),format,ap);va_end(ap);
 t->recursion--;jev_context_set(text);
}

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
  /* Identify this image by code address, not a filename substring. Besides
   * supporting renamed libraries, this avoids a cold libc string-search path. */
  uintptr_t self=(uintptr_t)&image_add;bool own=false;
  for(int j=0;j<info->dlpi_phnum;j++) {
    const ElfW(Phdr)* p=&info->dlpi_phdr[j];
    if((p->p_flags&PF_X)&&self>=info->dlpi_addr+p->p_vaddr&&self<info->dlpi_addr+p->p_vaddr+p->p_memsz)own=true;
  }
  for(int j=0;j<info->dlpi_phnum;j++) if(info->dlpi_phdr[j].p_flags&PF_X) {
    const ElfW(Phdr)* p=&info->dlpi_phdr[j]; unsigned i=atomic_load(&image_count); if(i>=MAX_IMAGES) abort();
    const char* path=*info->dlpi_name?info->dlpi_name:executable_path;
    images[i]=(Image){info->dlpi_addr+p->p_vaddr,info->dlpi_addr+p->p_vaddr+p->p_memsz,info->dlpi_addr,strhash(path),path,own}; atomic_store(&image_count,i+1);
  } return 0;
}
#endif
static size_t key_cache_bytes(void){return KEY_CACHE_SIZE*(sizeof(KeyCache)+(instrumented?MAX_DEPTH*sizeof(Frame):0));}
static void live_thread_finish(Thread*);
static void context_destroy(void* arg) {
 Thread* t=arg;
#ifdef __APPLE__
 pthread_setspecific(context_key,t);
#endif
 t->recursion++;
 if(living)live_thread_finish(t);
 /* Raw frees remain valid even if mimalloc's own destructor ran first. */
 if(t->keys)munmap(t->keys,key_cache_bytes());t->keys=NULL;t->active_key=NULL;
 memset(t->class_heaps,0,sizeof(t->class_heaps));
#ifdef __APPLE__
 mi_free(t);pthread_setspecific(context_key,NULL);
#else
 t->recursion--;
#endif
}
#ifndef __APPLE__
/* Called by the core before its existing thread teardown abandons class heaps.
 * Reuse that lifecycle rather than allocate a second pthread destructor key. */
void _mi_jev_context_done(void) {
 Thread* t=context();if(t->keys||t->live_shards||t->class_heaps[0]||t->class_heaps[1])context_destroy(t);
}
#endif
#ifndef __APPLE__
static uintptr_t maps_address(const char** text) {
 uintptr_t value=0;const char* p=*text;
 for(;;p++){unsigned digit=(unsigned char)*p;
  if(digit>='0'&&digit<='9')digit-='0';
  else if(digit>='a'&&digit<='f')digit=digit-'a'+10;
  else break;
  value=(value<<4)|digit;
 }
 *text=p;return value;
}
static bool main_stack_bounds(uintptr_t* low,uintptr_t* high) {
 int fd=open("/proc/self/maps",O_RDONLY|O_CLOEXEC);if(fd<0)return false;
 /* Only the address/protection prefix matters; a long pathname can be dropped.
  * Keep bootstrap stack use small and avoid libc's general integer parser. */
 char buf[512],line[128];size_t used=0;ssize_t got;bool found=false;
 uintptr_t here=(uintptr_t)&fd;
 while(!found&&(got=read(fd,buf,sizeof(buf)))>0)for(ssize_t i=0;i<got;i++) {
  if(buf[i]=='\n') {
   line[used]=0;const char* end=line;uintptr_t a=maps_address(&end),b=0;
   if(*end=='-'){end++;b=maps_address(&end);}
   while(*end==' ')end++;
   if(here>=a&&here<b&&*end=='r'){*low=a;*high=b;found=true;break;}
   used=0;
  } else if(used<sizeof(line)-1)line[used++]=buf[i];
 }
 close(fd);return found;
}
#endif
/* Exact identity without pulling a libc comparison path into keyed workloads. */
static inline bool same_pcs(const uintptr_t* a,const uintptr_t* b,unsigned n) {
 uintptr_t different=0;for(unsigned i=0;i<n;i++)different|=a[i]^b[i];return different==0;
}
static unsigned lookup(uint64_t);
static __attribute__((noinline)) uint64_t capture(Frame* frames,unsigned* count,unsigned* prediction) {
  if(!stack_hi
#ifndef __APPLE__
     ||(context()->main_thread&&(uintptr_t)__builtin_frame_address(0)<stack_lo)
#endif
  ) {
#ifdef __APPLE__
    stack_hi=(uintptr_t)pthread_get_stackaddr_np(pthread_self()); stack_lo=stack_hi-pthread_get_stacksize_np(pthread_self());
#else
    if(context()->main_thread&&main_stack_bounds(&stack_lo,&stack_hi)){}else {
    pthread_attr_t a; void* lo; size_t size; pthread_getattr_np(pthread_self(),&a); pthread_attr_getstack(&a,&lo,&size); pthread_attr_destroy(&a); stack_lo=(uintptr_t)lo;stack_hi=stack_lo+size;}
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
      pcs[n]=pc;if(n<(unsigned)depth)raw=((raw<<13)|(raw>>51))^pc;n++;
    }
    uintptr_t next=fp[0]; if(next<=f || next-f>8*1024*1024){fp=NULL;break;} fp=(uintptr_t*)next;
  }
  uint64_t signature=context_enabled?context()->signature:0;
  raw=mix(raw^signature);raw=raw?raw:1;
  if(!context()->keys) {
    context()->keys=mmap(NULL,key_cache_bytes(),PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
    if(context()->keys==MAP_FAILED){context()->keys=NULL;}
    if(!context()->keys){if(count)*count=0;if(prediction)*prediction=default_class;return 0;}
#ifdef __APPLE__
    pthread_setspecific(context_key,context());
#else
    mi_thread_init();
    if(!mi_heap_is_initialized(mi_heap_get_default())) {
      munmap(context()->keys,key_cache_bytes());context()->keys=NULL;
      if(count)*count=0;if(prediction)*prediction=default_class;return 0;
    }
#endif
  }
  /* Fold every frame into the index; low-bit XOR alone can ignore the innermost
   * PC after the rotations, thrashing sites that share their outer callers. */
  KeyCache* cached=&context()->keys[mix(raw)&(KEY_CACHE_SIZE-1)];
  if(instrumented)context()->active_key=cached;
  unsigned raw_nf=n<(unsigned)depth?n:(unsigned)depth;
  if(cached->signature==signature&&cached->raw==raw&&cached->raw_nf==raw_nf&&same_pcs(cached->pcs,pcs,raw_nf)) {if(count)*count=cached->nf;if(frames)memcpy(frames,cached->frames,cached->nf*sizeof(Frame));if(prediction)*prediction=cached->cls;return cached->key;}
  if(instrumented&&!cached->frames)cached->frames=(Frame*)(context()->keys+KEY_CACHE_SIZE)+(cached-context()->keys)*MAX_DEPTH;
  /* Only cache misses need the wider model stack. Keyed hot paths walk K frames. */
  if((tracing||living)&&n==(unsigned)depth)for(unsigned step=0;step<64&&n<(unsigned)model_depth;step++) {
    uintptr_t f=(uintptr_t)fp;
    if(f<lo||f>hi-2*sizeof(uintptr_t)||(f&(sizeof(uintptr_t)-1)))break;
    uintptr_t pc=fp[1];
#ifdef __APPLE__
    pc=(uintptr_t)ptrauth_strip((void*)pc,ptrauth_key_return_address);
#endif
    if(pc<own_lo||pc>=own_hi)pcs[n++]=pc;
    uintptr_t next=fp[0];if(next<=f||next-f>8*1024*1024){fp=NULL;break;}fp=(uintptr_t*)next;
  }
  uint64_t h=0x6a09e667f3bcc909ULL; unsigned nf=0;
  unsigned ni=atomic_load_explicit(&image_count,memory_order_acquire);
  for(unsigned j=0;j<n;j++) {
    unsigned im=0;uintptr_t pc=pcs[j];
    for(;im<ni;im++)if(pc>=images[im].lo && pc<images[im].hi)break;
    if(im<ni && !images[im].own) {
      uint64_t addr=pc-images[im].base;
      if(cached->frames)cached->frames[nf]=(Frame){addr,im};
      if(j<(unsigned)depth)h=mix(h^mix(addr)^images[im].hash);nf++;
    }
  }
  h=h?h:1;cached->site_key=h;cached->signature=signature;
  if(signature)h=mix(h^mix(signature));h=h?h:1;
  cached->raw_nf=raw_nf;memcpy(cached->pcs,pcs,raw_nf*sizeof(uintptr_t));cached->raw=raw;cached->key=h;cached->live_site=NULL;cached->cls=lookup(h);cached->nf=nf;
  if(frames)memcpy(frames,cached->frames,nf*sizeof(Frame));
  if(count)*count=nf;
  if(prediction)*prediction=cached->cls;
  return h;
}
static pthread_once_t keyed_once=PTHREAD_ONCE_INIT;
static void keyed_init(void);
uint64_t jev_site_key(void) { if(none_fast)pthread_once(&keyed_once,keyed_init);busy++; uint64_t key=capture(NULL,NULL,NULL); busy--; return key; }
static unsigned lookup(uint64_t key) {
  if(!table_cap) return default_class;
  size_t i=mix(key)&(table_cap-1); while(table[i].key) {if(table[i].key==key) return table[i].cls;i=(i+1)&(table_cap-1);} return default_class;
}
static bool table_space(char c){return c==' '||c=='\t'||c=='\r'||c=='\n'||c=='\v'||c=='\f';}
static uint64_t table_number(const char** text,unsigned base) {
 const char* p=*text;uint64_t value=0;unsigned digits=0;
 while(table_space(*p))p++;
 if(base==16&&p[0]=='0'&&(p[1]=='x'||p[1]=='X'))p+=2;
 for(;;p++) {
  unsigned digit=(unsigned char)*p;
  if(digit>='0'&&digit<='9')digit-='0';
  else if(digit>='a'&&digit<='f')digit=digit-'a'+10;
  else if(digit>='A'&&digit<='F')digit=digit-'A'+10;
  else break;
  if(digit>=base)break;
  if(value>(UINT64_MAX-digit)/base)abort();
  value=value*base+digit;digits++;
 }
 if(!digits||(*p&&!table_space(*p)))abort();*text=p;return value;
}
static void load_table(const char* path) {
  if(!path||!*path)return;
  int fd=open(path,O_RDONLY|O_CLOEXEC);struct stat st;
  if(fd<0||fstat(fd,&st)){perror("JEVALLOC_TABLE");abort();}
  if(!st.st_size){close(fd);return;}
  /* A private anonymous sentinel makes parsing safe even when the file length
   * ends exactly on a page boundary, without a stdio heap allocation. */
  size_t length=(size_t)st.st_size;
  char* input=mmap(NULL,length+1,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
  if(input==MAP_FAILED)abort();size_t used=0;
  while(used<length){ssize_t n=read(fd,input+used,length-used);if(n<0&&errno==EINTR)continue;if(n<=0)abort();used+=n;}close(fd);
  size_t count=0;
  for(int pass=0;pass<2;pass++) {
    const char* p=input;while(*p) {
      while(table_space(*p))p++;
      if(!*p)break;uint64_t key=table_number(&p,16);if(!key)abort();
      uint64_t cls=table_number(&p,10);if(cls>1)abort();
      if(pass==0)count++;
      else {size_t i=mix(key)&(table_cap-1);while(table[i].key&&table[i].key!=key)i=(i+1)&(table_cap-1);table[i]=(Entry){key,(unsigned)cls};}
    }
    if(pass==0){table_cap=16;while(table_cap<count*2+1)table_cap*=2;table=mmap(NULL,table_cap*sizeof(Entry),PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);if(table==MAP_FAILED)abort();}
  }
  munmap(input,length+1);if(mprotect(table,table_cap*sizeof(Entry),PROT_READ))abort();
}

static void trace_alloc(void*,size_t,uint64_t,Frame*,unsigned,unsigned);
static void trace_free(void*);
static void trace_finish(void);
typedef struct LiveShard LiveShard;
static void live_init(void);
static inline __attribute__((always_inline)) LiveShard* live_before(KeyCache*,size_t,unsigned*);
static inline __attribute__((always_inline)) void live_alloc(void*,size_t,LiveShard*);
static inline __attribute__((always_inline)) void live_free(void*);
static void live_finish(void);
static void keyed_init(void) {
#ifdef __APPLE__
  if(pthread_key_create(&context_key,context_destroy))abort();
#endif
#ifndef __APPLE__
  context()->main_thread=true;
  ssize_t path_len=readlink("/proc/self/exe",executable_path,sizeof(executable_path)-1);
  if(path_len>0)executable_path[path_len]=0;
#endif
  busy++;
  context_enabled=!(getenv("JEVALLOC_CONTEXT") && !strcmp(getenv("JEVALLOC_CONTEXT"),"0"));
  const char* s=getenv("JEVALLOC_DEPTH");if(s)depth=atoi(s);if(depth<1)depth=1;if(depth>MAX_DEPTH)depth=MAX_DEPTH;
  s=getenv("JEVALLOC_MODEL_DEPTH");if(s)model_depth=atoi(s);if(model_depth<1)model_depth=1;if(model_depth>MAX_DEPTH)model_depth=MAX_DEPTH;
  s=getenv("JEVALLOC_SHORT_BYTES");if(s){char* end;errno=0;short_bytes=strtoull(s,&end,10);if(errno||*end||!short_bytes||*s=='-')abort();}
  s=getenv("JEVALLOC_DEFAULT");if(s)default_class=atoi(s);if(default_class<0||default_class>1)abort();
  s=getenv("JEVALLOC_POLICY");if(s && !strcmp(s,"none"))policy=1;else if(s&&!strcmp(s,"keyonly"))policy=2;else if(s&&!strcmp(s,"explicit"))policy=3;
  legacy_heaps=getenv("JEVALLOC_HEAPS")&&!strcmp(getenv("JEVALLOC_HEAPS"),"legacy");
  fail_heaps=getenv("JEVALLOC_TEST_HEAP_FAIL")!=NULL;
  s=getenv("JEVALLOC_MODE");tracing=s&&!strcmp(s,"trace");living=s&&!strcmp(s,"live");if(living)live_init();
  if(getenv("JEVALLOC_OBJECT_TRACE"))tracing=true;
#ifdef __APPLE__
  _dyld_register_func_for_add_image(image_add);
#else
  dl_iterate_phdr(image_add,NULL);
#endif
  for(unsigned i=0;i<atomic_load(&image_count);i++)if(images[i].own){own_lo=images[i].lo;own_hi=images[i].hi;}
  load_table(getenv("JEVALLOC_TABLE"));
  /* In none mode the public key API can initialize concurrently with ordinary
   * allocations. Its immutable fast-path flags already have their final values. */
  if(!none_fast){instrumented=tracing||living;ready=true;}busy--;
}
/* A disabled policy needs none of the image registry, table, or thread-key setup.
 * The public key diagnostic initializes those lazily if explicitly requested. */
__attribute__((constructor)) static void init(void) {
 const char* p=getenv("JEVALLOC_POLICY");const char* m=getenv("JEVALLOC_MODE");
 if(p&&!strcmp(p,"none")&&!(m&&(!strcmp(m,"trace")||!strcmp(m,"live")))) {
  policy=1;none_fast=true;ready=true;return;
 }
 /* Loader constructors are serialized. Only the public diagnostic's lazy
  * initialization in disabled-policy mode needs pthread_once. */
 keyed_init();
}
__attribute__((destructor)) static void finish(void) { if(tracing || living) {busy++;if(tracing)trace_finish();if(living)live_finish();busy--;} }
static void* allocate(size_t n,size_t alignment,bool zero) {
  if(!ready || busy || (none_fast)) return alignment?(zero?mi_zalloc_aligned(n,alignment):mi_malloc_aligned(n,alignment)):(zero?mi_zalloc(n):mi_malloc(n));
  if(n>PTRDIFF_MAX){errno=ENOMEM;return NULL;}
  busy++; Frame frames[MAX_DEPTH];unsigned nf=0;uint64_t key=0;unsigned cls=0;LiveShard* site=NULL;
  if(policy!=1 || tracing || living) {unsigned predicted=default_class;key=capture(tracing?frames:NULL,tracing?&nf:NULL,living?NULL:&predicted);if(policy==0)cls=predicted;else __asm__ volatile("" : : "r"(predicted));}
  if(living&&key)site=live_before(context()->active_key,n,&cls);
  mi_heap_t* heap;
  if(policy==1||policy==2)heap=mi_heap_get_default();
  else {
    if(!heaps[cls]&&!fail_heaps) {
      mi_heap_t* backing=mi_heap_get_default();
      if(mi_heap_is_initialized(backing)) {
        if(legacy_heaps||policy==3)heaps[cls]=mi_heap_new();
        else {heaps[cls]=_mi_heap_by_tag(backing,cls+1);if(!heaps[cls])heaps[cls]=mi_heap_new_ex(cls+1,false,0);}
      }
    }
    heap=heaps[cls];
    if(!heap){busy--;errno=ENOMEM;return NULL;}
  }
  void* p=alignment?(zero?mi_heap_zalloc_aligned(heap,n,alignment):mi_heap_malloc_aligned(heap,n,alignment)):(zero?mi_heap_zalloc(heap,n):mi_heap_malloc(heap,n));
  if(tracing && p)trace_alloc(p,n,key,frames,nf,cls);if(living&&p)live_alloc(p,n,site); busy--;return p;
}
void* jev_malloc(size_t n) {if(none_fast)return n<=MI_SMALL_SIZE_MAX?mi_malloc_small(n):mi_malloc(n);return allocate(n,0,false);}
void* jev_calloc(size_t n,size_t s) {if(none_fast)return mi_calloc(n,s);if(s && n>SIZE_MAX/s){errno=ENOMEM;return NULL;}return allocate(n*s,0,true);}
void jev_cfree(void* p) {if(mi_is_in_heap_region(p))jev_free(p);}
void* jev_realloc(void* p,size_t n) {if(none_fast)return mi_realloc(p,n);if(!p)return jev_malloc(n);
 size_t usable=mi_usable_size(p);
 if(n>0&&n<=usable&&n>=usable/2) {
  if(ready&&!busy&&(tracing||living)) {
   busy++;Frame frames[MAX_DEPTH];unsigned nf,cls;
   uint64_t key=capture(frames,&nf,&cls);
   if(tracing)trace_free(p);
   if(living&&key){live_free(p);LiveShard* site=live_before(context()->active_key,n,&cls);live_alloc(p,n,site);}
   if(tracing)trace_alloc(p,n,key,frames,nf,cls);
   busy--;
  }
  return p;
 }
 void* q=jev_malloc(n);if(q){memcpy(q,p,n<mi_usable_size(p)?n:mi_usable_size(p));jev_free(p);}return q;}
void* jev_malloc_aligned(size_t n,size_t a) {if(none_fast)return a?mi_malloc_aligned(n,a):mi_malloc(n);return allocate(n,a,false);}
void* jev_aligned_alloc(size_t a,size_t n) {if(!a||(a&(a-1))||n%a){errno=EINVAL;return NULL;}return allocate(n,a,false);}
int jev_posix_memalign(void** p,size_t a,size_t n) {if(a<sizeof(void*)||(a&(a-1)))return EINVAL;void* q=allocate(n,a,false);if(!q)return ENOMEM;*p=q;return 0;}
void* jev_valloc(size_t n){return allocate(n,(size_t)getpagesize(),false);}
void* jev_pvalloc(size_t n){size_t a=getpagesize();if(n>SIZE_MAX-a){errno=ENOMEM;return NULL;}return allocate((n+a-1)&~(a-1),a,false);}
void* jev_memalign(size_t a,size_t n){if(!a||(a&(a-1))){errno=EINVAL;return NULL;}return allocate(n,a,false);}
void* jev_reallocf(void* p,size_t n){void* q=jev_realloc(p,n);if(!q)jev_free(p);return q;}
void* jev_reallocarray(void* p,size_t n,size_t s){if(s&&n>SIZE_MAX/s){errno=ENOMEM;return NULL;}return jev_realloc(p,n*s);}
int jev_reallocarr(void* pp,size_t n,size_t s){void* p=jev_reallocarray(*(void**)pp,n,s);if(!p)return ENOMEM;*(void**)pp=p;return 0;}
char* jev_strndup(const char* s,size_t n){if(none_fast)return mi_strndup(s,n);size_t k=strnlen(s,n);char* p=jev_malloc(k+1);if(p){memcpy(p,s,k);p[k]=0;}return p;}
char* jev_strdup(const char* s){if(none_fast)return mi_strdup(s);return jev_strndup(s,strlen(s));}
void jev_free_size(void* p,size_t n){(void)n;jev_free(p);}
void jev_free_aligned(void* p,size_t a){(void)a;jev_free(p);}
void jev_free_size_aligned(void* p,size_t n,size_t a){(void)n;(void)a;jev_free(p);}
char* jev_realpath(const char* path,char* resolved) {
 if(resolved||none_fast)return mi_realpath(path,resolved);
 char* raw=mi_realpath(path,NULL);if(!raw)return NULL;
 char* result=jev_strdup(raw);mi_free(raw);return result;
}
/* Test diagnostics; page tags survive ownership changes. */
unsigned jev_debug_tag(const void* p){return _mi_ptr_page((void*)p)->heap_tag;}
void jev_test_fail_heaps(int enabled){fail_heaps=enabled!=0;}
/* Trace implementation is kept in the same translation unit for private state. */
#include "trace.inc"

#include "live.inc"

/* The filter already knows the page; reuse it in the core's ordinary free body.
 * Slow paths perform the final free themselves so negative probes can tail-call
 * the allocator without saving registers across instrumentation calls. */
extern void _mi_jev_free_page(void*,mi_page_t*);
static __attribute__((noinline)) void trace_free_release(void* p){busy++;trace_free(p);if(living)live_free(p);busy--;mi_free(p);}
static __attribute__((noinline)) void live_free_release(void* p,size_t h,mi_page_t* page){
 live_free_sample(p,h);if(page)_mi_jev_free_page(p,page);else mi_free(p);
}
void jev_free(void* p) {
 if(instrumented&&p&&ready&&!busy) {
  if(tracing){trace_free_release(p);return;}
  if(living) {
   mi_page_t* page=filter_mode==2?_mi_ptr_page(p):NULL;
   if(filter_maybe_sampled_page(p,page)) {
    size_t h=sample_hash(p);
    if(GET(sample_buckets[h])){live_free_release(p,h,page);return;}
   }
   if(page){_mi_jev_free_page(p,page);return;}
  }
 }
 mi_free(p);
}
#ifndef __APPLE__
/* Match upstream's direct ELF alias instead of adding a forwarding jump. */
void free(void* p) __attribute__((alias("jev_free"),used,visibility("default")));
void _ZdlPv(void* p) __attribute__((alias("jev_free"),used,visibility("default")));
void _ZdaPv(void* p) __attribute__((alias("jev_free"),used,visibility("default")));
#endif
