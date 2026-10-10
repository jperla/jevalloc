# Review 1 — jevalloc interim experiment

Reviewed commit `2e1de18` and the requested documentation, allocator, sidecar, runner, and analysis tools. I changed no source files. Calculations below read the two committed JSON files directly, independently of their stored summary. No benchmarks or model requests were started.

During final verification, an external working-tree edit to `tools/matrix_summary.py:21` appeared, adding cold/negative-repetition filtering, and an untracked `SPEC-FRAG.md` appeared. I did not create, modify or revert either. The summary-bug finding and “committed script” columns below refer to the committed version read at the start; the external filter change addresses its primary cold-run bug, but is not part of the committed result.

The measured negative result is real for this implementation. The claim that it establishes a limit of lifetime segregation rather than the implementation is too strong. Fix the cold-run summary bug, the unconditional TLS footprint, and the live counter contention before presenting that causal conclusion. The oracle versus key-only comparison remains useful negative evidence, with qualifications below.

## 1. Numerical audit of RESULTS.md

### Matrix (lines 22–59)

For each workload and variant I computed the median of `score` and `peak_rss_bytes`, divided by the corresponding mimalloc medians, and took the geometric mean of those ratios. “Committed script” below reproduces `tools/matrix_summary.py`, including its cold-run bug. “Five warm repetitions” excludes negative repetition numbers and cold/coverage records.

| Variant | Committed script score | Committed script RSS | Five warm repetitions score | Five warm repetitions RSS |
|---|---:|---:|---:|---:|
| sys | 1.235547 | 0.652185 | 1.235547 | 0.652185 |
| mi | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| jev-none | 1.052393 | 1.263331 | 1.052393 | 1.263331 |
| jev-keyonly | 1.248397 | 1.318741 | 1.248397 | 1.318741 |
| table oracle | 1.251701 | 1.397834 | 1.251701 | 1.397834 |
| table random | 1.243399 | 1.456087 | 1.243399 | 1.456087 |
| table size | 1.258907 | 1.370849 | 1.258907 | 1.370849 |
| live heuristic | 2.074740 | 1.079168 | 2.073610 | 1.081848 |
| live static-model | 2.064224 | 1.126312 | 2.056944 | 1.127833 |
| live model | 2.072212 | 1.100531 | 2.068057 | 1.101668 |

All reported two-decimal cells are supported as rounded values except heuristic time **2.08**: direct rounding gives **2.07**, even with the buggy selection. Rounding the script's already rounded `2.075` again would explain 2.08. The statement that every cell is a median of five is false for the script's live rows.

The workload set is exactly the stated 11: cfrac, espresso, barnes, larson, larson-sized, xmalloc-test, cache-scratch1/N, cache-thrash1/N, mstress. The configuration lists 22 workloads. There are 598 `runs`: 583 for those 11 (50 measured + 3 cold per workload), plus 15 for incomplete rptest. There are 41 separate coverage-fill records. This supports the snapshot's “11 of 22 complete”; it cannot establish what is still running now.

Other comparisons:

- Oracle versus key-only: score ratio **1.002647**, RSS ratio **1.059976**. Thus “same time” is a reasonable rounded description of the aggregate, and oracle uses about **6.0% more RSS** than that control. Random RSS is **4.17% above oracle**, but random's aggregate score is slightly better, not worse. Specify that “slightly worse” means memory.
- `jev-none` larson RSS is **402,550,784 / 162,484,224 = 2.477476**, so “2.5×” is supported. The overall 1.26 is supported. It does **not** inflate every workload's ratio above one: xmalloc-test `jev-none` RSS is **0.857270×** mimalloc.
- Warm larson score ratios, heuristic/static/model: **8.431431 / 8.431801 / 8.415122**. Warm xmalloc-test: **12.494253 / 12.505747 / 12.459770**. The 8.4× and 12.5× claims are supported as **inverse-throughput scores**, not elapsed-time ratios. Wall ratios are about **1.002** and **0.996–1.001**, respectively, because these workloads run for fixed durations.
- “Indistinguishable” is stronger than these data establish. Similar geometric means do not constitute an equivalence test. For example, espresso static-model score is **1.389× mi**, heuristic **1.504×**; larson static-model RSS is **1.696× mi**, heuristic **1.454×**. Report aggregate similarity and no demonstrated model advantage, not that there is nothing measurable anywhere.
- All 168 accepted warm live records in the snapshot (including incomplete rptest) report zero `model_seconds`, zero new input tokens, zero replay misses, and zero decision errors. This supports the intended latency-free replay measurement at the level of recorded counters. It is not an independent server interference audit.

### Prompt study (lines 94–116)

The file contains **615 answers = 5 variants × 123 identical sampled sites**. Each variant has truth counts **55 short, 31 medium, 37 long**. There are **92** non-medium sites. Program sample counts are cfrac 26, redis-server 28, espresso 26, glibc-simple 16, rptest 18, larson 9.

The short-versus-long calculation compares the short and long probabilities, discarding the medium option and excluding medium truth sites (`tools/promptlab.py:266–273`). It is **not** ordinary three-class accuracy. Recomputing that calculation:

| Prompt | Correct / 92 | Short recall / 55 | Long recall / 37 | Medium recall / 31 |
|---|---:|---:|---:|---:|
| baseline | 58 = 63.04% | 26 = 47.27% | 32 = 86.49% | 2 = 6.45% |
| semantic | 64 = 69.57% | 42 = 76.36% | 22 = 59.46% | 2 = 6.45% |
| wide | 67 = 72.83% | 42 = 76.36% | 25 = 67.57% | 2 = 6.45% |
| JSON | 63 = 68.48% | 45 = 81.82% | 18 = 48.65% | 2 = 6.45% |
| two yes/no questions | 66 = 71.74% | 40 = 72.73% | 26 = 70.27% | **0 = 0%** |

Every displayed percentage in the short/long table rounds correctly. Baseline predicts long **80/123** times, as claimed. Redis short/long scores are **14, 14, 14, 13, 14 out of 24**, in the table's order, also correct. That is near a fair-coin baseline; attributing this specifically to wrappers is a plausible hypothesis, not a causal result established by the answer file.

**Wrong:** “Medium was found about 6% ... in every variant.” It is 2/31 for the four choice prompts, but 0/31 for `noul`: `tools/promptlab.py:190–193` only returns short or long. Its three-class accuracy is consequently not directly comparable as a three-way predictor. Ordinary three-class correct counts are baseline 50/123, semantic 53/123, wide 55/123, JSON 61/123, noul 66/123.

“Chance is 50%” is correct for uniform binary guessing, but the sample is not balanced between short and long: always-short scores **55/92 = 59.78%**. Include that baseline when calling code-only predictions “better than chance.”

Near-uniform probabilities exist, especially in baseline: **28/123** baseline answers have max-minus-min probability ≤0.10 (semantic 1, wide 6, JSON 2). An actual baseline short/medium/long example is **0.31605 / 0.30279 / 0.38116**. The specific **0.38 / 0.29 / 0.33** triple does not occur in that class order when rounding the committed choice probabilities to two decimals; label it illustrative or replace it with an actual record. The answer file contains probabilities and selected labels, not complete raw server responses or prompts.

Prompt sizes in the prose are imprecise: `state_text(site, 6, 2)` means **±6 lines** (up to 13 per snippet), and `(20, 3)` means **±20 lines** (up to 41 per snippet), from at most three source-bearing frames. “6 source lines” and “20 lines” should say radius/±. The JSON variant supplies structured **code context**, not observed runtime state (`promptlab.py:86–92`). The promptlab baseline is not byte-identical to the matrix prompt: `jevd.py:11–29` formats/truncates code differently, and live model additionally appends runtime state. They share the technical class definitions.

### Claims that need evidence not committed in these two files

- **Lifetime distribution table (RESULTS.md:65–74):** full site-class counts and byte shares for cfrac **161/3/11**, espresso **943/100/2**, redis **89/4/534**, barnes **0/0/20**, larson **1/3/5**, mstress **0/21/1** cannot be independently recomputed without the traces/oracle tables. Live site totals corroborate totals such as cfrac 175 and espresso 1,045, but have no truth-class labels. The prompt sample supplies only a subset of labels. Neither exact zero byte shares nor the rounded 1.00 shares are established by the committed matrix. Sum `class_bytes` over traces for actual object-byte shares; summing whole-site bytes assigned to the majority class is a different statistic and must be named as such. Small cumulative long-byte share also does not prove that long-lived resident objects cannot pin pages.
- **Microbenchmark (lines 83–92):** 9.6, 13, 17.5, 18.2 ns; isolated key 9.4 ns; earlier M2 67 ns: measurement records are absent from the committed files. They cannot be recomputed here. The 9.4 ns standalone key cost need not equal 17.5−13; these are different measurements.
- **Live accuracy (lines 119–130):** the matrix corroborates 175 cfrac sites, 175 static decisions, and 362 live-model decisions = 175 first sightings + 187 rechecks. It does **not** contain the answers/truth needed to verify numerators **68, 77, 146, 109**. Their arithmetic is consistent: **38.86%, 44.00%, 78.07%, 62.29%**. I attempted the authorized read-only SSH connection twice using BatchMode and a 10-second connect timeout; both returned `connect to host <test-machine> port 22: Operation timed out`. No remote files were read or changed, and no remote work was started. These accuracy claims remain **unverified**, not disproved.
- For that follow-up, select the exact cfrac static/model cold decision logs named in the matrix, join `request.key` to `tables/cfrac/oracle.txt`, partition by `prior is None`, and count the final answer per key. `tools/live_accuracy.py:12–20` filters `mr` only to decide whether to print a file, then scores **all response rows**, including fallbacks; distinguish policy accuracy from model-only accuracy. Its glob includes cold, warm, fills and attempts and its sliced filename output obscures provenance. Print full filenames and require matching-key coverage. The 187 rechecks are repeated decisions, not 187 independent sites; comparing them with all first sightings also changes the evaluated population.
- **Model speed (lines 133–138):** the filename Q8_0, CPU/Vulkan transition, Radeon 780M and thread settings have provenance assertions in `backend_transition`. **9.4 B parameters, ~550 tokens, ~10 s CPU, ~3 s Vulkan, identical choices and probability difference ~0.02** cannot be independently recomputed from the committed answer file (all its `seconds` values are zero) or matrix aggregates. Paired responses/token/latency logs and model metadata are needed.
- **Budget and espresso coverage are supported:** max-model-decisions is 400 in the configuration and enforced by `jevd.py:61–71, 93–116`. Espresso has 1,045 sites; static asks 400, leaves 645 unasked (**61.72%**), live model asks 330 distinct sites, leaves 715 unasked (**68.42%**) because rechecks consume slots. Their unasked byte shares are **33.58% / 66.10%**. Thus “most sites never asked” is correct, but “most bytes” would not hold for both. The budget includes cache hits and is shared with coverage fills, not simply 400 fresh inferences per cold run.
- **Host/status assertions (lines 3–6, 115–117, 140–145):** JSON establishes Linux x86-64/glibc 2.39 and configured processor count 16. It does not independently establish Beelink model, CPU SKU, installed 27 GB, distro identity, gcc 13.3, second study progress, or prior review history. One heap-segregation policy and no retention/purge experiment are consistent with the inspected code. Mixed CPU/Vulkan cache provenance is recorded. These are provenance/status statements, not recomputable performance results.
- The LLAMA reference (Google, ASPLOS 2020) and its long-lived server fragmentation motivation are supported by the [authors' publication page](https://research.google/pubs/learning-based-memory-allocation-for-c-server-workloads/). It describes a more elaborate lifetime/huge-page allocator; it does not establish that this three-heap implementation must help, or cannot help, these benchmarks.

## 2. Run selection and scoring

**P1 — cold runs enter the advertised medians.** `tools/matrix_summary.py:20–22` filters only `exit_status == 0`. Each completed live variant therefore has **six**, not five, observations; lines 31–34 take the median of all six. Example: espresso static cold wall time is **1,806.41 s**, model cold **1,258.27 s**. A six-value median is generally shifted even when the cold value is an outlier. The small resulting aggregate change does not make the selection correct.

Fix: explicitly require nonnegative repetition, exclude `cold`, `coverage_fill`, `coverage_probe` and rejected/interference records, validate output/decision success, and require exactly one accepted record for each repetition 0–4. Do not silently count duplicates as extra repetitions. Compute the eligible workload intersection once and use it for every variant and metric.

**The other requested checks pass for this snapshot:**

- `bench/run.py:180–195` excludes cold runs. Its stored score, wall, CPU and RSS medians independently match recomputation for all 120 stored groups, including incomplete rptest groups.
- Coverage runs are stored separately (`run.py:211–219, 279–286`); rejected replay probes are appended there rather than accepted `runs`. There are no duplicate `(benchmark, variant, repetition)` tuples, no accepted `attempt` filenames, and no retry attempts mixed into these medians. The compact script is still insufficiently defensive against future malformed/combined inputs.
- The shared completeness check at `matrix_summary.py:27–29` applies all ten variants to each workload. Consequently **the same 11 workloads** enter every geometric mean. Incomplete rptest is excluded. Because cold runs count toward five, a future workload with four warm live runs plus one cold could be prematurely included; require the exact warm repetition set.
- Throughput orientation is correct (`run.py:41–54`). Larson reports `1e9 / operations_per_second` (`third_party/mimalloc-bench/bench/larson/larson.cpp:565–567`); xmalloc reports `100 / million_frees_per_second` (`.../xmalloc-test.c:221–223`). Lower is better, so variant/mi is correct, not inverted. Rptest, glibc-thread and Redis are explicitly inverted too. Rename the headline column to “time / inverse-throughput score” and avoid interpreting larson/xmalloc ratios as elapsed time.
- Rotating variant order per repetition (`run.py:275–278`) implements interleaving. It is not randomized. Raw stdout files and an inference-interference audit are not committed here, so their contents/absence of external interference cannot be independently checked.

## 3. Cause of the no-key RSS overhead

**P1 — the supposedly disabled site cache still occupies static TLS in every Linux thread.** `src/jevalloc.c:24–29` embeds `keys[256]`, including 16 frames per entry, in an `initial-exec` TLS `Thread`. On the measured 64-bit ABI: `sizeof(Frame)=16`, `sizeof(KeyCache)=288`, and `sizeof(Thread)=73,784` bytes (about **72 KiB per thread**). Linux/glibc allocates and initializes static TLS when creating a thread regardless of `JEVALLOC_POLICY`; skipping `capture()` does not remove it.

This is especially damaging on larson: `_beginthread` creates joinable pthreads and discards their handles (`larson.cpp:86–99`); workers repeatedly create successors (`:655–668`) without a join/detach. Exited thread stack/TLS allocations accumulate. Thousands of those 72 KiB TLS blocks can account for hundreds of MB. This explains a concrete large RSS mechanism even though `jev_malloc`, `jev_calloc`, `jev_realloc` and C++'s `jev_malloc_aligned` **already bypass directly to mimalloc** in none mode (`jevalloc.c:176–181`). Blaming an unconditional `mi_heap_new()` in the ordinary none malloc path would be incorrect.

Fix: keep only a small recursion guard/pointer in static TLS. Lazily allocate the large key/frame cache with raw mimalloc when capture is actually needed; never allocate it in no-key mode. Reclaim it with a thread-exit destructor that safely coordinates with mimalloc lifetime and cannot recurse into shim initialization. Retain a small loader-safe bootstrap path. Use a thread-churn control and RSS/TLS measurements to validate. Do not change the benchmark merely to hide the overhead; a separately labeled detached/joined control can isolate its interaction.

This is a source-level diagnosis, not a measured attribution of every byte of the **1.263331** geometric mean. Other costs below exist; proving the entire ratio disappears requires a corrected build and rerun. The claim that the overhead cancels between all jevalloc variants is unsafe: larson creates different numbers of threads when variants have different throughput.

**P2 — “one heap” controls are also inconsistent.** The none bypass omits `jev_aligned_alloc`, `jev_posix_memalign`, `jev_valloc`, `jev_pvalloc`, `jev_memalign` (`jevalloc.c:182–186`). These enter `allocate()` and create `heaps[0]`, while ordinary malloc uses mimalloc's default heap. A program mixing malloc and posix_memalign in none mode therefore uses **two heaps**. Add equivalent validated no-policy fast paths for every allocation entry point, or centralize the bypass in `allocate()`.

**P1 — explicit heaps change reclamation, not just classification.** Key-only and class modes create heaps using `mi_heap_new()` (`jevalloc.c:172`). In mimalloc 2.2.4, `heap.c:253–255` explicitly creates these with `no_reclaim=true`; the default backing heap can reclaim abandoned pages. Thread-churning workloads therefore compare different reclamation behavior as well as key cost. Key-only is not a pure “key + lookup” overhead control.

Fix the key-only control to capture/look up then allocate on the default heap. For the segregation experiment, evaluate reclamation-enabled, class-tagged heaps via the available `mi_heap_new_ex(tag, false, arena)` API, with consistent handling of all class tags during cross-thread reclamation. Keep a matched one-explicit-heap control as an additional policy baseline so the original comparison remains interpretable. This needs validation rather than simply enabling reclaim for three tag-zero heaps.

Do **not** diagnose a general leak of undeleted mimalloc heaps from the absence of a jevalloc destructor: mimalloc already deletes each thread's non-backing heaps in `third_party/mimalloc/src/init.c:421–429`.

## 4. Cause of live throughput collapse

**P1 — the 1/64 sample rate does not sample the contended fast-path updates.** Every successful entry into `live_before()` executes **three atomic read-modify-writes** (`src/live.inc:110`): `s->allocs`, `s->bytes`, and the process-wide `live_clock`. The latter is one globally contended cache line even when sites differ. Larson and xmalloc also concentrate allocation traffic on a few shared sites. Relaxed atomics still require exclusive cache-line ownership on each update; changing memory order does not remove cache-line bouncing. `src/jevalloc.c:171` calls this for every live allocation, including all warm replays.

Additional traffic comes from global sampling counters, site histograms, sample-bucket counters and shard locks (`live.inc:129–140`). Every free hashes/probes the sampled-pointer table (`jevalloc.c:178`, `live.inc:135–137`), even if its allocation was unsampled. New threads/cache misses also take `live_mutex` to attach to a site (`:103–108`). These costs remain after replay has eliminated model inference. This is a concrete serialization mechanism, not merely “model latency” or an unexplained sampling cost.

Recorded blocking corroborates it is not mostly socket waiting: warm larson heuristic median wall **7.0626 s**, summed blocked **0.0340 s**, 19 decisions; xmalloc heuristic **5.0100 s**, blocked **0.0284 s**, 14 decisions. Static-model, which never rechecks, still pays the same per-allocation counters and collapses similarly. A profile/controlled ablation is needed to partition the slowdown among counter contention, lookup, locks and thread overhead; none was run on the busy test host.

Fix: shard site statistics by thread, use local counters and merge/batch them for decisions and exit reporting, and stop modifying a single global allocation clock on every allocation. For live mode explicitly accept/document a batched or sampled approximate byte clock; keep the exact clock in trace mode. Use padded independent shards and reusable sampled-record pools. Preserve cross-thread frees by attaching a lifetime-safe shard/site owner to sampled records, and preserve the one-in-flight decision protocol and well-defined recheck thresholds when aggregating. Padding alone does not fix a truly shared counter. With a replay-only path, omit runtime statistics that cannot affect the already recorded answer schedule, but report that separately from an optimized true-live implementation.

Fixed-duration programs do less work and larson creates fewer retained threads under this slowdown. Lower live RSS is therefore confounded by both work volume and TLS accumulation. It cannot establish that live predictions reduce fragmentation.

## 5. What the oracle result does and does not show

Supported: **this implementation, these 11 completed configurations, and these recorded schedules** do not beat mimalloc in aggregate; oracle class routing has essentially equal score and worse RSS than the existing key-only explicit-heap control. The live-only atomic defect cannot explain the table-oracle result, since that path never runs `live_before()`. Merely subtracting a common fixed shim cost would not turn an oracle loss to a matched control into a policy win. These are substantial reasons to remain skeptical of this particular policy.

Not established: “perfect-hindsight oracle,” “with this policy there is nothing for a better predictor to win,” or a demonstrated causal ceiling independent of implementation. `tools/common.py:10–12` chooses **one byte-majority class per site from a prior trace execution**. That is neither a perfect per-object classifier nor an optimizer of RSS or throughput, and the timed execution is a different run. The README correctly rejects a mathematical performance-upper-bound interpretation; RESULTS.md and the older spec should match it. Runtime phase adaptation can also do something a fixed majority label cannot.

For the stronger conclusion to be wrong **on these same workloads**, a benefit must be hidden by a non-cancelling implementation effect (for example, segregation-specific reclamation/heap lifecycle behavior or a different thread-churn/TLS interaction), or the majority-site oracle must fail to bound useful assignments/dynamic decisions. Corrected, matched measurements would then need to show oracle or another legitimate class decision policy improves the relevant score/RSS tradeoff. Fixing only the live counters may change the model/heuristic comparison, but does not by itself overturn the table control. A result on new, longer-lived workloads would limit generalization rather than falsify the narrow 11-workload observation.

Required evidence: rerun the same warm, interleaved comparison after reducing TLS overhead and matching heap/reclamation behavior; report oracle versus both corrected key-only and mimalloc, with per-workload uncertainty and work-normalized memory comparisons. Verify table-key coverage and trace byte distributions. Separately rerun optimized live policies with equal instrumentation and clearly identified replay/first-run accuracy populations.

## 6. Additional allocator correctness and measurement findings

**P1 — heap-creation failure is not handled.** `src/jevalloc.c:172–173` immediately passes the result of `mi_heap_new()` to heap allocation functions. Under memory pressure it can return NULL (`third_party/mimalloc/src/heap.c:240–243`), which is not a valid heap argument. Scenario: first allocation in a new class/thread cannot allocate heap metadata. Fix: check the heap result, unwind `busy`, set `errno=ENOMEM`, and return NULL; C++ new can then invoke its handler. Add fault-injected coverage for malloc/calloc/aligned entry points and realloc preserving its old pointer on failure.

**P2 — failed live allocations contaminate supposedly actual totals and decision history.** `live.inc:110` increments allocs/bytes/clock before `jevalloc.c:173` knows allocation success; `:174` only checks success for sampled pointer insertion. A large failed allocation can inflate `site_bytes`, advance lifetime buckets for other objects, and trigger later rechecks despite contributing no allocated object. This conflicts with using exit totals as actual allocated-byte coverage. Fix: distinguish attempts from successful allocation counts/bytes, update successful byte statistics only after obtaining a pointer, and define recheck scheduling against the chosen counter. A rollback of a globally observed clock is not a sound concurrent fix. If attempted bytes are intentional, rename them and keep separate successful-byte coverage.

**P2 — live heuristic statistics do not implement the stated truth definition.** `live.inc:139` adds one per sampled free to a histogram; the oracle is byte weighted, and never-freed samples do not enter that histogram. `tools/jevd.py:104–110` declares long at a fixed **64 MiB**, not “over half the final allocation volume or never freed.” A site mixing many tiny short objects with a few large retained objects can have opposite count-majority and byte-majority classes. A live heuristic cannot know the final volume exactly, but should be named as an approximation and expose sampled byte weights plus survival information. This weakens treating agreement with the heuristic as a precise test of model usefulness; it is not a thread-safety defect.

**P2 — realloc adds policy-independent copying and peak-memory costs.** Outside none mode, `src/jevalloc.c:180` always performs malloc/copy/free, including modest shrink/same-size operations. Mimalloc has an in-place path for sizes between half and all of usable size (`alloc.c:257–267`). Repeated resizing therefore creates avoidable traffic and simultaneous old/new storage in the tested allocator and changes the traced lifetime stream. Fix: preserve a suitable in-place path or use the selected heap's realloc API with explicit trace/live resize bookkeeping. Keep old contents/pointer on allocation failure. This is a performance/measurement defect, not proof of invalid realloc semantics: the current implementation may legally move, and generic realloc need not preserve extended alignment. Its zero-size non-NULL convention also follows mimalloc; do not label that alone a bug.

**P2 — heap tags do not preserve class separation through ownership changes.** All `mi_heap_new()` calls use tag zero. At thread teardown, mimalloc absorbs compatible heaps into the backing heap (`heap.c:473–487`); reclamation chooses a target by page tag (`segment.c:1237–1244`). Class identity therefore is not durable through abandonment/reclamation. With cross-thread surviving objects, the README/spec's unconditional “different classes never share a page” is not guaranteed, especially with default-heap internal allocations. Preserve class tags through lifecycle transitions and ensure receiving threads have the appropriate heaps; validate with a thread exiting while another retains/frees its objects.

**P2 — newly loaded Linux images are absent from site normalization.** `src/jevalloc.c:160` enumerates ELF images only at initialization; `capture():109–114` silently ignores unmatched addresses. Allocations from a subsequently `dlopen`ed plugin can lose the distinguishing frames and collapse onto a caller/empty key, causing incorrect table/live classification. The README excludes unloading/reuse, but not ordinary loading. Add loader-safe image registration and cache invalidation, or explicitly restrict supported programs to the startup image set. The raw-stack cache (`:97–104`) also treats a 64-bit hash match as exact stack identity; store/check frame count and PCs if collision-free cache identity is required. No collision was demonstrated in these data.

**Trace audit:** the ordinary trace allocation/free maps are mutex protected (`src/trace.inc:24–45`), including cross-thread frees. The candidate pruning at lines 19–22 and 39–42 is sound: once a lifetime is ≤ half the current monotonic allocation clock it cannot become long under a larger final clock; final pruning applies long precedence, and never-freed bytes are added at exit. I found no demonstrated off-by-one defect in the `<1 MiB` / `>half total` classification, no unsynchronized normal pointer-table lookup, and no evidence supporting an allegation of leaked class heaps at normal thread exit. The static lookup table is built at under 50% occupancy and handles ordinary hash collisions by probing (`jevalloc.c:123–134`).

There are nevertheless scope gaps: `jev_realpath` aliases raw `mi_realpath` (`src/jevalloc.h:31`, used by the macOS interposition path), so its returned allocation bypasses classification/trace statistics. Route that result through a shim allocation or explicitly exclude it. Bootstrap/internal and post-exit-snapshot work are already explicitly excluded in README and should not be reported as new defects. `live_finish()` takes the site-list mutex but other threads may continue atomic counter updates, so its totals are an approximate snapshot, unlike the closed mutex-serialized trace snapshot.

## Recompute the principal tables without running experiments

```python
import collections, json, math, statistics as st
D = json.load(open('results/interim/matrix-11-workloads.json'))
V = D['configuration']['variants']
g = collections.defaultdict(list)
for r in D['runs']:
    if (r['exit_status'] == 0 and r['output_ok']
        and r['repetition'] >= 0
        and not any(r.get(k) for k in ('cold', 'coverage_fill', 'coverage_probe'))):
        g[r['benchmark'], r['variant']].append(r)
B = [b for b in D['configuration']['workloads']
     if all(len(g[b, v]) == 5 and
            {r['repetition'] for r in g[b, v]} == set(range(5)) for v in V)]
for v in V:
    print(v, *[math.exp(st.mean(math.log(
        st.median(r[k] for r in g[b, v]) /
        st.median(r[k] for r in g[b, 'mi'])) for b in B))
        for k in ('score', 'peak_rss_bytes')])
P = json.load(open('results/interim/promptlab-round1.json'))
for v in dict.fromkeys(r['variant'] for r in P):
    rows = [r for r in P if r['variant'] == v]
    pairs = [(r['truth'], 'short' if
              r['probs'].get('short', r['probs'].get('temporary', 0)) >=
              r['probs'].get('long', r['probs'].get('retained', 0)) else 'long')
             for r in rows if r['truth'] != 'medium']
    print(v, sum(t == p for t, p in pairs), len(pairs),
          [(c, sum(t == p for t, p in pairs if t == c),
            sum(t == c for t, p in pairs)) for c in ('short', 'long')],
          'medium', sum(r['truth'] == r['pred'] == 'medium' for r in rows))
```

Remote accuracy, microbenchmark calibration, full trace distributions and paired CPU/Vulkan claims remain evidence gaps. The verified arithmetic and negative observed aggregate result should be retained, with the bugs and causal limitations made explicit.

REQUEST CHANGES
