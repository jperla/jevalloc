"""Context isolation, bounded text, pair admission, and every-allocation dispatch."""
import json, os, socketserver, subprocess, sys, tempfile, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import environment
SOURCE=r'''
#include "jevalloc.h"
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
static pthread_mutex_t barrier_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t barrier_cond=PTHREAD_COND_INITIALIZER;
static int barrier_count,barrier_total;
static void rendezvous(void) {
 pthread_mutex_lock(&barrier_lock);
 if(++barrier_count==barrier_total)pthread_cond_broadcast(&barrier_cond);
 while(barrier_count<barrier_total)pthread_cond_wait(&barrier_cond,&barrier_lock);
 pthread_mutex_unlock(&barrier_lock);
}
__attribute__((noinline)) static void work(void) {
 for(int i=0;i<200;i++){void* p=malloc(1024);if(!p)abort();memset(p,1,1024);free(p);}
}
static void* worker(void* arg) {
 char text[400];memset(text,(int)(long)arg,sizeof(text));text[399]=0;
 if(jev_context_set)jev_context_set(text);
 rendezvous();work();
 if(jev_context_setf)jev_context_setf("kind=store ttl=%s","short");
 work();if(jev_context_clear)jev_context_clear();work();return NULL;
}
int main(int argc,char** argv) {
 barrier_total=argc>1?2:1;
 if(argc>1){pthread_t t;pthread_create(&t,NULL,worker,(void*)'B');worker((void*)'A');pthread_join(t,NULL);}
 else worker((void*)'A');return 0;
}
'''
with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='context-') as name:
 folder=Path(name);(folder/'fixture.c').write_text(SOURCE)
 subprocess.run(['cc','-g','-O0','-fno-builtin','-fno-omit-frame-pointer','-I'+str(ROOT/'src'),str(folder/'fixture.c'),'-pthread',*(['-Wl,-undefined,dynamic_lookup'] if sys.platform=='darwin' else []),'-o',str(folder/'fixture')],check=True)
 subprocess.run([str(folder/'fixture')],check=True) # weak hooks link and run without preload
 env,extra=environment('jev-trace','',folder,mode='trace',trace=folder/'trace');env.update(extra)
 subprocess.run([str(folder/'fixture'),'threads'],env=env,check=True)
 ss=[json.loads(x) for x in (folder/'trace').read_text().splitlines()]
 texts={s['context'] for s in ss};assert 'A'*255 in texts and 'B'*255 in texts and 'kind=store ttl=short' in texts and '' in texts,texts
 assert all(len(s['context'].encode())<=255 for s in ss)
 assert all(s['context_signature']=='0000000000000000' and s['site_key']==s['key'] for s in ss if not s['context'])
 for mode in ('cached','per-alloc','negotiated'):
  per_alloc=mode!='cached'
  requests=[]
  class Handler(socketserver.StreamRequestHandler):
   def handle(self):
    request=json.loads(self.rfile.readline());requests.append(request)
    # Zero deliberately: per-alloc must dispatch even without a recheck schedule.
    self.wfile.write((json.dumps(dict({'class':0,'recheck_after':0},**({'per_allocation':1} if mode=='negotiated' else {})))+'\n').encode())
  sock=folder/'service.sock';server=socketserver.ThreadingUnixStreamServer(str(sock),Handler)
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  env,extra=environment('jev-live:static-model','',folder);env.update(extra)
  env.update(JEVALLOC_DEPTH='1',JEVALLOC_PER_ALLOC=str(int(mode=='per-alloc')),JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(folder/'stats'),JEVALLOC_OBJECT_TRACE=str(folder/'objects'),JEVALLOC_TRACE_OUT=str(folder/'trace'))
  try:subprocess.run([str(folder/'fixture')],env=env,check=True,timeout=60)
  finally:server.shutdown();server.server_close();thread.join();sock.unlink()
  stats=json.loads((folder/'stats').read_text());assert stats['failures']==0,stats
  payload=[r for r in requests if r['size']==1024]
  assert len(payload)==(3*(200-64) if per_alloc else 3),(per_alloc,len(payload))
  if per_alloc:
   assert all(r.get('per_alloc') for r in (payload[1:] if mode=='negotiated' else payload))
   events=[json.loads(x) for x in (folder/'objects').read_text().splitlines()]
   decided=[e for e in events if e['event']=='alloc' and e['decided']]
   assert len(decided)==len(payload)
   for key in {r['key'] for r in payload}:
    assert [e['ordinal'] for e in decided if e['key']==key]==list(range(136))
print('CONTEXT INTEGRATION PASSED')
