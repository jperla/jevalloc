# pass9/compaction/sqlite

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sqlite | mi | 10.147 [10.147, 10.148] | 1.000 | 0.146 [0.146, 0.147] | 1.000 | 205.8 [205.8, 205.8] | 1.000 | n/a |
| sqlite | jev-keyonly | 10.154 [10.149, 10.156] | 1.001 | 0.154 [0.149, 0.156] | 1.051 | 205.8 [205.7, 206.0] | 1.000 | n/a |
| sqlite | jev-table:oracle-site | 10.134 [10.131, 10.135] | 0.999 | 0.133 [0.131, 0.134] | 0.908 | 209.0 [208.8, 209.0] | 1.016 | n/a |
| sqlite | mesh | 10.439 [10.436, 10.443] | 1.029 | 0.439 [0.435, 0.443] | 3.000 | 317.1 [316.9, 317.4] | 1.541 | n/a |
| sqlite | nomesh | 10.295 [10.292, 10.300] | 1.015 | 0.294 [0.291, 0.300] | 2.011 | 317.2 [317.1, 317.5] | 1.542 | n/a |
