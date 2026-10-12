# pass9/per-alloc-small/performance

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| per-alloc-small | mi | 1.006 [1.006, 1.007] | 1.000 | 0.005 [0.005, 0.005] | 1.000 | 8.0 [8.0, 8.0] | 1.000 | n/a |
| per-alloc-small | jev-keyonly | 1.007 [1.007, 1.008] | 1.001 | 0.006 [0.006, 0.006] | 1.170 | 8.2 [8.0, 8.2] | 1.021 | n/a |
| per-alloc-small | jev-table:oracle-site | 1.007 [1.007, 1.032] | 1.001 | 0.006 [0.006, 0.006] | 1.191 | 8.2 [8.2, 8.2] | 1.022 | n/a |
| per-alloc-small | jev-table:oracle-context | 1.007 [1.006, 1.007] | 1.001 | 0.006 [0.005, 0.006] | 1.207 | 6.1 [6.1, 6.2] | 0.768 | n/a |
| per-alloc-small | jev-live:per-alloc | 1.820 [1.794, 1.837] | 1.809 | 0.165 [0.156, 0.165] | 32.843 | 8.1 [8.1, 8.2] | 1.012 | n/a |
