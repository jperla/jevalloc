#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
trap 'echo $? >results/pass8/final.status' EXIT
while ! test -f results/pass8/real.status; do sleep 5; done
test "$(cat results/pass8/real.status)" = 0
test ! -e results/pass8/redis-mesh-average-idle
mv results/pass8/real/redis-mesh results/pass8/redis-mesh-average-idle
cat >results/pass8/redis-mesh-average-idle/ARCHIVE-NOTE.txt <<'NOTE'
Superseded pilot: the headroom search incorrectly averaged two idle phases.
Final reports use the final idle phase. Re-scoring changes the greedy acceptance
path, so the complete Mesh headroom experiment is rerun with the corrected metric.
Raw file references in this historical matrix use the original
results/pass8/real/redis-mesh prefix; its archived files are now under
results/pass8/redis-mesh-average-idle. Do not join them to the new run's files.
The old source is preserved as results/pass8/headroom-average-idle.py.
NOTE
echo 'corrected Mesh final-idle headroom' >results/pass8/stage.txt
python3 tests/test_headroom.py >results/pass8/headroom-test.log 2>&1
python3 fragbench/headroom.py --benchmarks redis-mesh >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass8/real/redis-mesh/matrix.json >results/pass8/real/redis-mesh/audit.log
echo 0 >results/pass8/mesh-final.status
python3 tools/pass8_report.py
bash scripts/pass8-regression.sh
