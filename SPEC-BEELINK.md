# jevalloc — pass 2: Linux is the primary platform; live Clef-flash; run on the Beelink

State of the tree: pass 1 (SPEC.md) was implemented on macOS — allocator, trace mode,
tools, runner, tests; `make test` was green on macOS. The macOS benchmark pass was
stopped on purpose (results/first-pass.* are partial and from a noisy machine: treat
them as scratch, do not publish them). There is no CODEX-REPORT.md yet.

## Where things run now

Everything is measured on a Linux box ("the Beelink"), reachable from your sandbox:

    ssh -o BatchMode=yes "$JEVALLOC_REMOTE"        # user@host of the test machine

Beelink SER9, AMD Ryzen 7 255 (8 cores / 16 threads, AVX-512), 27 GB RAM, Ubuntu
24.04-based, gcc 13.3, python 3.12, passwordless sudo exists but DO NOT use it and do
not install system packages (cmake and ninja are in ~/jevalloc/venv/bin; add that to
PATH). Work only inside `~/jevalloc/` there. The machine is otherwise idle; it also runs
a VM and a desktop — leave them alone.

You edit here (macOS checkout, the source of truth), sync with rsync over ssh to
`~/jevalloc/src-tree/` on the Beelink (exclude build/, .venv-clef/, .git/), and build,
test and benchmark there. Put that loop in `scripts/beelink.sh` (sync / build / test /
bench / fetch-results subcommands). Long benchmark runs: start them with nohup on the
Beelink and poll, so an ssh drop does not kill them. Fetch results back into results/.

## 1. Linux port (primary target: x86_64, glibc, gcc)

- `libjevalloc.so` via `LD_PRELOAD`, same semantics as the dylib. Keep macOS building
  and its tests passing, but Linux is what gets benchmarked.
- Frame-pointer walk on x86_64: Ubuntu 24.04 builds its packages with frame pointers;
  build the benchmark programs and mimalloc with `-fno-omit-frame-pointer`. The walk
  must stay safe when a frame has no frame pointer (bounds + alignment checks as now).
- Build the whole mimalloc-bench program set that builds on Linux without system
  package installs, with the arguments bench.sh uses on a 16-thread machine: at least
  cfrac, espresso, barnes, larson/larson-sized, xmalloc-test, cache-scratch,
  cache-thrash, mstress, rptest, glibc-simple, glibc-thread, alloc-test, malloc-large,
  mleak, sh6bench/sh8bench if their sources can be fetched, and **redis** (the most
  lifetime-interesting workload: build it the way build-bench-env.sh does, run it the way
  bench.sh does with redis-benchmark). rocksdb/lean/lua/gs only if cheap.

## 2. Make the key cheap

Pass 1 measured ~67 ns per allocation for a depth-4 key (vs ~9 ns depth 1), which doubles
cfrac's run time. Causes visible in src/jevalloc.c: a linear scan of every loaded image
for every frame, and four pthread_getspecific calls per allocation. Fix: real TLS
(`__thread`/initial-exec) for the per-thread context, and no per-frame image search on
the fast path (e.g. hash raw return addresses and resolve image+offset only on a table
miss, with a small per-thread cache raw-key → site entry; ASLR means the raw key differs
between runs, so the stable key is computed once per new raw key). Target: depth-4 key +
lookup under 10 ns on the Beelink; report what you get.

## 3. Live mode — implement SPEC-LIVE.md

Read SPEC-LIVE.md; implement all of it. The decision model is **Clef-flash, served
locally on the Beelink** by llama.cpp (support merged upstream 2026-10-03, PR #29831):

    ~/jevalloc/llama.cpp/build/bin/llama-server      (already built, CPU)
    ~/jevalloc/models/Clef-Flash-Q8_0.gguf           (9.66 GB; may still be downloading —
                                                      ~/jevalloc/setup.out ends with SETUP_DONE)

Start it yourself bound to 127.0.0.1:8765 and find the right invocation and request
shape (the model card says "use via the /v1/systemone API"; the request body is the Jev
shape: {"model","state","questions":{name:{"type":"choice","instructions","criteria":{...}}}}
→ answers with per-option probabilities). Read the llama.cpp server docs/source in
~/jevalloc/llama.cpp for the exact route and response. jevd's `--decide-url` /
`--decide-path` must default to what works there. It is local and free, so — unlike what
SPEC-LIVE.md says — **you do run the real `model` and `static-model` policies**, in tests
(one smoke test, skipped when the server is absent) and in the benchmark pass. Record the
model's latency per decision and prompt token counts. Keep jevd's log of every request and
raw response; commit the logs for the final run under results/.

Use the probabilities, not only the argmax: record them, and let jevd take the argmax
unless you find a better use (say what you did).

## 4. The benchmark pass (on the Beelink)

Per benchmark: one trace run (for the oracle table), then the matrix, 5 repetitions,
variants interleaved, one benchmark process at a time, llama-server idle during
repetitions that replay from the response cache:

    sys (glibc malloc), mi (plain mimalloc 2.2.4 .so, same flags), jev-none, jev-keyonly,
    jev-table:oracle, jev-table:random, jev-table:size,
    jev-live:heuristic, jev-live:static-model, jev-live:model

For the live variants report the first (cold, really-asking-the-model) run separately:
decisions, model seconds, blocked time, wall, chip time; then the replayed repetitions as
the headline timing. Report time and peak RSS relative to `mi`, per benchmark and as a
geometric mean, plus: model accuracy against the oracle per benchmark (confusion matrix,
by sites and weighted by bytes), for static-model, model at first sight, and model after
rechecks; same for the heuristic.

## 5. Report

`CODEX-REPORT.md`: what exists, how the Linux override and the fast key work, measured
key cost, the full result tables, and a plain reading: where (if anywhere) Clef-flash
live decisions beat plain mimalloc, beat the no-model heuristic, and how far both are
from the oracle. If the oracle itself does not beat plain mimalloc on a benchmark, say
so: then no predictor can, with this policy. If you think a different use of the class
(SPEC.md "Policy") would do better, try it behind a switch and report it separately.
Also update README.md to describe the project and how to reproduce, honestly labelled
as an experiment.

Constraints as before: no git writes; nothing outside this directory and ~/jevalloc on
the Beelink; no sudo; no system packages. If the model server cannot be made to answer,
finish everything else and say exactly what failed.
