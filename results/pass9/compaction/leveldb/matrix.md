# pass9/compaction/leveldb

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| leveldb | mi | 11.373 [11.356, 11.408] | 1.000 | 1.464 [1.460, 1.475] | 1.000 | 198.8 [198.7, 199.1] | 1.000 | n/a |
| leveldb | jev-keyonly | 11.375 [11.352, 11.387] | 1.000 | 1.510 [1.488, 1.515] | 1.031 | 199.1 [198.9, 199.2] | 1.002 | n/a |
| leveldb | jev-table:oracle-site | 11.369 [11.346, 11.377] | 1.000 | 1.483 [1.476, 1.484] | 1.013 | 199.4 [199.1, 199.6] | 1.003 | n/a |
| leveldb | mesh | 11.444 [11.441, 11.472] | 1.006 | 1.454 [1.447, 1.465] | 0.993 | 236.9 [236.2, 237.6] | 1.191 | n/a |
| leveldb | nomesh | 11.431 [11.422, 11.445] | 1.005 | 1.401 [1.389, 1.411] | 0.957 | 237.1 [236.9, 237.5] | 1.192 | n/a |
