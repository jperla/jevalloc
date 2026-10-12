# Review 2 — passes 4–9

Reviewed commit `7c07d56`, starting with `RESULTS.md`, then review 1, the six pass specifications, `CODEX-REPORT.md`, the implementation, runners, and committed evidence. No source files were changed and the test machine was not contacted. Calculations below use individual committed run records, not their stored medians. Local checks used temporary files and the existing macOS library; they are not reruns of the Linux performance experiments.

The principal RSS arithmetic is supported. The synthetic experiment demonstrates that separating the deliberately different lifetimes can return substantial memory under the tested allocator settings. It does not establish comparable gains with mimalloc defaults or a model advantage over a rule given the same semantic information. There is also a reproducible instrumentation bug: object logging suppresses live sampled-free processing. The heuristic comparison replays historical decisions while hybrid recomputes its runtime rules. Those issues warrant changes despite the generally careful reporting of negative results.

## 1. Findings requiring changes

### F1 — P1: object logging disables sampled frees and changes the live policy

**Location:** `src/jevalloc.c:324–325, 369, 419–426`; `src/live.inc:357–389`; `fragbench/realtime.py:65–69`; `RESULTS.md:41, 53`.

`JEVALLOC_OBJECT_TRACE` enables `tracing` while leaving `living` enabled. Allocation calls both `trace_alloc` and `live_alloc`, but `jev_free` returns through `trace_free_release` as soon as `tracing` is true. That helper calls only `trace_free` and the underlying free. It never calls `live_free`. Sample records, owner references, live-byte estimates, free histograms, and hybrid free evidence therefore survive actual frees. This is a functional instrumentation error, not just the logger's memory/time overhead.

**Reproduction:** a local C fixture performed 1,000 `malloc(1024)`/`memset`/`free` pairs at one site, with `JEVALLOC_MODE=live`, `JEVALLOC_SAMPLE=1`, and admission set above its allocation volume so no decision service was needed. The same existing Darwin library reported:

| Configuration | Samples at the work site | Surviving samples at that site |
|---|---:|---:|
| Normal live mode | 1,000 | 0 |
| Live + `JEVALLOC_OBJECT_TRACE` | 1,000 | 1,000 |

The committed Linux results independently show the defect: `results/pass9/per-alloc-small/matrix.json` reports **37 samples / 37 survivors** in the cold run and all five logged warm runs; `performance/matrix.json` reports **37 / 2** in every unlogged warm run. Each unlogged repetition reports **2,214 changed requests out of 2,229**. This is systematic missing-free evidence, not merely concurrent snapshot drift.

**Impact:** a hybrid workload with object logging can fail to demote a wrong permanent prior and can promote on a false absence of frees. A runtime-model or heuristic request receives wrong statistics. The current small per-allocation model prompt is static with respect to runtime statistics (`tools/jevd.py:64`, `tools/prompts.py:27–37`), so this does **not** invalidate its independently logged object lifetimes or prove that its TTL answers are wrong. The separately unlogged 7.75 MiB measurement remains a real measurement. It does invalidate treating the logged and unlogged instruments as differing only in logging overhead.

**Fix:** when both modes are active, process the trace free and the sampled live free exactly once, before the physical block is freed. Add a combined-mode test that compares sampled free/live counts and hybrid demotions with and without object logging, including cross-thread frees and address reuse. Recollect the affected cold schedule/accuracy evidence after fixing the instrumentation, or explicitly retain it as evidence from the defective logger and qualify the replay comparison.

### F2 — P1: the measured heuristic is a replayed schedule, not the live heuristic

**Location:** `bench/run.py:104–116`; `tools/jevd.py:30–33, 47–55, 98–101`; `src/live.inc:199–206, 328, 351, 367, 388`; `RESULTS.md:33, 37, 168–169, 228, 368–370`.

Every warm `jev-live:*` run, including `heuristic`, receives `--replay`. A matching `(key, ordinal)` returns the old class before reaching the heuristic formula. Changed runtime state is logged, not evaluated. Conversely, hybrid's sampled-allocation/free rules execute again in C in each warm run. The comparison consequently mixes a frozen adaptive baseline with a live adaptive treatment.

**Reproduction:** using `Decisions` locally without networking, a request with 16 cohort entries, 8,192 older bytes, no frees, and a sufficiently old survivor returns permanent. Replay that slot with all 8,192 older bytes freed: it still returns permanent. Evaluating the changed request normally returns transient. In the committed site-mixed-16 matrix, the five heuristic repetitions contain **160 changed requests**; pass-8 pure plus regression matrices contain **818** heuristic request changes. These counters do not prove how many labels would change, but they rule out assuming identical inputs.

There is also an important limitation even without replay: the heuristic is checked at the sparse sidecar schedule, with at most four rechecks by default, whereas hybrid checks on every sampled birth/free. After its final recheck the heuristic cannot react to a later load drop. Both the observation schedule and the prior differ.

**Fix:** execute the deterministic heuristic from current warm statistics; there is no model inference to remove from this baseline. Preferably add the same continuous C runtime rules with a declared neutral prior as another control, keeping the historical heuristic for comparison. Until rerun, label the existing columns “replayed heuristic schedule” and restrict conclusions to that comparator. Do not infer the missing baseline's RSS or direction of change from this review.

### F3 — P2: the 280 MiB baseline is not a default-options mimalloc measurement

**Location:** `fragbench/run.py:11–16`; `fragbench/real.py:4`; `fragbench/realtime.py:11`; `bench/run.py:11–16, 99–100`; `RESULTS.md:3, 63, 168–189, 255, 1037–1039`.

All committed main server-sim mimalloc run records examined, from pass 4 through pass 9, explicitly set `MIMALLOC_PURGE_DELAY=0`, `MIMALLOC_ARENA_PURGE_MULT=1`, and `MIMALLOC_PURGE_DECOMMITS=1`. The runner strips inherited mimalloc variables before installing those settings. The vendored defaults are **10 ms**, **10**, and **1**, respectively (`third_party/mimalloc/src/options.c:122, 139, 148`); arena delay multiplies the first two (`src/arena.c:467–469`).

**There is no committed matching default-options server-sim comparison from which to report what defaults hold at idle.** The file `results/pass6/default-evidence.json` concerns the unknown-site class fallback, not mimalloc options. The observed final idle baseline is 280.21875 MiB for the configured one-thread workload; a default-options value is **not checkable from this repo**.

Zero delay requests immediate purging (`third_party/mimalloc/src/segment.c:554–558`), so it would be wrong to explain the 280 MiB simply as waiting less than a configured purge deadline. Nevertheless, retention/reuse during the preceding allocation stream can change with options. A zero-delay experiment does not establish the same layout or saving under defaults. Nor does ten seconds of quiet idle with the same zero-delay configuration supply that missing control.

**Fix:** name the configuration in the headline/baseline legend. Add a matched, separately labelled default-options series before making default-behavior claims: unset the mimalloc overrides for both baseline and placement variants, preserve the workload and phase protocol, and report both cycles. For this review, qualify the conclusion; do not substitute an invented default RSS or contact the test machine.

### F4 — P2: the synthetic comparison does not isolate the value of a model

**Location:** `fragbench/server-sim.c:25–39, 72–88`; `descriptions/server-sim.txt:1`; `descriptions-leaky/server-sim.txt:1`; `tools/prompts.py:7–15, 20–39, 47–56`; `tools/jevd.py:98–101`; `RESULTS.md:3, 168–169, 362–364, 923–939`.

The old description explicitly identifies `create_session_state` as ending at load drop and `insert_cache_index` as never freed; it also explains the mixed TTL mapping. That is answer-bearing benchmark-author input, and the report correctly acknowledges it at lines 938–939. In passes 7–9 the direct function-to-lifetime description is removed, but the benchmark's function names and prompt criteria still encode the intended answer: request/session objects versus a never-removed cache/index entry. The “neutral” description also states that session state is kept while a session is active. This is useful semantic information, but it is not a blind test of lifetime inference from arbitrary real code.

The no-description control is informative: static-model captures **99.0614% / 94.7979%** of the oracle saving with one/16 threads, versus **99.0744% / 94.0065%** with the description. Thus the description is not necessary for the demonstrated site-pure success; the remaining named stacks suffice in this fixture. There is no opaque/renamed-stack holdout, so a precise causal percentage attributable to names cannot be estimated. The separation of the dominant session and cache paths is fully expressible by a two-branch rule on their author-chosen names.

In site-mixed, the author maps the same TTL variable used to decide retention into the literal strings `ttl=0`, `ttl=short`, and `ttl=day` immediately before allocation. The model is being told the discriminating request attribute in meaningful language. That is legitimate input for the proposed context API, but a much easier and more annotated problem than discovering lifetime from a shared stack. The observed shared-payload answers are exactly the rule **permanent iff `ttl=day`**, otherwise transient. That rule also reproduces **every model-answered payload label in the small experiment**, including its 119 errors against the half-volume truth definition. The ten mixed hybrid runs have zero transitions: their saving is explained by the context-conditioned prior and placement, not runtime correction or demonstrated per-object reasoning beyond the bucket.

The heuristic is keyed by context, but never interprets its text; it uses only sampled survival statistics. Before the first drop, sessions and retained entries can have indistinguishable free histories. This comparison measures semantic prior information versus one statistics-only policy, not “model versus equally informed no-model alternative.” No direct oracle label is sent in the model payload: passing a table to jevd and incorporating its entry into a cache identity (`tools/jevd.py:67`) is not itself prompt leakage; model state construction is separate.

**Fix:** state this limitation beside the headlines. Add an explicitly labelled deterministic names/TTL rule with the same admission and placement machinery, and an unseen workload or renamed/opaque-context ablation before claiming a model-specific advantage. A rule's measured RSS is not available here; matching labels alone does not justify inventing its cost or RSS.

## 2. Independent numerical audit

For each `(workload, variant)`, I selected successful, output-valid repetitions 0–4, excluding cold/fill/probe/rejected/error records, required exactly those five repetitions, selected the last-cycle `idle` measurement, and took its median in bytes before dividing by 1,048,576. Capture is `(mi − policy)/(mi − oracle)`; pass 8 uses the better of the tested oracle/search tables. I did not average the cycles or mix matrices from different passes.

**Supported:** the requested headline idle-RSS tables, capture percentages, per-object arithmetic, and Mesh win counts reproduce at their displayed precision. **Wrong:** the combined logger's live survivor statistics and any interpretation of the heuristic numbers as executing its formula afresh on warm state. **Not checkable:** default-options fragbench RSS, a held-out causal attribution to names/context, the remote-only prompt-study observations, and full reconstruction of remote-only traces/decision/cache logs. These distinctions matter more than rounding.

### Site-pure and site-mixed history

These are independently recomputed MiB, shown to three decimals. “Adaptive” is the historical repeatedly queried model, not hybrid.

| Pass / prompt | Workload | mi | Oracle | Static model | Adaptive | Heuristic |
|---|---|---:|---:|---:|---:|---:|
| 6 | pure-1 | 280.219 | 41.355 | 282.773 | 282.773 | 228.770 |
| 6 | pure-16 | 295.492 | 51.723 | 298.293 | 313.492 | 251.574 |
| 6 | mixed-1 | 144.711 | 144.969 | 148.879 | 148.879 | 146.371 |
| 6 | mixed-16 | 146.426 | 149.664 | 165.297 | 165.441 | 155.281 |
| 7 / stack-v1 | pure-1 | 280.219 | 41.359 | 43.570 | 231.133 | 228.535 |
| 7 / stack-v1 | pure-16 | 296.547 | 51.684 | 66.359 | 261.699 | 262.828 |
| 7 / no description | pure-1 | 280.215 | 41.328 | 43.570 | 231.129 | 228.512 |
| 7 / no description | pure-16 | 296.547 | 51.527 | 64.273 | 260.195 | 261.500 |
| 7 / stack-v1 | mixed-1 | 144.699 | 144.984 | 146.363 | 154.281 | 146.434 |
| 7 / stack-v1 | mixed-16 | 146.426 | 149.668 | 154.387 | 164.945 | 154.887 |
| 7 / no description | mixed-1 | 144.699 | 144.980 | 146.367 | 154.281 | 146.422 |
| 7 / no description | mixed-16 | 146.430 | 149.625 | 154.566 | 166.344 | 154.961 |

Sources: `results/pass6/fragbench/matrix.json`; the four `results/pass7/{pure,rest}-stack-v1{,-nodesc}/matrix.json` files. These support `RESULTS.md:376–387, 763–768`. Redis rows in those tables also reproduce: pass-6 mi/oracle are 181.914/187.992 MiB for redis-mesh and 268.852/270.859 for redis-drop; pass-7 stack-v1 gives 183.945/185.961 and 269.426/271.023. Neither oracle saves memory in those comparisons.

| Pass 8 workload | mi MiB | Oracle MiB | Static MiB / capture | Hybrid MiB / capture | Heuristic MiB / capture |
|---|---:|---:|---:|---:|---:|
| site-pure-1 | 280.21875 | 41.32422 | 43.56250 / 99.0631% | 43.57422 / 99.0582% | 228.55078 / 21.6279% |
| site-pure-16 | 296.54688 | 51.45312 | 63.54688 / 95.0657% | 63.27344 / 95.1772% | 260.21875 / 14.8221% |

Source: `results/pass8/pure/matrix.json`. This supports `RESULTS.md:168–169, 181–182`. The static and hybrid gains are nearly the same here; these results do not demonstrate an added benefit from hybrid corrections.

The pass-4 instrument record gives final mi/key-only/oracle **280.21484/280.29297/42.32813 MiB** and **296.54297/295.68359/58.58984 MiB**, consistent with `CODEX-REPORT.md:145–153`; it is correctly described there as pre-final evidence. The pass-5 historical table (`RESULTS.md:965–970`) reproduces from `results/pass5/progress/fragbench-synthetic-complete.json`: pure-1 mi/fixed-S-oracle/random **280.21875/280.07422/42.55078**, pure-16 **295.50000/293.44531/64.72266**. Its four rows and live-policy values round as printed. This is a real wrong-boundary result, not a result to pool with the later transient/permanent oracle.

The sensitivity table at `RESULTS.md:971–974` also reproduces from `results/pass6/sensitivity/matrix.json`: the four permanent-definition oracle medians are **41.32422, 41.36719, 41.36719, 41.35156** MiB for one thread and **50.91406, 51.50000, 51.65234, 51.67969** for 16. The three fixed-S alternatives remain about **280.07** and **292.85–293.33** MiB. This tests the lifetime boundary, not mimalloc purge defaults.

### The seven real-program gates

All values below come from `results/pass8/real/<workload>/matrix.json`, recomputing the final-idle medians. “Best saving” is against mi and can be negative.

| Workload | mi MiB | Oracle MiB | Search MiB | Best saving |
|---|---:|---:|---:|---:|
| LevelDB | 87.61328 | 87.92969 | 87.80469 | -0.22% |
| Redis drop | 270.70703 | 271.04297 | 271.00391 | -0.11% |
| Redis mesh | 185.85156 | 185.96484 | 186.06250 | -0.06% |
| Redis sessions | 48.03906 | 49.95703 | 48.19141 | -0.32% |
| RocksDB cache | 121.96875 | 132.64453 | 126.64063 | -3.83% |
| RocksDB churn | 24.87500 | 25.92969 | 25.11328 | -0.96% |
| SQLite | 78.94531 | 82.07031 | 79.00781 | -0.08% |

Thus all seven fail the specified strict >5% gate, and their pass-8 matrices contain no live-model variants. I also recomputed every three-run candidate median and every >2% accept/reject decision from all **525 search trials**: only RocksDB-cache accepts flips (two). They do not survive the independent final comparison. This supports the carefully qualified definition at `RESULTS.md:173`, not a universal absence of useful per-site labels.

The later compaction matrix must remain separate: RocksDB-cache's oracle is **114.58203 / 125.15234 = 0.915540× mi**, an **8.4460%** descriptive saving. `RESULTS.md:152` already reports this contrary later observation and the overlapping ranges. It does not retroactively change the earlier gate; it does prevent an unqualified claim that RocksDB has no per-site headroom in general.

### Context and per-allocation RSS

| Workload | mi | Site oracle | Context oracle | Static/site | Static/context | Hybrid/context | Heuristic/context | Search | Per-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mixed-1 | 144.69531 | 145.00000 | 26.05469 | 146.43359 | 28.10547 | 28.10938 | 146.87109 | — | — |
| mixed-16 | 146.42188 | 149.69922 | 33.40625 | 154.45313 | 46.10547 | 46.61719 | 167.02734 | — | — |
| redis-drop | 271.19922 | 270.54688 | 283.77734 | — | — | — | — | 285.71094 | — |
| redis-mesh | 185.96094 | 188.04297 | 196.06250 | — | — | — | — | 180.01172 | — |
| redis-sessions | 48.10938 | 50.03125 | 50.03516 | — | — | — | — | 48.25391 | — |
| per-alloc-small | 7.96484 | 8.05469 | 5.10938 | — | — | — | — | — | 7.75391 |

Sources: `results/pass9/<workload>/matrix.json`, except the last row which must use `results/pass9/per-alloc-small/performance/matrix.json`. Using the logged small-run matrix instead would give **15.77344 MiB** for per-alloc, not the headline 7.75391; the report correctly selects the separate unlogged series.

Recomputed oracle savings are **81.9934% / 77.1849%**. Static capture is **98.2714% / 88.7633%**; hybrid capture **98.2681% / 88.3105%**. Small per-allocation saving is **2.6484%**, capture **7.3871%**. All support the rounded headline values. Redis-mesh's context search saves **3.1992%** against mi, below the gate. The other context gates fail too. All **225** context-search trials reproduce their decisions; only redis-mesh accepts a flip (one).

The headline pair/signature/coverage counts are consistent with the committed `truth` and `context-coverage.json` aggregates, and the permanent-pair catalogue supplies labels/probabilities for its stated subset. Complete raw pass-9 traces are not committed, so independently regenerating *all* pairs, signatures and byte coverage from original allocation events is not possible locally. These counts are supported by recorded aggregates, at a weaker evidentiary level than the RSS medians recomputed from individual phase observations.

### Per-object accuracy

I read all **2,414** rows of `results/pass9/per-alloc-small/object-truth.jsonl` and recomputed truth as “no death, or `2*(death − birth) > 3,695,936`”, rather than accepting each stored `truth`. The final allocation volume equals the sum of recorded requested sizes. Confusion matrices, rows truth transient/permanent and columns chosen transient/permanent, are:

| Population | Confusion matrix | Correct | Object accuracy | Byte accuracy |
|---|---|---:|---:|---:|
| Model-answered objects | `[[2031,0],[119,79]]` | 2,110 / 2,229 | 94.6613% | 93.4254% |
| All payloads | `[[2146,0],[175,79]]` | 2,225 / 2,400 | 92.7083% | 91.9778% |
| All logged objects | `[[2158,0],[177,79]]` | 2,237 / 2,414 | 92.6678% | 91.8877% |

The **185** unasked count is for all logged objects, not just payloads; payloads have **171** unasked. The report says “total objects”, so 185 is not an arithmetic error. Always-transient scores **91.1171%** on answered objects and permanent recall is **39.8990%**, as reported. All 119 answered errors are short-TTL objects exceeding the half-volume threshold; all 79 answered day-TTL objects are labelled permanent. The prompt's “freed while running” semantics differ from this finite-volume truth definition, so those errors are not necessarily failures to understand the described TTL behavior.

The cold record corroborates **2,229 decisions**, **3,048.3178 HTTP seconds**, and **3,060.3400 wall seconds**, with zero recorded cache hits/errors. Original HTTP responses and the unprocessed object event stream are not all committed; this verifies the provided per-object/counter evidence, not an independent reconstruction of the inference service. The exact object trace is separate from the defective sampled-free statistics in F1.

### Mesh

Recomputed from all **385 warm runs / 77 groups** in `results/pass9/compaction/*/matrix.json`. Every group has exactly five repetitions; the final `idle` and `idle10` medians are equal in all 77. MiB and savings below use those medians.

| Workload | mi | Mesh | nomesh | Mesh saving / nomesh | Mesh saving / mi |
|---|---:|---:|---:|---:|---:|
| LevelDB | 87.58984 | 78.43359 | 177.30469 | 55.76% | 10.45% |
| Redis drop | 269.41406 | 92.39844 | 331.20313 | 72.10% | 65.70% |
| Redis mesh | 185.98438 | 144.56250 | 198.39844 | 27.14% | 22.27% |
| Redis sessions | 48.03125 | 68.25000 | 263.99609 | 74.15% | -42.10% |
| RocksDB cache | 125.15234 | 106.53906 | 129.01563 | 17.42% | 14.87% |
| RocksDB churn | 24.96484 | 37.67188 | 68.52344 | 45.02% | -50.90% |
| mixed-1 | 144.69922 | 139.98047 | 170.26953 | 17.79% | 3.26% |
| mixed-16 | 146.42188 | 149.87500 | 172.69922 | 13.22% | -2.36% |
| pure-1 | 280.21875 | 270.62109 | 328.85938 | 17.71% | 3.43% |
| pure-16 | 296.54688 | 290.94531 | 331.41797 | 12.21% | 1.89% |
| SQLite | 78.93750 | 317.52734 | 317.52344 | -0.0012% | -302.25% |

This supports **10/11 >5% wins over nomesh**, and exactly **four** >5% wins over mi, all real-program workloads. The compaction-matrix placement values also reproduce: pure-1 oracle/static/hybrid/heuristic **41.36719/43.55859/43.57031/228.50391** MiB; pure-16 **51.83203/64.86328/63.37891/255.43359**; mixed-1 context-oracle/static/hybrid/heuristic **26.04688/28.12500/28.12500/146.86719**; mixed-16 **33.51563/46.73047/47.32813/165.63672**. These are separate measurements from the earlier matrices, not inconsistent rounding.

The report appropriately distinguishes Mesh/nomesh from Mesh/mi, notes that quiet waiting does not necessarily trigger another meshing pass, and warns that RSS is not the physical-memory saving measured by PSS. Retain those qualifications. “After 10 seconds” is a measurement time, not evidence of compaction caused by ten seconds of waiting. No PSS comparison or statistical superiority beyond these descriptive medians is established.

## 3. Is server-sim a sound instrument?

**For its stated synthetic, configured-RSS question, largely yes.** Allocations are touched (`server-sim.c:29–30`). The free loop precedes the idle protocol (`:88–94`). Workers sleep for 250 ms, execute the common 1,024 allocate/free pulse, then synchronize and wait another 250 ms before the idle measurement (`:42–59, 90–94`). All workers remain alive until the second cycle finishes; the idle gain is not produced by comparing terminated oracle workers against live mimalloc workers. With immediate purge enabled, free memory has an opportunity to be returned before the sample. This is not proof that every possible empty retired page has been collected; there is deliberately no allocator-specific forced collect.

The two cycles use distinct size ranges and deliberately retain first-cycle cache objects. `worker_live` is not reset when the pointer slots are overwritten. I independently simulated the 64-bit seeded RNG, TTL draws, allocation sizes, and drop predicates, then compared the result with **1,014** recorded phase observations from the pass-8 pure, pass-9 mixed, and unlogged small matrices (including available cold records): **zero live-byte mismatches**.

| Workload | First idle requested live bytes | Final idle requested live bytes |
|---|---:|---:|
| pure-1 | 11,523,136 | 30,725,760 |
| pure-16 | 11,528,192 | 30,749,952 |
| mixed-1 | 5,734,976 | 15,374,080 |
| mixed-16 | 5,767,040 | 15,448,576 |
| per-alloc-small | 80,896 | 210,176 |

These are correct **workload requested bytes**, not all process live bytes. The `mmap` pointer/size bookkeeping, thread stacks/TLS, libc/allocator metadata, rounding, and instrumentation remain in RSS but outside that denominator (`server-sim.c:64–68`). Therefore RSS/live is an amplification metric, not a pure measurement of allocator fragmentation. This particularly matters for the small case. SQLite, Redis, LevelDB and RocksDB use different application metrics, with the partial database estimates already acknowledged at `RESULTS.md:255`.

The pass-6 instrument also checks each cycle separately. From `results/pass6/instrument/matrix.json`, mi/random/oracle idle MiB are **122.21875/22.86719/22.83203** and **280.21875/42.55469/41.40625** for one thread, and **136.55078/41.41016/32.16406** and **295.67578/64.77734/50.58984** for 16. Both-cycle acceptance is supported. The later headlines consistently use the final cycle, not their mean. The superseded pass-8 Redis-mesh search did average cycles, but the final runner (`fragbench/headroom.py:17–20`) and committed replacement gate use the final idle correctly; the mistake is disclosed at `RESULTS.md:253`.

The payload-only experiment intentionally omits the purge pulse and parsing/response allocations for **all** of its controls, so its 7.96 MiB baseline cannot be compared directly with the 144.70 MiB full-workload baseline. The ten-second compaction runs add idle in cycle zero too, altering the history before cycle one; the report correctly keeps them separate.

Fairness to mimalloc is good within the specified configuration: the plain library is built from unpatched vendor sources, while the shim uses the patched core; Linux optimization settings are applied to both (`CMakeLists.txt:17–49`). Settings and work are shared, and no special collect is used for placement. Default-options behavior remains the missing experiment in F3. A single seeded “random” table is a useful control but not an average over random policies; pass 5 itself shows how lucky session/cache separation can dominate that comparison.

## 4. Replay, timing, and implementation correctness

**Cold runs are excluded now.** `tools/selection.py:2–15` filters negative repetitions and failure/fill/probe records and verifies exact repetition membership. The reviewed headline groups satisfy these requirements independently. The review-1 six-value-median defect is not present in these measurements. Pass-9's report helper itself only checks nonnegative repetition (`tools/pass9_report.py:11–15`), so using the common defensive selector there would prevent a future regression; the current inspected groups are nevertheless valid.

**Warm hybrid rules really run.** Its prior is replayed, but `hybrid_update_locked` executes on current samples and frees, and the fast allocation path reads the current site class. Pass-8 pure plus regression contains 360 warm live records with zero recorded inference seconds, replay misses, decision errors or new decisions; hybrid records **2,135 demotions** across those repetitions. Thus hybrid is not just replaying its cold transition sequence. The ten pass-9 mixed hybrid runs have zero transitions. Their success should not be attributed to runtime corrections.

Warm timing measures the synchronous socket/sidecar replay system with inference removed. It retains stack capture, sampling, allocator bookkeeping, IPC and service scheduling. It is neither end-to-end cold deployment cost nor a prediction of an integrated inference chip's latency. Wait periods dilute the wall ratios; target CPU excludes sidecar/model/Redis-client CPU. These limits are mostly already stated. The small unlogged per-allocation series indeed costs about **1.809× wall / 32.843× target CPU**; “inference removed” does not make its per-allocation machinery cheap. The pass-8 sh6benchN ratios also reproduce: **5.528903075 / 0.156681764 = 35.29×** hybrid and **13.09×** static-model.

**Lazy TLS and heap lifecycle:** the 72 KiB embedded cache from review 1 is gone. `Thread` contains a pointer to a lazy mmap cache (`src/jevalloc.c:35–38, 195–209`); `none_fast` avoids it, and the ordinary/aligned none paths use the default allocator. Thread cleanup unmaps the cache and flushes live shards. On Linux the mimalloc teardown hook calls this before abandoning heaps (`patches/mimalloc-class-tags.patch:58–69`); Darwin uses its pthread destructor. Fixed request-context text adds a small per-thread footprint, so “lazy” does not mean zero TLS. No new lifecycle corruption was established in the supported ordinary-thread path.

**Tagged, reclaim-enabled heaps:** classes use tags 1 and 2 with `allow_destroy=false` (`src/jevalloc.c:358–366`). This is materially different from untagged `mi_heap_new()`. Upstream only absorbs compatible equal-tag heaps into the backing heap (`third_party/mimalloc/src/heap.c:466–488`). The patch prepares matching heaps before taking ownership of abandoned pages; on allocation failure or nested reclaim it re-marks the segment abandoned and returns NULL before page ownership changes (`patches/mimalloc-class-tags.patch:7–29`). The modified caller accepts NULL. The normal receiving-thread test exists at `tests/defects.c:16–22, 45–49`. I found no demonstrated class-mixing or double-free defect in this path. The patch is private-version-dependent, including the use of `mi_page_t.padding[0]`; it is not a portable allocator extension.

**Failure paths:** a missing class heap causes NULL/ENOMEM rather than silently routing to an incorrect class (`src/jevalloc.c:366`); a failed moving realloc preserves the old allocation (`:387`). Failed cache mmap returns an unkeyed/default allocation path (`:197–208`). Socket operations have a deadline, handle partial I/O, and fail into a default answer/circuit breaker (`src/live.inc:129–174, 325`). This circuit suppresses future requests globally while already-classified sites can retain earlier answers; the runner rejects measured decision failures. Live/trace metadata allocation still aborts on OOM rather than offering graceful degradation (`src/trace.inc:36`, `src/live.inc:299–300`), so the correctness logs should not be read as production-grade OOM recovery. The wrapper failure-injection test does not exhaustively test tag-preparation OOM.

**Sharded statistics and synchronization:** successful allocation counters are owner-private; only published atomic totals are shared. Pointer records use sharded locks, cohort state uses its own lock, and sampled owner references survive thread exit (`src/live.inc:257–283, 357–389`). Free releases the sample lock before dropping the owner reference and taking `live_mutex`, avoiding that obvious lock-order cycle. Byte-weighted frees and persistent cumulative hybrid totals address the review-1 count/byte and retirement problems. The page filter saturates conservatively; saturation can add work rather than suppressing an actual sample. F1 is the concrete exception: combined tracing bypasses this lifecycle entirely.

The allocation clock is deliberately approximate (`src/live.inc:263–265, 377–378`). A birth includes the allocating thread's unpublished bytes; a cross-thread free may not see them and clamps an apparent negative age to zero (`:387`). Admission can be delayed by other threads' unpublished counters, and active threads can leave incomplete exit statistics. These affect age gates and reported coverage; they are acknowledged approximations, not an exact global allocation-order clock. No claim of exact cross-thread age or complete active-thread exit totals should be added.

**Hybrid rules:** `src/hybrid.h:5–9` implements the stated thresholds, including `>=16`, `>=5%`, strict `P(transient)<0.7`, strict oldest-age comparison, and `>=64 MiB`. Cohort updates/first-prior installation are locked; class reads are atomic. Cumulative sampled free evidence survives reservoir replacement and retirement. These rules can still misclassify an eventually freed object; “frees safely correct the prior” means a specified heuristic, not a mathematical guarantee of lower RSS. The report's mixed regression outcomes and shutdown-demotion caveat are appropriate.

**Context/API/cache identity:** the library copies and terminates at 255 bytes, hashes that copied text, reserves signature zero for empty context, and does not keep a caller buffer (`src/jevalloc.c:60–72`). Normalization belongs to the application. TLS keeps contexts separate across threads; it does not automatically propagate context across asynchronous work. The raw stack cache checks signature, frame count and PCs (`:195–216`), and the normalized pair key folds the signature into the site key (`:240–242`). Live sites copy their first context/frames (`src/live.inc:299`), so raw cache replacement does not overwrite an existing site's model stack. This fixes the ordinary cache-identity issues raised in review 1. The 64-bit hashes are still probabilistic identity, not collision-proof; no collision in these data was demonstrated. Distinctions beyond the first 255 bytes are intentionally lost.

Redis restores outer dispatch context around nested command calls (`patches/redis-request-context.patch:59–67`). Its parsing-before-dispatch limitation, numbered-key cardinality and table overhead are real and already disclosed. The key-only control also loads the oracle table (`bench/run.py:19–21`), so its approximately 16 MiB extra RSS is not the cost of hashing a 255-byte string alone.

**Per-allocation mode:** admission remains per pair; after admission, the mode bypasses the ordinary fast answer cache, serializes each pair's requests, and returns the allocation's own answer even if another thread later changes the site class (`src/live.inc:314–347, 349–352`). The sidecar includes requested size and context in the prompt, keys its response cache by the full request, and warm replay rejects changed size/context/signature/frames (`tools/jevd.py:52–53, 67–80`). It allows changed runtime statistics, as documented. The observed small run answers 2,229 of 2,400 payloads; it does not see every payload from startup.

The inherited in-place realloc path retains physical placement while recording a new logical allocation (`src/jevalloc.c:374–385`). In live/per-allocation mode it can even obtain a new class without moving the block. Thus a logged chosen class is not universally proof of the block's physical heap. The small payload fixture uses malloc/free, so its object-placement result is not invalidated by this path; the report correctly warns about Redis trimming. A claim of per-allocation physical reclassification must either exclude in-place realloc or relocate when the class changes and separately record physical versus requested policy class.

Linux dynamic image registration after startup and post-fork synchronization remain outside the validated scope, as already disclosed at `RESULTS.md:1047`; this review does not treat those inherited exclusions as newly discovered corruption.

## 5. Required wording and missing caveats

The report is substantially better calibrated than review 1: it reports unsuccessful real workloads, limited greedy search, baseline accuracy, poor permanent recall, expensive regressions, overlapping ranges, inference exclusion, and RSS/PSS limitations. Retain these. The following replacements/additions would bring the remaining claims to the strength of the evidence:

1. **Headline semantic dependence (`RESULTS.md:3, 168–169, 362`).** Add: “These gains occur in an author-designed synthetic server whose named allocation paths or supplied TTL buckets reveal the intended lifetime distinction; no equally informed names/TTL rule or held-out naming/context test was measured.” The numerical capture claims can remain.
2. **Baseline label (`:9, 63, 179`, options currently buried at `:255, 1038`).** Write: “Here mi means upstream mimalloc with purge delay 0, arena purge multiplier 1 and decommit enabled; matching default-options fragbench measurements are not available.” This makes clear that 280 MiB is measured, but not measured under defaults.
3. **Heuristic comparison (`:33, 37, 168–169, 368–370`).** Write: “The heuristic numbers replay a cold run's sparse decision schedule; unlike hybrid's C rules, the heuristic formula is not recomputed from warm observations, so these results do not establish superiority over a live statistics-only policy.”
4. **Logging/replay qualification (`:41, 53`).** Write: “The cold object logger preserved exact object lifetimes but, in this revision, skipped live sampled-free updates; unlogged warm runs restore those updates and differ in 2,214 of 2,229 request states per run. Their size/context/stack sequence is checked, and the model prompt does not consume the changed runtime statistics.” Remove this defect qualification only after correcting and validating the combined mode.
5. **Direct model versus bucket interpretation (`:39–47`).** Add: “A deterministic rule returning permanent for `ttl=day` and transient otherwise reproduces every model-answered payload class in the small experiment; this experiment demonstrates context-conditioned placement, not an advantage from repeated inference over that rule.” Keep the 94.66%, 91.12% and 39.90% statistics together.
6. **“No per-site headroom” (`:171`).** The following paragraph already limits it correctly, but a more accurate headline is: “Neither tested table cleared the 5% gate in the original five-run comparison on any of seven real workloads; this is not a bound over all per-site policies, and the later RocksDB-cache oracle comparison has an 8.4% lower median.” No allegation of an incorrectly executed gate is warranted.
7. **Historical causal assertion (`:923–935`, “the source code was the problem” and “drowns the names”).** Write: “A separate four-site prompt study reportedly changed the answers when source snippets were included; its raw round-6 records are not committed here. The later live result also changes admission, budget and runtime policy, so it does not isolate source snippets as the cause.” The remote-only 47.4/61.3 MiB quick check and its probability table cannot be independently verified from this repo. The current pass-7 caveat at `:364` is sound; the older categorical wording should not contradict it.
8. **RSS/live interpretation (`:774–775, 1037`).** Add: “For server-sim, live bytes count only requested workload objects; RSS includes bookkeeping mappings, allocator/runtime metadata and thread resources. RSS/live is therefore process-memory amplification relative to those objects, not allocator fragmentation alone.”
9. **Physical placement versus logical answers (`:49, 53`).** The Redis caveat is correct; make its general scope explicit: “An in-place realloc can receive/log a new policy class while retaining its old physical heap; per-object class accuracy is not always physical-placement accuracy.”
10. **Deployment and evidence scope (`:53–59, 228, 370`).** Add: “Warm replay removes HTTP inference but retains IPC/service costs and excludes sidecar CPU from the CPU metric; it measures this replay implementation, not end-to-end deployment or hypothetical on-chip inference. Compact aggregates permit recomputation of the published medians, but full trace/cache/decision reconstruction requires artifacts not committed here.”

The Mesh headline at `:63` does not need numerical correction. Its existing paired-baseline, descriptive-comparison, altered-cycle-history, quiet-idle and RSS/PSS qualifications are sufficient; do not recast it as a general physical-memory victory for placement over compaction.

## 6. Verification and disposition

Independent local checks covered all requested RSS families, final-idle gate/search arithmetic, the per-object confusion matrices and byte accuracy, the Mesh counts, and synthetic live-byte accounting. Existing offline tests `test_realtime_policy.py` (2), `test_hybrid.py` (1), and `test_stack.py` (3) passed. The logger and heuristic replay failures were reproduced separately without model requests. Committed Linux correctness/build/audit logs were inspected as evidence; the full Linux suite and experiments were not rerun, and no remote connection was attempted.

The required corrections are to the combined-mode free path, the interpretation or execution of the heuristic comparison, and the report's baseline/semantic-input caveats. The supported numerical results and negative real-workload findings should remain.

REQUEST CHANGES
