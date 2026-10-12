# pass9/site-mixed-16

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-16 | mi | 1.048 [1.046, 1.049] | 1.000 | 0.437 [0.398, 0.448] | 1.000 | 150.1 [147.4, 151.8] | 1.000 | n/a |
| site-mixed-16 | jev-keyonly | 1.056 [1.053, 1.079] | 1.008 | 0.538 [0.530, 0.602] | 1.231 | 152.2 [151.6, 153.6] | 1.014 | n/a |
| site-mixed-16 | jev-table:oracle-site | 1.055 [1.052, 1.057] | 1.006 | 0.540 [0.482, 0.546] | 1.236 | 154.0 [149.9, 155.5] | 1.026 | n/a |
| site-mixed-16 | jev-table:oracle-context | 1.045 [1.045, 1.047] | 0.997 | 0.544 [0.530, 0.556] | 1.245 | 118.1 [117.4, 126.7] | 0.787 | n/a |
| site-mixed-16 | jev-live:static-site | 1.065 [1.063, 1.069] | 1.016 | 0.565 [0.547, 0.633] | 1.293 | 154.2 [153.6, 157.6] | 1.027 | n/a |
| site-mixed-16 | jev-live:static-model | 1.055 [1.053, 1.061] | 1.007 | 0.580 [0.572, 0.648] | 1.327 | 126.5 [126.2, 127.4] | 0.843 | n/a |
| site-mixed-16 | jev-live:hybrid | 1.060 [1.059, 1.061] | 1.012 | 0.619 [0.591, 0.628] | 1.418 | 127.3 [126.3, 129.1] | 0.848 | n/a |
| site-mixed-16 | jev-live:heuristic | 1.054 [1.052, 1.057] | 1.006 | 0.445 [0.436, 0.481] | 1.018 | 169.0 [168.9, 169.3] | 1.126 | n/a |
