# pass9/redis-sessions

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-sessions | mi | 3.713 [3.698, 3.805] | 1.000 | 0.363 [0.350, 0.369] | 1.000 | 201.8 [201.6, 201.9] | 1.000 | n/a |
| redis-sessions | jev-keyonly | 3.768 [3.667, 3.872] | 1.015 | 0.424 [0.421, 0.428] | 1.169 | 202.0 [201.9, 203.8] | 1.001 | n/a |
| redis-sessions | jev-table:oracle-site | 3.770 [3.672, 3.871] | 1.016 | 0.421 [0.415, 0.432] | 1.160 | 203.8 [203.8, 204.0] | 1.010 | n/a |
| redis-sessions | jev-table:oracle-context | 3.818 [3.707, 3.894] | 1.028 | 0.416 [0.410, 0.417] | 1.146 | 203.8 [203.7, 203.9] | 1.010 | n/a |
| redis-sessions | jev-table:search | 3.815 [3.772, 3.866] | 1.028 | 0.416 [0.407, 0.428] | 1.145 | 202.0 [201.7, 204.0] | 1.001 | n/a |
