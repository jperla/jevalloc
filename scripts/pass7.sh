#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass7
printf '%s\n' $$ >results/pass7/pid
stage() { printf '%s\n' "$1" >results/pass7/stage.txt; }
trap 'rc=$?; printf "%s\n" "$rc" >results/pass7/status' EXIT
trap 'exit 143' TERM
stage 'waiting for full Linux validation'
while ! test -f results/pass7/validate.status; do sleep 5; done
test "$(cat results/pass7/validate.status)" = 0
cp results/tests.json results/pass7/tests.json
stage 'workload validation'
python3 tests/test_fragbench.py >results/pass7/frag-correctness.log 2>&1
stage instrument
if test -d results/frag-instrument && ! test -d results/pass7/prior-instrument; then
  mv results/frag-instrument results/pass7/prior-instrument
fi
python3 fragbench/run.py --instrument --name frag-instrument >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-instrument/matrix.json >results/pass7/instrument-audit.log
for prompt in stack-v1 stack-v1-nodesc; do
  stage "site-pure $prompt"
  python3 fragbench/run.py --name "pass7/pure-$prompt" --prompt "$prompt" --benchmarks site-pure-1 site-pure-16 >results/bench.log 2>&1
  python3 tools/audit_pass4.py "results/pass7/pure-$prompt/matrix.json" >"results/pass7/pure-$prompt/audit.log"
done
for prompt in stack-v1 stack-v1-nodesc; do
  stage "remaining fragbench $prompt"
  python3 fragbench/run.py --name "pass7/rest-$prompt" --prompt "$prompt" --benchmarks site-mixed-1 site-mixed-16 redis-mesh redis-drop >results/bench.log 2>&1
  python3 tools/audit_pass4.py "results/pass7/rest-$prompt/matrix.json" >"results/pass7/rest-$prompt/audit.log"
done
stage 'mimalloc-bench regression stack-v1'
python3 bench/run.py --name pass7-regression --prompt stack-v1 --procs 16 --reps 5 --max-model-decisions 1500 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass7-regression.json >results/pass7/regression-audit.log
stage complete
