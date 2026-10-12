#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/real results/pass9/builds
original="$PWD/build/extras/redis-6.2.7"
target="$PWD/build/real/redis-context-6.2.7"
if ! test -d "$target"; then
  cp -a "$original" "$target"
  patch -d "$target" -p1 <patches/redis-request-context.patch
fi
make -C "$target" -j8 MALLOC=libc REDIS_CFLAGS="-g -fno-omit-frame-pointer -I$PWD/src" >results/pass9/builds/redis-context.log 2>&1
cp "$target/src/redis-server" build/bench/redis-context-server
sha256sum "$original/src/server.c" "$target/src/server.c" patches/redis-request-context.patch build/bench/redis-context-server >results/pass9/builds/redis-context-sha256.txt
