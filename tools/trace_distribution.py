#!/usr/bin/env python3
"""Audit object-byte lifetimes separately from byte-majority site labels."""
import argparse
import hashlib
import json
from pathlib import Path

from common import oracle, sites, class_bytes


def distribution(trace, table, short_bytes=None):
    rows = sites(trace)
    labels = dict(line.split() for line in table.read_text().splitlines() if line.strip())
    counts, actual, assigned = [0] * 2, [0] * 2, [0] * 2
    mismatches = 0
    for row in rows:
        cls = oracle(row,short_bytes)
        counts[cls] += 1
        weights = class_bytes(row,short_bytes)
        for i, weight in enumerate(weights):
            actual[i] += weight
        assigned[cls] += sum(weights)
        mismatches += labels.get(row['key']) != str(cls)
    total = sum(actual)
    return dict(class_schema="transient-permanent-v1",classes=["transient","permanent"],sites=counts,
                actual_object_byte_shares=[n / total if total else 0 for n in actual],
                majority_site_byte_shares=[n / total if total else 0 for n in assigned],
                total_requested_bytes=total, oracle_mismatches=mismatches,
                trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--short-bytes',type=int,default=None)
    parser.add_argument('root', type=Path, help='directory containing traces/ and tables/')
    args = parser.parse_args()
    output = {p.stem: distribution(p, args.root / 'tables' / p.stem / 'oracle.txt',args.short_bytes)
              for p in sorted((args.root / 'traces').glob('*.jsonl'))}
    print(json.dumps(output, indent=2))
    raise SystemExit(1 if any(r['oracle_mismatches'] for r in output.values()) else 0)
