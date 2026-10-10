#!/usr/bin/env python3
"""Read-only status for a detached Beelink pass."""
import json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];results=root/'results'
out={}
for phase in ('test','bench'):
    log=results/(phase+'.log');status=results/(phase+'.status')
    if log.exists():out[phase]=log.read_text(errors='replace').splitlines()[-1:]
    if status.exists():out[phase+'_status']=status.read_text().strip()
p=results/'beelink.json'
if p.exists():
    data=json.loads(p.read_text());out['completed_runs']=len(data['runs']);out['coverage_runs']=len(data.get('coverage_runs',[]));out['workload_count']=len(data['configuration']['workloads']);out['expected_runs']=out['workload_count']*(data['configuration']['repetitions']*len(data['configuration']['variants'])+sum(v.startswith('jev-live:') for v in data['configuration']['variants']))
logs=list((results/'logs/beelink').glob('*.decisions.jsonl'))
if logs:
    p=max(logs,key=lambda p:p.stat().st_mtime);rows=[]
    for line in p.read_text().splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:pass
    out['active_log']=p.name;out['logged_decisions']=len(rows);out['last_decision_age_s']=round(time.time()-p.stat().st_mtime,1)
    out['model_seconds']=round(sum(r.get('model_seconds',0) for r in rows),1)
    if rows:out['budget_used']=rows[-1].get('model_decisions_used');out['last_error']=rows[-1].get('error')
print(json.dumps(out,indent=2))
