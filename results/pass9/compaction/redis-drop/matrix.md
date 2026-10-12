# pass9/compaction/redis-drop

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-drop | mi | 11.916 [11.905, 11.931] | 1.000 | 0.336 [0.333, 0.341] | 1.000 | 275.8 [275.8, 277.9] | 1.000 | n/a |
| redis-drop | jev-keyonly | 12.006 [11.995, 12.013] | 1.008 | 0.536 [0.530, 0.543] | 1.596 | 292.0 [291.9, 294.0] | 1.059 | n/a |
| redis-drop | jev-table:oracle-site | 11.947 [11.940, 11.956] | 1.003 | 0.408 [0.395, 0.414] | 1.215 | 278.0 [277.8, 278.0] | 1.008 | n/a |
| redis-drop | jev-table:oracle-context | 12.012 [11.986, 12.031] | 1.008 | 0.528 [0.525, 0.531] | 1.574 | 293.9 [293.9, 294.0] | 1.066 | n/a |
| redis-drop | jev-table:search | 12.007 [11.993, 12.026] | 1.008 | 0.532 [0.516, 0.552] | 1.585 | 293.9 [293.7, 294.0] | 1.066 | n/a |
| redis-drop | mesh | 12.069 [12.068, 12.073] | 1.013 | 0.886 [0.871, 0.895] | 2.639 | 330.3 [330.1, 330.6] | 1.198 | n/a |
| redis-drop | nomesh | 11.972 [11.960, 11.977] | 1.005 | 0.530 [0.507, 0.535] | 1.579 | 330.5 [330.4, 331.0] | 1.198 | n/a |
