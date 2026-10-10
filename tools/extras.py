#!/usr/bin/env python3
"""Fetch pinned optional workloads into build/, without packages or vendor edits."""
import hashlib, io, shutil, subprocess, tarfile, urllib.request, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
build=ROOT/'build'; extra=build/'extras';extra.mkdir(parents=True,exist_ok=True)
def fetch(url):
    return subprocess.check_output(['curl','-fL','--max-time','60',url])
def main():
    redis=extra/'redis-6.2.7'
    if not redis.exists():
        data=fetch('https://download.redis.io/releases/redis-6.2.7.tar.gz')
        (extra/'redis.tar.gz').write_bytes(data)
        with tarfile.open(fileobj=io.BytesIO(data)) as f:f.extractall(extra,filter='data')
    subprocess.run(['make','-C',str(redis),'-j','8','MALLOC=libc','USE_JEMALLOC=no','BUILD_TLS=no','REDIS_CFLAGS=-g -fno-omit-frame-pointer','REDIS_LDFLAGS='],check=True)
    for name in ('redis-server','redis-cli','redis-benchmark'):
        shutil.copy2(redis/'src'/name,build/'bench'/name)
    outcomes={}
    for n,url,sha,filename in [
        (6,'http://www.microquill.com/smartheap/shbench/bench.zip','506354d66b9eebef105d757e055bc55e8d4aea1e7b51faab3da35b0466c923a1','sh6bench.c'),
        (8,'http://www.microquill.com/smartheap/SH8BENCH.zip','12a8e75248c9dcbfee28245c12bc937a16ef56ec9cbfab88d0e348271667726f','SH8BENCH.C')]:
        try:
            data=subprocess.check_output(['curl','-fL','--max-time','60',url])
            if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('upstream checksum mismatch')
            archive=zipfile.ZipFile(io.BytesIO(data)); src=archive.read(filename).replace(b'\r\n',b'\n')
            raw=extra/f'sh{n}bench.c';raw.write_bytes(src)
            patch=(ROOT/f'third_party/mimalloc-bench/bench/shbench/sh{n}bench.patch').read_bytes().replace(b'\r\n',b'\n')
            dest=extra/f'sh{n}bench-new.c'
            subprocess.run(['patch','-p1','-o',str(dest),str(raw)],input=patch,check=True)
            subprocess.run(['cc','-O3','-g','-fno-omit-frame-pointer','-DBENCH=1','-DSYS_MULTI_THREAD=1',str(dest),'-pthread','-o',str(build/'bench'/f'sh{n}bench')],check=True)
            outcomes[f'sh{n}bench']='built'
        except Exception as e:outcomes[f'sh{n}bench']=str(e)
    import json
    (ROOT/'results/extras.json').write_text(json.dumps(outcomes,indent=2))
    print(outcomes)
if __name__=='__main__':main()
