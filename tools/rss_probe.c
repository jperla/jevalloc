/* Linux diagnostic only: snapshot file-backed/anonymous RSS after workload exit. */
#define _GNU_SOURCE
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
__attribute__((destructor)) static void snapshot(void) {
 const char* path=getenv("JEVALLOC_SMAPS_OUT");if(!path)return;
 int in=open("/proc/self/smaps",O_RDONLY),out=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);
 if(in<0||out<0)return;
 char data[4096];ssize_t n;
 while((n=read(in,data,sizeof(data)))>0){ssize_t done=0;while(done<n){ssize_t written=write(out,data+done,n-done);if(written<=0)break;done+=written;}}
 close(in);close(out);
}
