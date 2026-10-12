"""Bound state before admission, with active owners and cross-thread frees."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import environment
SOURCE=r'''
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "jevalloc.h"
#define N 8192
#define T 8
static unsigned char* held[T][N];
static pthread_barrier_t boundary;
static int shared;
__attribute__((noinline)) static void* object(void) {return malloc(128);}
static void* worker(void* arg) {
 size_t id=(size_t)arg;
 for(int i=0;i<N;i++) {
  char text[80];snprintf(text,sizeof(text),"key=%zu-%d",id,i);jev_context_set(shared?"shared":text);
  held[id][i]=object();if(!held[id][i])abort();memset(held[id][i],(int)(id+1),128);
 }
 pthread_barrier_wait(&boundary);
 size_t other=(id+1)%T;
 for(int i=0;i<N;i++) {
  for(int j=0;j<128;j++)if(held[other][i][j]!=other+1)abort();
  free(held[other][i]);
 }
 /* Force continued allocation after every limit has been exceeded. */
 for(int i=0;i<N;i++){void* p=object();if(!p)abort();memset(p,42,128);free(p);}
 pthread_barrier_wait(&boundary);
 for(;;)sleep(1); /* active owners must remain budgeted at exit */
}
int main(int argc,char** argv) {
 shared=argc>1;
 pthread_t threads[T];pthread_barrier_init(&boundary,NULL,T+1);
 for(size_t i=0;i<T;i++)if(pthread_create(&threads[i],NULL,worker,(void*)i))abort();
 pthread_barrier_wait(&boundary);pthread_barrier_wait(&boundary);
 puts("limits cross-thread OK");return 0;
}
'''
# macOS has no native pthread barriers: use the Linux test machine for this test.
if sys.platform!='linux':
 print('live limits: Linux pthread-barrier fixture; run on test machine');sys.exit(0)
with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='limits-') as d:
 p=Path(d);(p/'test.c').write_text(SOURCE)
 subprocess.run(['cc','-O0','-g','-fno-builtin','-fno-omit-frame-pointer','-I'+str(ROOT/'src'),str(p/'test.c'),'-pthread','-o',str(p/'test')],check=True)
 reports=[]
 for label,pairs,contexts,budget in [('contexts',1024,4,4*1024*1024),('pairs',12,100000,4*1024*1024),('bytes',10000,100000,65536),('shared-shards',10000,1,65536),('zero',0,64,0)]:
  env,extra=environment('jev-live:hybrid','',p);env.update(extra)
  env.update(JEVALLOC_DEPTH='1',JEVALLOC_MIN_SITE_BYTES=str(2**60),JEVALLOC_SAMPLE='1',JEVALLOC_HYBRID='1',JEVALLOC_MAX_PAIRS=str(pairs),JEVALLOC_MAX_CONTEXTS=str(contexts),JEVALLOC_MAX_METADATA_BYTES=str(budget),JEVALLOC_STATS_OUT=str(p/'stats.json'))
  result=subprocess.run([str(p/'test')]+(['shared'] if label=='shared-shards' else []),env=env,capture_output=True,text=True,check=True,timeout=120)
  stats=json.loads((p/'stats.json').read_text());m=stats['metadata']
  assert 'limits cross-thread OK' in result.stdout
  assert m['pairs']<=pairs and m['bytes']<=m['peak_bytes']<=budget,m
  assert m['max_observed_contexts']<=contexts,m
  if label!='shared-shards':
   assert m['overflow_allocations']>8*8192-1000,m
   assert m['overflow_bytes']>=128*(8*8192-1000),m
  else:
   assert m['peak_shards']>m['pairs'],m
   assert m['sample_overflows']>0,m
  assert stats['failures']==0,stats
  if label=='contexts':assert m['pairs']<=4+16,m
  if label=='pairs':assert m['pairs']==pairs,m
  if label=='zero':assert m['bytes']==m['peak_shards']==0,m
  reports.append(dict(case=label,metadata=m,samples=stats['samples'],survivors=stats['sampled_live_objects']))
 out=Path(os.environ.get('JEVALLOC_TEST_REPORT_DIR',ROOT/'results/pass11/tests'));out.mkdir(parents=True,exist_ok=True)
 (out/'live-limits.json').write_text(json.dumps(reports,indent=2)+'\n')
print('LIVE METADATA LIMITS PASSED')
