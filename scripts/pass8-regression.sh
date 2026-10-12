#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
echo $$ >results/pass8/regression.pid
trap 'echo $? >results/pass8/regression.status' EXIT
while ! test -f results/pass8/real.status; do sleep 5; done
test "$(cat results/pass8/real.status)" = 0
echo regression >results/pass8/stage.txt
python3 bench/run.py --resume --name pass8-regression --prompt stack-v1 --procs 16 --reps 5 --max-model-decisions 1500 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass8-regression.json >results/pass8/regression-audit.log
python3 tools/acceptance.py results/pass8-regression.json --output results/pass8/acceptance.json >results/pass8/acceptance.log || test $? = 1
test -s results/pass8/acceptance.json
cp results/pass8-regression.json results/pass8-regression.md results/pass8-regression.inference-audit.json results/pass8/
python3 tools/pass8_report.py
echo complete >results/pass8/stage.txt
