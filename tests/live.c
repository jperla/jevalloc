#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
static void* slots[4][12000];
static pthread_key_t release_key;
static int use_destructors,check_classes;
static unsigned (*debug_tag)(const void*);
static void release_slots(void* value){size_t t=(size_t)value-1;for(int i=0;i<12000;i++){free(slots[t][i]);slots[t][i]=NULL;}}
__attribute__((noinline)) static void* work(void* arg) {
 size_t t=(size_t)arg;
 for(int i=0;i<12000;i++){void* p=malloc(32);if(!p)abort();memset(p,(int)t,32);slots[t][i]=p;}
 if(check_classes&&debug_tag(slots[t][11999])!=1)abort();
 if(use_destructors)pthread_setspecific(release_key,(void*)(t+1));
 return NULL;
}
int main(int argc,char** argv) {
 if(argc>1&&!strcmp(argv[1],"environ")){char* original=getenv("JEVALLOC_SOCKET");if(original)memset(original,0,strlen(original));}
 check_classes=argc>1&&!strcmp(argv[1],"classes");if(check_classes){debug_tag=dlsym(RTLD_DEFAULT,"jev_debug_tag");if(!debug_tag)abort();}
 use_destructors=argc>1&&!strcmp(argv[1],"destructors");if(use_destructors)pthread_key_create(&release_key,release_slots);
 if(argc>1&&!use_destructors&&!check_classes){work(NULL);for(int i=0;i<12000;i++)free(slots[0][i]);}
 else {pthread_t threads[4];for(size_t t=0;t<4;t++)pthread_create(&threads[t],NULL,work,(void*)t);for(int t=0;t<4;t++)pthread_join(threads[t],NULL);for(int t=0;t<4;t++)for(int i=0;i<12000;i++){if(slots[t][i]&&((char*)slots[t][i])[0]!=t)abort();free(slots[t][i]);}}
 puts("live OK");return 0;
}
