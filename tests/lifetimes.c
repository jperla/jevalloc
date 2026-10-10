#include <stdlib.h>
#include <stdio.h>
static volatile void* sink;
__attribute__((noinline)) static void* make(size_t n){void* p=malloc(n);if(!p)abort();sink=p;return p;}
int main(void){
 void* p=make(12345);free(p);
 p=make(23456);void* q=make(2*1024*1024);free(q);free(p);
 p=make(34567);q=make(4*1024*1024);free(q);free(p);
 sink=make(45678);puts("lifetimes OK");return 0;
}
