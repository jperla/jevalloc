# frag-instrument

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 1.085 [1.084, 1.087] | 1.000 | 0.084 [0.083, 0.085] | 1.000 | 280.0 [280.0, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 1.148 [1.147, 1.151] | 1.058 | 0.147 [0.145, 0.150] | 1.754 | 280.0 [279.9, 280.0] | 1.000 | n/a |
| site-pure-1 | jev-table:oracle | 1.192 [1.183, 1.196] | 1.099 | 0.191 [0.182, 0.195] | 2.278 | 213.8 [213.7, 213.8] | 0.763 | n/a |
| site-pure-16 | mi | 1.040 [1.036, 1.041] | 1.000 | 0.455 [0.397, 0.468] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 1.048 [1.047, 1.049] | 1.008 | 0.509 [0.494, 0.555] | 1.117 | 298.4 [298.4, 298.4] | 1.000 | n/a |
| site-pure-16 | jev-table:oracle | 1.049 [1.047, 1.052] | 1.008 | 0.568 [0.535, 0.586] | 1.248 | 229.7 [229.2, 230.0] | 0.770 | n/a |
