#!/usr/bin/env bash
# Detached, fail-closed sequence; run from ~/jevalloc/src-tree on the test machine.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
status=results/pass4-stage.txt
rm -f results/pass4.status
trap 'rc=$?; echo "$rc" >results/pass4.status; printf "\nPipeline exit: %s, stage: %s\n" "$rc" "$(cat results/pass4-stage.txt)" >>CODEX-REPORT.md' EXIT
trap 'exit 143' TERM
stage() { printf '%s\n' "$1" >"$status"; printf '\nRunning: %s\n' "$1" >>CODEX-REPORT.md; }
stage 'build and targeted correctness'
make allocator >results/build-final.log 2>&1
python3 tests/test.py --benchmarks cfrac >results/pass4-targeted.log 2>&1
stage 'acceptance (five interleaved repetitions)'
python3 bench/run.py --name acceptance-final --variants mi jev-none jev-keyonly jev-table:oracle jev-live:heuristic --reps 5 --procs 16 >results/bench.log 2>&1
python3 tools/audit_pass4.py results/acceptance-final.json
python3 tools/acceptance.py results/acceptance-final.json --output results/acceptance-final-gate.json
stage 'full make test'
make test >results/pass4-test.log 2>&1
stage 'fragmentation instrument'
python3 bench/run.py --fragbench --instrument --name frag-instrument >results/bench.log 2>&1
stage 'fragmentation matrix'
python3 bench/run.py --fragbench --name fragbench >results/bench.log 2>&1
stage 'mimalloc-bench matrix'
python3 bench/run.py --name pass4 --procs 16 --reps 5 --max-model-decisions 400 >results/bench.log 2>&1
stage 'analysis'
python3 tools/audit_pass4.py results/fragbench/matrix.json
python3 tools/audit_pass4.py results/pass4.json
python3 tools/frag_summary.py results/fragbench/matrix.json >results/fragbench/summary.md
python3 tools/matrix_summary.py results/pass4.json >results/pass4-summary.txt
python3 tools/pass4_report.py
stage 'complete'
