#!/usr/bin/env python3
"""Exercise runner cache filling, then require a fully covered, model-idle replay."""
import json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import run_one, merge_schedule, schedule_path

def main():
    out=ROOT/'results/replay-test';out.mkdir(exist_ok=True)
    row={'name':'cfrac','binary':'../live-test','args':['single'],'stdin':None,'expect':'live OK'}
    # Replay transport fixture; the heuristic must run live.
    variant='jev-live:random';tables=ROOT/'results/tables'
    cold=run_one(row,variant,-1,out,tables)
    schedule=schedule_path(row,variant,out)
    # Deliberately withhold all rechecks to simulate a time-limited cold run.
    initial=[json.loads(line) for line in (ROOT/cold['decision_log']).read_text().splitlines()]
    schedule.write_text(''.join(json.dumps(r)+'\n' for r in initial if r['ordinal']==0))
    fill=run_one(row,variant,-2,out,tables)
    assert fill['new_decisions']>0 and fill['replay_missing']==0,fill
    merge_schedule(schedule,ROOT/fill['decision_log'])
    probe=run_one(row,variant,-3,out,tables)
    assert probe['new_decisions']==0,probe
    replay=run_one(row,variant,0,out,tables)
    assert replay['replay_missing']==0 and replay['model_seconds']==0,replay
    (out/'checks.json').write_text(json.dumps({'cold':cold,'fill':fill,'probe':probe,'replay':replay,'passed':True},indent=2))
    print('REPLAY COVERAGE TEST PASSED')
if __name__=='__main__':main()
