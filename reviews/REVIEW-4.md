# Review 4 — commit 623bebb

Reviewed **623bebb8c14712144afa3387015f5befd5759169 as committed**, including SPEC-REVIEW3.md, the three earlier reviews, RESULTS.md through the Pass 10 boundary, all pass-11 Markdown reports, design.json, the pass-11 journal, implementation and individual run records. HEAD matched this commit and the working tree was initially clean. No source files were changed, no inference or performance experiment was launched, and the test machine was not contacted. File/line references below refer to this commit.

The guard fixes the unbounded context-state failure. The missing pass-10 measurements are now committed. All 240 factorial cell medians/ranges and all 216 paired estimates/bootstrap intervals reproduce at their printed precision. There is a real, narrowly scoped naming/gate effect, but the proposed “about as likely to cost memory as to save it” interpretation is unsupported. Changes are requested for inconsistent reporting definitions and stale completion statements, not because the measured RSS values fail to reproduce.

**Version boundary:** this commit's `RESULTS.md:1–7` contains two pass-11 paragraphs, then `# Pass 10`. It contains neither the quoted “advantage is real … about as likely” sentence nor a pass-11 summary table. I therefore review that sentence as a proposed interpretation, not as text present in 623bebb. The actual headline reports **60/72** worse-than-mi comparisons; that number is correct. Its text is also present in `tools/pass11_finish.py:48–53`. I cannot attribute or assess a different author's later table as part of this snapshot. I did check the alternative summary program added in this commit; it has a materially different definition, described next.

## Findings requiring changes

**R4-F1 — P2: the alternative summary silently changes the meaning of wins and losses.** `tools/factorial_summary.py:2–6, 15–19` reads rounded Markdown medians and labels a condition `worse-than-mi` only when `model > mi + 2` MiB. `WIN` additionally requires model to beat **all three** comparators by more than 2 MiB. Neither threshold appears in its output. The declared analysis instead uses the median of repetition-paired differences, with zero as the boundary, and defines “beat both” against rule and neutral (`CODEX-REPORT.md:2773–2782`; `tools/pass11_report.py:31–36, 48–59`). These are different estimators and different questions.

Failing scenario: plausible/site-mixed/1 at gate 0.6 has model median **147.171875 MiB**, mi **146.218750 MiB**, and paired model-minus-mi **+0.955078 MiB**, interval **[+0.949219, +0.957031]**. The helper prints `worse-than-mi 0/4` for this naming/gate, although both mixed conditions are above mi. Across the complete design it labels only **47/72** conditions worse, whereas the declared test and committed headline correctly count **60/72**. This is not a rounding dispute or evidence of equivalence in the omitted 13 cells.

Fix: make the helper consume unrounded individual records or the verified structured paired comparisons and use the declared definitions. If a practical 2 MiB threshold is useful, publish it as a separate, explicitly post hoc column labelled “more than 2 MiB above mi”; define its estimator and retain the zero-threshold count. Likewise distinguish “beats rule and neutral” from “saves more than 2 MiB against rule, neutral, and mi.” Do not use the helper's current output to create an unqualified headline table or to infer a near-even chance of saving memory.

**R4-F2 — P2: synchronize the committed completion record.** `results/pass11/README.md:1, 9–12` still says “collection running” and that validation is pending. `RESULTS.md:3` says “everything remains uncommitted”; `results/pass11/findings.md:5` says the inherited groups remain uncommitted. At 623bebb these files coexist with all accepted groups and a passing `validation.json`. A reader following the evidence index is told the completed experiment is unfinished, and a reader of the headline is told the committed evidence is unavailable in a commit.

Fix: say the requested compact measurement groups and audits are present in this snapshot; mark only genuinely remote-only traces/logs/caches as unavailable locally. Update the README's status and remove current-tense “uncommitted” assertions from the final reports. Preserve the historical journal's contemporaneous statements as history. Update `tools/pass11_finish.py:11, 51` so regeneration does not restore the false statements. Its README rewrite at `:57–59` already describes the intended complete state, but that state did not reach the committed README. No new measurement is needed for this correction.

## 1. Review-3 disposition and Redis rerun

**R3-F1: resolved for the requested live metadata bound.** Defaults are 16,384 pairs, 64 nonempty contexts per site and 128 MiB of dynamically reserved live metadata (`src/live.inc:115, 141–144`). Pair/context checks run under `live_mutex`, and the byte reservation uses an overflow-safe CAS before any site, shard or thread-index allocation (`:120–125, 329–343`). A new thread's shard for an existing pair also consumes the byte budget. Allocation failure rolls back the reservation and partial allocations (`:344–346`). Overflow sets the default class, increments attempted-allocation/byte counters and registers no pair (`:133–135, 337–338`). A default-class fallback is expressly allowed by the specification; a context-free pair is not required.

Sample records also reserve budget before allocation, and retained free-record pools remain charged (`:408–425`). There is no site eviction. Shards retain an owner reference plus sampled-object references; retirement/free releases them only when the last reference goes away (`:298–316, 425, 440–446`). Existing cached pointers are not invalidated to make room. This addresses both the pre-admission explosion and the cross-thread lifetime hazard identified in review 3.

The bound is on raw live structures, not whole-process RSS: allocator rounding, fixed arrays (1,576,960 bytes on the recorded target), and general per-thread key/stack resources are separate. This distinction is disclosed in `results/pass11/results.md:354` and should remain. It is not an unbounded replacement table hidden outside the pair limit.

`tests/test_live_limits.py:14–39, 49–69` exercises eight live workers, 8,192 contexts per worker, data verification and cross-thread frees, further allocations after overflow, and owners kept alive until process exit. The five committed cases independently exercise context, pair, byte, shared-shard/sample, and zero limits. Their peak reserved bytes are respectively **62,936; 117,288; 62,936; 65,496; 0**. The shared case reaches eight shards for two pairs and records 72,193 sample-storage overflows. The pair case reaches exactly 12 pairs; the context case reaches exactly four contexts/site. These are credible targeted tests, supplemented by the combined logger/retired-owner tests; they are not a proof for every possible concurrent execution.

The Redis patch separately collapses trailing numeric IDs before truncating the family (`patches/redis-request-context.patch:23–35`). The original patch is retained as the unnormalized control. I locally ran the numeric-family test from the actual patch and the C hybrid gate-boundary assertions; both passed. I inspected the committed Linux stress/full-suite evidence rather than claiming to have rerun Linux tests on this Mac.

Independent medians from all four Redis matrices follow. RSS is final-cycle ordinary idle MiB; CPU is target-process user+system seconds and excludes the sidecar. Each policy has five accepted repetitions.

| Context / options | mi RSS / CPU | Static/site RSS / CPU | Static/context RSS / CPU | Hybrid/context RSS / CPU | Static/context raw metadata peak MiB / pairs / overflow allocations |
|---|---:|---:|---:|---:|---:|
| Normalized / defaults | 274.496 / 0.325483 | 281.570 / 0.438502 | 281.570 / 0.442746 | 281.613 / 0.437853 | 5.596 / 636 / 0 |
| Normalized / immediate | 270.953 / 0.335195 | 278.180 / 0.434990 | 277.863 / 0.427831 | 277.844 / 0.439552 | 5.596 / 636 / 0 |
| Unnormalized / defaults | 274.848 / 0.324659 | 281.805 / 0.426222 | 283.484 / 0.569564 | 283.762 / 0.571295 | 7.776 / 961 / 494960 |
| Unnormalized / immediate | 270.684 / 0.329299 | 277.746 / 0.439195 | 279.805 / 0.603024 | 280.238 / 0.610318 | 7.776 / 961 / 494960 |

The four live no-model controls also remain bounded. In the same row order, heuristic/neutral/names/TTL RSS medians are **281.391/281.648/281.605/281.676**, **277.578/277.840/277.816/277.949**, **283.434/284.055/283.895/283.664**, and **279.387/280.082/279.844/279.941 MiB**. Their target CPU ranges across these policy medians are 0.436–0.456, 0.440–0.454, 0.574–0.585, and 0.603–0.613 seconds respectively. Key-only and both table-oracle groups are present too; no required group is missing.

For unnormalized/defaults static/context, the overflow attempts cover **220.947 MiB requested bytes** and the per-site context count reaches 64. Relative to the historical **4246.531 MiB / 28.235 s**, the recorded guarded **283.484 MiB / 0.569564 s** is a substantial fix. It is a historical before/after comparison, not a simultaneous controlled attribution of every RSS byte. None of the four new static/context or hybrid/context medians beats mi.

**R3-F2: missing evidence resolved; final record wording partly resolved.** All 25 pass-10 fragmentation matrix hashes match `results/pass10/independent-check.json`, with exact five-run accepted groups. Regression has 154 complete groups (22 workloads × seven variants), 770 accepted observations; its and validation's hashes match the inherited pass-11 check. Thus the missing RocksDB-churn group, regression, and audit are no longer missing. The overall pass-10 validation records 1,905 accepted warm observations and ten additional logged checks. The pass-10 reports now acknowledge what was pending at review 3. R4-F2 remains a publication-state inconsistency, not a demand to redo completed work.

## 2. Frozen factorial and arithmetic

The available chronology supports predeclaration. `CODEX-REPORT.md:2716–2800` specifies the complete vocabulary, five seeds, every mapping, context permutations, gates, transports, primary endpoint, bootstrap, and exact repetition-order formula before the journal reports testing/launch (`:2840–2843`), Redis, diagnostics, or factorial outcomes (`:2914–2945`). `results/pass11/design.json:2–153` contains the vocabulary/mappings; `:154` onward contains all 240 orders. Independently regenerating it gives the declared SHA256 **cd4517bb49504fa455631fad7a867e121b2117785a6dcd63b71e95ae0e6a2b54**. The first new-name collections already fingerprint this design. It is unchanged between 4b47740 and 623bebb. There is no recorded post-result selection of names, seeds, gates or measurement order.

This is supported recorded chronology, not independently timestamped preregistration: the first Git commit containing the declaration already contains some results. The journal cannot exclude undisclosed preliminary experiments. The retained plausible mapping is deliberately historical, not a sixth fresh holdout. Neither limitation justifies accusing the authors of tuning after looking.

All five mechanically generated mappings avoid explicit lifetime-stating words such as cache/temp/perm/static/global/index/table. The vocabulary includes ordinary semantic fragments such as sess, conn, req and pool, as permitted by the specification. The actual generated names are not semantically blank, and the common description still describes requests, sessions and a cache index. “No explicit lifetime labels in the generated names” is justified; “no possible semantic hint anywhere in the prompt” is not.

I checked all **90** recorded prior entries: model, neutral and rule replay envelopes agree after removing controlled probabilities and induced initial class. All rule priors here are transient with P(transient)=1; neutral uses 0.5. Every warm model site's recorded prior agrees with its frozen answer. The rule does not decode the hidden class permutation. New mappings have dedicated collections; the old plausible mapping reuses its prior answers. This is a prior-plus-initial-placement comparison, not exclusively a promotion-veto comparison: seed1 has initially permanent predictions, for example.

For each of 24 factorial matrices I required 100 valid warm runs, one repetition 0–9 per variant, correct stored order and seed, identical workload live-byte phase histories, no MIMALLOC overrides, no model HTTP work, replay misses, decision failures, metadata/sample overflow or truncated transitions. The schedules' hashes match. All 30 pass-11 matrix hashes match their zero-overlap audits and final validation; recorded warm/diagnostic target intervals do not overlap. Available source/input fingerprints match the reviewed files. Full decision logs, binaries and original traces are not all committed, so the remote validator's complete replay/trace-label reconstruction cannot be rerun locally from this compact snapshot.

I independently took final-cycle ordinary `idle.rss_bytes`, computed medians/min/max, paired model-minus-control by repetition, and generated 20,000 bootstrap resamples with Python Random seed 110011 reset for each comparison and linearly interpolated 2.5/97.5 percentiles. **All 240 RSS and promotion cells and all 216 paired estimate/interval triples match `results/pass11/results.md:11–327` at three decimals.** No stored summary median was used as input. The full per-cell RSS median audit is appended below.

Here is the summary that follows the declared estimator. Every count is out of six namings. “Above mi” means median of the ten paired model-minus-mi differences **> 0**, without a 2 MiB margin.

| Gate | Workload | Threads | Beat both, paired medians | Beat both, both interval upper bounds < 0 | Above mi |
|---|---|---:|---:|---:|---:|
| 0.6 | pure | 1 | 3 | 2 | 4 |
| 0.6 | pure | 16 | 3 | 2 | 4 |
| 0.6 | mixed | 1 | 2 | 0 | 6 |
| 0.6 | mixed | 16 | 4 | 0 | 6 |
| 0.7 | pure | 1 | 3 | 3 | 3 |
| 0.7 | pure | 16 | 3 | 3 | 3 |
| 0.7 | mixed | 1 | 2 | 1 | 5 |
| 0.7 | mixed | 16 | 3 | 1 | 5 |
| 0.8 | pure | 1 | 0 | 0 | 6 |
| 0.8 | pure | 16 | 0 | 0 | 6 |
| 0.8 | mixed | 1 | 0 | 0 | 6 |
| 0.8 | mixed | 16 | 0 | 0 | 6 |

This reproduces `results/pass11/results.md:333–344`. Above-mi totals are **20/24, 16/24, 24/24**, hence **60/72**. The all-four-condition descriptive wins are **2/6, 1/6, 0/6**; interval-supported all-four wins are **0/6, 1/6, 0/6**. The lone interval-supported all-four winner is plausible at 0.7. The 0.6 descriptive winners depend on mixed model-minus-rule differences of only −0.002/−0.008 MiB (plausible) and −0.004/−0.035 MiB (seed2), all with intervals touching or crossing zero (`:256, 259, 280, 283`). These are not evidence of a reproducible mixed-workload advantage at 0.6. The headline says “by paired median,” so its arithmetic is not false, but adding the interval-supported counts beside it would make its substantive meaning much clearer.

For comparison, a declared **>2 MiB** margin would yield 11/24, 12/24 and 24/24 losses (47/72). That is an effect-size convention, not a confidence or equivalence test. It must not replace the zero-threshold definition without being named.

## 3. What the headline can say

The first part of the proposed reading is supported: the advantage is real for particular names/gates and absent or negative elsewhere. The near-50/50 probability claim is not. Among the **five generated namings**, model is above mi in **18/20** conditions at 0.6, **16/20** at 0.7 and **20/20** at 0.8: **54/60** in total. The six savings are seed2/pure at 0.6 and 0.7 and seed4/pure at 0.7, each at both thread counts. No generated mixed naming saves memory against mi. Even at the original 0.7 gate, this is four savings and sixteen losses, not approximately half of each. Correlated thread counts and gates on five fixed mappings do not estimate a population probability for real programs.

The sentence I would write is:

> Model probabilities combined with runtime rules yield a reproducible saving for some fixed names and gates, but among the five mechanically generated namings they use more idle memory than plain mimalloc in 54 of 60 tested conditions; none beats both controls across all four workload/thread conditions with both pointwise 95% intervals below zero, so these fixtures establish neither a general advantage nor the probability of a saving on new programs.

The historical plausible naming at gate 0.7 remains a legitimate positive result. Its paired model-minus-rule differences are −54.375, −30.959, −26.184 and −22.953 MiB for pure-1, pure-16, mixed-1 and mixed-16, with every corresponding interval below zero. Ten runs quantify execution variability with frozen priors, not repeated independent model draws. The pointwise intervals are not simultaneous family-wide guarantees.

## 4. Purge diagnosis

The qualified claim in `results/pass11/diagnosis.md:3–13` is supported. Independently selected final-cycle observations from the forced diagnostic runs are:

| Defaults policy | Idle10 RSS MiB | After default-heap collection | After tagged-heap collection | Precollection area used / committed MiB |
|---|---:|---:|---:|---:|
| mi | 280.223 | 279.477 | 279.477 | 29.915 / 266.199 |
| Oracle/site | 213.012 | 187.574 | 41.273 | 29.922 / 30.075 |
| Static model | 215.102 | 111.922 | 43.504 | 30.447 / 31.333 |

All three keep **30,725,760 requested workload live bytes** throughout the intervention. Approximately 172 MiB disappears from each placed variant without workload frees. Plain mi barely changes and has about 236 MiB of unused capacity within occupied heap areas, with only 0.008 MiB in entirely empty areas. Together these support mostly deferred reclamation in the placed variants and live-page pinning as the dominant baseline heap cost in this particular experiment.

The intervention is implemented on the allocating worker after the final idle10 (`fragbench/diagnostic11.py:47–53`). Collecting only the default heap is insufficient for the placement heaps; both observations are correctly retained. Under immediate purge the corresponding before/after-all-heaps RSS values are 280.172→279.480, 41.383→41.141 and 43.582→43.246 MiB. Identical histories through intervention avoid the earlier pass-10 cross-series wait confound for this diagnostic.

What it does **not** show: an exact resident-byte decomposition; a universal default purge timeout; eventual behavior under arbitrary activity or passive waiting; a guarantee for other workloads, thread counts or allocators; or that a model is necessary to obtain the placement benefit. These are single observations with separate MI_STAT=2 libraries. Heap-area traversal is intrusive and can process delayed frees; RSS is sampled before that traversal's counters. Area committed capacity is not measured resident bytes, and it does not enumerate every mapping in the process. The negative signed committed counters in immediate placed runs are unusable as absolute accounting. The report correctly relies on unchanged workload live bytes plus the RSS intervention and occupancy evidence, rather than subtracting these counters to manufacture fragmentation.

## 5. Code and overall account after four reviews

I found no additional demonstrated pass-11 allocator or runner defect that invalidates the accepted factorial, Redis or diagnostic RSS records. The guard and runtime gate are implemented as described; model/rule/neutral transport is matched; the diagnostic is excluded from performance medians. R4-F1 is a reporting-code defect that can produce a wrong interpretation, not corrupt the underlying matrices. The Linux stress suite remains inspected committed evidence, with the two small local checks noted above.

Across the review sequence, RESULTS.md now substantially presents an honest experimental account: it distinguishes configured immediate purge from defaults, retains the names/TTL explanation, qualifies historical replayed heuristics and the logger defect, reports real-program failures and regression costs, and restricts the positive result to synthetic conditions. Review 3's remaining evidence gaps that kept review-2 F2/F3 partly resolved are now filled. Earlier results remain historical observations, not measurements of the new bounded library. The allocator is still an experiment, and completion of the requested controls does not establish deployment utility.

Before approval: correct the helper's unannounced threshold/estimator and label any derived summary accordingly (R4-F1); synchronize final committed status wording (R4-F2). If the proposed near-even-odds sentence or a later summary table is to be published, replace that sentence with the scoped empirical statement above and verify the table against the declared counts. Prefer to show the interval-supported all-four counts beside the headline's tiny descriptive wins. No further test-machine access or rerun is necessary to resolve these findings.

## Appendix: independently recomputed per-cell idle RSS medians

MiB, final-cycle ordinary idle, ten accepted runs per column. M/N/R denote model/neutral/rule; suffixes denote gates. All min/max ranges and promotion medians/ranges were also checked against the published table and matched.

| Naming | Workload / threads | mi | M .6 | N .6 | R .6 | M .7 | N .7 | R .7 | M .8 | N .8 | R .8 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plausible | pure / 1 | 280.215 | 228.781 | 304.846 | 283.164 | 228.785 | 304.848 | 283.160 | 304.846 | 304.842 | 283.162 |
| plausible | pure / 16 | 296.518 | 267.967 | 331.998 | 298.709 | 267.963 | 331.977 | 298.896 | 331.943 | 332.008 | 298.588 |
| plausible | mixed / 1 | 146.219 | 147.172 | 158.984 | 147.172 | 120.988 | 158.984 | 147.172 | 158.988 | 158.988 | 147.172 |
| plausible | mixed / 16 | 170.531 | 172.102 | 178.045 | 172.105 | 149.107 | 178.170 | 172.094 | 178.068 | 177.104 | 172.105 |
| seed1 | pure / 1 | 280.219 | 304.840 | 304.832 | 283.152 | 304.840 | 304.816 | 283.152 | 304.836 | 304.836 | 283.152 |
| seed1 | pure / 16 | 296.607 | 331.961 | 331.945 | 298.756 | 331.971 | 331.936 | 298.727 | 331.965 | 331.994 | 298.760 |
| seed1 | mixed / 1 | 146.217 | 162.922 | 158.980 | 147.170 | 162.922 | 158.984 | 147.168 | 162.918 | 158.980 | 147.168 |
| seed1 | mixed / 16 | 170.531 | 182.102 | 178.111 | 172.062 | 184.129 | 179.051 | 172.104 | 181.137 | 178.041 | 172.098 |
| seed2 | pure / 1 | 280.219 | 228.779 | 304.840 | 283.156 | 228.785 | 304.848 | 283.160 | 304.844 | 304.848 | 283.160 |
| seed2 | pure / 16 | 296.543 | 267.906 | 331.975 | 298.367 | 267.975 | 331.977 | 298.701 | 331.977 | 331.994 | 298.895 |
| seed2 | mixed / 1 | 146.219 | 147.176 | 158.990 | 147.178 | 158.988 | 158.990 | 147.180 | 158.992 | 158.992 | 147.176 |
| seed2 | mixed / 16 | 170.531 | 172.102 | 178.105 | 172.137 | 178.182 | 180.111 | 172.109 | 181.141 | 178.074 | 172.105 |
| seed3 | pure / 1 | 280.219 | 283.164 | 304.852 | 283.168 | 304.854 | 304.854 | 283.168 | 304.852 | 304.852 | 283.170 |
| seed3 | pure / 16 | 296.543 | 298.588 | 331.920 | 298.799 | 331.973 | 331.928 | 298.693 | 331.982 | 331.977 | 298.904 |
| seed3 | mixed / 1 | 146.219 | 149.180 | 158.992 | 147.182 | 158.996 | 158.992 | 147.184 | 158.992 | 158.996 | 147.184 |
| seed3 | mixed / 16 | 170.527 | 172.139 | 177.141 | 172.121 | 178.172 | 179.111 | 172.141 | 178.053 | 178.168 | 172.102 |
| seed4 | pure / 1 | 280.219 | 283.160 | 304.848 | 283.156 | 228.787 | 304.846 | 283.160 | 304.848 | 304.848 | 283.160 |
| seed4 | pure / 16 | 296.518 | 298.869 | 331.910 | 298.826 | 267.973 | 331.916 | 298.732 | 331.992 | 331.914 | 298.744 |
| seed4 | mixed / 1 | 146.219 | 147.188 | 159.000 | 147.184 | 147.186 | 158.996 | 147.184 | 158.998 | 159.000 | 147.188 |
| seed4 | mixed / 16 | 170.527 | 172.117 | 178.105 | 172.088 | 172.107 | 177.082 | 172.148 | 177.086 | 179.080 | 172.174 |
| seed5 | pure / 1 | 280.219 | 283.168 | 304.852 | 283.168 | 283.168 | 304.854 | 283.168 | 304.846 | 304.850 | 283.170 |
| seed5 | pure / 16 | 296.547 | 298.682 | 331.945 | 298.766 | 298.715 | 331.980 | 298.686 | 331.947 | 331.979 | 298.691 |
| seed5 | mixed / 1 | 146.219 | 147.184 | 158.992 | 147.180 | 147.180 | 158.996 | 147.184 | 158.992 | 158.994 | 147.178 |
| seed5 | mixed / 16 | 170.531 | 172.082 | 179.102 | 172.111 | 172.139 | 178.143 | 172.117 | 178.078 | 178.168 | 172.166 |

REQUEST CHANGES
