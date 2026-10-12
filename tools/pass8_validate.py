#!/usr/bin/env python3
"""Validate the completed pass-8 evidence on the measurement host."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/pass8'
sys.path.insert(0,str(ROOT/'tools'))
from selection import accepted,complete_groups

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def idle(r):return max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p.get('cycle',0))['rss_bytes']
def audit(p):
 a=read(p.with_suffix('.inference-audit.json'))
 assert a['matrix_sha256']==digest(p) and a['overlapping_runs']==0,p
 return a['checked']

library=digest(ROOT/'build/libjevalloc.so')
tests=read(OUT/'tests.json')
assert tests['passed'] and tests['full_suite'] and len(tests['workloads'])==22
assert tests['library_sha256']==library
result=dict(library_sha256=library,correctness_workloads=22,real={})
intervals=dict(source_matrices={},runs=[])
for p in sorted((OUT/'real').glob('*/matrix.json')):
 d=read(p);name=p.parent.name
 assert d['complete'] and len(d['top_sites'])==len(d['search_steps'])==24
 assert len(d['search_runs'])==75 and all(accepted(r) for r in d['search_runs'])
 assert d['configuration']['fingerprints']['build/libjevalloc.so']==library
 if name=='redis-mesh':assert d['configuration']['idle_metric']=='final-idle'
 else:assert all(sum(q['phase']=='idle' for q in r['phases'])==1 for r in d['search_runs']+d['runs'])
 def training(v):
  rows=[r for r in d['search_runs'] if r['variant']==v]
  assert len(rows)==3 and {r['repetition'] for r in rows}=={0,1,2}
  return statistics.median(map(idle,rows))
 best=training('jev-table:search-base');assert best==d['search_baseline']
 chosen=set()
 for i,s in enumerate(d['search_steps']):
  value=training(f'jev-table:search-{i:02}')
  assert s['key']==d['top_sites'][i]['key'] and s['candidate_rss']==value and s['best_before']==best
  assert s['accepted']==(value<best*.98)
  if s['accepted']:best=value;chosen.add(s['key'])
  assert s['best_after']==best
 table=p.parent/'tables'/name/'search.txt'
 assert {k for k,v in (line.split() for line in table.read_text().splitlines()) if int(v)==1}==chosen
 controls=['mi','jev-table:oracle','jev-table:search']
 gate=d.get('gate_runs') or [r for r in d['runs'] if r['repetition']>=0]
 medians={}
 for v in controls:
  rows=[r for r in gate if r['variant']==v and accepted(r)]
  assert len(rows)==5 and {r['repetition'] for r in rows}==set(range(5))
  medians[v]=statistics.median(map(idle,rows))
 assert d['headroom']['idle_rss']==medians
 eligible=min(medians[v] for v in controls[1:])<medians['mi']*.95
 assert d['headroom']['eligible']==eligible
 if not eligible:assert {r['variant'] for r in d['runs']}==set(controls)
 result['real'][name]=dict(search_trials=75,accepted_flips=len(chosen),headroom=eligible,audited_warm_intervals=audit(p))
 intervals['source_matrices'][str(p.relative_to(ROOT))]=digest(p)
 intervals['runs'] += [{k:r[k] for k in ('benchmark','variant','repetition','started_unix','finished_unix')} for r in d['search_runs']]
assert len(result['real'])==7
reg=ROOT/'results/pass8-regression.json';d=read(reg);g,bs=complete_groups(d)
assert len(bs)==22 and len(d['configuration']['variants'])==12
assert sum(len(g[b,v]) for b in bs for v in d['configuration']['variants'])==1320
assert d['configuration']['fingerprints'][str(ROOT/'build/libjevalloc.so')]==library
hybrid=[r for b in bs for r in g[b,'jev-live:hybrid']]
assert len(hybrid)==110 and all(r['allocator_stats']['rechecks']==0 and r['model_seconds']==0 for r in hybrid)
for name in ('pure','instrument'):
 assert read(OUT/name/'matrix.json')['configuration']['fingerprints']['build/libjevalloc.so']==library
result.update(regression_workloads=22,regression_variants=12,regression_audited_warm_intervals=audit(reg),hybrid_warm_runs_without_rechecks=110,pure_audited_warm_intervals=audit(OUT/'pure/matrix.json'),instrument_audited_warm_intervals=audit(OUT/'instrument/matrix.json'))
assert result['regression_audited_warm_intervals']==1320
(OUT/'search-intervals.json').write_text(json.dumps(intervals,indent=2))
(OUT/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
