#!/usr/bin/env python3
"""Recompute gates, pair labels, search choices, costs and inference audit coverage."""
import gzip,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from common import sites,oracle
from context_tables import context_tables
NAMES=['site-mixed-1','site-mixed-16','redis-mesh','redis-drop','redis-sessions','per-alloc-small']
def idle(r):return max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p.get('cycle',0))['rss_bytes']
def table(path):return {k:int(v) for k,v in (line.split() for line in path.read_text().splitlines())}
def main():
 base=ROOT/'results/pass9';reports=[];fingerprints=set();permanent={}
 with gzip.open(base/'permanent-pairs.jsonl.gz','rt') as evidence:
  for line in evidence:
   pair=json.loads(line);keys=permanent.setdefault(pair['workload'],set())
   assert pair['key'] not in keys;keys.add(pair['key'])
   for model in pair['models'].values():
    answers=model.get('decisions',[]) if 'decisions' in model else [model]
    for answer in answers:
     if answer.get('answer') is None:continue
     probabilities=answer['probabilities']
     assert abs(sum(probabilities.values())-1)<1e-5
     assert answer['answer']==int(probabilities['permanent']>probabilities['transient'])
 for name in NAMES:
  path=base/name/'matrix.json';d=json.loads(path.read_text());assert d['complete'],name
  fingerprints.add(d['configuration']['fingerprints']['build/libjevalloc.so'])
  groups={}
  for r in d['runs']:
   assert r['exit_status']==0 and r['output_ok'] and not r.get('replay_missing') and not r.get('decision_errors'),r
   if r['repetition']>=0:
    assert not r.get('model_seconds',0),r
    groups.setdefault(r['variant'],[]).append(r)
  for v,rs in groups.items():assert sorted(r['repetition'] for r in rs)==list(range(5)),(name,v)
  ss=sites(base/name/'trace.jsonl');dest=base/name/'tables'/name
  assert permanent.get(name,set())=={s['key'] for s in ss if oracle(s)},name
  assert table(dest/'oracle-context.txt')=={s['key']:oracle(s) for s in ss}
  bysite={}
  for s in ss:
   weights=bysite.setdefault(s['site_key'],[0,0])
   for i in (0,1):weights[i]+=s['class_bytes'][i]
  assert table(dest/'oracle-site.txt')=={k:int(v[1]>v[0]) for k,v in bysite.items()}
  gate=d.get('gate_runs') or [r for r in d['runs'] if r['repetition']>=0]
  medians={v:statistics.median(idle(r) for r in gate if r['variant']==v) for v in d['headroom']['idle_rss']}
  assert medians==d['headroom']['idle_rss']
  eligible=min(value for v,value in medians.items() if v.startswith('jev-table:') and v!='jev-table:oracle-site')<medians['mi']*.95
  assert eligible==d['headroom']['eligible']
  if name.startswith('redis'):
   assert len(d['search_steps'])==min(24,len(ss))
   labels={s['key']:0 for s in ss};best=d['search_baseline']
   for i,step in enumerate(d['search_steps']):
    rs=[r for r in d['search_runs'] if r['variant']==f'jev-table:search-{i:02}'];assert len(rs)==3
    candidate=statistics.median(map(idle,rs));assert candidate==step['candidate_rss']
    assert step['best_before']==best and step['accepted']==(candidate<best*.98)
    if step['accepted']:labels[step['key']]=1;best=candidate
    assert step['best_after']==best
   assert table(dest/'search.txt')==labels
   if not eligible:assert not any(r['variant'].startswith('jev-live:') for r in d['runs'])
  audit=json.loads(path.with_suffix('.inference-audit.json').read_text())
  assert audit['matrix_sha256']==hashlib.sha256(path.read_bytes()).hexdigest() and audit['overlapping_runs']==0
  assert audit['checked']==sum(len(rs) for rs in groups.values())
  reports.append(dict(workload=name,warm_runs=sum(len(rs) for rs in groups.values()),pairs=len(ss),sites=len(bysite),headroom=eligible,search_trials=len(d['search_runs'])))
 accuracy=json.loads((base/'per-alloc-small/object-accuracy.json').read_text())
 assert accuracy['budget_fallbacks']==0 and accuracy['payload_objects']['objects']==2400
 assert accuracy['model_decisions']==2229,accuracy['model_decisions']
 objects=[json.loads(line) for line in (base/'per-alloc-small/object-truth.jsonl').open()]
 answered=[r for r in objects if r['model_answered']]
 for r in objects:assert r['truth']==int('death' not in r or 2*(r['death']-r['clock'])>accuracy['final_allocation_clock'])
 assert len(answered)==accuracy['model_decisions']==accuracy['model_answered']['objects']
 assert sum(r['class']==r['truth'] for r in answered)==accuracy['model_answered']['correct']
 performance=base/'per-alloc-small/performance/matrix.json'
 measured=json.loads(performance.read_text());assert measured['complete']
 for variant in measured['configuration']['variants']:
  rs=[r for r in measured['runs'] if r['variant']==variant]
  assert sorted(r['repetition'] for r in rs)==list(range(5))
  for r in rs:
   assert r['exit_status']==0 and r['output_ok'] and not r.get('replay_missing') and not r.get('model_seconds')
   assert 'JEVALLOC_OBJECT_TRACE' not in r['environment']
   if variant=='jev-live:per-alloc':assert r['allocator_stats']['decisions']==2229
 audit=json.loads(performance.with_suffix('.inference-audit.json').read_text())
 assert audit['matrix_sha256']==hashlib.sha256(performance.read_bytes()).hexdigest() and audit['overlapping_runs']==0
 fingerprints.add(measured['configuration']['fingerprints']['build/libjevalloc.so'])
 assert len(fingerprints)==1,fingerprints
 result=dict(passed=True,library_sha256=fingerprints.pop(),workloads=reports)
 (base/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
