# Pass 10 evidence

`immediate/named` repeats the original purge-delay=0, arena-multiplier=1,
decommit-enabled server comparison. `defaults/{named,opaque,plausible}` removes
all MIMALLOC_* overrides for every variant and adds the common 10-second idle
observation at each original workload cycle. Real workloads preserve their
original cycle count. Each matrix contains five interleaved warm repetitions,
full phase observations, workload CPU/wall costs and input fingerprints.

`regression.json` uses the existing 22-workload regression protocol and reports
peak RSS and the existing elapsed-time/inverse-throughput metric.

Heuristic and all three rule controls execute from current observations, with
no model inference and no decision replay. Static/hybrid priors use cold
schedules; C hybrid transitions execute in every warm process. Rules and naming
maps were fixed in CODEX-REPORT.md before measurement.

`model-decisions.jsonl.gz` contains model answers, probabilities, contexts and
prompt states. `sites.json` in each synthetic directory contains the trace site
catalogue including unasked sites. `phases.md`, `summary.json`, and `costs.json`
are recomputed from individual accepted records. `validation.json` verifies
complete groups, live rule answers, input hashes, trace labels and independent
inference-overlap audits.

The immediate-options small experiment includes a freshly collected logged cold
schedule; the defaults comparison reuses that checked schedule and recollects
exact lifetimes. Both include
`object-truth.jsonl`, `object-accuracy.json`, five logged warm checks and a
separate five-run interleaved unlogged cost comparison. The sampling-comparison
artifact checks logging does not suppress sampled frees.

Full stdout/stderr, raw traces, caches and decision logs remain on the test
machine at the paths named in each matrix. The compact evidence does not imply
that those remote artifacts can all be reconstructed from this directory.
