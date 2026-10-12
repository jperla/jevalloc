# pass9/site-mixed-1

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-mixed-1 | mi | 1.146 [1.145, 1.149] | 1.000 | 0.146 [0.144, 0.148] | 1.000 | 145.9 [145.8, 145.9] | 1.000 | n/a |
| site-mixed-1 | jev-keyonly | 1.225 [1.213, 1.228] | 1.069 | 0.224 [0.213, 0.227] | 1.533 | 146.0 [145.8, 146.1] | 1.001 | n/a |
| site-mixed-1 | jev-table:oracle-site | 1.210 [1.205, 1.213] | 1.056 | 0.209 [0.204, 0.211] | 1.433 | 146.0 [145.9, 146.1] | 1.001 | n/a |
| site-mixed-1 | jev-table:oracle-context | 1.216 [1.215, 1.220] | 1.061 | 0.215 [0.214, 0.219] | 1.473 | 111.9 [111.8, 111.9] | 0.767 | n/a |
| site-mixed-1 | jev-live:static-site | 1.235 [1.235, 1.240] | 1.077 | 0.230 [0.230, 0.236] | 1.579 | 146.6 [146.2, 146.6] | 1.005 | n/a |
| site-mixed-1 | jev-live:static-model | 1.271 [1.243, 1.281] | 1.108 | 0.246 [0.236, 0.255] | 1.686 | 114.6 [114.6, 114.7] | 0.786 | n/a |
| site-mixed-1 | jev-live:hybrid | 1.254 [1.248, 1.271] | 1.094 | 0.247 [0.243, 0.263] | 1.694 | 114.6 [114.5, 114.6] | 0.785 | n/a |
| site-mixed-1 | jev-live:heuristic | 1.182 [1.180, 1.199] | 1.031 | 0.168 [0.166, 0.185] | 1.150 | 146.6 [146.5, 146.6] | 1.005 | n/a |
