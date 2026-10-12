#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
test "$(cat results/pass9/validation.status)" = 0
trap 'echo $? >results/pass9/long-settle-build.status' EXIT
real="$PWD/build/real"
mkdir -p build/pre-long-settle results/pass9/builds
for binary in sqlite-driver leveldb-driver db_bench; do
  if ! test -f "build/pre-long-settle/$binary"; then cp "build/bench/$binary" "build/pre-long-settle/$binary"; fi
done
sha256sum build/pre-long-settle/* >results/pass9/builds/pre-long-settle.sha256
flags='-O2 -g -fno-omit-frame-pointer -fno-optimize-sibling-calls'
cc $flags -DSQLITE_THREADSAFE=1 -I"$real/sqlite-amalgamation-3500400" fragbench/sqlite-driver.c "$real/sqlite-amalgamation-3500400/sqlite3.c" -lpthread -ldl -lm -o build/bench/sqlite-driver >results/pass9/builds/sqlite-long-settle.log 2>&1
g++ $flags -I"$real/leveldb-1.23/include" fragbench/leveldb-driver.cc "$real/leveldb-build/libleveldb.a" -pthread -o build/bench/leveldb-driver >results/pass9/builds/leveldb-long-settle.log 2>&1
cmake --build "$real/rocksdb-build" --target db_bench -j4 >results/pass9/builds/rocksdb-long-settle.log 2>&1
cp "$real/rocksdb-build/db_bench" build/bench/db_bench
sha256sum build/bench/{sqlite-driver,leveldb-driver,db_bench} >results/pass9/builds/long-settle.sha256
