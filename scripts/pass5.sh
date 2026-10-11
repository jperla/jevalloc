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
# Continue using the already validated library; validates the synthetic workload too.
exec bash scripts/pass5-frag-finish.sh
