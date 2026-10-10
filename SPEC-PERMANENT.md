# jevalloc — pass 6: move the class boundary to transient vs permanent

Pass 5's own fragbench numbers show the two-class boundary is in the wrong place.

## The evidence (results/pass5/progress/synthetic-summary.md, site-pure-1)

| Variant | Idle RSS | vs mimalloc |
|---|---:|---:|
| plain mimalloc | 280.22 MiB (29.3 MiB live, 9.6× fragmentation) | 1.000 |
| oracle, short = freed within 1 MiB | 280.07 MiB | 0.999 |
| **random table** | **42.55 MiB** | **0.152** |

The trace explains it (four sites carry the bytes):

| Site | Bytes | Lifetime | Oracle S=64 KiB / 1 MiB / 16 MiB | Random |
|---|---:|---|---|---|
| assemble_response_buffer | 307 MiB | freed immediately | short | 1 |
| parse_request_buffer | 307 MiB | freed within ~1 KiB | short | 0 |
| create_session_state | 276 MiB | freed after 128–512 MiB more is allocated | long | 1 |
| insert_cache_index | 31 MiB | never freed | long | 0 |

Every fixed-S oracle puts sessions and cache entries in the same heap, which is what
plain mimalloc does. The random table happens to put the never-freed cache entries in a
different heap from the sessions, and idle memory falls by 85%. What matters for memory
after load drops is separating objects that are **eventually freed** (temporaries and
sessions alike: their pages empty out) from objects that **never go away** (they pin
whatever page they sit in). The 1 MiB cut separates the wrong pair.

## The change

- Two classes, renamed: `0 = transient`, `1 = permanent`.
  **permanent**: never freed, or alive for more than half of the program's total
  allocation volume. **transient**: everything else (freed immediately or after a while).
  The oracle is the byte-majority class per site under this definition. Keep
  `--short-bytes`/fixed-S tables only as extra controls (`oracle-S-1048576` etc.), no
  longer as "the oracle".
- Default class for unknown sites: transient (most allocation volume is transient);
  keep `all-transient` / `all-permanent` controls and say in the report if the data argue
  for the other default.
- Live heuristic: a site is permanent while none (or almost none: under 5% by sampled
  bytes) of its sampled objects older than the site's own median age have been freed —
  write down the exact rule you implement; it has to work without knowing the final run
  length. Transient as soon as frees are observed at a meaningful rate.
- Prompt (replaces the short/long wording in SPEC-TWOCLASS.md §2; same context: program
  description, 12-frame stack, three marked snippets): instructions "The marked lines
  lead to a heap allocation. Is the allocated object released at some point, or is it
  kept for the rest of the program?"; transient: "Released at some point while the
  program keeps running: a temporary, or something held for a while (a request, a
  session, a work item) and then freed."; permanent: "Permanent: kept for the rest of the
  program - a cache or index entry, a global table, configuration, or anything that is
  never freed." Runtime sentences: "Observed so far at this site: N objects allocated.
  Freed quickly (before the program allocated another 1 MiB): about X%. Freed later:
  about Y%. Not freed so far: about Z%." A prompt study with these wordings is running in
  `~/jevalloc/promptlab` (round5.log); use its best variant if it has finished.
- Decision caches from the short/long prompts are not reused.

## Then

1. Stop the fragbench run that is collecting short/long model decisions (archive it as
   `results/pass5-shortlong/` on the test machine; its tables stay in the report as the
   "wrong boundary" result — it is a finding, not a mistake to hide).
2. Instrument check again on site-pure (1 and 16 threads): the transient/permanent oracle
   should be at or below the random table's idle RSS and far below mimalloc's. If not,
   find out why before continuing.
3. Sensitivity on site-pure: the oracle under three "permanent" thresholds (alive for
   more than 25%, 50%, 90% of the run, plus never-freed-only).
4. fragbench in full (site-pure, site-mixed, redis Mesh test, redis peak-and-drop), then
   the mimalloc-bench regression matrix, variants as in SPEC-TWOCLASS.md §4 with the
   renamed controls. fragbench completes before mimalloc-bench starts.
5. Report and RESULTS.md. The headline to establish or refute, per workload: how much
   idle memory does the oracle save against plain mimalloc; how much of that does live
   Clef capture, with code only and with runtime state; how much does the no-model
   heuristic capture; at what cost in time. State the hard tier's per-site ceiling.

`tools/promptlab.py` is now your two-class tool; Fable's study script lives in
`tools/promptstudy.py` — leave it alone. Constraints unchanged (no git writes, no sudo,
no system packages, never write the machine's address into a file, do not disturb
`~/jevalloc/promptlab`). Keep appending to CODEX-REPORT.md.
