# pass9/compaction/site-pure-1

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 20.589 [20.588, 20.615] | 1.000 | 0.087 [0.087, 0.094] | 1.000 | 280.0 [279.9, 280.1] | 1.000 | n/a |
| site-pure-1 | jev-keyonly | 20.629 [20.628, 20.632] | 1.002 | 0.128 [0.127, 0.130] | 1.472 | 280.2 [280.1, 280.3] | 1.001 | n/a |
| site-pure-1 | jev-table:oracle-site | 20.730 [20.728, 20.737] | 1.007 | 0.229 [0.226, 0.236] | 2.631 | 213.9 [213.7, 214.0] | 0.764 | n/a |
| site-pure-1 | jev-live:static-model | 20.759 [20.757, 20.784] | 1.008 | 0.252 [0.247, 0.255] | 2.894 | 216.6 [216.6, 216.7] | 0.773 | n/a |
| site-pure-1 | jev-live:hybrid | 20.765 [20.765, 20.772] | 1.009 | 0.261 [0.260, 0.267] | 2.995 | 216.7 [216.5, 216.8] | 0.774 | n/a |
| site-pure-1 | jev-live:heuristic | 20.674 [20.673, 20.677] | 1.004 | 0.164 [0.163, 0.166] | 1.883 | 286.7 [286.6, 286.8] | 1.024 | n/a |
| site-pure-1 | mesh | 21.036 [21.033, 21.044] | 1.022 | 0.530 [0.525, 0.536] | 6.082 | 270.1 [269.7, 270.3] | 0.965 | n/a |
| site-pure-1 | nomesh | 20.759 [20.757, 20.770] | 1.008 | 0.258 [0.256, 0.270] | 2.962 | 328.5 [328.5, 328.6] | 1.173 | n/a |
