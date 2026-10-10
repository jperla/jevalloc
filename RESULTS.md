# jevalloc — headline results

**Status: interim (2026-10-10).** 11 of 22 workloads of the benchmark matrix are complete;
a second prompt study is in progress. Numbers below are from the Linux test machine
(Beelink SER9, Ryzen 7 255, 16 threads, 27 GB, Ubuntu 24.04-based, gcc 13.3).

**Reviewed once: verdict REQUEST CHANGES** ([reviews/REVIEW-1.md](reviews/REVIEW-1.md),
GPT-6 Astra via codex). Every number in the matrix and prompt-study tables was
recomputed and matches; the review found two implementation defects that explain the
overheads below, more defects in the controls, and that the first version of this page
overstated what the oracle result proves. This version carries those corrections. The
fixes and a rerun, plus a fragmentation benchmark, are specified in `SPEC-FRAG.md`.

## The question

Can a small typed decision model (Clef-flash), consulted **live while the program
runs**, make a better malloc? The model predicts each allocation site's lifetime class
(short / medium / long); the allocator keeps the classes in separate mimalloc heaps.
Today's model latency is set aside (decisions are recorded on a first run and replayed),
as if the model were burned into a chip. See `SPEC.md`, `SPEC-LIVE.md`.

## Headline

**Not so far. On mimalloc-bench, this implementation is slower and uses more memory than
plain mimalloc — and so is the same allocator when every site is given its true majority
lifetime class from a trace (the "oracle").** That is a negative result for this
implementation on these workloads. It is not yet evidence about the ceiling of the idea:
the implementation has defects (below) and the benchmark measures the wrong thing for
lifetime segregation.

Ratios to plain mimalloc 2.2.4 (lower is better), geometric mean over the 11 completed
workloads, median of 5 interleaved repetitions each:

| Variant | Time or inverse-throughput score | Peak RSS |
|---|---:|---:|
| glibc malloc (`sys`) | 1.24 | 0.65 |
| **plain mimalloc (`mi`)** | **1.00** | **1.00** |
| jevalloc, no site key, one heap (`jev-none`) | 1.05 | 1.26 |
| jevalloc, key + lookup, one heap (`jev-keyonly`) | 1.25 | 1.32 |
| table: oracle (true classes, same run) | 1.25 | 1.40 |
| table: random classes | 1.24 | 1.46 |
| table: class from request size only | 1.26 | 1.37 |
| live: no-model heuristic (observed lifetimes) | 2.07 | 1.08 |
| live: Clef-flash, code only (`static-model`) | 2.06 | 1.13 |
| live: Clef-flash, code + runtime state (`model`) | 2.07 | 1.10 |

Workloads included: cfrac, espresso, barnes, larson, larson-sized, xmalloc-test,
cache-scratch (1 and N threads), cache-thrash (1 and N), mstress. Reproduce the table
with `python3 tools/matrix_summary.py results/interim/matrix-11-workloads.json`.

Only warm repetitions 0–4 are counted (cold runs, where the model is really asked,
are excluded). For larson, xmalloc-test and other fixed-duration workloads the "time"
is bench.sh's inverse-throughput score, not elapsed seconds.

What the rows say:

1. **Knowing each site's true class did not help.** The oracle has the same score as the
   key-only control (ratio 1.003) and about 6% more peak RSS; random classes use 4% more
   RSS than the oracle and are no slower. The oracle is one byte-majority class per site
   taken from a separate trace run, so it is a strong control, not a mathematical upper
   bound on what any lifetime policy could do.
2. **No demonstrated advantage for the model.** Clef-flash (code only, or code plus
   runtime state) and the no-model heuristic have similar aggregates (score 2.06–2.07,
   RSS 1.08–1.13). Individual workloads differ in both directions (espresso score:
   static-model 1.39, heuristic 1.50; larson RSS: static-model 1.70, heuristic 1.45), and
   no equivalence test was run.
3. **The shim costs memory, and the cause is known.** `jev-none` should match plain
   mimalloc and does not (RSS 1.26; 2.48× on larson). Every Linux thread carries a
   ~72 KiB site cache in static TLS even when no key is computed, and larson creates
   threads it never joins, so those blocks accumulate. This does not cancel between
   variants (slower variants create fewer threads), and it is not uniform (`jev-none`
   uses 0.86× mimalloc's RSS on xmalloc-test).
4. **The controls are not clean.** Key-only and class modes allocate from explicit
   mimalloc heaps, which mimalloc creates with page reclamation disabled, while plain
   mimalloc's default heap reclaims abandoned pages. So "key-only" measures more than the
   cost of a key, and segregation is confounded with reclamation behaviour.
5. **Live mode collapses throughput in threaded workloads** (inverse-throughput score
   8.4× on larson, 12.5× on xmalloc-test; both run for a fixed time, so wall time is
   unchanged). Cause: three atomic updates on every allocation, one of them a single
   process-wide allocation clock, regardless of the 1-in-64 sampling. This is not model
   latency: warm runs spent about 0.03 s blocked on the sidecar. Live mode's lower RSS
   follows from doing less work and creating fewer threads; it is not evidence that live
   decisions save memory.

### Why this is probably the wrong benchmark

In almost every workload, nearly all bytes belong to sites of a single majority lifetime
class (each site's bytes are counted under its majority class; computed from the traces
on the test machine, which are not in this repo):

| Workload | Sites short / medium / long | Bytes short / medium / long |
|---|---|---|
| cfrac | 161 / 3 / 11 | 1.00 / 0 / 0 |
| espresso | 943 / 100 / 2 | 1.00 / 0 / 0 |
| redis | 89 / 4 / 534 | 1.00 / 0 / 0 |
| barnes | 0 / 0 / 20 | 0 / 0 / 1.00 |
| larson | 1 / 3 / 5 | 0 / 1.00 / 0 |
| mstress | 0 / 21 / 1 | 0 / 1.00 / 0 |

Lifetime segregation (as in Google's LLAMA, ASPLOS 2020, a far more elaborate allocator)
is meant for long-running servers, where long-lived objects allocated at a load peak pin
pages after the load drops. mimalloc-bench reports time and *peak* RSS of mostly short,
throughput-shaped programs. A small long-lived byte share does not prove long-lived
objects cannot pin pages, so this table is a reason to change benchmark, not a proof.
`SPEC-FRAG.md` adds one that measures memory still resident after load drops (a synthetic
server, and Redis workloads including the Mesh paper's fragmentation test).

## Allocator cost

One malloc+free pair, microbenchmark, nanoseconds (measurement records are on the test
machine, not in this repo):

| | ns |
|---|---:|
| plain mimalloc | 9.6 |
| jevalloc, no key | 13 |
| jevalloc, depth-4 site key + table lookup | 17.5 |
| jevalloc, oracle classes | 18.2 |

The depth-4 frame-pointer key alone costs 9.4 ns (the first implementation cost 67 ns, measured on a different machine, an Apple M2).

## How well does Clef-flash predict lifetimes?

**From code alone: better than chance, not by much.** 123 sites sampled across cfrac,
redis, espresso, glibc-simple, rptest and larson, scored against the oracle. Short
versus long only (the 92 non-medium sites, comparing the short and long probabilities;
a coin flip scores 50%, always answering "short" scores 60%):

| Context given to the model | Correct | Short found | Long found |
|---|---:|---:|---:|
| baseline: stack + source ±6 lines, classes defined by byte thresholds | 63% | 47% | 86% |
| classes described by meaning ("a temporary…", "stored in a global…") | 70% | 76% | 59% |
| meaning + wider code (±20 lines, 3 frames) | 73% | 76% | 68% |
| meaning + code as structured JSON | 68% | 82% | 49% |
| two yes/no questions + wider code | 72% | 73% | 70% |

- The baseline's byte-threshold wording biased it toward "long" (80 of 123 answers).
- "Medium" was found for 2 of 31 medium sites by each three-way prompt; the yes/no
  variant cannot answer medium at all.
- Redis stayed at chance (13–14 of 24). A plausible reason, not tested: its allocations
  pass through wrappers (`zmalloc`), so nearby code says little about who keeps the object.
- With the baseline prompt Clef's probabilities are often near uniform: 28 of 123 answers
  have all three within 0.10 (e.g. short 0.32 / medium 0.30 / long 0.38). With the
  meaning-based prompts that happens for 1–6 of 123.

Reproduce with `tools/promptlab.py` (raw answers: `results/interim/promptlab-round1.json`).
A second round (12-frame stacks, whole functions,
program descriptions, few-shot examples) is running.

**With live runtime state: much better.** cfrac, 175 sites, from the matrix's decision
logs on the test machine (the matrix used the baseline prompt). The reviewer could not
reach the machine, so these counts are not independently verified; and the recheck row is
187 repeated decisions over the busier sites, a different population from the first two:

| What the model saw | Correct |
|---|---:|
| code only (`static-model`) | 39% (68 / 175) |
| code only, first sight of a site in the live policy | 44% (77 / 175) |
| code + the site's observed counts and lifetimes (rechecks after 1,024 allocations) | 78% (146 / 187) |

Computed by `tools/live_accuracy.py` from the decision logs. Final answer per site: 62% (109 / 175), because many sites never allocate enough to be
rechecked. Once observed lifetimes are in the prompt, a no-model rule can read them too
— which is what the heuristic row in the matrix shows.

## Model speed

Clef-flash Q8_0 (9.4 B parameters) through llama.cpp's `/v1/systemone`, ~550-token
prompts: about 10 s per decision on the CPU, about 3 s on the Radeon 780M via Vulkan
(same choices, probabilities within ~0.02). A workload needs hundreds of decisions;
cold runs are capped at 400 per run, so on espresso (1,045 sites) most sites were never
asked and kept the default class.

## Caveats

- Interim: 11 of 22 workloads; redis, rptest, sh6bench/sh8bench and others are pending.
- The implementation defects above (TLS footprint, reclamation mismatch in the controls,
  live-mode counters) and others in the review (no in-place realloc, class separation
  not preserved when a thread exits, heap-creation failure unhandled) are not fixed yet.
- The oracle is a per-site majority class from a separate trace run of the same workload.
- One policy was tested (a heap per class). Other uses of a lifetime prediction
  (per-class purge and retention, arenas for long-lived data) were not.
- The live heuristic is an approximation of the class definitions (count-weighted, fixed
  64 MiB "long" threshold), so agreeing with it is not a precise test of the model.
- Part of the decision cache was produced on the CPU backend and part on Vulkan.
