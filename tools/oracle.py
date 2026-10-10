#!/usr/bin/env python3
"""Same-run, hindsight oracle: majority of requested bytes, not allocation count."""
import argparse
from common import sites, oracle, write_table

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace'); p.add_argument('-o', '--output', required=True)
    a = p.parse_args()
    write_table(a.output, ((s['key'], oracle(s)) for s in sites(a.trace)))
    print('Oracle: fitted and evaluated on the same workload; hindsight upper-bound control.')
if __name__ == '__main__': main()
