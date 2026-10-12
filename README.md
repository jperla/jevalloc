# jevalloc

Does predicting allocation-site lifetime improve malloc? This experiment routes transient and permanent allocations to separate per-thread mimalloc heaps. A local Clef-flash
model makes decisions **while the program runs**; recorded decisions are replayed to
measure the allocator without today's inference latency. A histogram heuristic and
same-workload trace oracle are controls. This is a research prototype.

**Current results: [RESULTS.md](RESULTS.md).** Pass 9 adds application-supplied
request context and a small per-allocation experiment to the code-only model,
hybrid and heuristic comparisons. Real-program headroom searches precede model
evaluation. Mesh/nomesh compaction comparisons follow the context measurements;
earlier regression matrices remain as history.
[CODEX-REPORT.md](CODEX-REPORT.md) records completed work and remote job status.

## Build and test

Linux x86-64 is the measured platform; macOS arm64 remains supported. Requires a C/C++
compiler, CMake 3.19+, Python 3 (standard library only), and the dependency checkouts:

```sh
git clone --branch v2.2.4 --depth 1 https://github.com/microsoft/mimalloc third_party/mimalloc
git clone https://github.com/daanx/mimalloc-bench third_party/mimalloc-bench
git -C third_party/mimalloc-bench checkout 69c41ed7e6419fb5d362eb04ba34b850ec89dc8e
make
make extras  # Linux: Redis and SmartHeap, downloaded and built under build/
make test
```

Vendor trees are not modified. `tools/dependency-revisions.json` records the original
revisions. `make allocator` builds just the libraries and helper programs; `make`
also builds benchmarks with debug information and frame pointers. `make test` runs
all available workloads in trace and random-table modes, C/C++ stress and site-key
checks, live protocol tests and replay tests. A real-model smoke test runs when the
local server is available, otherwise skips. Linux extras add sh6bench, sh8bench and
Redis to the workload list. No system package installation is performed by the tools.

Outputs are `build/libjevalloc.so` and matching `build/libmimalloc.so` on Linux;
macOS uses `.dylib`. The plain control and embedded mimalloc 2.2.4 core use matching
compiler flags. Linux uses ELF interposition; macOS uses mimalloc's generated
zone/interpose integration. C allocation APIs, aligned allocation, string duplication
and upstream C++ new/delete forms route through the shim.

## Live decisions

On the configured Beelink, `scripts/model-server.sh start` serves
`~/jevalloc/models/Clef-Flash-Q8_0.gguf` using `~/jevalloc/llama.cpp/build-vk`, Vulkan
on the Radeon 780M, `-ngl 99 -t 4`, bound to `127.0.0.1:8765`.
`/v1/systemone` accepts the Jev choice request shape. There is no paid API involved.
The script assumes these model/server files already exist.

```sh
python3 tools/jevd.py --socket "$PWD/build/jevd.sock" --policy hybrid \
  --cache results/example-cache --log results/example-decisions.jsonl \
  --max-model-decisions 3000 --model-backend vulkan &
sidecar_pid=$!
LD_PRELOAD="$PWD/build/libjevalloc.so" \
  JEVALLOC_MODE=live JEVALLOC_HYBRID=1 JEVALLOC_SOCKET="$PWD/build/jevd.sock" \
  JEVALLOC_STATS_OUT="$PWD/results/example-stats.json" \
  build/bench/cfrac 17545186520507317056371138836327483792789528
kill "$sidecar_pid"
```

Wait for the socket to exist before launching the application. The benchmark runner
does this automatically. On macOS use `DYLD_INSERT_LIBRARIES` and `.dylib`.

Policies: `hybrid` (default) asks once using `stack-v1`, exactly like
`static-model`, then the allocator applies fixed rules to sampled runtime evidence.
Set `JEVALLOC_HYBRID=1` on the application when using this policy; the benchmark
runner does this automatically. At least 16 samples and 5% sampled requested bytes
freed demote a site to transient. Promotion requires no sampled free ever,
P(transient)<0.7, an allocation clock >=64 MiB, and an oldest live reservoir sample
older than half that clock. A confident transient prior cannot be promoted merely
because no frees have happened. Changes affect future allocations.

`model-reask` retains pass 7's repeated model queries (`model` is a compatibility
alias). `static-model` keeps the first answer forever. First-sight prompts include
up to twelve named stack frames and a neutral description, with no source code;
`stack-v1-nodesc` omits the description. `heuristic` uses the previous sampled
free/age rule. `oracle` reads `--table`; `random` is seeded.
All requests, probabilities, responses, model latency and provenance are logged.

Each (site, context signature) pair uses the default class until it has successfully
requested at least 64 KiB. Empty context preserves per-site behavior.
Only then can the allocator ask the sidecar. Cross-thread counter batching can delay
this threshold. `--max-model-decisions` defaults to 3,000 including cache hits,
rechecks and replay coverage fills. At exhaustion new sites default transient and
existing sites keep their class without further rechecks. Fallbacks do not enter
the model cache. `--default-class` should match `JEVALLOC_DEFAULT` when run manually.

First-sight model answers use argmax. Under `model-reask`, an initially transient site can become permanent
only when a recheck gives permanent probability >=0.8 and the oldest still-live
reservoir sample has aged through strictly more than a quarter of the current
process allocation clock. Replayed runs apply recorded decisions with unchanged
instrumentation and no inference; drift from the recorded request is logged.

The historical CPU-to-Vulkan transition preserved its cache identity and answers. Every
model decision records its originating backend; the transition manifest and original
CPU logs are archived in results. Those historical cfrac cold timings include CPU cache reuse. The transient/permanent pass uses a new cache identity and reuses no short/long decisions.

## Runtime controls

| Variable | Default | Meaning |
|---|---|---|
| `JEVALLOC_MODE` | `run` | `run`, `trace`, or `live` |
| `JEVALLOC_TABLE` | absent | Text lines `hex-site-key class`, classes 0/1 |
| `JEVALLOC_SHORT_BYTES` | `1048576` | Fixed-S control / quick-free observation threshold |
| `JEVALLOC_DEFAULT` | `0` | Unknown site's class: transient/permanent = 0/1 |
| `JEVALLOC_DEPTH` | `4` | Site-key depth, clamped to 1–16 |
| `JEVALLOC_MODEL_DEPTH` | `12` | Wider context captured on cache misses for trace/live |
| `JEVALLOC_HEAPS` | tagged | `legacy` retains the original untagged heaps |
| `JEVALLOC_SAMPLE_FILTER` | page-local | `0` disables the filter; `spatial` selects the older global filter |
| `JEVALLOC_POLICY` | segregation | `none`: bypass key, one heap; `keyonly`: key/lookup on default heap; `explicit`: one explicit heap |
| `JEVALLOC_TRACE_OUT` | `jevalloc-trace.jsonl` | Trace at orderly exit |
| `JEVALLOC_SOCKET` | absent | Live Unix socket |
| `JEVALLOC_MIN_SITE_BYTES` | `65536` | Successful requested site bytes before sidecar admission; `0` is a protocol-test control |
| `JEVALLOC_CONTEXT` | `1` | Set `0` to ignore application context for per-site controls |
| `JEVALLOC_PER_ALLOC` | `0` | Send every admitted allocation with `--policy per-alloc` |
| `JEVALLOC_OBJECT_TRACE` | absent | Optional exact object events for small accuracy diagnostics |
| `JEVALLOC_HYBRID` | `0` | Enable local runtime rules using the hybrid sidecar prior |
| `JEVALLOC_SAMPLE` | `64` | Sample one in this many successful allocations per thread/site |
| `JEVALLOC_TIMEOUT_MS` | `30000` | One deadline covering socket connect/send/receive |
| `JEVALLOC_STATS_OUT` | `jevalloc-stats.json` | Live accounting and per-site requested-byte totals |

Requests at the same (site, signature) pair serialize decisions. Cached policies
reuse the first answer; per-alloc requests each receive their own answer. `model-reask`/heuristic rechecks target 1,024, 8,192,
65,536 and 524,288 further successful site allocations (at most four), approximately
when multiple threads contribute batched counters; a new class affects only
future allocations. Free supports cross-thread ownership. A failed sidecar opens a
process-lifetime circuit breaker and uses the default class without hanging. Sampled
pointer records support cross-thread frees; counters are approximate concurrent
snapshots. Blocked time includes threads waiting for another thread's decision.

## Keys, lifetimes and controls

A bounded frame-pointer walk checks stack bounds, alignment and increasing links,
examining at most 64 links for the key and, on a miss, at most 64 more for model
context. Linux uses a small initial-exec TLS record and a lazy 64-entry per-thread
raw-stack cache; cache hits avoid image searches and table probing. Misses normalize
return addresses by image base and include the image path in the stable key.
Missing frame pointers truncate context. Keys depend on exact binaries, paths,
libraries and depth; rebuilding or relocating can invalidate tables. Dynamic
unloading/reuse, alternate stacks and post-fork synchronization are not validated.
macOS registers images through dyld and retains its loader-safe pthread context.

Lifetime is measured in total requested allocation bytes, not wall-clock seconds.
Permanent means never freed, or freed after strictly more than half the program's
final allocation volume; everything else is transient. Trace mode tracks exact
allocations under a mutex. Freed lifetime records are spooled to an unlinked file
beside the trace output and classified at exit using exact integer comparisons.
Schema 3 contains 25%, 50%, 90% and never-freed-only truth plus fixed-S controls.
Internal/bootstrap and post-snapshot work are excluded; abrupt exits lose the trace.

The oracle chooses each site's majority class by bytes from a prior execution of
the same workload. It is a hindsight label-accuracy control, not a held-out model or
a mathematical upper bound on allocator performance. Random is seeded; size-only
uses a fixed mean-request threshold: at most 256 bytes is transient, otherwise permanent. The original run used untagged heaps. The new instrument uses tagged, reclaim-enabled
heaps with identical explicit purge options for every variant; its results are
reported separately from the historical matrix.

```sh
LD_PRELOAD="$PWD/build/libjevalloc.so" JEVALLOC_MODE=trace \
  JEVALLOC_TRACE_OUT="$PWD/results/example.jsonl" \
  build/bench/cfrac 17545186520507317056371138836327483792789528
python3 tools/symbolize.py results/example.jsonl -o results/example.sites.jsonl
python3 tools/oracle.py results/example.jsonl -o results/example.oracle.txt
python3 tools/baselines.py results/example.jsonl -o results/example-controls
```

`tools/label.py` remains an optional offline labeling client, separate from the live
experiment. It excludes trace runtime statistics from model input and caches raw
responses. The Beelink pass uses the local sidecar instead.

## Pass 6 sequence

Run `scripts/pass6-validate.sh` for full Linux correctness, workload validation and
the five-repetition instrument. Then `scripts/pass6-finish.sh` runs site-pure
sensitivity, full fragbench, the regression matrix and audited reports, sequentially.
Progress is in `results/pass6/stage.txt`. `tools/pass6_report.py` publishes only
complete audited matrices and reports remaining performance-target misses.
Historical short/long results stay archived as wrong-boundary evidence.

## Reproduce the matrix

```sh
# On the Beelink, after build, extras, tests and model-server startup:
python3 tools/calibrate.py
python3 tools/live_cost.py
python3 tools/provenance.py
nohup python3 bench/run.py --name beelink --procs 16 --reps 5 \
  --max-model-decisions 400 --resume > results/bench.log 2>&1 &
```

The current detached pipeline is `scripts/pass5.sh`; use its stage/status files.
Generate the audited report on the test host with `python3 tools/pass5_report.py`.
Fetch the `results/pass5/`, `results/fragbench-two/`, `results/frag-sensitivity/`
artifacts, regression JSON, and RESULTS.md after completion. Older
`scripts/beelink.sh` and `scripts/finalize-beelink.sh` refer to historical layouts.

The report generator refuses incomplete matrices or an unresolved inference-interference audit. This pass preserves and replaces headline blocks that overlapped a separate prompt study; the server request log and conservative timing audit are retained with the results. The runner fingerprints inputs,
libraries, tables and measurement code before resuming. Run one benchmark process
at a time; keep model inference and calibration out of headline repetitions.

The full matrix has 22 Linux configurations, twelve variants and five interleaved
repetitions, plus cold live runs and explicit coverage-fill/probe runs. Headline live
runs replay by stable key and decision ordinal; differing runtime requests are
logged. This measures the recorded decisions, not what the model would decide on
changed state. The model server performs no inference during accepted replay runs.

Reports include wall/CPU time, peak RSS, bench.sh throughput-normalized scores,
median/min/max, ratios to plain mimalloc and geometric means. Unasked byte shares
use actual exit-time site totals. Accuracy includes default-class fallbacks and
reports matched-key coverage. “Chip time” subtracts the sum of thread-blocked
intervals from wall time; it can be negative for concurrent programs and is only an
approximation. Headline replay is the preferred comparison. OS `wait4` measures
the benchmark child; sidecar/model memory is excluded, allocator bookkeeping is
included. Redis server alone receives the allocator; its client is unmodified.

The host's existing VM and desktop remain running. Small timing differences may be
noise. See the report before interpreting any prediction accuracy as a malloc win.

## Allocator implementation notes

Linux key normalization currently supports the **startup image set only**. Programs
whose allocating call paths come from subsequently `dlopen`ed images are unsupported;
unloading/reusing images is also unsupported. Raw-stack cache hits compare frame count
and PCs as well as their hash.

The key cache uses a lazy anonymous mapping, released at thread exit. Its 64 compact
entries need 12 KiB; trace/live mode adds 16 KiB for the wider normalized frame data. This avoids
committing a mimalloc medium-object page just for a small per-thread cache. `none` routes all
allocation APIs to the default mimalloc heap; `keyonly` captures/looks up a key and
uses that same heap. `JEVALLOC_POLICY=explicit` retains the old single explicit heap
control. The default class policy uses `mi_heap_new_ex(class+1,false,0)`.
`JEVALLOC_HEAPS=legacy` retains the untagged/no-reclaim policy for comparison. A patch
in `patches/` is applied only to the build-tree mimalloc core: reclamation prepares
matching tagged heaps before taking ownership, including when a receiving thread
has never allocated in that class. Metadata failure leaves the segment abandoned.
The plain mimalloc baseline uses the unmodified vendor sources.
On Linux, a core thread-exit hook releases the lazy cache and flushes live shards
before mimalloc abandons the thread's heaps; it reuses mimalloc's destructor
lifecycle. macOS retains its pthread context destructor. A diagnostic-only key
request in none mode initializes mimalloc's thread lifecycle too. The core also
exposes its ordinary free body with a known page, so live mode can reuse the page
lookup from its sample filter. The two entry points share one implementation.

Live allocations update thread-owned success counters and merge every 4,096 successes per thread/site (also before decisions and at thread exit).
Failed requests do not advance the byte clock or successful counts. A first-site
classification can still be requested before an eventual allocation failure; rechecks
are scheduled from successful counts. Cross-thread lifetimes use a batched approximate
byte clock; single-thread decisions remain deterministic. Sampled free histograms are
byte weighted. The heuristic uses the same fixed S threshold as trace truth, but sampled live
lifetimes are approximate and current survival is not proof of never being freed. Exit statistics read published totals if workers still run, omitting
their unmerged thread/site batches (up to 4,095 allocations each). Private owner
counters are never read by another thread. Joined/exited threads publish all successes.
The sampled-pointer negative filter uses the existing, otherwise unused padding word
in mimalloc 2.2.4's page metadata (64-bit targets). It does not enlarge the page
structure. Saturated counts remain positive until the page is cleared, so collisions
cannot hide a sampled free. `JEVALLOC_SAMPLE_FILTER=spatial` selects the earlier global
spatial filter; `=0` disables the filter for diagnostics. The exact pointer table
still determines sample membership. Allocation counts and sampling remain unchanged.
Live cache misses use a separate thread-local site index, released at thread exit,
rather than scanning every previously seen site.
Suitable reallocs remain in place and retain their page class; trace/live bookkeeping
closes the old logical lifetime and starts a new one at the realloc site.

`jevd --prompt stack-v1` uses the exact first-sight wording in SPEC-STACK.md,
neutral hand-written descriptions from `descriptions/<program>.txt`, and up to
twelve function/file/line frames. Rechecks append freed-quickly, freed-later and
still-alive sampled-byte shares, plus the oldest still-live reservoir sample's age
in allocated bytes. At 100% still alive, the prompt explicitly notes that eventually
freed objects also look this way early on. `stack-v1-nodesc` omits descriptions.
Legacy `v2` uses the pass-6 wording, snippets and `descriptions-leaky/` for ablations.
Decision schema 4 and policy-cache version 3 reject earlier replay/policy decisions.
Trace schema remains 3. The tokenizer limits state to 3,000 tokens.
The unknown-site default is transient. `all-transient` and `all-permanent` are controls.
`tools/oracle.py --short-bytes S` recomputes exact power-of-two thresholds from trace
histograms; for other thresholds use a trace recorded with `JEVALLOC_SHORT_BYTES=S`.

`python3 fragbench/run.py --instrument --name frag-instrument` measures the
instrument before the full matrix. A negative result requires investigation; the
pass-6 sequence stops for investigation. Both
use five interleaved repetitions. Phase RSS is read
from `/proc`, alongside live requested bytes (synthetic) or Redis `used_memory`
(which also includes metadata/usable-size accounting). Purge options are identical:
`MIMALLOC_PURGE_DELAY=0`, `MIMALLOC_ARENA_PURGE_MULT=1`,
`MIMALLOC_PURGE_DECOMMITS=1`. Synthetic workers wait 250 ms and issue a small allocation
pulse before a further 250 ms settle, to service deferred purge while threads remain
alive. Redis waits 500 ms. The Mesh adaptation uses the paper's 700,000 × 240-byte
and 170,000 × 492-byte insertions with a 100 MB LRU limit, fixed work rather than its
7.5-second deadline, and active defragmentation off. Its source is cited in the client.

The live heuristic uses a deterministic uniform reservoir of 128 sampled allocations
per site, retaining birth, requested size and free status after the object is freed.
At a decision, at least 16 entries are required. Entries strictly older than the
count median age (lower median for even counts) vote by requested bytes: permanent
if strictly under 5% were freed; otherwise transient. Empty/equal-age evidence uses
transient. Reservoir replacement is independent of survival; no final-run length
is assumed. Sampled updates use a per-site lock, while unsampled paths are unchanged.
`tools/oracle.py --permanent-percent 25|50|90|never` selects sensitivity truth.

The heuristic additionally requires the oldest still-live reservoir sample to be
strictly older than one quarter of the current allocation clock before choosing
permanent. Otherwise it selects transient, including when no live sample exists.
The age and clock use the same batched snapshot; neither requires final run length.

## Real-program headroom experiments

On the Linux test host, `scripts/build-real.sh` builds pinned SQLite, RocksDB,
LevelDB and gflags sources under `build/real` without installing system packages.
`python3 fragbench/headroom.py` runs the three-run, 24-site greedy table search,
then five interleaved baseline/oracle/search repetitions. It collects static-model,
hybrid and heuristic results only when a table saves more than 5% idle RSS.
Use `--benchmarks sqlite leveldb redis-sessions rocksdb-cache rocksdb-churn` to
select workloads; the default also retains Redis Mesh/drop. RSS is measured after
500 ms idle, with purge delay zero for every variant. RocksDB and LevelDB program
memory statistics are partial estimates, explicitly labelled in the output.
See [RESULTS.md](RESULTS.md) for audited findings and limitations.

Request context (pass 9) requires a small application change at request dispatch:

```c
#include "jevalloc.h"
if (jev_context_setf) jev_context_setf("kind=store ttl=%s", ttl_bucket);
/* Handle the request. */
if (jev_context_clear) jev_context_clear();
```

The optional weak symbols allow the same executable to run without jevalloc. On
macOS, link an application using these unbound optional imports with
`-Wl,-undefined,dynamic_lookup`; the guarded calls then work both with and without
the injected library. Linux needs no extra linker option. The library copies at most 255 bytes plus the terminator into thread-local storage.
`jev_context_set(NULL)` also clears it. Normalize before calling: bucket numeric
values and remove unique IDs. Text is hashed exactly as supplied; high-cardinality
contexts defeat caching and increase metadata. Calls do not retain the input
pointer. Nested dispatch must restore the outer context when it returns.

The decision key combines the stack site with that context signature. Admission
and hybrid evidence apply to each pair independently. `JEVALLOC_CONTEXT=0` gives
the per-site control. Context traces include `site_key`, `context_signature` and
`context`; `tools/context_tables.py` builds both byte-majority oracles from one
trace. The `stack-v1` question and choices stay unchanged; context adds a line
beginning “What the program is doing right now:”.

For the small uncached experiment, set `JEVALLOC_MODE=live`,
`JEVALLOC_PER_ALLOC=1` and run jevd with `--policy per-alloc`. The sidecar also
advertises this policy in its response. Each admitted allocation sends its own
context and requested size; no class is reused by signature. The full-request
response cache permits exact request reuse, and recorded schedules permit warm
runs without inference (size/context/stack mismatches are rejected). The decision
budget defaults to 3,000 in jevd. `JEVALLOC_OBJECT_TRACE` enables exact allocation
and free event logging for accuracy checks; it also enables full trace metadata
and therefore is intended only for small diagnostics. Set `JEVALLOC_TRACE_OUT`
explicitly alongside it. `fragbench/realtime.py` runs the pass-9 measurements and
keeps headroom training separate from the five-run comparisons.

Redis's dispatch patch is in `patches/redis-request-context.patch`; build it with
`scripts/build-redis-context.sh`. It copies the original tree under `build/real`
and writes `build/bench/redis-context-server`. It does not tag network/parser
allocations before command dispatch. `FRAG_LONG_SETTLE_MS=10000` adds an `idle10`
phase after the normal idle measurement in fragmentation workloads.

After the context measurements and validation complete, `tools/fetch_mesh.py`
pins the recipe's Mesh master revision and downloads archives under `build/`.
`scripts/build-mesh.sh` builds `libmesh.so` and `libnomesh.so` with the recipe's
default settings and `DISABLE_MESHING=ON` respectively. Pinned dependency archives
replace CMake's git downloads; the build adaptation is recorded with hashes.
`scripts/build-long-settle.sh` preserves the old real-program binaries before
rebuilding their optional idle marker. `scripts/pass9-compaction.sh` then runs
all eleven workloads, five interleaved repetitions, normal and 10-second idle,
and independent inference-overlap audits. `tools/pass9_status.py` reports progress.
