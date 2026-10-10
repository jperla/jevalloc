#!/usr/bin/env python3
"""Measure live fast-path cost with an actual heuristic sidecar; no model calls."""
import json, os, statistics, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tests')]
from run import environment
from test_live import daemon

def main():
    samples=[]
    with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='live-cost-') as d:
        folder=Path(d)
        for i in range(5):
            log=folder/f'{i}.jsonl';p,sock=daemon(folder,'heuristic',log,folder/'cache')
            env,extra=environment('jev-live:heuristic','',ROOT/'results/tables');env.update(extra)
            stats=folder/'stats.json';env.update(JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(stats))
            try:output=subprocess.check_output([str(ROOT/'build/cost')],env=env,text=True)
            finally:p.terminate();p.wait()
            samples.append({'ns_per_pair':float(output.split()[0]),'stats':json.loads(stats.read_text())})
    result={'samples':samples,'median_ns_per_pair':statistics.median(r['ns_per_pair'] for r in samples),'note':'5 million malloc/free pairs; sample rate 64; heuristic sidecar, deterministic rechecks. Includes socket and stats costs amortized over the loop.'}
    (ROOT/'results/live-cost.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
