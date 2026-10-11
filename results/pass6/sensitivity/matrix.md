# frag-sensitivity

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 1.088 [1.086, 1.090] | 1.000 | 0.087 [0.085, 0.088] | 1.000 | 280.1 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle-P-25 | 1.223 [1.220, 1.232] | 1.124 | 0.221 [0.219, 0.231] | 2.543 | 213.8 [213.7, 213.9] | 0.764 | n/a |
| site-pure-1 | jev-table:oracle | 1.224 [1.219, 1.256] | 1.125 | 0.223 [0.217, 0.255] | 2.560 | 213.9 [213.8, 214.1] | 0.764 | n/a |
| site-pure-1 | jev-table:oracle-P-90 | 1.224 [1.219, 1.227] | 1.125 | 0.223 [0.218, 0.226] | 2.557 | 213.9 [213.8, 214.0] | 0.764 | n/a |
| site-pure-1 | jev-table:oracle-P-never | 1.222 [1.219, 1.224] | 1.123 | 0.221 [0.218, 0.223] | 2.542 | 213.9 [213.7, 214.1] | 0.764 | n/a |
| site-pure-1 | jev-table:oracle-S-65536 | 1.114 [1.113, 1.116] | 1.024 | 0.112 [0.111, 0.115] | 1.290 | 279.9 [279.7, 279.9] | 0.999 | n/a |
| site-pure-1 | jev-table:oracle-S-1048576 | 1.113 [1.112, 1.115] | 1.023 | 0.111 [0.111, 0.114] | 1.280 | 279.9 [279.7, 279.9] | 0.999 | n/a |
| site-pure-1 | jev-table:oracle-S-16777216 | 1.113 [1.111, 1.114] | 1.023 | 0.111 [0.109, 0.113] | 1.273 | 279.9 [279.8, 279.9] | 0.999 | n/a |
| site-pure-16 | mi | 1.041 [1.037, 1.043] | 1.000 | 0.445 [0.398, 0.493] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-table:oracle-P-25 | 1.057 [1.056, 1.079] | 1.015 | 0.660 [0.644, 0.672] | 1.483 | 221.1 [219.4, 222.4] | 0.741 | n/a |
| site-pure-16 | jev-table:oracle | 1.055 [1.053, 1.056] | 1.013 | 0.625 [0.620, 0.663] | 1.404 | 220.9 [218.6, 223.1] | 0.741 | n/a |
| site-pure-16 | jev-table:oracle-P-90 | 1.055 [1.053, 1.060] | 1.013 | 0.623 [0.600, 0.685] | 1.400 | 220.4 [218.5, 223.6] | 0.739 | n/a |
| site-pure-16 | jev-table:oracle-P-never | 1.056 [1.050, 1.082] | 1.014 | 0.653 [0.625, 0.682] | 1.467 | 221.5 [219.0, 222.9] | 0.742 | n/a |
| site-pure-16 | jev-table:oracle-S-65536 | 1.048 [1.043, 1.049] | 1.007 | 0.500 [0.450, 0.526] | 1.124 | 295.1 [294.3, 296.0] | 0.989 | n/a |
| site-pure-16 | jev-table:oracle-S-1048576 | 1.047 [1.045, 1.051] | 1.006 | 0.516 [0.477, 0.540] | 1.159 | 295.7 [294.8, 296.1] | 0.991 | n/a |
| site-pure-16 | jev-table:oracle-S-16777216 | 1.047 [1.046, 1.049] | 1.006 | 0.512 [0.504, 0.544] | 1.150 | 295.2 [294.6, 295.8] | 0.989 | n/a |
