# pass8/redis-mesh

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-mesh | mi | 3.847 [3.838, 3.855] | 1.000 | 1.366 [1.358, 1.386] | 1.000 | 177.9 [177.7, 180.0] | 1.000 | n/a |
| redis-mesh | jev-table:oracle | 3.909 [3.904, 3.949] | 1.016 | 1.472 [1.470, 1.484] | 1.077 | 181.9 [179.9, 184.0] | 1.022 | n/a |
| redis-mesh | jev-table:search | 3.902 [3.893, 3.942] | 1.014 | 1.458 [1.456, 1.472] | 1.067 | 180.0 [177.9, 180.1] | 1.011 | n/a |
