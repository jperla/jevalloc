#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo $$ >results/pass6/queue.pid
while kill -0 "$(cat results/pass6/validate.pid)" 2>/dev/null; do sleep 5; done
test "$(cat results/pass6/validate.status)" = 0
exec bash scripts/pass6-finish.sh
