# pass8/redis-sessions

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-sessions | mi | 3.698 [3.661, 3.803] | 1.000 | 0.354 [0.345, 0.364] | 1.000 | 201.9 [201.6, 203.7] | 1.000 | n/a |
| redis-sessions | jev-table:oracle | 3.809 [3.703, 3.812] | 1.030 | 0.376 [0.371, 0.381] | 1.062 | 203.7 [203.6, 203.9] | 1.009 | n/a |
| redis-sessions | jev-table:search | 3.700 [3.686, 3.812] | 1.001 | 0.379 [0.376, 0.381] | 1.070 | 201.9 [201.9, 203.5] | 1.000 | n/a |
