# jevalloc — spec v0

An experiment, not a product: **does a typed decision model (Jev / Clef class) that
predicts object lifetime per allocation site make a better malloc?** We assume the model
is "burned into a chip": inference latency is treated as zero, so the model's answers are
precomputed offline into a table and looked up at run time. What we measure is whether
the *decisions* help, on the mimalloc-bench workloads, against plain mimalloc.

Platform for v0: macOS arm64 (Apple M2, 8 GB RAM, 8 cores), clang, cmake. Keep the code
portable to Linux where it is cheap to do so, but only macOS has to work now.

## Layout (repo root = this directory)

    third_party/mimalloc         mimalloc v2.2.4 checkout (already present; do not edit in place —
                                 if a patch is unavoidable, keep it as patches/*.patch applied by the build)
    third_party/mimalloc-bench   benchmark suite checkout (already present; programs already
                                 build with: cmake third_party/mimalloc-bench/bench, see out/bench there)
    src/                         the allocator (C11)
    tools/                       python3 (stdlib only) offline tools
    bench/                       benchmark runner + definitions
    tests/                       correctness tests
    results/                     committed result files (json + markdown)
    CMakeLists.txt, Makefile (thin convenience wrapper), README.md, LICENSE (MIT, "Joseph Perla")

## The allocator: libjevalloc.dylib

A drop-in malloc replacement loaded with `DYLD_INSERT_LIBRARIES`, built on mimalloc's
allocation machinery (static, linked in). It must correctly replace
malloc/calloc/realloc/free/posix_memalign/aligned_alloc/valloc/malloc_size and C++
operator new/delete (all the forms mimalloc's own override covers) for every benchmark
program below. Reusing or adapting mimalloc's own macOS override path (zone + interpose)
is fine and probably the most robust route; choose whatever works and say why.

**Site key.** On every allocation entry point, compute a 64-bit site key from the
calling context: walk up to `K` return addresses via the frame-pointer chain (arm64
always keeps x29; K default 4, env `JEVALLOC_DEPTH`), normalise each address so the key
is stable across runs of the same binary (subtract the owning image's ASLR slide, or an
equivalent scheme), and hash. The walk must be safe (bounded, stays inside the thread's
stack) and cheap. Document the measured cost.

**Lifetime classes.** Three: `0 = short`, `1 = medium`, `2 = long`.

- short: the object is typically freed before the program allocates another 1 MiB.
- long: the object typically lives until exit, or for more than half of the program's
  total allocation volume.
- medium: everything else.

"Time" is the allocation clock: cumulative bytes requested by the whole process.

**Policy.** Each thread has one mimalloc heap per class; an allocation goes to the heap
of its site's class, so objects of different predicted lifetime never share a mimalloc
page. `free` works on any pointer. Unknown site → class from `JEVALLOC_DEFAULT`
(default medium). This is the one place where a better idea is welcome: if you see a
policy that uses the class more profitably (e.g. different purge/retention per class),
implement it behind an env switch and keep the plain segregation policy as the baseline.

**Modes** (env `JEVALLOC_MODE`):

- `run` (default): load the table at `JEVALLOC_TABLE` (text: `<hex key> <class>` per line)
  into a read-only open-addressing hash table at init; per allocation = key + lookup.
  No table → every site gets the default class.
- `trace`: record, per site, the frames (normalised addresses + image path), allocation
  count, bytes, a histogram of lifetimes on the allocation clock (log2 buckets), and the
  count never freed. Written at exit to `JEVALLOC_TRACE_OUT` (JSON lines). Must work for
  multi-threaded programs (larson, xmalloc-test, mstress, rptest free on other threads).
  Speed in this mode does not matter; correctness of the statistics does.
- `JEVALLOC_POLICY=none`: skip the key entirely and use one heap (measures pure shim cost;
  should be within noise of plain mimalloc).
- `JEVALLOC_POLICY=keyonly`: compute key + lookup but send everything to one heap
  (separates lookup cost from segregation effect).

## Offline tools

- `tools/symbolize.py trace.jsonl` → adds, per frame, function name and file:line (use
  `atos`; the benchmark programs must therefore be built with `-g`, same optimisation
  level as mimalloc-bench uses) and the surrounding source lines (±12) for frames that
  resolve into the benchmark's own source.
- `tools/oracle.py trace.jsonl -o table.txt` → the class each site *should* get by the
  definitions above (majority by bytes). This is the upper bound: fit and tested on the
  same run, and labelled as such everywhere.
- `tools/label.py sites.jsonl --model <id> -o table.txt` → ask a decision model, one
  request per site, through the TrustedRouter decide route:

      POST {TR_BASE_URL or https://api.trustedrouter.com}/v1/decide
      Authorization: Bearer $TRUSTEDROUTER_API_KEY
      {"model": "...", "state": "<text>", "questions": {"lifetime": {"type": "choice",
        "instructions": "...", "criteria": {"short": "...", "medium": "...", "long": "..."}}}}
      → {"answers": {"lifetime": {"choice": "short", "probabilities": {...}}}, "usage": {...}}

  The state shown to the model contains ONLY what a compiler/loader would have before
  the program runs: program name, the symbolised call stack, the source snippets, and
  the requested size if it is a compile-time constant in the snippet. NO runtime
  statistics from the trace (no counts, no lifetimes). Cache responses on disk keyed by
  (model, request hash); write the raw responses next to the table; print accuracy and a
  confusion matrix against the oracle. Optional `--reasoning` passes `"reasoning": true`.
  A 502 with header `x-should-retry: false` is already billed: do not retry it.
- `tools/baselines.py` → tables for controls: `random` (seeded), `all-short`, `all-long`,
  and `size` (class from the site's typical request size only — the "no model needed"
  heuristic; pick thresholds without looking at lifetimes).

## Benchmark runner

`bench/run.py` — runs a matrix of (benchmark × allocator variant × repetition) and writes
`results/<name>.json` plus a markdown summary. Per run record wall time, user+sys time
and peak RSS (`/usr/bin/time -l` on macOS gives "maximum resident set size" and "peak
memory footprint"; record both). Interleave variants within each repetition (never all
reps of one variant in a row), default 5 reps, report median and min/max, and report
each variant relative to plain mimalloc.

Benchmarks: take the command lines and inputs from `third_party/mimalloc-bench/bench.sh`
for every test that builds on macOS from `bench/CMakeLists.txt`: cfrac, espresso, barnes,
larson (and larson-sized), xmalloc-test, cache-scratch, cache-thrash, mstress, rptest,
glibc-simple, glibc-thread, alloc-test, malloc-large, mleak. Use the same arguments
bench.sh uses, with its processor-count logic for this 8-core machine. If redis from
`build-bench-env.sh` can be built offline it would be the most interesting workload, but
it is a stretch goal — do not let it block.

Allocator variants: `sys` (macOS malloc), `mi` (plain mimalloc 2.2.4 dylib built from the
same checkout with the same flags, its own override), `jev-none`, `jev-keyonly`,
`jev-oracle`, `jev-random`, `jev-size`, and `jev-model:<table>` for any table file.

## Correctness tests

`make test` must: run every benchmark program above under libjevalloc in `run` mode with
a random table and in `trace` mode and check exit status + expected output where the
suite has one; run a small stress test (multi-threaded malloc/realloc/free with
cross-thread frees, aligned allocs, C++ new/delete, strdup, zero-size and huge sizes)
under the dylib; and unit-test that the site key is identical across two runs of the same
binary and differs between two call sites.

## Deliverables for this pass

1. Everything above, building with `make` from a clean checkout.
2. `make test` green.
3. A first real result: traces + oracle + baseline tables for every benchmark, then
   `bench/run.py` over all benchmarks with variants sys, mi, jev-none, jev-keyonly,
   jev-oracle, jev-random, jev-size (3 reps is enough for this first pass), committed
   under `results/`. Do NOT run tools/label.py — no API key is available to you.
4. `CODEX-REPORT.md`: what you built, the interposition approach and why, measured
   per-allocation cost of the key walk, anything that does not work, anything you could
   not verify, and the result table with an honest reading of it (including if the
   oracle loses to plain mimalloc).

Constraints: do not run git commands that write (the sandbox cannot); leave the tree
uncommitted. Do not touch anything outside this directory. Do not install system
packages. The machine has 8 GB of RAM: run benchmarks one at a time.
