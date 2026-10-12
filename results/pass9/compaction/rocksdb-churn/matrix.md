# pass9/compaction/rocksdb-churn

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rocksdb-churn | mi | 95.308 [93.681, 96.427] | 1.000 | 271.123 [260.842, 287.222] | 1.000 | 102.8 [98.0, 103.7] | 1.000 | n/a |
| rocksdb-churn | jev-keyonly | 92.909 [91.084, 93.749] | 0.975 | 259.962 [251.267, 284.014] | 0.959 | 100.1 [97.0, 105.8] | 0.974 | n/a |
| rocksdb-churn | jev-table:oracle-site | 93.031 [85.576, 94.905] | 0.976 | 271.983 [260.672, 287.328] | 1.003 | 105.3 [103.6, 109.3] | 1.025 | n/a |
| rocksdb-churn | mesh | 92.487 [88.847, 97.907] | 0.970 | 249.609 [236.281, 254.660] | 0.921 | 71.2 [70.0, 74.3] | 0.693 | n/a |
| rocksdb-churn | nomesh | 91.235 [87.758, 94.240] | 0.957 | 245.783 [231.491, 258.800] | 0.907 | 84.5 [81.9, 89.5] | 0.822 | n/a |
