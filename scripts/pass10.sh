#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass10
trap 'echo $? >results/pass10/status' EXIT
echo $$ >results/pass10/pid
python3 - <<'PY'
import json
from pathlib import Path
p=Path('results/pass10/tests/tests.json')
d=json.loads(p.read_text());assert d['passed'] and d['full_suite'] and len(d['workloads'])==22
assert 'FRAGBENCH CORRECTNESS PASSED' in Path('results/pass10/tests/frag.log').read_text()
PY
for stage in server peralloc real; do
 echo "$stage" >results/pass10/stage.txt
 python3 fragbench/review2.py "$stage" >"results/pass10/$stage.log" 2>&1
 python3 tools/pass10_report.py
 printf '\nPass 10: %s block completed; matrices and inference audits retained under results/pass10.\n' "$stage" >>CODEX-REPORT.md
done
echo regression >results/pass10/stage.txt
python3 bench/run.py --resume --name pass10/regression --prompt stack-v1 --procs 16 --reps 5 --max-model-decisions 3000 --variants mi jev-keyonly jev-table:oracle jev-live:static-model jev-live:hybrid jev-live:heuristic jev-live:rules-neutral >results/pass10/regression.log 2>&1
python3 tools/audit_pass4.py results/pass10/regression.json >results/pass10/regression-audit.log
python3 tools/pass10_report.py
python3 tools/pass10_validate.py >results/pass10/validation.log
printf '\nPass 10: regression and final evidence validation completed.\n' >>CODEX-REPORT.md
echo complete >results/pass10/stage.txt
