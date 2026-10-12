# pass8/pure

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 1.088 [1.087, 1.089] | 1.000 | 0.086 [0.085, 0.088] | 1.000 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.221 [1.215, 1.225] | 1.123 | 0.220 [0.214, 0.224] | 2.545 | 213.8 [213.7, 213.9] | 0.763 | n/a |
| site-pure-1 | jev-live:static-model | 1.245 [1.242, 1.267] | 1.145 | 0.240 [0.237, 0.244] | 2.776 | 216.5 [216.5, 216.7] | 0.773 | n/a |
| site-pure-1 | jev-live:hybrid | 1.256 [1.254, 1.289] | 1.155 | 0.251 [0.249, 0.284] | 2.907 | 216.5 [216.4, 216.5] | 0.773 | n/a |
| site-pure-1 | jev-live:heuristic | 1.167 [1.167, 1.171] | 1.073 | 0.157 [0.157, 0.161] | 1.817 | 286.6 [286.5, 286.7] | 1.023 | n/a |
| site-pure-16 | mi | 1.043 [1.041, 1.045] | 1.000 | 0.472 [0.435, 0.502] | 1.000 | 298.3 [298.3, 298.5] | 1.000 | n/a |
| site-pure-16 | jev-table:oracle | 1.057 [1.052, 1.079] | 1.013 | 0.656 [0.588, 0.682] | 1.390 | 221.5 [220.6, 223.2] | 0.743 | n/a |
| site-pure-16 | jev-live:static-model | 1.065 [1.059, 1.068] | 1.021 | 0.693 [0.680, 0.737] | 1.468 | 232.1 [228.7, 234.5] | 0.778 | n/a |
| site-pure-16 | jev-live:hybrid | 1.066 [1.059, 1.066] | 1.022 | 0.703 [0.649, 0.728] | 1.488 | 232.3 [230.5, 232.6] | 0.779 | n/a |
| site-pure-16 | jev-live:heuristic | 1.063 [1.059, 1.076] | 1.019 | 0.565 [0.506, 0.609] | 1.197 | 296.2 [295.4, 306.5] | 0.993 | n/a |
