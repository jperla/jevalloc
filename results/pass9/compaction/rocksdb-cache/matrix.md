# pass9/compaction/rocksdb-cache

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rocksdb-cache | mi | 15.244 [14.747, 17.309] | 1.000 | 63.573 [62.418, 63.995] | 1.000 | 140.8 [128.6, 149.2] | 1.000 | n/a |
| rocksdb-cache | jev-keyonly | 15.052 [14.764, 15.295] | 0.987 | 63.450 [63.188, 63.781] | 0.998 | 132.1 [127.7, 140.7] | 0.938 | n/a |
| rocksdb-cache | jev-table:oracle-site | 15.209 [14.762, 15.863] | 0.998 | 63.482 [63.034, 63.837] | 0.999 | 129.4 [127.7, 154.6] | 0.919 | n/a |
| rocksdb-cache | mesh | 15.127 [14.587, 17.152] | 0.992 | 62.509 [62.044, 64.206] | 0.983 | 119.7 [117.5, 121.1] | 0.850 | n/a |
| rocksdb-cache | nomesh | 14.914 [14.646, 15.078] | 0.978 | 61.904 [61.845, 62.263] | 0.974 | 128.0 [127.3, 129.8] | 0.909 | n/a |
