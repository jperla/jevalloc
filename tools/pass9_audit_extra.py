"""Collect independent search/gate intervals for the existing server-log audit."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'results/pass9';runs=[]
for path in base.glob('*/matrix.json'):
 d=json.loads(path.read_text())
 if d.get('complete'):runs.extend(d.get('search_runs',[]));runs.extend(d.get('gate_runs',[]))
path=base/'search-gate-intervals.json';path.write_text(json.dumps(dict(runs=runs),indent=2))
subprocess.run([sys.executable,str(ROOT/'tools/audit_pass4.py'),str(path)],check=True)
