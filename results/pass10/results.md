# Pass 10 — answering review 2

The question is whether lifetime placement saves RSS under mimalloc defaults, whether live runtime rules help, and whether a model adds value beyond the supplied function names and TTL text.

Completed fragmentation blocks: 16/25. Each published group has five interleaved successful repetitions. **Defaults** means no MIMALLOC_* overrides on any variant; **immediate** means purge delay 0, arena purge multiplier 1 and decommit enabled. Earlier measurements remain separately labelled below.

With defaults on one-thread site-pure, static-model holds 216.81 MiB versus mimalloc 280.21 MiB: a 22.6% reduction. The names rule holds 216.81 MiB. The earlier roughly 84% model RSS reduction therefore does not carry over to defaults in this fixture. Capturing most of the default-options oracle saving is a smaller absolute benefit.

Plain upstream mimalloc holds the following at final idle under defaults: site-mixed-1 146.21 MiB; site-mixed-16 170.53 MiB; site-pure-1 280.21 MiB; site-pure-16 296.55 MiB. The ordinary and 10-second observations, both cycles and ranges are reported in [phase measurements](phases.md).

| Options / naming / workload | mi MiB | Oracle MiB | Static MiB / capture | Hybrid MiB / capture | Live heuristic MiB | Neutral rules MiB | Names rule MiB | TTL rule MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| defaults/named/site-mixed-1 | 146.21 | 112.18 | 115.02 / 91.7% | 115.02 / 91.7% | 147.14 | 158.96 | 147.14 | 115.02 |
| defaults/named/site-mixed-16 | 170.53 | 138.91 | 140.07 / 96.3% | 140.12 / 96.2% | 171.24 | 180.02 | 172.07 | 140.07 |
| defaults/named/site-pure-1 | 280.21 | 214.00 | 216.81 / 95.8% | 216.81 / 95.8% | 286.83 | 304.81 | 216.81 | — |
| defaults/named/site-pure-16 | 296.55 | 234.80 | 239.98 / 91.6% | 241.92 / 88.5% | 305.36 | 331.91 | 239.74 | — |
| defaults/opaque/site-mixed-1 | 146.21 | 112.19 | 147.13 / -2.7% | 158.95 / -37.4% | 147.13 | 158.95 | 147.13 | 147.13 |
| defaults/opaque/site-mixed-16 | 170.53 | 138.92 | 172.12 / -5.0% | 178.06 / -23.8% | 171.13 | 178.00 | 172.07 | 172.00 |
| defaults/opaque/site-pure-1 | 280.22 | 214.00 | 283.12 / -4.4% | 304.81 / -37.1% | 286.88 | 304.80 | 283.12 | — |
| defaults/opaque/site-pure-16 | 296.55 | 234.86 | 298.57 / -3.3% | 331.88 / -57.3% | 307.25 | 331.93 | 298.75 | — |
| defaults/plausible/site-mixed-1 | 146.21 | 112.19 | 147.13 / -2.7% | 120.95 / 74.3% | 147.14 | 158.95 | 147.14 | 147.13 |
| defaults/plausible/site-mixed-16 | 170.53 | 138.91 | 172.12 / -5.0% | 150.07 / 64.7% | 171.44 | 178.05 | 172.07 | 172.07 |
| defaults/plausible/site-pure-1 | 280.22 | 214.00 | 283.12 / -4.4% | 228.75 / 77.7% | 286.89 | 304.81 | 283.12 | — |
| defaults/plausible/site-pure-16 | 296.55 | 234.86 | 298.77 / -3.6% | 267.99 / 46.3% | 305.12 | 332.00 | 298.46 | — |
| immediate/named/site-mixed-1 | 144.70 | 26.06 | 28.12 / 98.3% | 28.10 / 98.3% | 146.87 | 75.73 | 146.52 | 28.09 |
| immediate/named/site-mixed-16 | 146.43 | 33.54 | 46.38 / 88.6% | 46.67 / 88.4% | 166.64 | 89.64 | 154.94 | 46.29 |
| immediate/named/site-pure-1 | 280.21 | 41.34 | 43.67 / 99.0% | 43.66 / 99.0% | 228.61 | 139.38 | 43.64 | — |
| immediate/named/site-pure-16 | 296.55 | 51.88 | 62.67 / 95.6% | 65.20 / 94.6% | 259.87 | 156.20 | 61.96 | — |

The heuristic now evaluates its sparse formula on current warm observations. Rules-neutral uses P(transient)=0.5 and the same continuous C runtime checks as hybrid. Rule-names uses the fixed cache/index/table/global/config/intern/registry keyword list; rule-ttl returns permanent iff context contains ttl=day. Both semantic controls use one-hot priors and the same admission, placement and continuous runtime rules. None uses a model.

site-pure-1, opaque: static-model retains -4.6% of the named saving; hybrid retains -38.8% of the named saving.
site-pure-1, plausible: static-model retains -4.6% of the named saving; hybrid retains 81.2% of the named saving.
site-pure-16, opaque: static-model retains -3.6% of the named saving; hybrid retains -64.7% of the named saving.
site-pure-16, plausible: static-model retains -3.9% of the named saving; hybrid retains 52.3% of the named saving.
site-mixed-1, opaque: static-model retains -2.9% of the named saving; hybrid retains -40.8% of the named saving.
site-mixed-1, plausible: static-model retains -2.9% of the named saving; hybrid retains 81.0% of the named saving.
site-mixed-16, opaque: static-model retains -5.2% of the named saving; hybrid retains -24.8% of the named saving.
site-mixed-16, plausible: static-model retains -5.2% of the named saving; hybrid retains 67.3% of the named saving.

static-model has a lower measured median than the matching semantic rule in defaults/opaque/site-pure-16 (0.17 MiB lower).

hybrid has a lower measured median than the matching semantic rule in defaults/plausible/site-mixed-1 (26.19 MiB lower); defaults/plausible/site-mixed-16 (22.00 MiB lower); defaults/plausible/site-pure-1 (54.37 MiB lower); defaults/plausible/site-pure-16 (30.47 MiB lower).
These five-run median differences are descriptive; consult ranges before interpreting small gaps. Renaming also changes the supplied context vocabulary. The ablation tests dependence on these hints; it is not a held-out real application.

Per-site and per-(site, context) model answers and probabilities are in the [readable site table](model-sites.md); exact prompt states are in [model-decisions.jsonl.gz](model-decisions.jsonl.gz). Unasked sites and trace truth are retained in each synthetic block’s sites.json. [Full phases and costs](phases.md) include all controls, both original cycles where present, the 10-second sample, peak RSS and target-process CPU. [Cold and fill costs](costs.json) are separate from warm replay. Wall time includes all prescribed idle waits; default-series wall ratios can therefore obscure allocation-path overhead. Target CPU and the regression scores provide complementary measurements.


The combined object-logging free path now updates trace and sampled-live state exactly once before releasing storage. The dedicated test covers retired allocating threads, cross-thread frees, actual address reuse, sample counts, survivors and hybrid demotions at sample rates 1 and 64.

Warm model runs replay first-sight answers; hybrid’s rules and all no-model controls execute live. Warm replay retains IPC/service costs and excludes sidecar CPU. It is not end-to-end deployment or hypothetical on-chip inference. Server-sim live bytes exclude metadata, bookkeeping mappings and thread resources, so RSS/live is process-memory amplification. In-place realloc can log a new policy class while retaining its physical heap. Compact aggregates support the published medians; complete trace/cache/decision reconstruction still needs remote artifacts.

