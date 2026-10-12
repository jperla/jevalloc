#!/usr/bin/env python3
"""Pass 9: context controls, Redis greedy gate, and exact per-allocation truth."""
import argparse,copy,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,merge_schedule,schedule_path,prepare_replay
from common import sites,write_table
from context_tables import context_tables
from symbolize import symbolize
OPTIONS={'MIMALLOC_PURGE_DELAY':'0','MIMALLOC_ARENA_PURGE_MULT':'1','MIMALLOC_PURGE_DECOMMITS':'1','JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12'}
def idle(run):return max((p for p in run['phases'] if p['phase']=='idle'),key=lambda p:p.get('cycle',0))['rss_bytes']
def definitions():
 common=dict(stdin=None,expect='fragbench OK',environment=OPTIONS,gate_inference=True,prompt='stack-v1')
 rows=[dict(common,name=f'site-mixed-{n}',binary='../server-sim',args=[str(n),'site-mixed','400000','250']) for n in (1,16)]
 rows += [dict(common,name='redis-'+mode,binary='redis-context-server',args=['--activedefrag','no'],redis_driver=mode) for mode in ('mesh','drop','sessions')]
 rows += [dict(common,name='per-alloc-small',binary='../server-sim',args=['1','site-mixed','1200','250','payload-only'])]
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--benchmarks',nargs='+');a=p.parse_args()
 rows=definitions()
 if a.benchmarks:
  assert not set(a.benchmarks)-{r['name'] for r in rows}
  rows=[r for r in rows if r['name'] in a.benchmarks]
 for row in rows:
  name=row['name'];out=ROOT/'results/pass9'/name;out.mkdir(parents=True,exist_ok=True)
  logs=out/'logs';tables=out/'tables';table=tables/name;path=out/'matrix.json'
  files=[ROOT/'build/bench'/row['binary'],ROOT/'build/libjevalloc.so',ROOT/'build/libmimalloc.so',ROOT/'tools/jevd.py',ROOT/'tools/prompts.py',ROOT/'bench/run.py',Path(__file__),ROOT/'fragbench/redis_workload.py']
  files += sorted((ROOT/'descriptions').glob('*.txt'))
  config=dict(row=row,idle_metric='final-idle',repetitions=5,search_repetitions=3,top_pairs=24,max_model_decisions=3000,fingerprints={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
  data=json.loads(path.read_text()) if path.exists() else dict(name='pass9/'+name,configuration=config,runs=[],coverage_runs=[],search_runs=[],search_steps=[])
  if config!=data['configuration']:raise RuntimeError('Resume inputs changed: '+name)
  if data.get('complete'):continue
  def persist():save(path,data)
  trace=out/'trace.jsonl';ss=None
  if not data.get('trace_complete'):
   print(name,'TRACE',flush=True)
   data['trace_run']=run_one(row,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
   ss=sites(trace);data['truth']=context_tables(ss,table)
   top=sorted(ss,key=lambda s:(-s['bytes'],s['key']))[:24];symbolize(top)
   data['top_pairs']=top;data['trace_complete']=True;persist()
  if ss is None:ss=sites(trace)
  controls=['mi','jev-keyonly','jev-table:oracle-site','jev-table:oracle-context']
  if row.get('redis_driver'):
   labels={s['key']:0 for s in ss}
   for step in data['search_steps']:
    if step['accepted']:labels[step['key']]=1
   def trial(tag,values):
    write_table(table/(tag+'.txt'),values.items());variant='jev-table:'+tag
    runs=[r for r in data['search_runs'] if r['variant']==variant]
    for rep in range(len(runs),3):
     print(name,variant,f'rep {rep+1}/3',flush=True)
     r=run_one(row,variant,rep,logs/'search',tables);data['search_runs'].append(r);runs.append(r);persist()
    return statistics.median(map(idle,runs))
   if 'search_baseline' not in data:data['search_baseline']=trial('search-base',labels);persist()
   best=data['search_steps'][-1]['best_after'] if data['search_steps'] else data['search_baseline']
   for index,site in enumerate(data['top_pairs']):
    if index<len(data['search_steps']):continue
    candidate={**labels,site['key']:1};rss=trial(f'search-{index:02}',candidate);accepted=rss<best*.98
    data['search_steps'].append(dict(key=site['key'],context=site['context'],bytes=site['bytes'],frames=site['frames'],candidate_rss=rss,best_before=best,best_after=rss if accepted else best,accepted=accepted))
    if accepted:labels=candidate;best=rss
    persist()
   write_table(table/'search.txt',labels.items());controls.append('jev-table:search')
  def runrow(v,rep):
   r=copy.deepcopy(row)
   if v=='jev-live:per-alloc':
    r['environment']={**r['environment'],'JEVALLOC_OBJECT_TRACE':str(logs/f'objects-{rep}.jsonl'),'JEVALLOC_TRACE_OUT':str(logs/f'objects-{rep}.trace.jsonl')}
   return r
  def warm(variants):
   for rep in range(5):
    for variant in variants[rep%len(variants):]+variants[:rep%len(variants)]:
     if any(r['variant']==variant and r['repetition']==rep for r in data['runs']):continue
     for attempt in range(6):
      print(name,variant,f'rep {rep+1}/5 attempt {attempt+1}',flush=True)
      r=run_one(runrow(variant,rep),variant,rep,logs,tables,attempt=attempt,max_model_decisions=3000)
      if not r.get('replay_missing'):break
      r['coverage_probe']=True;data['coverage_runs'].append(r);persist();prepare_replay(runrow(variant,-2),variant,logs,tables,7200,data,path,3000)
     else:raise RuntimeError('Replay coverage did not converge')
     data['runs'].append(r);persist()
  if 'headroom' not in data:
   warm(controls)
   medians={v:statistics.median(idle(r) for r in data['runs'] if r['variant']==v and r['repetition']>=0) for v in controls}
   data['headroom']=dict(idle_rss=medians,eligible=min(medians[v] for v in controls if v.startswith('jev-table:') and v!='jev-table:oracle-site')<medians['mi']*.95);persist()
  models=['jev-live:static-site','jev-live:static-model','jev-live:hybrid','jev-live:heuristic']
  if name=='per-alloc-small':models=['jev-live:per-alloc']
  if not row.get('redis_driver') or data['headroom']['eligible']:
   for variant in models:
    if not any(r['variant']==variant and r['repetition']==-1 for r in data['runs']):
     print(name,variant,'COLD',flush=True)
     r=run_one(runrow(variant,-1),variant,-1,logs,tables,max_model_decisions=3000);data['runs'].append(r);persist()
    cold=next(r for r in data['runs'] if r['variant']==variant and r['repetition']==-1)
    merge_schedule(schedule_path(row,variant,logs),ROOT/cold['decision_log'])
    prepare_replay(runrow(variant,-2),variant,logs,tables,7200,data,path,3000)
   if not data.get('gate_runs'):
    data['gate_runs']=[r for r in data['runs'] if r['repetition']>=0];data['runs']=[r for r in data['runs'] if r['repetition']<0];persist()
   warm(controls+models)
  data['complete']=True;persist();print(name,'COMPLETE',data['headroom'],flush=True)
if __name__=='__main__':main()
