#!/usr/bin/env python3
"""One greedy pass over 24 byte-heavy sites, then independent interleaved runs.

Search measurements (three per candidate) are training data, not headline RSS.
The final five-run table comparison gates model collection for each workload.
"""
import argparse,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,merge_schedule,schedule_path,prepare_replay
from common import sites,oracle,write_table
from symbolize import symbolize
sys.path.insert(0,str(ROOT/'fragbench'))
from real import definitions,OPTIONS

def idle(run):
 phases=[p for p in run['phases'] if p['phase']=='idle']
 if not phases:raise RuntimeError('missing idle measurement')
 return max(phases,key=lambda p:p.get('cycle',0))['rss_bytes']

def main():
 p=argparse.ArgumentParser();p.add_argument('--benchmarks',nargs='+');a=p.parse_args()
 rows=definitions()
 for mode in ('mesh','drop'):rows.append(dict(name='redis-'+mode,binary='redis-server',args=['--activedefrag','no'],stdin=None,expect='fragbench OK',redis_driver=mode,environment=OPTIONS,prompt='stack-v1',gate_inference=True))
 if a.benchmarks:rows=[r for r in rows if r['name'] in a.benchmarks]
 for row in rows:
  out=ROOT/'results/pass8/real'/row['name'];out.mkdir(parents=True,exist_ok=True)
  logs=out/'logs';tables=out/'tables';table=tables/row['name'];path=out/'matrix.json'
  files=[ROOT/'build/bench'/row['binary'],ROOT/'build/libjevalloc.so',ROOT/'build/libmimalloc.so',ROOT/'bench/run.py',ROOT/'tools/jevd.py',ROOT/'fragbench/headroom.py',ROOT/'fragbench/real.py',ROOT/'fragbench/redis_workload.py']
  files += [ROOT/'fragbench'/name for name in ('sqlite-driver.c','leveldb-driver.cc','phase.h')]
  files += [ROOT/'tools'/name for name in ('prompts.py','symbolize.py','patch_rocksdb.py')]
  files += sorted((ROOT/'descriptions').glob('*.txt'))
  config=dict(row=row,idle_metric='final-idle',repetitions=5,search_repetitions=3,top_sites=24,keep_threshold=.02,headroom_threshold=.05,prompt='stack-v1',max_model_decisions=1500,fingerprints={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
  data=json.loads(path.read_text()) if path.exists() else dict(name='pass8/'+row['name'],configuration=config,runs=[],coverage_runs=[],search_runs=[],search_steps=[])
  if data['configuration']!=config:raise RuntimeError('Resume inputs changed: '+row['name'])
  if data.get('complete'):continue
  def persist():save(path,data)
  trace=out/'trace.jsonl'
  if not data.get('trace_complete'):
   print(row['name'],'TRACE',flush=True)
   data['trace_run']=run_one(row,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
   ss=sites(trace);write_table(table/'oracle.txt',[(s['key'],oracle(s)) for s in ss]);write_table(table/'all-transient.txt',[(s['key'],0) for s in ss])
   top=sorted(ss,key=lambda s:(-s['bytes'],s['key']))[:24];symbolize(top)
   data['top_sites']=top;data['trace_complete']=True;persist()
  ss=sites(trace)
  labels={s['key']:0 for s in ss}
  for step in data['search_steps']:
   if step['accepted']:labels[step['key']]=1
  def trial(tag,values):
   write_table(table/(tag+'.txt'),values.items());variant='jev-table:'+tag
   runs=[r for r in data['search_runs'] if r['variant']==variant]
   for rep in range(len(runs),3):
    print(row['name'],variant,f'rep {rep+1}/3',flush=True)
    r=run_one(row,variant,rep,logs/'search',tables);data['search_runs'].append(r);runs.append(r);persist()
   return statistics.median(map(idle,runs))
  if 'search_baseline' not in data:data['search_baseline']=trial('search-base',labels);persist()
  best=data['search_steps'][-1]['best_after'] if data['search_steps'] else data['search_baseline']
  for index,site in enumerate(data['top_sites']):
   if index<len(data['search_steps']):continue
   candidate={**labels,site['key']:1};rss=trial(f'search-{index:02}',candidate);accepted=rss<best*.98
   data['search_steps'].append(dict(key=site['key'],bytes=site['bytes'],frames=site['frames'],candidate_rss=rss,best_before=best,best_after=rss if accepted else best,accepted=accepted))
   if accepted:labels=candidate;best=rss
   persist()
  write_table(table/'search.txt',labels.items())
  controls=['mi','jev-table:oracle','jev-table:search']
  def warm(variants):
   for rep in range(5):
    for variant in variants[rep%len(variants):]+variants[:rep%len(variants)]:
     if any(r['variant']==variant and r['repetition']==rep for r in data['runs']):continue
     for attempt in range(6):
      print(row['name'],variant,f'rep {rep+1}/5 attempt {attempt+1}',flush=True)
      r=run_one(row,variant,rep,logs,tables,attempt=attempt)
      if not r.get('replay_missing'):break
      r['coverage_probe']=True;data['coverage_runs'].append(r);persist();prepare_replay(row,variant,logs,tables,7200,data,path)
     else:raise RuntimeError('Replay coverage did not converge')
     data['runs'].append(r);persist()
  warm(controls)
  medians={v:statistics.median(idle(r) for r in data['runs'] if r['variant']==v and r['repetition']>=0) for v in controls}
  data.setdefault('headroom',dict(idle_rss=medians,eligible=min(medians[v] for v in controls[1:])<medians['mi']*.95))
  persist()
  if data['headroom']['eligible']:
   models=['jev-live:static-model','jev-live:hybrid','jev-live:heuristic']
   for variant in models:
    if not any(r['variant']==variant and r['repetition']==-1 for r in data['runs']):
     print(row['name'],variant,'COLD',flush=True);r=run_one(row,variant,-1,logs,tables);data['runs'].append(r);persist()
    cold=next(r for r in data['runs'] if r['variant']==variant and r['repetition']==-1)
    merge_schedule(schedule_path(row,variant,logs),ROOT/cold['decision_log']);prepare_replay(row,variant,logs,tables,7200,data,path)
   # Interleave new baseline/table observations with the model variants. Keep the
   # headroom gate measurements separately to avoid doubling the published n.
   if not data.get('gate_runs'):
    data['gate_runs']=[r for r in data['runs'] if r['repetition']>=0];data['runs']=[r for r in data['runs'] if r['repetition']<0];persist()
   warm(controls+models)
  data['complete']=True;persist()
  print(row['name'],'COMPLETE',data['headroom'],flush=True)
if __name__=='__main__':main()
