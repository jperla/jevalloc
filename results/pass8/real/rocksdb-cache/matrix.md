# pass8/rocksdb-cache

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rocksdb-cache | mi | 5.574 [5.390, 5.816] | 1.000 | 63.768 [63.483, 64.207] | 1.000 | 134.3 [129.0, 144.1] | 1.000 | n/a |
| rocksdb-cache | jev-table:oracle | 5.773 [5.494, 6.223] | 1.036 | 64.417 [64.007, 64.853] | 1.010 | 136.4 [132.4, 143.7] | 1.016 | n/a |
| rocksdb-cache | jev-table:search | 5.699 [5.325, 7.298] | 1.022 | 64.811 [63.973, 65.267] | 1.016 | 136.2 [129.1, 156.1] | 1.014 | n/a |
