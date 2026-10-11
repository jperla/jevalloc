# frag-instrument

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 1.087 [1.081, 1.088] | 1.000 | 0.085 [0.081, 0.087] | 1.000 | 280.1 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 1.124 [1.122, 1.127] | 1.035 | 0.123 [0.121, 0.126] | 1.442 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.224 [1.221, 1.226] | 1.127 | 0.223 [0.220, 0.225] | 2.609 | 214.0 [213.9, 214.1] | 0.764 | n/a |
| site-pure-1 | jev-table:random | 1.163 [1.155, 1.170] | 1.070 | 0.162 [0.154, 0.169] | 1.898 | 214.1 [214.0, 214.1] | 0.764 | n/a |
| site-pure-16 | mi | 1.042 [1.041, 1.043] | 1.000 | 0.459 [0.434, 0.466] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 1.046 [1.045, 1.047] | 1.004 | 0.480 [0.445, 0.513] | 1.044 | 298.5 [298.5, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-table:oracle | 1.055 [1.053, 1.057] | 1.012 | 0.641 [0.611, 0.650] | 1.396 | 222.2 [219.6, 224.6] | 0.745 | n/a |
| site-pure-16 | jev-table:random | 1.050 [1.048, 1.072] | 1.008 | 0.559 [0.492, 0.589] | 1.217 | 234.5 [234.4, 234.7] | 0.786 | n/a |
