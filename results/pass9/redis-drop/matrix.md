# pass9/redis-drop

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-drop | mi | 2.421 [2.419, 2.438] | 1.000 | 0.326 [0.317, 0.331] | 1.000 | 277.7 [275.8, 277.9] | 1.000 | n/a |
| redis-drop | jev-keyonly | 2.491 [2.487, 2.516] | 1.029 | 0.519 [0.517, 0.535] | 1.589 | 293.7 [291.9, 293.9] | 1.058 | n/a |
| redis-drop | jev-table:oracle-site | 2.451 [2.431, 2.460] | 1.012 | 0.403 [0.397, 0.408] | 1.235 | 278.0 [278.0, 278.0] | 1.001 | n/a |
| redis-drop | jev-table:oracle-context | 2.511 [2.490, 2.519] | 1.037 | 0.515 [0.507, 0.523] | 1.577 | 293.9 [293.8, 294.0] | 1.058 | n/a |
| redis-drop | jev-table:search | 2.498 [2.477, 2.503] | 1.032 | 0.513 [0.501, 0.525] | 1.572 | 293.9 [291.8, 294.0] | 1.058 | n/a |
