#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static void* held[5000];
static void* (*heap_new)(int,int,int);
static void* (*heap_alloc)(void*,size_t);
static unsigned (*tag)(const void*);
static void (*fail)(int);
static void* (*raw_malloc)(size_t);
static void* worker(void* unused) {
 (void)unused;
 void* old=malloc(64);assert(old);memset(old,37,64);
 assert(realloc(old,48)==old);free(old);
 void* heaps[2];for(int c=0;c<2;c++){heaps[c]=heap_new(c+1,0,0);assert(heaps[c]);}
 for(int i=0;i<5000;i++){held[i]=heap_alloc(heaps[i%2],128);assert(held[i]);assert(tag(held[i])==(unsigned)(i%2+1));}
 return NULL;
}
static void* failed_heap(void* unused) {
 (void)unused;void* old=NULL;assert(posix_memalign(&old,64,256)==0);memset(old,42,256);
 /* Existing class heap is intentionally present here; use a fresh thread below
  * for first-heap failure, and the size limit to test realloc preservation. */
 volatile size_t huge=(size_t)PTRDIFF_MAX+1;errno=0;assert(realloc(old,huge)==NULL);assert(errno==ENOMEM);assert(((char*)old)[0]==42);free(old);return NULL;
}
static void* no_heap(void* unused) {
 (void)unused;void* old=raw_malloc(64);assert(old);memset(old,51,64);fail(1);
 assert(realloc(old,1024)==NULL);assert(((unsigned char*)old)[0]==51);free(old);
 for(int i=0;i<2048;i++){errno=0;assert(malloc(123)==NULL&&errno==ENOMEM);}
 errno=0;assert(calloc(1,123)==NULL&&errno==ENOMEM);
 void* p=(void*)(uintptr_t)123;assert(posix_memalign(&p,64,128)==ENOMEM);assert(p==(void*)(uintptr_t)123);
 assert(aligned_alloc(64,128)==NULL);fail(0);return NULL;
}
int main(int argc,char** argv) {
 (void)argv;
 raw_malloc=dlsym(RTLD_DEFAULT,"mi_malloc");assert(raw_malloc);
 heap_new=dlsym(RTLD_DEFAULT,"mi_heap_new_ex");heap_alloc=dlsym(RTLD_DEFAULT,"mi_heap_malloc");assert(heap_new&&heap_alloc);
 tag=dlsym(RTLD_DEFAULT,"jev_debug_tag");fail=dlsym(RTLD_DEFAULT,"jev_test_fail_heaps");assert(tag&&fail);
 pthread_t t;
 if(argc>1){assert(!pthread_create(&t,NULL,no_heap,NULL));pthread_join(t,NULL);puts("failed allocations OK");return 0;}
 assert(!pthread_create(&t,NULL,worker,NULL));pthread_join(t,NULL);
 /* Receiving thread initially has no class heap. Reclaim must create one with
  * the abandoned page's tag before allocating into that page. */
 for(int i=0;i<5000;i++){assert(tag(held[i])==(unsigned)(i%2+1));free(held[i]);void* p=malloc(128);assert(p);assert(tag(p)==1);free(p);}
 assert(!pthread_create(&t,NULL,failed_heap,NULL));pthread_join(t,NULL);
 /* Set the injection in the worker after pthread startup allocations. */
 assert(!pthread_create(&t,NULL,no_heap,NULL));pthread_join(t,NULL);
 puts("defects OK");return 0;
}
