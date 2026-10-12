#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
while ! test -f results/pass9/compaction.status; do sleep 5; done
test "$(cat results/pass9/compaction.status)" = 0
trap 'echo $? >results/pass9/mesh-tests.status' EXIT
sha256sum -c results/pass9/builds/mesh-binaries.sha256
# Build each unit configuration explicitly: upstream shares the output path.
cmake --build build/nomesh-build --target unit.test --clean-first >results/pass9/builds/nomesh-unit-build.log 2>&1
set +e
timeout 300 build/mesh-source/build/bin/unit.test >results/pass9/builds/nomesh-unit.log 2>&1
nomesh_status=$?
set -e
# Build only the enabled unit target. The two measured LD_PRELOAD libraries are
# separate copies and are not replaced by this build.
cmake --build build/mesh-build --target unit.test --clean-first >results/pass9/builds/mesh-unit-build.log 2>&1
set +e
timeout 300 build/mesh-source/build/bin/unit.test >results/pass9/builds/mesh-unit.log 2>&1
mesh_status=$?
set -e
sha256sum -c results/pass9/builds/mesh-binaries.sha256
python3 - "$mesh_status" "$nomesh_status" <<'PY'
import json,sys
from pathlib import Path
result=dict(mesh_exit_status=int(sys.argv[1]),nomesh_exit_status=int(sys.argv[2]),measured_libraries_unchanged=True)
Path('results/pass9/builds/mesh-unit-results.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
PY
test "$mesh_status" = 0
test "$nomesh_status" = 0
