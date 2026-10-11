# pass7/pure-stack-v1

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 1.296 [1.293, 1.324] | 1.192 | 0.295 [0.292, 0.298] | 3.415 | 214.4 [214.2, 214.5] | 0.766 | n/a |
| site-pure-1 | mi | 1.087 [1.086, 1.088] | 1.000 | 0.086 [0.086, 0.087] | 1.000 | 280.0 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-none | 1.088 [1.087, 1.089] | 1.000 | 0.087 [0.085, 0.087] | 1.006 | 280.0 [279.8, 280.0] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 1.124 [1.121, 1.146] | 1.034 | 0.123 [0.120, 0.145] | 1.428 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.223 [1.222, 1.226] | 1.125 | 0.222 [0.221, 0.225] | 2.568 | 213.8 [213.7, 214.0] | 0.764 | n/a |
| site-pure-1 | jev-table:random | 1.165 [1.161, 1.190] | 1.071 | 0.164 [0.159, 0.164] | 1.901 | 214.1 [214.1, 214.1] | 0.765 | n/a |
| site-pure-1 | jev-table:size | 1.117 [1.117, 1.120] | 1.027 | 0.117 [0.116, 0.119] | 1.352 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:all-transient | 1.117 [1.116, 1.146] | 1.027 | 0.116 [0.115, 0.144] | 1.343 | 280.1 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:all-permanent | 1.118 [1.117, 1.119] | 1.028 | 0.117 [0.116, 0.118] | 1.352 | 280.1 [280.0, 280.2] | 1.000 | n/a |
| site-pure-1 | jev-live:heuristic | 1.169 [1.162, 1.173] | 1.075 | 0.159 [0.151, 0.163] | 1.839 | 286.5 [286.4, 286.6] | 1.023 | n/a |
| site-pure-1 | jev-live:static-model | 1.249 [1.244, 1.251] | 1.148 | 0.244 [0.239, 0.246] | 2.829 | 216.6 [216.5, 216.6] | 0.773 | n/a |
| site-pure-1 | jev-live:model | 1.163 [1.160, 1.200] | 1.069 | 0.152 [0.151, 0.189] | 1.761 | 288.7 [288.6, 288.9] | 1.031 | n/a |
| site-pure-16 | sys | 1.107 [1.107, 1.109] | 1.063 | 0.966 [0.885, 1.065] | 2.110 | 214.1 [214.0, 214.2] | 0.718 | n/a |
| site-pure-16 | mi | 1.042 [1.038, 1.066] | 1.000 | 0.458 [0.415, 0.483] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-none | 1.042 [1.040, 1.044] | 1.000 | 0.452 [0.423, 0.476] | 0.987 | 298.3 [298.3, 298.5] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 1.046 [1.043, 1.048] | 1.004 | 0.502 [0.456, 0.541] | 1.097 | 298.5 [298.5, 298.6] | 1.001 | n/a |
| site-pure-16 | jev-table:oracle | 1.055 [1.053, 1.065] | 1.013 | 0.629 [0.623, 0.671] | 1.374 | 222.4 [219.1, 224.3] | 0.746 | n/a |
| site-pure-16 | jev-table:random | 1.051 [1.048, 1.053] | 1.008 | 0.567 [0.534, 0.591] | 1.238 | 234.6 [234.4, 234.7] | 0.786 | n/a |
| site-pure-16 | jev-table:size | 1.049 [1.044, 1.070] | 1.007 | 0.510 [0.431, 0.534] | 1.115 | 298.4 [298.3, 298.4] | 1.000 | n/a |
| site-pure-16 | jev-table:all-transient | 1.047 [1.043, 1.050] | 1.005 | 0.519 [0.469, 0.541] | 1.134 | 298.5 [298.5, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-table:all-permanent | 1.047 [1.043, 1.070] | 1.005 | 0.518 [0.456, 0.535] | 1.132 | 298.5 [298.5, 298.6] | 1.001 | n/a |
| site-pure-16 | jev-live:heuristic | 1.062 [1.061, 1.076] | 1.020 | 0.552 [0.518, 0.576] | 1.205 | 300.9 [298.1, 303.5] | 1.009 | n/a |
| site-pure-16 | jev-live:static-model | 1.061 [1.059, 1.064] | 1.019 | 0.650 [0.645, 0.701] | 1.420 | 232.4 [227.7, 235.2] | 0.779 | n/a |
| site-pure-16 | jev-live:model | 1.066 [1.061, 1.081] | 1.023 | 0.582 [0.554, 0.607] | 1.271 | 296.3 [293.9, 303.3] | 0.993 | n/a |
