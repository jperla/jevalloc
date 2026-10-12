#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
while ! test -f results/pass9/long-settle-build.status; do sleep 5; done
test "$(cat results/pass9/long-settle-build.status)" = 0
test "$(cat results/pass9/mesh-build.status)" = 0
test "$(cat results/pass9/validation.status)" = 0
trap 'echo $? >results/pass9/compaction.status' EXIT
echo compaction-measurements >results/pass9/stage.txt
python3 fragbench/compaction.py >results/pass9/compaction.log 2>&1
for matrix in results/pass9/compaction/*/matrix.json; do
 python3 tools/audit_pass4.py "$matrix" >"$(dirname "$matrix")/audit.log"
done
python3 tools/pass9_mesh_report.py >results/pass9/compaction-report.log 2>&1
python3 tools/pass9_report.py --publish >results/pass9/report.log 2>&1
echo complete >results/pass9/stage.txt
