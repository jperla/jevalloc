# pass9/compaction/site-mixed-1

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-1 | mi | 20.651 [20.648, 20.652] | 1.000 | 0.150 [0.147, 0.150] | 1.000 | 145.8 [145.7, 145.9] | 1.000 | n/a |
| site-mixed-1 | jev-keyonly | 20.725 [20.719, 20.732] | 1.004 | 0.224 [0.217, 0.231] | 1.494 | 145.9 [145.9, 146.1] | 1.001 | n/a |
| site-mixed-1 | jev-table:oracle-site | 20.715 [20.710, 20.718] | 1.003 | 0.213 [0.209, 0.217] | 1.420 | 145.9 [145.9, 146.0] | 1.001 | n/a |
| site-mixed-1 | jev-table:oracle-context | 20.728 [20.722, 20.737] | 1.004 | 0.225 [0.220, 0.236] | 1.501 | 111.9 [111.9, 112.0] | 0.768 | n/a |
| site-mixed-1 | jev-live:static-site | 20.743 [20.737, 20.748] | 1.004 | 0.234 [0.233, 0.238] | 1.558 | 146.6 [146.5, 146.7] | 1.005 | n/a |
| site-mixed-1 | jev-live:static-model | 20.768 [20.746, 20.775] | 1.006 | 0.261 [0.240, 0.268] | 1.740 | 114.6 [114.6, 114.7] | 0.786 | n/a |
| site-mixed-1 | jev-live:hybrid | 20.760 [20.755, 20.762] | 1.005 | 0.253 [0.250, 0.255] | 1.689 | 114.6 [114.4, 114.7] | 0.786 | n/a |
| site-mixed-1 | jev-live:heuristic | 20.683 [20.680, 20.699] | 1.002 | 0.168 [0.166, 0.185] | 1.120 | 146.6 [146.5, 146.7] | 1.005 | n/a |
| site-mixed-1 | mesh | 20.836 [20.832, 20.838] | 1.009 | 0.330 [0.327, 0.332] | 2.201 | 142.0 [140.9, 144.4] | 0.974 | n/a |
| site-mixed-1 | nomesh | 20.687 [20.684, 20.688] | 1.002 | 0.185 [0.184, 0.187] | 1.233 | 170.0 [169.9, 170.0] | 1.166 | n/a |
