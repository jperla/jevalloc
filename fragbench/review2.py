#!/usr/bin/env python3
"""Pass 10 matched controls. Fixed policies/names are declared in CODEX-REPORT.md."""
import argparse,copy,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,schedule_path,merge_schedule,prepare_replay,LIVE_RULE_POLICIES
from common import sites
from context_tables import context_tables
from selection import complete_groups
from symbolize import symbolize
sys.path.insert(0,str(ROOT/'fragbench'))
from realtime import definitions as context_definitions,OPTIONS
from real import definitions as real_definitions
BASE=ROOT/'results/pass10'
POLICIES=['jev-live:'+p for p in ('static-model','hybrid','heuristic','rules-neutral','rule-names')]

def rows(stage):
 if stage=='server':
  for options in ('immediate','defaults'):
   for naming in (('named',) if options=='immediate' else ('named','opaque','plausible')):
    for mode in ('site-pure','site-mixed'):
     for threads in (1,16):
      row=dict(name=f'{mode}-{threads}',binary='../server-sim'+('' if naming=='named' else '-'+naming),args=[str(threads),mode,'400000','250'],stdin=None,expect='fragbench OK',gate_inference=True,prompt='stack-v1',environment=dict(OPTIONS))
      yield options,naming,row
 elif stage=='real':
  for row in [r for r in context_definitions() if r.get('redis_driver')]+[r for r in real_definitions() if not r['name'].startswith('redis')]:
   yield 'defaults','named',copy.deepcopy(row)
 elif stage=='peralloc':
  for options in ('immediate','defaults'):
   yield options,'named',copy.deepcopy(next(r for r in context_definitions() if r['name']=='per-alloc-small'))

def audit(path):
 with path.with_suffix('.audit.log').open('w') as log:subprocess.run([sys.executable,str(ROOT/'tools/audit_pass4.py'),str(path)],check=True,stdout=log,stderr=subprocess.STDOUT)

def block(options,naming,row):
 name=row['name'];small=name=='per-alloc-small';mixed=name.startswith('site-mixed');redis=bool(row.get('redis_driver'))
 out=BASE/options/naming/name;out.mkdir(parents=True,exist_ok=True);logs=out/'logs';logs.mkdir(exist_ok=True);tables=out/'tables';path=out/'matrix.json'
 if options=='defaults':
  row['environment']={k:v for k,v in row['environment'].items() if not k.startswith('MIMALLOC_')}
  row['environment']['FRAG_LONG_SETTLE_MS']='10000'
 variants=['mi','jev-keyonly','jev-table:oracle-site']
 if mixed or redis or small:variants+=['jev-table:oracle-context']
 if small:variants+=['jev-live:per-alloc']
 else:
  if mixed or redis:variants+=['jev-live:static-site']
  variants+=POLICIES
  if mixed or redis:variants+=['jev-live:rule-ttl']
 files=[ROOT/'build/bench'/row['binary'],ROOT/'build/libjevalloc.so',ROOT/'build/libmimalloc.so',ROOT/'bench/run.py',ROOT/'tools/jevd.py',ROOT/'tools/prompts.py',ROOT/'tools/symbolize.py',ROOT/'fragbench/server-sim.c',ROOT/'fragbench/redis_workload.py',Path(__file__)]
 files+=sorted((ROOT/'descriptions').glob('*.txt'))
 config=dict(row=row,options=options,naming=naming,variants=variants,repetitions=5,workloads=[name],fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
 d=json.loads(path.read_text()) if path.exists() else dict(name=str(out.relative_to(ROOT/'results')),configuration=config,runs=[],coverage_runs=[])
 assert d['configuration']==config,'Resume inputs changed: '+str(path)
 if d.get('complete'):return
 def persist():save(path,d)
 def execute(v,rep,logged=False,attempt=0):
  r=copy.deepcopy(row)
  if logged:r['environment'].update(JEVALLOC_OBJECT_TRACE=str(logs/f'objects-{rep}.jsonl'),JEVALLOC_TRACE_OUT=str(logs/f'objects-{rep}.trace.jsonl'))
  print(options,naming,name,v,rep,'logged' if logged else '',flush=True)
  result=run_one(r,v,rep,logs,tables,attempt=attempt,max_model_decisions=3000)
  if options=='defaults':assert not any(k.startswith('MIMALLOC_') for k in result['environment'])
  stats=result.get('allocator_stats',{})
  if len(stats.get('site_bytes',{}))>10000:
   # Preserve full exit statistics remotely; keep admitted-site detail and exact
   # global/model-coverage totals in the compact matrix (no instrumentation change).
   retained={k for k,b in stats['site_bytes'].items() if b>=65536}
   result['site_statistics_storage']=dict(scope='sites with >=65536 requested bytes',total_sites=len(stats['site_bytes']),retained_sites=len(retained),full_file=result['decision_log'].replace('.decisions.jsonl','.stats.json'))
   for field in ('site_bytes','site_sampled_live'):
    stats[field]={k:v for k,v in stats[field].items() if k in retained}
  return result
 trace=out/'trace.jsonl'
 if not d.get('trace_complete'):
  d['trace_run']=run_one(row,'jev-trace',0,logs/'trace',tables,mode='trace',trace=trace)
  ss=sites(trace);d['truth']=context_tables(ss,tables/name)
  if name.startswith('site-') or small:
   symbolize(ss);(out/'sites.json').write_text(json.dumps(ss,indent=2)+'\n')
  d['trace_complete']=True;persist()
 for v in variants:
  if not v.startswith('jev-live:') or v.split(':')[1] in LIVE_RULE_POLICIES:continue
  if not any(r['variant']==v and r['repetition']==-1 for r in d['runs']):
   if small and options=='defaults':
    source=BASE/'immediate/named/per-alloc-small/logs'
    shutil.copyfile(schedule_path(row,v,source),schedule_path(row,v,logs))
    cold=execute(v,-2,logged=True)
    assert not cold['model_seconds'] and not cold['new_decisions'] and not cold['replay_missing']
    cold.update(repetition=-1,cold=True,coverage_fill=False,schedule_source=str(schedule_path(row,v,source).relative_to(ROOT)),cold_inference_recollected=False)
   else:
    cold=execute(v,-1,logged=small)
   d['runs'].append(cold);persist()
  cold=next(r for r in d['runs'] if r['variant']==v and r['repetition']==-1)
  merge_schedule(schedule_path(row,v,logs),ROOT/cold['decision_log'])
  if not small:prepare_replay(row,v,logs,tables,7200,d,path,3000)
 # Logged warm runs verify recollected lifetimes/sampling separately from cost runs.
 if small:
  for rep in range(5):
   if any(r['repetition']==rep for r in d.get('logged_runs',[])):continue
   r=execute('jev-live:per-alloc',rep,logged=True,attempt=99)
   assert not r['replay_missing'] and r['allocator_stats']['decisions']==2229
   d.setdefault('logged_runs',[]).append(r);persist()
 for rep in range(5):
  for v in variants[rep%len(variants):]+variants[:rep%len(variants)]:
   if any(r['variant']==v and r['repetition']==rep for r in d['runs']):continue
   for attempt in range(6):
    r=execute(v,rep,attempt=attempt)
    if not r.get('replay_missing'):break
    r['coverage_probe']=True;d['coverage_runs'].append(r);persist();prepare_replay(row,v,logs,tables,7200,d,path,3000)
   else:raise RuntimeError('Replay coverage did not converge')
   assert not r.get('model_seconds')
   if v.split(':')[-1] in LIVE_RULE_POLICIES:
    assert r['decision_execution']=='live-current-statistics'
    events=[json.loads(line) for line in (ROOT/r['decision_log']).open()]
    assert not any(e.get('replayed') or e.get('raw_response') for e in events)
   if options=='defaults':assert any(p['phase']=='idle10' for p in r['phases'])
   d['runs'].append(r);persist()
 assert complete_groups(d)[1]==[name]
 persist()
 if small:
  from pass9_report import object_accuracy
  object_accuracy(out)
  cold=next(r for r in d['runs'] if r.get('cold'))
  comparisons=[cold]+d['logged_runs']+[r for r in d['runs'] if r['repetition']>=0 and r['variant']=='jev-live:per-alloc']
  sample_counts=[(r['allocator_stats']['samples'],r['allocator_stats']['sampled_live_objects']) for r in comparisons]
  assert len(set(sample_counts))==1,sample_counts
  (out/'sampling-comparison.json').write_text(json.dumps(dict(counts=sample_counts,drift=[r['replay_drift'] for r in comparisons]),indent=2)+'\n')
 d['complete']=True;persist();audit(path)
 subprocess.run([sys.executable,str(ROOT/'tools/pass10_report.py')],check=True)
 with (ROOT/'CODEX-REPORT.md').open('a') as journal:
  journal.write('\nPass 10 completed '+str(out.relative_to(ROOT))+': five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.\n')
 print('COMPLETE',out.relative_to(ROOT),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['server','peralloc','real']);a=p.parse_args()
 for options,naming,row in rows(a.stage):block(options,naming,row)
if __name__=='__main__':main()
