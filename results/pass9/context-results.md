# Pass 9 — decisions from live request context

site-mixed-1: context oracle saves 82.0% of mimalloc idle RSS; Clef/context captures 98.3% and hybrid/context 98.3% of that saving. site-mixed-16: context oracle saves 77.2% of mimalloc idle RSS; Clef/context captures 88.8% and hybrid/context 88.3% of that saving. No validated >5% context-table headroom on redis-drop, redis-mesh, redis-sessions. These workloads receive no model decisions.

The context API requires a small change to the application at request dispatch.

Completed context workload blocks: 6/6. Five interleaved warm repetitions per published variant.

| Workload | mi MiB | Per-site oracle | Context oracle | Code-only/site | Clef/context | Hybrid/context | Heuristic/context | Search | Per-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| per-alloc-small | 7.96 | 8.05 | 5.11 | — | — | — | — | — | 7.75 |
| redis-drop | 271.20 | 270.55 | 283.78 | — | — | — | — | 285.71 | — |
| redis-mesh | 185.96 | 188.04 | 196.06 | — | — | — | — | 180.01 | — |
| redis-sessions | 48.11 | 50.03 | 50.04 | — | — | — | — | 48.25 | — |
| site-mixed-1 | 144.70 | 145.00 | 26.05 | 146.43 | 28.11 | 28.11 | 146.87 | — | — |
| site-mixed-16 | 146.42 | 149.70 | 33.41 | 154.45 | 46.11 | 46.62 | 167.03 | — | — |

| Workload | Original sites | Context pairs | Distinct signatures | Bytes carrying context |
|---|---:|---:|---:|---:|
| per-alloc-small | 7 | 9 | 4 | 99.64% |
| redis-drop | 629 | 495421 | 160292 | 48.10% |
| redis-mesh | 621 | 626 | 6 | 11.24% |
| redis-sessions | 644 | 662 | 13 | 63.52% |
| site-mixed-1 | 10 | 16 | 4 | 99.98% |
| site-mixed-16 | 10 | 16 | 4 | 99.77% |

| Workload | Policy | Warm wall/mi | CPU/mi | Peak MiB | Cold wall s | Cold+fill HTTP s | Sidecar / model answers | Asked pairs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| per-alloc-small | jev-live:per-alloc | 1.809 | 32.843 | 8.11 | 3060.34 | 3048.32 | 2229 / 2229 | 3 / 9 |
| site-mixed-1 | jev-live:static-site | 1.072 | 1.571 | 146.48 | 6.86 | 5.45 | 4 / 4 | 4 / 10 |
| site-mixed-1 | jev-live:static-model | 1.082 | 1.636 | 114.61 | 13.69 | 12.25 | 10 / 10 | 10 / 16 |
| site-mixed-1 | jev-live:hybrid | 1.097 | 1.751 | 114.60 | 1.44 | 0.00 | 10 / 10 | 10 / 16 |
| site-mixed-1 | jev-live:heuristic | 1.040 | 1.259 | 146.62 | 1.18 | 0.00 | 34 / 0 | n/a / 16 |
| site-mixed-16 | jev-live:static-site | 1.017 | 1.302 | 156.38 | 1.24 | 0.00 | 4 / 4 | 4 / 10 |
| site-mixed-16 | jev-live:static-model | 1.009 | 1.306 | 126.48 | 1.24 | 0.00 | 10 / 10 | 10 / 16 |
| site-mixed-16 | jev-live:hybrid | 1.009 | 1.380 | 126.86 | 1.25 | 0.00 | 10 / 10 | 10 / 16 |
| site-mixed-16 | jev-live:heuristic | 1.005 | 1.011 | 169.04 | 1.05 | 0.00 | 32 / 0 | n/a / 16 |

Per-allocation accuracy on model-answered objects: 2110/2229 (94.66%). Across all payloads, including the default class before admission: 2225/2400 (92.71%). 185 total objects were not model-answered. The confusion matrix and byte accuracy are in [object-accuracy.json](results/pass9/per-alloc-small/object-accuracy.json).
Cold per-allocation: 2229 model decisions, 2229 HTTP requests, 3048.32 model seconds, 3060.34 wall seconds.
The small experiment has 2,400 payload allocations over two cycles, four times the normal payload size, and omits parsing/response allocations and purge pulses. This allows the rare day-TTL pair to reach admission within a 3,000-decision budget. The cold run logs exact object lifetimes. Separate five-run warm comparisons disable this logger, retain per-allocation decisions and sampling, and replay the recorded answers; headline RSS and warm timing use those measurements when complete.
An always-transient classifier would score 2031/2229 (91.12%) on the same answered objects. Permanent-object recall is 79/198 (39.90%). The observed chosen class is constant within each TTL bucket across the tested requested sizes.

At this small scale, per-allocation placement saves 2.6% of mimalloc idle RSS and captures 7.4% of the context oracle's saving. High object accuracy does not imply the same RSS saving: admission leaves early allocations in the default heap, and live-decision machinery has a material fixed cost. The 119 model-answered errors are short-TTL objects that exceed the trace's half-volume lifetime threshold; 56 additional day-TTL payloads precede admission.

At the shared payload stack: no context: transient (P=0.6411); kind=store ttl=0: transient (P=0.6487); kind=store ttl=short: transient (P=0.7178); kind=store ttl=day: permanent (P=0.6189).
Hybrid makes 0 class transitions across 10 warm mixed-workload runs.

The context API requires a small application change. Applications normalize and bucket the supplied text; the library copies 255 bytes plus NUL. Context applies to allocations after the dispatch hook. Redis input parsing precedes the command hook. Some context-bearing value records are logical realloc events during string trimming; the inherited in-place realloc path retains the original physical block. Context on that later event does not retroactively relocate storage, so trace classification accuracy is not a physical-placement upper bound.

Redis-drop uses colon-free numbered keys. The specified prefix rule retains these identifiers (up to 16 bytes), producing 160,292 signatures and 495,421 pairs. That defeats cache sharing and adds table/key metadata overhead; the key-only control is about 16 MiB above mimalloc. No model was run on this failed-gate workload.

Admission is 64 KiB per (site, context signature), budget 3,000. Cross-thread counter batching can delay admission. Byte coverage includes bytes allocated before an answer; it is not the fraction routed under the model label. Hybrid rules operate per pair. Cached warm runs replay recorded answers without HTTP inference; sampling and hybrid transitions still execute. The per-allocation response cache includes the full allocation request; warm ordinal replay rejects changed size, context or stack. Runtime statistics may drift.

RSS is the final idle phase, not the mean of multiple cycles. Greedy search uses the top 24 byte-heavy pairs, three runs per flip and a >2% training improvement, followed by five independent interleaved comparisons. Redis model runs require >5% validated table savings against mimalloc. Search does not prove an optimum.

CPU time is the workload process user plus system time from wait4; sidecar CPU is excluded. Wall time includes synchronous decision-service delays. Native model HTTP seconds are reported separately.

Exact permanent-pair labels, model probabilities and prompt states: [permanent-pairs.jsonl.gz](results/pass9/permanent-pairs.jsonl.gz). All measured costs: [costs.json](results/pass9/costs.json). Full median/range data: [summary.json](results/pass9/summary.json).
