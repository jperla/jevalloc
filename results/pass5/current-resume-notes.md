## Workload attribution correction — partial matrix archived

Source attribution exposed GCC identical-code folding: all four tiny lifetime
wrappers resolved as parse_request_buffer in addr2line, although their caller PCs
still made distinct keys. Thus the model received misleading stack names; session
and cache prompts could collapse to the same source context. The first matrix is
being stopped cleanly and preserved, not published as final model evidence.
CMake now disables GCC IPA identical-code folding for server-sim only. The allocator
library c15e9f... is unchanged; its full validation remains valid.

At the same workload revision, TTL choices use the seeded PRNG instead of i%20.
The periodic pattern aliased 1-in-64 sampling (some retained TTL positions could
never be sampled). Probabilities remain 50% immediate, 45% load-drop, 5% retained;
actual trace shares and ceiling are measured. No sampling rate/policy is changed.
Only server-sim is rebuilt. Unique wrapper PCs/debug names, phase behavior and trace
consistency will be checked, followed by a fresh instrument and full fragbench.

## Distinct wrapper and genuine mixed-site validation

The first corrected workload validation deliberately stopped before any matrix:
GCC branch threading duplicated the mixed allocation call based on TTL, making
short and long populations separately classifiable despite identical source lines.
TTL selection is now a noinline function, preserving one common allocation PC.
A trace-based check requires exactly one payload site with 40–60% short bytes and
3–7% never-freed bytes, four distinct pure wrapper symbols, consistent trace totals,
and drop/idle live-byte accounting at both 1 and 16 threads. All four checks pass.
Pure workload byte-majority accuracy ceiling is 99.932%; genuine mixed is 83.374%
(single thread) / 83.394% (16 threads), including the pure temporary sites.

Final server SHA-256: 2bd8e95865531b34a715b536d99b4519b93c85c516464724ff31ce4920f5a5c9.
Allocator remains c15e9f5ca2e429f883b5e93db1b110d1fb44f443b6b16d07a713fc96e28f7195.
The failed validator supervisor 4042611 exited 1; its successor is recorded in
results/pass5/frag-finish.pid. The archived first matrix and its earlier numerical
commentary are superseded, not combined with this build's measurements.

Corrected supervisor PID 4044072 passed workload validation and completed the
five-run instrument. Oracle/key idle ratios: 0.99859 and 0.99907 (1 thread),
1.00685 and 0.98705 (16 threads). This again fails the strict every-phase gate;
fixed-S session/cache label merging remains the explanation. The full matrix
continues under the recorded explicit override. Frozen source and executable copies
are remote results/pass5/source-distinct.tgz and results/pass5/frozen-distinct/;
local validation has the source archive, checks and checksums. The original full
Linux library suite remains applicable. Current model cold stage: site-pure-1.

Report maintenance: tools/report.py now routes to the audited pass-5 report instead
of emitting obsolete three-class prose or replacing the interruption journal. Its
previous source is preserved as results/pass5/prior/report-pre-pass5.py. README
uses the fixed-S sampled byte-share heuristic, native two-class size baseline and
current pipeline. Report covers cold/fill costs separately, validates the shared
400-slot budget, and scores explicit cold logs with matching-key coverage.
