"""Stop the explicitly named pass-5 supervisor and its descendants only."""
import os,signal,sys,time
from pathlib import Path
root=int(sys.argv[1]);cmd=(Path('/proc')/str(root)/'cmdline').read_bytes()
if b'pass5' not in cmd:raise SystemExit('Not a pass5 process')
parents={}
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:parents[int(p.name)]=int((p/'stat').read_text().rsplit(')',1)[1].split()[1])
  except (OSError,ValueError,IndexError):pass
owned={root}
while True:
 more={p for p,parent in parents.items() if parent in owned}-owned
 if not more:break
 owned|=more
for p in sorted(owned,reverse=True):
 try:os.kill(p,signal.SIGTERM)
 except ProcessLookupError:pass
print('Signaled owned pass5 tree:',sorted(owned))
