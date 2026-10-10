# jevalloc — pass 3: resume on the GPU server, finish the matrix, report

Pass 2 (SPEC-BEELINK.md) got as far as: Linux port done, fast key done (9.4 ns depth 4),
live mode done, tests green on both platforms, benchmark matrix started on the Beelink
(`bench/run.py --name beelink --procs 16 --reps 5 --resume --allow-cold-upgrade`, pid
file/logs under ~/jevalloc/src-tree/results). The codex session that was polling it was
stopped on purpose; the runner and jevd may still be running on the Beelink.

## What changed

Clef-flash on the CPU took ~10 s per decision, which made the cold phases take many
hours. Fable built llama.cpp with Vulkan (`~/jevalloc/llama.cpp/build-vk`, Radeon 780M
via RADV): ~3 s per decision on the same prompts, same choices, probabilities within
~0.02 of the CPU build. `scripts/model-server.sh` now starts that build
(`-ngl 99 -t 4`). A test instance of it may still be listening on 127.0.0.1:8766 — stop it.

## Do

1. On the Beelink: stop the running matrix runner and its jevd cleanly, stop the old CPU
   llama-server on 8765 and the test server on 8766, sync the tree, start the model
   server with the updated script, confirm /v1/systemone answers.
2. Decisions already cached from the CPU server stay valid (same model, same weights,
   argmax-identical on the prompts checked). Keep the cache; record in provenance that
   the backend changed from CPU to Vulkan part-way and which decisions came from which.
   If the cache key includes anything backend-specific, do not invalidate it.
3. **Budget the cold phases.** Even at 3 s, redis (thousands of sites) is too slow to ask
   about everything. Give jevd a per-run model budget (`--max-model-decisions`, default
   400 including rechecks; when exhausted, answer new sites with the default class and
   stop rechecking, and count how many sites and what share of allocated bytes went
   unasked). Report that share per benchmark. If a cheaper prompt gets the same answers
   (fewer source lines), say so but do not change the prompt mid-matrix.
4. Resume the matrix to completion (all workloads in the list, including sh6bench,
   sh8bench and redis), 5 repetitions, variants interleaved, as specified in
   SPEC-BEELINK.md §4. Run it detached on the Beelink and poll sparingly (every few
   minutes, not every few seconds).
5. Fetch results, generate the full report, write CODEX-REPORT.md and update README.md
   as specified in SPEC-BEELINK.md §5. Include the honest reading: per benchmark and as a
   geometric mean, time and peak RSS of every variant relative to plain mimalloc; model
   accuracy against the oracle; model vs heuristic; oracle vs mimalloc. Note in the
   report that Clef's probabilities on these prompts are often close to uniform (e.g.
   0.38/0.29/0.33) and give the distribution of its top-class probability.

Constraints unchanged: no git writes, no sudo, no system packages, only this directory
and ~/jevalloc on the Beelink.
