# frag-instrument

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 1.088 [1.086, 1.089] | 1.000 | 0.086 [0.085, 0.088] | 1.000 | 280.1 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 1.125 [1.123, 1.127] | 1.034 | 0.123 [0.122, 0.125] | 1.436 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.217 [1.215, 1.247] | 1.119 | 0.215 [0.214, 0.246] | 2.509 | 214.0 [213.9, 214.1] | 0.764 | n/a |
| site-pure-1 | jev-table:random | 1.163 [1.160, 1.164] | 1.069 | 0.161 [0.158, 0.163] | 1.880 | 214.1 [214.0, 214.1] | 0.764 | n/a |
| site-pure-16 | mi | 1.041 [1.039, 1.045] | 1.000 | 0.444 [0.408, 0.519] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 1.047 [1.044, 1.050] | 1.007 | 0.507 [0.475, 0.566] | 1.141 | 298.7 [298.5, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-table:oracle | 1.055 [1.055, 1.060] | 1.014 | 0.648 [0.635, 0.682] | 1.460 | 219.4 [218.9, 225.6] | 0.735 | n/a |
| site-pure-16 | jev-table:random | 1.048 [1.047, 1.050] | 1.007 | 0.537 [0.516, 0.570] | 1.209 | 234.5 [234.4, 234.7] | 0.786 | n/a |
