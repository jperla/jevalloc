#!/usr/bin/env python3
"""Mesh/non-Mesh twins and placement controls, with normal and 10-second idle."""
import argparse,copy,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,merge_schedule,schedule_path,prepare_replay
from common import sites
from context_tables import context_tables
sys.path.insert(0,str(ROOT/'fragbench'))
from realtime import definitions as context_definitions,OPTIONS
from real import definitions as real_definitions

def main():
 p=argparse.ArgumentParser();p.add_argument('--benchmarks',nargs='+');a=p.parse_args()
 assert (ROOT/'results/pass9/context.status').read_text().strip()=='0','Context measurements must complete first'
 rows=[dict(name=f'site-pure-{n}',binary='../server-sim',args=[str(n),'site-pure','400000','250'],stdin=None,expect='fragbench OK',environment=OPTIONS,prompt='stack-v1',gate_inference=True) for n in (1,16)]
 rows += [r for r in context_definitions() if r['name']!='per-alloc-small']
 rows += [r for r in real_definitions() if not r['name'].startswith('redis')]
 if a.benchmarks:
  assert not set(a.benchmarks)-{r['name'] for r in rows}
  rows=[r for r in rows if r['name'] in a.benchmarks]
 for original in rows:
  row=copy.deepcopy(original);name=row['name'];row['environment']={**row['environment'],'FRAG_LONG_SETTLE_MS':'10000'}
  out=ROOT/'results/pass9/compaction'/name;out.mkdir(parents=True,exist_ok=True);logs=out/'logs';logs.mkdir(exist_ok=True);path=out/'matrix.json'
  previous=ROOT/'results/pass9'/name/'matrix.json'
  prior=json.loads(previous.read_text()) if previous.exists() else None
  if prior:
   assert prior['complete']
   variants=list(dict.fromkeys(r['variant'] for r in prior['runs'] if r['repetition']>=0))
   tables=previous.parent/'tables'
  else:
   variants=['mi','jev-keyonly','jev-table:oracle-site']
   if name.startswith('site-pure'):variants+=['jev-live:static-model','jev-live:hybrid','jev-live:heuristic']
   tables=out/'tables'
  variants+=['mesh','nomesh']
  files=[ROOT/'build/bench'/row['binary'],ROOT/'build/libjevalloc.so',ROOT/'build/libmimalloc.so',ROOT/'build/libmesh.so',ROOT/'build/libnomesh.so',ROOT/'bench/run.py',ROOT/'fragbench/redis_workload.py',Path(__file__)]
  config=dict(row=row,variants=variants,workloads=[name],repetitions=5,long_settle_ms=10000,fingerprints={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
  d=json.loads(path.read_text()) if path.exists() else dict(name='pass9/compaction/'+name,configuration=config,runs=[],coverage_runs=[])
  if d['configuration']!=config:raise RuntimeError('Resume inputs changed: '+name)
  if d.get('complete'):continue
  def persist():save(path,d)
  if not prior and not d.get('trace_complete'):
   print(name,'TRACE',flush=True)
   trace=out/'trace.jsonl';d['trace_run']=run_one(row,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
   d['truth']=context_tables(sites(trace),tables/name);d['trace_complete']=True;persist()
  for v in variants:
   if not v.startswith('jev-live:'):continue
   schedule=schedule_path(row,v,logs)
   if not schedule.exists():
    if prior:
     source=schedule_path(row,v,previous.parent/'logs');assert source.exists();shutil.copyfile(source,schedule)
     d.setdefault('schedule_sources',{})[v]=str(source.relative_to(ROOT));persist()
    else:
     print(name,v,'COLD',flush=True)
     cold=run_one(row,v,-1,logs,tables,max_model_decisions=3000);d['runs'].append(cold);merge_schedule(schedule,ROOT/cold['decision_log']);persist()
   if any(not any(r['variant']==v and r['repetition']==rep for r in d['runs']) for rep in range(5)):
    prepare_replay(row,v,logs,tables,7200,d,path,3000)
  for rep in range(5):
   for v in variants[rep%len(variants):]+variants[:rep%len(variants)]:
    if v in d.get('failed_variants',{}):continue
    if any(r['variant']==v and r['repetition']==rep for r in d['runs']):continue
    for attempt in range(6):
     print(name,v,f'rep {rep+1}/5 attempt {attempt+1}',flush=True)
     try:r=run_one(row,v,rep,logs,tables,attempt=attempt,max_model_decisions=3000)
     except RuntimeError as error:
      if v not in ('mesh','nomesh'):raise
      d.setdefault('failed_variants',{})[v]=dict(repetition=rep,error=str(error))
      for old in d['runs']:
       if old['variant']==v:old['rejected']=True;old['rejection_reason']='variant failed in another repetition'
      persist();print(name,v,'FAILED',str(error),flush=True);r=None;break
     if not r.get('replay_missing'):break
     r['coverage_probe']=True;d['coverage_runs'].append(r);persist();prepare_replay(row,v,logs,tables,7200,d,path,3000)
    else:raise RuntimeError('Replay coverage did not converge')
    if r is None:continue
    assert any(p['phase']=='idle10' for p in r['phases']),r
    d['runs'].append(r);persist()
  d['complete']=True;persist();print(name,'COMPLETE',flush=True)
if __name__=='__main__':main()
