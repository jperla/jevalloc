/* Linux x86-64 diagnostic sampler. Never use its timing/RSS as acceptance data.
 * SIGPROF records PCs without allocation or locks; symbolize after the run. */
#define _GNU_SOURCE
#include <signal.h>
#include <stdint.h>
#include <stdatomic.h>
#include <sys/time.h>
#include <ucontext.h>
#include <stdlib.h>
#include <stdio.h>
#include <dlfcn.h>
#define SLOTS 16384
static struct { _Atomic uintptr_t pc; _Atomic unsigned long count; } bins[SLOTS];
static void sample(int sig,siginfo_t* info,void* opaque) {
 (void)sig;(void)info;
 uintptr_t pc=((ucontext_t*)opaque)->uc_mcontext.gregs[REG_RIP]&~(uintptr_t)15;
 unsigned h=((pc>>4)^(pc>>20))&(SLOTS-1);
 for(unsigned n=0;n<SLOTS;n++,h=(h+1)&(SLOTS-1)) {
  uintptr_t old=atomic_load_explicit(&bins[h].pc,memory_order_relaxed);
  if(!old){atomic_compare_exchange_strong_explicit(&bins[h].pc,&old,pc,memory_order_relaxed,memory_order_relaxed);if(!old)old=pc;}
  if(old==pc){atomic_fetch_add_explicit(&bins[h].count,1,memory_order_relaxed);return;}
 }
}
__attribute__((constructor)) static void start(void) {
 struct sigaction sa={0};sa.sa_sigaction=sample;sa.sa_flags=SA_SIGINFO|SA_RESTART;sigemptyset(&sa.sa_mask);sigaction(SIGPROF,&sa,NULL);
 struct itimerval timer={{0,1000},{0,1000}};setitimer(ITIMER_PROF,&timer,NULL);
}
__attribute__((destructor)) static void finish(void) {
 struct itimerval off={0};setitimer(ITIMER_PROF,&off,NULL);
 const char* path=getenv("JEVALLOC_PROFILE_OUT");if(!path)return;FILE* f=fopen(path,"w");if(!f)return;
 for(unsigned i=0;i<SLOTS;i++){uintptr_t pc=atomic_load(&bins[i].pc);unsigned long count=atomic_load(&bins[i].count);Dl_info d;
  if(pc&&count&&dladdr((void*)pc,&d))fprintf(f,"%lu %llx %s\n",count,(unsigned long long)(pc-(uintptr_t)d.dli_fbase),d.dli_fname);
 }
 fclose(f);
}
