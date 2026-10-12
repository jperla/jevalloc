"""Trace+live must preserve samples, cross-thread frees, reuse, and demotions."""
import json, os, socketserver, subprocess, sys, tempfile, threading
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bench'))
from run import environment
SOURCE = r'''
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
static void* held[4096];
static uintptr_t seen[8192];
__attribute__((noinline)) static void* object(void) {
 void* p=malloc(1024); if(!p) abort(); memset(p,17,1024); return p;
}
static void* producer(void* unused) {
 for(int i=0;i<4096;i++) held[i]=object();
 return NULL;
}
int main(void) {
 pthread_t t; if(pthread_create(&t,NULL,producer,NULL)) abort();
 pthread_join(t,NULL); /* sampled owner retires before another thread frees */
 for(int i=0;i<4096;i++) free(held[i]);
 unsigned reused=0;
 for(int i=0;i<8192;i++) {
  void* p=object(); seen[i]=(uintptr_t)p;
  for(int j=0;j<i;j++) if(seen[j]==seen[i]) {reused++;break;}
  free(p);
 }
 if(!reused) abort();
 printf("reused=%u\n",reused); return 0;
}
'''
with tempfile.TemporaryDirectory(dir=ROOT/'build', prefix='combined-') as name:
 folder=Path(name); (folder/'fixture.c').write_text(SOURCE)
 subprocess.run(['cc','-g','-O0','-fno-builtin','-fno-omit-frame-pointer',str(folder/'fixture.c'),'-pthread','-o',str(folder/'fixture')],check=True)
 reports=[]
 for sample in (1,64):
  paired=[]
  for logged in (False,True):
   requests=[]
   class Handler(socketserver.StreamRequestHandler):
    def handle(self):
     requests.append(json.loads(self.rfile.readline()))
     self.wfile.write(b'{"class":1,"recheck_after":0,"prior_transient":0.1,"prior_permanent":0.9}\n')
   sock=folder/'service.sock'
   server=socketserver.ThreadingUnixStreamServer(str(sock),Handler)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   env,extra=environment('jev-live:hybrid','',ROOT/'results/tables');env.update(extra)
   env.update(JEVALLOC_HYBRID='1',JEVALLOC_DEPTH='1',JEVALLOC_SAMPLE=str(sample),JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(folder/'stats.json'))
   if logged:env.update(JEVALLOC_OBJECT_TRACE=str(folder/'objects.jsonl'),JEVALLOC_TRACE_OUT=str(folder/'trace.jsonl'))
   try:result=subprocess.run([str(folder/'fixture')],env=env,check=True,capture_output=True,text=True,timeout=120)
   finally:server.shutdown();server.server_close();thread.join();sock.unlink()
   stats=json.loads((folder/'stats.json').read_text())
   assert stats['failures']==stats['rechecks']==0,stats
   keys=[k for k,b in stats['site_bytes'].items() if b==12288*1024];assert len(keys)==1,stats
   key=keys[0];row=stats['hybrid_sites'][key]
   assert row['samples']==12288//sample,row
   assert row['sampled_bytes']==row['freed_bytes']==12288*1024//sample,row
   assert stats['site_sampled_live'][key]==0,stats
   assert (row['class'],row['promotions'],row['demotions'])==(0,0,1),row
   assert sum(r['key']==key for r in requests)==1,requests
   paired.append(row)
   reports.append(dict(sample=sample,logged=logged,site=row,survivors=0,output=result.stdout))
  assert paired[0]==paired[1],paired
 out=Path(os.environ.get('JEVALLOC_TEST_REPORT_DIR',ROOT/'results/pass10/tests'));out.mkdir(parents=True,exist_ok=True)
 (out/'combined.json').write_text(json.dumps(reports,indent=2)+'\n')
print('COMBINED TRACE/LIVE PASSED')
