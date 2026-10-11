#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
# Let the first full suite and its diagnostic instrument finish unchanged.
while [ ! -f results/pass5/status ]; do sleep 5; done
if ! grep -q 'ALL TESTS PASSED' results/pass5/full-test.log; then
  echo 'First full suite failed; inspect before continuing' >results/pass5/continue.status
  exit 1
fi
mv results/pass5/full-test.log results/pass5/prior/full-test-before-snapshot-guard.log
cp results/pass5/tests.json results/pass5/prior/tests-before-snapshot-guard.json
if [ -d results/frag-instrument ]; then mv results/frag-instrument results/pass5/prior/instrument-before-snapshot-guard; fi
cp results/pass5/status results/pass5/prior/status-before-snapshot-guard
make allocator >results/pass5/build-guard.log 2>&1
exec bash scripts/pass5-final.sh
