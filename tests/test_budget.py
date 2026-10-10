#!/usr/bin/env python3
"""Exercise budget fallback and byte coverage through the allocator and sidecar."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import run_one, merge_schedule, schedule_path

def main():
    out=ROOT/'results/budget-test';out.mkdir(exist_ok=True)
    row={'name':'budget','binary':'../live-test','args':['single'],'stdin':None,'expect':'live OK'}
    tables=out/'tables';(tables/'budget').mkdir(parents=True,exist_ok=True)
    (tables/'budget/oracle.txt').write_text('')
    for variant in ('jev-live:model','jev-live:static-model'):
        cold=run_one(row,variant,-1,out,tables,max_model_decisions=0)
        schedule=schedule_path(row,variant,out);schedule.unlink(missing_ok=True)
        merge_schedule(schedule,ROOT/cold['decision_log'])
        warm=run_one(row,variant,0,out,tables,max_model_decisions=0)
        for r in (cold,warm):
            c=r['model_coverage'];st=r['allocator_stats']
            assert c['sites']>0 and c['allocated_bytes']>0,r
            assert c['unasked_sites']==c['sites'] and c['asked_sites']==0,r
            assert c['unasked_bytes']==c['allocated_bytes']==st['allocation_clock'],r
            assert c['unasked_byte_share']==1 and st['rechecks']==0,r
            assert r['model_seconds']==0 and r['replay_missing']==0,r
            events=[json.loads(line) for line in (ROOT/r['decision_log']).read_text().splitlines()]
            assert all(e['response']=={'class':1,'recheck_after':0} and e['budget_exhausted'] and e['raw_response'] is None for e in events)
        (out/(variant.split(':')[1]+'.json')).write_text(json.dumps({'cold':cold,'warm':warm,'passed':True},indent=2))
    print('BUDGET INTEGRATION TEST PASSED')
if __name__=='__main__':main()
