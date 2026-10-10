#!/usr/bin/env python3
"""Controls. Size thresholds fixed independently of lifetime data: <=256 short,
257..16384 medium, >16384 long. Typical size is mean requested bytes/allocation."""
import argparse, random
from pathlib import Path
from common import sites, write_table

def generate(trace, output, seed=42):
    ss = sorted(sites(trace), key=lambda s:s['key'])
    rng = random.Random(seed)
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    for mode in ('random', 'all-short', 'all-long', 'size'):
        entries = []
        for s in ss:
            mean = s['bytes'] / max(1, s['count'])
            cls = rng.randrange(3) if mode == 'random' else 0 if mode == 'all-short' else 2 if mode == 'all-long' else (0 if mean <= 256 else 1 if mean <= 16384 else 2)
            entries.append((s['key'], cls))
        write_table(out / (mode+'.txt'), entries)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('trace');p.add_argument('-o','--output',required=True);p.add_argument('--seed',type=int,default=42)
    a=p.parse_args();generate(a.trace,a.output,a.seed)
if __name__ == '__main__': main()
