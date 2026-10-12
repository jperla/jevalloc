# pass9/compaction/redis-sessions

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| redis-sessions | mi | 13.211 [13.205, 13.312] | 1.000 | 0.363 [0.361, 0.368] | 1.000 | 201.7 [201.2, 203.7] | 1.000 | n/a |
| redis-sessions | jev-keyonly | 13.198 [13.165, 13.272] | 0.999 | 0.425 [0.420, 0.447] | 1.170 | 202.0 [201.4, 202.1] | 1.001 | n/a |
| redis-sessions | jev-table:oracle-site | 13.266 [13.164, 13.374] | 1.004 | 0.420 [0.414, 0.427] | 1.158 | 203.8 [201.7, 204.0] | 1.010 | n/a |
| redis-sessions | jev-table:oracle-context | 13.266 [13.214, 13.365] | 1.004 | 0.422 [0.411, 0.425] | 1.162 | 204.0 [203.7, 205.9] | 1.011 | n/a |
| redis-sessions | jev-table:search | 13.264 [13.171, 13.312] | 1.004 | 0.421 [0.417, 0.428] | 1.161 | 201.9 [201.4, 202.0] | 1.001 | n/a |
| redis-sessions | mesh | 13.480 [13.378, 13.584] | 1.020 | 0.754 [0.737, 0.759] | 2.076 | 269.1 [268.7, 270.3] | 1.334 | n/a |
| redis-sessions | nomesh | 13.289 [13.196, 13.294] | 1.006 | 0.512 [0.506, 0.515] | 1.410 | 270.3 [269.7, 270.9] | 1.340 | n/a |
