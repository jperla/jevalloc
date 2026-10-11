
## Pass 6 sensitivity — stable across permanent thresholds

All 80 warm intervals pass the independent inference audit (zero overlaps). Five-repetition median final-idle MiB:

| Workload | mi | >25% | >50% | >90% | Never freed | S=64 KiB | S=1 MiB | S=16 MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.22 | 41.32 | 41.37 | 41.37 | 41.35 | 280.07 | 280.07 | 280.07 |
| site-pure-16 | 297.54 | 50.91 | 51.50 | 51.65 | 51.68 | 292.85 | 292.99 | 293.33 |

The four dominant sites keep the same majority labels under all permanent thresholds. Fixed-S merges sessions and cache entries and recreates the wrong-boundary negative. Full fragbench is collecting fresh permanent-prompt decisions; no regression has started.
