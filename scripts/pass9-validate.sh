#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
while ! test -f results/pass9/context.status; do sleep 5; done
test "$(cat results/pass9/context.status)" = 0
trap 'echo $? >results/pass9/validation.status' EXIT
echo context-performance >results/pass9/stage.txt
python3 tests/test_context.py >results/pass9/context-portable-linux-test.log 2>&1
python3 fragbench/peralloc_performance.py >results/pass9/per-alloc-performance.log 2>&1
python3 tools/audit_pass4.py results/pass9/per-alloc-small/performance/matrix.json >results/pass9/per-alloc-small/performance/audit.log
python3 tools/pass9_audit_extra.py >results/pass9/search-gate-audit.log
python3 tools/pass9_report.py --publish >results/pass9/report.log 2>&1
python3 tools/pass9_validate.py >results/pass9/validation.log 2>&1
echo context-verified >results/pass9/stage.txt
