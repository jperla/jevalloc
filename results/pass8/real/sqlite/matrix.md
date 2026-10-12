# pass8/sqlite

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sqlite | mi | 0.646 [0.643, 0.651] | 1.000 | 0.145 [0.142, 0.150] | 1.000 | 205.8 [205.7, 205.8] | 1.000 | n/a |
| sqlite | jev-table:oracle | 0.630 [0.628, 0.633] | 0.975 | 0.130 [0.128, 0.131] | 0.897 | 208.9 [208.9, 209.0] | 1.015 | n/a |
| sqlite | jev-table:search | 0.651 [0.649, 0.654] | 1.008 | 0.150 [0.148, 0.153] | 1.040 | 205.8 [205.8, 205.9] | 1.000 | n/a |
