# pass9/site-mixed-16

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-16 | mi | 1.049 [1.047, 1.050] | 1.000 | 0.434 [0.414, 0.475] | 1.000 | 149.8 [146.5, 151.0] | 1.000 | n/a |
| site-mixed-16 | jev-keyonly | 1.059 [1.056, 1.083] | 1.009 | 0.563 [0.555, 0.609] | 1.297 | 152.5 [147.6, 154.3] | 1.018 | n/a |
| site-mixed-16 | jev-table:oracle-site | 1.055 [1.054, 1.057] | 1.005 | 0.536 [0.511, 0.554] | 1.235 | 153.1 [150.5, 154.1] | 1.022 | n/a |
| site-mixed-16 | jev-table:oracle-context | 1.046 [1.043, 1.050] | 0.997 | 0.558 [0.523, 0.607] | 1.285 | 119.6 [116.1, 121.4] | 0.799 | n/a |
| site-mixed-16 | jev-live:static-site | 1.066 [1.063, 1.068] | 1.017 | 0.565 [0.545, 0.616] | 1.302 | 156.4 [153.2, 158.6] | 1.044 | n/a |
| site-mixed-16 | jev-live:static-model | 1.059 [1.055, 1.062] | 1.009 | 0.567 [0.526, 0.630] | 1.306 | 126.5 [125.6, 127.5] | 0.844 | n/a |
| site-mixed-16 | jev-live:hybrid | 1.059 [1.057, 1.060] | 1.009 | 0.599 [0.596, 0.637] | 1.380 | 126.9 [126.8, 129.1] | 0.847 | n/a |
| site-mixed-16 | jev-live:heuristic | 1.054 [1.052, 1.056] | 1.005 | 0.439 [0.431, 0.465] | 1.011 | 169.0 [168.9, 169.2] | 1.129 | n/a |
