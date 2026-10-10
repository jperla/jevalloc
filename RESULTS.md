# jevalloc — headline results

**Status: interim (2026-10-10).** 11 of 22 workloads of the benchmark matrix are complete;
the rest are still running, and a second prompt study is in progress. Numbers below are
from the Linux test machine (Beelink SER9, Ryzen 7 255, 16 threads, 27 GB, Ubuntu
24.04-based, gcc 13.3). Nothing here has had an independent review yet.

## The question

Can a small typed decision model (Clef-flash), consulted **live while the program
runs**, make a better malloc? The model predicts each allocation site's lifetime class
(short / medium / long); the allocator keeps the classes in separate mimalloc heaps.
Today's model latency is set aside (decisions are recorded on a first run and replayed),
as if the model were burned into a chip. See `SPEC.md`, `SPEC-LIVE.md`.

## Headline

**No. On mimalloc-bench, jevalloc is slower and uses more memory than plain mimalloc —
and so does the same allocator driven by a perfect-hindsight oracle.** The limit is the
policy and these workloads, not the model.

Ratios to plain mimalloc 2.2.4 (lower is better), geometric mean over the 11 completed
workloads, median of 5 interleaved repetitions each:

| Variant | Time | Peak RSS |
|---|---:|---:|
| glibc malloc (`sys`) | 1.24 | 0.65 |
| **plain mimalloc (`mi`)** | **1.00** | **1.00** |
| jevalloc, no site key, one heap (`jev-none`) | 1.05 | 1.26 |
| jevalloc, key + lookup, one heap (`jev-keyonly`) | 1.25 | 1.32 |
| table: oracle (true classes, same run) | 1.25 | 1.40 |
| table: random classes | 1.24 | 1.46 |
| table: class from request size only | 1.26 | 1.37 |
| live: no-model heuristic (observed lifetimes) | 2.08 | 1.08 |
| live: Clef-flash, code only (`static-model`) | 2.06 | 1.13 |
| live: Clef-flash, code + runtime state (`model`) | 2.07 | 1.10 |

Workloads included: cfrac, espresso, barnes, larson, larson-sized, xmalloc-test,
cache-scratch (1 and N threads), cache-thrash (1 and N), mstress. Reproduce the table
with `python3 tools/matrix_summary.py results/interim/matrix-11-workloads.json`.

What the rows say:

1. **Perfect prediction does not help.** The oracle uses more memory than the same
   allocator with no segregation (1.40 vs 1.32) and the same time. Random classes are
   only slightly worse than the oracle (1.46). With this policy there is nothing for a
   better predictor to win.
2. **Clef-flash, the no-model heuristic and code-only Clef are indistinguishable**
   (time 2.06–2.08, RSS 1.08–1.13). The model adds nothing measurable over a rule that
   reads the observed lifetimes.
3. **The shim itself costs memory.** `jev-none` should match plain mimalloc and does not
   (RSS 1.26; 2.5× on larson). The cause is not diagnosed yet; it is a defect in the
   shim, and it inflates every jevalloc row. It does not change conclusions 1 and 2,
   which compare jevalloc variants with each other.
4. **Live mode is slow in threaded workloads** (larson 8.4×, xmalloc-test 12.5× the time
   of mimalloc). The no-model heuristic is just as slow, so this is not model latency;
   the likely cause is the lifetime sampling and shared per-site statistics (not yet
   profiled). Its lower RSS may simply follow from the slowdown, so it is not evidence
   that live decisions save memory.

### Why the oracle cannot win here

In almost every workload, nearly all allocated bytes fall in one lifetime class, so
there is nothing to separate:

| Workload | Sites short / medium / long | Bytes short / medium / long |
|---|---|---|
| cfrac | 161 / 3 / 11 | 1.00 / 0 / 0 |
| espresso | 943 / 100 / 2 | 1.00 / 0 / 0 |
| redis | 89 / 4 / 534 | 1.00 / 0 / 0 |
| barnes | 0 / 0 / 20 | 0 / 0 / 1.00 |
| larson | 1 / 3 / 5 | 0 / 1.00 / 0 |
| mstress | 0 / 21 / 1 | 0 / 1.00 / 0 |

Lifetime segregation (as in Google's LLAMA, ASPLOS 2020) pays off on long-running
servers whose heaps mix lifetimes on the same pages. mimalloc-bench is mostly short,
throughput-shaped programs.

## Allocator cost

One malloc+free pair, microbenchmark, nanoseconds:

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
versus long (92 sites; chance is 50%):

| Context given to the model | Correct | Short found | Long found |
|---|---:|---:|---:|
| baseline: stack + 6 source lines, classes defined by byte thresholds | 63% | 47% | 86% |
| classes described by meaning ("a temporary…", "stored in a global…") | 70% | 76% | 59% |
| meaning + wider code (20 lines, 3 frames) | 73% | 76% | 68% |
| meaning + structured JSON state | 68% | 82% | 49% |
| two yes/no questions + wider code | 72% | 73% | 70% |

- The baseline's byte-threshold wording biased it toward "long" (80 of 123 answers).
- "Medium" was found about 6% of the time in every variant.
- Redis stayed at chance (13–14 of 24): its allocations pass through wrappers
  (`zmalloc`), so nearby code says little about who keeps the object.
- Clef's probabilities on these prompts are often near uniform (e.g. 0.38 / 0.29 / 0.33).

Reproduce with `tools/promptlab.py` (raw answers: `results/interim/promptlab-round1.json`).
A second round (12-frame stacks, whole functions,
program descriptions, few-shot examples) is running.

**With live runtime state: much better.** cfrac, 175 sites, from the matrix's decision
logs (the matrix used the baseline prompt):

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
- The oracle is fitted and tested on the same run (an upper bound, by design).
- One policy was tested (a heap per class). Other uses of a lifetime prediction (per-class
  purge and retention, arenas for long-lived data) were not.
- The `jev-none` memory overhead (item 3) should be fixed before reading absolute RSS.
- Part of the decision cache was produced on the CPU backend and part on Vulkan.
- No independent review yet.
