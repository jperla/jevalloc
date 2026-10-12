# pass9/redis-mesh

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-mesh | mi | 3.816 [3.805, 3.854] | 1.000 | 1.343 [1.323, 1.380] | 1.000 | 185.9 [181.8, 185.9] | 1.000 | n/a |
| redis-mesh | jev-keyonly | 4.243 [4.209, 4.268] | 1.112 | 1.747 [1.719, 1.755] | 1.301 | 182.0 [178.0, 186.1] | 0.979 | n/a |
| redis-mesh | jev-table:oracle-site | 4.103 [4.040, 4.183] | 1.075 | 1.634 [1.618, 1.678] | 1.217 | 187.8 [183.9, 188.0] | 1.010 | n/a |
| redis-mesh | jev-table:oracle-context | 4.138 [3.997, 4.249] | 1.084 | 1.655 [1.619, 1.677] | 1.232 | 195.8 [190.1, 196.0] | 1.053 | n/a |
| redis-mesh | jev-table:search | 4.097 [4.055, 4.149] | 1.073 | 1.643 [1.625, 1.672] | 1.224 | 180.1 [178.0, 186.0] | 0.969 | n/a |
