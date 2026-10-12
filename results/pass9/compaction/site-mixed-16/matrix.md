# pass9/compaction/site-mixed-16

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-16 | mi | 20.550 [20.548, 20.551] | 1.000 | 0.446 [0.432, 0.467] | 1.000 | 148.9 [147.2, 150.7] | 1.000 | n/a |
| site-mixed-16 | jev-keyonly | 20.559 [20.557, 20.559] | 1.000 | 0.580 [0.540, 0.590] | 1.301 | 151.4 [151.1, 153.6] | 1.017 | n/a |
| site-mixed-16 | jev-table:oracle-site | 20.558 [20.555, 20.565] | 1.000 | 0.538 [0.530, 0.582] | 1.208 | 152.1 [149.6, 156.1] | 1.021 | n/a |
| site-mixed-16 | jev-table:oracle-context | 20.550 [20.547, 20.553] | 1.000 | 0.565 [0.552, 0.587] | 1.268 | 117.4 [116.2, 121.9] | 0.788 | n/a |
| site-mixed-16 | jev-live:static-site | 20.565 [20.564, 20.567] | 1.001 | 0.571 [0.560, 0.587] | 1.282 | 153.8 [153.6, 156.4] | 1.033 | n/a |
| site-mixed-16 | jev-live:static-model | 20.559 [20.558, 20.562] | 1.000 | 0.591 [0.582, 0.619] | 1.326 | 127.1 [125.7, 127.3] | 0.854 | n/a |
| site-mixed-16 | jev-live:hybrid | 20.561 [20.557, 20.584] | 1.001 | 0.623 [0.620, 0.648] | 1.398 | 127.1 [127.1, 129.4] | 0.854 | n/a |
| site-mixed-16 | jev-live:heuristic | 20.555 [20.554, 20.559] | 1.000 | 0.446 [0.443, 0.468] | 1.001 | 169.2 [169.0, 169.3] | 1.136 | n/a |
| site-mixed-16 | mesh | 20.695 [20.691, 20.698] | 1.007 | 0.461 [0.448, 0.465] | 1.035 | 147.7 [147.6, 148.1] | 0.991 | n/a |
| site-mixed-16 | nomesh | 20.607 [20.603, 20.610] | 1.003 | 0.360 [0.348, 0.366] | 0.808 | 171.6 [171.2, 171.9] | 1.152 | n/a |
