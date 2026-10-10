# jevalloc

Does predicting allocation-site lifetime improve malloc? This experiment routes short,
medium and long allocations to separate per-thread mimalloc heaps. A local Clef-flash
model makes decisions **while the program runs**; recorded decisions are replayed to
measure the allocator without today's inference latency. A histogram heuristic and
same-workload trace oracle are controls. This is a research prototype.

**Headline results: [RESULTS.md](RESULTS.md).** Short version: on mimalloc-bench this does
not beat plain mimalloc, and neither does a perfect-hindsight oracle with the same policy.
The matrix is still running; the full generated report (`CODEX-REPORT.md`) will follow.

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
python3 tools/jevd.py --socket "$PWD/build/jevd.sock" --policy model \
  --cache results/example-cache --log results/example-decisions.jsonl \
  --max-model-decisions 400 --model-backend vulkan &
sidecar_pid=$!
LD_PRELOAD="$PWD/build/libjevalloc.so" \
  JEVALLOC_MODE=live JEVALLOC_SOCKET="$PWD/build/jevd.sock" \
  JEVALLOC_STATS_OUT="$PWD/results/example-stats.json" \
  build/bench/cfrac 17545186520507317056371138836327483792789528
kill "$sidecar_pid"
```

Wait for the socket to exist before launching the application. The benchmark runner
does this automatically. On macOS use `DYLD_INSERT_LIBRARIES` and `.dylib`.

Policies: `model` sees symbolized stack, at most two source snippets and quantized
live statistics; `static-model` sees code only and never rechecks; `heuristic` starts
medium then classifies sampled lifetime histograms. `oracle` reads `--table`;
`random` is seeded. Model classes use the probability argmax. All requests, raw
responses, probabilities, token usage, model latency and cache provenance are logged.
The prompt stays fixed across the matrix.

`--max-model-decisions` defaults to 400, including initial decisions, cache hits and
rechecks. When exhausted, new sites get the default class; existing sites retain
their class and stop rechecking. Coverage fills reserve the model slots already in
the replay schedule, so they cannot repeatedly acquire another 400 decisions.
Fallbacks are logged without polluting the model cache. `--default-class` defaults
to medium and should match `JEVALLOC_DEFAULT` when running manually.

The CPU-to-Vulkan transition preserved cache identity and all old answers. Every
model decision records its originating backend; the transition manifest and original
CPU logs are archived in results. Resumed cfrac cold timings therefore include CPU
cache reuse and are not empty-cache measurements.

## Runtime controls

| Variable | Default | Meaning |
|---|---|---|
| `JEVALLOC_MODE` | `run` | `run`, `trace`, or `live` |
| `JEVALLOC_TABLE` | absent | Text lines `hex-site-key class`, classes 0/1/2 |
| `JEVALLOC_DEFAULT` | `1` | Unknown site's class: short/medium/long = 0/1/2 |
| `JEVALLOC_DEPTH` | `4` | Frame count, clamped to 1–16 |
| `JEVALLOC_POLICY` | segregation | `none`: bypass key, one heap; `keyonly`: key/lookup, one heap |
| `JEVALLOC_TRACE_OUT` | `jevalloc-trace.jsonl` | Trace at orderly exit |
| `JEVALLOC_SOCKET` | absent | Live Unix socket |
| `JEVALLOC_SAMPLE` | `64` | Sample one in this many allocations per site |
| `JEVALLOC_TIMEOUT_MS` | `30000` | One deadline covering socket connect/send/receive |
| `JEVALLOC_STATS_OUT` | `jevalloc-stats.json` | Live accounting and per-site requested-byte totals |

Same-site requests share one in-flight decision. Rechecks occur after 1,024, 8,192,
65,536 and 524,288 further site allocations (at most four); a new class affects only
future allocations. Free supports cross-thread ownership. A failed sidecar opens a
process-lifetime circuit breaker and uses the default class without hanging. Sampled
pointer records support cross-thread frees; counters are approximate concurrent
snapshots. Blocked time includes threads waiting for another thread's decision.

## Keys, lifetimes and controls

A bounded frame-pointer walk checks stack bounds, alignment and increasing links,
examining at most 64 links. Linux uses initial-exec TLS and a 256-entry per-thread
raw-stack cache; cache hits avoid image searches and table probing. Misses normalize
return addresses by image base and include the image path in the stable key.
Missing frame pointers truncate context. Keys depend on exact binaries, paths,
libraries and depth; rebuilding or relocating can invalidate tables. Dynamic
unloading/reuse, alternate stacks and post-fork synchronization are not validated.
macOS registers images through dyld and retains its loader-safe pthread context.

Lifetime is measured in total requested allocation bytes, not wall-clock seconds:
short means freed before another 1 MiB; long means until exit or over half the total
allocation volume; medium is the remainder. Long takes precedence when definitions
overlap. Trace mode tracks successful allocations exactly under a mutex, including
cross-thread frees, and writes lifetime histograms, exact class-byte totals and
never-freed bytes. Internal/bootstrap work and work after the exit snapshot are
excluded; abrupt exits do not yield complete traces.

The oracle chooses each site's majority class by bytes from a prior execution of
the same workload. It is a hindsight label-accuracy control, not a held-out model or
a mathematical upper bound on allocator performance. Random is seeded; size-only
uses fixed mean-request thresholds of 256 bytes and 16 KiB. Plain segregation is
the only allocation policy measured; no purge/retention tuning is mixed in.

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

## Reproduce the matrix

```sh
# On the Beelink, after build, extras, tests and model-server startup:
python3 tools/calibrate.py
python3 tools/live_cost.py
python3 tools/provenance.py
nohup python3 bench/run.py --name beelink --procs 16 --reps 5 \
  --max-model-decisions 400 --resume > results/bench.log 2>&1 &
```

From this checkout, `scripts/beelink.sh sync|build|test|bench|fetch-results` wraps the
SSH/rsync workflow. Sync excludes build, results, virtualenv and git metadata.
`test` and `bench` detach; inspect `results/test.status` or `results/bench.status`
on the remote host for completion. Poll `scripts/progress.py` remotely every few
minutes. `fetch-results` copies into local `results/beelink/`, then run:

```sh
python3 tools/report.py --results results/beelink
```

The report generator refuses incomplete matrices or an unresolved inference-interference audit. This pass preserves and replaces headline blocks that overlapped a separate prompt study; the server request log and conservative timing audit are retained with the results. The runner fingerprints inputs,
libraries, tables and measurement code before resuming. Run one benchmark process
at a time; keep model inference and calibration out of headline repetitions.

The full matrix has 22 Linux configurations, ten variants and five interleaved
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
