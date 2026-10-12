# pass9/site-mixed-1

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-1 | mi | 1.150 [1.146, 1.173] | 1.000 | 0.145 [0.144, 0.149] | 1.000 | 145.8 [145.7, 145.8] | 1.000 | n/a |
| site-mixed-1 | jev-keyonly | 1.217 [1.216, 1.245] | 1.058 | 0.216 [0.215, 0.220] | 1.486 | 146.0 [145.8, 146.0] | 1.002 | n/a |
| site-mixed-1 | jev-table:oracle-site | 1.214 [1.213, 1.219] | 1.056 | 0.213 [0.212, 0.218] | 1.467 | 146.0 [145.9, 146.0] | 1.001 | n/a |
| site-mixed-1 | jev-table:oracle-context | 1.221 [1.217, 1.223] | 1.062 | 0.220 [0.216, 0.221] | 1.515 | 111.9 [111.8, 112.0] | 0.768 | n/a |
| site-mixed-1 | jev-live:static-site | 1.232 [1.231, 1.241] | 1.072 | 0.228 [0.227, 0.236] | 1.571 | 146.5 [146.4, 146.6] | 1.005 | n/a |
| site-mixed-1 | jev-live:static-model | 1.244 [1.240, 1.259] | 1.082 | 0.238 [0.234, 0.253] | 1.636 | 114.6 [114.6, 114.7] | 0.786 | n/a |
| site-mixed-1 | jev-live:hybrid | 1.261 [1.253, 1.270] | 1.097 | 0.255 [0.246, 0.263] | 1.751 | 114.6 [114.4, 114.8] | 0.786 | n/a |
| site-mixed-1 | jev-live:heuristic | 1.197 [1.183, 1.201] | 1.040 | 0.183 [0.169, 0.186] | 1.259 | 146.6 [146.4, 146.7] | 1.006 | n/a |
