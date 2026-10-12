# jevalloc — pass 10: answer review 2

Read reviews/REVIEW-2.md in full (verdict: REQUEST CHANGES). Its numerical audit supports
the published RSS arithmetic; its four findings and ten wording corrections are this
pass. Where you disagree with a finding, say why in CODEX-REPORT.md and still add the
measurement that would settle it.

## 1. F1 — object logging skips sampled frees

Fix the combined trace+live free path so each free is processed once by both, before the
block is released. Add the combined-mode test the review describes (sample counts,
survivors and hybrid demotions with and without object logging; cross-thread frees;
address reuse). Recollect the per-allocation small experiment (cold schedule, accuracy,
warm runs) on the fixed library.

## 2. F2 — the heuristic must run live

- Warm `jev-live:heuristic` runs must evaluate the heuristic from the current run's
  statistics, not replay a cold schedule. There is no inference to remove from it.
- Add `rules-neutral`: hybrid's continuous C runtime rules with a neutral prior
  (P(transient) = 0.5) and no model at all. This is the statistics-only policy with the
  same observation schedule as hybrid.
- Rerun both on site-pure and site-mixed (1 and 16 threads; with context keys on mixed)
  and on the regression set, next to static-model and hybrid. Keep the old numbers in the
  history labelled "replayed heuristic schedule".

## 3. F3 — mimalloc with its default options

Add a matched default-options series on every fragbench workload: no MIMALLOC_* overrides
for any variant (plain mimalloc, key-only, oracle, static-model, hybrid, the heuristics,
context variants), same workload and phase protocol, both cycles reported, five
interleaved repetitions. Also report idle RSS after a 10 s settle under defaults. The
headline tables must name the configuration they were measured under, and RESULTS.md
must say what plain mimalloc holds at idle under defaults.

## 4. F4 — is it the model, or the names and the TTL string?

- `rule-names`: no model. A fixed keyword rule on the stack's function names decides the
  first-sight class (permanent if any frame name contains `cache`, `index`, `table`,
  `global`, `config`, `intern`, `registry`; otherwise transient), then the same admission,
  placement and hybrid runtime rules. `rule-ttl` for context keys: permanent iff the
  context contains `ttl=day`. Write the rules down before running anything; do not tune
  them on the results.
- Opaque ablation of server-sim, built as separate binaries from the same source with
  only identifiers changed: (a) `opaque`: every allocation-path function renamed to
  `fn_a` … `fn_e`, context values to `k=0`, `k=1`, `k=2`; (b) `plausible`: names a real
  codebase might use that do not say the lifetime outright (e.g. `conn_attach`,
  `obj_new`, `entry_put`, `buf_get`, `resp_build`; context `class=a|b|c`). Program
  description unchanged. Run oracle, static-model, hybrid, rule-names/rule-ttl and
  rules-neutral on each.
- Report, per naming: what the model answered per site or per (site, context) with
  probabilities, idle RSS, capture. State plainly how much of the saving survives when
  the names stop giving the answer, and whether the model beats the keyword rule
  anywhere.

## 5. Wording

Apply review 2's ten wording corrections to RESULTS.md (section 5 of the review), and
keep the headline section short and readable by someone arriving cold: what was asked;
what works and under which configuration; what does not; what the controls show.

## 6. Order

F1 fix and tests; live heuristic and rules-neutral; the rule controls; the opaque and
plausible binaries; then the runs — default-options series and the F2/F4 matrix on
server-sim first, the per-allocation recollection, then the regression set. Update
RESULTS.md and CODEX-REPORT.md as each block completes.

Constraints unchanged: no git writes, no sudo, no system packages, never write the
machine's address into a file, do not disturb `~/jevalloc/promptlab`, leave
`tools/promptstudy.py` alone.
