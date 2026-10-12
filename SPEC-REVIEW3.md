# jevalloc — pass 11: answer review 3

Read reviews/REVIEW-3.md in full (verdict: REQUEST CHANGES; the published arithmetic
reproduces; review 2's F1 and F4 are resolved, F2 and F3 partly). Finish whatever pass 10
left running first (the last real-program block, the regression set, validation.json),
then do the following.

## 1. R3-F1 — bound live metadata (the 4.2 GiB Redis failure)

A `LiveSite` (6,016 bytes) and a per-thread `LiveShard` (1,664 bytes) are allocated for
every new (site, context) pair before the 64 KiB admission test, never reclaimed, and
unbounded. Implement the guard the review specifies:

- a process-wide budget for live metadata (pairs and bytes; default 16,384 pairs,
  `JEVALLOC_MAX_PAIRS`) and a per-site context limit (default 64 distinct contexts,
  `JEVALLOC_MAX_CONTEXTS`), checked atomically before allocating site or shard state;
- on overflow, fall back to the context-free decision for that site (one pair per site),
  or to the default class, without registering another pair; count overflows and the
  bytes they covered and report them at exit;
- no eviction of state that has cached shard pointers or outstanding samples;
- a high-cardinality stress test (many more contexts than the cap, worker threads kept
  alive, cross-thread frees) asserting bounded state and continued correct allocation.

Separately fix the Redis context patch so numeric key suffixes normalise into key
families (`k123456` → `k#`), as an application-side fix, and keep the unnormalised
variant as the stress case. Rerun redis-drop (both variants, defaults and immediate
purge) for mi, static/site, static/context, hybrid/context and the no-model controls,
with explicit metadata-byte counters, and report idle RSS and CPU.

## 2. R3-F2 — finish and correct the record

Commit the remaining accepted five-run groups and audits; make results/pass10/README.md
and results.md say "pending" wherever an artifact is absent at a given revision; state in
the headline what is and is not complete.

## 3. Is the plausible-names advantage real? A predeclared factorial

The only evidence of a model-specific advantage is hybrid on one plausible renaming, and
the review shows it depends on the 0.7 promotion gate (pure survives 0.6, mixed does not;
neither should survive 0.8). Settle it. **Write the full design into CODEX-REPORT.md,
including every name mapping and seed, before running any of it, and do not change it
after the first result.**

- Factors: promotion gate {0.6, 0.7, 0.8} × prior source {model, neutral 0.5, matching
  names/TTL rule} × workload {site-pure, site-mixed} × threads {1, 16}, mimalloc defaults.
  Model and neutral priors go through identical transport (replay of a recorded answer
  file; only the probabilities differ).
- Namings: the existing plausible mapping, plus **five new mappings generated
  mechanically** — take a fixed list of 40 identifier fragments commonly found in C
  server code (write the list down first: e.g. conn, sess, req, resp, buf, obj, entry,
  node, item, ctx, msg, pkt, slot, rec, blk, hdr, str, vec, map, pool …; no word that
  states a lifetime such as cache, temp, tmp, perm, static, global, index, table) and
  verbs (new, get, put, add, make, init, attach, build, alloc, push), and draw each
  function's name with a seeded RNG (seeds 1–5). For site-mixed also permute which
  context class letter maps to which lifetime, per seed. Same description text for all.
- Fresh model inference for every new mapping (budget as before); record every
  probability.
- Ten repetitions per cell, variant order randomised within each repetition block with a
  recorded seed; report per cell the median and range of idle RSS, promotions (which
  site, when), and for each naming × workload the paired difference hybrid(model) −
  rule and hybrid(model) − hybrid(neutral) with a bootstrap 95% interval.
- Report plainly: in how many of the six namings does model+rules beat both the matching
  rule and the neutral-prior rules, at which gates; and in how many is it worse than
  plain mimalloc.

## 4. Why defaults return less (diagnostic only)

For site-pure-1 under defaults and under immediate purge, with identical phase histories:
record mimalloc's own statistics (committed, reserved, purged; `mi_stats` or the
MIMALLOC_SHOW_STATS output) at each phase for mi, oracle and static-model, and one
separately labelled diagnostic run that calls `mi_collect(true)` at idle. Report whether
the remaining 214 MiB under defaults is committed-but-free memory awaiting purge or
pages still in use.

## 5. Report

RESULTS.md headline: adopt the one-paragraph headline proposed at the end of review 3 as
the starting point and update it with what this pass finds. Say "4 of 16 server
comparisons against the matching names/TTL rule". Keep the history below.

Constraints unchanged: no git writes, no sudo, no system packages, never write the
machine's address into a file, do not disturb `~/jevalloc/promptlab`, leave
`tools/promptstudy.py` alone. Keep appending to CODEX-REPORT.md.
