#!/usr/bin/env python3
"""Prior-trace oracle: majority of requested bytes, not allocation count."""
import argparse
from common import sites, oracle, write_table

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace'); p.add_argument('-o', '--output', required=True)
    boundary=p.add_mutually_exclusive_group()
    boundary.add_argument('--short-bytes',type=int,default=None,help='Extra fixed-S control, not the default oracle')
    boundary.add_argument('--permanent-percent',choices=['25','50','90','never'],default='50')
    a = p.parse_args()
    write_table(a.output, ((s['key'], oracle(s,a.short_bytes,a.permanent_percent)) for s in sites(a.trace)))
    label=f'Fixed-S control (S={a.short_bytes})' if a.short_bytes is not None else f'Transient/permanent oracle ({a.permanent_percent})'
    print(label+': byte-majority site labels from a prior trace; not an RSS bound.')
if __name__ == '__main__': main()
