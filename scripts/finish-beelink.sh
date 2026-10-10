#!/usr/bin/env bash
# Run on the Beelink after launching the full test suite; detach this script.
set -euo pipefail
cd "$HOME/jevalloc/src-tree"
if [[ -f results/test.pid ]]; then
  while kill -0 "$(cat results/test.pid)" 2>/dev/null && [[ ! -f results/test.status ]]; do sleep 60; done
fi
[[ "$(cat results/test.status)" == 0 ]]
python3 tools/calibrate.py > results/fast-cost.log 2>&1
python3 tools/live_cost.py > results/live-cost.log 2>&1
python3 tools/provenance.py
rm -f results/bench.status
set +e
python3 bench/run.py --name beelink --procs 16 --reps 5 --resume --max-model-decisions 400 > results/bench.log 2>&1 &
runner=$!
echo "$runner" > results/bench.runner.pid
wait "$runner"
status=$?
echo "$status" > results/bench.status
exit "$status"
