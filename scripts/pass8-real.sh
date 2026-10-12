#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
trap 'echo $? >results/pass8/real.status' EXIT
while ! test -f results/pass8/pure.status; do sleep 5; done
test "$(cat results/pass8/pure.status)" = 0
echo build >results/pass8/stage.txt
bash scripts/build-real.sh >results/pass8/builds-launch.log 2>&1
echo headroom >results/pass8/stage.txt
python3 fragbench/headroom.py >results/bench.log 2>&1
for matrix in results/pass8/real/*/matrix.json; do python3 tools/audit_pass4.py "$matrix" >"$(dirname "$matrix")/audit.log"; done
echo real-complete >results/pass8/stage.txt
