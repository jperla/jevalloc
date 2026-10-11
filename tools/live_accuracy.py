#!/usr/bin/env python3
"""Audit explicit cold logs only; separate policy/model populations and coverage."""
import argparse,collections,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('results',nargs='?',default='results');p.add_argument('--matrix',default='pass4.json');a=p.parse_args();root=Path(a.results);matrix_path=root/a.matrix;matrix=json.loads(matrix_path.read_text())
for run in matrix['runs']:
    if not run.get('cold'):continue
    workload=run['benchmark'];truth={k:int(v) for k,v in (s.split() for s in (matrix_path.parent/'tables'/workload/'oracle.txt').read_text().splitlines() if s.strip())}
    path=root/Path(run['decision_log']).relative_to('results');events=[json.loads(s) for s in path.read_text().splitlines()]
    unknown={e['request']['key'] for e in events if 'response' in e and e['request']['key'] not in truth}
    if unknown:raise SystemExit(f'{path}: {len(unknown)} decision sites have no matching truth; accuracy withheld')
    for scope in ('policy','model-only'):
        rows=[e for e in events if 'response' in e and (scope=='policy' or e.get('raw_response'))]
        matched=[e for e in rows if e['request']['key'] in truth]
        first=[e for e in matched if e['ordinal']==0];rechecks=[e for e in matched if e['ordinal']>0]
        last={e['request']['key']:e for e in sorted(matched,key=lambda e:e['ordinal'])}
        def metric(xs):return {'correct':sum(e['response']['class']==truth[e['request']['key']] for e in xs),'observations':len(xs)}
        print(json.dumps(dict(file=str(path),benchmark=workload,variant=run['variant'],scope=scope,first=metric(first),rechecks=metric(rechecks),final_sites=metric(list(last.values())),matched_sites=len(last),truth_sites=len(truth),unmatched_decisions=len(rows)-len(matched),recheck_note='Repeated decisions; not independent sites.')))
