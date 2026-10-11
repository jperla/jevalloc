"""Untimed diagnostic: current two-class instrument and Redis protocol."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one
from common import sites,oracle,write_table
from baselines import generate
import importlib.util
spec=importlib.util.spec_from_file_location('fragrun',ROOT/'fragbench/run.py');frag=importlib.util.module_from_spec(spec);spec.loader.exec_module(frag)
out=ROOT/'results/pass5/probe';out.mkdir(parents=True,exist_ok=True)
for row in frag.definitions()[:2]:
 row['gate_inference']=False
 trace=out/(row['name']+'.jsonl');print(row['name'],'trace',flush=True)
 run_one(row,'jev-trace',0,out/'logs',out/'tables',mode='trace',trace=trace)
 ss=sites(trace);generate(trace,out/'tables'/row['name']);write_table(out/'tables'/row['name']/'oracle.txt',[(s['key'],oracle(s)) for s in ss])
 print([(s['bytes'],s['class_bytes']) for s in ss if s['bytes']>1000000],flush=True)
 for v in ('mi','jev-keyonly','jev-table:oracle'):
  r=run_one(row,v,0,out/'logs',out/'tables');print(v,r['phases'],flush=True)
from definitions import definitions
row=next(r for r in definitions(16) if r['name']=='redis')
(out/'tables/redis').mkdir(parents=True,exist_ok=True);(out/'tables/redis/oracle.txt').write_text('')
for rep in range(3):
 print('redis heuristic diagnostic',rep,flush=True)
 r=run_one(row,'jev-live:heuristic',-1,out/('redis'+str(rep)),out/'tables');print(r['allocator_stats']['failures'],flush=True)
