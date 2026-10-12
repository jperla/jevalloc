# pass8/redis-mesh

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-mesh | mi | 3.823 [3.815, 3.843] | 1.000 | 1.370 [1.347, 1.386] | 1.000 | 185.8 [177.8, 185.9] | 1.000 | n/a |
| redis-mesh | jev-table:oracle | 3.907 [3.901, 3.918] | 1.022 | 1.484 [1.467, 1.497] | 1.083 | 186.0 [184.0, 188.0] | 1.001 | n/a |
| redis-mesh | jev-table:search | 3.911 [3.883, 3.947] | 1.023 | 1.485 [1.460, 1.507] | 1.084 | 185.9 [183.8, 186.0] | 1.001 | n/a |
