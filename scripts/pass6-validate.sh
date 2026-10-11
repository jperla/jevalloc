#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass6
echo $$ >results/pass6/validate.pid
stage() { printf '%s\n' "$1" >results/pass6/stage.txt; }
trap 'rc=$?; echo "$rc" >results/pass6/validate.status' EXIT
stage 'full Linux correctness'
make test >results/pass6/full-test.log 2>&1
cp results/tests.json results/pass6/tests.json
stage 'workload validation'
python3 tests/test_fragbench.py >results/pass6/frag-correctness.log 2>&1
stage instrument
python3 bench/run.py --fragbench --instrument --name frag-instrument >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-instrument/matrix.json >results/pass6/instrument-audit.log
stage 'instrument complete'
