# Pass 10 — answering review 2

The question is whether lifetime placement saves RSS under mimalloc defaults, whether live runtime rules help, and whether a model adds value beyond the supplied function names and TTL text.

Completed fragmentation blocks: 6/25. Each published group has five interleaved successful repetitions. **Defaults** means no MIMALLOC_* overrides on any variant; **immediate** means purge delay 0, arena purge multiplier 1 and decommit enabled. Earlier measurements remain separately labelled below.

With defaults on one-thread site-pure, static-model holds 216.81 MiB versus mimalloc 280.21 MiB: a 22.6% reduction. The names rule holds 216.81 MiB. The earlier roughly 84% model RSS reduction therefore does not carry over to defaults in this fixture. Capturing most of the default-options oracle saving is a smaller absolute benefit.

Plain upstream mimalloc holds the following at final idle under defaults: site-pure-1 280.21 MiB; site-pure-16 296.55 MiB. The ordinary and 10-second observations, both cycles and ranges are reported in [phase measurements](results/pass10/phases.md).

| Options / naming / workload | mi MiB | Oracle MiB | Static MiB / capture | Hybrid MiB / capture | Live heuristic MiB | Neutral rules MiB | Names rule MiB | TTL rule MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| defaults/named/site-pure-1 | 280.21 | 214.00 | 216.81 / 95.8% | 216.81 / 95.8% | 286.83 | 304.81 | 216.81 | — |
| defaults/named/site-pure-16 | 296.55 | 234.80 | 239.98 / 91.6% | 241.92 / 88.5% | 305.36 | 331.91 | 239.74 | — |
| immediate/named/site-mixed-1 | 144.70 | 26.06 | 28.12 / 98.3% | 28.10 / 98.3% | 146.87 | 75.73 | 146.52 | 28.09 |
| immediate/named/site-mixed-16 | 146.43 | 33.54 | 46.38 / 88.6% | 46.67 / 88.4% | 166.64 | 89.64 | 154.94 | 46.29 |
| immediate/named/site-pure-1 | 280.21 | 41.34 | 43.67 / 99.0% | 43.66 / 99.0% | 228.61 | 139.38 | 43.64 | — |
| immediate/named/site-pure-16 | 296.55 | 51.88 | 62.67 / 95.6% | 65.20 / 94.6% | 259.87 | 156.20 | 61.96 | — |

The heuristic now evaluates its sparse formula on current warm observations. Rules-neutral uses P(transient)=0.5 and the same continuous C runtime checks as hybrid. Rule-names uses the fixed cache/index/table/global/config/intern/registry keyword list; rule-ttl returns permanent iff context contains ttl=day. Both semantic controls use one-hot priors and the same admission, placement and continuous runtime rules. None uses a model.


Per-site and per-(site, context) model answers and probabilities are in the [readable site table](results/pass10/model-sites.md); exact prompt states are in [model-decisions.jsonl.gz](results/pass10/model-decisions.jsonl.gz). Unasked sites and trace truth are retained in each synthetic block’s sites.json. [Full phases and costs](results/pass10/phases.md) include all controls, both original cycles where present, the 10-second sample, peak RSS and target-process CPU. [Cold and fill costs](results/pass10/costs.json) are separate from warm replay.


The combined object-logging free path now updates trace and sampled-live state exactly once before releasing storage. The dedicated test covers retired allocating threads, cross-thread frees, actual address reuse, sample counts, survivors and hybrid demotions at sample rates 1 and 64.

Warm model runs replay first-sight answers; hybrid’s rules and all no-model controls execute live. Warm replay retains IPC/service costs and excludes sidecar CPU. It is not end-to-end deployment or hypothetical on-chip inference. Server-sim live bytes exclude metadata, bookkeeping mappings and thread resources, so RSS/live is process-memory amplification. In-place realloc can log a new policy class while retaining its physical heap. Compact aggregates support the published medians; complete trace/cache/decision reconstruction still needs remote artifacts.

