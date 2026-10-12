#ifndef FRAGBENCH_PHASE_H
#define FRAGBENCH_PHASE_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
static void frag_phase(const char* phase,uint64_t live,const char* metric) {
 unsigned long total=0,resident=0;FILE* f=fopen("/proc/self/statm","r");
 if(!f || fscanf(f,"%lu %lu",&total,&resident)!=2){perror("statm");_exit(2);}fclose(f);
 unsigned long long rss=(unsigned long long)resident*sysconf(_SC_PAGESIZE);
 printf("{\"phase\":\"%s\",\"cycle\":0,\"rss_bytes\":%llu,\"live_bytes\":%llu,\"live_metric\":\"%s\",\"fragmentation_ratio\":%.6f}\n",phase,rss,(unsigned long long)live,metric,live?(double)rss/live:0);fflush(stdout);
 const char* longer=getenv("FRAG_LONG_SETTLE_MS");
 if(longer&&!strcmp(phase,"idle")){
  int ms=atoi(longer)-500;if(ms>0)usleep((unsigned)ms*1000);
  frag_phase("idle10",live,metric);
 }
}
#endif
