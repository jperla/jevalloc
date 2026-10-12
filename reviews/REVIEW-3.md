Review 3 — commit c1182c7dc81ac8dc48881827713caf6d830d81fa

Reviewed the committed snapshot, including the pass-10 headline through `PASS10-END`, `SPEC-REVIEW2.md`, review 2, the pass-10 reports, code and individual run records. I used `git show`, the parent diff and an isolated `git archive` extraction; working-tree changes were ignored. No source files were changed and the test machine was not contacted. All file/line references below refer to this commit.

The published headline arithmetic reproduces. F1 is fixed; the live controls and naming ablations substantially answer review 2. The plausible-name hybrid benefit is a repeatable observation in these fixtures, not an established general model advantage. The substantive allocator defect exposed by this pass is unbounded live metadata for context pairs. The committed pass is also incomplete.

**Required findings**

**R3-F1 — P1: bound live metadata before admitting new context pairs.** `src/live.inc:15–40, 291–313` allocates a full `LiveSite` and a per-thread `LiveShard` for every new pair **before** testing the 64-KiB decision-admission threshold. `live_sites[16384]` and the thread's 512-bucket index are hash bucket counts, not entry limits. Sites are never reclaimed; shards persist on active threads (`src/live.inc:267–283`). A decision budget or the context string's 255-byte bound does not bound this storage.

Failing scenario: redis-drop creates numbered `k0`…`k159999` keys (`fragbench/redis_workload.py:79–89`); the context hook copies up to 16 characters before a colon (`patches/redis-request-context.patch:20–29, 48`). These keys have no colon, so the supposedly bounded prefix is effectively a distinct key identifier. The representative warm static/context record has 495,328 pairs, only nine model-asked pairs, and 45.01% unasked requested bytes. It holds 4246.531 MiB at final idle versus 281.422 MiB for static/site and 274.332 MiB for plain mimalloc. All no-model live/context controls reproduce the roughly 4.15-GiB failure (full audit below).

This is an allocator instrumentation/state-management defect, even though better application bucketing would avoid this particular trigger. A long-running application can exhaust memory merely by presenting new contexts, including contexts too small ever to get a decision. The library aborts if these metadata allocations fail (`src/live.inc:299–300`).

Fix: impose a configurable process-wide metadata-byte/pair budget and a per-site context limit, checked atomically under the existing lock **before** allocating either site or shard state; budget shards across threads as well. On overflow, use a bounded context-free site fallback or the default class without registering another pair. Bound any pre-admission frequency sketch/table too; making cohorts lazy alone leaves an unbounded key table. Record overflow counts and bytes. Do not evict state with cached shard pointers or outstanding samples without a safe lifetime protocol. Normalize Redis's numeric key suffixes into genuine key families as a separate application fix. Add a local high-cardinality stress test that holds worker threads alive, allocates/frees through many more contexts than the cap, and verifies bounded state, safe cross-thread frees and continued allocations. A future matched redis-drop run with this guard and explicit metadata-byte counters should verify the RSS/CPU improvement.

**R3-F2 — P2: finish the requested evidence and stop describing absent artifacts as available.** `SPEC-REVIEW2.md:23–24, 29–34` requires the regression set and every default-options fragbench workload. At this commit there are 24/25 completed fragmentation blocks, six of seven real workloads, an incomplete `results/pass10/defaults/named/rocksdb-churn/matrix.json`, and no committed `results/pass10/regression.json` or final `validation.json`. The launcher schedules them only after the real blocks (`scripts/pass10.sh:15–25`). The full correctness log is not a substitute for the requested performance regression comparison.

`RESULTS.md:5, 24` correctly discloses partial fragmentation completion. However, `results/pass10/README.md:10–12, 28–30` describes regression and validation artifacts in the present tense, and `results/pass10/results.md:46` invokes regression scores that are absent. Fix those references to say pending at this revision, explicitly state that the new-control regression matrix is missing in the headline, and commit the remaining accepted five-run groups/audits before calling pass 10 complete. This review does not authorize or perform a remote rerun.

**Disposition of review 2's four findings**

| Finding | Status | Checked evidence |
|---|---|---|
| F1: object logging skips sampled frees | Resolved | `src/jevalloc.c:419–425` now calls trace-free and live-free exactly once before physical free. `tests/test_combined.py:15–65` covers retired producer threads, cross-thread frees, actual address reuse and demotions. Committed `results/pass10/tests/combined.json` has equal logged/unlogged 12,288 samples at rate 1 and 192 at rate 64, zero survivors and one demotion. The recollected small matrices have 37 samples / 2 survivors in the cold, five logged and five unlogged records in each options series. |
| F2: replayed heuristic compared with live hybrid | Partly resolved | The implementation defect is resolved: `bench/run.py:110–117` excludes deterministic policies from replay; `tools/jevd.py:16–17, 75, 103–106` rejects replay and recomputes the heuristic. Neutral rules use the continuous C policy. All four named server workloads have five measured repetitions alongside static/hybrid, under both configurations. The required regression rerun is not committed. |
| F3: nondefault baseline presented as defaults | Partly resolved | Baseline labelling and the four server comparisons are resolved. `bench/run.py:13` strips inherited options; `fragbench/review2.py:39–41` removes row overrides for defaults; the committed accepted records agree. Both cycles and 10-second observations are present. The seventh real workload is incomplete. Also, adding the long wait in cycle zero changes the history entering cycle one, so across-series differences do not isolate options alone. |
| F4: model value not isolated from names/TTL | Resolved for the requested synthetic controls | Fixed names/TTL rules, neutral rules, and both renamings are implemented and measured, with probabilities. The named results do not demonstrate a model advantage; static loses the positive saving in all eight renamed comparisons; opaque hybrid loses it in all four. Plausible hybrid supplies a narrow positive result, examined below. This resolves the missing control, not the broader question of utility on unseen applications. |

The fresh immediate small collection has 2,229 HTTP decisions; defaults explicitly reuses its fixed-library answer schedule. In both, the independently logged answered-object confusion matrix is `[[2031,0],[119,79]]`: 2110/2229 = 94.6613% accuracy, 2031/2229 = 91.1171% always-transient accuracy, and 79/198 = 39.8990% permanent recall. The TTL rule matches all 2,229 answered classes. Defaults' recorded replay drift of 1,200 refers to the immediate source schedule, not a recurrence of the logging bug; the committed within-defaults request comparison reports no logged/unlogged differences. Full request logs are not committed, so that last comparison can be inspected as evidence but not independently reconstructed here.

**Disposition of all ten wording corrections**

All ten are substantively resolved as wording corrections; the incomplete experiments above remain separate.

| # | Review-2 correction | Status and current location |
|---|---|---|
| 1 | Synthetic semantic dependence | Resolved: `RESULTS.md:16–22, 41–43`; named rules match, and the renamed result is limited to specific synthetic ablations. |
| 2 | Baseline/configuration label | Resolved: `RESULTS.md:5–16, 34–36`; defaults now has actual measurements and historical immediate-purge results are labelled. |
| 3 | Historical heuristic replay | Resolved: `RESULTS.md:37–39`, with historical table labels. New live heuristic execution is verified in code. |
| 4 | Logger/replay qualification | Resolved: fix and recollection at `RESULTS.md:26–28`; historical defective evidence remains explicitly qualified at `:92`. |
| 5 | Model versus TTL bucket | Resolved: `RESULTS.md:26, 90–95`; accuracy, base rate, permanent recall and exact TTL-rule match are together. |
| 6 | “No per-site headroom” | Resolved: `RESULTS.md:222–224` limits the original gate and preserves the later 8.4% RocksDB observation (`:203`). |
| 7 | Source-snippet causality | Resolved: `RESULTS.md:971–977` replaces the categorical explanation with an uncommitted-study qualification and the changed-policy confound. |
| 8 | RSS/live is not fragmentation alone | Resolved: `RESULTS.md:44–46`; workload live bytes exclude metadata and thread resources. |
| 9 | Logical class versus physical realloc placement | Resolved: `RESULTS.md:100` explicitly generalizes the in-place realloc limitation. |
| 10 | Deployment and evidence scope | Resolved: `RESULTS.md:28, 47–50` and `results/pass10/results.md:70`; warm IPC remains, sidecar CPU is excluded, full reconstruction needs uncommitted artifacts. Names-rule live symbolization versus model replay is also disclosed. |

**Independent RSS recomputation**

I selected successful output-valid repetitions 0–4, excluded cold/fill/probe/rejected/interference/diagnostic/error records, required exactly one of each repetition per variant, and checked zero decision failures/replay misses and zero warm HTTP inference in completed groups. Each cell below is the median of individual last-cycle `idle.rss_bytes`, converted to MiB. No stored summary median was used. Oracle is site-only for pure and context-pair for mixed. Capture is `(mi − policy)/(mi − oracle)`. Sources are the individual `results/pass10/<options>/<naming>/<workload>/matrix.json` files.

| Defaults, named | mi | Oracle | Static model | Hybrid | Live heuristic | Neutral rules | Matching names / TTL rule |
|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.215 | 213.996 | 216.809 | 216.809 | 286.828 | 304.812 | 216.809 |
| site-pure-16 | 296.547 | 234.801 | 239.980 | 241.918 | 305.363 | 331.914 | 239.742 |
| site-mixed-1 | 146.215 | 112.184 | 115.020 | 115.016 | 147.145 | 158.957 | 115.016 |
| site-mixed-16 | 170.527 | 138.914 | 140.070 | 140.125 | 171.238 | 180.023 | 140.070 |

Static/hybrid oracle capture, in that row order: 95.75/95.75%, 91.61/88.47%, 91.67/91.68%, 96.34/96.17%. These reproduce `RESULTS.md:11–14` and the expanded report.

| Defaults renaming / workload | mi | Oracle | Static | Hybrid | Live heuristic | Neutral | Matching rule | Static / hybrid capture |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| opaque / pure-1 | 280.219 | 213.996 | 283.121 | 304.809 | 286.883 | 304.801 | 283.121 | −4.38% / −37.13% |
| opaque / pure-16 | 296.547 | 234.859 | 298.574 | 331.879 | 307.250 | 331.934 | 298.746 | −3.29% / −57.28% |
| opaque / mixed-1 | 146.215 | 112.188 | 147.129 | 158.945 | 147.129 | 158.945 | 147.129 | −2.69% / −37.41% |
| opaque / mixed-16 | 170.527 | 138.918 | 172.117 | 178.059 | 171.129 | 178.004 | 172.000 | −5.03% / −23.83% |
| plausible / pure-1 | 280.219 | 213.996 | 283.121 | 228.746 | 286.887 | 304.809 | 283.117 | −4.38% / 77.73% |
| plausible / pure-16 | 296.547 | 234.855 | 298.770 | 267.992 | 305.125 | 332.004 | 298.465 | −3.60% / 46.29% |
| plausible / mixed-1 | 146.215 | 112.188 | 147.133 | 120.945 | 147.137 | 158.945 | 147.133 | −2.70% / 74.26% |
| plausible / mixed-16 | 170.531 | 138.914 | 172.117 | 150.066 | 171.438 | 178.055 | 172.070 | −5.02% / 64.73% |

For mixed rows, the table uses TTL as the matching rule. The separately measured names-only medians are 147.133/172.070 MiB for opaque 1/16 threads and 147.137/172.070 MiB for plausible 1/16 threads (named defaults: 147.145/172.070 MiB).

Plausible hybrid retains 81.18%, 52.27%, 80.99%, 67.31% of the corresponding named absolute saving. Opaque hybrid retains −38.78%, −64.68%, −40.80%, −24.77% (rounded); negative means worse than its own mi baseline. Static has no positive saving in any renamed block. Its opaque pure-16 median is 0.171875 MiB below the rule, but both exceed mi and their ranges overlap; this is not a useful model advantage.

The report's comparison loop (`tools/pass10_report.py:146–155`) covers **16 server blocks**, selecting names on pure and TTL on mixed. Hybrid beats that **matching semantic rule in 4/16**: only the four plausible blocks, by 54.371, 30.473, 26.188 and 22.004 MiB in the row order above. Restricted to defaults it is 4/12; restricted to renamings, 4/8. Calling this “4 of N versus the keyword rule” is imprecise: against literal `rule-names` alone it is **8/16**, because that rule also loses the four named mixed comparisons where TTL text is necessary. Use “4/16 against the matching names/TTL rule.” These are four conditions on two synthetic workload forms, not sixteen independent applications.

**Plausible-name probabilities and gate sensitivity**

I cross-checked the native probabilities in `model-decisions.jsonl.gz` against all five warm hybrid records' `allocator_stats.hybrid_sites`, not just the rounded static table. Static and hybrid agree. Probabilities are identical at 1 and 16 threads. The following tables therefore give every answered site/pair in **each** of the four plausible blocks without duplicating identical rows. All initial classes are transient. A negative margin means the prior passes the strict `P(transient) < gate` test; it does not alone cause promotion (free history and age gates still apply).

Pure-1 **and** pure-16 (`results/pass10/model-sites.md:87–96`):

| Site key / function, empty context | P(transient) | P(permanent) | P(transient) − 0.7 |
|---|---:|---:|---:|
| `3ae0a936eeeb4cfb` buf_get, main work | 0.743952783 | 0.256047217 | +0.043952783 |
| `29576832f1f5b260` resp_build | 0.738968416 | 0.261031584 | +0.038968416 |
| `fcbeb76a3434e316` conn_attach, sessions | 0.733194429 | 0.266805571 | +0.033194429 |
| `3e6e881d5301cf0a` entry_put, retained | 0.549059143 | 0.450940857 | −0.150940857 |
| `9b90b058545f9dfb` buf_get, purge pulse | 0.738635476 | 0.261364524 | +0.038635476 |

Mixed-1 **and** mixed-16 (`results/pass10/model-sites.md:67–86`; exact prior example `defaults/plausible/site-mixed-1/matrix.json:3758`):

| Pair key / function / context | P(transient) | P(permanent) | P(transient) − 0.7 |
|---|---:|---:|---:|
| `767fed8d7765c0ea` obj_new / class=a | 0.701723158 | 0.298276842 | +0.001723158 |
| `ca9d61f35663622f` buf_get / class=a | 0.746656609 | 0.253343391 | +0.046656609 |
| `6440f1cd41010eac` resp_build / class=a | 0.730113591 | 0.269886409 | +0.030113591 |
| `826d0012da961867` obj_new / class=b | 0.708230286 | 0.291769714 | +0.008230286 |
| `dbc8c9604c0250f8` buf_get / class=b | 0.758253334 | 0.241746666 | +0.058253334 |
| `f8dc05cf3b7a5cc5` resp_build / class=b | 0.761135820 | 0.238864180 | +0.061135820 |
| `0d507e64d9e0dfbe` obj_new / class=c, retained | 0.678920634 | 0.321079366 | −0.021079366 |
| `38b1bf09899871c7` buf_get / class=c | 0.740671705 | 0.259328295 | +0.040671705 |
| `c2fe34ed4c769a32` resp_build / class=c | 0.727340556 | 0.272659444 | +0.027340556 |
| `9b90b058545f9dfb` buf_get / empty, pulse | 0.738635476 | 0.261364524 | +0.038635476 |

For completeness, the mixed blocks also measure a separate **static-site** control with context disabled. Its four answered sites are `ad4b802267e0512f` obj_new: 0.640510424 / 0.359489576 (margin −0.059489576); `a2f8e6a3201aa447` buf_get: 0.743952783 / 0.256047217 (+0.043952783); `2da13f5944258421` resp_build: 0.738968416 / 0.261031584 (+0.038968416); and the same pulse key/probability above. These are identical across thread counts too. Static-site does not execute hybrid promotion; these margins are hypothetical, not additional hybrid results.

The catalogues contain seven further unasked sites in each block: keys `a3cc4795af0459d5` and `6957cfd0d57e38ee` (stdio input/output buffers), `a029e0f454dc86f2`, `25799c95ebe6a98b`, `111b8975a02c4e8b`, `049b5d2e8405ab3a` (phase-report fopen paths), and `92451a9ba7b32786` (thread-stack setup). They have **no model probability and no installed hybrid prior**, not a model answer of 0.5. Thus the pure catalogues have 12 sites, five answered; mixed has 17 pairs, ten answered.

`src/hybrid.h:7–8` and `src/live.inc:199–206` establish the mechanism: after sufficient allocation age, a no-free retained stream can be promoted only if the prior passes the gate; free evidence overrides the prior. Every plausible warm hybrid run records exactly one promotion (entry_put or obj_new/class=c) and no demotion. Neutral records two promotions and one demotion: it also temporarily promotes the session stream before the drop.

| Gate | Pure blocks | Mixed blocks |
|---|---|---|
| 0.6 | Same prior eligibility as 0.7: only entry_put passes. The useful policy distinction should survive for the same event stream. | No answered pair passes. The retained path cannot promote; the demonstrated benefit disappears at the policy level. |
| 0.7 | Only entry_put passes. | Only obj_new/class=c passes. |
| 0.8 | Every answered site passes, including conn_attach. | Every answered pair passes, including the session-like class=b. |

At 0.8 all these initially transient model priors are equivalent to neutral's 0.5 for the only probability-dependent branch. With identical sampled events, the policy follows neutral, which loses to mi and the semantic rule in these blocks. That is strong evidence the current win would not survive 0.8; it is not a measured alternate-gate RSS value. At 0.6 pure should survive, mixed should not. The “only retained pair eligible” window in mixed is approximately `(0.678921, 0.701723]`; the session-like class=b itself crosses at 0.708230. Class=a's frequent frees already provide another block on promotion. Do not turn the displayed decimal precision into a claim of calibrated probability accuracy.

**Was this tuned after looking?** There is no committed evidence of that. The 0.7 gate already exists unchanged in `7c07d56:src/hybrid.h` and in the earlier `SPEC-REAL.md:28–38`; the c1182c7 diff does not change it. The preceding spec commit `f13e0b9` already gives exactly these plausible name examples and class=a/b/c (`SPEC-REVIEW2.md:44–48`). `CODEX-REPORT.md:2293–2303` fixes the concrete mappings and rules before the first completed run at `:2358`; `:2351–2356` freezes the measured library; plausible results first appear at `:2474`. This supports a predeclared test, not an accusation of post-result threshold selection. A journal and committed inputs cannot exclude undisclosed experiments. More importantly, it remains one author/spec-selected renaming, with the original semantic program description retained; thread-count repetitions reuse the same priors. It is not an independently selected naming holdout or repeated model sampling.

**Is neutral identical except for the prior?** At the allocator-policy level, yes for these plausible blocks: both start transient, use the same admission/sampling/context keys, set `JEVALLOC_HYBRID=1`, get one first-sight answer and no sidecar recheck, and execute the same C update function. Neutral supplies 0.5 (`tools/jevd.py:107, 129–134`); model probabilities control the promotion veto. No second heuristic is secretly substituted. Across all workloads the initial class can also differ, as intended by replacing a model prior.

As a whole measured system it is not literally a single-field substitution: hybrid replays a cold response while neutral computes/logs a live deterministic response and writes its cache record (`tools/jevd.py:54–55, 107–114`); model budgeting also differs. These may change response timing and multithreaded sample order. They do not explain away the observed selective promotions, but a stricter causal control should use identical replay/transport for both and change only the supplied prior, preserving initial class for this all-transient comparison. Neutral has no model inference to measure; its current implementation is adequate to test the specified live rule policy, not to assert identical execution timing.

**Are five repetitions enough?** They support a reproducible within-fixture RSS difference, not a universal or precisely estimated effect. Here the gaps are not borderline noise:

| Plausible block | Hybrid range MiB | Matching rule range MiB | Difference of medians MiB | Smallest possible rule-minus-hybrid using observed extrema |
|---|---:|---:|---:|---:|
| pure-1 | 228.734–228.750 | 283.113–283.125 | 54.371 | 54.363 |
| pure-16 | 254.797–268.051 | 297.969–298.934 | 30.473 | 29.918 |
| mixed-1 | 120.938–120.953 | 147.133–147.133 | 26.188 | 26.180 |
| mixed-16 | 148.016–152.078 | 171.949–172.129 | 22.004 | 19.871 |

Every measured hybrid repetition beats every matching-rule repetition. The user’s “21–54 MiB” is more precisely 22.00–54.37 MiB for differences of these medians. Five runs cannot establish stability across seeds, model draws, contexts or applications, and the ranges are not confidence intervals. The deterministic rotated execution order is interleaved, not a randomized experiment. The broad pure-16 hybrid range is a reason to avoid overprecise effect estimates, not a reason to dismiss its approximately 30-MiB gap.

The most useful additional experiment is a **predeclared matched gate/prior factorial run**: freeze current binaries, inputs and recorded model outputs; compare gates 0.6/0.7/0.8, model versus neutral priors through identical transport, and the matching semantic rule. Randomize variant order in paired blocks, use enough new repetitions for a prespecified paired confidence interval, record promotion identities/times and RSS at both cycles, and repeat across workload seeds. To settle whether the probability advantage generalizes rather than merely reproduce this fixture, include independently chosen unseen name/context mappings and permutations of class=a/b/c-to-lifetime assignments, frozen before new inference. Keep the existing 0.7 result in the report regardless of the outcome. No such run was performed in this review.

**Why defaults saves about 20%, not about 85%**

This is primarily a difference in the measured placed variant, not a large change in the pure baseline: pure-1 mi is 280.215 MiB in both series, while static is 43.668 immediate versus 216.809 defaults. The same default-options oracle also retains 213.996 MiB, so a suddenly bad model is not the explanation. The immediate run returns most of the placed variant's RSS during the drop; the defaults run barely falls from its peak. Selected independently recomputed phase medians:

| pure-1 / policy / configuration | Cycle | Peak | Drop | Ordinary idle | 10-second idle |
|---|---:|---:|---:|---:|---:|
| mi / immediate | 1 | 280.215 | 280.215 | 280.215 | not measured |
| oracle / immediate | 1 | 213.109 | 41.336 | 41.344 | not measured |
| static / immediate | 1 | 215.188 | 43.660 | 43.668 | not measured |
| mi / defaults | 0 | 122.090 | 122.152 | 122.215 | 122.215 |
| oracle / defaults | 0 | 122.180 | 122.117 | 122.184 | 122.184 |
| static / defaults | 0 | 125.035 | 124.859 | 124.930 | 97.621 |
| mi / defaults | 1 | 280.215 | 280.215 | 280.215 | 280.215 |
| oracle / defaults | 1 | 214.309 | 213.996 | 213.996 | 213.996 |
| static / defaults | 1 | 217.121 | 216.809 | 216.809 | 216.809 |

All four named defaults workloads have identical ordinary/final-10-second medians for mi, oracle, static and hybrid. The cycle-zero pure-1 static/hybrid/names fall from about 124.93 to 97.621 MiB is real and must not be hidden; it shows that some release can occur during this observation interval. Other first-cycle values also differ across configurations. The phase table (`results/pass10/phases.md:121–144`) and `CODEX-REPORT.md:2382–2390` represent these facts correctly.

It is therefore unsupported to say that the headline is merely a 250-ms observation taken before defaults catches up: the final 10-second samples do not catch up. It is equally unsupported to claim the remaining RSS has been proven irreducible live-page fragmentation. The pulse is 1,024 allocate/free operations of **64 bytes** after the first wait (`fragbench/server-sim.c:116–120`); the later observation mostly waits with workers alive (`:80–85`). It is not proof that every affected size class/heap's deferred purge was serviced. Phase-report stdio also allocates, so “quiet” does not mean absolutely allocation-free.

The committed report wisely stops short of a specific allocator mechanism: `CODEX-REPORT.md:2389–2390` explicitly declines to attribute an unmeasured cause; `results/pass10/results.md:46` acknowledges that the extra first-cycle wait confounds an options-only comparison. Its empirical explanation—large release under immediate purge, substantially smaller observed benefit under the defaults protocol—is supported. A claim that defaults generally requires more than ten seconds, or that memory is permanently pinned under defaults, is not.

To distinguish reuse/layout from pending reclaim, run both option sets with identical short/long phase histories and obtain allocator active/committed/purge counters; after 10 seconds add matched ordinary allocation activity in the affected sizes/heaps, with forced collection only as a separately labelled diagnostic. A passive longer wait alone cannot settle whether an allocator needs activity to service reclaim. The present result is a 10-second observed RSS result under this workload protocol, not an asymptotic statement about defaults.

**Redis-drop arithmetic and causal strength**

Recomputed from `results/pass10/defaults/named/redis-drop/matrix.json`, each value uses five accepted runs. Final ordinary and 10-second medians agree for every row:

| Variant | Idle MiB | Target CPU seconds |
|---|---:|---:|
| mi | 274.332 | 0.331577 |
| key-only | 288.781 | 0.530761 |
| site oracle | 274.582 | 0.404758 |
| context oracle | 290.266 | 0.521352 |
| static/site | 281.422 | 0.429206 |
| static/context | 4246.531 | 28.235230 |
| hybrid/context | 4245.867 | 28.274370 |
| live heuristic/context | 4243.613 | 28.253446 |
| neutral/context | 4244.930 | 28.274957 |
| names/context | 4243.910 | 28.275530 |
| TTL/context | 4244.422 | 28.267916 |

Static/context is **4.1470 GiB**, with **85.154×** mi target CPU. Its five RSS observations are 4246.996, 4247.184, 4245.957, 4246.531, 4245.742 MiB. This is not just a peak measurement or an idle-before-purge transient.

The cause is strongly established at the mechanism/category level: switching static/site to static/context increases live entries from 629 to about 495,328; table/context alone costs only about 290 MiB; no-model live/context variants suffer the same multi-GiB cost; and the source allocates persistent, large records per pair regardless of model admission. A local layout probe compiled from the committed struct declarations gives `sizeof(LiveSite)=6016`, `sizeof(LiveShard)=1664`, or 7,680 raw bytes for a pair with one owning thread. At 495,328 entries that is **3627.891 MiB (3.543 GiB)** before allocator size-class rounding, samples and other process storage. This is an LP64 source-layout check, not a remote heap profile, but it explains the scale of the roughly 3.9-GiB incremental RSS. Bucket-chain traversal and scans of `all_shards` (`src/live.inc:187–189, 295–300, 331`) also provide plausible CPU costs as cardinality grows.

The committed compact records do **not** provide a byte-for-byte RSS attribution or CPU profile; full low-volume per-site stats are omitted by `fragbench/review2.py:63–69`. Thus “every extra byte is context metadata” or a specific CPU hotspot would exceed the evidence. The absence of a heap profile does not make the unbounded-state defect speculative. It is visible in source and independently corroborated by several no-model controls. `CODEX-REPORT.md:2612–2626` is right to call this high-cardinality state overhead rather than model inference. R3-F1 is the guard needed to make that failure bounded.

**Conclusion strength and proposed project headline**

`RESULTS.md` is now substantially well calibrated: it leads with defaults, reports the named-rule equivalence, preserves negative renaming results, limits plausible success to specific ablations, reports severe real-workload failures, and distinguishes object accuracy from saving. Retain the plausible benefit; neither the ranges nor the chronology justify erasing it or alleging tuning. Improve `RESULTS.md:22` by saying “four of sixteen server comparisons against the matching names/TTL rule,” explicitly noting that alternate gates are unmeasured, and describing the mixed result as sensitive to the promotion threshold. Make the missing regression evidence explicit and describe Redis as a boundedness defect requiring a guard, not merely an expensive configuration. Those changes would align the entry point with the committed scope.

The one-paragraph headline I would write is:

“Separating lifetimes substantially reduces idle RSS in an author-designed synthetic server: roughly 84% in the one-thread pure case with immediate purge, but 23% under the tested default-options protocol, where the reduction persists at ten seconds. Simple names/TTL rules match the model on the original fixture; opaque names remove its benefit, while one plausible renaming gives a reproducible but threshold-sensitive advantage to model probabilities combined with runtime rules. The completed real-program tests show no model reduction above 5% and include severe regressions, notably an unbounded context-state failure, so this experiment demonstrates conditional placement benefits rather than a general advantage for model-guided allocation; the requested pass-10 regression matrix and final real-workload block remain incomplete.”

Local verification: independently recomputed all 16 server blocks and the redis-drop table from run records, checked plausible probabilities against warm hybrid priors, inspected the fixed logger/recollection and committed Linux test evidence, and ran the offline `test_review2.py` (2), `test_hybrid.py` (1), and `test_stack.py` (3) tests successfully in the isolated snapshot. The latter two initially needed the snapshot's missing temporary `build` directory, then passed. No Linux performance experiments or full native allocator suite were rerun, no current working-tree source was used, and no remote connection was attempted.

REQUEST CHANGES
