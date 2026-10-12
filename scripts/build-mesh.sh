#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
test "$(cat results/pass9/validation.status)" = 0
trap 'echo $? >results/pass9/mesh-build.status' EXIT
python3 tools/prepare_mesh_build.py >results/pass9/builds/mesh-dependencies.log 2>&1
for variant in mesh nomesh; do
  disabled=OFF
  if test "$variant" = nomesh; then disabled=ON; fi
  cmake -S build/mesh-source -B "build/$variant-build" -DDISABLE_MESHING="$disabled" >"results/pass9/builds/$variant-configure.log" 2>&1
  # Upstream places both configurations' outputs in the source tree. Relink on
  # a resumed build before copying, so the twin cannot reuse the other output.
  cmake --build "build/$variant-build" --clean-first >"results/pass9/builds/$variant-build.log" 2>&1
  cp build/mesh-source/build/lib/libmesh.so "build/lib$variant.so"
done
sha256sum build/libmesh.so build/libnomesh.so >results/pass9/builds/mesh-binaries.sha256
