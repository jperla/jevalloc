#include <stdint.h>
#include <stdio.h>
#include <dlfcn.h>
#include <time.h>
#include <stdlib.h>
static uint64_t (*key)(void);
__attribute__((noinline)) static uint64_t a(void){__asm__ volatile("nop");return key();}
__attribute__((noinline)) static uint64_t b(void){__asm__ volatile("nop; nop");return key();}
__attribute__((noinline)) static uint64_t c(void){return a();}
__attribute__((noinline)) static uint64_t d(void){return c();}
__attribute__((noinline)) static uint64_t e(void){return d();}
int main(int argc,char** argv){key=dlsym(RTLD_DEFAULT,"jev_site_key");if(!key)return 1;
 if(argc>1){int n=5000000;struct timespec x,y;clock_gettime(CLOCK_MONOTONIC,&x);uint64_t sum=0;for(int i=0;i<n;i++)sum^=e();clock_gettime(CLOCK_MONOTONIC,&y);printf("%.3f ns/key %llu\n",((y.tv_sec-x.tv_sec)*1e9+y.tv_nsec-x.tv_nsec)/n,(unsigned long long)sum);}
 else printf("%016llx %016llx\n",(unsigned long long)a(),(unsigned long long)b());return 0;}
