#!/usr/bin/env python3
"""Warm per-allocation costs without the cold run's exact lifetime logger."""
import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,schedule_path
sys.path.insert(0,str(ROOT/'fragbench'))
from realtime import definitions

def main():
 base=ROOT/'results/pass9/per-alloc-small'
 original=json.loads((base/'matrix.json').read_text());assert original['complete']
 row=next(r for r in definitions() if r['name']=='per-alloc-small')
 out=base/'performance';out.mkdir(exist_ok=True);logs=out/'logs';logs.mkdir(exist_ok=True);path=out/'matrix.json'
 variants=['mi','jev-keyonly','jev-table:oracle-site','jev-table:oracle-context','jev-live:per-alloc']
 files=[ROOT/'build/libjevalloc.so',ROOT/'build/server-sim',ROOT/'bench/run.py',ROOT/'tools/jevd.py',Path(__file__)]
 config=dict(row=row,variants=variants,repetitions=5,workloads=[row['name']],object_logging=False,cold_accuracy_source=str((base/'matrix.json').relative_to(ROOT)),fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
 d=json.loads(path.read_text()) if path.exists() else dict(name='pass9/per-alloc-small/performance',configuration=config,runs=[])
 assert d['configuration']==config,'Resume inputs changed'
 if d.get('complete'):return
 schedule=schedule_path(row,'jev-live:per-alloc',logs)
 if not schedule.exists():shutil.copyfile(schedule_path(row,'jev-live:per-alloc',base/'logs'),schedule)
 for rep in range(5):
  for v in variants[rep%len(variants):]+variants[:rep%len(variants)]:
   if any(r['variant']==v and r['repetition']==rep for r in d['runs']):continue
   print(v,f'rep {rep+1}/5',flush=True)
   r=run_one(row,v,rep,logs,base/'tables',max_model_decisions=3000)
   assert not r.get('replay_missing') and not r.get('model_seconds'),r
   if v=='jev-live:per-alloc':assert r['allocator_stats']['decisions']==2229
   assert 'JEVALLOC_OBJECT_TRACE' not in r['environment']
   d['runs'].append(r);save(path,d)
 d['complete']=True;save(path,d)
if __name__=='__main__':main()
