#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static void* slots[4][12000];
__attribute__((noinline)) static void* work(void* arg) {
 size_t t=(size_t)arg;
 for(int i=0;i<12000;i++){void* p=malloc(32);if(!p)abort();memset(p,(int)t,32);slots[t][i]=p;}
 return NULL;
}
int main(int argc,char** argv) {
 if(argc>1){work(NULL);for(int i=0;i<12000;i++)free(slots[0][i]);}
 else {pthread_t threads[4];for(size_t t=0;t<4;t++)pthread_create(&threads[t],NULL,work,(void*)t);for(int t=0;t<4;t++)pthread_join(threads[t],NULL);for(int t=0;t<4;t++)for(int i=0;i<12000;i++){if(((char*)slots[t][i])[0]!=t)abort();free(slots[t][i]);}}
 puts("live OK");return 0;
}
