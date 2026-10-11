# Fragmentation results

Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.

| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 214.81 [214.80, 214.81] | 29.30 | 7.331 | 214.38 | 1.284 [1.281, 1.286] | 0.283 | 0.767 | 1.180 |
| site-pure-1 | mi | 280.22 [280.16, 280.22] | 29.30 | 9.563 | 280.05 | 1.087 [1.086, 1.113] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-none | 280.27 [280.21, 280.27] | 29.30 | 9.565 | 280.10 | 1.088 [1.086, 1.091] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-keyonly | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.09 | 1.128 [1.123, 1.141] | 0.124 | 1.000 | 1.037 |
| site-pure-1 | jev-table:oracle | 280.07 [280.02, 280.07] | 29.30 | 9.558 | 279.86 | 1.114 [1.112, 1.115] | 0.113 | 0.999 | 1.024 |
| site-pure-1 | jev-table:random | 42.55 [42.49, 42.55] | 29.30 | 1.452 | 214.08 | 1.161 [1.160, 1.163] | 0.160 | 0.152 | 1.067 |
| site-pure-1 | jev-table:size | 280.29 [280.24, 280.30] | 29.30 | 9.566 | 280.06 | 1.119 [1.116, 1.148] | 0.119 | 1.000 | 1.029 |
| site-pure-1 | jev-table:all-short | 280.29 [280.29, 280.29] | 29.30 | 9.566 | 280.10 | 1.118 [1.117, 1.120] | 0.117 | 1.000 | 1.028 |
| site-pure-1 | jev-table:all-long | 280.29 [280.29, 280.30] | 29.30 | 9.566 | 280.02 | 1.119 [1.119, 1.142] | 0.118 | 1.000 | 1.029 |
| site-pure-1 | jev-live:heuristic | 282.87 [282.82, 282.87] | 29.30 | 9.653 | 282.63 | 1.140 [1.138, 1.143] | 0.127 | 1.009 | 1.049 |
| site-pure-1 | jev-live:static-model | 282.87 [282.87, 282.88] | 29.30 | 9.654 | 282.61 | 1.133 [1.129, 1.138] | 0.127 | 1.009 | 1.042 |
| site-pure-1 | jev-live:model | 282.87 [282.82, 282.87] | 29.30 | 9.654 | 282.68 | 1.141 [1.138, 1.146] | 0.128 | 1.009 | 1.049 |

site-pure-1, observed medians: oracle beats mimalloc on idle RSS (0.999×). Live Clef does not beat the heuristic (1.000× RSS, 1.000× wall time, 1.005× target CPU time). Clef/oracle: 1.010× RSS, 1.024× wall, 1.136× CPU; heuristic/oracle: 1.010× RSS, 1.024× wall, 1.131× CPU. Clef/mi target CPU: 1.482×.

| site-pure-16 | sys | 215.46 [215.46, 215.46] | 29.33 | 7.347 | 214.25 | 1.106 [1.105, 1.131] | 0.989 | 0.729 | 1.062 |
| site-pure-16 | mi | 295.50 [294.50, 296.48] | 29.33 | 10.077 | 298.32 | 1.042 [1.038, 1.067] | 0.450 | 1.000 | 1.000 |
| site-pure-16 | jev-none | 296.53 [294.67, 297.59] | 29.33 | 10.112 | 298.34 | 1.041 [1.036, 1.064] | 0.434 | 1.003 | 0.999 |
| site-pure-16 | jev-keyonly | 295.81 [294.70, 296.80] | 29.33 | 10.087 | 298.60 | 1.048 [1.044, 1.048] | 0.516 | 1.001 | 1.006 |
| site-pure-16 | jev-table:oracle | 293.45 [293.34, 293.99] | 29.33 | 10.007 | 295.51 | 1.046 [1.044, 1.072] | 0.495 | 0.993 | 1.004 |
| site-pure-16 | jev-table:random | 64.72 [64.72, 64.85] | 29.33 | 2.207 | 234.61 | 1.048 [1.046, 1.071] | 0.537 | 0.219 | 1.006 |
| site-pure-16 | jev-table:size | 297.00 [295.69, 297.25] | 29.33 | 10.128 | 298.38 | 1.047 [1.044, 1.048] | 0.504 | 1.005 | 1.005 |
| site-pure-16 | jev-table:all-short | 297.18 [296.55, 297.98] | 29.33 | 10.134 | 298.60 | 1.047 [1.045, 1.067] | 0.498 | 1.006 | 1.005 |
| site-pure-16 | jev-table:all-long | 297.13 [297.00, 297.19] | 29.33 | 10.132 | 298.55 | 1.045 [1.044, 1.068] | 0.499 | 1.006 | 1.003 |
| site-pure-16 | jev-live:heuristic | 301.94 [299.94, 308.10] | 29.33 | 10.296 | 304.01 | 1.060 [1.060, 1.062] | 0.479 | 1.022 | 1.018 |
| site-pure-16 | jev-live:static-model | 297.84 [296.25, 300.43] | 29.33 | 10.156 | 297.21 | 1.059 [1.056, 1.079] | 0.482 | 1.008 | 1.016 |
| site-pure-16 | jev-live:model | 301.10 [298.61, 304.59] | 29.33 | 10.267 | 300.21 | 1.062 [1.059, 1.067] | 0.493 | 1.019 | 1.020 |

site-pure-16, observed medians: oracle beats mimalloc on idle RSS (0.993×). Live Clef beats the heuristic (0.997× RSS, 1.002× wall time, 1.028× target CPU time). Clef/oracle: 1.026× RSS, 1.016× wall, 0.995× CPU; heuristic/oracle: 1.029× RSS, 1.014× wall, 0.968× CPU. Clef/mi target CPU: 1.096×.

| site-mixed-1 | sys | 111.15 [111.15, 111.15] | 14.66 | 7.581 | 110.75 | 1.172 [1.171, 1.176] | 0.171 | 0.768 | 1.026 |
| site-mixed-1 | mi | 144.71 [144.69, 144.72] | 14.66 | 9.870 | 145.81 | 1.143 [1.142, 1.155] | 0.141 | 1.000 | 1.000 |
| site-mixed-1 | jev-none | 144.75 [144.73, 144.76] | 14.66 | 9.872 | 145.87 | 1.145 [1.142, 1.147] | 0.143 | 1.000 | 1.002 |
| site-mixed-1 | jev-keyonly | 144.79 [144.79, 144.79] | 14.66 | 9.875 | 145.88 | 1.181 [1.179, 1.204] | 0.180 | 1.001 | 1.033 |
| site-mixed-1 | jev-table:oracle | 144.97 [144.96, 145.01] | 14.66 | 9.888 | 145.89 | 1.175 [1.173, 1.184] | 0.174 | 1.002 | 1.029 |
| site-mixed-1 | jev-table:random | 145.06 [145.06, 145.07] | 14.66 | 9.894 | 145.66 | 1.168 [1.168, 1.169] | 0.167 | 1.002 | 1.022 |
| site-mixed-1 | jev-table:size | 144.98 [144.97, 144.99] | 14.66 | 9.889 | 145.78 | 1.174 [1.172, 1.176] | 0.173 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:all-short | 144.98 [144.96, 144.99] | 14.66 | 9.888 | 145.83 | 1.176 [1.173, 1.177] | 0.175 | 1.002 | 1.029 |
| site-mixed-1 | jev-table:all-long | 144.98 [144.96, 144.99] | 14.66 | 9.888 | 145.80 | 1.175 [1.174, 1.178] | 0.174 | 1.002 | 1.029 |
| site-mixed-1 | jev-live:heuristic | 146.50 [146.48, 146.52] | 14.66 | 9.992 | 146.32 | 1.207 [1.203, 1.218] | 0.194 | 1.012 | 1.056 |
| site-mixed-1 | jev-live:static-model | 146.88 [146.86, 146.88] | 14.66 | 10.017 | 146.70 | 1.127 [1.126, 1.159] | 0.121 | 1.015 | 0.986 |
| site-mixed-1 | jev-live:model | 146.87 [146.86, 146.88] | 14.66 | 10.017 | 146.68 | 1.134 [1.130, 1.198] | 0.123 | 1.015 | 0.993 |

site-mixed-1: a fixed per-site majority label classifies 83.37% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


site-mixed-1, observed medians: oracle does not beat mimalloc on idle RSS (1.002×). Live Clef does not beat the heuristic (1.003× RSS, 0.940× wall time, 0.637× target CPU time). Clef/oracle: 1.013× RSS, 0.965× wall, 0.709× CPU; heuristic/oracle: 1.011× RSS, 1.027× wall, 1.113× CPU. Clef/mi target CPU: 0.873×.

| site-mixed-16 | sys | 111.79 [111.79, 111.80] | 14.73 | 7.588 | 110.62 | 1.064 [1.064, 1.087] | 0.549 | 0.763 | 1.013 |
| site-mixed-16 | mi | 146.43 [146.43, 146.45] | 14.73 | 9.939 | 148.54 | 1.050 [1.045, 1.051] | 0.412 | 1.000 | 1.000 |
| site-mixed-16 | jev-none | 146.46 [146.46, 146.48] | 14.73 | 9.941 | 149.32 | 1.047 [1.043, 1.050] | 0.428 | 1.000 | 0.998 |
| site-mixed-16 | jev-keyonly | 146.69 [146.68, 146.77] | 14.73 | 9.956 | 151.38 | 1.053 [1.048, 1.077] | 0.508 | 1.002 | 1.003 |
| site-mixed-16 | jev-table:oracle | 149.65 [149.60, 149.69] | 14.73 | 10.158 | 155.02 | 1.051 [1.048, 1.078] | 0.472 | 1.022 | 1.001 |
| site-mixed-16 | jev-table:random | 156.44 [156.37, 156.52] | 14.73 | 10.618 | 155.42 | 1.050 [1.046, 1.072] | 0.445 | 1.068 | 1.000 |
| site-mixed-16 | jev-table:size | 149.65 [149.64, 149.73] | 14.73 | 10.157 | 150.36 | 1.052 [1.048, 1.052] | 0.479 | 1.022 | 1.002 |
| site-mixed-16 | jev-table:all-short | 149.62 [149.61, 149.71] | 14.73 | 10.156 | 154.38 | 1.050 [1.048, 1.052] | 0.485 | 1.022 | 1.001 |
| site-mixed-16 | jev-table:all-long | 149.70 [149.64, 149.75] | 14.73 | 10.161 | 153.61 | 1.051 [1.049, 1.075] | 0.471 | 1.022 | 1.001 |
| site-mixed-16 | jev-live:heuristic | 163.84 [163.28, 164.82] | 14.73 | 11.121 | 164.57 | 1.056 [1.055, 1.057] | 0.396 | 1.119 | 1.006 |
| site-mixed-16 | jev-live:static-model | 165.47 [165.41, 165.57] | 14.73 | 11.231 | 166.65 | 1.046 [1.041, 1.074] | 0.373 | 1.130 | 0.997 |
| site-mixed-16 | jev-live:model | 165.22 [164.72, 165.27] | 14.73 | 11.214 | 166.63 | 1.051 [1.050, 1.052] | 0.365 | 1.128 | 1.002 |

site-mixed-16: a fixed per-site majority label classifies 83.39% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


site-mixed-16, observed medians: oracle does not beat mimalloc on idle RSS (1.022×). Live Clef does not beat the heuristic (1.008× RSS, 0.996× wall time, 0.923× target CPU time). Clef/oracle: 1.104× RSS, 1.001× wall, 0.774× CPU; heuristic/oracle: 1.095× RSS, 1.005× wall, 0.839× CPU. Clef/mi target CPU: 0.886×.

Complete workloads: 4/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.
