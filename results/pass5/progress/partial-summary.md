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

site-pure-1: oracle beats mimalloc on idle RSS (0.999×). Live Clef does not beat the heuristic (1.000× RSS, 1.000× wall time, 1.005× target CPU time). Clef/oracle: 1.010× RSS, 1.024× time; heuristic/oracle: 1.010× RSS, 1.024× time.

Complete workloads: 1/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.
