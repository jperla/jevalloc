#!/usr/bin/env python3
"""Compact view of a benchmark matrix: every variant relative to plain mimalloc.

Prints score (time, or bench.sh's throughput-normalised time) and peak RSS as ratios to
`mi`, per workload and as geometric means, using only workloads with all repetitions.
"""
import argparse, collections, json, math, statistics as st
from selection import complete_groups

V = ['sys', 'mi', 'jev-none', 'jev-keyonly', 'jev-table:oracle', 'jev-table:random', 'jev-table:size',
     'jev-live:heuristic', 'jev-live:static-model', 'jev-live:model']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results', nargs='?', default='results/beelink.json')
    ap.add_argument('--reps', type=int, default=5)
    a = ap.parse_args()
    d = json.load(open(a.results))
    variants = d['configuration'].get('variants', V)
    g, benches = complete_groups(d,a.reps,variants)
    short = [v.replace('jev-', '').replace('table:', 't:').replace('live:', 'l:')[:9] for v in variants]
    print('%-14s' % 'workload' + ' '.join('%9s' % s for s in short))
    geo = {k: collections.defaultdict(list) for k in ('score', 'peak_rss_bytes')}
    for b in benches:
        if any(len(g.get((b, v), ())) < a.reps for v in variants):
            continue
        for k, label in (('score', b), ('peak_rss_bytes', '  rss')):
            base = st.median(r[k] for r in g[(b, 'mi')])
            cells = []
            for v in variants:
                x = st.median(r[k] for r in g[(b, v)]) / base
                geo[k][v].append(x)
                cells.append('%9.3f' % x)
            print('%-14s' % label + ' '.join(cells))
        if b in ('larson','larson-sized','xmalloc-test','glibc-thread'):
            # Compare resource cost per unit throughput within each repetition.
            # This is not RSS per live byte or a substitute for the RSS gate.
            base=st.median(r['peak_rss_bytes']*r['score'] for r in g[b,'mi'])
            print('%-14s' % '  rss/rate' + ' '.join('%9.3f' % (st.median(r['peak_rss_bytes']*r['score'] for r in g[b,v])/base) for v in variants))
    for k, label in (('score', 'GEOMEAN time'), ('peak_rss_bytes', 'GEOMEAN rss')):
        print('%-14s' % label + ' '.join('%9.3f' % (math.exp(sum(map(math.log, geo[k][v])) / len(geo[k][v])) if geo[k][v] else float('nan')) for v in variants))
    print('workloads complete:', len(geo['score']['mi']))
    print('rss/rate: median of peak RSS × inverse-throughput score, relative to mi; lower is better. This resource-efficiency diagnostic is not memory per live byte or a fixed-work RSS experiment.')


if __name__ == '__main__':
    main()
