#!/usr/bin/env python3
"""Report strict SPEC-FRAG gates without silently relaxing thresholds."""
import argparse,json,statistics
from pathlib import Path
from selection import complete_groups
p=argparse.ArgumentParser();p.add_argument('matrix');p.add_argument('--output');a=p.parse_args()
x=json.loads(Path(a.matrix).read_text());g,bs=complete_groups(x)
checks=[]
for b in bs:
    def ratio(v,w,m):return statistics.median(r[m] for r in g[b,v])/statistics.median(r[m] for r in g[b,w])
    row=dict(workload=b,none_time=ratio('jev-none','mi','score'),none_rss=ratio('jev-none','mi','peak_rss_bytes'),keyonly_rss=ratio('jev-keyonly','jev-none','peak_rss_bytes'))
    row['fix1_pass']=max(row['none_time'],row['none_rss'],row['keyonly_rss'])<=1.03
    if b in ('larson','larson-sized','xmalloc-test','mstress','rptest','sh6benchN','sh8benchN'):
        row['live_time']=ratio('jev-live:heuristic','jev-table:oracle','score');row['fix2_pass']=row['live_time']<=1.15
    checks.append(row)
result=dict(complete_workloads=len(bs),expected_workloads=len(x['configuration']['workloads']),passed=len(bs)==len(x['configuration']['workloads']) and all(c['fix1_pass'] and c.get('fix2_pass',True) for c in checks),checks=checks)
print(json.dumps(result,indent=2))
if a.output:Path(a.output).write_text(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
