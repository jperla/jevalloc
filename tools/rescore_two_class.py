#!/usr/bin/env python3
"""Rescore prompt-study answers as two classes: short vs long (old "medium" counts as long).

A three-way answer is short when P(short) >= P(medium) + P(long); a yes/no pair is short
when P(temporary) >= P(retained).
"""
import collections, json, sys

for path in sys.argv[1:]:
    rows = json.load(open(path))
    print(path)
    for v in dict.fromkeys(r['variant'] for r in rows):
        c = collections.Counter(); per = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            if r['variant'] != v:
                continue
            p = r['probs']
            if 'temporary' in p:
                pred = 'short' if p['temporary'] >= p['retained'] else 'long'
            else:
                pred = 'short' if p.get('short', 0) >= p.get('medium', 0) + p.get('long', 0) else 'long'
            truth = 'short' if r['truth'] == 'short' else 'long'
            c[(truth, pred)] += 1
            per[r['program']][0] += truth == pred; per[r['program']][1] += 1
        ns, nl = c[('short', 'short')] + c[('short', 'long')], c[('long', 'long')] + c[('long', 'short')]
        rs, rl = c[('short', 'short')] / max(ns, 1), c[('long', 'long')] / max(nl, 1)
        print('  %-16s n=%d correct=%.0f%% balanced=%.0f%% short found=%.0f%% (of %d) long found=%.0f%% (of %d)  %s' % (
            v, ns + nl, 100 * (c[('short', 'short')] + c[('long', 'long')]) / (ns + nl), 50 * (rs + rl), 100 * rs, ns, 100 * rl, nl,
            ' '.join('%s:%d/%d' % (g.replace('-server', ''), a, b) for g, (a, b) in per.items())))
