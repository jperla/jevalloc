#!/usr/bin/env python3
"""Predeclared pass-11 experiments. Design lives in results/pass11/design.json."""
import argparse,copy,hashlib,json,random,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,schedule_path,merge_schedule,LIVE_RULE_POLICIES
from selection import accepted
from symbolize import symbolize
from jevd import NAME_KEYWORDS
from common import sites
from context_tables import context_tables
BASE=ROOT/'results/pass11'
DESIGN=json.loads((BASE/'design.json').read_text())
OPTIONS={'MIMALLOC_PURGE_DELAY':'0','MIMALLOC_ARENA_PURGE_MULT':'1','MIMALLOC_PURGE_DECOMMITS':'1'}
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
def load(path,config):
 data=json.loads(path.read_text()) if path.exists() else dict(configuration=config,runs=[],coverage_runs=[])
 assert data['configuration']==config,('Changed inputs',str(path))
 return data

def fingerprints():
 files=['results/pass11/design.json','build/libjevalloc.so','build/libmimalloc.so','src/live.inc','src/hybrid.h','bench/run.py','tools/jevd.py','tools/prompts.py','fragbench/review3.py','fragbench/redis_workload.py','patches/redis-request-context.patch','patches/redis-request-context-unnormalized.patch']
 files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'build').glob('server-sim*')) if p.is_file() and p.suffix=='' and p.name!='server-sim-diag']
 files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'build/bench').glob('redis-context-*')) if p.is_file()]
 files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'descriptions').glob('*.txt')) if p.name!='server-sim-diag.txt']
 return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
def row(naming,workload,threads):
 return dict(name=f'{workload}-{threads}',binary='../server-sim-'+naming,args=[str(threads),workload,'400000','250'],stdin=None,expect='fragbench OK',gate_inference=True,prompt='stack-v1',model_cache=str(BASE/'model-cache'/naming/workload),environment={'JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12','FRAG_LONG_SETTLE_MS':'10000'})
def empty_table(tables,name):
 folder=tables/name;folder.mkdir(parents=True,exist_ok=True)
 if not (folder/'oracle.txt').exists():(folder/'oracle.txt').write_text('')
def check(r,warm=True):
 assert r['exit_status']==0 and r['output_ok'],r
 assert not r.get('decision_errors') and not r.get('allocator_stats',{}).get('failures'),r
 if warm:assert not r.get('model_seconds') and not r.get('new_decisions') and not r.get('replay_missing'),r
 m=r.get('allocator_stats',{}).get('metadata')
 if m:assert m['pairs']<=m['max_pairs'] and m['max_observed_contexts']<=m['max_contexts'] and m['bytes']<=m['peak_bytes']<=m['max_bytes'],m
 assert sum(p['phase']=='idle10' for p in r['phases'])>=1

def audit(path):
 with path.with_suffix('.audit.log').open('w') as log:subprocess.run([sys.executable,str(ROOT/'tools/audit_pass4.py'),str(path)],cwd=ROOT,check=True,stdout=log,stderr=subprocess.STDOUT)
def collect(r,variant,out,source=None):
 """Cold answer and coverage probes; frozen model schedule is independent of gate."""
 out.mkdir(parents=True,exist_ok=True);tables=out/'tables';empty_table(tables,r['name'])
 path=out/'collection.json';config=dict(row=r,variant=variant,fingerprints=fingerprints())
 d=load(path,config);logs=out/'logs';logs.mkdir(exist_ok=True)
 schedule=schedule_path(r,variant,logs)
 if d.get('complete'):return schedule
 if source and not schedule.exists():shutil.copyfile(source,schedule)
 if not schedule.exists():
  print('COLD',out.relative_to(ROOT),flush=True)
  result=run_one(r,variant,-1,logs,tables,max_model_decisions=3000);check(result,False)
  d['runs'].append(result);merge_schedule(schedule,ROOT/result['decision_log']);write(path,d)
 for attempt in range(12):
  print('COVERAGE',out.relative_to(ROOT),attempt,flush=True)
  result=run_one(r,variant,-2-attempt,logs,tables,max_model_decisions=3000);check(result,False)
  d['coverage_runs'].append(result);merge_schedule(schedule,ROOT/result['decision_log']);write(path,d)
  if not result['new_decisions'] and not result['replay_missing']:break
 else:raise RuntimeError('Coverage did not converge')
 d['complete']=True;d['schedule_sha256']=hashlib.sha256(schedule.read_bytes()).hexdigest();write(path,d)
 return schedule

def factorial_schedules(naming,workload):
 out=BASE/'factorial'/naming/workload;canonical=out/'model.jsonl'
 if (out/'priors.json').exists():return out
 source=None
 if naming=='plausible':
  r=row(naming,workload,1)
  source=schedule_path(r,'jev-live:hybrid',ROOT/'results/pass10/defaults/plausible'/r['name']/'logs')
 one=collect(row(naming,workload,1),'jev-live:hybrid',out/'collect-1',source)
 sixteen=collect(row(naming,workload,16),'jev-live:hybrid',out/'collect-16',one)
 merge_schedule(canonical,one);merge_schedule(canonical,sixteen)
 events=[json.loads(line) for line in canonical.read_text().splitlines()]
 priors=[];neutral=[];rule=[]
 for event in events:
  assert event['ordinal']==0 and event['response']['recheck_after']==0
  assert event.get('raw_response') and not event.get('budget_exhausted')
  request=event['request'];frames=[dict(f,address=f.get('addr','0x0')) for f in request['frames']]
  symbolize([{'frames':frames}])
  cls=int(any(word in f.get('function','').lower() for f in frames for word in NAME_KEYWORDS)) if workload=='site-pure' else int('ttl=day' in request.get('context',''))
  probabilities=event['raw_response']['answers']['lifetime']['probabilities']
  priors.append(dict(key=request['key'],context=request.get('context',''),frames=frames,probabilities=probabilities,rule_class=cls,model_class=event['response']['class'],model_request=event.get('model_request')))
  for dest,p,label in [(neutral,.5,'neutral'),(rule,float(1-cls),'rule')]:
   e=copy.deepcopy(event);e['response'].update({'class':0 if label=='neutral' else cls,'prior_transient':p,'prior_permanent':1-p})
   e['raw_response']['answers']['lifetime']['probabilities']={'transient':p,'permanent':1-p}
   # Preserve transport envelope; only probabilities and their induced class differ.
   dest.append(e)
 for name,items in [('neutral',neutral),('rule',rule)]:
  (out/(name+'.jsonl')).write_text(''.join(json.dumps(e,sort_keys=True)+'\n' for e in items))
 write(out/'priors.json',priors)
 return out

def factorial():
 for m in DESIGN['mappings']:
  naming=m['name']
  for workload in ('site-pure','site-mixed'):
   sources=factorial_schedules(naming,workload)
   for threads in (1,16):
    r=row(naming,workload,threads);out=sources/str(threads);out.mkdir(exist_ok=True);path=out/'matrix.json'
    config=dict(row=r,repetitions=10,variants=[f'{s}-{g}' for g in ('0.6','0.7','0.8') for s in ('model','neutral','rule')]+['mi'],workloads=[r['name']],fingerprints=fingerprints(),schedules={s:hashlib.sha256((sources/(s+'.jsonl')).read_bytes()).hexdigest() for s in ('model','neutral','rule')})
    d=load(path,config)
    if d.get('complete'):continue
    empty_table(out/'tables',r['name'])
    for order in DESIGN['orders']:
     if (order['naming'],order['workload'],order['threads'])!=(naming,workload,threads):continue
     rep=order['repetition']
     for label in order['variants']:
      if any(x['variant']==label and x['repetition']==rep for x in d['runs']):continue
      rr=copy.deepcopy(r);logs=out/'logs'/label;logs.mkdir(parents=True,exist_ok=True)
      variant='mi' if label=='mi' else 'jev-live:hybrid'
      if label!='mi':
       source,gate=label.split('-');rr['environment']['JEVALLOC_PROMOTION_GATE']=gate
       shutil.copyfile(sources/(source+'.jsonl'),schedule_path(rr,variant,logs))
      print('FACTORIAL',naming,workload,threads,rep,label,flush=True)
      result=run_one(rr,variant,rep,logs,out/'tables')
      if result.get('replay_missing'):
       result['coverage_probe']=True;d['coverage_runs'].append(result);write(path,d)
      check(result)
      assert not any(k.startswith('MIMALLOC_') for k in result['environment'])
      result.update(transport_variant=variant,variant=label,order_seed=order['seed'])
      if label!='mi':
       assert result['allocator_stats']['promotion_gate']==float(gate)
       assert not result['allocator_stats']['metadata']['overflow_allocations']
      d['runs'].append(result);write(path,d)
    assert len(d['runs'])==100 and all(accepted(x) for x in d['runs'])
    d['complete']=True;write(path,d);audit(path)
    print('COMPLETE',path.relative_to(ROOT),flush=True)

def redis():
 variants=['mi','jev-keyonly','jev-table:oracle-site','jev-table:oracle-context','jev-live:static-site','jev-live:static-model','jev-live:hybrid','jev-live:heuristic','jev-live:rules-neutral','jev-live:rule-names','jev-live:rule-ttl']
 for ni,naming in enumerate(('normalized','unnormalized')):
  for oi,options in enumerate(('defaults','immediate')):
   r=dict(name='redis-drop',binary='redis-context-'+naming,args=['--activedefrag','no'],redis_driver='drop',stdin=None,expect='fragbench OK',gate_inference=True,prompt='stack-v1',environment={'JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12','FRAG_LONG_SETTLE_MS':'10000'})
   if options=='immediate':r['environment'].update(OPTIONS)
   out=BASE/'redis'/naming/options;out.mkdir(parents=True,exist_ok=True);path=out/'matrix.json'
   d=load(path,dict(row=r,repetitions=5,variants=variants,workloads=[r['name']],fingerprints=fingerprints()))
   if d.get('complete'):continue
   tables=out/'tables';empty_table(tables,r['name']);logs=out/'logs';logs.mkdir(exist_ok=True)
   if 'trace' not in d:
    trace=out/'trace.jsonl';d['trace']=run_one(r,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
    d['truth']=context_tables(sites(trace),tables/r['name']);write(path,d)
   for v in ('jev-live:static-site','jev-live:static-model','jev-live:hybrid'):
    source=collect(r,v,out/('collect-'+v.split(':')[1]))
    shutil.copyfile(source,schedule_path(r,v,logs))
   for rep in range(5):
    seed=111000+ni*100+oi*10+rep;order=variants[:];random.Random(seed).shuffle(order)
    for v in order:
     if any(x['variant']==v and x['repetition']==rep for x in d['runs']):continue
     print('REDIS',naming,options,rep,v,flush=True)
     for attempt in range(6):
      result=run_one(r,v,rep,logs,tables,attempt=attempt)
      if not result.get('replay_missing'):break
      result['coverage_probe']=True;d['coverage_runs'].append(result);write(path,d)
      fill=run_one(r,v,-2-attempt,logs,tables,attempt=20);merge_schedule(schedule_path(r,v,logs),ROOT/fill['decision_log']);d['coverage_runs'].append(fill);write(path,d)
     check(result);result['order_seed']=seed;d['runs'].append(result);write(path,d)
   assert len(d['runs'])==55
   d['complete']=True;write(path,d);audit(path)
   print('COMPLETE',path.relative_to(ROOT),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['redis','factorial']);a=p.parse_args()
 {'redis':redis,'factorial':factorial}[a.stage]()
if __name__=='__main__':main()
