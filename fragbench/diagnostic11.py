#!/usr/bin/env python3
"""Matched histories and allocator statistics; separate MI_STAT=2 build."""
import copy,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'fragbench'),str(ROOT/'tools'),str(ROOT/'bench')]
from review3 import BASE,OPTIONS,write,load,collect,check,audit
from run import run_one,schedule_path
from common import sites
from context_tables import context_tables
HOOK=r'''
#include "mimalloc-stats.h"
#pragma weak mi_stats_get
#pragma weak mi_stats_merge
#pragma weak mi_collect
#pragma weak mi_heap_collect
#pragma weak mi_heap_get_default
#pragma weak mi_heap_visit_blocks
extern mi_heap_t* _mi_heap_by_tag(mi_heap_t*,uint8_t) __attribute__((weak));
static size_t area_committed,area_used,empty_committed;
static bool visit(const mi_heap_t* heap,const mi_heap_area_t* area,void* block,size_t size,void* arg) {
 (void)heap;(void)block;(void)size;(void)arg;
 area_committed+=area->committed;area_used+=area->used*area->block_size;
 if(!area->used)empty_committed+=area->committed;
 return true;
}
static void allocator_stats(int cycle,const char* phase) {
 if(!mi_stats_get||!mi_stats_merge)abort();
 area_committed=area_used=empty_committed=0;
 mi_heap_t* heap=mi_heap_get_default();mi_heap_visit_blocks(heap,false,visit,NULL);
 if(_mi_heap_by_tag)for(int tag=1;tag<=2;tag++) {
  mi_heap_t* h=_mi_heap_by_tag(heap,(uint8_t)tag);
  if(h&&h!=heap)mi_heap_visit_blocks(h,false,visit,NULL);
 }
 mi_stats_merge();mi_stats_t s;mi_stats_get(sizeof(s),&s);
 printf("{\"mi_phase\":\"%s\",\"cycle\":%d,\"reserved\":%lld,\"committed\":%lld,\"purged\":%lld,\"page_committed\":%lld,\"malloc_current\":%lld,\"area_committed\":%zu,\"area_used\":%zu,\"empty_area_committed\":%zu}\n",phase,cycle,(long long)s.reserved.current,(long long)s.committed.current,(long long)s.purged.total,(long long)s.page_committed.current,(long long)(s.malloc_normal.current+s.malloc_huge.current),area_committed,area_used,empty_committed);
 fflush(stdout);
}
'''
def build():
 build=ROOT/'build/pass11-stats'
 subprocess.run(['cmake','-S',str(ROOT),'-B',str(build),'-DCMAKE_C_FLAGS=-DMI_STAT=2'],check=True)
 subprocess.run(['cmake','--build',str(build),'--target','jevalloc','mimalloc','-j8'],check=True)
 source=(ROOT/'fragbench/server-sim.c').read_text().replace('../src/jevalloc.h',str(ROOT/'src/jevalloc.h'))
 source=source.replace('static void emit(int cycle,const char* name) {',HOOK+'\nstatic void emit(int cycle,const char* name) {')
 source=source.replace('fflush(stdout);\n}', 'fflush(stdout);allocator_stats(cycle,name);\n}')
 source=source.replace('pthread_barrier_wait(&boundary);if(id==0)emit(cycle,"idle10");pthread_barrier_wait(&boundary);', '''pthread_barrier_wait(&boundary);if(id==0)emit(cycle,"idle10");pthread_barrier_wait(&boundary);
  if(cycle==1&&getenv("FRAG_COLLECT")) {
   mi_collect(true);if(id==0)emit(cycle,"collected-default");
   mi_heap_t* heap=mi_heap_get_default();
   if(_mi_heap_by_tag)for(int tag=1;tag<=2;tag++){mi_heap_t* h=_mi_heap_by_tag(heap,(uint8_t)tag);if(h&&h!=heap)mi_heap_collect(h,true);}
   if(id==0)emit(cycle,"collected-all-heaps");
  }''')
 # Hook's own fflush must not call itself; replacement above only matches final newline-brace.
 source=source.replace('fflush(stdout);allocator_stats(cycle,name);\n}\n\nstatic void emit','fflush(stdout);\n}\n\nstatic void emit')
 dest=ROOT/'build/pass11/server-sim-diag.c';dest.write_text(source)
 subprocess.run(['cc','-O3','-g','-fno-builtin','-fno-omit-frame-pointer','-fno-optimize-sibling-calls','-fno-ipa-icf','-I'+str(ROOT/'third_party/mimalloc/include'),str(dest),'-pthread','-o',str(ROOT/'build/server-sim-diag')],check=True)
 shutil.copyfile(ROOT/'descriptions/server-sim.txt',ROOT/'descriptions/server-sim-diag.txt')
def main():
 build()
 for options in ('defaults','immediate'):
  out=BASE/'diagnostic'/options;out.mkdir(parents=True,exist_ok=True);tables=out/'tables'
  row=dict(name='site-pure-1',binary='../server-sim-diag',args=['1','site-pure','400000','250'],stdin=None,expect='fragbench OK',gate_inference=True,prompt='stack-v1',environment={'JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12','FRAG_LONG_SETTLE_MS':'10000'})
  if options=='immediate':row['environment'].update(OPTIONS)
  path=out/'matrix.json';files=[ROOT/'build/server-sim-diag',ROOT/'build/pass11-stats/libjevalloc.so',ROOT/'build/pass11-stats/libmimalloc.so',Path(__file__)]
  data=load(path,dict(row=row,statistics='MI_STAT=2; heap areas traversed at each phase',fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))
  if data.get('complete'):continue
  logs=out/'logs';logs.mkdir(exist_ok=True)
  if 'trace' not in data:
   rr=copy.deepcopy(row);rr['environment']['LD_PRELOAD']=str(ROOT/'build/pass11-stats/libjevalloc.so')
   trace=out/'trace.jsonl';data['trace']=run_one(rr,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
   data['truth']=context_tables(sites(trace),tables/row['name']);write(path,data)
  rr=copy.deepcopy(row);rr['environment']['LD_PRELOAD']=str(ROOT/'build/pass11-stats/libjevalloc.so')
  source=collect(rr,'jev-live:static-model',out/'collection')
  shutil.copyfile(source,schedule_path(rr,'jev-live:static-model',logs))
  for forced in (False,True):
   for variant in ('mi','jev-table:oracle-site','jev-live:static-model'):
    label=variant+('/collect' if forced else '/ordinary')
    if any(r['variant']==label for r in data['runs']):continue
    r=copy.deepcopy(row);r['environment']['LD_PRELOAD']=str(ROOT/'build/pass11-stats'/('libmimalloc.so' if variant=='mi' else 'libjevalloc.so'))
    if forced:r['environment']['FRAG_COLLECT']='1'
    result=run_one(r,variant,int(forced),logs,tables);check(result)
    result['allocator_phases']=[json.loads(line) for line in (ROOT/result['stdout']).read_text().splitlines() if line.startswith('{"mi_phase":')]
    assert len(result['allocator_phases'])==len(result['phases'])
    result.update(variant=label,transport_variant=variant,diagnostic=True,forced_collection=forced);data['runs'].append(result);write(path,data)
  data['complete']=True;write(path,data);audit(path)
if __name__=='__main__':main()
