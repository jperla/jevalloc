# Fragmentation results

Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.

| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | mi | 280.22 [280.21, 280.22] | 29.30 | 9.563 | 280.10 | 1.088 [1.087, 1.089] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-table:oracle | 41.32 [41.29, 41.38] | 29.30 | 1.410 | 213.82 | 1.221 [1.215, 1.225] | 0.220 | 0.147 | 1.123 |
| site-pure-1 | jev-live:static-model | 43.56 [43.55, 43.64] | 29.30 | 1.487 | 216.53 | 1.245 [1.242, 1.267] | 0.240 | 0.155 | 1.145 |
| site-pure-1 | jev-live:hybrid | 43.57 [43.57, 43.62] | 29.30 | 1.487 | 216.50 | 1.256 [1.254, 1.289] | 0.251 | 0.156 | 1.155 |
| site-pure-1 | jev-live:heuristic | 228.55 [228.51, 228.59] | 29.30 | 7.800 | 286.55 | 1.167 [1.167, 1.171] | 0.157 | 0.816 | 1.073 |

Oracle saves 238.89 MiB (85.3%) against plain mimalloc.
Code-only Clef: 99.1% of the oracle saving; idle RSS/oracle 1.054, wall/mi 1.145, CPU/mi 2.776.
hybrid: 99.1% of the oracle saving; idle RSS/oracle 1.054, wall/mi 1.155, CPU/mi 2.907.
No-model heuristic: 21.6% of the oracle saving; idle RSS/oracle 5.531, wall/mi 1.073, CPU/mi 1.817.

site-pure-1, observed medians: oracle beats mimalloc on idle RSS (0.147×). Live Clef beats the heuristic (0.191× RSS, 1.076× wall time, 1.600× target CPU time). Clef/oracle: 1.054× RSS, 1.029× wall, 1.142× CPU; heuristic/oracle: 5.531× RSS, 0.956× wall, 0.714× CPU. Clef/mi target CPU: 2.907×.

| site-pure-16 | mi | 296.55 [294.50, 296.55] | 29.33 | 10.112 | 298.33 | 1.043 [1.041, 1.045] | 0.472 | 1.000 | 1.000 |
| site-pure-16 | jev-table:oracle | 51.45 [51.15, 53.38] | 29.33 | 1.755 | 221.54 | 1.057 [1.052, 1.079] | 0.656 | 0.174 | 1.013 |
| site-pure-16 | jev-live:static-model | 63.55 [60.32, 67.88] | 29.33 | 2.167 | 232.15 | 1.065 [1.059, 1.068] | 0.693 | 0.214 | 1.021 |
| site-pure-16 | jev-live:hybrid | 63.27 [61.16, 66.50] | 29.33 | 2.158 | 232.33 | 1.066 [1.059, 1.066] | 0.703 | 0.213 | 1.022 |
| site-pure-16 | jev-live:heuristic | 260.22 [254.57, 266.33] | 29.33 | 8.873 | 296.19 | 1.063 [1.059, 1.076] | 0.565 | 0.877 | 1.019 |

Oracle saves 245.09 MiB (82.6%) against plain mimalloc.
Code-only Clef: 95.1% of the oracle saving; idle RSS/oracle 1.235, wall/mi 1.021, CPU/mi 1.468.
hybrid: 95.2% of the oracle saving; idle RSS/oracle 1.230, wall/mi 1.022, CPU/mi 1.488.
No-model heuristic: 14.8% of the oracle saving; idle RSS/oracle 5.057, wall/mi 1.019, CPU/mi 1.197.

site-pure-16, observed medians: oracle beats mimalloc on idle RSS (0.174×). Live Clef beats the heuristic (0.243× RSS, 1.003× wall time, 1.243× target CPU time). Clef/oracle: 1.230× RSS, 1.009× wall, 1.071× CPU; heuristic/oracle: 5.057× RSS, 1.006× wall, 0.861× CPU. Clef/mi target CPU: 1.488×.

Complete workloads: 2/2. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.
