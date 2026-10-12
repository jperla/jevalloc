# pass8/redis-drop

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-drop | mi | 2.432 [2.405, 2.440] | 1.000 | 0.319 [0.312, 0.330] | 1.000 | 277.8 [275.6, 277.9] | 1.000 | n/a |
| redis-drop | jev-table:oracle | 2.432 [2.414, 2.442] | 1.000 | 0.358 [0.342, 0.362] | 1.120 | 278.0 [277.9, 278.0] | 1.001 | n/a |
| redis-drop | jev-table:search | 2.435 [2.418, 2.470] | 1.001 | 0.349 [0.340, 0.371] | 1.093 | 277.9 [277.9, 278.0] | 1.000 | n/a |
