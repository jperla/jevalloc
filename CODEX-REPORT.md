# Pass 5 execution record — native two-class work

Current status (2026-10-10): final two-class library c15e9f... passed full Linux
correctness and macOS targeted tests. The first partial fragbench matrix is archived
under remote results/pass5/prior/folded-wrappers: GCC folded distinct lifetime
wrappers to one debug identity. Server-sim now disables that folding and uses seeded
TTL draws to avoid sample-period aliasing. The new supervisor is
scripts/pass5-frag-finish.sh (PID 4044072, also in results/pass5/frag-finish.pid).
Workload validation passed. The repeated instrument is negative; its 30 timings
have zero inference overlaps. Fragbench has completed all four synthetic blocks and is collecting Redis Mesh
cold model decisions;
sensitivity and regression follow. No regression has started. Progress: results/pass5/stage.txt and
results/bench.log; exit: results/pass5/status. Do not replace the active build.
Old pass-4 text below is historical.

# Pass 4 execution record

Status (2026-10-10): acceptance has not passed; full model matrices are withheld.

Latest completed five-repetition check: cfrac none/mi time 1.023761, RSS
1.000914, key-only/none RSS 1.033790. That compare attempt was stopped and archived.
The subsequent cache diagnostic passed targeted Linux/macOS tests and reduced
cfrac live time substantially, but still missed key RSS and threaded live gates.
Current detached supervisor: **2101937**, `scripts/pass4.sh`; finalizer **2101938**.
It builds and runs targeted correctness, then five interleaved repetitions across
all 22 acceptance workloads. Progress: `results/pass4-stage.txt`,
`results/pass4-targeted.log`, `results/bench.log`; exit: `results/pass4.status`.
The entire acceptance matrix will finish even if an early numerical check fails,
to identify the full failure set. Strict gates still stop subsequent full tests,
final instrument, and the model matrices. No full model matrix has started.

The rest of this document is a chronological record; earlier running PIDs and
candidate descriptions are superseded by the later entries.

Read SPEC-FRAG.md, RESULTS.md and reviews/REVIEW-1.md. The previous matrix
and its supervisor/descendants were stopped on the test machine before syncing.
Its complete results directory is preserved under
`~/jevalloc/src-tree/results/interim-run1/`. The independent promptlab process
was left running. No machine address is recorded here. All work remains uncommitted.

Planned order: small lazy TLS/default-heap controls and acceptance; batched live
statistics and acceptance; remaining allocator findings; prompt v2; fragmentation
instrument validation; detached fragbench then regression matrices; final analysis.

Initial source diagnosis: static TLS embeds 256 large key entries; aligned none-mode
entry points lack a bypass; key-only uses an explicit no-reclaim heap; live mode
writes a global allocation clock and shared site counters on every allocation.

## First acceptance attempt

The first Linux build reduces PT_TLS from about 72 KiB to **81 bytes**. A detached
five-repetition control matrix is running (`results/acceptance-fix1.json`, progress
in `results/bench.log`). Early results **fail** the strict 3% gate: cfrac none/mi
score 1.062 and RSS 1.371; espresso 1.028 and 1.183. Larson's large TLS memory
penalty disappears in early repetitions, but time remains above the target.

A further confound was identified: linking the shim with the C++ driver forces
libstdc++ into C workloads, adding roughly 1.8 MiB. The next build makes C++ ABI
references weak on Linux, keeping C++ exception/new-handler behavior when a C++
program supplies its runtime. It also enables equal LTO/local-call optimization
for both allocator libraries. This requires renewed acceptance, not adjustment
of the recorded data.

Implemented locally, not yet accepted: sharded success counters with 256-object
merges, batched byte clock, reusable sample records, byte-weighted freed histograms;
reclaim-enabled tagged heaps and build-tree-only upstream reclamation patch;
heap failure checks; in-place realloc bookkeeping; realpath routing; exact raw
stack cache comparisons; separate key/model depths (4/12); versioned prompts.

Linux key normalization explicitly supports startup images only for this pass;
dlopen-created images remain outside the supported program set. No claim of
loader-safe dynamic image support is made.

The no-libstdc++ build passes the Linux fault-injection and C++ stress tests.
Early renewed cfrac measurements have none/mi time 1.004 and RSS 1.017, so that
additional RSS confound was material. Key-only still exceeded 3% RSS; the cache
is being reduced to 64 entries. Wider model stacks are now captured only on
cache misses, not on every live allocation. These changes invalidate reuse of
earlier acceptance records; they will receive a new run name.

The targeted Linux suite passed (cfrac trace/random, exact lifetime boundaries,
all interposition stress policies, live protocol/timeout/cache, replay fills,
model budget). The equivalent macOS cfrac-targeted suite also passed before the
latest cache-size change. Full `make test` remains pending.

Fragbench code now includes site-pure/site-mixed at 1/16 threads and two Redis
RESP workloads. It records phase RSS/live bytes and the ratio, plus peak RSS and
wall time. The instrument gate requires lower oracle idle RSS at both idle
phases and both site-pure thread counts, and binds the result to the library hash.
No full fragmentation or model matrix has been authorized by a passing gate yet.

## Live contention follow-up and portability

The five warm Larson observations in the second attempt still put live heuristic
around 2.2× oracle time. The 15% gate has **not** passed. Allocation counters alone
were insufficient: sampled histograms, live estimates and sample totals still
wrote shared cache lines. Those statistics now live in padded thread/site owners;
reference-counted owners survive thread exit while sampled objects remain, then
merge into the site and are freed. Sample record pools and locks are sharded;
recheck polling is local between bounded aggregation points. This implementation
runs the same statistics in cold and replay modes (no replay-only fast path).

A targeted macOS cross-thread test found that a C TLS recursion guard in the
mimalloc patch could recursively invoke the loader while initializing TLS. The
patch now uses the backing heap's existing no-reclaim guard during preparation,
which also prevents recursive reclaim while allocating heap metadata. The
three-tag thread-exit regression passes after this fix. C++ new-handler invocation
has explicit coverage in addition to bad_alloc and nothrow cases.

Reporting helpers now reject cold/fill/probe/failed/interfered records and require
exactly one accepted observation for every warm repetition, across the same
workload intersection. Live accuracy now selects explicit cold log paths and
separates policy answers from model-backed answers and unmatched-key coverage.

The first fully sharded diagnostic (one repetition, not acceptance) measured
live/oracle time ratios **1.37 on Larson** and **1.32 on xmalloc-test**, versus
about 2.2 on Larson before sharding sampled statistics. The latest build isolates
clock/control cache lines and merges success counters/clock every **1,024** successes.
It retains 1-in-64 lifetime sampling. This is still a true-live path; replay does not
skip the counters. Clock error can span pending bytes from every active thread.

The lazy key cache now uses an anonymous mapping: allocating its roughly 28 KiB
through mimalloc committed a larger medium-object page, undermining the small
control's 3% RSS target. The mapping is unmapped on thread exit, independent of
mimalloc destructor order. Table parsing and main-thread stack-bound discovery
also avoid stdio heap allocations. A new diagnostic and the five-repetition
site-pure instrument check are running sequentially on the remote machine.

The final isolated macOS cfrac-targeted suite passed, including the new tests.
Earlier overlapping local test attempts were invalidated by shared output paths;
only `build/pass4-tests-single.log` is the accepted local suite record.

Warm-run inference gating now publishes the existing repetition marker and waits
for the local server's `/slots` to be idle before starting timing. This lets the
independent prompt study finish its in-flight request, then obey its existing gate;
it is not stopped or paused by this project. Explicit run start/end timestamps
support a subsequent server-log interference audit.

## Instrument evidence (five interleaved repetitions)

The completed instrument check **passes both phases at both thread counts** on the
pre-final library (hash and raw phase observations in `results/pass4/instrument/`).
Final idle medians:

| Site-pure workload | mi RSS MiB | key-only RSS MiB | oracle RSS MiB | oracle / mi |
|---|---:|---:|---:|---:|
| 1 thread | 280.21 | 280.29 | 42.33 | 0.151 |
| 16 threads | 296.54 | 295.68 | 58.59 | 0.198 |

At the first idle point oracle was 22.64 / 41.29 MiB (1 / 16 threads), versus
key-only 122.29 / 136.69 MiB. Tagged, reclaim-enabled heaps do return free pages
with the common immediate-purge options; separate arenas are not needed to make
this instrument work. This is synthetic oracle evidence, **not** model evidence.
The check must be repeated after the final library changes before any long matrix.

The pre-final one-repetition diagnostic still fails the live target (Larson about
1.41× oracle; xmalloc about 1.34×). The last optimization adds a conservative
spatial negative filter for sampled pointers, so most unsampled frees can skip
the larger hash table. Four-bit filter counters saturate permanently positive;
collisions/overflow cause extra probes, never missed samples. Sampling remains
1/64, with unchanged site/clock semantics. `JEVALLOC_SAMPLE_FILTER=0` permits an
ablation. Final acceptance is not yet known.

## Final validation sequence

Final review caught a thread-destructor ordering issue: leaving the shim recursion
guard raised after freeing its cache would skip sampled frees made by later
application TLS destructors. Teardown now clears cached heap pointers and restores
the Linux recursion guard. A regression uses a later pthread-key destructor to free
all objects; sample rate 1 also exercises filter saturation. The superseded partial
full test log is preserved as `results/pass4-test-before-destructor-fix.log` remotely.

`scripts/pass4.sh` is the detached, fail-closed sequence: targeted Linux correctness,
five interleaved acceptance repetitions, full Linux `make test`, instrument recheck bound to the final
library and server-sim binary/options, fragbench matrix, then mimalloc-bench matrix,
then summaries and an inference audit. It writes `results/pass4.pid`,
`results/pass4-stage.txt`, `results/pass4.status` and appends stages to the remote
CODEX-REPORT.md. The long matrices are conditional on passing every gate; no failed
gate is waived. Logs, cold/fill decisions, stdout, stderr and phase records remain
on the test machine. The prompt study remains running independently.

## Review disposition

- Review §2: warm selection requires exact repetition sets, successful output and
  decisions, and excludes cold, fills/probes, rejected/interfered records. Shared
  workload intersection is used. Accuracy population and coverage are explicit.
- §3: static TLS cache removed; all listed aligned APIs share the centralized none
  bypass; key-only uses the default heap. `jev-explicit` / `JEVALLOC_POLICY=explicit`
  preserve the old one-explicit-heap control. Performance gates remain empirical.
- §4: success counters and sampled statistics are sharded; the clock is batched;
  sampled owners survive cross-thread frees. No replay-only instrumentation shortcut.
- §6: heap failure checks and injected tests; failed attempts excluded from successful
  bytes/clock; byte-weighted histograms plus sampled survival; in-place realloc with
  explicit logical lifetime bookkeeping; class tags retained across thread exit and
  receiving heaps created lazily; raw-stack identity checks; realpath routing.
- Dynamic Linux image loading is explicitly outside the supported program set,
  rather than claiming a loader-safe implementation. Metadata/bootstrap and work
  after the exit snapshot remain excluded. Concurrent exit statistics are approximate.
- The heuristic's long threshold/survival evidence are explicitly approximations,
  not the trace's retrospective truth. Oracle is a prior-trace byte-majority site
  label, not a per-object classifier or a bound on possible RSS policies.
- Historical evidence and caveats from the numerical/prompt audit remain archived;
  current RESULTS.md makes no new unmeasured model or Redis claim.

Further fast-path changes queued after the current test pass: replace per-allocation
sampling division with an equivalent countdown; parse stack-map address ranges
without pulling in scanf; route none-mode strdup/strndup/realpath directly to mimalloc.
The sampling period and decision schedule are unchanged. The destructor regression
now checks the targeted site's surviving samples, rather than incorrectly requiring
zero surviving samples from unrelated runtime/stdout allocations at process exit.
Per-site surviving-sample totals are included in the final stats file.

The next supervisor first builds and runs targeted correctness, then runs the full
five-repetition acceptance set. Only if that passes does it run full `make test`,
repeat the instrument on the exact final build, and start fragbench followed by
mimalloc-bench. A detached finalizer publishes complete tables only after every gate
and inference audit passes; otherwise it records the exact failed stage and measured
gates. The original in-flight test pass is allowed to finish before the restart.

Latest deployed source: targeted Linux suite **ALL TESTS PASSED**, including the
per-site destructor/saturation assertion, replay, budget, stress, exact lifetimes
and cfrac trace/random modes. Final-source macOS live tests also pass. The current
Linux PT_TLS segment is **97 bytes** (readelf), versus about 72 KiB originally.
The five-repetition acceptance run is active across all 22 workloads, supervisor
PID **1746341**, finalizer PID **1746342** (also recorded in remote PID files).
The full 10-variant model matrices remain conditional on passing the gates.
Local validation evidence is in `results/pass4/validation/`.

All 22 workloads in the preceding full test attempt completed trace and random
runs. That attempt failed an obsolete exact-count assertion on the **threaded** live
case: batched aggregation may legitimately skip the 1,024 quantization bucket. The
exact 1,024 assertion now uses a single-thread fixture; threaded tests require safe
rechecks without assuming an exact merged count. Separately, the destructor test
uses a precise per-site survivor assertion because runtime/stdout objects can remain
alive at exit. Targeted Linux and macOS live suites passed before this test-only
scheduling assertion correction; it is included in the queued full suite. Full `make test` is queued
again on the final source after acceptance, before the final instrument and matrices.

The corrected single-thread recheck test passed locally (`build/pass4-live-corrected.log`).
An additional fault-injection regression now repeats 2,048 failed allocations at one
site and verifies zero successful bytes/samples and no success-driven rechecks. It
is queued for validation. Reporting now states the numeric byte-classification
ceiling for each site-mixed trace. The finalizer was restarted as PID **1757873**
after making publication idempotent; the acceptance supervisor was not restarted.

Five completed cfrac acceptance repetitions: none/mi time **1.0212**, none/mi RSS
**1.0329**, key-only/none RSS **1.0035**. Thus the 3% no-policy RSS gate still fails
on this workload (147,456 additional bytes). Other workload acceptance is running;
no inference/model matrix has been authorized by an unpassed gate.

The 2,048-failure accounting regression passed locally
(`build/pass4-live-accounting.log`). A further candidate now avoids all keyed
startup initialization in ordinary none mode, while the public key diagnostic
initializes it lazily. Live before/after/free paths inline only their unsampled
checks; decisions, sampled records and locks remain in out-of-line slow paths.
The recheck poll counter now shares the thread-owned success-counter cache line.
No sample rate, class decision or threshold was changed. This candidate is under
local correctness validation and has not replaced the remotely measured library.

The countdown-build acceptance attempt was stopped after cfrac, espresso, barnes
and larson completed five repetitions each. Larson live/oracle was **1.3371**,
above 1.15. Raw logs were moved to remote `results/logs/acceptance-countdown`;
record paths were updated accordingly. The matching source and library are retained
under remote `results/pass4-attempts/countdown`, and the matrix was fetched to
`results/pass4/attempts/acceptance-countdown.json`. Supervisor and descendants are
confirmed stopped; the independent prompt study was not signaled. The old supervisor's
SIGTERM trap wrote 0; the archive explicitly marks this as a manual stop, not success.

The next candidate also derives surviving samples/bytes from sampled totals minus
frees, removes redundant atomic RMWs under existing sample locks, and places each
reusable sample-record pool head beside its padded mutex. It preserves sample rate
64 and the same statistics. Completed recheck schedules no longer poll every 64
allocations. The inline-only candidate passed local targeted tests; the additional
counter changes are now being tested on both machines. Detached remote diagnostic
PID **1859634** writes `results/pass4-diagnostic.status`, stage/log files, and
`results/diagnostic-inline.json`. This is one repetition for cfrac/larson/xmalloc,
not acceptance and not either requested model matrix. No finalizer is active until
the acceptance supervisor is restarted.

The counter/inline candidate passed targeted correctness on Linux and macOS
(`results/pass4/validation/pass4-inline-targeted.log`, local
`build/pass4-counter-tests.log`). Its one-repetition diagnostic measured
cfrac none time/RSS 1.027/1.001 and key/none RSS 1.005; larson live/oracle 1.219;
xmalloc live/oracle 1.168. xmalloc none time was 1.074, so it is not evidence of
acceptance. These diagnostics are in `results/pass4/attempts/diagnostic-inline.json`.

The inference audit initially reported one 20 ms overlap at the end of the last
cfrac oracle run. Source inspection of the running server showed that the log's
wall-clock origin is distinct from /proc process-start time. Calibrating paired
release log timestamps and LRU `t_last_used` monotonic values puts the logger origin
**206.082 ms later**; ten recent pairs agree within 1.2 microseconds. The corrected
audit finds **zero overlaps in 106 recorded warm runs**, including the incomplete
next workload. The calibration pairs are preserved in the fetched audit JSON.
The performance failures are unchanged. Future acceptance and both full matrices
require this calibrated audit, with PID-start identity checked separately.

Detached diagnostic PID **1881923** now runs a rare-sampling ablation followed by
a SIGPROF CPU-PC profile of Larson. `perf_event_paranoid=4` prevents ordinary perf
profiling; the small Linux-only diagnostic sampler allocates nothing in its signal
handler. These runs carry diagnostic markers and cannot enter headline selection.
Production sampling remains 1/64. The normal supervisor will run build, acceptance
plus inference audit, full make test, exact-build instrument, fragbench, then
mimalloc-bench; it no longer repeats the already passed targeted suite on startup.

The rare-sampling ablation (1/1,048,576, diagnostic only) measured Larson live/oracle
**1.1161**, versus 1.2194 at the unchanged production 1/64 rate. A 2,224-sample
SIGPROF profile attributed about 28.5% to capture, 16.2% to mimalloc allocation,
8.1% to the shim allocation path, 5.7% to shim free and 5.0% to mimalloc free.
This is a coarse CPU-PC profile, not a blocked-time attribution or acceptance run.
Raw PCs and both diagnostic matrices are retained under results/pass4/attempts.

A page-local negative filter is now under validation (remote diagnostic PID
**1895434**). It uses mimalloc's unused padding word without changing page size;
`mi_segment_page_clear` already zeros that word after the last object is released,
and abandonment/reclamation retain it with live objects. The old spatial filter
remains selectable. Saturation is conservative. This candidate has not yet
established the 15% gate. Production sampling is still 1/64.

Owner-local class publication and its threaded long-to-short heap-tag regression
passed Linux tests. The candidate also removes recursion-guard writes from
unsampled frees and moves C++ handler/exception work to a cold failure path.
One-repetition owner candidate: Larson live/oracle 1.2151; xmalloc 1.1652, with
xmalloc none/mi time 1.0132. This still did not establish the 15% gate.

The latest candidate keeps normalized model frames out of the key-only cache:
12 KiB for keyed-only state, plus 16 KiB only when instrumented. Merge batches are
now 4,096 successes per thread/site, also flushed before decisions and at thread
exit; sampling remains 1/64, and the single-thread 1,024 recheck remains exact.
Larger batches make cross-thread clock/count snapshots coarser. Both targeted
suites passed. Diagnostic PID **1940146** is the current measurement job.
Full-suite reports now carry the tested library hash and a full-suite flag; final
publication checks that acceptance, tests and both matrices use the same library.

The compare attempt (supervisor 1962789) was stopped after its five cfrac
repetitions failed the key-only RSS limit. Results and source/library are preserved
under `results/acceptance-compare.json` and `results/pass4-attempts/compare/` remotely.
A diagnostic smaps probe identified additional cold libc pages in keyed mode;
image initialization now avoids filename substring search. The sampled pointer
hash previously mapped 1 KiB aligned blocks within a page to just two sample
locks. It now uses the existing full integer mixer. Neither change is accepted yet.

The hash candidate passed targeted Linux and macOS correctness. Its short
comparison is running as PID 1976680. Two further local edits await Linux validation:
main-stack discovery uses a small address/protection prefix buffer and a narrow
hex parser; the raw-PC cache index mixes all bits so inner call sites do not vanish
from the index after rotations. Exact PC/count comparison still establishes cache
identity. These changes do not alter normalized site keys or sampling rate.

The cache diagnostic measured live/oracle time 1.2017 on Larson and 1.1751 on
xmalloc (one repetition, not acceptance). Cfrac live/oracle fell from 3.1907 to
1.5553 after mixing the raw-PC index. Key-only RSS remained 1.034735 of none.
The next candidate aliases ELF free directly, moves trace-only recursion work
out of the live free path, and releases Linux contexts through mimalloc's existing
thread teardown before heap abandonment. This removes a redundant pthread key and
its cold libc paths. The core-only patch now includes init.c; the vendor and plain
mimalloc remain unchanged. Targeted lifecycle validation precedes timing.

The lifecycle candidate passed targeted Linux and macOS tests, including retained
class tags and late TLS-destructor sampled frees. Its measurement is still running.
Further local changes avoid pthread_once in the already serialized loader
constructor (retained for the public none-mode lazy key API), and ask LTO to inline
the small mimalloc free path while keeping sampled/trace slow paths out of line.
The latter lets the negative filter and free reuse page lookup work; these edits
need their own Linux correctness and performance checks.

The broad `flatten` experiment was rejected: GCC pulled cold allocator paths into
free, increased its stack frame dramatically, and produced a strong C++ RTTI
reference that failed the C fault-injection executable. It was removed before any
benchmark from that candidate. The replacement exposes only the ordinary free
body with an already-resolved page, leaving baseline/vendor free unchanged.
Linux targeted tests passed for that helper plus a thread-local live-site hash
index; macOS passed for the helper before the index was added. The index removes
linear live-shard lookup after raw-cache collisions.

A five-repetition bootstrap diagnostic (cfrac controls only) still measured
none/mi time 1.01218, RSS 1.00000, key/none RSS 1.034735. External peak smaps
sampling showed only 16 KiB actual RSS difference in one paired diagnostic, despite
a much larger ru_maxrss difference; file faulting/accounting is significant at
this scale. The acceptance metric and threshold are unchanged. The parser for
the oracle table is the remaining keyed-only use of libc's general integer parser;
a checked narrow parser now awaits Linux validation, with overflow/truncation tests.

The pagefree diagnostic completed: Larson live/oracle 1.2048, xmalloc 1.1687,
so the 15% gate remained unmet. A 9,911-sample SIGPROF run attributed 33.5% to
capture, 9.8% to shim free and 2.1% to the core page-aware free. The next candidate
uses a one-multiply pointer hash, omits unused live capture outputs, and loads
model frames only on the live slow path. It also includes the checked table
parser. The shared core free body is now factored once, rather than duplicated.
Targeted Linux tests passed; compact diagnostic PID 2072047 is measuring it.

Disabling the negative sample filter worsened the diagnostic Larson live/oracle
ratio to 1.2839, so page filtering remains enabled. The new candidate keeps the
1/64 sample rate: power-of-two sampling uses the existing allocation count instead
of writing a separate countdown; arbitrary rates retain the countdown. Hot owner
fields fit the first cache line. Sample-table locks use a test-and-test-and-set
loop with processor pause and bounded spinning before sched_yield. Their acquire/
release ordering and exact pointer membership are unchanged. Direct ELF C++ new/
delete aliases remove forwarding jumps. Full supervisor 2101937 is validating
this candidate and will collect all 22 acceptance workloads before evaluating gates.

The sampler candidate passed targeted Linux and macOS suites. ELF PT_TLS is
**105 bytes** (0x69); free/delete and scalar/array new aliases resolve to identical
target addresses as intended. The full 22-workload, five-repetition acceptance is
running. Its input tables, traces, source, libraries, and targeted test log were
frozen before any later full make test under
`results/pass4-acceptance-inputs/sampler/` on the test machine. Local validation
records are in `results/pass4/validation/sampler-*`.

## Review disposition and historical evidence

The numerical audit was independently recomputed from the committed interim JSON:
`results/pass4/review-audit.json`. Warm-only heuristic score is 2.073610 (rounds
2.07); static/model are 2.056944/2.068057. The old prompt study's always-short
baseline is 55/92 = 59.78%, and the two-answer prompt has medium recall 0/31,
not 2/31. These are historical corrections, not new allocator results.

Archived cfrac cold decision logs and the archived oracle table now reproduce the
previously unverified accuracy numerators: static 68/175; model first 77/175,
rechecks 146/187, final-per-site 109/175. Every decision key matched truth, and
policy/model-only populations agree for these specific logs. Rechecks remain
repeated decisions over a different population, not independent sites. Evidence:
`results/pass4/review-evidence/` and `results/pass4/review-old-accuracy.jsonl`.
The accuracy tool now withholds scores on unmatched truth keys and supports the
fragmentation matrix's table directory; its regression test passed locally/remotely.

Sections 3/4: lazy small TLS, consistent default-heap controls, tagged reclaim,
thread-owned success counters, batched clock and lifetime-safe sampled owners are
implemented; performance acceptance is still pending. Section 6: heap failure,
failed-success accounting, byte-weighted survival-aware heuristic, in-place realloc,
class tags across exit, exact raw-cache identity and realpath routing have targeted
coverage. Linux dynamic image loading is explicitly unsupported (startup set only),
as the review allows. No general leak of mimalloc's normally deleted heaps is
claimed. The oracle is a prior-trace site majority, not a per-object or RSS bound.
Legacy microbenchmark, CPU/Vulkan speed and lifetime-distribution claims are not
reused as new evidence. The original report is preserved unchanged as an archive.

Current sampler acceptance has completed cfrac, espresso, barnes and Larson.
All four pass the memory/control gate; Larson live/oracle is **1.188301**, failing
1.15. The supervisor continues through all workloads to collect the full failure
set; this established failure will keep it from starting the full model matrices.

A local follow-up is under macOS validation and has NOT been synced to the running
Linux build: allocation counters are private non-atomic owner fields; exit reporting
reads only published totals when workers remain active. Finished/joined threads
still publish every success; active workers can leave up to 4,095 unmerged allocations
per thread/site. An admitted in-flight allocation no longer rereads the global close
flag after raw allocation. Two cold-path corrections avoid rewriting immutable
none-mode flags during lazy key initialization and reject an uninitialized default
heap before class-tag lookup. These edits require fresh Linux tests and acceptance.

The first 11 completed sampler acceptance workloads establish failures in xmalloc
none time (1.0473) and mstress key/none RSS (1.0526), in addition to live time on
Larson, Larson-sized and xmalloc (about 1.19). Mstress live time passes at 0.9583.
The matrix is still collecting the remaining workloads. The follow-up private-counter
candidate passed the macOS targeted suite. It additionally requests inlining of
only the small raw/page-aware free entry points (not recursive flattening), to
remove forwarding cost and expose shared page calculations to LTO. Linux validation
waits until the current acceptance finishes; no build is changed during timing.

The archived traces now also reproduce all six historical site-class counts with
zero oracle-table mismatches. `tools/trace_distribution.py` reproduces
`results/pass4/review-lifetimes.json` from the retained evidence. Actual object-byte
shares differ from whole-site majority shares: Larson is 2.433% short, 96.906%
medium, 0.661% long, whereas assigning every byte its site's majority class gives
99.9997% medium. Mstress has 0.907% actual short bytes despite zero short-majority
sites. Cfrac/espresso/Redis actual short shares are 99.963%/99.503%/99.814%; Barnes
is 100% long in this trace. These are cumulative requested bytes, not a bound on
resident fragmentation or page pinning.

The mstress key-RSS failure is not evidence of a 5% cache footprint: raw five-run
peaks span 502,096–534,580 KiB for key-only and 500,704–534,452 KiB for none, with
medians falling into different clusters. Thread scheduling and segment retention
are plausible contributors, not established causes. The specified five-run median
and 3% gate remain unchanged; this run is still a failure.

Thirteen workloads are complete. Rptest live/oracle passes at 1.0885, but none/mi
RSS is 1.0375 and fails; glibc-simple passes. No thresholds are changed. Report
publication now regenerates acceptance from its input matrix and requires each
inference audit to carry that matrix's SHA-256, preventing stale evidence reuse.
The obsolete countdown restart helper was removed locally.

The completed glibc-thread check fails none time at 1.0598; alloc-test1/N and
malloc-large pass. Mleak10 fails key-only/none RSS at 1.2011. Its mi peaks span
8,364–24,752 KiB, none 16,500–22,564 KiB, and key-only 16,508–24,776 KiB. The
thread-churn benchmark is highly variable in this run; that is recorded alongside
the failed gate, not used to discard observations or change acceptance.

## Pass 5 start — two classes (2026-10-10)

Read SPEC-TWOCLASS first; it supersedes the old strict performance gates. Remote
inspection found pass4.status=1 and no supervisor/finalizer still running. Acceptance
stopped in the Redis heuristic cold run with a live-decision failure, after earlier
workloads completed. Its JSON is retained locally at results/pass5/prior/acceptance-final.json;
remote raw logs and frozen sampler inputs remain untouched. Round4 promptlab is
running independently and has not been signaled or modified. Preserve all existing
uncommitted fixes, including the locally validated private-counter follow-up.

Implementation direction: exact fixed-threshold trace classes (short < S, long >= S
or never freed), default long, two tagged heaps, new cache identity, hand-written
program descriptions, and 64 KiB/1 MiB/16 MiB oracle sensitivity. Performance misses
will be measured and reported, not block the fragmentation/model matrices.

Initial two-class macOS targeted suite passes, including stress, trace consistency,
heap failure, retained tags through thread exit, late destructor frees, live rechecks,
replay coverage and budget integration. New tests check S exactly and S+1 separately.
Descriptions in descriptions/*.txt are hand-written from local source/docs, not model
outputs; they are code-side input and do not contain measured oracle labels. The old
Redis failure had no timeout or sidecar exception; errno was not recorded. The new
build records failure_errno to diagnose a recurrence without discarding the run.
A short two-class instrument/Redis diagnostic follows Linux targeted correctness.

The two-class diagnostic labels >99% of session bytes long at 1 MiB, as it does
cache entries: this workload's former medium/long separation is gone. One-rep
oracle RSS is essentially equal to key-only (and worse at 16-thread first idle).
This is a classification/instrument limitation, not evidence of failed page purging;
the earlier three-class positive control stays archived and is not reused as a
passing two-class instrument. Five repetitions and threshold sensitivity are next.

Redis diagnosis: failure_errno=111 (ECONNREFUSED), always after 574 decisions, no
sidecar error. live_init retained getenv storage for the socket path; Redis's
setproctitle overwrites original environment storage. Copying the path in init is
under test, with a regression that zeros the original JEVALLOC_SOCKET value in the
application. This is a pass-4 correctness fix retained in pass 5.

Prior sampler acceptance completed 21/22 workloads. Target misses: Larson live/oracle
1.1883, Larson-sized 1.1913, xmalloc 1.1946 (and none/mi time 1.0473), mstress key RSS
1.0526, rptest none RSS 1.0375, glibc-thread none time 1.0598, mleak10 key RSS 1.2011,
sh6bench none time 1.1018 and live/oracle 1.7720, sh8bench none time 1.0556 and
live/oracle 1.4846. Redis is incomplete. No more micro-tuning is planned: residual
capture/sampling work and noisy page/thread accounting are suspected contributors.

The Linux cache repeat test exposed a pre-existing exemplar instability: a site uses
four key frames, but rechecks took twelve model frames from whichever direct-mapped
cache entry last survived ASLR-dependent collisions. Counts/keys matched; outer
frames differed in one recheck. LiveSite now retains its first observed model stack
for all rechecks, matching trace site's first-observation convention. This avoids
cache layout changing the model's code evidence without changing key depth.

A final snapshot guard is queued before timing: concurrent sampled allocations/frees
can straddle the live totals read, so bound live/short partitions before subtracting
and rendering percentages (prevent unsigned wrap). This source-only fix has not
changed the active Linux full-test binary. The current full suite is allowed to
finish; the guarded build will receive its own full suite before headline timing.
All three fixed-socket Redis diagnostic runs completed without failures. The native
two-class prompt/tool tests also check legacy replay rejection and exact histogram
threshold reconstruction; non-power-of-two sensitivity requires retracing.

Instrument decision: preserve the requested 400,000-object server workload and its
actual fixed-S truth. Do not rescale it below S just to recreate the old positive
control. If the five-repetition nominal oracle fails to lower every idle RSS,
continue only with explicit --allow-negative-instrument, recording the negative
and its investigation. This is an interpretation of SPEC-TWOCLASS's direction to
finish the matrices, not a claim that the strict SPEC-FRAG instrument target passed.
The runner still requires complete instrument measurements on the identical library,
server binary, options and threshold before allowing this explicit continuation.

Prompt fitting now shortens source lines only; program description and runtime
percentages survive the 3,000-token budget. The former uniform line clipping could
cut off "kept longer"/"never freed" percentages. A tokenizer-mocked regression
checks that all three call markers and the final percentage survive. v2 remains
the matrix default; no-description and runtime-only variants are selectable in
jevd and both runners. Model probability maps must contain exactly short/long.

Prior acceptance audit: **zero inference overlaps in all 525 warm runs** (21 complete
workloads × 5 variants × 5 repetitions), with calibrated logger origin and matrix
SHA binding; JSON retained in results/pass5/prior. Final guard build is queued by
scripts/pass5-continue.sh after the currently running suite/instrument exits. It
archives those pre-guard outputs, rebuilds, reruns full correctness, then runs
instrument, fragbench, table sensitivity, regression and report via pass5-final.sh.
No performance threshold will be presented as passed when it failed.

The bounded-snapshot build passes the macOS targeted suite (results/pass5/validation/
macos-targeted-final.log). The Linux queue PID is 3909734; it waits for the first
suite/instrument, then reruns full tests on the final build. The final source and
prompt are frozen; only analysis/report helpers may change during measurement.

The sidecar can share a raw model-response cache for identical native two-class
payloads; the runners use results/pass5/model-cache. This avoids repeating exactly
the same initial code-only question for static-model and model, or Redis Mesh/drop.
Cached answers still consume each policy's 400-decision budget, replay/fills reserve
those slots, and original backend provenance remains attached. Decision schedules
and runtime requests remain separate per workload/policy. No old three-class cache
is imported. A unit test verifies both cache reuse and unchanged budget consumption.

The first full Linux suite passed all 22 workloads. Its five-repetition two-class
instrument is negative: first idle at 16 threads is oracle/key-only 1.0064; final
idle is 0.9892. Single-thread oracle/key-only is about 0.9992. Raw pre-guard results
are archived in remote results/pass5/prior/instrument-before-snapshot-guard.
The final guard build is now running its own full Linux suite.

A fragbench scope correction is necessary for the requested hard tier: the old
site-mixed TTL choices both survived past S, making it almost entirely long under
two classes. Site-mixed now has request-data TTL=0 payloads freed in the current
operation (50%), payloads released at the load drop (45%), and never-freed payloads
(5%, which is 10% of peak live payload slots). The same store_request_payload call
produces both short and long; per-site labels cannot separate them. Site-pure's
400,000-object workload is unchanged. Original mixed source is retained in
results/pass5/prior/server-sim-before-mixed-ttl.c. This corrects the hard-tier
contract; it does not rescale the negative site-pure instrument to manufacture a win.

Final source snapshot is retained remotely at results/pass5/source-final.tgz.
Validated-build candidate SHA-256: c15e9f5ca2e429f883b5e93db1b110d1fb44f443b6b16d07a713fc96e28f7195.
Server binary SHA-256: ad90ff9df10c0185c48702c1fdf83cab14ca3389a189a53a575f2904a6150330.
The Linux TLS segment is 97 bytes. The new mixed-tier phase smoke check passed;
its measured timing/RSS is diagnostic only because full correctness was concurrent.

## Final two-class validation and active matrices

Full Linux correctness PASSED on c15e9f5ca2e429f883b5e93db1b110d1fb44f443b6b16d07a713fc96e28f7195;
all 22 trace/random workload pairs plus live protocol, invalid class 2 rejection,
setproctitle/environment mutation, replay, exact S boundaries and budget tests.
Logs/manifest are copied to results/pass5/validation. Final instrument gate there
contains all four five-run comparisons and the matching server/library hashes.

Fragbench is now running, with twelve variants including all-short/all-long, five
interleaved repetitions and a 400-answer budget per cold model policy shared with
fills. Supervisor PID 3909734; progress results/pass5/stage.txt and results/bench.log.
It will run table sensitivity before the regression matrix. Preserve active code,
tables and native response caches. If interrupted after the supervisor stops, use
fragbench/run.py --name fragbench-two --allow-negative-instrument --resume to resume
only when fingerprints match; do not rerun the historical pass4 supervisor.

First completed two-class workload (site-pure-1, five repetitions): mi idle RSS
280.16 MiB; key-only 280.29; oracle 280.07; heuristic 282.88; static-model 283.10;
adaptive model 280.84. Uniform all-short/all-long are both about 280.30 MiB. Random
is 42.55 MiB, with wall time 1.161 s versus mi 1.087 s (common 1 s settle included).
This is an important positive control: two tagged heaps can release memory, but
S=1 MiB assigns both sessions and persistent cache entries long. Random happens to
separate them. The byte-majority lifetime oracle is emphatically not an RSS optimum.
These are complete workload medians, but the full matrix/audit is still pending.

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

Corrected site-pure-1 cold collection completed: static 183.8 s wall / 181.4 s
model HTTP, adaptive 318.9 s wall; zero decision errors. Four main lifetime paths
have distinct debug attribution and static labels match trace-majority truth.
Warm five-repetition collection has started. Report inputs now additionally audit
the instrument and verify every fragbench oracle table against exact trace labels;
actual object-byte distributions stay separate from whole-site majority assignments.

Corrected site-pure-1 block complete, 60 accepted warm runs; independent audit has
zero inference overlaps (snapshot in results/pass5/progress). Median final idle MiB:
mi 280.22, key 280.30, oracle 280.07, random 42.55, heuristic/static/model 282.87.
All-short/all-long both 280.29. Oracle labels merge sessions/cache; the seeded random
control separates them and releases pages, on this same corrected build. Model
labels for all four main allocation paths match oracle truth, without an RSS win.
Median model wall 1.141 s vs mi 1.087 s includes a common 1 s settle; CPU is 0.128
vs 0.086 s, about 1.49x. Report now states CPU ratios to avoid masking work behind
settle time. Five repetitions are descriptive, not an equivalence test. Workload
site-pure-16 cold collection is in progress; no complete-matrix claim yet.

Both corrected site-pure blocks complete (2/6 workloads). On 16 threads the observed
oracle/mi final-idle RSS ratio is 0.993; adaptive/heuristic 0.997, adaptive/oracle
1.026. Differences between adaptive and heuristic are small relative to run ranges.
The site-mixed-1 cold phases completed with 10 static and 23 adaptive decisions,
24.6 / 67.6 new HTTP seconds respectively, before warm collection. Existing identical
native payload answers are reused and still charged to the per-policy budget.

Site-mixed-1 complete (3/6). Median idle MiB: mi 144.71, oracle 144.97,
heuristic 146.50, static 146.88, adaptive 146.87. Adaptive/heuristic ratios:
RSS 1.003, wall 0.940, target CPU 0.637. Thus this workload shows a time/memory
tradeoff, not a fragmentation win. Main payload static/adaptive predictions remain
long, while its trace-majority class is short near the 50% boundary; do not assume
higher oracle-label accuracy optimizes execution cost. Mixed-16 cold passed with
10 static / 23 adaptive decisions; static reused all native payload answers and
adaptive added 79.2 HTTP seconds. Warm collection follows, then both Redis tasks.

All four corrected synthetic workloads complete (4/6). Mixed-16 ratios:
oracle/mi idle RSS 1.022; adaptive/heuristic RSS 1.008, wall 0.996, CPU 0.923;
adaptive/oracle RSS 1.104, CPU 0.774. Warm ranges remain in the matrix. Redis Mesh
trace has 621 sites, 100,951,634 short and 318,292,001 long requested bytes, with
99.964% prior-trace per-site classification ceiling. Heuristic cold passed with
653 decisions (model-free). Static model cold is active, limited to 400 answers;
startup-site coverage will be reported rather than assuming all sites were asked.

All 22 full-suite regression traces match their two-class oracle tables (zero label
mismatches). Distribution evidence is in local validation/regression-trace-distributions.json
and remote results/pass5/regression-trace-distributions.json. Actual short requested
byte shares: cfrac 99.96%, espresso 99.50%, barnes 0%, larson 2.43%, mstress 0.87%,
Redis 99.81%. These are actual object-byte sums, not the proportion of all bytes
assigned to a majority-short site. The full report regenerates both quantities.

## Pass 6 start — transient/permanent boundary (2026-10-10)

SPEC-PERMANENT.md takes precedence. Inspected the remote state first: supervisor
4044072 was collecting static-model Redis Mesh decisions. Signaled only that
supervisor and its descendants, confirmed they exited, and moved pass5,
fragbench-two, frag-instrument and bench.log into results/pass5-shortlong/ remotely.
The archive includes snapshots of this journal and RESULTS.md. Four completed
synthetic blocks remain the wrong-boundary finding; partial Redis is not complete.
The independent round4 prompt process is untouched. promptlab5.py and round5.sh
exist but no round5.log/results yet; use SPEC-PERMANENT's default wording.

Implementation: default transient; byte-majority ties transient. Trace schema 3
spools exact freed lifetimes in an unlinked file beside the trace output, then
classifies against final requested allocation volume with integer comparisons.
Permanent means never freed or strictly greater than 25/50/90 percent of total
volume (50 default). Never-freed-only and fixed-S controls are separately named.
Old traces and decision/replay caches are rejected, not silently relabelled.

Live heuristic: deterministic uniform reservoir of 128 sampled allocations per
site, across all its threads and its entire observed history. Each entry retains
birth allocation-clock, requested size, serial and whether it has been freed;
replacement is independent of survival. At a decision, take the count median age
of that reservoir (lower median for even counts), and consider entries strictly
older than it. With at least 16 entries and nonzero older bytes, permanent iff
20 * freed older bytes < total older bytes (strictly under 5%); otherwise transient.
No final-run length is used. Small/equal-age cohorts default transient. Reservoir
updates occur only on sampled allocations/frees, under a per-site lock; unsampled
paths are unchanged. Batched clocks and finite reservoirs remain approximations.

The first macOS targeted suite PASSED: cfrac trace/random, trace volume/sensitivity
accounting, fault injection, retained two-class tags, late destructor frees,
setproctitle socket preservation, sidecar timeout/invalid-class handling, deterministic
live requests, replay coverage and budget fallback. New default assertions now expect
transient. The full Linux suite is running before the instrument. The reservoir
adds only sampled-path work; its cost will be measured without a performance gate.

The reservoir transition integration also passes on Linux (sample rates 1 and 64):
one allocation PC transitions transient -> permanent while objects are held ->
transient after meaningful frees, including reuse of sampled pointer addresses.
The 25/50/90 trace fields agree with known fixture lifetimes; fixed-S exact-boundary
checks remain separate. No old short/long cache is imported.

Validation supervisor is remote PID 4063666. Queued successor PID 4072866 waits for
successful full correctness and the instrument. The instrument includes random,
requires oracle <= random at all four idle points, and oracle < half mimalloc's RSS.
A failed instrument stops the queue for investigation, without using the old
negative-instrument override. On success: site-pure sensitivity (25/50/90/never
plus three separately named fixed-S controls), then all six fragbench workloads,
then all 22 regression workloads, with five interleaved repetitions and 400 model
answers per cold policy including fills. Progress is results/pass6/stage.txt and
results/bench.log; status files are results/pass6/validate.status and pass6/status.

Before any pass-6 performance measurements, alloc-testN tracing exposed an avoidable
18 GB spool. Validation and the queued successor were stopped and their partial
outputs preserved in results/pass6/before-spool-pruning. Exact pruning now skips a
freed lifetime if it is <=25% of the current clock: the final clock cannot be smaller,
so the object cannot qualify at any supported permanent fraction. This preserves
all exact class results while eliminating immediate/short lifetime records. Full
correctness is restarted on the revised library; the earlier hash is superseded.
No performance run from that library is being reused.

Revised library SHA-256 is 0348583f88903b991810a4528f70a0013f591cde762406aa3a3fa80aa4413d95;
server-sim remains 2bd8e95865531b34a715b536d99b4519b93c85c516464724ff31ce4920f5a5c9.
Static TLS remains 97 bytes. The revised macOS targeted suite passes, including the
reservoir integration and fraction checks. Restarted validation PID 4074450 and
queued successor PID 4074451 supersede the earlier PIDs. During alloc-testN the
pruned spool was about 9 MB, versus over 18 GB in the interrupted unpruned trace;
this is a trace-resource diagnostic, not a headline performance result.

Full Linux correctness PASSED on 0348583f...: all 22 trace/random workload pairs,
live protocol and cross-thread ownership/destructor checks, reservoir transition
at sample rates 1/64, exact permanent sensitivity accounting, fixed-S boundaries,
replay coverage and model-budget integration. Results and logs are retained locally
in results/pass6/validation and remotely in results/pass6. Workload attribution and
genuine mixed-PC checks precede the new five-repetition instrument.

Pass 6 running: oracle permanent-threshold and fixed-S sensitivity

## Pass 6 instrument — passed

Five interleaved repetitions, exact final library and unchanged server-sim. Oracle is at or below random and below half of mimalloc at all four idle points. Independent audit: zero model-inference overlaps in 40 warm intervals.

| Workload | Cycle | mi MiB | Random MiB | Oracle MiB | Oracle saving vs mi |
|---|---:|---:|---:|---:|---:|
| site-pure-1 | 0 | 122.22 | 22.87 | 22.83 | 81.32% |
| site-pure-1 | 1 | 280.22 | 42.55 | 41.41 | 85.22% |
| site-pure-16 | 0 | 136.55 | 41.41 | 32.16 | 76.45% |
| site-pure-16 | 1 | 295.68 | 64.78 | 50.59 | 82.89% |

Sensitivity is running; full model fragbench and regression remain pending. This is oracle evidence, not model evidence. Raw observations, gate and audit are local results/pass6/instrument/.

Pass 6 running: full transient/permanent fragbench

## Pass 6 sensitivity — stable across permanent thresholds

All 80 warm intervals pass the independent inference audit (zero overlaps). Five-repetition median final-idle MiB:

| Workload | mi | >25% | >50% | >90% | Never freed | S=64 KiB | S=1 MiB | S=16 MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.22 | 41.32 | 41.37 | 41.37 | 41.35 | 280.07 | 280.07 | 280.07 |
| site-pure-16 | 297.54 | 50.91 | 51.50 | 51.65 | 51.68 | 292.85 | 292.99 | 293.33 |

The four dominant sites keep the same majority labels under all permanent thresholds. Fixed-S merges sessions and cache entries and recreates the wrong-boundary negative. Full fragbench is collecting fresh permanent-prompt decisions; no regression has started.

## First complete permanent-boundary workload — site-pure-1

Five repetitions for all 12 variants are complete; the partial-matrix snapshot has
zero inference overlaps. Final-idle MiB: mi 280.22, oracle 41.36, heuristic 228.77,
static-model 282.77, adaptive model 282.77. The oracle saves 238.86 MiB (85.2%).
Heuristic captures 21.5% of that saving; both model policies capture -1.1% (use
slightly more than mi). Adaptive/heuristic RSS is 1.236; adaptive target CPU is
0.858x heuristic, a time/memory tradeoff. Versus mi, static wall/CPU are 1.045/1.484;
adaptive 1.055/1.541; heuristic 1.074/1.795. Settle time is included in wall.

Static Clef calls create_session_state permanent with probability 0.582 versus
0.418 transient. All adaptive session decisions also remain permanent, including
its final recheck with 47% sampled bytes freed later. The heuristic changes to
transient at that recheck (all older-reservoir bytes had been freed), but earlier
session/cache mixing already pinned pages. No prompt tuning or label override is
applied to improve this negative model result. Site-pure-16 cold collection follows.
Raw snapshot, audit and full ranges are in results/pass6/progress/.

Site-pure-16 is complete (2/6 full fragbench blocks). Its medians: mi 295.49 MiB,
oracle 51.72, random 64.73, heuristic 251.57, static 298.29, adaptive 313.49.
Oracle saves 82.5%; heuristic captures 18.0% of oracle saving; static/adaptive
capture -1.1%/-7.4%. Static/adaptive/heuristic CPU ratios to mi are 1.079/1.111/1.184,
and wall ratios 1.014/1.021/1.027. All 120 completed synthetic warm intervals have
zero inference overlap. Five-run ranges remain in the partial summary; no equivalence
claim. Site-mixed-1 cold collection is active; no Redis or regression claim yet.

Site-mixed-1 complete and audited (3/6; 180 warm intervals, zero inference overlap).
Idle MiB: mi 144.71, oracle 144.97, heuristic 146.37, static/adaptive 148.88. Oracle
has no saving to capture. Adaptive/heuristic RSS is 1.017 but CPU is 0.629 and wall
0.939; adaptive/mi CPU is 0.848. The hard tier's whole-trace site-majority ceiling
is 96.47% of requested bytes, which emphatically does not imply an RSS improvement.
The final report also records the mixed payload site's own ceiling separately.

All four synthetic blocks are complete (4/6), with zero inference overlaps in 240 warm runs. Mixed-16 idle MiB (mi/oracle/heuristic/static/adaptive): 146.43/149.66/155.28/165.30/165.44. Oracle uses 2.2% more than mi; adaptive/heuristic RSS is 1.065, CPU 0.790, wall 0.984. Its whole-trace per-site ceiling is 96.47%. Redis Mesh static cold collection is active; no regression started.

Redis Mesh cold collection completed without failures. Static: 1,637.4 s wall,
1,615.0 s new HTTP time; adaptive: 22.2 s wall, zero new HTTP time (native payload
cache reuse). Both spend 400 answers on 400 startup sites, leave 221 sites unasked,
and leave about 97.97% of requested bytes unasked. Adaptive has zero model-backed
runtime rechecks before its budget is exhausted; do not interpret its row as evidence
for useful runtime-state input on this workload. Warm repetitions have started.

Redis Mesh completed and audited (5/6; 300 warm intervals with zero inference overlap). Idle MiB (mi/oracle/heuristic/static/adaptive): 181.91/187.99/230.92/194.83/192.85. Oracle uses 3.3% more RSS than mi. Adaptive/heuristic RSS 0.835, wall 1.033, CPU 1.049; adaptive/mi RSS 1.060, wall 1.120, CPU 1.225. No oracle saving exists to capture. Budget/zero-runtime-query qualification above applies. Redis peak-and-drop cold collection follows.

## Pass 6 measured report

# jevalloc — transient and permanent allocations

**Status: fragmentation complete; sensitivity or regression pending/incomplete.** Five interleaved warm repetitions per completed workload. Full Linux correctness passed on the measured library.

Library SHA-256: `0348583f88903b991810a4528f70a0013f591cde762406aa3a3fa80aa4413d95`.

Classes are **transient = 0** and **permanent = 1**. Permanent means never freed,
or alive for strictly more than half the program's final requested allocation volume.
The oracle chooses the byte-majority label per site from a prior trace, with ties
transient. Unknown sites default transient. Keys use four frames; model context
uses twelve named frames and three marked ±20-line source snippets plus hand-written
program descriptions. The oracle is a classification control, not an RSS optimum.

The prompt asks whether the object is released while the program keeps running or
kept for the rest of the program. Runtime rechecks add sampled requested-byte shares
freed quickly, freed later and not freed so far. Static-model omits runtime state
and never rechecks. Schema 3 and transient-permanent-v1 cache identities reject
short/long replay and response caches. No completed round-5 study was present at
start, so the wording in SPEC-PERMANENT is used.

The no-model heuristic maintains a deterministic uniform 128-entry reservoir of
sampled allocation births and free status per site. With at least 16 entries, take
the count median age (lower median for an even count), select strictly older entries,
and choose permanent if their freed requested bytes are strictly under 5% of their
total bytes. With no such evidence choose transient. Births stay in the reservoir
after free; replacement is independent of survival. It needs no final-run length.

## Fragmentation


Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.


| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 214.81 [214.81, 214.81] | 29.30 | 7.331 | 214.38 | 1.300 [1.296, 1.325] | 0.298 | 0.767 | 1.195 |
| site-pure-1 | mi | 280.22 [280.16, 280.22] | 29.30 | 9.563 | 279.99 | 1.088 [1.086, 1.090] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-none | 280.27 [280.21, 280.27] | 29.30 | 9.565 | 280.05 | 1.086 [1.083, 1.089] | 0.085 | 1.000 | 0.999 |
| site-pure-1 | jev-keyonly | 280.29 [280.29, 280.30] | 29.30 | 9.566 | 280.08 | 1.123 [1.121, 1.146] | 0.122 | 1.000 | 1.033 |
| site-pure-1 | jev-table:oracle | 41.36 [41.26, 41.38] | 29.30 | 1.411 | 213.81 | 1.226 [1.222, 1.227] | 0.225 | 0.148 | 1.128 |
| site-pure-1 | jev-table:random | 42.55 [42.49, 42.55] | 29.30 | 1.452 | 214.14 | 1.164 [1.162, 1.166] | 0.163 | 0.152 | 1.070 |
| site-pure-1 | jev-table:size | 280.30 [280.23, 280.30] | 29.30 | 9.566 | 280.07 | 1.120 [1.114, 1.126] | 0.119 | 1.000 | 1.030 |
| site-pure-1 | jev-table:all-transient | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.05 | 1.119 [1.118, 1.122] | 0.118 | 1.000 | 1.029 |
| site-pure-1 | jev-table:all-permanent | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.06 | 1.118 [1.116, 1.123] | 0.117 | 1.000 | 1.028 |
| site-pure-1 | jev-live:heuristic | 228.77 [228.76, 228.84] | 29.30 | 7.807 | 286.54 | 1.168 [1.166, 1.172] | 0.155 | 0.816 | 1.074 |
| site-pure-1 | jev-live:static-model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.55 | 1.136 [1.131, 1.137] | 0.128 | 1.009 | 1.045 |
| site-pure-1 | jev-live:model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.58 | 1.147 [1.140, 1.175] | 0.133 | 1.009 | 1.055 |

Oracle saves 238.86 MiB (85.2%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.045, CPU/mi 1.484.
Clef with runtime: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.055, CPU/mi 1.541.
No-model heuristic: 21.5% of the oracle saving; idle RSS/oracle 5.532, wall/mi 1.074, CPU/mi 1.795.

site-pure-1, observed medians: oracle beats mimalloc on idle RSS (0.148×). Live Clef does not beat the heuristic (1.236× RSS, 0.982× wall time, 0.858× target CPU time). Clef/oracle: 6.838× RSS, 0.935× wall, 0.591× CPU; heuristic/oracle: 5.532× RSS, 0.952× wall, 0.688× CPU. Clef/mi target CPU: 1.541×.

| site-pure-16 | sys | 215.46 [215.46, 215.46] | 29.33 | 7.347 | 214.12 | 1.111 [1.107, 1.116] | 1.086 | 0.729 | 1.067 |
| site-pure-16 | mi | 295.49 [294.45, 296.48] | 29.33 | 10.076 | 298.32 | 1.041 [1.040, 1.046] | 0.454 | 1.000 | 1.000 |
| site-pure-16 | jev-none | 295.61 [295.54, 296.72] | 29.33 | 10.080 | 298.34 | 1.042 [1.041, 1.066] | 0.467 | 1.000 | 1.001 |
| site-pure-16 | jev-keyonly | 295.82 [295.69, 297.80] | 29.33 | 10.087 | 298.54 | 1.047 [1.046, 1.048] | 0.519 | 1.001 | 1.006 |
| site-pure-16 | jev-table:oracle | 51.72 [51.54, 52.61] | 29.33 | 1.764 | 223.92 | 1.055 [1.052, 1.075] | 0.620 | 0.175 | 1.014 |
| site-pure-16 | jev-table:random | 64.73 [64.66, 64.79] | 29.33 | 2.207 | 234.49 | 1.050 [1.047, 1.053] | 0.561 | 0.219 | 1.009 |
| site-pure-16 | jev-table:size | 297.06 [294.93, 297.81] | 29.33 | 10.130 | 298.38 | 1.047 [1.045, 1.049] | 0.487 | 1.005 | 1.006 |
| site-pure-16 | jev-table:all-transient | 297.12 [295.63, 297.18] | 29.33 | 10.132 | 298.61 | 1.044 [1.042, 1.070] | 0.493 | 1.006 | 1.003 |
| site-pure-16 | jev-table:all-permanent | 296.44 [296.38, 297.18] | 29.33 | 10.109 | 298.54 | 1.047 [1.042, 1.072] | 0.518 | 1.003 | 1.005 |
| site-pure-16 | jev-live:heuristic | 251.57 [243.89, 253.02] | 29.33 | 8.579 | 286.67 | 1.069 [1.067, 1.080] | 0.538 | 0.851 | 1.027 |
| site-pure-16 | jev-live:static-model | 298.29 [296.67, 300.76] | 29.33 | 10.172 | 298.44 | 1.055 [1.055, 1.062] | 0.490 | 1.009 | 1.014 |
| site-pure-16 | jev-live:model | 313.49 [313.14, 316.99] | 29.33 | 10.690 | 316.89 | 1.063 [1.061, 1.066] | 0.505 | 1.061 | 1.021 |

Oracle saves 243.77 MiB (82.5%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 5.767, wall/mi 1.014, CPU/mi 1.079.
Clef with runtime: -7.4% of the oracle saving; idle RSS/oracle 6.061, wall/mi 1.021, CPU/mi 1.111.
No-model heuristic: 18.0% of the oracle saving; idle RSS/oracle 4.864, wall/mi 1.027, CPU/mi 1.184.

site-pure-16, observed medians: oracle beats mimalloc on idle RSS (0.175×). Live Clef does not beat the heuristic (1.246× RSS, 0.994× wall time, 0.939× target CPU time). Clef/oracle: 6.061× RSS, 1.007× wall, 0.814× CPU; heuristic/oracle: 4.864× RSS, 1.013× wall, 0.867× CPU. Clef/mi target CPU: 1.111×.

| site-mixed-1 | sys | 111.15 [111.14, 111.15] | 14.66 | 7.581 | 110.75 | 1.176 [1.176, 1.178] | 0.175 | 0.768 | 1.024 |
| site-mixed-1 | mi | 144.71 [144.70, 144.73] | 14.66 | 9.870 | 145.91 | 1.149 [1.147, 1.151] | 0.148 | 1.000 | 1.000 |
| site-mixed-1 | jev-none | 144.75 [144.74, 144.78] | 14.66 | 9.873 | 145.78 | 1.151 [1.149, 1.151] | 0.150 | 1.000 | 1.002 |
| site-mixed-1 | jev-keyonly | 144.79 [144.78, 144.80] | 14.66 | 9.875 | 145.77 | 1.187 [1.184, 1.188] | 0.186 | 1.001 | 1.033 |
| site-mixed-1 | jev-table:oracle | 144.97 [144.96, 144.97] | 14.66 | 9.887 | 145.86 | 1.181 [1.176, 1.209] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:random | 145.07 [145.05, 145.08] | 14.66 | 9.894 | 145.67 | 1.171 [1.166, 1.204] | 0.170 | 1.002 | 1.019 |
| site-mixed-1 | jev-table:size | 144.98 [144.96, 144.98] | 14.66 | 9.888 | 145.83 | 1.181 [1.178, 1.182] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:all-transient | 144.98 [144.97, 145.00] | 14.66 | 9.888 | 145.84 | 1.180 [1.179, 1.181] | 0.179 | 1.002 | 1.027 |
| site-mixed-1 | jev-table:all-permanent | 144.99 [144.98, 144.99] | 14.66 | 9.889 | 145.84 | 1.181 [1.176, 1.183] | 0.179 | 1.002 | 1.028 |
| site-mixed-1 | jev-live:heuristic | 146.37 [146.36, 146.39] | 14.66 | 9.983 | 146.39 | 1.212 [1.211, 1.213] | 0.200 | 1.011 | 1.055 |
| site-mixed-1 | jev-live:static-model | 148.88 [148.87, 148.88] | 14.66 | 10.154 | 148.71 | 1.131 [1.127, 1.133] | 0.125 | 1.029 | 0.984 |
| site-mixed-1 | jev-live:model | 148.88 [148.88, 148.89] | 14.66 | 10.154 | 148.68 | 1.138 [1.136, 1.162] | 0.126 | 1.029 | 0.991 |

site-mixed-1: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -0.26 MiB (-0.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.984, CPU/mi 0.839.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.991, CPU/mi 0.848.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.010, wall/mi 1.055, CPU/mi 1.348.

site-mixed-1, observed medians: oracle does not beat mimalloc on idle RSS (1.002×). Live Clef does not beat the heuristic (1.017× RSS, 0.939× wall time, 0.629× target CPU time). Clef/oracle: 1.027× RSS, 0.964× wall, 0.700× CPU; heuristic/oracle: 1.010× RSS, 1.026× wall, 1.113× CPU. Clef/mi target CPU: 0.848×.

| site-mixed-16 | sys | 111.79 [111.79, 111.80] | 14.73 | 7.588 | 110.62 | 1.067 [1.061, 1.091] | 0.555 | 0.763 | 1.019 |
| site-mixed-16 | mi | 146.43 [146.41, 146.44] | 14.73 | 9.939 | 148.45 | 1.047 [1.045, 1.050] | 0.441 | 1.000 | 1.000 |
| site-mixed-16 | jev-none | 146.49 [146.45, 146.51] | 14.73 | 9.943 | 149.29 | 1.051 [1.048, 1.075] | 0.441 | 1.000 | 1.003 |
| site-mixed-16 | jev-keyonly | 146.63 [146.56, 146.70] | 14.73 | 9.953 | 150.63 | 1.054 [1.052, 1.077] | 0.498 | 1.001 | 1.007 |
| site-mixed-16 | jev-table:oracle | 149.66 [149.66, 149.71] | 14.73 | 10.158 | 153.41 | 1.055 [1.051, 1.077] | 0.497 | 1.022 | 1.007 |
| site-mixed-16 | jev-table:random | 156.44 [156.20, 156.46] | 14.73 | 10.618 | 155.66 | 1.051 [1.046, 1.076] | 0.453 | 1.068 | 1.004 |
| site-mixed-16 | jev-table:size | 149.65 [149.64, 149.71] | 14.73 | 10.157 | 151.50 | 1.053 [1.052, 1.053] | 0.487 | 1.022 | 1.005 |
| site-mixed-16 | jev-table:all-transient | 149.68 [149.59, 149.76] | 14.73 | 10.160 | 152.38 | 1.053 [1.053, 1.055] | 0.494 | 1.022 | 1.006 |
| site-mixed-16 | jev-table:all-permanent | 149.67 [149.62, 149.69] | 14.73 | 10.159 | 153.47 | 1.052 [1.049, 1.078] | 0.483 | 1.022 | 1.005 |
| site-mixed-16 | jev-live:heuristic | 155.28 [154.82, 155.66] | 14.73 | 10.540 | 155.05 | 1.070 [1.069, 1.073] | 0.486 | 1.060 | 1.022 |
| site-mixed-16 | jev-live:static-model | 165.30 [164.73, 165.36] | 14.73 | 11.220 | 166.49 | 1.050 [1.048, 1.069] | 0.404 | 1.129 | 1.002 |
| site-mixed-16 | jev-live:model | 165.44 [165.22, 165.61] | 14.73 | 11.229 | 168.17 | 1.053 [1.051, 1.055] | 0.383 | 1.130 | 1.005 |

site-mixed-16: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -3.24 MiB (-2.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.104, wall/mi 1.002, CPU/mi 0.915.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.105, wall/mi 1.005, CPU/mi 0.869.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.038, wall/mi 1.022, CPU/mi 1.101.

site-mixed-16, observed medians: oracle does not beat mimalloc on idle RSS (1.022×). Live Clef does not beat the heuristic (1.065× RSS, 0.984× wall time, 0.790× target CPU time). Clef/oracle: 1.105× RSS, 0.998× wall, 0.771× CPU; heuristic/oracle: 1.038× RSS, 1.014× wall, 0.977× CPU. Clef/mi target CPU: 0.869×.

| redis-mesh | sys | 171.65 [170.02, 172.08] | 100.00 | 1.717 | 171.44 | 3.913 [3.897, 4.012] | 1.427 | 0.944 | 1.021 |
| redis-mesh | mi | 181.91 [178.00, 186.00] | 100.00 | 1.819 | 181.81 | 3.834 [3.816, 3.856] | 1.364 | 1.000 | 1.000 |
| redis-mesh | jev-none | 180.03 [177.95, 185.93] | 100.00 | 1.800 | 179.90 | 3.859 [3.847, 3.900] | 1.407 | 0.990 | 1.006 |
| redis-mesh | jev-keyonly | 185.99 [178.02, 186.07] | 100.00 | 1.860 | 185.83 | 3.983 [3.951, 4.025] | 1.581 | 1.022 | 1.039 |
| redis-mesh | jev-table:oracle | 187.99 [180.05, 188.06] | 100.00 | 1.880 | 187.87 | 3.942 [3.887, 3.947] | 1.483 | 1.033 | 1.028 |
| redis-mesh | jev-table:random | 185.95 [180.04, 186.08] | 100.00 | 1.860 | 185.82 | 3.931 [3.899, 3.946] | 1.487 | 1.022 | 1.025 |
| redis-mesh | jev-table:size | 186.00 [178.08, 186.11] | 100.00 | 1.860 | 185.76 | 3.904 [3.889, 3.938] | 1.482 | 1.022 | 1.018 |
| redis-mesh | jev-table:all-transient | 186.08 [178.00, 186.13] | 100.00 | 1.861 | 185.97 | 3.909 [3.894, 3.932] | 1.494 | 1.023 | 1.020 |
| redis-mesh | jev-table:all-permanent | 186.02 [177.64, 186.11] | 100.00 | 1.860 | 185.79 | 3.915 [3.899, 3.947] | 1.487 | 1.023 | 1.021 |
| redis-mesh | jev-live:heuristic | 230.92 [223.02, 230.96] | 100.00 | 2.309 | 230.42 | 4.157 [4.112, 4.292] | 1.593 | 1.269 | 1.084 |
| redis-mesh | jev-live:static-model | 194.83 [190.89, 194.88] | 100.00 | 1.948 | 194.54 | 4.276 [4.272, 4.387] | 1.677 | 1.071 | 1.115 |
| redis-mesh | jev-live:model | 192.85 [188.88, 194.88] | 100.00 | 1.929 | 194.55 | 4.294 [4.238, 4.452] | 1.671 | 1.060 | 1.120 |

Oracle saves -6.08 MiB (-3.3%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.036, wall/mi 1.115, CPU/mi 1.229.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.026, wall/mi 1.120, CPU/mi 1.225.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.228, wall/mi 1.084, CPU/mi 1.167.

redis-mesh, observed medians: oracle does not beat mimalloc on idle RSS (1.033×). Live Clef beats the heuristic (0.835× RSS, 1.033× wall time, 1.049× target CPU time). Clef/oracle: 1.026× RSS, 1.089× wall, 1.127× CPU; heuristic/oracle: 1.228× RSS, 1.055× wall, 1.074× CPU. Clef/mi target CPU: 1.225×.

| redis-drop | sys | 236.59 [236.52, 236.73] | 23.74 | 9.966 | 237.97 | 2.474 [2.462, 2.481] | 0.450 | 0.880 | 1.017 |
| redis-drop | mi | 268.85 [267.48, 271.46] | 27.26 | 9.863 | 275.93 | 2.433 [2.422, 2.446] | 0.326 | 1.000 | 1.000 |
| redis-drop | jev-none | 270.40 [269.28, 270.67] | 27.26 | 9.886 | 277.95 | 2.418 [2.413, 2.435] | 0.329 | 1.006 | 0.994 |
| redis-drop | jev-keyonly | 270.54 [268.99, 271.44] | 27.38 | 9.881 | 277.34 | 2.440 [2.438, 2.445] | 0.365 | 1.006 | 1.003 |
| redis-drop | jev-table:oracle | 270.86 [270.23, 271.04] | 27.38 | 9.898 | 278.00 | 2.429 [2.416, 2.436] | 0.358 | 1.007 | 0.999 |
| redis-drop | jev-table:random | 270.98 [270.27, 272.39] | 27.26 | 9.915 | 277.88 | 2.421 [2.413, 2.432] | 0.353 | 1.008 | 0.995 |
| redis-drop | jev-table:size | 270.87 [270.46, 271.64] | 27.26 | 9.922 | 277.99 | 2.430 [2.415, 2.447] | 0.356 | 1.008 | 0.999 |
| redis-drop | jev-table:all-transient | 270.83 [268.62, 271.92] | 27.26 | 9.903 | 277.91 | 2.418 [2.410, 2.435] | 0.359 | 1.007 | 0.994 |
| redis-drop | jev-table:all-permanent | 270.97 [270.43, 272.04] | 27.26 | 9.940 | 277.92 | 2.422 [2.412, 2.437] | 0.355 | 1.008 | 0.995 |
| redis-drop | jev-live:heuristic | 277.36 [276.12, 278.20] | 27.26 | 10.175 | 284.62 | 2.624 [2.585, 2.644] | 0.427 | 1.032 | 1.079 |
| redis-drop | jev-live:static-model | 279.62 [279.23, 279.76] | 27.26 | 10.246 | 286.64 | 2.639 [2.539, 2.652] | 0.422 | 1.040 | 1.085 |
| redis-drop | jev-live:model | 279.83 [279.04, 280.39] | 27.26 | 10.239 | 286.54 | 2.653 [2.595, 2.672] | 0.438 | 1.041 | 1.091 |

Oracle saves -2.01 MiB (-0.7%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.032, wall/mi 1.085, CPU/mi 1.297.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.033, wall/mi 1.091, CPU/mi 1.344.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.024, wall/mi 1.079, CPU/mi 1.313.

redis-drop, observed medians: oracle does not beat mimalloc on idle RSS (1.007×). Live Clef does not beat the heuristic (1.009× RSS, 1.011× wall time, 1.024× target CPU time). Clef/oracle: 1.033× RSS, 1.092× wall, 1.224× CPU; heuristic/oracle: 1.024× RSS, 1.080× wall, 1.196× CPU. Clef/mi target CPU: 1.344×.

Complete workloads: 6/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.

![Audited synthetic idle RSS](results/pass6/progress/synthetic-rss.png)
The figure shows the four synthetic workloads; Redis measurements are in the tables.
All peak, drop and idle phase medians are in [phases.md](results/pass6/phases.md); raw observations retain per-repetition values.
site-mixed-1: the single mixed payload site has a 89.40% byte-majority classification ceiling; the whole-workload ceiling is 96.47%. A fixed label cannot separate the payload's permanent and transient objects; neither percentage bounds attainable RSS.
site-mixed-16: the single mixed payload site has a 89.39% byte-majority classification ceiling; the whole-workload ceiling is 96.47%. A fixed label cannot separate the payload's permanent and transient objects; neither percentage bounds attainable RSS.
Actual object-byte lifetime shares and majority-site assignments are recorded separately in [trace-distributions.json](results/pass6/trace-distributions.json); every oracle table label matches its trace.

## Instrument and sensitivity

The transient/permanent instrument passes the requirement of oracle idle RSS at or below random and below half of plain mimalloc at every idle point. This is reported separately from correctness.

| Workload | Cycle | mi MiB | Random MiB | Oracle MiB | Oracle/mi | Oracle/random |
|---|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 0 | 122.219 | 22.867 | 22.832 | 0.1868 | 0.9985 |
| site-pure-1 | 1 | 280.219 | 42.555 | 41.406 | 0.1478 | 0.9730 |
| site-pure-16 | 0 | 136.551 | 41.410 | 32.164 | 0.2355 | 0.7767 |
| site-pure-16 | 1 | 295.676 | 64.777 | 50.590 | 0.1711 | 0.7810 |

The synthetic workload is unchanged from the corrected pass-5 version. Four
lifetime wrapper names remain distinct; seeded TTL data cannot split the mixed
allocation PC. The previous fixed-S oracle merged sessions with permanent cache
entries. That wrong-boundary finding is preserved in results/pass5-shortlong on
the test machine and the local results/pass5/progress snapshots: single-thread
mimalloc/oracle/random idle RSS was 280.22/280.07/42.55 MiB. All four synthetic
short/long blocks completed; Redis was stopped during cold decision collection.
Those measurements are historical and are not combined with this pass.

Historical wrong-boundary result (short/long at S=1 MiB), idle RSS MiB:

| Workload | mi | Fixed-S oracle | Random | Heuristic | Static Clef | Adaptive Clef |
|---|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.22 | 280.07 | 42.55 | 282.87 | 282.87 | 282.87 |
| site-pure-16 | 295.50 | 293.45 | 64.72 | 301.94 | 297.84 | 301.10 |
| site-mixed-1 | 144.71 | 144.97 | 145.06 | 146.50 | 146.88 | 146.87 |
| site-mixed-16 | 146.43 | 149.65 | 156.44 | 163.84 | 165.47 | 165.22 |
Oracle sensitivity: table-only controls, no model. Median final-idle RSS.

| Workload | >25% | >50% | >90% | Never freed only | S=64 KiB | S=1 MiB | S=16 MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 41.324 | 41.367 | 41.367 | 41.352 | 280.074 | 280.074 | 280.070 |
| site-pure-16 | 50.914 | 51.500 | 51.652 | 51.680 | 292.848 | 292.992 | 293.332 |

## Model budget and accuracy

Each cold model policy has 400 decisions shared with coverage fills. Identical native two-class model payloads share a raw response cache across policies/workloads; cached answers still consume decision slots, and original backend provenance is retained. Headline runs replay recorded answers with unchanged live instrumentation and no inference. Changed request states are logged: this measures the recorded policy, not whether the model would choose the same answers on warm state. Model server memory is excluded from allocator RSS.

| Workload | Policy | Cold decisions | Model rechecks | Cold unasked byte share | Warm unasked byte share |
|---|---|---:|---:|---:|---:|
| site-pure-1 | static-model | 11 | 0 | 0.00% | 0.00% |
| site-pure-1 | model | 27 | 16 | 0.00% | 0.00% |
| site-pure-16 | static-model | 11 | 0 | 0.00% | 0.00% |
| site-pure-16 | model | 26 | 15 | 0.00% | 0.00% |
| site-mixed-1 | static-model | 10 | 0 | 0.00% | 0.00% |
| site-mixed-1 | model | 23 | 13 | 0.00% | 0.00% |
| site-mixed-16 | static-model | 10 | 0 | 0.00% | 0.00% |
| site-mixed-16 | model | 23 | 13 | 0.00% | 0.00% |
| redis-mesh | static-model | 400 | 0 | 97.97% | 97.97% |
| redis-mesh | model | 400 | 0 | 97.97% | 97.97% |
| redis-drop | static-model | 400 | 0 | 99.12% | 99.12% |
| redis-drop | model | 400 | 0 | 99.12% | 99.12% |
No model-backed runtime recheck occurred in: redis-mesh, redis-drop. The adaptive label in those rows does not establish an effect of runtime input; inspect budget/coverage before attributing results to it.
Dominant site-pure decision histories, probabilities and observed free shares are in [site-decisions.json](results/pass6/site-decisions.json). Changes affect future allocations only; earlier permanent objects can continue pinning pages.
Among unasked cold-model bytes with matching prior-trace site truth, 73.6% belong to majority-transient sites. This aggregate supports transient as the classification fallback, not necessarily the memory-optimal fallback; the tested default remains transient. Policies and workloads contribute separate observations, not independent samples.

Cold accuracy populations and two-class confusion matrices are in [accuracy.json](results/pass6/accuracy.json). Rechecks are repeated decisions, not independent sites. Scores are withheld if any decision key lacks matching trace truth. Budget defaults are separated from model-backed answers.


## Cold inference and replay coverage cost

These costs are outside the warm timings. HTTP time includes queueing behind the independent prompt study; it is not isolated inference speed. Cached responses retain their original provenance. Coverage fills share the same 400-slot schedule budget.

| Workload | Policy | Final model slots | Cold HTTP s | Fill/probe HTTP s | Cold wall s | Warm changed requests |
|---|---|---:|---:|---:|---:|---:|
| site-pure-1 | static-model | 11 | 181.7 | 0.0 | 184.1 | 0 |
| site-pure-1 | model | 27 | 314.3 | 0.0 | 316.9 | 0 |
| site-pure-16 | static-model | 11 | 0.0 | 0.0 | 2.3 | 17 |
| site-pure-16 | model | 26 | 111.8 | 0.0 | 114.3 | 85 |
| site-mixed-1 | static-model | 10 | 30.6 | 0.0 | 32.8 | 0 |
| site-mixed-1 | model | 23 | 70.4 | 0.0 | 72.8 | 0 |
| site-mixed-16 | static-model | 10 | 0.0 | 0.0 | 2.2 | 11 |
| site-mixed-16 | model | 23 | 103.8 | 0.0 | 106.2 | 71 |
| redis-mesh | static-model | 400 | 1615.0 | 0.0 | 1637.4 | 28 |
| redis-mesh | model | 400 | 0.0 | 0.0 | 22.2 | 22 |
| redis-drop | static-model | 400 | 0.0 | 0.0 | 20.1 | 38 |
| redis-drop | model | 400 | 0.0 | 0.0 | 20.2 | 22 |

## mimalloc-bench regression

Regression has not completed; no aggregate claim is made. The interrupted three-class acceptance completed 21/22 workloads and is archived in results/pass5/prior.

## Measurement limits and interpretation

Unknown sites default transient because most requested allocation volume is
expected to be released. The all-transient/all-permanent controls are reported;
they do not directly test changing only the fallback for unseen sites. Neither
uniform control isolates the effect of changing that fallback alone.

Live lifetimes sample one allocation in 64 per thread/site. Success counters merge
every 4,096 allocations, at decisions and thread exit. Replay retains the same
instrumentation. Batched clocks, finite reservoirs and concurrent snapshots are
approximate; active workers can leave 4,095 unmerged allocations per thread/site
at exit. Retired sampled owners survive until their final cross-thread free.

Synthetic live bytes are requested bytes; Redis used_memory includes metadata and
usable-size effects. Every fragmentation variant uses MIMALLOC_PURGE_DELAY=0,
MIMALLOC_ARENA_PURGE_MULT=1 and MIMALLOC_PURGE_DECOMMITS=1, with the same settle/pulse.
Oracle-saving capture is (mi RSS - policy RSS)/(mi RSS - oracle RSS), undefined when the oracle saves no memory. It may be negative or exceed 100%; a small oracle saving makes the fraction unstable. Five repetitions show medians and ranges, not statistical equivalence. Raw phase,
stdout/stderr, replay/fill and inference-audit records remain on the test machine.

The pass-4 and pass-5 fixes are preserved, including copying the sidecar socket path
before applications can overwrite environment storage (Redis setproctitle), and
retaining each site's first model stack so cache collisions cannot change recheck
source context. Linux supports startup images only; dynamic loading/unloading and
post-fork synchronization remain outside the validated set.


Pass 6 running: mimalloc-bench regression

## Pass 6 measured report

# jevalloc — transient and permanent allocations

**Status: fragmentation and sensitivity complete; regression pending/incomplete.** Five interleaved warm repetitions per completed workload. Full Linux correctness passed on the measured library.

Library SHA-256: `0348583f88903b991810a4528f70a0013f591cde762406aa3a3fa80aa4413d95`.

Classes are **transient = 0** and **permanent = 1**. Permanent means never freed,
or alive for strictly more than half the program's final requested allocation volume.
The oracle chooses the byte-majority label per site from a prior trace, with ties
transient. Unknown sites default transient. Keys use four frames; model context
uses twelve named frames and three marked ±20-line source snippets plus hand-written
program descriptions. The oracle is a classification control, not an RSS optimum.

The prompt asks whether the object is released while the program keeps running or
kept for the rest of the program. Runtime rechecks add sampled requested-byte shares
freed quickly, freed later and not freed so far. Static-model omits runtime state
and never rechecks. Schema 3 and transient-permanent-v1 cache identities reject
short/long replay and response caches. No completed round-5 study was present at
start, so the wording in SPEC-PERMANENT is used.

The no-model heuristic maintains a deterministic uniform 128-entry reservoir of
sampled allocation births and free status per site. With at least 16 entries, take
the count median age (lower median for an even count), select strictly older entries,
and choose permanent if their freed requested bytes are strictly under 5% of their
total bytes. With no such evidence choose transient. Births stay in the reservoir
after free; replacement is independent of survival. It needs no final-run length.

## Fragmentation


| Workload | mi idle MiB | Oracle | Heuristic | Code-only Clef | Runtime Clef | Oracle saving vs mi |
|---|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.22 | 41.36 | 228.77 | 282.77 | 282.77 | 85.2% |
| site-pure-16 | 295.49 | 51.72 | 251.57 | 298.29 | 313.49 | 82.5% |
| site-mixed-1 | 144.71 | 144.97 | 146.37 | 148.88 | 148.88 | -0.2% |
| site-mixed-16 | 146.43 | 149.66 | 155.28 | 165.30 | 165.44 | -2.2% |
| redis-mesh | 181.91 | 187.99 | 230.92 | 194.83 | 192.85 | -3.3% |
| redis-drop | 268.85 | 270.86 | 277.36 | 279.62 | 279.83 | -0.7% |


Warm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.


| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | sys | 214.81 [214.81, 214.81] | 29.30 | 7.331 | 214.38 | 1.300 [1.296, 1.325] | 0.298 | 0.767 | 1.195 |
| site-pure-1 | mi | 280.22 [280.16, 280.22] | 29.30 | 9.563 | 279.99 | 1.088 [1.086, 1.090] | 0.086 | 1.000 | 1.000 |
| site-pure-1 | jev-none | 280.27 [280.21, 280.27] | 29.30 | 9.565 | 280.05 | 1.086 [1.083, 1.089] | 0.085 | 1.000 | 0.999 |
| site-pure-1 | jev-keyonly | 280.29 [280.29, 280.30] | 29.30 | 9.566 | 280.08 | 1.123 [1.121, 1.146] | 0.122 | 1.000 | 1.033 |
| site-pure-1 | jev-table:oracle | 41.36 [41.26, 41.38] | 29.30 | 1.411 | 213.81 | 1.226 [1.222, 1.227] | 0.225 | 0.148 | 1.128 |
| site-pure-1 | jev-table:random | 42.55 [42.49, 42.55] | 29.30 | 1.452 | 214.14 | 1.164 [1.162, 1.166] | 0.163 | 0.152 | 1.070 |
| site-pure-1 | jev-table:size | 280.30 [280.23, 280.30] | 29.30 | 9.566 | 280.07 | 1.120 [1.114, 1.126] | 0.119 | 1.000 | 1.030 |
| site-pure-1 | jev-table:all-transient | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.05 | 1.119 [1.118, 1.122] | 0.118 | 1.000 | 1.029 |
| site-pure-1 | jev-table:all-permanent | 280.30 [280.29, 280.30] | 29.30 | 9.566 | 280.06 | 1.118 [1.116, 1.123] | 0.117 | 1.000 | 1.028 |
| site-pure-1 | jev-live:heuristic | 228.77 [228.76, 228.84] | 29.30 | 7.807 | 286.54 | 1.168 [1.166, 1.172] | 0.155 | 0.816 | 1.074 |
| site-pure-1 | jev-live:static-model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.55 | 1.136 [1.131, 1.137] | 0.128 | 1.009 | 1.045 |
| site-pure-1 | jev-live:model | 282.77 [282.77, 282.78] | 29.30 | 9.650 | 282.58 | 1.147 [1.140, 1.175] | 0.133 | 1.009 | 1.055 |

Oracle saves 238.86 MiB (85.2%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.045, CPU/mi 1.484.
Clef with runtime: -1.1% of the oracle saving; idle RSS/oracle 6.838, wall/mi 1.055, CPU/mi 1.541.
No-model heuristic: 21.5% of the oracle saving; idle RSS/oracle 5.532, wall/mi 1.074, CPU/mi 1.795.

site-pure-1, observed medians: oracle beats mimalloc on idle RSS (0.148×). Live Clef does not beat the heuristic (1.236× RSS, 0.982× wall time, 0.858× target CPU time). Clef/oracle: 6.838× RSS, 0.935× wall, 0.591× CPU; heuristic/oracle: 5.532× RSS, 0.952× wall, 0.688× CPU. Clef/mi target CPU: 1.541×.

| site-pure-16 | sys | 215.46 [215.46, 215.46] | 29.33 | 7.347 | 214.12 | 1.111 [1.107, 1.116] | 1.086 | 0.729 | 1.067 |
| site-pure-16 | mi | 295.49 [294.45, 296.48] | 29.33 | 10.076 | 298.32 | 1.041 [1.040, 1.046] | 0.454 | 1.000 | 1.000 |
| site-pure-16 | jev-none | 295.61 [295.54, 296.72] | 29.33 | 10.080 | 298.34 | 1.042 [1.041, 1.066] | 0.467 | 1.000 | 1.001 |
| site-pure-16 | jev-keyonly | 295.82 [295.69, 297.80] | 29.33 | 10.087 | 298.54 | 1.047 [1.046, 1.048] | 0.519 | 1.001 | 1.006 |
| site-pure-16 | jev-table:oracle | 51.72 [51.54, 52.61] | 29.33 | 1.764 | 223.92 | 1.055 [1.052, 1.075] | 0.620 | 0.175 | 1.014 |
| site-pure-16 | jev-table:random | 64.73 [64.66, 64.79] | 29.33 | 2.207 | 234.49 | 1.050 [1.047, 1.053] | 0.561 | 0.219 | 1.009 |
| site-pure-16 | jev-table:size | 297.06 [294.93, 297.81] | 29.33 | 10.130 | 298.38 | 1.047 [1.045, 1.049] | 0.487 | 1.005 | 1.006 |
| site-pure-16 | jev-table:all-transient | 297.12 [295.63, 297.18] | 29.33 | 10.132 | 298.61 | 1.044 [1.042, 1.070] | 0.493 | 1.006 | 1.003 |
| site-pure-16 | jev-table:all-permanent | 296.44 [296.38, 297.18] | 29.33 | 10.109 | 298.54 | 1.047 [1.042, 1.072] | 0.518 | 1.003 | 1.005 |
| site-pure-16 | jev-live:heuristic | 251.57 [243.89, 253.02] | 29.33 | 8.579 | 286.67 | 1.069 [1.067, 1.080] | 0.538 | 0.851 | 1.027 |
| site-pure-16 | jev-live:static-model | 298.29 [296.67, 300.76] | 29.33 | 10.172 | 298.44 | 1.055 [1.055, 1.062] | 0.490 | 1.009 | 1.014 |
| site-pure-16 | jev-live:model | 313.49 [313.14, 316.99] | 29.33 | 10.690 | 316.89 | 1.063 [1.061, 1.066] | 0.505 | 1.061 | 1.021 |

Oracle saves 243.77 MiB (82.5%) against plain mimalloc.
Code-only Clef: -1.1% of the oracle saving; idle RSS/oracle 5.767, wall/mi 1.014, CPU/mi 1.079.
Clef with runtime: -7.4% of the oracle saving; idle RSS/oracle 6.061, wall/mi 1.021, CPU/mi 1.111.
No-model heuristic: 18.0% of the oracle saving; idle RSS/oracle 4.864, wall/mi 1.027, CPU/mi 1.184.

site-pure-16, observed medians: oracle beats mimalloc on idle RSS (0.175×). Live Clef does not beat the heuristic (1.246× RSS, 0.994× wall time, 0.939× target CPU time). Clef/oracle: 6.061× RSS, 1.007× wall, 0.814× CPU; heuristic/oracle: 4.864× RSS, 1.013× wall, 0.867× CPU. Clef/mi target CPU: 1.111×.

| site-mixed-1 | sys | 111.15 [111.14, 111.15] | 14.66 | 7.581 | 110.75 | 1.176 [1.176, 1.178] | 0.175 | 0.768 | 1.024 |
| site-mixed-1 | mi | 144.71 [144.70, 144.73] | 14.66 | 9.870 | 145.91 | 1.149 [1.147, 1.151] | 0.148 | 1.000 | 1.000 |
| site-mixed-1 | jev-none | 144.75 [144.74, 144.78] | 14.66 | 9.873 | 145.78 | 1.151 [1.149, 1.151] | 0.150 | 1.000 | 1.002 |
| site-mixed-1 | jev-keyonly | 144.79 [144.78, 144.80] | 14.66 | 9.875 | 145.77 | 1.187 [1.184, 1.188] | 0.186 | 1.001 | 1.033 |
| site-mixed-1 | jev-table:oracle | 144.97 [144.96, 144.97] | 14.66 | 9.887 | 145.86 | 1.181 [1.176, 1.209] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:random | 145.07 [145.05, 145.08] | 14.66 | 9.894 | 145.67 | 1.171 [1.166, 1.204] | 0.170 | 1.002 | 1.019 |
| site-mixed-1 | jev-table:size | 144.98 [144.96, 144.98] | 14.66 | 9.888 | 145.83 | 1.181 [1.178, 1.182] | 0.180 | 1.002 | 1.028 |
| site-mixed-1 | jev-table:all-transient | 144.98 [144.97, 145.00] | 14.66 | 9.888 | 145.84 | 1.180 [1.179, 1.181] | 0.179 | 1.002 | 1.027 |
| site-mixed-1 | jev-table:all-permanent | 144.99 [144.98, 144.99] | 14.66 | 9.889 | 145.84 | 1.181 [1.176, 1.183] | 0.179 | 1.002 | 1.028 |
| site-mixed-1 | jev-live:heuristic | 146.37 [146.36, 146.39] | 14.66 | 9.983 | 146.39 | 1.212 [1.211, 1.213] | 0.200 | 1.011 | 1.055 |
| site-mixed-1 | jev-live:static-model | 148.88 [148.87, 148.88] | 14.66 | 10.154 | 148.71 | 1.131 [1.127, 1.133] | 0.125 | 1.029 | 0.984 |
| site-mixed-1 | jev-live:model | 148.88 [148.88, 148.89] | 14.66 | 10.154 | 148.68 | 1.138 [1.136, 1.162] | 0.126 | 1.029 | 0.991 |

site-mixed-1: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -0.26 MiB (-0.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.984, CPU/mi 0.839.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.027, wall/mi 0.991, CPU/mi 0.848.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.010, wall/mi 1.055, CPU/mi 1.348.

site-mixed-1, observed medians: oracle does not beat mimalloc on idle RSS (1.002×). Live Clef does not beat the heuristic (1.017× RSS, 0.939× wall time, 0.629× target CPU time). Clef/oracle: 1.027× RSS, 0.964× wall, 0.700× CPU; heuristic/oracle: 1.010× RSS, 1.026× wall, 1.113× CPU. Clef/mi target CPU: 0.848×.

| site-mixed-16 | sys | 111.79 [111.79, 111.80] | 14.73 | 7.588 | 110.62 | 1.067 [1.061, 1.091] | 0.555 | 0.763 | 1.019 |
| site-mixed-16 | mi | 146.43 [146.41, 146.44] | 14.73 | 9.939 | 148.45 | 1.047 [1.045, 1.050] | 0.441 | 1.000 | 1.000 |
| site-mixed-16 | jev-none | 146.49 [146.45, 146.51] | 14.73 | 9.943 | 149.29 | 1.051 [1.048, 1.075] | 0.441 | 1.000 | 1.003 |
| site-mixed-16 | jev-keyonly | 146.63 [146.56, 146.70] | 14.73 | 9.953 | 150.63 | 1.054 [1.052, 1.077] | 0.498 | 1.001 | 1.007 |
| site-mixed-16 | jev-table:oracle | 149.66 [149.66, 149.71] | 14.73 | 10.158 | 153.41 | 1.055 [1.051, 1.077] | 0.497 | 1.022 | 1.007 |
| site-mixed-16 | jev-table:random | 156.44 [156.20, 156.46] | 14.73 | 10.618 | 155.66 | 1.051 [1.046, 1.076] | 0.453 | 1.068 | 1.004 |
| site-mixed-16 | jev-table:size | 149.65 [149.64, 149.71] | 14.73 | 10.157 | 151.50 | 1.053 [1.052, 1.053] | 0.487 | 1.022 | 1.005 |
| site-mixed-16 | jev-table:all-transient | 149.68 [149.59, 149.76] | 14.73 | 10.160 | 152.38 | 1.053 [1.053, 1.055] | 0.494 | 1.022 | 1.006 |
| site-mixed-16 | jev-table:all-permanent | 149.67 [149.62, 149.69] | 14.73 | 10.159 | 153.47 | 1.052 [1.049, 1.078] | 0.483 | 1.022 | 1.005 |
| site-mixed-16 | jev-live:heuristic | 155.28 [154.82, 155.66] | 14.73 | 10.540 | 155.05 | 1.070 [1.069, 1.073] | 0.486 | 1.060 | 1.022 |
| site-mixed-16 | jev-live:static-model | 165.30 [164.73, 165.36] | 14.73 | 11.220 | 166.49 | 1.050 [1.048, 1.069] | 0.404 | 1.129 | 1.002 |
| site-mixed-16 | jev-live:model | 165.44 [165.22, 165.61] | 14.73 | 11.229 | 168.17 | 1.053 [1.051, 1.055] | 0.383 | 1.130 | 1.005 |

site-mixed-16: a fixed per-site majority label classifies 96.47% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.


Oracle saves -3.24 MiB (-2.2%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.104, wall/mi 1.002, CPU/mi 0.915.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.105, wall/mi 1.005, CPU/mi 0.869.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.038, wall/mi 1.022, CPU/mi 1.101.

site-mixed-16, observed medians: oracle does not beat mimalloc on idle RSS (1.022×). Live Clef does not beat the heuristic (1.065× RSS, 0.984× wall time, 0.790× target CPU time). Clef/oracle: 1.105× RSS, 0.998× wall, 0.771× CPU; heuristic/oracle: 1.038× RSS, 1.014× wall, 0.977× CPU. Clef/mi target CPU: 0.869×.

| redis-mesh | sys | 171.65 [170.02, 172.08] | 100.00 | 1.717 | 171.44 | 3.913 [3.897, 4.012] | 1.427 | 0.944 | 1.021 |
| redis-mesh | mi | 181.91 [178.00, 186.00] | 100.00 | 1.819 | 181.81 | 3.834 [3.816, 3.856] | 1.364 | 1.000 | 1.000 |
| redis-mesh | jev-none | 180.03 [177.95, 185.93] | 100.00 | 1.800 | 179.90 | 3.859 [3.847, 3.900] | 1.407 | 0.990 | 1.006 |
| redis-mesh | jev-keyonly | 185.99 [178.02, 186.07] | 100.00 | 1.860 | 185.83 | 3.983 [3.951, 4.025] | 1.581 | 1.022 | 1.039 |
| redis-mesh | jev-table:oracle | 187.99 [180.05, 188.06] | 100.00 | 1.880 | 187.87 | 3.942 [3.887, 3.947] | 1.483 | 1.033 | 1.028 |
| redis-mesh | jev-table:random | 185.95 [180.04, 186.08] | 100.00 | 1.860 | 185.82 | 3.931 [3.899, 3.946] | 1.487 | 1.022 | 1.025 |
| redis-mesh | jev-table:size | 186.00 [178.08, 186.11] | 100.00 | 1.860 | 185.76 | 3.904 [3.889, 3.938] | 1.482 | 1.022 | 1.018 |
| redis-mesh | jev-table:all-transient | 186.08 [178.00, 186.13] | 100.00 | 1.861 | 185.97 | 3.909 [3.894, 3.932] | 1.494 | 1.023 | 1.020 |
| redis-mesh | jev-table:all-permanent | 186.02 [177.64, 186.11] | 100.00 | 1.860 | 185.79 | 3.915 [3.899, 3.947] | 1.487 | 1.023 | 1.021 |
| redis-mesh | jev-live:heuristic | 230.92 [223.02, 230.96] | 100.00 | 2.309 | 230.42 | 4.157 [4.112, 4.292] | 1.593 | 1.269 | 1.084 |
| redis-mesh | jev-live:static-model | 194.83 [190.89, 194.88] | 100.00 | 1.948 | 194.54 | 4.276 [4.272, 4.387] | 1.677 | 1.071 | 1.115 |
| redis-mesh | jev-live:model | 192.85 [188.88, 194.88] | 100.00 | 1.929 | 194.55 | 4.294 [4.238, 4.452] | 1.671 | 1.060 | 1.120 |

Oracle saves -6.08 MiB (-3.3%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.036, wall/mi 1.115, CPU/mi 1.229.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.026, wall/mi 1.120, CPU/mi 1.225.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.228, wall/mi 1.084, CPU/mi 1.167.

redis-mesh, observed medians: oracle does not beat mimalloc on idle RSS (1.033×). Live Clef beats the heuristic (0.835× RSS, 1.033× wall time, 1.049× target CPU time). Clef/oracle: 1.026× RSS, 1.089× wall, 1.127× CPU; heuristic/oracle: 1.228× RSS, 1.055× wall, 1.074× CPU. Clef/mi target CPU: 1.225×.

| redis-drop | sys | 236.59 [236.52, 236.73] | 23.74 | 9.966 | 237.97 | 2.474 [2.462, 2.481] | 0.450 | 0.880 | 1.017 |
| redis-drop | mi | 268.85 [267.48, 271.46] | 27.26 | 9.863 | 275.93 | 2.433 [2.422, 2.446] | 0.326 | 1.000 | 1.000 |
| redis-drop | jev-none | 270.40 [269.28, 270.67] | 27.26 | 9.886 | 277.95 | 2.418 [2.413, 2.435] | 0.329 | 1.006 | 0.994 |
| redis-drop | jev-keyonly | 270.54 [268.99, 271.44] | 27.38 | 9.881 | 277.34 | 2.440 [2.438, 2.445] | 0.365 | 1.006 | 1.003 |
| redis-drop | jev-table:oracle | 270.86 [270.23, 271.04] | 27.38 | 9.898 | 278.00 | 2.429 [2.416, 2.436] | 0.358 | 1.007 | 0.999 |
| redis-drop | jev-table:random | 270.98 [270.27, 272.39] | 27.26 | 9.915 | 277.88 | 2.421 [2.413, 2.432] | 0.353 | 1.008 | 0.995 |
| redis-drop | jev-table:size | 270.87 [270.46, 271.64] | 27.26 | 9.922 | 277.99 | 2.430 [2.415, 2.447] | 0.356 | 1.008 | 0.999 |
| redis-drop | jev-table:all-transient | 270.83 [268.62, 271.92] | 27.26 | 9.903 | 277.91 | 2.418 [2.410, 2.435] | 0.359 | 1.007 | 0.994 |
| redis-drop | jev-table:all-permanent | 270.97 [270.43, 272.04] | 27.26 | 9.940 | 277.92 | 2.422 [2.412, 2.437] | 0.355 | 1.008 | 0.995 |
| redis-drop | jev-live:heuristic | 277.36 [276.12, 278.20] | 27.26 | 10.175 | 284.62 | 2.624 [2.585, 2.644] | 0.427 | 1.032 | 1.079 |
| redis-drop | jev-live:static-model | 279.62 [279.23, 279.76] | 27.26 | 10.246 | 286.64 | 2.639 [2.539, 2.652] | 0.422 | 1.040 | 1.085 |
| redis-drop | jev-live:model | 279.83 [279.04, 280.39] | 27.26 | 10.239 | 286.54 | 2.653 [2.595, 2.672] | 0.438 | 1.041 | 1.091 |

Oracle saves -2.01 MiB (-0.7%) against plain mimalloc.
Code-only Clef: capture undefined because the oracle saves no memory; idle RSS/oracle 1.032, wall/mi 1.085, CPU/mi 1.297.
Clef with runtime: capture undefined because the oracle saves no memory; idle RSS/oracle 1.033, wall/mi 1.091, CPU/mi 1.344.
No-model heuristic: capture undefined because the oracle saves no memory; idle RSS/oracle 1.024, wall/mi 1.079, CPU/mi 1.313.

redis-drop, observed medians: oracle does not beat mimalloc on idle RSS (1.007×). Live Clef does not beat the heuristic (1.009× RSS, 1.011× wall time, 1.024× target CPU time). Clef/oracle: 1.033× RSS, 1.092× wall, 1.224× CPU; heuristic/oracle: 1.024× RSS, 1.080× wall, 1.196× CPU. Clef/mi target CPU: 1.344×.

Complete workloads: 6/6. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.

![Audited synthetic idle RSS](results/pass6/progress/synthetic-rss.png)
The figure shows the four synthetic workloads; Redis measurements are in the tables.
All peak, drop and idle phase medians are in [phases.md](results/pass6/phases.md); raw observations retain per-repetition values.
site-mixed-1: the single mixed payload site has a 89.40% byte-majority classification ceiling; the whole-workload ceiling is 96.47%. A fixed label cannot separate the payload's permanent and transient objects; neither percentage bounds attainable RSS.
site-mixed-16: the single mixed payload site has a 89.39% byte-majority classification ceiling; the whole-workload ceiling is 96.47%. A fixed label cannot separate the payload's permanent and transient objects; neither percentage bounds attainable RSS.
Actual object-byte lifetime shares and majority-site assignments are recorded separately in [trace-distributions.json](results/pass6/trace-distributions.json); every oracle table label matches its trace.

## Instrument and sensitivity

The transient/permanent instrument passes the requirement of oracle idle RSS at or below random and below half of plain mimalloc at every idle point. This is reported separately from correctness.

| Workload | Cycle | mi MiB | Random MiB | Oracle MiB | Oracle/mi | Oracle/random |
|---|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 0 | 122.219 | 22.867 | 22.832 | 0.1868 | 0.9985 |
| site-pure-1 | 1 | 280.219 | 42.555 | 41.406 | 0.1478 | 0.9730 |
| site-pure-16 | 0 | 136.551 | 41.410 | 32.164 | 0.2355 | 0.7767 |
| site-pure-16 | 1 | 295.676 | 64.777 | 50.590 | 0.1711 | 0.7810 |

The synthetic workload is unchanged from the corrected pass-5 version. Four
lifetime wrapper names remain distinct; seeded TTL data cannot split the mixed
allocation PC. The previous fixed-S oracle merged sessions with permanent cache
entries. That wrong-boundary finding is preserved in results/pass5-shortlong on
the test machine and the local results/pass5/progress snapshots: single-thread
mimalloc/oracle/random idle RSS was 280.22/280.07/42.55 MiB. All four synthetic
short/long blocks completed; Redis was stopped during cold decision collection.
Those measurements are historical and are not combined with this pass.

Historical wrong-boundary result (short/long at S=1 MiB), idle RSS MiB:

| Workload | mi | Fixed-S oracle | Random | Heuristic | Static Clef | Adaptive Clef |
|---|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 280.22 | 280.07 | 42.55 | 282.87 | 282.87 | 282.87 |
| site-pure-16 | 295.50 | 293.45 | 64.72 | 301.94 | 297.84 | 301.10 |
| site-mixed-1 | 144.71 | 144.97 | 145.06 | 146.50 | 146.88 | 146.87 |
| site-mixed-16 | 146.43 | 149.65 | 156.44 | 163.84 | 165.47 | 165.22 |
Oracle sensitivity: table-only controls, no model. Median final-idle RSS.

| Workload | >25% | >50% | >90% | Never freed only | S=64 KiB | S=1 MiB | S=16 MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| site-pure-1 | 41.324 | 41.367 | 41.367 | 41.352 | 280.074 | 280.074 | 280.070 |
| site-pure-16 | 50.914 | 51.500 | 51.652 | 51.680 | 292.848 | 292.992 | 293.332 |

## Model budget and accuracy

Each cold model policy has 400 decisions shared with coverage fills. Identical native two-class model payloads share a raw response cache across policies/workloads; cached answers still consume decision slots, and original backend provenance is retained. Headline runs replay recorded answers with unchanged live instrumentation and no inference. Changed request states are logged: this measures the recorded policy, not whether the model would choose the same answers on warm state. Model server memory is excluded from allocator RSS.

| Workload | Policy | Cold decisions | Model rechecks | Cold unasked byte share | Warm unasked byte share |
|---|---|---:|---:|---:|---:|
| site-pure-1 | static-model | 11 | 0 | 0.00% | 0.00% |
| site-pure-1 | model | 27 | 16 | 0.00% | 0.00% |
| site-pure-16 | static-model | 11 | 0 | 0.00% | 0.00% |
| site-pure-16 | model | 26 | 15 | 0.00% | 0.00% |
| site-mixed-1 | static-model | 10 | 0 | 0.00% | 0.00% |
| site-mixed-1 | model | 23 | 13 | 0.00% | 0.00% |
| site-mixed-16 | static-model | 10 | 0 | 0.00% | 0.00% |
| site-mixed-16 | model | 23 | 13 | 0.00% | 0.00% |
| redis-mesh | static-model | 400 | 0 | 97.97% | 97.97% |
| redis-mesh | model | 400 | 0 | 97.97% | 97.97% |
| redis-drop | static-model | 400 | 0 | 99.12% | 99.12% |
| redis-drop | model | 400 | 0 | 99.12% | 99.12% |
No model-backed runtime recheck occurred in: redis-mesh, redis-drop. The adaptive label in those rows does not establish an effect of runtime input; inspect budget/coverage before attributing results to it.
Dominant site-pure decision histories, probabilities and observed free shares are in [site-decisions.json](results/pass6/site-decisions.json). Changes affect future allocations only; earlier permanent objects can continue pinning pages.
Among unasked cold-model bytes with matching prior-trace site truth, 73.6% belong to majority-transient sites. This aggregate supports transient as the classification fallback, not necessarily the memory-optimal fallback; the tested default remains transient. Policies and workloads contribute separate observations, not independent samples.

Cold accuracy populations and two-class confusion matrices are in [accuracy.json](results/pass6/accuracy.json). Rechecks are repeated decisions, not independent sites. Scores are withheld if any decision key lacks matching trace truth. Budget defaults are separated from model-backed answers.


## Cold inference and replay coverage cost

These costs are outside the warm timings. HTTP time includes queueing behind the independent prompt study; it is not isolated inference speed. Cached responses retain their original provenance. Coverage fills share the same 400-slot schedule budget.

| Workload | Policy | Final model slots | Cold HTTP s | Fill/probe HTTP s | Cold wall s | Warm changed requests |
|---|---|---:|---:|---:|---:|---:|
| site-pure-1 | static-model | 11 | 181.7 | 0.0 | 184.1 | 0 |
| site-pure-1 | model | 27 | 314.3 | 0.0 | 316.9 | 0 |
| site-pure-16 | static-model | 11 | 0.0 | 0.0 | 2.3 | 17 |
| site-pure-16 | model | 26 | 111.8 | 0.0 | 114.3 | 85 |
| site-mixed-1 | static-model | 10 | 30.6 | 0.0 | 32.8 | 0 |
| site-mixed-1 | model | 23 | 70.4 | 0.0 | 72.8 | 0 |
| site-mixed-16 | static-model | 10 | 0.0 | 0.0 | 2.2 | 11 |
| site-mixed-16 | model | 23 | 103.8 | 0.0 | 106.2 | 71 |
| redis-mesh | static-model | 400 | 1615.0 | 0.0 | 1637.4 | 28 |
| redis-mesh | model | 400 | 0.0 | 0.0 | 22.2 | 22 |
| redis-drop | static-model | 400 | 0.0 | 0.0 | 20.1 | 38 |
| redis-drop | model | 400 | 0.0 | 0.0 | 20.2 | 22 |

## mimalloc-bench regression

Regression has not completed; no aggregate claim is made. The interrupted three-class acceptance completed 21/22 workloads and is archived in results/pass5/prior.

## Measurement limits and interpretation

Unknown sites default transient because most requested allocation volume is
expected to be released. The all-transient/all-permanent controls are reported;
they do not directly test changing only the fallback for unseen sites. Neither
uniform control isolates the effect of changing that fallback alone.

Live lifetimes sample one allocation in 64 per thread/site. Success counters merge
every 4,096 allocations, at decisions and thread exit. Replay retains the same
instrumentation. Batched clocks, finite reservoirs and concurrent snapshots are
approximate; active workers can leave 4,095 unmerged allocations per thread/site
at exit. Retired sampled owners survive until their final cross-thread free.

Synthetic live bytes are requested bytes; Redis used_memory includes metadata and
usable-size effects. Every fragmentation variant uses MIMALLOC_PURGE_DELAY=0,
MIMALLOC_ARENA_PURGE_MULT=1 and MIMALLOC_PURGE_DECOMMITS=1, with the same settle/pulse.
Oracle-saving capture is (mi RSS - policy RSS)/(mi RSS - oracle RSS), undefined when the oracle saves no memory. It may be negative or exceed 100%; a small oracle saving makes the fraction unstable. Five repetitions show medians and ranges, not statistical equivalence. Raw phase,
stdout/stderr, replay/fill and inference-audit records remain on the test machine.

The pass-4 and pass-5 fixes are preserved, including copying the sidecar socket path
before applications can overwrite environment storage (Redis setproctitle), and
retaining each site's first model stack so cache collisions cannot change recheck
source context. Linux supports startup images only; dynamic loading/unloading and
post-fork synchronization remain outside the validated set.


## Pass 7 start — stack-only live classification

SPEC-STACK.md governs this pass. Inspected the remote process tree before editing.
Stopped the pass-6 regression runner (57170) and its cfrac/sidecar descendants;
archived its partial JSON, Markdown, decision/cache/log directory and bench.log in
results/pass6-regression-partial/. The independent promptlab process was left alone.
Pass-6 fragmentation remains the v-permanent-1 historical result.

Implementing stack-v1 and stack-v1-nodesc with the exact specified question and
choices, no source code, and neutral hand-written descriptions. Original descriptions
are preserved verbatim in descriptions-leaky/. Default budget becomes 1,500 answers.
Only sites with >=64 KiB of successful requested allocation bytes may contact the
sidecar. Before eligibility the allocator uses its default class, checking local byte
progress and periodically checking published cross-thread totals. Other threads'
4096-allocation batching can delay eligibility; it cannot admit an undersized site.

Runtime age is the oldest still-live object in the uniform 128-sample reservoir,
measured in requested allocation bytes on the batched clock. Model promotion of a
first-sight transient site requires permanent probability >=0.8 and age strictly
above one quarter of the current process clock. The heuristic retains pass 6's
>=16-sample, strictly-older-than-median cohort and <5% freed-byte rule, but also
requires the same strict age gate before choosing permanent. Meaningful frees
immediately permit transient, with no confidence/age barrier. Replay schema 4 and
policy-cache version 3 isolate old policy decisions; raw model caches are prompt-keyed.

Full Linux correctness PASSED for all 22 trace/random workload pairs, plus live
ownership/protocol, sample-reservoir transitions at 1/64, replay, budget and new
stack/age/admission checks. The standalone label-default checks also passed on
Linux after switching that tool to stack-v1. The remote pass-6 supervisor recorded
exit 1 at the interrupted regression stage; this is an intentional partial archive,
not a completed regression. Instrument validation and the new model matrices follow.

The pass-7 instrument PASSED on library
cae42e81344dd0838d08f595627fda1256a21eca6a15f2b0251ab7c5d478ca92.
At every idle point oracle <= random and < half mimalloc; all 40 warm instrument
intervals have zero inference overlap. Full workload correctness also passed.
The first site-pure-1 stack-v1 cold decisions classify create_session_state transient
(p=0.867) and insert_cache_index permanent (p=0.797), with both request-buffer paths
transient. Five model-answered sites cover 99.99855% of requested bytes; six small
sites totaling 13,376 bytes are never asked. Warm performance remains pending.

First cold site-pure-1 observation (not yet five-run performance): code-only Clef
idle RSS is 43.58 MiB, while runtime Clef is 231.14 MiB and heuristic 228.51 MiB.
Runtime's session first-sight answer is correctly transient, but its first recheck
returns permanent p=0.906 and satisfies the specified age gate. Subsequent early
rechecks also return permanent around p=0.90 while no session has ended. The last
recheck has 52% still alive and permanent p=0.641, so the new guard restores
transient; earlier mixing can already pin pages. No prompt or policy tuning is
being applied to this negative runtime result.

## Pass 7 — first audited stack-v1 result

Both site-pure workloads completed five repetitions for every variant; 120 warm
intervals have zero inference overlap. Idle MiB, mi/oracle/code-only/runtime/heuristic:
site-pure-1 = 280.22/41.36/43.57/231.13/228.54;
site-pure-16 = 296.55/51.68/66.36/261.70/262.83.
Code-only captures 99.1% and 94.0% of oracle saving; runtime 20.6% and 14.2%;
heuristic 21.6% and 13.8%. All five queried first-sight sites agree with trace truth.
Thus there is no first-sight misclassified site to fix. The remaining code-only
RSS gap (2.21/14.68 MiB) is consistent with live metadata and permanent cache objects
allocated transient before byte eligibility, especially across threads; these two
contributors have not been independently measured. No prompt tuning is applied.
The runtime gate admits early session promotions because sampled age already spans
95–99% of the current allocation clock, despite no session having ended.
RESULTS.md now includes these audited observations above the unchanged pass-6 report.

## Pass 7 — site-pure description ablation complete

All four prompt/thread blocks are audited (240 warm intervals; zero inference
overlap). stack-v1-nodesc code-only captures 99.1%/94.8% of oracle saving at 1/16
threads, versus 99.1%/94.0% with the description. Both classify all five asked sites
correctly. The neutral description increases session transient probability from
0.654 to 0.867, and cache permanent probability from 0.685 to 0.797, but no RSS
benefit is established on this workload. Nodesc idle MiB mi/oracle/static/runtime/
heuristic: 280.21/41.33/43.57/231.13/228.51 (1 thread), and
296.55/51.53/64.27/260.20/261.50 (16 threads). Runtime still promotes sessions early;
its capture is 20.5%/14.8%. Five-run ranges and cold costs are in results/pass7/.
The rest of fragbench is now running under stack-v1, then stack-v1-nodesc.

Redis Mesh stack-v1 code-only cold collection completes with 12 model-answered
sites out of 630 observed sites, covering 99.8104% of requested bytes; 794,698 of
419,116,478 bytes remain at unasked sites. No budget fallback. New HTTP time is
25.15 seconds. This contrasts with pass 6's 400 startup answers and only ~2.03%
byte coverage. Runtime collection and warm memory results are still pending;
coverage improvement alone does not establish an RSS benefit.

## Pass 7 — full stack-v1 fragbench audited

All six stack-v1 workloads and the two nodesc site-pure workloads are complete and
audited: 480 warm intervals, zero inference overlap. Mixed-1 mi/oracle/static/
runtime/heuristic idle MiB: 144.70/144.98/146.36/154.28/146.43; mixed-16:
146.43/149.67/154.39/164.95/154.89. Redis Mesh:
183.95/185.96/192.90/224.95/226.93; Redis drop:
269.43/271.02/277.69/277.84/277.78. The oracle saves no memory in these four blocks,
so saving capture is undefined, not zero or a success. Static/runtime Redis coverage
is 99.81% (Mesh) and 99.78% (drop). Model schedules consume 12/43 slots for Mesh
(static/runtime, 31 runtime rechecks) and 13/38 for drop (25 runtime rechecks), all
well below 1,500. The byte gate, rather than a binding raised budget, is the observed
reason startup sites no longer consume the available decisions on Redis.
High coverage alone does not improve memory. In Mesh runtime uses 1.165x code-only
RSS and 1.223x mimalloc RSS, versus heuristic 1.234x mimalloc. The nodesc remainder
is running before regression begins. RESULTS.md includes the audited data and costs.

The nodesc Redis Mesh third warm runtime repetition encountered a new replay slot.
The runner retained that observation as a coverage probe, filled missing decisions
outside headline measurements, and successfully retried the same repetition. Warm
state drift is not fresh inference; results measure the recorded policy. Fill slots
continue to share the 1,500-answer cold budget. No failed/probe row is used as one of
five accepted repetitions. (Mesh runtime/code-only RSS ratio above rounds to 1.166.)

## Pass 7 — fragmentation complete

All 12 prompt/workload blocks have five accepted interleaved observations for each
of 12 variants: 720 warm intervals, zero inference overlap (plus the separate
40-interval instrument audit). Nodesc mixed-1/mixed-16 mi/oracle/static/runtime/
heuristic idle MiB: 144.70/144.98/146.37/154.28/146.42 and
146.43/149.62/154.57/166.34/154.96. Nodesc Mesh:
185.95/186.01/192.90/220.93/230.93; nodesc drop:
270.52/271.37/277.28/277.49/277.73. None has a positive oracle saving. Nodesc
Redis coverage remains about 99.8%, with 12/43 static/runtime model slots in Mesh
and 13/38 in drop. The two new variants isolate description text at first sight;
comparisons to pass 6 also change admission, budget and runtime policy and cannot
isolate source removal alone. Full results, ranges, phase medians, cold costs,
coverage and dominant-site decisions are in RESULTS.md and results/pass7/.

The full 22-workload mimalloc-bench regression has now started with stack-v1,
1,500-slot schedules and five interleaved warm repetitions. No regression aggregate
is claimed until it completes and is independently audited.

Regression checkpoint: cfrac completed all 60 warm observations; espresso cold
collection has begun. The partial matrix is checkpointed locally as
results/pass7/regression-progress.json (not yet independently audited). Cfrac
static coverage is 99.9588% with 66 answered sites; runtime cold collection used
229 answers including rechecks. Regression remains incomplete, so no full-matrix
aggregate is published yet.

Cfrac's completed 60 warm observations are now independently audited (zero
inference overlap) and published. Espresso static cold collection completed in
799.1 s: 500 answered sites of 1,045 observed, 99.7999% byte coverage, no budget
fallback. Its trace has 501 sites totaling >=64 KiB; a site may cross the threshold
on its final allocation and have no subsequent allocation to classify. Thus the
larger budget is actually used on Espresso: static answers exceed the old 400 cap.
Espresso runtime collection is active; timings from it remain outside warm results.

Regression checkpoint: Espresso completed all five warm repetitions for every
variant. Runtime cold collection took 1,342.6 s, used 1,235 model-backed decisions
(500 initial sites plus rechecks), covered 99.7999% of bytes, and had zero budget
fallbacks. This is substantial inference cost even with stack-only prompts; it is
reported separately from replay timings. Barnes has started warm repetitions.
The recorded Redis headers were also checked directly: stack-v1 includes the
neutral Redis description, while nodesc omits it; program names remain redis-server
after delayed admission. No source/prompt changes were made during measurements.

The first three regression workloads are now audited and published; no inference
overlap. Barnes has 0% model coverage and no model calls: its six >=64-KiB trace
sites each allocate exactly one object (6.25, 250, 63.75, 137.5, 18.75 and 12.5 MiB
requested). Admission checks before a subsequent allocation, so crossing the byte
threshold on the only allocation cannot retrospectively classify it. This is an
explicit limitation, not a budget failure; requesting a model answer after that
last allocation would not change its already chosen heap. All such bytes remain
in the coverage denominator. Larson warm repetitions are active.

Larson completed: preliminary score/mi (lower is better) is 1.021 for jev-none,
1.673 for the oracle table, 2.052 for heuristic, 2.041 for static and 2.027 for
runtime. Peak RSS/mi is 0.980/1.141/1.412/1.158/1.158 respectively. Heuristic/oracle
score is about 1.227, above the 1.15 target; retained stack capture and sampled
lifetime tracking are plausible contributors, not separately isolated causes.
Per SPEC-TWOCLASS, this target miss is recorded without tuning or withholding the
remaining matrix. Larson-sized cold collection follows. Full audit is pending for
this newly completed block.

Five regression workloads are now audited and published, with zero inference
overlap. Current target misses: cfrac keyonly RSS/none 1.0319 vs 1.03; Larson
heuristic score/oracle 1.2267 vs 1.15; Larson-sized none score/mi 1.0375 vs 1.03,
and heuristic score/oracle 1.2046 vs 1.15. These are measured medians, not claims
of statistical significance or isolated causes. Xmalloc-test warm repetitions
have begun. Source, library and prompt fingerprints remain fixed.

Ten regression workloads (through cache-thrashN) are complete and independently
audited, with zero inference overlap. Xmalloc heuristic/oracle score is 1.4181,
another >1.15 target miss; none/mi score is 1.0068. All detailed ranges and current
target misses are published in results/pass7/ and RESULTS.md. Mstress cold
collection is active. No benchmark or prompt tuning was applied after these misses.

Twelve regression workloads, through rptest, are now independently audited and
published with zero inference overlap. The primary time table now includes the
normalized score as well as wall and CPU ratios so duration-limited throughput
costs are visible directly. Glibc-simple is running; the remaining matrix continues.

Sixteen regression workloads, through alloc-testN, are now independently audited
and published with zero inference overlap. Alloc-testN runtime repetition five
needed a second coverage fill: the missing-slot probe was excluded, the fill ran
outside timing, and the retry completed. Mstress keyonly RSS/none is 1.0474
(target 1.03); this additional miss is recorded without tuning. Malloc-large is
running. RESULTS.md now leads with the measured first-sight success and the
runtime session-promotion failure, followed by the full evidence tables.

Twenty-one regression workloads, through sh8benchN, are complete and independently
audited with zero inference overlap. Redis cold collection has completed and its
five warm repetitions are underway. All current results and target misses are
published; final matrix completion and audit remain pending.

Focused macOS validation passed: stack prompt contract (12 frames, no source,
neutral-description ablation, runtime caveat), strict quarter-clock and 0.8 model
promotion boundaries including response-cache hits, heuristic free/age boundaries,
64-KiB admission and failed-allocation exclusion, existing ownership/protocol,
reservoir sample rates 1/64, replay and zero-budget integration. Legacy protocol
fixtures explicitly set JEVALLOC_MIN_SITE_BYTES=0; dedicated admission cases and
benchmark runs use the 65536 default. The old source-context test now explicitly
selects v2, rather than assuming the default still includes snippets.

Full Linux validation is running. scripts/pass7.sh waits for it, then validates
the instrument, runs both site-pure thread counts under each prompt, completes the
other four fragbench workloads under each prompt, and finally runs all 22 regression
workloads under stack-v1. Every block uses five interleaved warm repetitions after
cold collection and coverage fills, followed by an independent inference-overlap audit.

Final pass-7 completion (supersedes the queued launch-status paragraph immediately
above, which the long-lived launch shell appended when it finally exited): full
Linux validation passed, the instrument passed, both prompts completed all six
fragbench workloads, and stack-v1 completed all 22 mimalloc-bench workloads. The
remote pipeline reports stage complete and exit status 0. Each variant has five
accepted interleaved warm repetitions. Independent audits verified 2,080 warm
intervals (40 instrument, 720 fragbench, 1,320 regression), zero inference overlap,
and matching matrix hashes. The measured library is the full-suite-validated
cae42e81344dd0838d08f595627fda1256a21eca6a15f2b0251ab7c5d478ca92.

Final RESULTS.md preserves every pass-6 table after the pass-7 report. Audited
matrices, audit evidence, warm ranges, phase medians, byte coverage, cold/fill costs,
first-sight accuracy and dominant-site histories are in results/pass7/. Regression
is saved locally as results/pass7/pass7-regression.json with its matching audit;
raw traces, model cache and detailed run logs remain on the test machine. The old
pass-6 partial regression remains archived in results/pass6-regression-partial/.

The main outcome is first-sight success: code-only stack-v1 captures 99.1%/94.0%
of site-pure oracle idle-RSS savings at 1/16 threads; nodesc captures 99.1%/94.8%.
The specified runtime guard still allows the wrong early session promotion, leaving
runtime capture at 20.6%/14.2%. No further prompt or policy tuning was applied.
Redis fragmentation model-byte coverage is about 99.8%; regression Redis reaches
99.98% with 7 static or 20 runtime model decisions. Its static/runtime time score
is 1.378/1.432 times mimalloc. Barnes remains the explicit 0%-coverage, one-shot
allocation limitation of next-allocation admission.

There are 13 recorded regression acceptance-target misses, including heuristic
score/oracle 3.104 on sh6benchN and 2.276 on sh8benchN. They are diagnostic misses,
not hidden or treated as passing. Full Linux correctness and focused local tests
passed; no source changes followed measurement startup. Only reporting and journal
updates were made while the matrix ran. Everything remains uncommitted, no git
writes were performed, and promptstudy.py and the independent prompt study were
left alone. The remote address was never written into an artifact.

## Pass 8 — initial state and hybrid implementation

SPEC-REAL.md is authoritative for this pass. Initial remote inspection found no
running regression process: pass 7 had completed all 22 workloads, status 0, as
also recorded by the committed report. Preserved the completed aggregate, audit,
and raw logs under results/pass7-regression-partial/ with an ARCHIVE-NOTE.txt
explaining this discrepancy. There was no process to stop. No promptlab files or
processes were touched. New regressions remain last in the pass.

Hybrid uses exactly the static-model first-sight payload and returns both prior
probabilities. Runtime transitions execute locally on sampled allocation/free
updates, without a second model request. Exact cumulative sampled bytes and frees
include samples evicted from the age reservoir and samples from retired threads.
Demotion requires >=16 samples and >=5% sampled requested bytes freed. Promotion
requires no sampled free ever, P(transient)<0.7, oldest live reservoir sample older
than half the allocation clock, and >=64 MiB clock. Classes persist between
transitions; a demoted site cannot promote again because it has observed frees.
The sampled path uses the existing cohort lock; hybrid allocation reads the site's
atomic class so cross-thread demotion reaches subsequent allocations. Clock and
oldest-live reservoir age remain approximate, as in the previous pass.

Pass-8 workload design: SQLite 3.50.4 amalgamation, RocksDB 10.10.1 (matching the
mimalloc-bench recipe), LevelDB 1.23, and gflags 2.2.2 are fetched from upstream
archives into build/real. No system installation is used. SQLite holds a 100,000
row in-memory database through a burst of 48 connections and 16 sorted prepared
queries per connection, then closes the burst. LevelDB retains iterators across
memtable churn, releases them, and compacts. RocksDB's db_bench is patched only to
add phase markers and a flush/background-compaction wait before idle; both cache
and small-cache/churn variants use 16 threads. Program memory estimates are labelled
as partial where appropriate; they are not presented as exact allocator live bytes.

Redis sessions keeps a 30,000-key catalogue, writes 64,000 session keys through 16
pipelined clients, reads large MGET replies, and publishes to 32 subscribers. TTLs
are armed after the fixed-work peak, subscribers disconnect, and idle measurement
waits for every session to expire. This prevents cold model time changing the live
key set at the measured peak. All workloads use the same purge options as pass 7
and a 500-ms settle period (purge delay is zero). Existing Mesh/drop workloads stay.

The headroom runner traces first, starts with all-transient, considers the 24
highest-byte sites once in descending byte order, and accepts a flip only for a
>2% fall in three-run median idle RSS. Candidate measurements remain separate from
the final five interleaved baseline/oracle/search runs. Only a >5% saving in that
final comparison permits model collection. Eligible workloads then get a fresh
five-run interleaved comparison of baseline, both tables and all three policies.
No-headroom cases consume no model decisions. Search overfitting and run noise are
controlled by separate final measurements, not by calling the lifetime oracle an
RSS optimum.

Hybrid validation additionally exercises the complete socket/allocator path using
one fake first-sight answer per site. At sample rates 1 and 64: a .9 transient prior
stays transient through 128 MiB with no frees; a .6 transient prior promotes only
after maturity; a .1 transient prior (permanent answer) demotes when frees occur.
All six cases passed, with exact expected sample/free totals, no failures, and no
rechecks. This validates the C transition plumbing, not just the isolated rule.

Full Linux correctness completed successfully for all 22 mimalloc-bench workloads,
including ownership/stress, exact trace accounting, live protocol, reservoir,
replay coverage, and budget tests. Fragmentation attribution/accounting checks
also passed. The instrument and site-pure warm comparisons follow using the same
library; there have been no allocator changes since this build.

Site-pure-1 five-run provisional medians: mi 280.21875 MiB, oracle 41.32422,
static-model 43.56250, hybrid 43.57422, heuristic 228.55078. Hybrid preserves all
five first-sight classes; session P(transient)=0.867015, no promotions or demotions.
The corresponding 16-thread cold run also preserves all five classes. Combined
independent audit and 16-thread warm completion are still pending at this checkpoint.

Site-pure complete and independently audited: 50 warm intervals, zero inference
overlap. Final-idle medians at 16 threads: mi 296.55 MiB, oracle 51.45,
static-model 63.55, hybrid 63.27, heuristic 260.22. Saving capture is 95.1% static
and 95.2% hybrid; at one thread both capture 99.1%. The 0.28-MiB difference at
16 threads is not an established advantage from five runs; hybrid and static use
the same five classes and have no runtime class transitions. The originally
motivating wrong session promotion is absent. The real-program build now follows.

Build correction: gflags' upstream default REGISTER_INSTALL_PREFIX=ON created one
CMake package-registry pointer under ~/.cmake despite the local install prefix.
The exact generated pointer was verified and removed immediately; build-real.sh
now explicitly disables both REGISTER_INSTALL_PREFIX and REGISTER_BUILD_DIR.
No libraries or headers were installed outside build/real/prefix, and no system
packages were used. This fixes the recipe's unintended registry side effect.

Real-driver smoke checks passed (not headline measurements; RocksDB compilation
was concurrent). SQLite retains ~59.85 MiB by sqlite3_memory_used after closing the
query burst, down from ~179.89 MiB at peak. LevelDB's approximate-memory-usage drops
to only 4,104 bytes after compaction despite ~88 MiB RSS: this property excludes
substantial process state and must not be called exact live bytes or used as an
exact fragmentation denominator. Phase records and report text label that limit.

All requested new source builds succeeded: SQLite amalgamation, LevelDB, and
RocksDB db_bench with local gflags. No application needed a build skip. Source
archive and executable SHA-256 files are in results/pass8/builds/. The sequential
real headroom pipeline has started with SQLite; no real-program model decisions
are collected before its workload's independent >5% table-saving gate.

SQLite is complete and independently audited. Final medians: mimalloc 78.9453 MiB,
oracle 82.0703 MiB, search 79.0078 MiB. No search flip cleared 2% in training; the
final search is all-transient. Neither table saves >5% (neither saves anything),
so this workload is reported as no per-site headroom and receives zero model
runs. That is a result for these tables/workload, not proof that all possible
per-site assignments are ineffective. LevelDB's search follows.

LevelDB completed with zero inference overlap. Final idle RSS bytes are
91,869,184 (mi), 92,200,960 (oracle), and 92,069,888 (search), all about 88 MiB.
No greedy flip was accepted. Neither table cleared 5%, so LevelDB receives no
model runs. Redis sessions trace/workload validation completed and its headroom
search started; RocksDB variants and the existing Redis cases remain queued.

Redis sessions completed and audited: mi 50,372,608 bytes, oracle 52,383,744,
search 50,532,352 (about 48.04/49.96/48.19 MiB). All 24 greedy flips were rejected;
no per-site headroom and no model runs. The catalogue survived and all 64,000
session keys expired before idle. RocksDB cache-heavy trace is now running,
followed by its small-cache/memtable-churn variant and the older Redis workloads.

RocksDB cache-heavy search has provisional positive training evidence. Starting
all-transient at 131.668 MiB, it accepted AllocateBlock/ReadBlockContents through
MaybeReadBlockAndLoadToCache (128.46 MiB), then a distinct key through
ReadAndParseBlockFromFile and CompactionJob (114.55 MiB). These are training
medians only, not established headroom against plain mimalloc; the full greedy
pass and independent five-run control comparison must finish before model calls.

RocksDB cache-heavy independent validation rejected the apparent training gain.
Five-run idle MiB: mi [137.98, 137.23, 121.97, 120.66, 120.87]; oracle
[137.72, 114.64, 132.64, 109.09, 132.94]; search
[125.93, 133.14, 116.23, 134.20, 126.64]. Medians are 121.97 / 132.64 / 126.64.
The final search file is byte-identical to the selected training candidate
(indices 0 and 2 retained). Thus this is not a lost-label bug: run variability and
selection on three trials did not produce a reproducible saving. No per-site
headroom under the required final gate; no model run. Independent audit passed.
Keep the accepted block-cache/compaction labels and all training measurements in
the report rather than hiding the failed validation. RocksDB churn now follows.

RocksDB churn baseline trials take 78–86 seconds each (roughly 270–290 target CPU
seconds). The full requested 24-site/three-trial search and five final repetitions
are retained; this block is substantially longer than the others. It remains
sequential, with all later real blocks and regression queued behind it. No partial
training result is treated as completed headroom or used to authorize model calls.

Long-run checkpoint: RocksDB churn has reached candidate 11 of 24. The runner is
healthy and retains every completed three-run trial. Real-program completion and
the final regression matrix are still pending; no new aggregate is claimed.

RocksDB churn's complete 24-candidate search finished. Its independent five-run
baseline/oracle/search validation has started. The lengthy search was completed
without reducing workload size, candidate count, or trial repetitions.

RocksDB churn finished all 24 three-run candidates and all five interleaved final
repetitions. No flips were accepted. Final idle RSS bytes: mi 26,083,328; oracle
27,189,248; search 26,333,184 (24.88/25.93/25.11 MiB). No per-site headroom, no
model runs, and zero inference overlap in the independent audit. All five newly
added real-program workloads are complete; the retained Redis Mesh/drop headroom
checks now run before the full regression matrix.

The source-build recipe now verifies the four upstream archive SHA-256 values
recorded during this pass and downloads through a temporary file. This changes
only future fetch validation, not any measured binary, workload, or policy.

## Final-idle metric correction before regression

An audit found that headroom.py averaged all idle points, whereas the report and
prior fragbench convention use the final idle point. This affects only the
existing two-cycle Redis Mesh workload. Every other real workload has exactly one
idle point, so its search, gate and reported result are unchanged. The old runner
is preserved as results/pass8/headroom-average-idle.py.

Stopped only the waiting pass-8 regression launcher, leaving the active Redis-drop
run alone. Re-scoring Mesh changes the greedy acceptance path (it cannot be fixed
by reformatting the final table). Its entire average-idle experiment is archived
as results/pass8/redis-mesh-average-idle/, with a raw-path relocation note. A fresh
complete Mesh trace/search/five-run gate now uses final idle, then the regression
launcher resumes. New unit tests distinguish final idle from both the maximum and
an average, and ensure averaging cannot incorrectly authorize model collection;
all three tests pass. No model decisions were made on the superseded pilot.

Corrected Mesh completed all 24 candidates (three runs each), accepted no flips,
and completed five interleaved final repetitions. Final idle RSS bytes:
mi 194,879,488; oracle 194,998,272; search 195,100,672. Redis-drop completed with
mi 283,856,896; oracle 284,209,152; search 284,168,192. Both fail the >5% headroom
gate. All seven real-program workload blocks are complete and independently
audited; none authorized model evaluation. No inference accuracy claim is made
for the new real-program stacks. The superseded Mesh pilot remains separate.

The complete 22-workload/12-variant regression matrix is now running last, with
five warm repetitions, stack-v1, static-model, hybrid and heuristic. The legacy
model-reask policy is retained but not rerun. Preserved the full correctness
report and current instrumentation matrix/gate/audit under results/pass8/.
The reporting code now links exact wrong-permanent-prior probabilities/stacks
and hybrid counters; shutdown demotions will not be presented as proven useful
corrections. Added final-idle tests to the standard test entry point; the new
headroom and hybrid protocol tests pass locally.

Regression checkpoint: cfrac, espresso, Barnes and Larson completed all requested
warm repetitions. Completed hybrid observations have zero rechecks. Cfrac and
espresso record runtime demotions; these are not yet interpreted as an RSS gain
because end-of-process counters include shutdown. The full matrix and its final
inference audit remain pending. Benchmark inputs and measured allocator remain
unchanged during collection.

## Pass 8 completed

The final pipeline exited 0. Pure, real, corrected-Mesh, regression and overall
status files are all 0. No pass-8 benchmark or launcher process remains; the
existing model server is left running. No work was committed or staged.

Completed the full 22-workload, 12-variant, five-repetition regression matrix:
1,320 accepted warm observations, 66 cold observations and 66 coverage records.
All 110 warm hybrid observations have zero model rechecks and zero HTTP inference
time. Every headline run exited successfully and passed its workload output
check. The independently audited warm intervals comprise 1,320 regression, 50
site-pure, 105 real-program validation and 40 instrumentation observations.
An additional audit covers all 525 retained greedy-search trials. All 2,040
intervals have zero inference overlap. The superseded average-idle Mesh pilot is
excluded from these final counts.

Added tools/pass8_validate.py to recompute all 168 greedy candidate decisions,
all seven five-run headroom gates, selected permanent-site tables, repetition
counts, and library fingerprints. Validation passes. All measured blocks match
the full correctness report's allocator SHA-256:
e6ffcfc52823ef422a8565967bccf7986d86ac6e0de6057f13bc5b40681fa48e.
The new protocol/final-idle unit tests pass locally; Python compilation and
`git diff --check` pass. Full Linux correctness for 22 workloads, hybrid allocator
integration, stack tests, and fragmentation tests passed earlier in this pass.

Final findings:

- Site-pure hybrid idle RSS is 43.57 MiB (one thread) and 63.27 MiB (16 threads),
  capturing 99.1% and 95.2% of the oracle saving. It preserves the confident
  transient session prior, matching static-model without runtime promotions.
- All seven real-program workloads fail the >5% per-site headroom gate. All
  requested source builds succeeded, including LevelDB as the additional program.
  No models were evaluated on these real-program fragmentation stacks, as required.
  RocksDB cache search accepted two training flips but lost in final validation;
  both the failed validation and the noisy training improvement remain visible.
- Wrong permanent priors occur in 12 regression workloads (488 workload/site
  first-sight answers versus prior-trace lifetime labels). Hybrid demotes many,
  but RSS changes are mixed. Glibc-thread median peak falls 95.30 -> 69.16 MiB
  versus static-model, while its inverse-throughput cost grows 3.26x -> 6.69x
  mimalloc; duration-limited work also differs. Rptest peak increases
  159.88 -> 193.83 MiB. Mleak100's lower median has overlapping five-run ranges.
  End-of-process demotion counters may include shutdown, so they do not establish
  that a useful correction preceded peak RSS.
- Runtime cost is a serious limitation. Hybrid sh6benchN takes 35.29x mimalloc
  time versus 13.09x for static-model; sh8benchN is 20.22x versus 9.18x.
  Xmalloc-test inverse-throughput cost is 10.15x versus 4.83x. No late allocator
  tuning was performed after collecting the measurements.
- The inherited acceptance diagnostic is false: four baseline/key-only checks
  and five heuristic/oracle timing checks miss their thresholds. These are
  performance/memory targets, distinct from the passing correctness tests.
  Every miss and all 12 variants' ranges remain in the report.

All pass-8 model answers reused exact-payload cached answers, including coverage
fills: total native HTTP inference time was zero. The cache provenance and model
probabilities are retained; this pass does not measure fresh inference latency.
Warm runs still execute sampling and local hybrid transitions on each new process.

RESULTS.md now leads with completed findings, negative real headroom, and severe
regression costs, followed by full tables and earlier-pass history. Exact wrong
prior probabilities/stacks/counters are in results/pass8/wrong-priors.json;
validation and search-inference audit artifacts are preserved alongside aggregates.
Raw traces, decision schedules, stdout/stderr and caches remain on the test machine
at the paths recorded in the matrices; compact evidence and final oracle/search
tables were synced locally. results/pass8/README.md explains the artifact layout
and the superseded Mesh pilot.

The final scan of every modified/untracked local file found neither the remote
address nor its host component. tools/promptstudy.py is unchanged, promptlab was
not touched, and no system packages were installed. The prior pass's already
completed matrix remains archived with an explanatory note under the requested
pass7-regression-partial directory. Everything is left uncommitted.

## Pass 9 — initial state and request-context implementation

SPEC-REALTIME.md governs this pass. Inspected the test machine before changing it:
all five pass-8 status files (overall, pure, real, corrected Mesh workload,
regression) contain 0, and no benchmark/launcher/sidecar remains running. The
existing llama-server is healthy on its configured local port and is left alone.
No previous work needs stopping; pass-8 evidence stays intact. The existing local
uncommitted changes belong to the prior pass and are preserved.

Implementing bounded thread-local application context, pair-keyed trace/table/live
policies, and an explicitly uncached per-allocation policy. The application owns
normalization. Per-site controls disable context in the allocator so they measure
the same instrumented executable and the same request stream.

Context integration passes on Linux, including weak-link operation without preload,
255-byte copying, two-thread isolation, empty-context compatibility, and exact
64-KiB admission per pair. A mock sidecar returning recheck_after=0 still receives
every admitted allocation in per-alloc mode (408/408 expected requests); cached
mode receives exactly three first-sight requests on the same fixture.

Redis instrumentation is kept as patches/redis-request-context.patch. Its build
copies the existing source tree under build/real and applies the patch there,
leaving the original source and pass-8 binary alone. The hook wraps cmd->proc,
restores outer context for nested commands, and records command, key prefix,
expiry presence and a size bucket. Parser/network allocations preceding dispatch
remain context-free. Keys without a colon retain up to 16 bytes as specified;
this can be high-cardinality (notably redis-drop) and is not hidden by the report.

The small per-allocation experiment uses 2,400 payload allocations, four times
the normal size so rare day-TTL pairs can pass admission. It omits parse/response
buffers and purge pulses to spend its <3,000 decision budget on request payloads.
The same scaled workload is used for all its controls. Optional exact object
logging records allocation/free clocks, requested sizes, pair keys, returned
classes and per-pair ordinals; its overhead is included in the small live run.

Both exploratory mixed-site blocks completed. Before publishing, archived them
under results/pass9/pilot-before-final on the test machine and started fresh
matrices after finalizing per-allocation protocol negotiation, per-object replay
checks and optional long-settle phase hooks. These pilots are excluded from final
results. The preliminary context oracle reduced one-thread idle RSS from about
145 MiB to 26 MiB, and Clef/context was about 28 MiB; final numbers must come from
the new five-run matrices and their matching library/workload fingerprints.

The final context pipeline runs full Linux correctness, fragmentation truth
checks, the isolated Redis build, both mixed server cases, all three Redis
24-pair greedy searches/gates, and the small per-allocation experiment, in that
order. Existing test artifacts that used historical pass directories now support
JEVALLOC_TEST_REPORT_DIR; this pass redirects them under results/pass9 to preserve
prior evidence. Mesh work waits until these context measurements complete.

Full Linux correctness passed for all 22 trace/random workload pairs, C/C++ stress,
site/table checks, exact lifetime accounting, hybrid integration, live/replay/budget
checks and the new context/per-allocation tests. The context fixture forces depth
1 so all three contexts share the same stack site; cached mode still asks exactly
three times, while per-alloc asks on all 408 admitted allocations. Unit coverage
also rejects a per-allocation replay when the object's requested size changes.

Normal model budget defaults are now 3,000 in jevd and both benchmark CLIs.
The instrumented Redis executable has its own copy of the neutral Redis program
description, avoiding an accidental no-description ablation caused by its name.

Final site-mixed-1 completed all five interleaved repetitions and passed the
independent inference audit (zero overlaps). Median final idle MiB:
mi 144.6953; jev-keyonly 144.8008; per-site oracle 145.0000;
context oracle 26.0547; code-only/site 146.4336; Clef/context 28.1055;
hybrid/context 28.1094; heuristic/context 146.8711. Live context therefore creates
a saving absent from the per-site control, and both Clef policies capture about
98.3% of the context oracle's saving. These are final-library measurements, not
the archived pilot. The 16-thread block and Redis gates continue sequentially.

Final site-mixed-16 also completed all five repetitions and has zero inference
overlap. Median idle MiB: mi 146.4219; keyonly 146.8398; per-site oracle 149.6992;
context oracle 33.4062; code-only/site 154.4531; Clef/context 46.1055;
hybrid/context 46.6172; heuristic/context 167.0273. Clef captures 88.8% and hybrid
88.3% of the oracle saving. Both mixed workloads have 16 distinct pairs, 10
original sites and four signatures including empty context. The gap from the
context oracle is larger with 16 threads; warm ranges and admission/metadata
costs remain visible rather than calling this oracle-equivalent.

Redis-Mesh trace has 626 pairs, 621 sites and six signatures. Its greedy search
has an accepted training move at empty context so far; this is not a validated
saving and does not authorize model calls until the independent five-run gate.

The Redis-Mesh trace quantifies the dispatch-hook limit: 372,103,036 of
419,219,686 requested bytes (88.8%) carry empty context. The accepted search
training move is also empty-context, at ztrymalloc_usable -> _sdsnewlen ->
createRawStringObject -> processMultibulkBuffer. Thus most value allocation
happens during RESP parsing, before cmd->proc receives the dispatch context.
This is measured coverage of the specified small application patch, not a claim
that richer instrumentation could never separate those allocations.

Redis-Mesh completed and passed its inference audit. Median idle MiB:
mi 185.9609; keyonly 182.0742; per-site oracle 188.0430;
context oracle 196.0625; context search 180.0117. Search saves only 3.2% against
mimalloc, below the strict >5% gate, so no model runs are authorized for this
workload. The accepted empty-context parsing-site move is retained as training
and validation evidence; it is not attributed to live request information.

Redis-drop trace completed: 495,421 pairs, 629 sites and 160,292 signatures.
Its colon-free k<number> keys expose the specified prefix rule's high cardinality.
The raw 907-MiB trace stays on the test machine. The permanent-pair catalogue is
compressed, so every label remains available without putting this raw trace in
the repository. Its 24-pair search now runs with the same admission/gate rules.

Redis-drop has another important measurement limit. A sampled context-bearing
1,030-byte value row symbolizes to ztryrealloc_usable -> zrealloc ->
sdsRemoveFreeSpace -> trimStringObjectIfNeeded -> setCommand -> call. Redis first
allocates these strings in the context-free RESP parser, then trims them during
command execution. The inherited jev_realloc fast path retains the physical block
when the request fits its usable size; trace mode nevertheless records a logical
free/new-allocation lifetime transition. A context label on that realloc does not
retroactively move its original storage. Consequently the context trace's high
classification accuracy is not a physical-placement upper bound. This limit will
be stated alongside the Redis headroom result, rather than attributed to a model
failure or hidden behind the logical oracle's accuracy.

Redis-drop completed with no accepted greedy flips and passed its inference
audit. Median idle MiB: mi 271.1992; keyonly 286.9648; per-site oracle 270.5469;
context oracle 283.7773; search 285.7109. No context table clears the >5% gate,
so model decisions remain zero. The enormous context table itself increases the
key-only control's memory cost; comparison with keyonly is retained alongside
comparison with plain mimalloc. Redis-sessions follows (662 pairs, 644 sites,
13 signatures in its trace).

The mixed payload call path makes the model's use of context explicit. Without
context it answers transient with probability 0.641128. With context: ttl=0 is
transient at 0.648658; ttl=short is transient at 0.717772; ttl=day is permanent at
0.618898. Both thread counts reuse these exact-payload answers. All five warm
hybrid runs at both thread counts have zero promotions and zero demotions, so
this saving comes from the context-conditioned prior, not runtime corrections.
The day answer is only moderately confident; no probability threshold was tuned.

Redis-sessions completed and passed its inference audit. No greedy flips were
accepted. Median idle MiB: mi 48.1094; keyonly 48.2031; per-site oracle 50.0312;
context oracle 50.0352; search 48.2539. All three Redis workloads therefore fail
the >5% context-table gate and receive zero model decisions. Live request context
turns the mixed synthetic workload into a saving, but the specified Redis command
hook does not produce a validated saving in these three tests.

The per-allocation small experiment has started its cold run. Initial records
show one HTTP decision per admitted allocation, with no errors; final per-object
accuracy waits for the exact free events and final allocation clock at exit.
Additional protocol negotiation integration passed with JEVALLOC_PER_ALLOC=0:
the sidecar's per_allocation response enables all 408 expected subsequent
admitted requests, including when recheck_after remains zero.

While remote per-allocation inference runs, built the allocator locally on macOS
arm64 and ran the context integration fixture. The fixture now uses a portable
mutex/condition rendezvous instead of pthread_barrier_t. This Darwin linker needs
-Wl,-undefined,dynamic_lookup for unbound weak imports; the test and README now
include that application link option. Linking/running without the library, TLS
isolation, context admission and both explicit/negotiated per-allocation modes
all pass on macOS as well. These are test/documentation changes; the measured
Linux allocator binary is unchanged.

The fixed-seed small workload contains 1,218 ttl=0, 1,047 ttl=short and 135 ttl=day
payloads. Applying the 64-KiB per-pair gate to that sequence predicts 1,159, 991
and 79 model decisions respectively: 2,229 total, safely within budget 3,000.
This provides an independent expected dispatch count for the completed trace.
At the 583-decision checkpoint there are no errors or response-cache hits;
observed HTTP time is about 1.37 seconds per allocation.

The per-allocation cold run passed 1,915 decisions / 2,618.8 HTTP seconds with
zero decision errors and zero response-cache hits. A queued validation launcher
waits for successful context completion before the portable Linux integration
fixture, five additional replay repetitions without exact lifetime logging,
and independent inference-overlap audits of the search and gate trials. The
cold lifetime logger is retained for exact object truth, but excluded from the
headline warm RSS and time comparison. The permanent-pair catalogue now includes
all small-run per-allocation answers and probabilities, not just cached policies.
Mesh has not been fetched or built while sections 1–4 remain in progress.

Sections 1–4 are complete and independently validated. The per-allocation cold
run made exactly 2,229 native HTTP calls in 3,048.32 model seconds / 3,060.34 wall
seconds, with no budget fallbacks. Accuracy is 2,110/2,229 (94.66%) on answered
objects and 2,225/2,400 (92.71%) across payloads. The 119 answered errors are
short-TTL objects exceeding the trace lifetime threshold; 56 day-TTL objects
precede admission. Five separate warm repetitions without object logging yield
7.75 MiB for per-alloc vs 7.96 MiB mi and 5.11 MiB context oracle. All 180 main
warm runs, 25 supplemental runs and 285 search/gate trials have zero independently
observed inference overlap. Validation recomputes oracle labels, all search
choices and gates, the full permanent-pair catalogue and per-object truth.

Only after that completion, fetched Mesh master at
2987f883b8695c07a80dc40da67c61f524460dfd and built both recipe configurations.
Both builds pass. Dependencies use archives at the exact CMake/gitlink revisions,
not git clone; the build-only dependency-path patch and archive hashes are in
results/pass9/builds. CMake 4 compatibility is enabled for the old googletest
project. No allocator source code or default randomization/meshing settings are
changed. The recipe's serial make behavior is retained. No packages installed.
The updated benchmark runner maps mesh/nomesh to their separate shared libraries;
the context-phase runner is preserved with its verified original fingerprint in
results/pass9/context-inputs/bench-run.py. Old real-program binaries are preserved
remotely in build/pre-long-settle before adding the optional 10-second sample.
The eleven-workload compaction matrix is now running.

The first compaction block (site-pure-1) completed all 40 warm runs without
failures. Median normal/10-second idle MiB are identical: mi 280.22, keyonly
280.31, oracle-site 41.37, static 43.56, hybrid 43.57, heuristic 228.50, Mesh
270.62, nomesh 328.86. Mesh improves its own twin by 17.7%, while placement is
much smaller on this site-separable synthetic case. Final server-log audits
will cover all eleven blocks. Source inspection shows the pinned Mesh revision
checks its 100 ms interval on eligible frees rather than on a background idle
timer. The report also distinguishes mapping RSS from physical memory sharing;
unchanged RSS cannot establish zero physical compaction, and PSS is not measured.

Site-pure-16 also completed all 40 warm runs without failures. Median normal and
10-second idle MiB: mi 296.55, keyonly 295.95, oracle-site 51.83, static 64.86,
hybrid 63.38, heuristic 255.43, Mesh 290.95, nomesh 331.42. Mesh improves its twin
by 12.2%; the two placement policies remain much smaller. Two of eleven
compaction blocks / 80 warm runs are complete; mixed-context blocks follow.

Site-mixed-1 completed all 50 compaction warm runs. Normal/10-second median idle
MiB are identical: mi 144.70, keyonly 144.80, per-site oracle 145.00, context
oracle 26.05, code-only/site 146.46, Clef/context 28.12, hybrid/context 28.12,
heuristic 146.87, Mesh 139.98, nomesh 170.27. Mesh saves 17.8% against its twin;
context-aware placement saves about 80.6% against keyonly. The per-site controls
still show no placement headroom. Three blocks / 130 warm runs are complete.

Site-mixed-16 completed all 50 compaction warm runs. Normal/10-second median idle
MiB are identical: mi 146.42, keyonly 146.82, per-site oracle 149.71, context
oracle 33.52, code-only/site 154.62, Clef/context 46.73, hybrid/context 47.33,
heuristic 165.64, Mesh 149.88, nomesh 172.70. Mesh saves 13.2% against its twin
but remains above plain mimalloc; context-aware placement remains much smaller.
All four synthetic blocks / 180 warm runs are complete, with no failures.
The Redis compaction blocks have started. Their failed context-placement gates
remain in force; no new Redis model runs are introduced by this comparison.

Redis-mesh completed all 35 compaction warm runs without failures. Normal and
10-second median idle MiB: mi 185.98, keyonly 186.05, per-site oracle 188.01,
context oracle 196.07, search 186.09, Mesh 144.56, nomesh 198.40. This is a real
case where compaction improves the measured RSS and the tested context placement
tables do not: Mesh saves 27.1% against nomesh and 22.3% against mimalloc.
Median workload CPU is 2.13 s Mesh vs 1.80 s nomesh and 1.35 s mimalloc; wall
including common waits is 23.49 / 23.24 / 22.82 s. The extra first-cycle idle can
change second-cycle layouts, so this comparison is not pooled with the original
short-settle headroom measurements. Five blocks / 215 warm runs are complete.

Redis-drop completed all 35 compaction warm runs. Median normal/10-second idle
MiB: mi 269.41, keyonly 285.60, per-site oracle 270.20, context oracle 284.31,
search 286.48, Mesh 92.40, nomesh 331.20. Mesh saves 72.1% against its twin and
65.7% against mimalloc, while this dispatch context still gives no table saving.
Median workload CPU: Mesh 0.89 s, nomesh 0.53 s, mi 0.34 s. Six blocks / 250
warm runs are complete without failures. Redis-sessions follows.

Redis-sessions completed all 35 compaction warm runs. Normal/10-second median
idle MiB: mi 48.03, keyonly 48.21, per-site/context oracles 50.02, search 48.20,
Mesh 68.25, nomesh 264.00. Compaction saves 74.1% against its own twin, but Mesh
still uses more RSS than plain mimalloc. This is why both baselines are reported.
All three Redis blocks and four synthetic blocks are complete: 285 warm runs,
zero allocator failures. SQLite, LevelDB and the two RocksDB workloads follow.
The optional additional database request-context hooks were not added; these
four programs retain their per-site oracle controls in the compaction matrix.

SQLite completed all 25 compaction warm runs. Normal/10-second median idle MiB:
mi 78.94, keyonly 79.01, oracle-site 82.10, Mesh 317.53, nomesh 317.52. Meshing
shows no measurable RSS benefit against its twin here, and both Mesh variants
use about four times mimalloc's RSS. Median workload CPU is 0.44 s Mesh,
0.29 s nomesh and 0.15 s mimalloc. No vendor allocator tuning was applied.
Eight blocks / 310 warm runs are complete; LevelDB is running.

LevelDB completed all 25 compaction warm runs. Normal/10-second median idle MiB:
mi 87.59, keyonly 87.72, oracle-site 87.92, Mesh 78.43, nomesh 177.30. Mesh saves
55.8% against its twin and 10.5% against mimalloc. Nine blocks / 335 warm runs
are complete without failures. The two RocksDB blocks remain.

RocksDB-cache completed all 25 compaction warm runs. Normal/10-second median
idle MiB: mi 125.15, keyonly 128.47, oracle-site 114.58, Mesh 106.54, nomesh
129.02. Mesh saves 17.4% against its twin and 14.9% against mimalloc. The later
oracle median is 8.4% below mimalloc, but its five-run range (111.11–128.12 MiB)
overlaps mimalloc (123.33–137.04); Mesh spans 100.18–122.66. This descriptive
compaction matrix is not pooled with the earlier headroom gate or used as a
post-hoc model gate. No additional database context hook/model experiment was
added. Ten blocks / 360 warm runs are complete; RocksDB-churn is last.

RocksDB-churn completed all 25 warm runs. Normal/10-second median idle MiB:
mi 24.96, keyonly 25.22, oracle-site 26.25, Mesh 37.67, nomesh 68.52. Mesh saves
45.0% against its twin, but mimalloc remains smaller. Median wall/CPU seconds
are mi 95.31/271.12, Mesh 92.49/249.61, nomesh 91.23/245.78. This completes
all eleven compaction blocks: 385 warm runs, zero allocator/workload failures.
All eleven independent inference audits pass with zero overlap. Normal and
10-second median RSS are exactly equal in all 77 allocator/workload groups.

Mesh saves more than 5% RSS against nomesh on 10/11 workloads (SQLite is the
exception), and against mimalloc on four real workloads: Redis eviction, Redis
drop, LevelDB and RocksDB-cache. Placement remains much smaller on all four
synthetic cases. The report includes all idle/long-idle, peak, wall and CPU costs,
both baselines, full ranges, a visually checked PNG/SVG comparison, and explicit
RSS/PSS and free-triggered-meshing limitations.

After measurements and audits finished, upstream Mesh unit checks passed:
35/35 enabled tests; nomesh 28 passed and 7 meshing-specific tests skipped.
The measured library SHA256 values are unchanged before/after these checks.
The unit-check script now explicitly rebuilds each configuration on future runs,
so rerunning it cannot mislabel upstream's shared unit-binary output path.
The source fetcher can restore absent source archives using the recorded commit
and archive hashes, without following a newer master or making git writes.

Final validation passed: all six context blocks, the unlogged per-allocation
performance comparison, and all eleven compaction blocks are complete. Across
875 independently audited warm/search/gate intervals there is zero inference
overlap. All 279 recorded input fingerprints verify (the historical context
runner uses its preserved snapshot). Every launcher status is zero. No owned
benchmark, sidecar, or test jobs remain running. The original model server
(PID 970221) remains healthy and was left available; promptlab was not touched.
The compact evidence, plots, validation and build/test logs are copied locally.
Raw traces, decision caches and full run stdout/stderr remain on the test machine.
The remote-address scan is clean; tools/promptstudy.py is unchanged. Everything
is left uncommitted, with no git writes, sudo, or system-package installation.

## Pass 10 — review 2, initial state and fixed controls

Read SPEC-REVIEW2.md, review 2, RESULTS.md and this journal. Initial remote
inspection found no owned benchmark/sidecar jobs; the existing model server
(PID 970221) is running. Prior evidence is preserved. No promptlab access or
changes are needed. The four findings are accepted; no disputed measurement
is being substituted for the requested reruns.

Before any new experiment, the deterministic controls are fixed as follows.
Rules-neutral starts transient with P(transient)=0.5. Rule-names starts permanent
iff any symbolized stack function name contains cache, index, table, global,
config, intern, or registry (case-insensitive), otherwise transient. Rule-ttl
starts permanent iff the supplied context contains the literal ttl=day,
otherwise transient. The latter two use one-hot priors. All three retain the
same 64-KiB admission, placement, sampling and continuous C hybrid rules.
No rule will be tuned after observing results. Opaque names map the five
allocation wrappers in source order to fn_a through fn_e; plausible names map
them to buf_get, resp_build, conn_attach, entry_put, obj_new. TTL values map
0/short/day to k=0/1/2 or class=a/b/c; the description stays byte-identical.

Work order is F1 fix/tests, live heuristic and neutral rules, semantic rules,
naming builds, server matrices, fresh small per-allocation collection, then
real fragbench/defaults and regression measurements. New evidence uses pass10.

F1 combined-mode regression passed on macOS and Linux at sample rates 1 and 64:
12,288 allocations at one site, all sampled bytes freed, zero survivors and
exactly one wrong-permanent-prior demotion with logging both disabled/enabled.
The fixture includes producer-thread exit followed by main-thread frees and
checks that churn actually reuses addresses. Linux full correctness is running.

F2 warm deterministic policies now reject replay at the service boundary and
run from current observations. The replay transport fixture uses random instead
of heuristic. F4 binaries compile the same source with only preprocessor name
and context-string substitutions; descriptions are copied byte-for-byte. Fresh
traces provide each binary's own oracle keys. Server runs compare the original
immediate-purge configuration and defaults on named stacks; the opaque/plausible
ablation uses defaults. Every defaults variant removes every MIMALLOC_* override
and records ordinary/10-second idle at each existing workload cycle. Real programs
with one original cycle retain that protocol. This pass's explicit all-variant
defaults request supersedes earlier model gates for these matched real controls.

Additional macOS hybrid, context and live-protocol integration passed. Historical
RESULTS wording now names the immediate-purge configuration, labels replayed
heuristic schedules, retains the pass-9 logger defect qualification, separates
TTL bucket matching from a model advantage, qualifies original table gates and
source-snippet causality, and states process-RSS, realloc and evidence limits.
For very high-cardinality live runs, compact matrices retain admitted-site exit
statistics plus exact global/coverage totals; full per-site exit statistics stay
in the explicitly linked remote stats file. This is output compaction only.

The first complete-workload Linux attempt passed all 22 trace/random pairs and
allocator integration, then stopped on a harness NameError: the comment added
when switching the replay fixture to random accidentally swallowed the tables
assignment. The assignment is restored on its own line. The launcher failed
closed before any performance run. The replay fixture is tested separately, then
the complete Linux suite is rerun; both failed-attempt logs are retained. No
allocator or measured workload source changed for this harness correction.

The defaults small control will replay the freshly recollected fixed-library
per-object schedule from the immediate configuration, checking size/context/stack
identity and collecting its own exact object lifetimes. This holds answers fixed
across the allocator-options comparison and avoids a redundant second HTTP
collection. Its cold/accuracy record explicitly names the schedule source and
marks inference as not recollected. The immediate small experiment performs the
requested fresh cold collection; all its warm measurements use the fixed library.

The rerun of full Linux correctness passed all 22 trace/random workload pairs,
allocator/C++ stress, combined trace/live tests, context, hybrid, live heuristic,
replay, budget and exact lifetime checks. Fragmentation source-attribution and
TTL/accounting checks passed. The measured library is now frozen. The sequential
server matrices have started; baseline options and every decision-execution mode
are recorded in each run. Local copies of the correctness evidence are retained.

Pass 10 completed results/pass10/immediate/named/site-pure-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Pass 10 completed results/pass10/immediate/named/site-pure-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Pass 10 completed results/pass10/immediate/named/site-mixed-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Pass 10 completed results/pass10/immediate/named/site-mixed-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

The four immediate-purge server blocks are complete and independently audited.
Pure 1/16-thread idle MiB (mi/static/hybrid/live heuristic/neutral/names):
280.21/43.67/43.66/228.61/139.38/43.64 and
296.55/62.67/65.20/259.87/156.20/61.96.
Mixed 1/16-thread (mi/context oracle/static/hybrid/live heuristic/neutral/TTL):
144.70/26.06/28.12/28.10/146.87/75.73/28.09 and
146.43/33.54/46.38/46.67/166.64/89.64/46.29.
Thus the matched semantic rules reproduce the large model-associated reductions
in these named fixtures. Continuous neutral rules capture about 50–59% of the
oracle saving, better than the sparse live heuristic in these four comparisons,
but below the semantic priors. Hybrid has no transitions; neutral has median two
promotions and one demotion, and TTL has two demotions (temporary buffer paths).
These are original-options results, not defaults. Defaults collection follows.

Pass 10 completed results/pass10/defaults/named/site-pure-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

First completed defaults block materially changes the absolute saving. At one
thread site-pure, final ordinary/10-second idle MiB are identical: mi 280.215,
oracle 213.996, static/hybrid/names rule 216.809, live heuristic 286.828,
neutral rules 304.812. Static saves 22.6% of mi under defaults, compared with
84.4% in the new immediate-purge block; the names rule matches it. Cycle zero
must not be hidden: mi is 122.215 at both observations, oracle 122.184; static,
hybrid and names rule fall from about 124.93 ordinary idle to 97.621 at 10 s.
The same sampling protocol is used by all variants. These observations settle
F3 for this workload without attributing the change to an unmeasured mechanism.

Pass 10 completed results/pass10/defaults/named/site-pure-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Default-options site-pure-16 is complete and audited. Final idle MiB:
mi 296.55, oracle 234.80, static 239.98, hybrid 241.92,
live heuristic 305.36, neutral 331.91, names rule 239.74.
The static reduction is about 19.1%, far smaller than under immediate purge;
neutral and sparse heuristic use more RSS than plain mimalloc here. The keyword
rule again matches the useful semantic placement closely. Mixed defaults follow.

Pass 10 reporting/verification update: the RESULTS.md entry point now keeps the
default-options comparison compact and links the full pass report, both-cycle
phase table and per-site probability table. Final validation additionally audits
the five logged per-object warm runs independently for inference overlap and
checks renamed-binary context vocabularies and workload live-byte equality.
These changes affect reporting and validation only; measured inputs stay frozen.

Pass 10 completed results/pass10/defaults/named/site-mixed-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Default-options site-mixed-1 is complete and independently audited. Final
ordinary/10-second idle MiB: mi 146.215, context oracle 112.184, static
115.020, hybrid 115.016, live heuristic 147.145, neutral 158.957, names
147.145, TTL rule 115.016. Static saves about 21.3%; the literal TTL rule
reproduces its useful reduction. The site-only oracle stays at 146.309.
Cycle-zero mi is 66.215 and context oracle 68.246; both remain unchanged at
10 seconds. This further limits the original immediate-purge headline.

Pass 10 completed results/pass10/defaults/named/site-mixed-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

All four named default-options server blocks are complete. Site-mixed-16
final ordinary/10-second idle MiB: mi 170.527, context oracle 138.914,
static 140.070, hybrid 140.125, live heuristic 171.238, neutral 180.023,
names 172.070, TTL rule 140.070. Static saves 17.9%; the TTL rule has
the same median. Oracle range is wide (120.480–138.980 MiB), so the 96.3%
capture is a ratio of descriptive medians, not a precise efficiency estimate.
Plain mi cycle-zero idle is 74.527 MiB and unchanged at 10 seconds. Across
all four named defaults fixtures static-model has no lower median than the
matching names/TTL rule. Renamed fixtures follow with frozen rules and prompts.

Pass 10 completed results/pass10/defaults/opaque/site-pure-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Opaque site-pure-1 is complete and audited. Final idle MiB: mi 280.219,
oracle 213.996, static 283.121, hybrid 304.809, live heuristic 286.883,
neutral 304.801, names rule 283.121. The model labels all five asked paths
transient (P(transient) about 0.57–0.60), including the retained-object path.
Hybrid and neutral both have median two promotions and one demotion.
Relative to the matched named saving, static retains -4.6% and hybrid -38.8%;
negative means an RSS increase, not a surviving positive saving. The oracle
still reduces RSS, while static and the fixed rule have equal medians.

Pass 10 completed results/pass10/defaults/opaque/site-pure-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Opaque site-pure-16 is complete and audited. Final idle MiB: mi 296.547,
oracle 234.859, static 298.574, hybrid 331.879, live heuristic 307.250,
neutral 331.934, names rule 298.746. Hybrid and neutral again show median
two promotions and one demotion. Static is 0.172 MiB below the names-rule
median, but ranges overlap (297.836–299.199 versus 298.258–298.836) and
both exceed plain mi. This is not a useful model-specific saving.
Static/hybrid retain -3.6%/-64.7% of their respective named savings.

Pass 10 completed results/pass10/defaults/opaque/site-mixed-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Opaque site-mixed-1 is complete and audited. Final idle MiB: mi 146.215,
context oracle 112.188, static 147.129, hybrid 158.945, live heuristic
147.129, neutral 158.945, names rule 147.133, TTL rule 147.129. All ten
asked model pairs are transient, including retained fn_e/k=2; its transient
probability is 0.6034. Hybrid and neutral each show median two promotions
and one demotion. Static equals the matching TTL-rule median.
Static/hybrid retain -2.9%/-40.8% of the respective named savings; neither
retains a positive saving here. The correctly labelled context oracle still
reduces RSS under the same workload and options.

Pass 10 completed results/pass10/defaults/opaque/site-mixed-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

All four opaque blocks are complete and audited. Site-mixed-16 final idle
MiB: mi 170.527, context oracle 138.918, static 172.117, hybrid 178.059,
live heuristic 171.129, neutral 178.004, names rule 172.070, TTL rule 172.000.
Hybrid/neutral each have median two promotions and one demotion; their ranges
are broad and overlapping. Static is slightly above both fixed-rule medians.
Static/hybrid retain -5.2%/-24.8% of the respective named savings here.
Across all four opaque comparisons neither has a positive saving over mi;
the trace-fitted oracle still reduces RSS in each. Plausible names follow.

Pass 10 completed results/pass10/defaults/plausible/site-pure-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Plausible-name site-pure-1 gives a positive hybrid result. Final idle MiB:
mi 280.219, oracle 213.996, static 283.121, hybrid 228.746, heuristic
286.887, neutral 304.809, names rule 283.117. Hybrid retains 81.2% of
the named saving and is 54.371 MiB below the names-rule median; their ranges
do not overlap (228.734–228.750 versus 283.113–283.125). Static retains
no positive saving. All initial classes are transient. Hybrid promotes only
entry_put (P(transient)=0.5491), while conn_attach (0.7332) stays transient;
the fixed promotion gate requires P(transient)<0.7. Buffers also stay transient.
This observed benefit uses model probability priors plus runtime rules. It must
remain visible beside the negative opaque and static-model results. Reporting
now explicitly compares both static and hybrid with the matching fixed rule.

Pass 10 completed results/pass10/defaults/plausible/site-pure-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Plausible-name site-pure-16 is complete and audited. Final idle MiB:
mi 296.547, oracle 234.855, static 298.770, hybrid 267.992, heuristic
305.125, neutral 332.004, names rule 298.465. Hybrid shows one promotion
and zero demotions, with a broader 254.797–268.051 MiB range; the names
rule range is 297.969–298.934 MiB. Hybrid is 30.473 MiB below that rule
median and saves 9.6% against mi. Static has no positive saving.
Static/hybrid retain -3.9%/52.3% of their respective named savings.
Both plausible pure workloads therefore show a benefit for the model-prior
plus runtime-rule combination, while the static labels alone do not.

Pass 10 completed results/pass10/defaults/plausible/site-mixed-1: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Plausible site-mixed-1 is complete and audited. Final idle MiB: mi 146.215,
context oracle 112.188, static 147.133, hybrid 120.945, heuristic 147.137,
neutral 158.945, names rule 147.137, TTL rule 147.133. Hybrid is 26.188 MiB
below the TTL-rule median; its 120.938–120.953 MiB range does not overlap
that rule's 147.133 MiB observations. Static equals the TTL-rule median.
Every warm hybrid run promotes only obj_new/class=c, once, with no demotion.
The model answers all pairs transient initially; its obj_new transient priors
are 0.7017/0.7082/0.6789 for class=a/b/c. The fixed 0.7 gate admits only
class=c for promotion. These probabilities are close to that gate, so this
is evidence for this fixed naming/context ablation, not robustness to all
renamings or a held-out real application. Hybrid retains about 81% of its
named saving. One 16-thread server block remains before per-object recollection.

Pass 10 completed results/pass10/defaults/plausible/site-mixed-16: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Pass 10: server block completed; matrices and inference audits retained under results/pass10.

All 16 server blocks are complete and independently audited. Plausible
site-mixed-16 final idle MiB: mi 170.531, context oracle 138.914, static
172.117, hybrid 150.066, heuristic 171.438, neutral 178.055, names/TTL
rules both 172.070. Hybrid has one promotion and no demotions, with range
148.016–152.078 MiB; TTL range is 171.949–172.129. It beats that fixed
rule by 22.004 MiB and saves 12.0% against mi.
Static/hybrid retain -5.2%/67.3% of their named savings here. Across
all renamed comparisons static retains no positive saving; opaque hybrid
also loses the saving, while plausible hybrid retains about 52–81%. This
benefit over the specified fixed rules is tied to probability priors and
runtime checks in these particular synthetic ablations. The close mixed
probabilities around the fixed 0.7 gate remain visible in the site table.

Fresh fixed-library logged per-allocation cold inference has now started,
followed by logged warm checks and separate unlogged performance repetitions.

An independent local check recomputed all 152 server policy medians from
760 accepted warm observations and verified five distinct repetitions, audit
hashes/zero overlap, default-option environments, both renamed context
vocabularies, and identical requested live bytes in every corresponding phase.
The compact check record is results/pass10/server-independent-check.json.

Protocol clarification: the defaults series adds the requested quiet 10-second
observation after each original idle phase. This also delays the following
cycle, whereas the immediate series preserves its original shorter waits.
Every variant within a series is matched, but the across-series difference
changes idle duration as well as options; it cannot assign a causal share
to those two changes separately. The report and phase-table legend now state
this explicitly. No performance input or measurement was changed.

Fresh per-allocation cold recollection finished: 2,229 new HTTP requests,
3,050.571 HTTP seconds and 3,062.905 target wall seconds. The fixed combined
logger reports 37 samples / 2 survivors, replacing the historical defective
37 / 37 result. All five logged warm checks also report 37 / 2. Separate
unlogged interleaved performance runs are collecting before accuracy/RSS
publication; matching sampled counts do not imply every runtime request field
is identical, since logging still has memory overhead.

Pass 10 completed results/pass10/immediate/named/per-alloc-small: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

The fresh immediate-options small block is complete and audited. All eleven
cold/logged-warm/unlogged-warm records agree at 37 samples / 2 survivors.
Unlike the old logger, every warm request now matches the cold request exactly:
all ten replay-drift counters are zero, and request-drift.json has no changed
fields. Object accuracy is unchanged at 2,110/2,229 (94.66%), versus 91.12%
always-transient and 39.90% permanent recall. The literal TTL rule reproduces
all 2,229 model-answered classes. Five unlogged idle medians: mi 7.965 MiB,
key-only 8.055, site oracle 8.051, context oracle 5.117, per-alloc 7.770.
This remains a small RSS reduction despite exact per-object requests and high
headline accuracy. Defaults uses this newly collected schedule with fresh
lifetime logging; its logged checks have started with the 10-second protocol.

Pass 10 completed results/pass10/defaults/named/per-alloc-small: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Pass 10: peralloc block completed; matrices and inference audits retained under results/pass10.

The defaults small block is complete and audited. Final unlogged idle MiB:
mi 8.129, key-only 8.223, site oracle 8.219, context oracle 6.219, per-alloc
8.453. The per-object policy has no positive saving in this defaults protocol.
All eleven sample/survivor records again equal 37 / 2, and all logged/unlogged
warm request streams match the defaults logged reference exactly.

The defaults reference reuses the newly collected immediate schedule. Compared
with that source schedule, all defaults runs have 1,200/2,229 changed runtime
states: process.rss, process.committed and process.alloc_clock differ in 1,200
requests, and site.oldest_age_bytes in 68. The defaults series adds a phase
observation between cycles; the model's per-object prompt does not consume
these runtime fields. Size, context/signature and frames still match under
the strict replay checks. source-schedule-drift.json records this distinct
cross-protocol comparison so it cannot be confused with the zero drift
between logged and unlogged runs within each series. Real defaults now follow.

Independent local object-accuracy verification passed both small series.
Recomputing each truth label from birth/death clocks and half the sum of all
requested sizes gives confusion [[2031,0],[119,79]] in both, 3,255,808
correct model-answered bytes, and 2,229/2,229 TTL-rule agreement. Immediate
has 2,414 objects and allocation clock 3,695,936; defaults has 2,418 and
3,698,928, making the extra phase-observation allocation volume explicit.
See results/pass10/small-independent-check.json.

Pass 10 completed results/pass10/defaults/named/redis-mesh: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

First real defaults block, redis-mesh, is complete and audited. Final
ordinary/10-second idle MiB: mi 185.973, site oracle 188.031, context
oracle 196.074, static-site 193.020, static/context 193.008, hybrid
208.965, heuristic 231.000, neutral 219.031, names rule 192.961, TTL
rule 193.000. None saves idle RSS versus mi. Target CPU medians are
1.363 s for mi, 1.781 s for static/context and 1.782 s for hybrid; they
exclude sidecar CPU. Both original cycles remain in the full phase table.
The new model runs were included despite the old failed gate, as requested.

Pass 10 completed results/pass10/defaults/named/redis-drop: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Redis-drop defaults is complete and audited, with a severe negative live-context
result. Final ordinary/10-second idle MiB: mi 274.332, key-only 288.781,
site oracle 274.582, context oracle 290.266, static-site 281.422,
static/context 4246.531, hybrid 4245.867, heuristic 4243.613, neutral
4244.930, names rule 4243.910, TTL rule 4244.422. Thus context-aware live
RSS is about 4.15 GiB, not a memory saving. Static/context target CPU is
28.235 s versus mi 0.332 s, and wall is 39.493 s versus 11.924 s including
the prescribed quiet time. All live context controls exhibit this cost.

Representative first warm static/context record: 495,328 site/context entries,
9 model-asked entries and 45.0% of requested bytes unasked, versus 629 entries
and 13 asked in the site-only record. The compact matrix retains admitted-size
site statistics and exact global/coverage counters; the full exit statistics
remain at its recorded remote path. This high-cardinality state overhead must
be prominent, and must not be described as a model-inference cost.

Pass 10 completed results/pass10/defaults/named/redis-sessions: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

Redis-sessions defaults is complete and audited. Final ordinary/10-second
idle MiB: mi 157.406, site oracle 159.387, context oracle 161.562,
static-site 164.582, static/context 162.238, hybrid 165.258, heuristic
172.469, neutral 160.301, names rule 172.609, TTL rule 165.523. No tested
variant has a lower median than mi. Ranges are broad: mi 151.691–189.266,
static/context 126.855–172.984, hybrid 147.148–172.883 MiB. These overlap
and do not support a precise effect estimate. Three incomplete warm coverage
probes were retained outside the published groups; missing schedule entries
were filled before their replacement measurements. All published warm groups
still have five successful repetitions and zero inference overlap.

Pass 10 completed results/pass10/defaults/named/sqlite: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

SQLite defaults is complete and audited. Final ordinary/10-second idle MiB:
mi 207.020, oracle 208.949, static 209.875, hybrid 209.762, heuristic
209.824, neutral 209.902, names rule 209.773. All tested placement variants
exceed mi; ranges are narrow. Target CPU is 0.108 s for mi, 0.117 s for
static and 0.119 s for hybrid, excluding the sidecar. This default-options
baseline is materially above the historical immediate-purge SQLite value;
the two series remain separately labelled. LevelDB follows.

Pass 10 completed results/pass10/defaults/named/leveldb: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

LevelDB defaults is complete and audited. Final idle MiB: mi 147.059,
oracle 147.652, static 151.988, hybrid 152.016, heuristic 156.406,
neutral 152.219, names rule 152.613. No tested median improves on mi.
Plain mi remains 147.059 after ten seconds; neutral changes by only 0.004 MiB.
Oracle range includes one lower observation (141.059–147.699), while static
is 151.914–152.125 and hybrid 149.504–152.480. The descriptive medians
and full ranges remain separate. RocksDB cache and churn are next.

RocksDB's live names-rule runs expose substantial symbol-resolution wall cost.
The sidecar resolves each new frame with addr2line and caches it within that
process. Warm model replay bypasses prompt preparation/symbolization as well
as HTTP, whereas rule-names does this work live. Target CPU excludes both
sidecar and its symbolizer children. The report/README now explicitly bound
timing comparisons to these implemented paths; no end-to-end model-versus-rule
speed advantage is inferred. Measured policy code remains unchanged.

Pass-10 RocksDB-cache progress: coverage probes during the third repetition exposed additional internal stack keys. The existing fill/retry procedure converged for static-model and hybrid; all fill/probe records remain excluded from warm medians. The live names rule spends several minutes per process in symbolization, whereas warm model replay bypasses prompt preparation and symbolization as well as HTTP inference. This timing asymmetry is now explicit in the evidence README and report. Measurement inputs remain frozen. Local Python syntax and git diff --check passed during this wait.

Pass 10 completed results/pass10/defaults/named/rocksdb-cache: five interleaved repetitions, current-statistics deterministic policies, zero inference overlap. See matrix.json and the updated phase table.

RocksDB-cache defaults completed all five interleaved repetitions and its independent inference audit. Final idle MiB: mi 144.246 (133.000–152.816), oracle 160.023, static-model 242.895, hybrid 1019.105 (941.098–1112.109), live heuristic 236.773, neutral 237.855, names rule 697.719. There is no model saving; hybrid is about seven times the mimalloc median. Names-rule median wall is 397.451 seconds, versus mi 14.576 and warm-replayed static 14.736. Symbolization remains part of the live rule cost, not a fair estimate of end-to-end model-versus-rule latency. The ordinary and 10-second medians match except names-rule changes by 0.016 MiB. No measurement inputs were changed. The report headline now explicitly includes the hybrid RSS failure.
