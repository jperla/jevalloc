# jevalloc — pass 8: fix the runtime-state regression; real programs

Pass 7 (RESULTS.md) was interrupted on purpose during the mimalloc-bench regression
matrix (1 of 22 workloads). Archive that partial run on the test machine as
`results/pass7-regression-partial/` and stop it. Regression runs last in this pass.

## 1. The runtime-state regression, diagnosed

site-pure-1, runtime policy, cold decision log
(`results/pass7/pure-stack-v1/logs/site-pure-1-jev-live-cold-0b787c30.decisions.jsonl`):

| Step | create_session_state (truth: transient) | insert_cache_index (truth: permanent) |
|---|---|---|
| first sight, stack names only | transient 0.87 — right | permanent 0.80 — right |
| recheck at 1,024 objects ("Not freed so far: about 100%") | **permanent 0.91 — promoted** | permanent 0.97 |
| rechecks at 8,192 and 65,536 | permanent 0.90–0.91 | permanent 0.97 |
| recheck at 524,288 ("Freed later 47%") | back to transient, too late | permanent 0.97 |

The first-sight answer was right and the recheck overturned it. The promotion gate
(probability ≥ 0.8 and oldest sample older than a quarter of the allocation clock) is
trivially met early in a run, when everything is young, and the cautionary sentence in
the prompt did not stop the model. "Nothing freed so far" is what both a session and a
cache entry look like until the first sessions end; no statistic can tell them apart
early. Only the code-side prior can.

## 2. The fix: policy `hybrid` (model prior + evidence that only counts when it is evidence)

- First sight: `stack-v1` (code only), exactly as `static-model`. Record the two
  probabilities as the site's prior.
- Afterwards the model is **not** asked again. Sampled runtime statistics update the
  class by fixed rules:
  - **Demote to transient** as soon as frees are observed at a meaningful rate: at least
    5% of the site's sampled requested bytes have been freed (and at least 16 samples).
    Frees are direct evidence; this overrides any prior.
  - **Promote to permanent** only when all hold: no sampled object of the site has ever
    been freed; the prior did not favour transient strongly (P(transient) < 0.7); the
    site's oldest live sample is older than half of the allocation clock; and the clock
    is at least 64 MiB. A site whose prior says transient with P ≥ 0.7 is never promoted
    on absence of frees.
- Keep pass 7's `model` policy available under the name `model-reask` (already measured;
  do not rerun it) and report `hybrid` next to `static-model` and the heuristic.
- Tests: a synthetic trace/unit test for each rule, including the session-like case
  (confident transient prior, no frees for a long time → stays transient) and the
  wrong-prior case (prior permanent, frees appear → demoted).

Expected on site-pure: `hybrid` equals `static-model` (≈ 99% / 94% capture). The case
where `hybrid` should beat `static-model` is a site the model wrongly calls permanent;
report whether any workload contains one.

## 3. Real programs

Add real applications to fragbench, built from source under `build/` on the test machine
with no system packages (skip any that cannot be built that way and say why). For each:
a scripted peak-then-drop workload, idle RSS after a settle period, live bytes from the
program's own statistics where it has them, same mimalloc options for every variant,
five interleaved repetitions.

- **RocksDB `db_bench`** (the mimalloc-bench recipe builds it): fill, then a read-heavy
  phase with many threads and a block cache, then compaction/flush finishes and the
  benchmark goes idle; and a variant where the block cache is small and memtables churn.
  RocksDB has distinct call paths for block-cache entries, table readers, memtable
  arenas, iterators and per-request temporaries.
- **SQLite** (amalgamation): a small C driver — build a large in-memory database, then a
  burst of many connections and prepared statements running queries, then close them and
  go idle.
- **Redis, realistic mixed traffic** (`redis-sessions`): a permanent catalogue written
  once, session keys with TTLs that expire after the peak, many clients with pipelines
  and large replies, pub/sub subscribers that disconnect at the drop. (The two existing
  Redis workloads stay.)
- One more of your choice if it builds cleanly and has an obvious peak-then-drop shape
  (e.g. LevelDB, nginx built without PCRE/zlib and driven by a small client, memcached
  only if libevent headers are already present).

**Headroom first.** The lifetime oracle is not an RSS optimum (pass 5 showed a random
table beating it). Before any model run on a workload, measure whether *any* per-site
labelling helps:
- the transient/permanent oracle table;
- a **search table**: start from all-transient, take the 24 sites with the most
  requested bytes, flip each to permanent in turn and keep the flip if median idle RSS of
  3 runs drops by more than 2%; one greedy pass. Report its idle RSS and which sites it
  moved (by function names).
If neither beats plain mimalloc by more than 5% on a workload, report "no per-site
headroom" for it, with the numbers, and do not spend model decisions there.

Where there is headroom: run `static-model`, `hybrid`, `heuristic` (prompt `stack-v1`,
neutral description written for each new program, 64 KiB admission, budget 1,500), and
report idle RSS, share of the best table's saving captured, time, and for each site the
search or oracle labelled permanent: what the model answered and with what probability,
with the stack it saw. Real code has less descriptive names than server-sim; say plainly
how the model did on them.

## 4. Order and report

1. `hybrid` implemented and tested; site-pure (1 and 16 threads) rerun with it.
2. Real programs: build, headroom check, then model runs where there is headroom.
3. The mimalloc-bench regression matrix, complete, with `stack-v1`, `static-model`,
   `hybrid` and `heuristic`.
4. RESULTS.md rewritten for a reader arriving cold: a short headline section first (what
   was asked, what works, what does not, on which workloads), then the tables; earlier
   passes moved below as history. CODEX-REPORT.md keeps the detail.

Constraints unchanged: no git writes, no sudo, no system packages, never write the
machine's address into a file, do not disturb `~/jevalloc/promptlab`, leave
`tools/promptstudy.py` alone. Keep appending to CODEX-REPORT.md.
