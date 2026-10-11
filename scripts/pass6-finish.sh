#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
echo $$ >results/pass6/pid
stage() { printf '%s\n' "$1" >results/pass6/stage.txt; printf '\nPass 6 running: %s\n' "$1" >>CODEX-REPORT.md; }
trap 'rc=$?; echo "$rc" >results/pass6/status; printf "\nPass 6 pipeline exit %s at %s\n" "$rc" "$(cat results/pass6/stage.txt)" >>CODEX-REPORT.md' EXIT
trap 'exit 143' TERM
python3 - <<'PY'
import hashlib,json
from pathlib import Path
t=json.load(open('results/pass6/tests.json'));g=json.load(open('results/frag-instrument/gate.json'))
assert t['passed'] and t['full_suite'] and len(t['workloads'])==22
assert t['library_sha256']==g['library_sha256']==hashlib.sha256(Path('build/libjevalloc.so').read_bytes()).hexdigest()
assert g['passed'] and g['class_schema']=='transient-permanent-v1'
PY
stage 'oracle permanent-threshold and fixed-S sensitivity'
python3 bench/run.py --fragbench --sensitivity --name frag-sensitivity >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-sensitivity/matrix.json >results/pass6/sensitivity-audit.log
stage 'full transient/permanent fragbench'
python3 bench/run.py --fragbench --name fragbench-permanent >results/bench.log 2>&1
python3 tools/audit_pass4.py results/fragbench-permanent/matrix.json >results/pass6/frag-audit.log
python3 tools/pass6_report.py
stage 'mimalloc-bench regression'
python3 bench/run.py --name pass6-regression --procs 16 --reps 5 --max-model-decisions 400 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass6-regression.json >results/pass6/regression-audit.log
stage report
python3 tools/pass6_report.py
stage complete
