# Fragmentation results

Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.

| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 214.81 [214.80, 214.81] | 29.30 | 7.331 | 214.50 | 1.282 [1.281, 1.285] | 0.282 | 0.767 | 1.180 |
| site-pure-1 | mi | 280.16 [280.16, 280.21] | 29.30 | 9.561 | 280.03 | 1.087 [1.085, 1.089] | 0.085 | 1.000 | 1.000 |
| site-pure-1 | jev-none | 280.27 [280.21, 280.27] | 29.30 | 9.565 | 279.96 | 1.088 [1.084, 1.092] | 0.087 | 1.000 | 1.001 |
| site-pure-1 | jev-keyonly | 280.29 [280.29, 280.29] | 29.30 | 9.566 | 280.08 | 1.122 [1.121, 1.123] | 0.121 | 1.000 | 1.033 |
| site-pure-1 | jev-table:oracle | 280.07 [280.02, 280.07] | 29.30 | 9.558 | 279.85 | 1.113 [1.111, 1.115] | 0.112 | 1.000 | 1.024 |
| site-pure-1 | jev-table:random | 42.55 [42.55, 42.55] | 29.30 | 1.452 | 214.09 | 1.161 [1.155, 1.185] | 0.160 | 0.152 | 1.068 |
| site-pure-1 | jev-table:size | 280.29 [280.18, 280.30] | 29.30 | 9.565 | 280.01 | 1.118 [1.116, 1.119] | 0.117 | 1.000 | 1.029 |
| site-pure-1 | jev-table:all-short | 280.29 [280.24, 280.30] | 29.30 | 9.565 | 280.09 | 1.120 [1.117, 1.147] | 0.119 | 1.000 | 1.031 |
| site-pure-1 | jev-table:all-long | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.12 | 1.117 [1.115, 1.120] | 0.116 | 1.000 | 1.028 |
| site-pure-1 | jev-live:heuristic | 282.88 [282.88, 282.89] | 29.30 | 9.654 | 282.71 | 1.139 [1.137, 1.142] | 0.127 | 1.010 | 1.049 |
| site-pure-1 | jev-live:static-model | 283.10 [283.10, 283.11] | 29.30 | 9.661 | 282.88 | 1.140 [1.139, 1.172] | 0.134 | 1.010 | 1.050 |
| site-pure-1 | jev-live:model | 280.84 [280.83, 280.84] | 29.30 | 9.584 | 280.66 | 1.141 [1.141, 1.179] | 0.129 | 1.002 | 1.050 |

site-pure-1: oracle beats mimalloc on idle RSS (1.000×). Live Clef beats the heuristic (0.993× RSS, 1.002× wall time, 1.019× target CPU time). Clef/oracle: 1.003× RSS, 1.026× time; heuristic/oracle: 1.010× RSS, 1.024× time.

| site-pure-16 | sys | 215.46 [215.46, 215.46] | 29.33 | 7.347 | 214.12 | 1.107 [1.105, 1.108] | 0.941 | 0.727 | 1.064 |
| site-pure-16 | mi | 296.48 [295.62, 296.55] | 29.33 | 10.110 | 298.33 | 1.041 [1.038, 1.044] | 0.427 | 1.000 | 1.000 |
| site-pure-16 | jev-none | 295.54 [295.48, 296.59] | 29.33 | 10.078 | 298.34 | 1.041 [1.040, 1.043] | 0.456 | 0.997 | 1.000 |
| site-pure-16 | jev-keyonly | 295.80 [295.69, 296.73] | 29.33 | 10.087 | 298.54 | 1.046 [1.041, 1.049] | 0.500 | 0.998 | 1.005 |
| site-pure-16 | jev-table:oracle | 292.95 [292.58, 293.47] | 29.33 | 9.990 | 295.31 | 1.046 [1.044, 1.069] | 0.493 | 0.988 | 1.005 |
| site-pure-16 | jev-table:random | 64.73 [64.67, 64.79] | 29.33 | 2.207 | 234.54 | 1.048 [1.046, 1.053] | 0.522 | 0.218 | 1.007 |
| site-pure-16 | jev-table:size | 296.30 [296.25, 297.87] | 29.33 | 10.104 | 298.45 | 1.048 [1.047, 1.066] | 0.490 | 0.999 | 1.006 |
| site-pure-16 | jev-table:all-short | 297.12 [296.32, 297.23] | 29.33 | 10.132 | 298.55 | 1.046 [1.041, 1.049] | 0.504 | 1.002 | 1.005 |
| site-pure-16 | jev-table:all-long | 296.49 [295.64, 297.98] | 29.33 | 10.110 | 298.55 | 1.047 [1.044, 1.048] | 0.508 | 1.000 | 1.005 |
| site-pure-16 | jev-live:heuristic | 305.80 [301.51, 306.14] | 29.33 | 10.428 | 306.21 | 1.060 [1.060, 1.062] | 0.471 | 1.031 | 1.019 |
| site-pure-16 | jev-live:static-model | 298.61 [298.00, 299.24] | 29.33 | 10.182 | 299.66 | 1.056 [1.052, 1.061] | 0.483 | 1.007 | 1.014 |
| site-pure-16 | jev-live:model | 289.73 [287.95, 291.95] | 29.33 | 9.880 | 294.55 | 1.073 [1.062, 1.079] | 0.487 | 0.977 | 1.031 |

site-pure-16: oracle beats mimalloc on idle RSS (0.988×). Live Clef beats the heuristic (0.947× RSS, 1.012× wall time, 1.032× target CPU time). Clef/oracle: 0.989× RSS, 1.025× time; heuristic/oracle: 1.044× RSS, 1.013× time.

Complete workloads: 2/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.
