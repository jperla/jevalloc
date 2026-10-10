# jevalloc — pass 5: two lifetime classes, then finish pass 4

Joseph's decision (2026-10-10): **drop "medium"; use two classes.** In two prompt
studies the model found medium sites 0–21% of the time in most variants, and a
three-way question dilutes the short/long signal.

Pass 4 (SPEC-FRAG.md) was interrupted on purpose to make this change before the long
runs. Its state is in CODEX-REPORT.md (your own running record) and on the test machine
(`results/pass4-stage.txt`, `results/pass4.status`, `results/acceptance-final.*`; a
detached supervisor `scripts/pass4.sh` may still be running — check, let the acceptance
matrix finish or stop it cleanly, and use what it measured). Keep every fix from pass 4.

## 1. Two classes everywhere

- Classes: `0 = short`, `1 = long`. **short**: the object is typically freed before the
  program allocates another `S` bytes (allocation clock), `S` = 1 MiB by default
  (`JEVALLOC_SHORT_BYTES`; tools take `--short-bytes`). **long**: everything else,
  including never freed. No dependence on total run volume any more.
- Allocator: two class heaps per thread (plus whatever the no-policy/key-only controls
  use). Default class for an unknown site: long (`JEVALLOC_DEFAULT`), because sending a
  long-lived object to the short heap is the costly mistake; say in the report if the
  data argue for the opposite default, and include `all-short` / `all-long` tables as
  controls.
- Trace, oracle, baselines (`random`, `size`, `all-short`, `all-long`), heuristic,
  table format, jevd protocol (`class` is 0 or 1), tests, report, accuracy tools: all
  two-class. The oracle is the byte-majority class per site at threshold `S`.
- Old three-class results stay archived as they are (`results/interim*`); do not
  convert them. Decision caches from three-class prompts are not reused.
- On fragbench, report the oracle at `S` = 64 KiB, 1 MiB and 16 MiB as a sensitivity
  check of the instrument (cheap: tables only, no model).

## 2. Prompt v2, two-class (replaces SPEC-FRAG.md §3)

Evidence so far (tools/promptlab.py, results/interim/promptlab-round*.json; rescored as
two classes with tools/rescore_two_class.py): a short description of the program was the
only code-side context that helped; deeper stacks, whole functions and few-shot examples
did not; runtime observations written as plain sentences were read correctly where the
raw histogram line was not. A native two-class study (round 4) is running on the test
machine in `~/jevalloc/promptlab` (round4.log); if it has finished, use its best
variants; otherwise use these defaults and keep the prompt selectable:

- Question (choice, two options). Instructions: "The marked lines lead to a heap
  allocation. Is the allocated object a short-lived temporary or is it kept?"
  short: "A temporary: freed once the current operation is finished, before the program
  has allocated much more memory." long: "Kept beyond the current operation: stored in a
  data structure, table, cache or global and freed much later, or never freed."
- State: program name; **program description** (one paragraph: what the program does,
  its allocation wrappers, what it keeps and what is temporary) read from
  `descriptions/<program>.txt` — write one for every workload including fragbench, by
  hand, from the program's source and docs, and say in the report that they are
  hand-written; stack of up to 12 frames by name; source ±20 lines for the three
  innermost frames with source, call line marked `>>`.
- With runtime state (the `model` policy, at rechecks) append plain sentences:
  "Observed so far at this site: N objects allocated. Freed quickly (before the program
  allocated another 1 MiB): about X%. Kept longer than that before being freed: about
  Y%. Never freed: about Z%." (quantised so replay still hits the cache).
- Record the probabilities. Decide by argmax.
- `static-model` = no runtime sentences, never rechecks. `heuristic` = no model: long
  until observations exist, then short iff the byte-weighted share freed within `S` is
  at least half.

## 3. Acceptance targets are targets, not gates

SPEC-FRAG.md asked for `jev-none` within 3% of `mi`, `jev-keyonly` RSS within 3% of
`jev-none`, and live heuristic within 15% of the oracle table on threaded workloads.
Get as close as is reasonable, then **stop tuning and move on**: record every remaining
miss in the report with its measured size and suspected cause. Do not withhold the
fragbench and model matrices because a micro-gate misses by a few percent.

## 4. Then finish SPEC-FRAG.md §4–5 with two classes

fragbench (server-sim site-pure and site-mixed tiers, redis Mesh test and peak-and-drop)
with the instrument check first; then the detached runs, fragbench first, then the
mimalloc-bench regression matrix; variants sys, mi, jev-none, jev-keyonly,
jev-table:{oracle,random,size,all-short,all-long}, jev-live:{heuristic,static-model,model};
5 interleaved repetitions; cold-run budget 400 model decisions. If time is short,
fragbench completes before mimalloc-bench starts. Then the report and RESULTS.md, with
the plain reading asked for in SPEC-FRAG.md §5.

Constraints unchanged: no git writes, no sudo, no system packages, only this directory
and `~/jevalloc` on the test machine; never write the machine's address into a file; do
not disturb `~/jevalloc/promptlab`.
