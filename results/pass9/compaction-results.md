## Mesh compaction comparison

After 10 seconds, Mesh saves more than 5% RSS against nomesh on 10/11 comparable workloads: leveldb, redis-drop, redis-mesh, redis-sessions, rocksdb-cache, rocksdb-churn, site-mixed-1, site-mixed-16, site-pure-1, site-pure-16. Against plain mimalloc, Mesh clears 5% on these real-program workloads: leveldb, redis-drop, redis-mesh, rocksdb-cache. These are descriptive five-run comparisons, not new model-admission gates. Normal and 10-second idle RSS medians are identical in all 77 allocator/workload comparisons.

![Idle RSS and ratios against each allocator's own baseline](results/pass9/compaction-comparison.png)
[Vector figure](results/pass9/compaction-comparison.svg)

11/11 workload blocks processed, with 0 allocator/workload failures. Five interleaved repetitions per reported successful variant. Normal idle and 10-second idle are sampled in the same process; longer idle in the first cycle can affect the next cycle. Wall time includes all common settle periods.

| Workload | Variant | Idle MiB | 10 s idle MiB | Peak MiB | Wall s | CPU s | Idle / mi | Idle / twin | 10 s / twin |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| leveldb | mi | 87.59 | 87.59 | 198.84 | 11.373 | 1.464 | 1.000 | — | — |
| leveldb | jev-keyonly | 87.72 | 87.72 | 199.15 | 11.375 | 1.510 | 1.001 | 1.000 | 1.000 |
| leveldb | jev-table:oracle-site | 87.92 | 87.92 | 199.45 | 11.369 | 1.483 | 1.004 | 1.002 | 1.002 |
| leveldb | mesh | 78.43 | 78.43 | 236.90 | 11.444 | 1.454 | 0.895 | 0.442 | 0.442 |
| leveldb | nomesh | 177.30 | 177.30 | 237.11 | 11.431 | 1.401 | 2.024 | 1.000 | 1.000 |
| redis-drop | mi | 269.41 | 269.41 | 275.82 | 11.916 | 0.336 | 1.000 | — | — |
| redis-drop | jev-keyonly | 285.60 | 285.60 | 291.98 | 12.006 | 0.536 | 1.060 | 1.000 | 1.000 |
| redis-drop | jev-table:oracle-site | 270.20 | 270.20 | 278.00 | 11.947 | 0.408 | 1.003 | 0.946 | 0.946 |
| redis-drop | jev-table:oracle-context | 284.31 | 284.31 | 293.91 | 12.012 | 0.528 | 1.055 | 0.995 | 0.995 |
| redis-drop | jev-table:search | 286.48 | 286.48 | 293.91 | 12.007 | 0.532 | 1.063 | 1.003 | 1.003 |
| redis-drop | mesh | 92.40 | 92.40 | 330.32 | 12.069 | 0.886 | 0.343 | 0.279 | 0.279 |
| redis-drop | nomesh | 331.20 | 331.20 | 330.50 | 11.972 | 0.530 | 1.229 | 1.000 | 1.000 |
| redis-mesh | mi | 185.98 | 185.98 | 185.92 | 22.825 | 1.354 | 1.000 | — | — |
| redis-mesh | jev-keyonly | 186.05 | 186.05 | 185.82 | 23.279 | 1.779 | 1.000 | 1.000 | 1.000 |
| redis-mesh | jev-table:oracle-site | 188.01 | 188.01 | 187.95 | 23.134 | 1.660 | 1.011 | 1.010 | 1.010 |
| redis-mesh | jev-table:oracle-context | 196.07 | 196.07 | 196.00 | 23.129 | 1.655 | 1.054 | 1.054 | 1.054 |
| redis-mesh | jev-table:search | 186.09 | 186.09 | 185.98 | 23.160 | 1.702 | 1.001 | 1.000 | 1.000 |
| redis-mesh | mesh | 144.56 | 144.56 | 188.70 | 23.485 | 2.134 | 0.777 | 0.729 | 0.729 |
| redis-mesh | nomesh | 198.40 | 198.40 | 198.00 | 23.237 | 1.803 | 1.067 | 1.000 | 1.000 |
| redis-sessions | mi | 48.03 | 48.03 | 201.72 | 13.211 | 0.363 | 1.000 | — | — |
| redis-sessions | jev-keyonly | 48.21 | 48.21 | 201.96 | 13.198 | 0.425 | 1.004 | 1.000 | 1.000 |
| redis-sessions | jev-table:oracle-site | 50.02 | 50.02 | 203.75 | 13.266 | 0.420 | 1.041 | 1.038 | 1.038 |
| redis-sessions | jev-table:oracle-context | 50.02 | 50.02 | 203.99 | 13.266 | 0.422 | 1.041 | 1.037 | 1.037 |
| redis-sessions | jev-table:search | 48.20 | 48.20 | 201.95 | 13.264 | 0.421 | 1.004 | 1.000 | 1.000 |
| redis-sessions | mesh | 68.25 | 68.25 | 269.11 | 13.480 | 0.754 | 1.421 | 0.259 | 0.259 |
| redis-sessions | nomesh | 264.00 | 264.00 | 270.29 | 13.289 | 0.512 | 5.496 | 1.000 | 1.000 |
| rocksdb-cache | mi | 125.15 | 125.15 | 140.79 | 15.244 | 63.573 | 1.000 | — | — |
| rocksdb-cache | jev-keyonly | 128.47 | 128.47 | 132.09 | 15.052 | 63.450 | 1.027 | 1.000 | 1.000 |
| rocksdb-cache | jev-table:oracle-site | 114.58 | 114.58 | 129.35 | 15.209 | 63.482 | 0.916 | 0.892 | 0.892 |
| rocksdb-cache | mesh | 106.54 | 106.54 | 119.70 | 15.127 | 62.509 | 0.851 | 0.826 | 0.826 |
| rocksdb-cache | nomesh | 129.02 | 129.02 | 128.00 | 14.914 | 61.904 | 1.031 | 1.000 | 1.000 |
| rocksdb-churn | mi | 24.96 | 24.96 | 102.75 | 95.308 | 271.123 | 1.000 | — | — |
| rocksdb-churn | jev-keyonly | 25.22 | 25.22 | 100.05 | 92.909 | 259.962 | 1.010 | 1.000 | 1.000 |
| rocksdb-churn | jev-table:oracle-site | 26.25 | 26.25 | 105.30 | 93.031 | 271.983 | 1.052 | 1.041 | 1.041 |
| rocksdb-churn | mesh | 37.67 | 37.67 | 71.21 | 92.487 | 249.609 | 1.509 | 0.550 | 0.550 |
| rocksdb-churn | nomesh | 68.52 | 68.52 | 84.49 | 91.235 | 245.783 | 2.745 | 1.000 | 1.000 |
| site-mixed-1 | mi | 144.70 | 144.70 | 145.81 | 20.651 | 0.150 | 1.000 | — | — |
| site-mixed-1 | jev-keyonly | 144.80 | 144.80 | 145.90 | 20.725 | 0.224 | 1.001 | 1.000 | 1.000 |
| site-mixed-1 | jev-table:oracle-site | 145.00 | 145.00 | 145.95 | 20.715 | 0.213 | 1.002 | 1.001 | 1.001 |
| site-mixed-1 | jev-table:oracle-context | 26.05 | 26.05 | 111.95 | 20.728 | 0.225 | 0.180 | 0.180 | 0.180 |
| site-mixed-1 | jev-live:static-site | 146.46 | 146.46 | 146.61 | 20.743 | 0.234 | 1.012 | 1.011 | 1.011 |
| site-mixed-1 | jev-live:static-model | 28.12 | 28.12 | 114.63 | 20.768 | 0.261 | 0.194 | 0.194 | 0.194 |
| site-mixed-1 | jev-live:hybrid | 28.12 | 28.12 | 114.61 | 20.760 | 0.253 | 0.194 | 0.194 | 0.194 |
| site-mixed-1 | jev-live:heuristic | 146.87 | 146.87 | 146.61 | 20.683 | 0.168 | 1.015 | 1.014 | 1.014 |
| site-mixed-1 | mesh | 139.98 | 139.98 | 142.00 | 20.836 | 0.330 | 0.967 | 0.822 | 0.822 |
| site-mixed-1 | nomesh | 170.27 | 170.27 | 170.00 | 20.687 | 0.185 | 1.177 | 1.000 | 1.000 |
| site-mixed-16 | mi | 146.42 | 146.42 | 148.95 | 20.550 | 0.446 | 1.000 | — | — |
| site-mixed-16 | jev-keyonly | 146.82 | 146.82 | 151.41 | 20.559 | 0.580 | 1.003 | 1.000 | 1.000 |
| site-mixed-16 | jev-table:oracle-site | 149.71 | 149.71 | 152.07 | 20.558 | 0.538 | 1.022 | 1.020 | 1.020 |
| site-mixed-16 | jev-table:oracle-context | 33.52 | 33.52 | 117.38 | 20.550 | 0.565 | 0.229 | 0.228 | 0.228 |
| site-mixed-16 | jev-live:static-site | 154.62 | 154.62 | 153.83 | 20.565 | 0.571 | 1.056 | 1.053 | 1.053 |
| site-mixed-16 | jev-live:static-model | 46.73 | 46.73 | 127.14 | 20.559 | 0.591 | 0.319 | 0.318 | 0.318 |
| site-mixed-16 | jev-live:hybrid | 47.33 | 47.33 | 127.14 | 20.561 | 0.623 | 0.323 | 0.322 | 0.322 |
| site-mixed-16 | jev-live:heuristic | 165.64 | 165.64 | 169.20 | 20.555 | 0.446 | 1.131 | 1.128 | 1.128 |
| site-mixed-16 | mesh | 149.88 | 149.88 | 147.68 | 20.695 | 0.461 | 1.024 | 0.868 | 0.868 |
| site-mixed-16 | nomesh | 172.70 | 172.70 | 171.62 | 20.607 | 0.360 | 1.179 | 1.000 | 1.000 |
| site-pure-1 | mi | 280.22 | 280.22 | 280.02 | 20.589 | 0.087 | 1.000 | — | — |
| site-pure-1 | jev-keyonly | 280.31 | 280.31 | 280.25 | 20.629 | 0.128 | 1.000 | 1.000 | 1.000 |
| site-pure-1 | jev-table:oracle-site | 41.37 | 41.37 | 213.94 | 20.730 | 0.229 | 0.148 | 0.148 | 0.148 |
| site-pure-1 | jev-live:static-model | 43.56 | 43.56 | 216.59 | 20.759 | 0.252 | 0.155 | 0.155 | 0.155 |
| site-pure-1 | jev-live:hybrid | 43.57 | 43.57 | 216.67 | 20.765 | 0.261 | 0.155 | 0.155 | 0.155 |
| site-pure-1 | jev-live:heuristic | 228.50 | 228.50 | 286.65 | 20.674 | 0.164 | 0.815 | 0.815 | 0.815 |
| site-pure-1 | mesh | 270.62 | 270.62 | 270.14 | 21.036 | 0.530 | 0.966 | 0.823 | 0.823 |
| site-pure-1 | nomesh | 328.86 | 328.86 | 328.50 | 20.759 | 0.258 | 1.174 | 1.000 | 1.000 |
| site-pure-16 | mi | 296.55 | 296.55 | 298.33 | 20.543 | 0.462 | 1.000 | — | — |
| site-pure-16 | jev-keyonly | 295.95 | 295.95 | 298.73 | 20.548 | 0.517 | 0.998 | 1.000 | 1.000 |
| site-pure-16 | jev-table:oracle-site | 51.83 | 51.83 | 221.76 | 20.556 | 0.636 | 0.175 | 0.175 | 0.175 |
| site-pure-16 | jev-live:static-model | 64.86 | 64.86 | 232.77 | 20.562 | 0.671 | 0.219 | 0.219 | 0.219 |
| site-pure-16 | jev-live:hybrid | 63.38 | 63.38 | 232.03 | 20.567 | 0.693 | 0.214 | 0.214 | 0.214 |
| site-pure-16 | jev-live:heuristic | 255.43 | 255.43 | 298.70 | 20.562 | 0.530 | 0.861 | 0.863 | 0.863 |
| site-pure-16 | mesh | 290.95 | 290.95 | 288.62 | 20.837 | 0.710 | 0.981 | 0.878 | 0.878 |
| site-pure-16 | nomesh | 331.42 | 331.42 | 330.12 | 20.675 | 0.511 | 1.118 | 1.000 | 1.000 |
| sqlite | mi | 78.94 | 78.94 | 205.80 | 10.147 | 0.146 | 1.000 | — | — |
| sqlite | jev-keyonly | 79.01 | 79.01 | 205.79 | 10.154 | 0.154 | 1.001 | 1.000 | 1.000 |
| sqlite | jev-table:oracle-site | 82.10 | 82.10 | 209.01 | 10.134 | 0.133 | 1.040 | 1.039 | 1.039 |
| sqlite | mesh | 317.53 | 317.53 | 317.12 | 10.439 | 0.439 | 4.023 | 1.000 | 1.000 |
| sqlite | nomesh | 317.52 | 317.52 | 317.25 | 10.295 | 0.294 | 4.022 | 1.000 | 1.000 |

Twin is nomesh for both Mesh variants, jev-keyonly for placement policies. Each allocator has its own baseline; a Mesh/mi difference alone does not isolate compaction. CPU is workload-process user plus system time, excluding the sidecar. Full ranges and all costs are in [compaction-summary.json](results/pass9/compaction-summary.json).

The later RocksDB-cache per-site oracle median is 8.4% below mimalloc, with run ranges 111.11–128.12 MiB (oracle) and 123.33–137.04 MiB (mimalloc). The intervals overlap. This uses a new trace and the longer-settle workload; the earlier independent headroom gate is retained separately, and no additional database context/model experiment was added.

Mesh source revision: `2987f883b8695c07a80dc40da67c61f524460dfd` (the recipe follows master). Default randomization is unchanged; the twin differs by `DISABLE_MESHING=ON`. Dependency archives retain the exact pinned revisions. Build logs, hashes and the CMake dependency-fetch adaptation are in [builds](results/pass9/builds).
This revision checks a 100 ms meshing interval on eligible frees; it does not run a background compaction thread during a completely quiet idle. Waiting longer alone therefore need not trigger another mesh pass.
These are process RSS measurements, as requested. RSS counts resident mappings; PSS apportions shared pages across mappings ([Linux kernel documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html)). Because Mesh preserves virtual addresses by aliasing physical pages, RSS alone can understate its physical-memory benefit. This experiment does not measure PSS and does not equate unchanged RSS with zero physical compaction.

Upstream unit checks pass in both configurations (meshing-specific tests are skipped by nomesh). The measured library hashes were verified unchanged before and after the checks. Logs: [Mesh](results/pass9/builds/mesh-unit.log), [nomesh](results/pass9/builds/nomesh-unit.log).
