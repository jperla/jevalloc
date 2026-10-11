# pass7/pure-stack-v1-nodesc

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 1.296 [1.292, 1.301] | 1.191 | 0.295 [0.291, 0.300] | 3.414 | 214.5 [214.2, 214.5] | 0.766 | n/a |
| site-pure-1 | mi | 1.087 [1.087, 1.112] | 1.000 | 0.086 [0.086, 0.089] | 1.000 | 280.0 [279.8, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-none | 1.089 [1.088, 1.091] | 1.001 | 0.088 [0.086, 0.089] | 1.014 | 280.0 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 1.124 [1.121, 1.126] | 1.033 | 0.123 [0.120, 0.125] | 1.424 | 280.0 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.223 [1.218, 1.224] | 1.125 | 0.222 [0.217, 0.223] | 2.566 | 213.8 [213.7, 214.1] | 0.764 | n/a |
| site-pure-1 | jev-table:random | 1.168 [1.167, 1.192] | 1.074 | 0.167 [0.166, 0.191] | 1.936 | 214.0 [213.9, 214.2] | 0.764 | n/a |
| site-pure-1 | jev-table:size | 1.118 [1.117, 1.120] | 1.028 | 0.117 [0.116, 0.119] | 1.360 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:all-transient | 1.120 [1.117, 1.122] | 1.030 | 0.119 [0.116, 0.120] | 1.377 | 280.1 [280.1, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:all-permanent | 1.120 [1.118, 1.146] | 1.030 | 0.119 [0.118, 0.121] | 1.377 | 280.1 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-live:heuristic | 1.167 [1.163, 1.170] | 1.073 | 0.157 [0.152, 0.160] | 1.821 | 286.5 [286.4, 286.6] | 1.023 | n/a |
| site-pure-1 | jev-live:static-model | 1.249 [1.245, 1.252] | 1.148 | 0.244 [0.240, 0.247] | 2.823 | 216.5 [216.3, 216.7] | 0.773 | n/a |
| site-pure-1 | jev-live:model | 1.163 [1.160, 1.168] | 1.069 | 0.153 [0.150, 0.158] | 1.775 | 288.6 [288.6, 288.8] | 1.031 | n/a |
| site-pure-16 | sys | 1.112 [1.108, 1.134] | 1.067 | 0.924 [0.891, 1.004] | 2.047 | 214.1 [214.0, 214.4] | 0.718 | n/a |
| site-pure-16 | mi | 1.042 [1.041, 1.069] | 1.000 | 0.452 [0.444, 0.503] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-none | 1.041 [1.039, 1.043] | 1.000 | 0.437 [0.427, 0.457] | 0.969 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 1.045 [1.042, 1.045] | 1.003 | 0.481 [0.455, 0.491] | 1.065 | 298.5 [298.5, 298.6] | 1.001 | n/a |
| site-pure-16 | jev-table:oracle | 1.055 [1.054, 1.078] | 1.013 | 0.645 [0.609, 0.657] | 1.428 | 220.9 [219.0, 224.6] | 0.741 | n/a |
| site-pure-16 | jev-table:random | 1.050 [1.046, 1.051] | 1.007 | 0.566 [0.518, 0.589] | 1.255 | 234.5 [234.4, 234.6] | 0.786 | n/a |
| site-pure-16 | jev-table:size | 1.047 [1.045, 1.048] | 1.005 | 0.506 [0.500, 0.531] | 1.120 | 298.4 [298.3, 298.4] | 1.000 | n/a |
| site-pure-16 | jev-table:all-transient | 1.047 [1.043, 1.073] | 1.005 | 0.502 [0.468, 0.537] | 1.111 | 298.6 [298.5, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-table:all-permanent | 1.047 [1.043, 1.068] | 1.005 | 0.505 [0.462, 0.547] | 1.118 | 298.6 [298.5, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-live:heuristic | 1.060 [1.059, 1.083] | 1.017 | 0.531 [0.497, 0.610] | 1.176 | 299.4 [296.6, 304.5] | 1.004 | n/a |
| site-pure-16 | jev-live:static-model | 1.064 [1.061, 1.065] | 1.021 | 0.679 [0.663, 0.679] | 1.503 | 231.4 [231.0, 232.2] | 0.776 | n/a |
| site-pure-16 | jev-live:model | 1.061 [1.058, 1.063] | 1.019 | 0.521 [0.499, 0.565] | 1.154 | 299.3 [294.8, 306.9] | 1.003 | n/a |
