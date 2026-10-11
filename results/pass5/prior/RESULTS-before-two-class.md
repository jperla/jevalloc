# jevalloc — pass 4 results

**Status: pass 5 fragbench matrix is running (2026-10-10).** Final native two-class Linux correctness passed all 22 workloads and live/replay/budget checks; macOS targeted tests passed. The prior acceptance and instrument measurements remain archived. All tables below are historical **three-class pass-4** evidence, not two-class results. New five-repetition tables will replace them once complete and audited.


## Fragmentation instrument

Five interleaved repetitions, median RSS at the final settled idle point. The workload
retains about 10% of each peak's objects. Identical purge settings apply to every variant:
`MIMALLOC_PURGE_DELAY=0`, `MIMALLOC_ARENA_PURGE_MULT=1`,
`MIMALLOC_PURGE_DECOMMITS=1`. The worker threads remain alive during measurement.

| Site-pure workload | Plain mimalloc | Key-only | Oracle | Oracle / mimalloc |
|---|---:|---:|---:|---:|
| 1 thread | 280.21 MiB | 280.29 MiB | 42.33 MiB | 0.151 |
| 16 threads | 296.54 MiB | 295.68 MiB | 58.59 MiB | 0.198 |

The oracle also beats key-only at the first idle point for both thread counts. This
establishes that reclaim-enabled tagged heaps can turn site separation into returned
memory on this synthetic workload. It does not establish a benefit for Clef, Redis,
or mixed-lifetime sites. Separate arenas were unnecessary for this instrument.

Raw phase observations, timing, peak RSS, options and run records:
[matching instrument matrix](results/pass4/instrument/matrix.json),
[gate and library hash](results/pass4/instrument/gate.json). These results precede
the final free-path/destructor changes and must be reproduced by the final gate.
They are instrument evidence, not the requested completed ten-variant table.

## Allocator acceptance

The static TLS site cache was removed; all none-policy entry points now use the
default heap, and key-only also uses the default heap. A previously unreported
libstdc++ dependency added roughly 1.8 MiB to C workloads; the shim no longer forces
that dependency. Live successful counters, sampled byte histograms and surviving
sample owners are sharded; the byte clock is batched, with exact trace mode retained.

The stopped acceptance attempt completed five repetitions for four workloads:

| Workload | none / mi time | none / mi peak RSS | key-only / none RSS | live heuristic / oracle time |
|---|---:|---:|---:|---:|
| cfrac | 1.021 | 1.033 | 1.004 | 2.615 |
| espresso | 1.006 | 1.002 | 1.009 | 8.705 |
| barnes | 1.004 | 1.002 | 1.000 | 1.007 |
| larson | 1.026 | 0.974 | 0.870 | 1.337 |

[Stopped acceptance records](results/pass4/attempts/acceptance-countdown.json).
The cfrac no-policy RSS gate (1.033 > 1.03) and Larson live gate (1.337 > 1.15)
failed. The attempt was stopped before all 22 workloads completed. No acceptance
claim is made from the incomplete matrix. A later compact-cache candidate completed five cfrac repetitions with none/mi time
1.023761, none/mi RSS 1.000914, and key-only/none RSS **1.033790**, still above
1.03. [Later check](results/pass4/attempts/acceptance-compare-gate-partial.json).
Later diagnostics reduced cfrac key-only RSS to 4,408 KiB versus 4,384 KiB for
none by avoiding cold general-purpose table parsing. Threaded live time remained
about 1.20 of oracle. The current full acceptance includes lighter sample locks,
count-based sampling at the unchanged 1/64 rate, and direct ELF C++ aliases.
These are candidate improvements; the full matrix determines acceptance.

## What remains unanswered

- Does oracle beat plain mimalloc on Redis and the site-mixed tier? Not measured yet.
- Does live Clef beat the no-model heuristic, and how far is each from oracle?
  Not measured on the corrected fragmentation workloads yet.
- What is the full time/peak-RSS regression across mimalloc-bench? Pending final tests
  and acceptance. Duration-limited workloads use inverse-throughput scores.

Prompt v2 is implemented: semantic class definitions, up to 12 named frames, source
from up to three ±20-line contexts, and plain-language byte-weighted sampled statistics.
The allocator key remains depth 4. v1 is selectable with its legacy cache identity;
v2 is logged and has a separate cache identity. Cold model policies retain the
400-decision budget shared with coverage fills.

The old implementation's negative interim result and original prompt-study tables are
preserved in [the run-1 report](results/interim/RESULTS-run1.md). They are historical
measurements of the defective implementation and are not substituted for final-build
results. The oracle remains one byte-majority label per site from a separate trace;
it is neither a per-object oracle nor a mathematical RSS bound.
