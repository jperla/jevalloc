#!/usr/bin/env python3
"""Configure a generated source overlay; never edit the upstream checkout."""
import shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'third_party/mimalloc-bench/bench'
stage=ROOT/'build/bench-source'
stage.mkdir(parents=True,exist_ok=True)
for p in source.iterdir():
    if p.name=='CMakeLists.txt': continue
    dest=stage/p.name
    if not dest.exists(): dest.symlink_to(p, target_is_directory=p.is_dir())
text=(source/'CMakeLists.txt').read_text().replace('if(NOT APPLE)', 'if(NOT APPLE AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/shbench/sh6bench-new.c")')
(stage/'CMakeLists.txt').write_text(text)
cache=ROOT/'build/bench/CMakeCache.txt'
if cache.exists() and f'CMAKE_HOME_DIRECTORY:INTERNAL={stage}' not in cache.read_text():
    cache.unlink();shutil.rmtree(cache.parent/'CMakeFiles',ignore_errors=True)
subprocess.run(['cmake','-S',str(stage),'-B',str(ROOT/'build/bench'),'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_FLAGS=-g -fno-omit-frame-pointer','-DCMAKE_CXX_FLAGS=-g -fno-omit-frame-pointer'],check=True)
subprocess.run(['cmake','--build',str(ROOT/'build/bench'),'-j','8','--target',*'cfrac espresso barnes larson larson-sized xmalloc-test cache-scratch cache-thrash mstress rptest glibc-simple glibc-thread alloc-test malloc-large mleak'.split()],check=True)
