#!/usr/bin/env python3
"""Run only while no other benchmark is active; save raw timing samples."""
import json, os, statistics, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench'))
from run import environment

def main():
    result={'unit':'nanoseconds','key_samples':{},'allocation_free_pair_samples':{},'notes':'Five interleaved samples; 5 million calls or 32-byte malloc/free pairs per sample. Key cost includes noinline and indirect call overhead.'}
    for rep in range(5):
        for depth in (1,4,8,16):
            env,extra=environment('jev-keyonly','cfrac',ROOT/'results/tables');env.update(extra);env['JEVALLOC_DEPTH']=str(depth)
            text=subprocess.check_output([str(ROOT/'build/site-test'),'cost'],env=env,text=True)
            result['key_samples'].setdefault(str(depth),[]).append(float(text.split()[0]))
        variants=['mi','jev-none','jev-keyonly','jev-oracle']
        variants=variants[rep%4:]+variants[:rep%4]
        for variant in variants:
            env,extra=environment(variant,'cfrac',ROOT/'results/tables');env.update(extra)
            text=subprocess.check_output([str(ROOT/'build/cost')],env=env,text=True)
            result['allocation_free_pair_samples'].setdefault(variant,[]).append(float(text.split()[0]))
    result['medians']={k:{name:statistics.median(values) for name,values in result[k].items()} for k in ('key_samples','allocation_free_pair_samples')}
    (ROOT/'results/cost.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['medians'],indent=2))
if __name__=='__main__':main()
