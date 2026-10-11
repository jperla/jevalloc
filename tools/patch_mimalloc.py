"""Apply documented core-only patches in the build tree; never edit the vendor."""
import pathlib, subprocess, sys
source, out, patch = map(pathlib.Path, sys.argv[1:])
(out/'src').mkdir(parents=True,exist_ok=True)
for name in ('segment','heap','init','alloc','free'):(out/f'src/{name}.c').write_bytes((source/f'src/{name}.c').read_bytes())
subprocess.run(['patch','-s','-p1','-i',str(patch.resolve())],cwd=out,check=True)
