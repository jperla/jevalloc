# pass9/compaction/redis-mesh

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-mesh | mi | 22.825 [22.805, 22.845] | 1.000 | 1.354 [1.337, 1.374] | 1.000 | 185.9 [185.8, 185.9] | 1.000 | n/a |
| redis-mesh | jev-keyonly | 23.279 [23.216, 23.288] | 1.020 | 1.779 [1.742, 1.800] | 1.314 | 185.8 [185.8, 186.0] | 0.999 | n/a |
| redis-mesh | jev-table:oracle-site | 23.134 [23.065, 23.335] | 1.014 | 1.660 [1.650, 1.732] | 1.226 | 187.9 [187.5, 188.0] | 1.011 | n/a |
| redis-mesh | jev-table:oracle-context | 23.129 [23.114, 23.168] | 1.013 | 1.655 [1.644, 1.696] | 1.222 | 196.0 [195.9, 196.1] | 1.054 | n/a |
| redis-mesh | jev-table:search | 23.160 [23.074, 23.259] | 1.015 | 1.702 [1.664, 1.750] | 1.257 | 186.0 [185.9, 186.1] | 1.000 | n/a |
| redis-mesh | mesh | 23.485 [23.462, 23.510] | 1.029 | 2.134 [2.129, 2.153] | 1.576 | 188.7 [188.1, 190.1] | 1.015 | n/a |
| redis-mesh | nomesh | 23.237 [23.208, 23.269] | 1.018 | 1.803 [1.784, 1.825] | 1.331 | 198.0 [197.4, 198.2] | 1.065 | n/a |
