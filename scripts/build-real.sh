#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/jevalloc/venv/bin:$PATH"
real="$PWD/build/real"
# Inputs are source tarballs; all dependencies and outputs stay under build/.
mkdir -p "$real" results/pass8/builds
fetch() {
  if ! test -f "$real/$1"; then
    curl -fsSL --retry 3 "$2" -o "$real/$1.download"
    mv "$real/$1.download" "$real/$1"
  fi
  printf '%s  %s\n' "$3" "$real/$1" | sha256sum -c -
}
fetch sqlite.zip https://www.sqlite.org/2025/sqlite-amalgamation-3500400.zip 1d3049dd0f830a025a53105fc79fd2ab9431aea99e137809d064d8ee8356b032
fetch rocksdb.tar.gz https://codeload.github.com/facebook/rocksdb/tar.gz/refs/tags/v10.10.1 df2ff348f3fac8578fd4b727eee7267aaf90cd403c99b55e898d1db63fa8cff5
fetch leveldb.tar.gz https://codeload.github.com/google/leveldb/tar.gz/refs/tags/1.23 9a37f8a6174f09bd622bc723b55881dc541cd50747cbd08831c2a82d620f6d76
fetch gflags.tar.gz https://codeload.github.com/gflags/gflags/tar.gz/refs/tags/v2.2.2 34af2f15cf7367513b352bdcd2493ab14ce43692d2dcd9dfc499492966c64dcf
python3 -m zipfile -e "$real/sqlite.zip" "$real"
for p in rocksdb leveldb gflags; do tar xzf "$real/$p.tar.gz" -C "$real"; done
sha256sum "$real"/*.tar.gz "$real"/sqlite.zip >results/pass8/builds/source-sha256.txt
flags='-O2 -g -fno-omit-frame-pointer -fno-optimize-sibling-calls'
cc $flags -DSQLITE_THREADSAFE=1 -I"$real/sqlite-amalgamation-3500400" fragbench/sqlite-driver.c "$real/sqlite-amalgamation-3500400/sqlite3.c" -lpthread -ldl -lm -o build/bench/sqlite-driver >results/pass8/builds/sqlite.log 2>&1
cmake -S "$real/leveldb-1.23" -B "$real/leveldb-build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="$flags" -DLEVELDB_BUILD_TESTS=OFF -DLEVELDB_BUILD_BENCHMARKS=OFF -DLEVELDB_INSTALL=OFF >results/pass8/builds/leveldb.log 2>&1
cmake --build "$real/leveldb-build" -j8 >>results/pass8/builds/leveldb.log 2>&1
g++ $flags -I"$real/leveldb-1.23/include" fragbench/leveldb-driver.cc "$real/leveldb-build/libleveldb.a" -pthread -o build/bench/leveldb-driver >>results/pass8/builds/leveldb.log 2>&1
cmake -S "$real/gflags-2.2.2" -B "$real/gflags-build" -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DREGISTER_BUILD_DIR=OFF -DREGISTER_INSTALL_PREFIX=OFF -DCMAKE_INSTALL_PREFIX="$real/prefix" -DCMAKE_CXX_FLAGS="$flags" >results/pass8/builds/gflags.log 2>&1
cmake --build "$real/gflags-build" -j8 >>results/pass8/builds/gflags.log 2>&1
cmake --install "$real/gflags-build" >>results/pass8/builds/gflags.log 2>&1
python3 tools/patch_rocksdb.py
cmake -S "$real/rocksdb-10.10.1" -B "$real/rocksdb-build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="$flags" -DCMAKE_PREFIX_PATH="$real/prefix" -DWITH_GFLAGS=ON -DWITH_LIBURING=OFF -DWITH_TESTS=OFF -DWITH_TOOLS=OFF -DWITH_BENCHMARK_TOOLS=ON -DFAIL_ON_WARNINGS=OFF -DROCKSDB_BUILD_SHARED=OFF >results/pass8/builds/rocksdb.log 2>&1
cmake --build "$real/rocksdb-build" --target db_bench -j4 >>results/pass8/builds/rocksdb.log 2>&1
cp "$real/rocksdb-build/db_bench" build/bench/db_bench
sha256sum build/bench/{sqlite-driver,leveldb-driver,db_bench} >results/pass8/builds/binary-sha256.txt
