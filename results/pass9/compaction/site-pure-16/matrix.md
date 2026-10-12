# pass9/compaction/site-pure-16

Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Live cold runs are reported separately; headline live timings replay their decision sequence without model inference.

Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.

| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-16 | mi | 20.543 [20.541, 20.544] | 1.000 | 0.462 [0.451, 0.492] | 1.000 | 298.3 [298.3, 298.3] | 1.000 | n/a |
| site-pure-16 | jev-keyonly | 20.548 [20.547, 20.557] | 1.000 | 0.517 [0.500, 0.535] | 1.120 | 298.7 [298.7, 298.7] | 1.001 | n/a |
| site-pure-16 | jev-table:oracle-site | 20.556 [20.555, 20.559] | 1.001 | 0.636 [0.616, 0.682] | 1.378 | 221.8 [219.5, 223.6] | 0.743 | n/a |
| site-pure-16 | jev-live:static-model | 20.562 [20.561, 20.567] | 1.001 | 0.671 [0.645, 0.692] | 1.453 | 232.8 [230.1, 235.2] | 0.780 | n/a |
| site-pure-16 | jev-live:hybrid | 20.567 [20.566, 20.568] | 1.001 | 0.693 [0.678, 0.720] | 1.500 | 232.0 [231.0, 237.1] | 0.778 | n/a |
| site-pure-16 | jev-live:heuristic | 20.562 [20.559, 20.563] | 1.001 | 0.530 [0.462, 0.603] | 1.149 | 298.7 [292.7, 305.4] | 1.001 | n/a |
| site-pure-16 | mesh | 20.837 [20.829, 20.863] | 1.014 | 0.710 [0.692, 0.716] | 1.538 | 288.6 [288.2, 289.0] | 0.967 | n/a |
| site-pure-16 | nomesh | 20.675 [20.671, 20.682] | 1.006 | 0.511 [0.492, 0.526] | 1.107 | 330.1 [330.1, 330.2] | 1.107 | n/a |
