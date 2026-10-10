#!/usr/bin/env bash
# Detached completion after the main matrix, including the external-client audit.
set -euo pipefail
cd "$HOME/jevalloc/src-tree"
python3 tools/repair_interference.py
python3 tests/test_budget.py > results/budget-integration.log 2>&1
cp results/provenance-beelink.json results/provenance-beelink-start.json
python3 tools/provenance.py
python3 tools/report.py --results results
printf '0\n' > results/finalize.status
