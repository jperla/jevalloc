# diagnostic-rare-larson

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| larson | jev-table:oracle | 7.052 [7.052, 7.052] | nan | 79.709 [79.709, 79.709] | nan | 182.0 [182.0, 182.0] | nan | n/a |
| larson | jev-live:heuristic | 7.058 [7.058, 7.058] | nan | 79.758 [79.758, 79.758] | nan | 181.9 [181.9, 181.9] | nan | n/a |
