# pass8/rocksdb-churn

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rocksdb-churn | mi | 85.823 [84.399, 87.787] | 1.000 | 284.100 [270.637, 286.935] | 1.000 | 101.7 [98.4, 103.1] | 1.000 | n/a |
| rocksdb-churn | jev-table:oracle | 87.780 [84.604, 89.337] | 1.023 | 279.291 [255.516, 286.703] | 0.983 | 102.6 [101.5, 107.9] | 1.009 | n/a |
| rocksdb-churn | jev-table:search | 85.599 [83.771, 87.004] | 0.997 | 286.242 [264.214, 289.848] | 1.008 | 103.0 [101.5, 105.1] | 1.012 | n/a |
