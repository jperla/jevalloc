"""Standalone sensitivity summary; raw tables retain exact thresholds."""
import json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from selection import complete_groups
p=ROOT/'results/frag-sensitivity/matrix.json';d=json.loads(p.read_text());g,bs=complete_groups(d)
print('| Workload | Threshold | Idle RSS MiB | RSS/mi | Time s |')
print('|---|---:|---:|---:|---:|')
for b in bs:
 def metric(v):
  rows=g[b,v];rss=statistics.median(max((x for x in r['phases'] if x['phase']=='idle'),key=lambda x:x['cycle'])['rss_bytes'] for r in rows)
  return rss,statistics.median(r['wall_seconds'] for r in rows)
 base=metric('mi')[0]
 for n,v in ((65536,'jev-table:oracle-65536'),(1048576,'jev-table:oracle'),(16777216,'jev-table:oracle-16777216')):
  rss,sec=metric(v);print(f'| {b} | {n} | {rss/2**20:.3f} | {rss/base:.4f} | {sec:.3f} |')
