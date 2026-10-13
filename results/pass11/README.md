# Pass 11 evidence (complete)

The design in `design.json` and CODEX-REPORT.md was fixed before inference and
performance measurements: six namings, three gates, three priors, two workloads,
two thread counts, ten randomized repetitions. A plain-mi observation accompanies
every paired block. New mappings use fresh inference; the existing plausible
mapping retains pass-10 answers. All priors use the same hybrid replay transport.

`results.md` explicitly reports completed/expected groups. All requested factorial, Redis and diagnostic artifacts and `validation.json`
are present and complete. Earlier partial snapshots were explicitly pending. A successful
correctness suite is not a substitute for the requested measurements.

Metadata reservations include live pair records, thread shards, shard indexes,
and retained sample records. Counters describe raw structure bytes, not RSS or
mimalloc rounding. Fixed live arrays are reported separately. Overflow allocation
counts/bytes count attempted allocations that fall back without registering state.
Samples omitted because sample storage is full have a separate counter.

The Redis follow-up keeps both normalized and unnormalized applications, both
option sets, five repetitions for eleven policies. Diagnostic MI_STAT=2 libraries
are built separately and never substituted into the factorial or Redis runs.
The forced-collection diagnostic samples the default heap first, then tagged
class heaps separately, after the last ten-second observation.

Matrices retain every accepted run, both-cycle phases, metadata, transition
identities/times and CPU. `priors.json` records names, contexts, prompts and all
probabilities. Full traces, logs and caches stay remotely at the paths recorded
in each matrix; the compact evidence does not claim full trace reconstruction.

The full Linux correctness suite passed all 22 workloads and all five live-budget
stress cases. Frozen production library SHA256:
`0496214ecc6dc27fb9f5c2c39b9b40474e3720aa7736037a0fc3c432ca56e0cc`.

Reproduction entry points: `scripts/build-pass11.py` builds the five mechanical
namings and both Redis variants from existing dependencies, `scripts/pass11.sh`
requires passing Linux tests and runs Redis, diagnostics, then the factorial.
`tools/pass11_report.py` recomputes only complete, inference-audited groups;
`tools/pass11_validate.py` requires all 24 factorial blocks, four Redis blocks,
two diagnostic blocks, exact orders, priors, table labels, fingerprints and
zero inference overlap. The declared design is immutable. No generated model
answer or measurement should be replaced to improve an outcome.

`tools/pass11_sync.py --watch` synchronizes compact evidence every 60 seconds,
retries transient transfer failures, and runs `tools/pass11_finish.py` only after
successful final validation and matching local matrix hashes. The active local
watcher's PID/log are `sync.pid` and `sync.log`; remote pipeline status is in
`stage.txt`, `pid`, and (only after exit) `status`. It never treats a running or
failed pipeline as complete. The SSH destination is read from the environment
and is not stored in these files.
