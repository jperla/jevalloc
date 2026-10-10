# jevalloc — pass 4: fix the two defects, add a fragmentation benchmark, rerun

Read RESULTS.md first (interim headline results), then `build/REVIEW-1.md` (an
independent review of those results and of the code; treat every finding there as part
of this task unless it is wrong, in which case say why in the report).

The test machine is reached with `ssh -o BatchMode=yes "$JEVALLOC_REMOTE"`; work only in
`~/jevalloc` there. A previous matrix run may still be going (`results/bench.log`,
`results/bench.runner.pid` in `~/jevalloc/src-tree`): stop it cleanly before you sync a
new build, and keep its results directory as `results/interim-run1/` on the test machine.
A prompt study may be using the model server (`~/jevalloc/promptlab`, process
`promptlab.py`): leave it running; it only queries the server and waits while the
benchmark log is inside a timed repetition.

## 1. Fix: the shim costs memory

`jev-none` (no site key, one heap) must match plain mimalloc; it currently uses 1.26× its
peak RSS (2.5× on larson). Suspected: a ~72 KiB per-thread site cache in TLS that every
thread pays for even when the policy never uses it, and extra per-thread heaps created
eagerly. Fix so that per-thread state is small and lazy (allocate the site cache on the
first keyed allocation; create a class heap on first use; use the thread's default
mimalloc heap when the policy needs only one heap), and thread exit releases it.

**Acceptance:** on every workload, `jev-none` within 3% of `mi` in time and peak RSS
(5 interleaved repetitions), and `jev-keyonly` RSS within 3% of `jev-none`.

## 2. Fix: live mode is 8–12× slower on threaded workloads

`jev-live:heuristic` takes 8.4× mimalloc's time on larson and 12.5× on xmalloc-test; the
table variants take 1.6–1.9×. Suspected: shared atomic counters and a shared allocation
clock updated on every allocation by every thread. Fix: thread-local counters flushed in
batches, a per-thread allocation clock merged periodically, lifetime sampling that
touches shared state only for the 1-in-N sampled objects, no shared cache line written on
the unsampled fast path. Rechecks may then fire at approximate counts; keep them
deterministic for single-threaded programs (the replay test depends on it).

**Acceptance:** `jev-live:heuristic` within 15% of `jev-table:oracle` in time on larson,
larson-sized, xmalloc-test, mstress, rptest and sh6bench/sh8bench.

## 3. Prompt

The baseline prompt defines classes by byte thresholds and renders runtime statistics as
raw histogram buckets. A prompt study (RESULTS.md) found that describing classes by
meaning and giving more code raises short-vs-long accuracy from 63% to 72–73%. Make the
prompt a named, versioned thing (`tools/prompts.py`, `jevd --prompt <name>`, recorded in
every decision log and in the cache key):

- `v1`: the current prompt, unchanged (so old caches stay valid).
- `v2` (new default): class criteria by meaning — short: "A temporary: scratch space or
  an intermediate value that this function or its caller frees once the current
  operation is finished."; medium: "Kept in a data structure for a while (many
  operations) and released later, well before the program ends."; long: "Stored in a
  global, a table, a cache or another structure that lasts for most of the program, or
  never freed." Stack of up to 12 frames by function name; source for the three innermost
  frames that have source, 20 lines either side, the call line marked `>>`. Runtime
  statistics in plain sentences, e.g. "So far this site has allocated about 1,000
  objects; about half have been freed; of those freed, most were freed almost
  immediately (before 256 bytes more were allocated by the program)." Keep the state
  under 3,000 tokens (the server context is 4,096).

Raise the site key depth for the traced stack shown to the model if needed, but keep the
allocator's key depth a separate setting, and report both.

## 4. A benchmark that can show the effect: fragbench

mimalloc-bench reports time and **peak** RSS of short programs in which nearly all bytes
share one lifetime class; lifetime segregation cannot help there even with perfect
prediction. What it is supposed to help is **memory still resident after load drops**,
when long-lived objects pin pages that short-lived neighbours have left. Add workloads
and a metric for that.

Metric: at marked quiescent points (after a settle time long enough for mimalloc's purge
delay — set the same mimalloc options for every variant and record them), resident
memory and live requested bytes; report RSS, RSS / live bytes ("fragmentation ratio"),
plus total time. Peak RSS is reported too but is not the headline. The runner needs a way
to sample these: for our own programs print them at each phase boundary (read
/proc/self/statm; keep a live-byte counter in the program); for redis use `INFO memory`
(`used_memory`, `used_memory_rss`) and /proc/<pid>/statm.

Workloads:

1. `fragbench/server-sim.c` — a synthetic request server, deterministic (seeded),
   single- and multi-threaded. Distinct, realistically named call paths that all end in
   one `xmalloc` wrapper (so a depth-1 key is useless and depth matters): per-request
   temporaries (parse buffers, response assembly), session objects that live for many
   requests, and cache/index entries that live for the whole run — in the **same size
   classes**. Phases: ramp to a peak (many concurrent sessions, large cache), drop to 10%
   load, idle; then a second peak with a shifted size distribution, drop, idle. Two tiers:
   - `site-pure`: each call path has one lifetime (what a per-site predictor can learn).
   - `site-mixed`: one call path produces both short- and long-lived objects, decided by
     request data (e.g. a TTL field) that is visible in the caller's source but not in
     the stack. Per-site prediction cannot separate these; report it as the hard tier
     and state the per-site oracle's ceiling.
2. `redis-frag` — two scripted redis workloads driven through redis-cli/redis-benchmark
   or a small python client (stdlib sockets, RESP):
   a. The Mesh paper's fragmentation test (Powers et al., PLDI 2019, adapted from redis's
      own active-defrag test): redis as an LRU cache with `maxmemory 100mb`, load random
      keys, then insert a second batch with different value sizes; measure after settle.
   b. Peak-and-drop: populate a keyspace while many clients send large pipelined
      requests, then delete 90% of keys at random and go idle; measure after settle.
   Keep `activedefrag` off for every variant.
3. Keep the full mimalloc-bench set as the second table (regression: are we still slower).

For each fragbench workload, first check the instrument: the **oracle** table must show a
lower idle RSS than `jev-keyonly` on `site-pure`. If it does not, the policy is not
turning separation into returned memory — investigate before running anything else
(mimalloc v2 pages of different heaps share 32 MiB segments; check that fully free pages
are actually purged, and whether per-class heaps need separate arenas/segments to give
memory back) and fix the policy behind a switch, keeping the old one for comparison.

## 5. Rerun and report

After 1–4 pass their acceptance checks: stop, sync, build, `make test` on the test
machine, then run both matrices detached there (fragbench first — it is the new
evidence), 5 interleaved repetitions, variants as before (sys, mi, jev-none, jev-keyonly,
jev-table:{oracle,random,size}, jev-live:{heuristic,static-model,model}) with prompt v2,
cold-run budget 400 model decisions. Poll sparingly. Then:

- regenerate the report (CODEX-REPORT.md) and write the new numbers into RESULTS.md,
  replacing the interim tables; keep the "Status" line honest about what is complete;
- say plainly, per fragbench workload: does the oracle beat plain mimalloc on idle RSS;
  does live Clef beat the no-model heuristic; how far each is from the oracle; what it
  costs in time.

Constraints: no git writes (leave the tree uncommitted), no sudo, no system packages,
only this directory and `~/jevalloc` on the test machine. Do not put the machine's
address in any file.
