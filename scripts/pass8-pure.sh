#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass8
trap 'echo $? >results/pass8/pure.status' EXIT
cmake -S . -B build >results/pass8/configure.log 2>&1
cmake --build build -j8 >results/pass8/build.log 2>&1
python3 tests/test.py >results/pass8/full-test.log 2>&1
python3 tests/test_stack.py >results/pass8/stack-test.log 2>&1
python3 tests/test_fragbench.py >results/pass8/frag-test.log 2>&1
if test -d results/frag-instrument; then mv results/frag-instrument results/pass8/prior-instrument; fi
python3 fragbench/run.py --instrument --name frag-instrument >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-instrument/matrix.json >results/pass8/instrument-audit.log
python3 fragbench/run.py --name pass8/pure --benchmarks site-pure-1 site-pure-16 --variants mi jev-table:oracle jev-live:static-model jev-live:hybrid jev-live:heuristic >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass8/pure/matrix.json >results/pass8/pure/audit.log
