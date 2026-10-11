#!/usr/bin/env bash
# Correctness is mandatory; performance target misses are reported, not gates.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
mkdir -p results/pass5
stage() { printf '%s\n' "$1" >results/pass5/stage.txt; printf '\nPass 5 running: %s\n' "$1" >>CODEX-REPORT.md; }
trap 'rc=$?; echo "$rc" >results/pass5/status; printf "\nPass 5 pipeline exit %s at %s\n" "$rc" "$(cat results/pass5/stage.txt)" >>CODEX-REPORT.md' EXIT
trap 'exit 143' TERM
rm -f results/pass5/status
stage 'full Linux correctness'
make test >results/pass5/full-test.log 2>&1
cp results/tests.json results/pass5/tests.json
stage 'two-class instrument, five interleaved repetitions'
python3 bench/run.py --fragbench --instrument --name frag-instrument >results/bench.log 2>&1 || {
  # Numerical negative is investigated in CODEX-REPORT: sessions and cache merge
  # under fixed S. Missing/corrupt outputs still stop the pipeline.
  python3 -c "import json; g=json.load(open('results/frag-instrument/gate.json')); assert g['repetitions']==5 and len(g['comparisons'])==4"
  printf '\nTwo-class instrument negative; retain workload and report the measured failure.\n' >>CODEX-REPORT.md
}
stage 'fragbench matrix, five interleaved repetitions'
python3 bench/run.py --fragbench --name fragbench-two --allow-negative-instrument >results/bench.log 2>&1
python3 tools/audit_pass4.py results/fragbench-two/matrix.json >results/pass5/frag-audit.log
stage 'oracle threshold sensitivity, five interleaved repetitions'
python3 bench/run.py --fragbench --sensitivity --name frag-sensitivity >results/bench.log 2>&1
python3 tools/audit_pass4.py results/frag-sensitivity/matrix.json >results/pass5/sensitivity-audit.log
stage 'mimalloc-bench regression, five interleaved repetitions'
python3 bench/run.py --name pass5-regression --procs 16 --reps 5 --max-model-decisions 400 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/pass5-regression.json >results/pass5/regression-audit.log
python3 tools/acceptance.py results/pass5-regression.json --output results/pass5/acceptance-targets.json >results/pass5/acceptance-targets.log || test "$?" = 1
stage 'report'
python3 tools/pass5_report.py
stage complete
