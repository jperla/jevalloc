#!/usr/bin/env bash
# Short candidate check before committing time to every acceptance workload.
set -euo pipefail
cd "$(dirname "$0")/.."
label=${1:-inline}
if (( $# )); then shift; fi
workloads=("$@")
if (( ${#workloads[@]} == 0 )); then workloads=(cfrac larson xmalloc-test); fi
export PATH="$HOME/jevalloc/venv/bin:$PATH"
trap 'rc=$?; echo "$rc" >results/pass4-diagnostic.status' EXIT
trap 'exit 143' TERM
rm -f results/pass4-diagnostic.status
printf '%s\n' 'candidate build and targeted correctness' >results/pass4-stage.txt
make allocator >"results/build-$label.log" 2>&1
python3 tests/test.py --benchmarks cfrac >"results/pass4-$label-targeted.log" 2>&1
printf '%s\n' 'candidate diagnostic (one repetition, not acceptance)' >results/pass4-stage.txt
python3 bench/run.py --name "diagnostic-$label" --benchmarks "${workloads[@]}" --variants mi jev-none jev-keyonly jev-table:oracle jev-live:heuristic --reps 1 --procs 16 >results/bench.log 2>&1
printf '%s\n' 'candidate diagnostic complete; acceptance still required' >results/pass4-stage.txt
