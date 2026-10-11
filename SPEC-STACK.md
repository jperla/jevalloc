# jevalloc — pass 7: a first-sight prompt that works, run through the live allocator

Read RESULTS.md, in particular "Why Clef captured none of the saving, and a prompt that
would". Pass 6 was interrupted on purpose while the mimalloc-bench regression matrix was
collecting decisions; archive that partial run on the test machine
(`results/pass6-regression-partial/`) and stop it. The fragbench results of pass 6 stand
as "prompt v-permanent-1".

## 1. Prompt `stack-v1` (new default for first-sight decisions)

- State: `Program: <name>`, then `About the program: <neutral description>`, then
  `Call stack of the allocation to classify (innermost first):` and up to 12 frames as
  `  function  (file:line)`. **No source code.**
- Question (choice): "The marked lines lead to a heap allocation. Will this object be
  freed while the program is still running?" — keep this exact wording even though no
  line is marked (it is what was tested); transient: "Yes: it is freed at some point -
  right away, when the request finishes, or when a session or connection ends."
  permanent: "No: it stays until the program exits - an entry added to a cache, index or
  global table that is never removed."
- Descriptions must be **neutral**: what the program is and does, in one or two
  sentences, written as a README would. They must not say which function or call path is
  temporary or retained, and must not name allocation functions with their lifetimes.
  The pass-6 server-sim description does exactly that; rewrite every file in
  `descriptions/`. For server-sim use: "server-sim is a request server: it parses each
  request, builds a response, keeps per-client session state while a session is active,
  and maintains a cache index of content it has served." Keep the old ones as
  `descriptions-leaky/` for an ablation only.
- Prompt variants to run as separate live variants, so the report can say what each piece
  is worth: `stack-v1` (above), `stack-v1-nodesc` (no "About the program" line), and the
  pass-6 prompt (already measured; do not rerun).

## 2. Runtime state: frees are evidence, their absence is not

In pass 6 the runtime policy confirmed "permanent" for the session site because no
session had ended yet when it was rechecked. Change the adaptive (`model`) policy:

- The recheck prompt is `stack-v1` plus: "Observed so far at this site: N objects
  allocated. Freed quickly (before the program allocated another 1 MiB): about X%. Freed
  later: about Y%. Not freed so far: about Z%. The oldest objects from this site have
  existed while the program allocated another V." and one more sentence when Z is 100%:
  "Nothing from this site has been freed yet, which is also what a long-lived but
  eventually freed object looks like early on."
- A site whose first-sight answer was transient stays transient unless a recheck answers
  permanent with probability at least 0.8 **and** the oldest sampled objects are older
  than a quarter of everything the program has allocated so far.
- Apply the same asymmetry to the no-model heuristic and say exactly what rule you
  implemented. Report the old heuristic too (it is the pass-6 number).

## 3. Spend the model budget where the bytes are

On Redis the 400-decision budget went to startup sites and about 98% of requested bytes
came from sites that were never asked. Change the sidecar/allocator protocol so a site is
only sent to the model once it has allocated at least 64 KiB in total (smaller sites use
the default class and are never asked), and raise the budget to 1,500 decisions per cold
run — `stack-v1` prompts are a few hundred tokens. Report, per workload, the share of
requested bytes that came from model-answered sites.

## 4. Runs

1. site-pure (1 and 16 threads) first, all variants including the three live policies
   under `stack-v1` and `stack-v1-nodesc`. Expected if the wording test holds: code-only
   Clef at or near the oracle's idle RSS. If it is not, find out which site was
   misclassified and report it; do not tune the prompt further in this pass.
2. The rest of fragbench (site-mixed, redis-mesh, redis-drop).
3. Then the mimalloc-bench regression matrix, complete, with `stack-v1`.
4. Update RESULTS.md (keep the pass-6 tables as the earlier prompt's result) and
   CODEX-REPORT.md. Headline per workload: oracle saving vs mimalloc; share of it captured
   by code-only Clef, runtime Clef, the heuristic; time cost; share of bytes covered.

Constraints unchanged: no git writes, no sudo, no system packages, never write the
machine's address into a file, do not disturb `~/jevalloc/promptlab`, leave
`tools/promptstudy.py` alone. Keep appending to CODEX-REPORT.md.
