/* Allocation/free pair calibration; -fno-builtin prevents removal of the work. */
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <time.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
int main(void){const int n=5000000;uintptr_t sum=0;double start=now();for(int i=0;i<n;i++){void* p=malloc(32);if(!p)return 1;((char*)p)[0]=(char)i;sum^=(uintptr_t)p;free(p);}printf("%.3f %llu\n",(now()-start)*1e9/n,(unsigned long long)sum);}
