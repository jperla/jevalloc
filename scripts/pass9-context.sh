#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass9
trap 'echo $? >results/pass9/context.status' EXIT
echo correctness >results/pass9/stage.txt
cmake -S . -B build >results/pass9/configure.log 2>&1
cmake --build build -j8 >results/pass9/build.log 2>&1
JEVALLOC_TEST_REPORT_DIR="$PWD/results/pass9" python3 tests/test.py >results/pass9/full-test.log 2>&1
cp results/tests.json results/pass9/tests.json
JEVALLOC_TEST_REPORT_DIR="$PWD/results/pass9" python3 tests/test_fragbench.py >results/pass9/frag-test.log 2>&1
echo redis-build >results/pass9/stage.txt
bash scripts/build-redis-context.sh >results/pass9/redis-build-launch.log 2>&1
echo context-measurements >results/pass9/stage.txt
python3 fragbench/realtime.py >results/pass9/context.log 2>&1
for matrix in results/pass9/{site-mixed-1,site-mixed-16,redis-mesh,redis-drop,redis-sessions,per-alloc-small}/matrix.json; do
 python3 tools/audit_pass4.py "$matrix" >"$(dirname "$matrix")/audit.log"
done
python3 tools/pass9_report.py >results/pass9/report.log 2>&1
echo context-complete >results/pass9/stage.txt
