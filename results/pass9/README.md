# Pass 9 evidence

`SPEC-REALTIME.md` governs this pass. `CODEX-REPORT.md` records progress and
limitations; `RESULTS.md` contains the completed findings.

On the test machine, each context workload directory contains a fingerprinted matrix, trace-derived
site/context oracle tables, five-run comparisons, cold model costs and any Redis
search steps. Redis search training and independent headroom validation are
separate. Raw traces, stdout/stderr, response caches, replay schedules and exact
per-object events remain on the test machine. Compact aggregates and supporting
labels are copied here when complete.

`pilot-before-final/` on the test machine contains the completed exploratory
mixed-site measurements before final protocol and measurement-hook changes.
Those pilot numbers are excluded from the final tables.

`permanent-pairs.jsonl.gz` records every context-oracle permanent pair, model answers
and probabilities (or the reason no answer exists). `per-alloc-small/` also
contains exact per-object accuracy and confusion counts. Its `performance/`
subdirectory repeats the five interleaved warm comparisons with exact object
logging disabled, preserving the per-allocation policy while excluding diagnostic
trace metadata from headline memory and timing. `validation.json`
recomputes all gates and greedy decisions; inference audits check actual server
log intervals against the warm measurements.

`compaction/` contains all eleven completed Mesh/nomesh comparisons at normal and
10-second idle (385 interleaved warm runs), with independent inference audits.
These ran after all context measurements. Build provenance and upstream unit-test
logs are under `builds/`. `compaction-comparison.png` and `.svg` visualize the
audited medians; `tools/pass9_plot.py` regenerates them with Matplotlib.
