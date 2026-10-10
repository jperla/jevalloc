# jevalloc — spec v1: live decisions (supersedes the "precomputed table" framing of SPEC.md)

Joseph's correction: a table computed offline is not the experiment — offline you could
use any big model. The point is a small decision model consulted **live, while the
program runs, from live state**. It is slow today; we imagine it burned into a chip
later. So the allocator must really ask the model during the run, and the measurement
must separate "what the decisions did" from "how long today's model took to answer".

Everything in SPEC.md stays (trace mode, oracle, table mode, runner, tests); table mode
becomes a control. This adds a live mode.

## jevd — the decision sidecar (stands in for the chip)

`tools/jevd.py` (python3 stdlib only), listening on a unix socket
(`JEVALLOC_SOCKET`). The allocator never does HTTP itself. Line-delimited JSON, one
request → one response.

Request from the allocator:

    {"op":"decide","key":"<hex>","frames":[{"addr":"<hex, slide-normalised>","image":"<path>"}...],
     "size":<bytes of the triggering request>,
     "site":   {"allocs":N,"frees":N,"live":N,"bytes":N,"life_hist":[...log2 buckets on the allocation clock, sampled...]},
     "process":{"alloc_clock":bytes,"live_bytes":N,"committed":N,"rss":N,"threads":N,"sites":N},
     "prior":  <class given last time, or null>}

Response: `{"class":0|1|2,"recheck_after":<allocations of this site until it may ask again>}`.

jevd symbolises the frames (atos, cached), attaches source snippets as in
tools/symbolize.py, and decides according to `--policy`:

- `model`  — POST `{--decide-url}/v1/decide` (same contract as tools/label.py),
  `--model <id>`, optional `--reasoning`. **The model is Clef-flash, served locally**:
  `--decide-url` defaults to `http://127.0.0.1:8765` (a local server Fable provides that
  wraps the MLX 4-bit build of Cloudflare/clef-flash behind the same request/response
  shape; no API key — send the Authorization header only if `JEVALLOC_DECIDE_KEY` is
  set). Default `--model clef-flash`. Keep prompts short (well under 1k tokens: stack,
  ±6 source lines for at most two frames, compact statistics) — the model runs on an
  8 GB laptop. State = program name + symbolised stack + snippets + the live site and
  process statistics rendered as short readable text. Question: choice short/medium/long
  with the class definitions from SPEC.md.
- `heuristic` — no model: medium on first sight, afterwards classify from `life_hist`
  alone. This is the control that matters most: the model has to beat it.
- `static-model` — like `model` but the state omits all runtime statistics and it never
  asks to be rechecked (isolates what the model gets from code alone).
- `oracle` — answers from an oracle table of a prior trace (upper bound).
- `random` — seeded.

**Response cache / replay.** jevd keeps a disk cache keyed by (policy, model, canonical
request). To make repeated runs hit it, the allocator quantises every statistic it sends
(counts and bytes to powers of two; histogram to per-bucket log2 shares) and rechecks at
deterministic points (see below). First run of a benchmark = live and slow; later
repetitions replay the same decisions in microseconds. jevd logs every decision
(request, raw model response, latency, cache hit/miss, token usage) to a JSONL file.

## Allocator: `JEVALLOC_MODE=live`

- Unknown site → send `decide`, **block** this allocation until the answer arrives, cache
  the class for the site. Other threads asking for the same site wait for the same answer.
- Recheck: when a site's allocation count since its last decision reaches
  `recheck_after` (jevd's default schedule: 1k, then ×8 each time, capped by
  `--max-rechecks`, default 4), ask again with the current statistics. A changed class
  applies to future allocations only.
- Per-site statistics need object lifetimes: sample (default 1 in 64 allocations per
  site, env `JEVALLOC_SAMPLE`) and track sampled objects until free. Document the fast
  path cost of this.
- If jevd is unreachable or times out (`JEVALLOC_TIMEOUT_MS`, default 30000): default
  class, count it, never crash, never hang the program.
- **Time accounting.** Accumulate the wall nanoseconds every thread spent blocked on
  jevd, plus counts (decisions, rechecks, timeouts). At exit write them to
  `JEVALLOC_STATS_OUT` (JSON). The runner reports, per run: raw wall time, model-blocked
  time, and "chip time" = wall − blocked. For multi-threaded programs chip time is only an
  approximation (other threads kept running while one waited) — say so in the output, and
  prefer the replayed repetitions (cache hits, near-zero blocked time) as the headline.

## Runner additions

Variants `jev-live:<policy>[:model]` start a jevd for the run (or one shared jevd per
variant), wait for the socket, run the benchmark, collect allocator stats and the jevd
decision log, and stop it. Record per run: decisions, cache hits, model seconds, tokens,
dollars if the response reports usage. The summary compares, against plain mimalloc:
jev-none, jev-keyonly, table oracle, live heuristic, live static-model, live model.

## Tests

A fake jevd in the tests (fixed answers, artificial delay, and a mode that never
answers) to prove: blocking + accounting are right, a dead sidecar does not hang or
crash, rechecks fire at the scheduled counts, a class change mid-run is safe under
multi-threaded load, and a second run with a warm cache produces byte-identical requests
for a single-threaded deterministic benchmark (cfrac).

Do not call the real model in tests or in your benchmark pass (no key in the sandbox);
run the live variants with `heuristic`, `oracle` and `random` only. Fable runs `model`.
