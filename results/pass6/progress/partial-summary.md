# Fragmentation results

Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.

| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 214.81 [214.81, 214.81] | 29.30 | 7.331 | 214.38 | 1.300 [1.296, 1.325] | 0.298 | 0.767 | 1.195 |
| site-pure-1 | mi | 280.22 [280.16, 280.22] | 29.30 | 9.563 | 279.99 | 1.088 [1.086, 1.090] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-none | 280.27 [280.21, 280.27] | 29.30 | 9.565 | 280.05 | 1.086 [1.083, 1.089] | 0.085 | 1.000 | 0.999 |
| site-pure-1 | jev-keyonly | 280.29 [280.29, 280.30] | 29.30 | 9.566 | 280.08 | 1.123 [1.121, 1.146] | 0.122 | 1.000 | 1.033 |
| site-pure-1 | jev-table:oracle | 41.36 [41.26, 41.38] | 29.30 | 1.411 | 213.81 | 1.226 [1.222, 1.227] | 0.225 | 0.148 | 1.128 |
| site-pure-1 | jev-table:random | 42.55 [42.49, 42.55] | 29.30 | 1.452 | 214.14 | 1.164 [1.162, 1.166] | 0.163 | 0.152 | 1.070 |
| site-pure-1 | jev-table:size | 280.30 [280.23, 280.30] | 29.30 | 9.566 | 280.07 | 1.120 [1.114, 1.126] | 0.119 | 1.000 | 1.030 |
| site-pure-1 | jev-table:all-transient | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.05 | 1.119 [1.118, 1.122] | 0.118 | 1.000 | 1.029 |
| site-pure-1 | jev-table:all-permanent | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.06 | 1.118 [1.116, 1.123] | 0.117 | 1.000 | 1.028 |
| site-pure-1 | jev-live:heuristic | 228.77 [228.76, 228.84] | 29.30 | 7.807 | 286.54 | 1.168 [1.166, 1.172] | 0.155 | 0.816 | 1.074 |
| site-pure-1 | jev-live:static-model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.55 | 1.136 [1.131, 1.137] | 0.128 | 1.009 | 1.045 |
| site-pure-1 | jev-live:model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.58 | 1.147 [1.140, 1.175] | 0.133 | 1.009 | 1.055 |

Oracle saves 238.86 MiB (85.2%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.045, CPU/mi 1.484.
Clef with runtime: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.055, CPU/mi 1.541.
No-model heuristic: 21.5% of the oracle saving; idle RSS/oracle 5.532, wall/mi 1.074, CPU/mi 1.795.

site-pure-1, observed medians: oracle beats mimalloc on idle RSS (0.148×). Live Clef does not beat the heuristic (1.236× RSS, 0.982× wall time, 0.858× target CPU time). Clef/oracle: 6.838× RSS, 0.935× wall, 0.591× CPU; heuristic/oracle: 5.532× RSS, 0.952× wall, 0.688× CPU. Clef/mi target CPU: 1.541×.

| site-pure-16 | sys | 215.46 [215.46, 215.46] | 29.33 | 7.347 | 214.12 | 1.111 [1.107, 1.116] | 1.086 | 0.729 | 1.067 |
| site-pure-16 | mi | 295.49 [294.45, 296.48] | 29.33 | 10.076 | 298.32 | 1.041 [1.040, 1.046] | 0.454 | 1.000 | 1.000 |
| site-pure-16 | jev-none | 295.61 [295.54, 296.72] | 29.33 | 10.080 | 298.34 | 1.042 [1.041, 1.066] | 0.467 | 1.000 | 1.001 |
| site-pure-16 | jev-keyonly | 295.82 [295.69, 297.80] | 29.33 | 10.087 | 298.54 | 1.047 [1.046, 1.048] | 0.519 | 1.001 | 1.006 |
| site-pure-16 | jev-table:oracle | 51.72 [51.54, 52.61] | 29.33 | 1.764 | 223.92 | 1.055 [1.052, 1.075] | 0.620 | 0.175 | 1.014 |
| site-pure-16 | jev-table:random | 64.73 [64.66, 64.79] | 29.33 | 2.207 | 234.49 | 1.050 [1.047, 1.053] | 0.561 | 0.219 | 1.009 |
| site-pure-16 | jev-table:size | 297.06 [294.93, 297.81] | 29.33 | 10.130 | 298.38 | 1.047 [1.045, 1.049] | 0.487 | 1.005 | 1.006 |
| site-pure-16 | jev-table:all-transient | 297.12 [295.63, 297.18] | 29.33 | 10.132 | 298.61 | 1.044 [1.042, 1.070] | 0.493 | 1.006 | 1.003 |
| site-pure-16 | jev-table:all-permanent | 296.44 [296.38, 297.18] | 29.33 | 10.109 | 298.54 | 1.047 [1.042, 1.072] | 0.518 | 1.003 | 1.005 |
| site-pure-16 | jev-live:heuristic | 251.57 [243.89, 253.02] | 29.33 | 8.579 | 286.67 | 1.069 [1.067, 1.080] | 0.538 | 0.851 | 1.027 |
| site-pure-16 | jev-live:static-model | 298.29 [296.67, 300.76] | 29.33 | 10.172 | 298.44 | 1.055 [1.055, 1.062] | 0.490 | 1.009 | 1.014 |
| site-pure-16 | jev-live:model | 313.49 [313.14, 316.99] | 29.33 | 10.690 | 316.89 | 1.063 [1.061, 1.066] | 0.505 | 1.061 | 1.021 |

Oracle saves 243.77 MiB (82.5%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 5.767, wall/mi 1.014, CPU/mi 1.079.
Clef with runtime: -7.4% of the oracle saving; idle RSS/oracle 6.061, wall/mi 1.021, CPU/mi 1.111.
No-model heuristic: 18.0% of the oracle saving; idle RSS/oracle 4.864, wall/mi 1.027, CPU/mi 1.184.

site-pure-16, observed medians: oracle beats mimalloc on idle RSS (0.175×). Live Clef does not beat the heuristic (1.246× RSS, 0.994× wall time, 0.939× target CPU time). Clef/oracle: 6.061× RSS, 1.007× wall, 0.814× CPU; heuristic/oracle: 4.864× RSS, 1.013× wall, 0.867× CPU. Clef/mi target CPU: 1.111×.

| site-mixed-1 | sys | 111.15 [111.14, 111.15] | 14.66 | 7.581 | 110.75 | 1.176 [1.176, 1.178] | 0.175 | 0.768 | 1.024 |
| site-mixed-1 | mi | 144.71 [144.70, 144.73] | 14.66 | 9.870 | 145.91 | 1.149 [1.147, 1.151] | 0.148 | 1.000 | 1.000 |
| site-mixed-1 | jev-none | 144.75 [144.74, 144.78] | 14.66 | 9.873 | 145.78 | 1.151 [1.149, 1.151] | 0.150 | 1.000 | 1.002 |
| site-mixed-1 | jev-keyonly | 144.79 [144.78, 144.80] | 14.66 | 9.875 | 145.77 | 1.187 [1.184, 1.188] | 0.186 | 1.001 | 1.033 |
| site-mixed-1 | jev-table:oracle | 144.97 [144.96, 144.97] | 14.66 | 9.887 | 145.86 | 1.181 [1.176, 1.209] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:random | 145.07 [145.05, 145.08] | 14.66 | 9.894 | 145.67 | 1.171 [1.166, 1.204] | 0.170 | 1.002 | 1.019 |
| site-mixed-1 | jev-table:size | 144.98 [144.96, 144.98] | 14.66 | 9.888 | 145.83 | 1.181 [1.178, 1.182] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:all-transient | 144.98 [144.97, 145.00] | 14.66 | 9.888 | 145.84 | 1.180 [1.179, 1.181] | 0.179 | 1.002 | 1.027 |
| site-mixed-1 | jev-table:all-permanent | 144.99 [144.98, 144.99] | 14.66 | 9.889 | 145.84 | 1.181 [1.176, 1.183] | 0.179 | 1.002 | 1.028 |
| site-mixed-1 | jev-live:heuristic | 146.37 [146.36, 146.39] | 14.66 | 9.983 | 146.39 | 1.212 [1.211, 1.213] | 0.200 | 1.011 | 1.055 |
| site-mixed-1 | jev-live:static-model | 148.88 [148.87, 148.88] | 14.66 | 10.154 | 148.71 | 1.131 [1.127, 1.133] | 0.125 | 1.029 | 0.984 |
| site-mixed-1 | jev-live:model | 148.88 [148.88, 148.89] | 14.66 | 10.154 | 148.68 | 1.138 [1.136, 1.162] | 0.126 | 1.029 | 0.991 |

site-mixed-1: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -0.26 MiB (-0.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.984, CPU/mi 0.839.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.991, CPU/mi 0.848.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.010, wall/mi 1.055, CPU/mi 1.348.

site-mixed-1, observed medians: oracle does not beat mimalloc on idle RSS (1.002×). Live Clef does not beat the heuristic (1.017× RSS, 0.939× wall time, 0.629× target CPU time). Clef/oracle: 1.027× RSS, 0.964× wall, 0.700× CPU; heuristic/oracle: 1.010× RSS, 1.026× wall, 1.113× CPU. Clef/mi target CPU: 0.848×.

| site-mixed-16 | sys | 111.79 [111.79, 111.80] | 14.73 | 7.588 | 110.62 | 1.067 [1.061, 1.091] | 0.555 | 0.763 | 1.019 |
| site-mixed-16 | mi | 146.43 [146.41, 146.44] | 14.73 | 9.939 | 148.45 | 1.047 [1.045, 1.050] | 0.441 | 1.000 | 1.000 |
| site-mixed-16 | jev-none | 146.49 [146.45, 146.51] | 14.73 | 9.943 | 149.29 | 1.051 [1.048, 1.075] | 0.441 | 1.000 | 1.003 |
| site-mixed-16 | jev-keyonly | 146.63 [146.56, 146.70] | 14.73 | 9.953 | 150.63 | 1.054 [1.052, 1.077] | 0.498 | 1.001 | 1.007 |
| site-mixed-16 | jev-table:oracle | 149.66 [149.66, 149.71] | 14.73 | 10.158 | 153.41 | 1.055 [1.051, 1.077] | 0.497 | 1.022 | 1.007 |
| site-mixed-16 | jev-table:random | 156.44 [156.20, 156.46] | 14.73 | 10.618 | 155.66 | 1.051 [1.046, 1.076] | 0.453 | 1.068 | 1.004 |
| site-mixed-16 | jev-table:size | 149.65 [149.64, 149.71] | 14.73 | 10.157 | 151.50 | 1.053 [1.052, 1.053] | 0.487 | 1.022 | 1.005 |
| site-mixed-16 | jev-table:all-transient | 149.68 [149.59, 149.76] | 14.73 | 10.160 | 152.38 | 1.053 [1.053, 1.055] | 0.494 | 1.022 | 1.006 |
| site-mixed-16 | jev-table:all-permanent | 149.67 [149.62, 149.69] | 14.73 | 10.159 | 153.47 | 1.052 [1.049, 1.078] | 0.483 | 1.022 | 1.005 |
| site-mixed-16 | jev-live:heuristic | 155.28 [154.82, 155.66] | 14.73 | 10.540 | 155.05 | 1.070 [1.069, 1.073] | 0.486 | 1.060 | 1.022 |
| site-mixed-16 | jev-live:static-model | 165.30 [164.73, 165.36] | 14.73 | 11.220 | 166.49 | 1.050 [1.048, 1.069] | 0.404 | 1.129 | 1.002 |
| site-mixed-16 | jev-live:model | 165.44 [165.22, 165.61] | 14.73 | 11.229 | 168.17 | 1.053 [1.051, 1.055] | 0.383 | 1.130 | 1.005 |

site-mixed-16: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -3.24 MiB (-2.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.104, wall/mi 1.002, CPU/mi 0.915.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.105, wall/mi 1.005, CPU/mi 0.869.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.038, wall/mi 1.022, CPU/mi 1.101.

site-mixed-16, observed medians: oracle does not beat mimalloc on idle RSS (1.022×). Live Clef does not beat the heuristic (1.065× RSS, 0.984× wall time, 0.790× target CPU time). Clef/oracle: 1.105× RSS, 0.998× wall, 0.771× CPU; heuristic/oracle: 1.038× RSS, 1.014× wall, 0.977× CPU. Clef/mi target CPU: 0.869×.

| redis-mesh | sys | 171.65 [170.02, 172.08] | 100.00 | 1.717 | 171.44 | 3.913 [3.897, 4.012] | 1.427 | 0.944 | 1.021 |
| redis-mesh | mi | 181.91 [178.00, 186.00] | 100.00 | 1.819 | 181.81 | 3.834 [3.816, 3.856] | 1.364 | 1.000 | 1.000 |
| redis-mesh | jev-none | 180.03 [177.95, 185.93] | 100.00 | 1.800 | 179.90 | 3.859 [3.847, 3.900] | 1.407 | 0.990 | 1.006 |
| redis-mesh | jev-keyonly | 185.99 [178.02, 186.07] | 100.00 | 1.860 | 185.83 | 3.983 [3.951, 4.025] | 1.581 | 1.022 | 1.039 |
| redis-mesh | jev-table:oracle | 187.99 [180.05, 188.06] | 100.00 | 1.880 | 187.87 | 3.942 [3.887, 3.947] | 1.483 | 1.033 | 1.028 |
| redis-mesh | jev-table:random | 185.95 [180.04, 186.08] | 100.00 | 1.860 | 185.82 | 3.931 [3.899, 3.946] | 1.487 | 1.022 | 1.025 |
| redis-mesh | jev-table:size | 186.00 [178.08, 186.11] | 100.00 | 1.860 | 185.76 | 3.904 [3.889, 3.938] | 1.482 | 1.022 | 1.018 |
| redis-mesh | jev-table:all-transient | 186.08 [178.00, 186.13] | 100.00 | 1.861 | 185.97 | 3.909 [3.894, 3.932] | 1.494 | 1.023 | 1.020 |
| redis-mesh | jev-table:all-permanent | 186.02 [177.64, 186.11] | 100.00 | 1.860 | 185.79 | 3.915 [3.899, 3.947] | 1.487 | 1.023 | 1.021 |
| redis-mesh | jev-live:heuristic | 230.92 [223.02, 230.96] | 100.00 | 2.309 | 230.42 | 4.157 [4.112, 4.292] | 1.593 | 1.269 | 1.084 |
| redis-mesh | jev-live:static-model | 194.83 [190.89, 194.88] | 100.00 | 1.948 | 194.54 | 4.276 [4.272, 4.387] | 1.677 | 1.071 | 1.115 |
| redis-mesh | jev-live:model | 192.85 [188.88, 194.88] | 100.00 | 1.929 | 194.55 | 4.294 [4.238, 4.452] | 1.671 | 1.060 | 1.120 |

Oracle saves -6.08 MiB (-3.3%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.036, wall/mi 1.115, CPU/mi 1.229.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.026, wall/mi 1.120, CPU/mi 1.225.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.228, wall/mi 1.084, CPU/mi 1.167.

redis-mesh, observed medians: oracle does not beat mimalloc on idle RSS (1.033×). Live Clef beats the heuristic (0.835× RSS, 1.033× wall time, 1.049× target CPU time). Clef/oracle: 1.026× RSS, 1.089× wall, 1.127× CPU; heuristic/oracle: 1.228× RSS, 1.055× wall, 1.074× CPU. Clef/mi target CPU: 1.225×.

Complete workloads: 5/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.
