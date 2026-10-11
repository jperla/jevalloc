# jevalloc — pass 9: decisions per allocation, from live request context

Joseph: "can we go heavier and use Clef for more real-time malloc" — still imagining the
model on a chip, so call time is set aside and measured separately, as before.

## Why

Everything so far asks the model once per allocation **site**. That works when a call
path has one lifetime (site-pure: 99% of the oracle's saving) and cannot work when one
call path produces both kinds of object (site-mixed, Redis values: zero saving even for
the per-site oracle; the hard tier's per-site classification ceiling is 89.4%). What
separates those objects is data the program has at the moment of allocation — a TTL, a
command, a key name — not the stack. A statistics-only heuristic keyed by site cannot use
it either. A decision model that is consulted with that live context can.

## 1. Request context

- API (header `jevalloc.h`, weak symbols so programs still link without the library):
  `void jev_context_set(const char* text)` and `void jev_context_clear(void)` — a
  thread-local, bounded (≤ 256 bytes) text describing what the thread is doing right now,
  set by the application at its dispatch point. Example for a key-value server:
  `cmd=SET key=session:8f3a ttl=30s size=512`.
- The allocator's decision key becomes (site key, context signature). The signature is a
  hash of the context text after normalisation that the application controls by what it
  writes (it should bucket numbers and strip unique ids itself; provide a helper
  `jev_context_setf` with printf formatting, and document that high-cardinality contexts
  defeat the cache).
- jevd: the context line is added to the `stack-v1` state as
  `What the program is doing right now: <text>`. Same question and criteria. One model
  answer per (site, signature), cached and replayed exactly as before; admission still
  needs 64 KiB at that (site, signature). Budget 3,000.
- `hybrid` rules apply per (site, signature).
- Two reference modes for comparison, both table-driven: `oracle-context` (byte-majority
  class per (site, signature) from a trace that records the signature) and the existing
  per-site oracle.

## 2. Truly per-allocation (no cache), at small scale

To show the ceiling of "the model sees every allocation": a mode
`JEVALLOC_MODE=live`, `--policy per-alloc` where **every** allocation at admitted sites is
sent to the model with its own context and requested size, no caching by signature (the
response cache still keys on the full request so replays are free). Use it only on a
scaled-down server-sim (a few thousand payload allocations) so the cold run finishes in
about an hour; report decisions, model seconds, and accuracy per allocation against the
trace's per-object truth.

## 3. Workloads

1. **server-sim site-mixed** (1 and 16 threads): the worker sets the context before
   handling a request, with the request's TTL bucketed as the code already computes it
   (`ttl=0`, `ttl=short`, `ttl=day`) plus the request kind. Expected: `oracle-context`
   shows a large idle-RSS saving where the per-site oracle showed none; report how much
   of it `static-model` and `hybrid` capture with the context line, and the per-alloc
   mode at small scale.
2. **Redis** (redis-mesh, redis-drop, redis-sessions): a small patch (kept under
   `patches/`, applied by the build, original tree untouched) that sets the context in
   `processCommand`/`call`: command name, the first key's prefix up to the first `:` or
   16 bytes, whether the command carries an expiry, value size bucket; cleared after the
   command. Headroom first: `oracle-context` and a context-level greedy search versus
   plain mimalloc; model runs only if a table saves more than 5%.
3. Any pass-8 real program that showed no per-site headroom and has an obvious request
   dispatch point (SQLite: statement kind; RocksDB/LevelDB: operation kind and whether
   the allocation is for the cache, a memtable or an iterator) — optional, only if cheap.

## 4. Report

Add to RESULTS.md, headline-first: for each workload, idle RSS for plain mimalloc,
per-site oracle, context oracle, code-only Clef per site, Clef with context, hybrid with
context, heuristic; the number of distinct (site, signature) pairs and model decisions;
time cost; for every (site, signature) the context oracle labels permanent, what the model
answered and with what probability. State plainly whether live context turns the hard
tier and Redis from "no saving" into a saving, and how much of it the model captures.
Be explicit that the context API requires a small change to the application.

Constraints unchanged: no git writes, no sudo, no system packages, never write the
machine's address into a file, do not disturb `~/jevalloc/promptlab`, leave
`tools/promptstudy.py` alone. Keep appending to CODEX-REPORT.md.

## 5. Compaction baseline: Mesh

Two readers asked the same question from different sides: "why not just make a better
collector?" and "just catch the segfault and rewrite the pointer". In C the workable form
of that idea keeps every virtual address and moves the physical memory underneath it:
Mesh (Powers et al., PLDI 2019) merges two pages whose live objects do not overlap onto
one physical page by remapping, and uses page protection and a fault handler only as a
write barrier while it copies. Add it as a fragbench variant so the report can say where
compaction beats placement and where placement is enough.

- Build Mesh from source under `build/` the way mimalloc-bench's `build-bench-env.sh`
  does (variant names `mesh` and, with meshing disabled, `nomesh`). No system packages;
  if it cannot be built that way, say exactly what is missing and skip it.
- Run both on every fragbench workload (server-sim pure and mixed at 1 and 16 threads,
  the three Redis workloads, and the pass-8 real programs), five interleaved repetitions,
  same settle period; Mesh compacts on its own timer, so also report idle RSS after a
  longer settle (10 s) for every variant on these workloads.
- Report idle RSS, peak RSS and time next to plain mimalloc, the oracles and the model
  policies. Different base allocators have different baselines, so also report each
  compactor against its own non-compacting twin (`mesh` vs `nomesh`) and each placement
  policy against `jev-keyonly`.
- Do this after sections 1–4 are measured; it must not delay them.
