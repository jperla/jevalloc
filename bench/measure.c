/* Fallback for sandboxed macOS time -l, whose kern.clockrate sysctl is denied.
 * wait4 supplies exact CPU/RSS. proc_pid_rusage supplies lifetime footprint peak. */
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <errno.h>
#ifdef __APPLE__
#include <libproc.h>
#endif
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
int main(int argc,char** argv){
 if(argc<3)return 2;
 double start=now();pid_t pid=fork();if(pid<0)return 2;if(!pid){execvp(argv[2],argv+2);_exit(127);}
 uint64_t footprint=0;int footprint_ok=0,zombie_ok=0;
 for(;;){
  siginfo_t si={0};int rc=waitid(P_PID,pid,&si,WEXITED|WNOHANG|WNOWAIT);
  if(rc<0&&errno!=EINTR)return 3;
#ifdef __APPLE__
  struct rusage_info_v4 ri={0};
  if(proc_pid_rusage(pid,RUSAGE_INFO_V4,(rusage_info_t*)&ri)==0){footprint_ok=1;if(ri.ri_lifetime_max_phys_footprint>footprint)footprint=ri.ri_lifetime_max_phys_footprint;if(si.si_pid)zombie_ok=1;}
#endif
  if(si.si_pid)break;
  struct timespec pause={0,1000000};nanosleep(&pause,NULL);
 }
 int status;struct rusage r;while(wait4(pid,&status,0,&r)<0)if(errno!=EINTR)return 4;
 int child_status=WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status);
 FILE* f=fopen(argv[1],"w");if(!f)return 5;
 long long rss=r.ru_maxrss;
#ifndef __APPLE__
 rss*=1024;
#endif
 fprintf(f,"{\"exit_status\":%d,\"wall_seconds\":%.9f,\"user_seconds\":%.6f,\"sys_seconds\":%.6f,\"peak_rss_bytes\":%lld,\"peak_footprint_bytes\":",child_status,now()-start,r.ru_utime.tv_sec+r.ru_utime.tv_usec/1e6,r.ru_stime.tv_sec+r.ru_stime.tv_usec/1e6,rss);
 if(footprint_ok)fprintf(f,"%llu",(unsigned long long)footprint);else fputs("null",f);
 fprintf(f,",\"footprint_final_read\":%s,\"measurement\":\"wait4 + proc_pid_rusage\"}\n",zombie_ok?"true":"false");fclose(f);
 return WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status);
}
