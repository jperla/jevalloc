#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass11
trap 'echo $? >results/pass11/status' EXIT
echo $$ >results/pass11/pid
python3 - <<'PY'
import json
from pathlib import Path
p=Path('results/pass11/tests/tests.json')
d=json.loads(p.read_text());assert d['passed'] and d['full_suite'] and len(d['workloads'])==22
assert 'LIVE METADATA LIMITS PASSED' in Path('results/pass11/tests/full.log').read_text()
PY
for stage in redis diagnostic factorial; do
 echo "$stage" >results/pass11/stage.txt
 if test "$stage" = diagnostic; then
  python3 fragbench/diagnostic11.py >results/pass11/diagnostic.log 2>&1
 else
  python3 fragbench/review3.py "$stage" >"results/pass11/$stage.log" 2>&1
 fi
 echo "$stage complete" >>results/pass11/progress.log
done
python3 tools/pass11_report.py
python3 tools/pass11_validate.py >results/pass11/validation.log
echo complete >results/pass11/stage.txt
