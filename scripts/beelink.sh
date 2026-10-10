#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
host=${JEVALLOC_REMOTE:?set JEVALLOC_REMOTE=user@host of the Linux test machine}
remote='~/jevalloc/src-tree'
case "${1:-}" in
 sync)
  ssh -o BatchMode=yes "$host" 'mkdir -p ~/jevalloc/src-tree'
  rsync -az --exclude build/ --exclude .venv-clef/ --exclude .git/ --exclude results/ --exclude out/ --exclude "build-*.log" --exclude __pycache__/ ./ "$host:$remote/" ;;
 build) ssh -o BatchMode=yes "$host" 'export PATH="$HOME/jevalloc/venv/bin:$PATH"; cd ~/jevalloc/src-tree && make all && python3 tools/extras.py' ;;
 test) ssh -o BatchMode=yes "$host" 'cd ~/jevalloc/src-tree; mkdir -p results; rm -f results/test.status; nohup sh -c '\''python3 tests/test.py > results/test.log 2>&1; echo $? > results/test.status'\'' </dev/null >/dev/null 2>&1 & echo $!';;
 bench) ssh -o BatchMode=yes "$host" 'cd ~/jevalloc/src-tree; mkdir -p results; rm -f results/bench.status; nohup sh -c '\''python3 bench/run.py --name beelink --procs 16 --reps 5 --resume --max-model-decisions 400 > results/bench.log 2>&1; echo $? > results/bench.status'\'' </dev/null >/dev/null 2>&1 & echo $! > results/bench.pid; cat results/bench.pid' ;;
 fetch-results) mkdir -p results/beelink; rsync -az "$host:$remote/results/" results/beelink/ ;;
 *) echo 'Usage: scripts/beelink.sh sync|build|test|bench|fetch-results' >&2; exit 2 ;;
esac
