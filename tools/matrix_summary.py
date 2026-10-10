#!/usr/bin/env python3
"""Compact view of a benchmark matrix: every variant relative to plain mimalloc.

Prints score (time, or bench.sh's throughput-normalised time) and peak RSS as ratios to
`mi`, per workload and as geometric means, using only workloads with all repetitions.
"""
import argparse, collections, json, math, statistics as st

V = ['sys', 'mi', 'jev-none', 'jev-keyonly', 'jev-table:oracle', 'jev-table:random', 'jev-table:size',
     'jev-live:heuristic', 'jev-live:static-model', 'jev-live:model']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results', nargs='?', default='results/beelink.json')
    ap.add_argument('--reps', type=int, default=5)
    a = ap.parse_args()
    d = json.load(open(a.results))
    g = collections.defaultdict(list)
    for r in d['runs']:
        if r.get('exit_status') == 0 and not r.get('cold') and r.get('repetition', 0) >= 0:
            g[(r['benchmark'], r['variant'])].append(r)
    benches = list(dict.fromkeys(b for b, _ in g))
    short = [v.replace('jev-', '').replace('table:', 't:').replace('live:', 'l:')[:9] for v in V]
    print('%-14s' % 'workload' + ' '.join('%9s' % s for s in short))
    geo = {k: collections.defaultdict(list) for k in ('score', 'peak_rss_bytes')}
    for b in benches:
        if any(len(g.get((b, v), ())) < a.reps for v in V):
            continue
        for k, label in (('score', b), ('peak_rss_bytes', '  rss')):
            base = st.median(r[k] for r in g[(b, 'mi')])
            cells = []
            for v in V:
                x = st.median(r[k] for r in g[(b, v)]) / base
                geo[k][v].append(x)
                cells.append('%9.3f' % x)
            print('%-14s' % label + ' '.join(cells))
    for k, label in (('score', 'GEOMEAN time'), ('peak_rss_bytes', 'GEOMEAN rss')):
        print('%-14s' % label + ' '.join('%9.3f' % math.exp(sum(map(math.log, geo[k][v])) / len(geo[k][v])) for v in V))
    print('workloads complete:', len(geo['score']['mi']))


if __name__ == '__main__':
    main()
