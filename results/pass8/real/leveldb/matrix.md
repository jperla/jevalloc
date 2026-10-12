# pass8/leveldb

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| leveldb | mi | 1.856 [1.841, 1.863] | 1.000 | 1.463 [1.457, 1.475] | 1.000 | 199.1 [198.7, 199.4] | 1.000 | n/a |
| leveldb | jev-table:oracle | 1.869 [1.851, 1.881] | 1.007 | 1.486 [1.477, 1.509] | 1.016 | 199.5 [199.0, 199.6] | 1.002 | n/a |
| leveldb | jev-table:search | 1.876 [1.872, 1.880] | 1.011 | 1.494 [1.484, 1.502] | 1.021 | 199.2 [199.1, 199.4] | 1.001 | n/a |
