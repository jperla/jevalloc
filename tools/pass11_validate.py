#!/usr/bin/env python3
"""Fail-closed final evidence audit for the declared pass-11 matrix."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/pass11'
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'bench')]
from selection import accepted
from pass11_design import design
from run import schedule_path
from common import sites
from symbolize import symbolize
from jevd import NAME_KEYWORDS

def main():
 assert json.loads((BASE/'design.json').read_text())==design()
 tests=json.loads((BASE/'tests/tests.json').read_text());assert tests['passed'] and tests['full_suite']
 assert len(json.loads((BASE/'tests/live-limits.json').read_text()))==5
 matrices=list((BASE/'factorial').glob('*/*/*/matrix.json'));redis=list((BASE/'redis').glob('*/*/matrix.json'));diag=list((BASE/'diagnostic').glob('*/matrix.json'))
 assert (len(matrices),len(redis),len(diag))==(24,4,2)
 hashes={};tables={};warm=0;requests=0;probabilities=0
 assert tests['library_sha256']==hashlib.sha256((ROOT/'build/libjevalloc.so').read_bytes()).hexdigest()
 for path in matrices+redis+diag:
  d=json.loads(path.read_text());assert d['complete'],path
  audit=json.loads(path.with_suffix('.inference-audit.json').read_text())
  digest=hashlib.sha256(path.read_bytes()).hexdigest();assert audit['matrix_sha256']==digest and audit['overlapping_runs']==0
  hashes[str(path.relative_to(BASE))]=digest
  for relative,digest in d['configuration']['fingerprints'].items():assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
  if path in redis+diag:
   rows=sites(path.parent/'trace.jsonl');pairs={r['key']:int(r['class_bytes'][1]>r['class_bytes'][0]) for r in rows};totals={}
   for r in rows:
    counts=totals.setdefault(r['site_key'],[0,0])
    for i in (0,1):counts[i]+=r['class_bytes'][i]
   name=d['configuration']['row']['name']
   for filename,expected in [('oracle.txt',pairs),('oracle-context.txt',pairs),('oracle-site.txt',{k:int(v[1]>v[0]) for k,v in totals.items()})]:
    table=path.parent/'tables'/name/filename
    assert {k:int(v) for k,v in (line.split() for line in table.read_text().splitlines())}==expected
    tables[str(table.relative_to(BASE))]=dict(labels=len(expected),sha256=hashlib.sha256(table.read_bytes()).hexdigest())
  if path in diag:
   assert len(d['runs'])==6
   for r in d['runs']:assert r['diagnostic'] and len(r['phases'])==len(r['allocator_phases'])
   continue
  n=10 if path in matrices else 5
  for v in d['configuration']['variants']:
   rs=[r for r in d['runs'] if r['variant']==v];assert len(rs)==n and {r['repetition'] for r in rs}==set(range(n)),(path,v)
  for r in d['runs']:
   assert accepted(r) and not r.get('model_seconds') and not r.get('new_decisions') and not r.get('replay_missing')
   warm+=1
   if path in matrices or path.parent.name=='defaults':assert not any(k.startswith('MIMALLOC_') for k in r['environment'])
   m=r.get('allocator_stats',{}).get('metadata')
   if m:
    assert m['pairs']<=m['max_pairs'] and m['max_observed_contexts']<=m['max_contexts'] and m['bytes']<=m['peak_bytes']<=m['max_bytes']
    # The measured Linux target is LP64; every persistent reservation must reconcile.
    assert m['bytes']==m['pairs']*m['site_size']+m['shards']*m['shard_size']+m['indexes']*512*8+m['sample_records']*m['sample_size']
   if r.get('decision_log'):
    events=[json.loads(line) for line in (ROOT/r['decision_log']).read_text().splitlines()];requests+=len(events)
    assert all(not e.get('error') and not e.get('model_seconds') and not e.get('replay_missing') for e in events)
    if path in redis and r['variant'].split(':')[-1] in ('heuristic','rules-neutral','rule-names','rule-ttl'):
     policy=r['variant'].split(':')[-1]
     for e in events:
      assert not e.get('replayed') and not e.get('raw_response')
      req=e['request'];reply=e['response']
      if policy=='heuristic':
       st=req['site'];expected=int(st['cohort_count']>=16 and st['older_sampled_bytes']>0 and 20*st['older_freed_bytes']<st['older_sampled_bytes'] and 4*st['oldest_age_bytes']>req['process']['alloc_clock'])
      elif policy=='rules-neutral':expected=0;assert reply['prior_transient']==.5
      elif policy=='rule-ttl':expected=int('ttl=day' in req['context'])
      else:
       fs=[dict(f,address=f.get('addr','0x0')) for f in req['frames']];symbolize([{'frames':fs}])
       expected=int(any(w in f.get('function','').lower() for f in fs for w in NAME_KEYWORDS))
      assert reply['class']==expected
    if path in matrices:
     assert all(e.get('replayed') for e in events)
     assert not m['overflow_allocations'] and not m['sample_overflows']
     assert all(t['count']==len(t['events']) for t in r['allocator_stats']['transitions'].values())
     source=r['variant'].split('-')[0];folder=path.parent.parent
     schedule={(e['request']['key'],e['ordinal']):e for e in map(json.loads,(folder/(source+'.jsonl')).read_text().splitlines())}
     for e in events:
      old=schedule[e['request']['key'],e['ordinal']]
      assert e['response']==old['response']
      assert e['raw_response']['answers']['lifetime']['probabilities']==old['raw_response']['answers']['lifetime']['probabilities']
   if path in matrices:
    mi=next(x for x in d['runs'] if x['variant']=='mi' and x['repetition']==r['repetition'])
    assert [(p['cycle'],p['phase'],p['live_bytes']) for p in r['phases']]==[(p['cycle'],p['phase'],p['live_bytes']) for p in mi['phases']]
  if path in matrices:
   naming,workload,threads=path.relative_to(BASE).parts[1:4]
   for source,digest in d['configuration']['schedules'].items():
    assert hashlib.sha256((path.parent.parent/(source+'.jsonl')).read_bytes()).hexdigest()==digest
   for rep in range(10):
    order=next(o for o in design()['orders'] if (o['naming'],o['workload'],o['threads'],o['repetition'])==(naming,workload,int(threads),rep))
    assert [r['variant'] for r in d['runs'] if r['repetition']==rep]==order['variants']
    assert all(r['order_seed']==order['seed'] for r in d['runs'] if r['repetition']==rep)
 prior_paths=list((BASE/'factorial').glob('*/*/priors.json'));assert len(prior_paths)==12
 for path in prior_paths:
  rows=json.loads(path.read_text());probabilities+=len(rows)
  if path.parent.parent.name!='plausible':
   cold=json.loads((path.parent/'collect-1/collection.json').read_text())
   assert cold['complete'] and sum(r.get('model_seconds',0) for r in cold['runs'])>0
   assert all(r.get('model_coverage',{}).get('budget_fallbacks',0)==0 for r in cold['runs']+cold['coverage_runs'])
  folder=path.parent
  schedules={s:list(map(json.loads,(folder/(s+'.jsonl')).read_text().splitlines())) for s in ('model','neutral','rule')}
  for m,n in zip(schedules['model'],schedules['neutral']):
   assert m['request']==n['request'] and m['ordinal']==n['ordinal']
   assert n['raw_response']['answers']['lifetime']['probabilities']=={'transient':.5,'permanent':.5}
   assert n['response']['class']==0
   normalized=[]
   for e in (m,n):
    e=copy.deepcopy(e)
    for k in ('class','prior_transient','prior_permanent'):e['response'].pop(k,None)
    e['raw_response']['answers']['lifetime'].pop('probabilities')
    normalized.append(e)
   assert normalized[0]==normalized[1], 'Model and neutral envelopes differ beyond the prior/induced class'
  assert len(schedules['model'])==len(schedules['neutral'])==len(schedules['rule'])==len(rows)
 result=dict(passed=True,matrices=len(hashes),accepted_warm_runs=warm,decision_events=requests,recorded_probabilities=probabilities,matrix_sha256=hashes,oracle_tables=tables)
 (BASE/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
