#!/usr/bin/env python3
"""Build generated naming fixtures and both Redis context variants locally."""
import json,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args,**kw):subprocess.run(args,cwd=ROOT,check=True,**kw)
def main():
 out=ROOT/'build/pass11';out.mkdir(exist_ok=True)
 design=json.loads((ROOT/'results/pass11/design.json').read_text())
 source=(ROOT/'fragbench/server-sim.c').read_text()
 generated=source.replace('#if defined(JEV_NAMES_OPAQUE)','#if defined(JEV_NAMES_GENERATED)\n#elif defined(JEV_NAMES_OPAQUE)',1)
 (out/'server-sim.c').write_text(generated.replace('../src/jevalloc.h',str(ROOT/'src/jevalloc.h')))
 for m in design['mappings'][1:]:
  h=out/(m['name']+'.h')
  h.write_text('#define JEV_NAMES_GENERATED\n'+''.join(f'#define {a} {b}\n' for a,b in m['functions'].items())+'#define REQUEST_CONTEXT "class=%s"\n'+''.join(f'#define TTL_{a} "{m["contexts"][b]}"\n' for a,b in [('ZERO','0'),('SHORT','short'),('DAY','day')]))
  run(['cc','-O3','-g','-fno-builtin','-fno-omit-frame-pointer','-fno-optimize-sibling-calls','-fno-ipa-icf','-include',str(h),str(out/'server-sim.c'),'-pthread','-o',str(ROOT/'build'/('server-sim-'+m['name']))])
  shutil.copyfile(ROOT/'descriptions/server-sim-plausible.txt',ROOT/'descriptions'/('server-sim-'+m['name']+'.txt'))
 original=ROOT/'build/extras/redis-6.2.7'
 for variant,suffix in [('unnormalized','-unnormalized'),('normalized','')]:
  target=out/('redis-'+variant)
  if not target.exists():
   shutil.copytree(original,target,symlinks=True)
   with (ROOT/'patches'/('redis-request-context'+suffix+'.patch')).open() as patch:run(['patch','-d',str(target),'-p1'],stdin=patch)
  with (ROOT/'results/pass11'/('build-redis-'+variant+'.log')).open('w') as log:
   run(['make','-C',str(target),'-j8','MALLOC=libc','REDIS_CFLAGS=-g -fno-omit-frame-pointer -I'+str(ROOT/'src')],stdout=log,stderr=subprocess.STDOUT)
  shutil.copyfile(target/'src/redis-server',ROOT/'build/bench'/('redis-context-'+variant));(ROOT/'build/bench'/('redis-context-'+variant)).chmod(0o755)
  shutil.copyfile(ROOT/'descriptions/redis-context-server.txt',ROOT/'descriptions'/('redis-context-'+variant+'.txt'))
 files=[ROOT/'build/libjevalloc.so',ROOT/'build/libmimalloc.so',ROOT/'build/server-sim-plausible']+[ROOT/'build'/('server-sim-'+m['name']) for m in design['mappings'][1:]]+[ROOT/'build/bench'/('redis-context-'+v) for v in ('normalized','unnormalized')]
 (ROOT/'results/pass11/builds.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
if __name__=='__main__':main()
