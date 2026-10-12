#!/usr/bin/env python3
"""Fail closed on pass-10 repetitions, defaults, policy execution and provenance."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from selection import complete_groups,accepted
from common import sites,oracle
from context_tables import context_tables
from symbolize import symbolize
BASE=ROOT/'results/pass10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 matrices=sorted(BASE.glob('*/*/*/matrix.json'));assert len(matrices)==25,len(matrices)
 checked=0;fingerprints=0;rules=0;logged_checked=0;table_checks={}
 test=json.loads((BASE/'tests/tests.json').read_text());assert test['passed'] and test['full_suite'] and len(test['workloads'])==22
 assert test['library_sha256']==sha(ROOT/'build/libjevalloc.so')
 for path in matrices+[BASE/'regression.json']:
  d=json.loads(path.read_text());cfg=d['configuration'];groups,benches=complete_groups(d)
  assert benches==cfg['workloads'],(path,benches)
  for filename,digest in cfg['fingerprints'].items():
   assert sha(ROOT/filename)==digest,(path,filename);fingerprints+=1
  audit=json.loads(path.with_suffix('.inference-audit.json').read_text())
  assert audit['matrix_sha256']==sha(path) and audit['overlapping_runs']==0,path
  for r in d['runs']:
   if not accepted(r):continue
   checked+=1
   if cfg.get('options')=='defaults' or path.name=='regression.json':assert not any(k.startswith('MIMALLOC_') for k in r['environment']),r
   if r['variant'].split(':')[-1] in ('heuristic','rules-neutral','rule-names','rule-ttl'):
    assert r['decision_execution']=='live-current-statistics'
    for line in (ROOT/r['decision_log']).open():
     e=json.loads(line);assert not e.get('raw_response') and not e.get('replayed') and not e.get('replay_missing')
     req=e['request'];policy=r['variant'].split(':')[-1];reply=e['response']
     if policy=='heuristic':
      s=req['site'];expected=int(s['cohort_count']>=16 and s['older_sampled_bytes']>0 and 20*s['older_freed_bytes']<s['older_sampled_bytes'] and 4*s['oldest_age_bytes']>req['process']['alloc_clock'])
     elif policy=='rules-neutral':expected=0;assert reply['prior_transient']==.5
     elif policy=='rule-ttl':expected=int('ttl=day' in req['context'])
     else:
      fs=[dict(f,address=f.get('addr',f.get('address'))) for f in req['frames']];symbolize([{'frames':fs}])
      expected=int(any(word in f['function'].lower() for f in fs for word in ('cache','index','table','global','config','intern','registry')))
     assert reply['class']==expected,(policy,e);rules+=1
   assert not r.get('model_seconds') and not r.get('new_decisions')
  if path.name=='matrix.json':
   assert d['complete']
   # Every table label is independently recomputed from exact trace class bytes.
   ss=sites(path.parent/'trace.jsonl');pairs={s['key']:int(s['class_bytes'][1]>s['class_bytes'][0]) for s in ss}
   totals={}
   for s in ss:
    counts=totals.setdefault(s['site_key'],[0,0])
    for i in (0,1):counts[i]+=s['class_bytes'][i]
   expected_tables={'oracle-context.txt':pairs,'oracle.txt':pairs,'oracle-site.txt':{k:int(v[1]>v[0]) for k,v in totals.items()}}
   for name,expected in expected_tables.items():
    table=path.parent/'tables'/cfg['workloads'][0]/name
    parsed={k:int(v) for k,v in (line.split() for line in table.read_text().splitlines())};assert parsed==expected,(path,name)
    table_checks[str(table.relative_to(ROOT))]=dict(sha256=sha(table),labels=len(parsed))
   if cfg['workloads'][0]=='per-alloc-small':
    from pass9_report import object_accuracy
    before=json.loads((path.parent/'object-accuracy.json').read_text());assert object_accuracy(path.parent)==before
    counts=json.loads((path.parent/'sampling-comparison.json').read_text())['counts'];assert len({tuple(x) for x in counts})==1
    logged=d['logged_runs'];assert len(logged)==5 and {r['repetition'] for r in logged}==set(range(5))
    assert all(accepted(r) and not r['model_seconds'] and not r['new_decisions'] for r in logged)
    def requests(run):
     events=[json.loads(line) for line in (ROOT/run['decision_log']).open()]
     result={(e['request']['key'],e['ordinal']):e['request'] for e in events}
     assert len(result)==len(events)==2229
     return result
    reference=requests(next(r for r in d['runs'] if r.get('cold')))
    assert all(requests(r)==reference for r in logged+[r for r in d['runs'] if accepted(r) and r['variant']=='jev-live:per-alloc'])
    logged_path=path.parent/'logged-checks.json'
    logged_path.write_text(json.dumps(dict(configuration=cfg,runs=logged),indent=2)+'\n')
    subprocess.run([sys.executable,str(ROOT/'tools/audit_pass4.py'),str(logged_path)],check=True,stdout=subprocess.DEVNULL)
    logged_checked+=len(logged)
 for naming in ('opaque','plausible'):
  assert (ROOT/'descriptions'/f'server-sim-{naming}.txt').read_bytes()==(ROOT/'descriptions/server-sim.txt').read_bytes()
  expected={'fn_a','fn_b','fn_c','fn_d','fn_e'} if naming=='opaque' else {'buf_get','resp_build','conn_attach','entry_put','obj_new'}
  found=set()
  for path in (BASE/'defaults'/naming).glob('*/sites.json'):
   catalogue=json.loads(path.read_text())
   contexts={s['context'] for s in catalogue if s['context']}
   vocabulary={'k=0','k=1','k=2'} if naming=='opaque' else {'class=a','class=b','class=c'}
   assert contexts==(vocabulary if path.parent.name.startswith('site-mixed') else set()),(path,contexts)
   matrix=json.loads((path.parent/'matrix.json').read_text())
   named=json.loads((BASE/'defaults/named'/path.parent.name/'matrix.json').read_text())
   def workload_bytes(r):return [(p['phase'],p['cycle'],p['live_bytes']) for p in r['phases']]
   reference=workload_bytes(next(r for r in named['runs'] if accepted(r) and r['variant']=='mi'))
   assert all(workload_bytes(r)==reference for r in matrix['runs'] if accepted(r)),path
   for s in catalogue:
    found.update(f.get('function') for f in s['frames'])
    assert not any(word in f.get('function','') for f in s['frames'] for word in ('parse_request_buffer','assemble_response_buffer','create_session_state','insert_cache_index','store_request_payload'))
  assert expected<=found,(naming,expected-found)
 result=dict(passed=True,matrices=len(matrices)+1,warm_runs=checked,logged_warm_checks=logged_checked,fingerprints=fingerprints,live_rule_answers=rules,library_sha256=test['library_sha256'],oracle_tables_verified=table_checks)
 (BASE/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
