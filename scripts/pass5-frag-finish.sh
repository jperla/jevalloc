#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
echo $$ >results/pass5/pid
rm -f results/pass5/status
stage() { printf '%s\n' "$1" >results/pass5/stage.txt; printf '\nPass 5 running: %s\n' "$1" >>CODEX-REPORT.md; }
trap 'rc=$?; echo "$rc" >results/pass5/status; printf "\nPass 5 pipeline exit %s at %s\n" "$rc" "$(cat results/pass5/stage.txt)" >>CODEX-REPORT.md' EXIT
trap 'exit 143' TERM
python3 - <<'PY'
import hashlib,json
from pathlib import Path
t=json.load(open('results/pass5/tests.json'))
assert t['passed'] and t['full_suite'] and len(t['workloads'])==22
assert t['library_sha256']==hashlib.sha256(Path('build/libjevalloc.so').read_bytes()).hexdigest()
PY
stage 'workload source and mixed-TTL validation'
python3 tests/test_fragbench.py >results/pass5/frag-correctness.log 2>&1
stage 'instrument on distinct-wrapper build'
python3 bench/run.py --fragbench --instrument --name frag-instrument >results/bench.log 2>&1 || {
 python3 -c "import json; g=json.load(open('results/frag-instrument/gate.json')); assert g['repetitions']==5 and len(g['comparisons'])==4"
 printf '\nInstrument negative after investigation; continue with explicit recorded override.\n' >>CODEX-REPORT.md
}
python3 tools/audit_pass4.py results/frag-instrument/matrix.json >results/pass5/instrument-audit.log
stage 'fragbench matrix, distinct wrappers and seeded TTL data'
python3 bench/run.py --fragbench --name fragbench-two --allow-negative-instrument >results/bench.log 2>&1
python3 tools/audit_pass4.py results/fragbench-two/matrix.json >results/pass5/frag-audit.log
python3 tools/pass5_report.py
stage 'oracle threshold sensitivity'
python3 bench/run.py --fragbench --sensitivity --name frag-sensitivity >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-sensitivity/matrix.json >results/pass5/sensitivity-audit.log
python3 tools/pass5_report.py
stage 'mimalloc-bench regression'
python3 bench/run.py --name pass5-regression --procs 16 --reps 5 --max-model-decisions 400 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass5-regression.json >results/pass5/regression-audit.log
stage report
python3 tools/pass5_report.py
stage complete
