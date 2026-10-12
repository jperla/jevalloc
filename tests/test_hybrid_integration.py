"""Exercise local hybrid transitions through the real allocator and socket protocol."""
import json,os,socketserver,subprocess,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import environment
SOURCE='''#include <stdlib.h>
#include <string.h>
static void* held[131072];
__attribute__((noinline)) static void work(int release){
 for(int i=0;i<131072;i++){held[i]=malloc(1024);if(!held[i])abort();memset(held[i],i,1024);}
 if(release)for(int i=0;i<131072;i++)free(held[i]);
}
int main(int argc,char** argv){work(argc>1);return 0;}
'''
with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='hybrid-integration-') as name:
 folder=Path(name);(folder/'fixture.c').write_text(SOURCE)
 subprocess.run(['cc','-g','-O0','-fno-builtin','-fno-omit-frame-pointer',str(folder/'fixture.c'),'-o',str(folder/'fixture')],check=True)
 reports=[]
 for sample in (1,64):
  for probability,release,expected,promotions,demotions in ((.9,False,0,0,0),(.6,False,1,1,0),(.1,True,0,0,1)):
   requests=[]
   class Handler(socketserver.StreamRequestHandler):
    def handle(self):
     request=json.loads(self.rfile.readline());requests.append(request)
     self.wfile.write((json.dumps({'class':int(probability<.5),'recheck_after':0,'prior_transient':probability,'prior_permanent':1-probability})+'\n').encode())
   sock=folder/'service.sock';server=socketserver.ThreadingUnixStreamServer(str(sock),Handler)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   env,extra=environment('jev-live:hybrid','',ROOT/'results/tables');env.update(extra)
   env.update(JEVALLOC_HYBRID='1',JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(folder/'stats.json'),JEVALLOC_SAMPLE=str(sample))
   try:subprocess.run([str(folder/'fixture'),*(['release'] if release else [])],env=env,check=True,timeout=120)
   finally:server.shutdown();server.server_close();thread.join();sock.unlink()
   stats=json.loads((folder/'stats.json').read_text());assert stats['failures']==stats['rechecks']==0,stats
   target=[k for k,b in stats['site_bytes'].items() if b==131072*1024];assert len(target)==1,stats
   row=stats['hybrid_sites'][target[0]]
   assert (row['class'],row['promotions'],row['demotions'])==(expected,promotions,demotions),row
   assert row['samples']==131072//sample and row['freed_bytes']==(131072*1024//sample if release else 0),row
   assert len([r for r in requests if r['key']==target[0]])==1
   reports.append(dict(sample=sample,prior=probability,release=release,site=row))
 out=Path(os.environ.get('JEVALLOC_TEST_REPORT_DIR',ROOT/'results/pass8'));out.mkdir(exist_ok=True,parents=True);(out/'hybrid-integration.json').write_text(json.dumps(reports,indent=2))
print('HYBRID INTEGRATION PASSED')
