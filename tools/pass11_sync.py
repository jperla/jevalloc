#!/usr/bin/env python3
"""Synchronize compact evidence; optional watcher never persists the SSH destination."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/pass11'
def command(args):
 # Capture transport errors rather than saving a command/exception with its address.
 result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
 if result.returncode:raise RuntimeError('Evidence synchronization failed (exit '+str(result.returncode)+'); destination omitted')
 return result.stdout

def sync():
 destination=os.environ['JEVALLOC_REMOTE']
 command(['rsync','-a','-e','ssh -o BatchMode=yes','--exclude=logs/','--exclude=tables/','--exclude=cache/','--exclude=model-cache/','--exclude=trace.jsonl','--exclude=*.log',destination+':jevalloc/src-tree/results/pass11/',str(BASE)+'/'])
 checkpoint=BASE/'sync-state.json';old=json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
 signature=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(BASE.rglob('*.inference-audit.json')))).hexdigest()
 if old.get('_audit_signature')!=signature or not (BASE/'summary.json').exists():
  subprocess.run([sys.executable,str(ROOT/'tools/pass11_report.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 summary=json.loads((BASE/'summary.json').read_text())
 state=dict(redis_complete=summary['redis_complete'],factorial_complete=summary['factorial_complete'],diagnostic_phases=len(summary['diagnostic']),stage=(BASE/'stage.txt').read_text().strip())
 if (BASE/'status').exists():state['exit_status']=int((BASE/'status').read_text())
 state['_audit_signature']=signature
 if not old:old=state
 if any(old.get(k)!=state[k] for k in ('redis_complete','factorial_complete','diagnostic_phases')):
  with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write('\nPass-11 synchronized milestone: Redis '+str(state['redis_complete'])+'/4 audited blocks; factorial '+str(state['factorial_complete'])+'/24 audited blocks; '+str(state['diagnostic_phases'])+' diagnostic phase observations. Compact evidence and recomputed tables are local under results/pass11; all other groups remain pending.\n')
 checkpoint.write_text(json.dumps(state,indent=2)+'\n')
 print(json.dumps({k:v for k,v in state.items() if not k.startswith('_')}),flush=True)
 return state

def main():
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
 while True:
  try:state=sync()
  except RuntimeError:
   if not a.watch:raise
   print('Evidence transfer failed; retrying in 60 seconds (destination omitted).',flush=True)
   time.sleep(60)
   continue
  if 'exit_status' in state:
   if state['exit_status']:raise SystemExit(state['exit_status'])
   assert state['stage']=='complete' and json.loads((BASE/'validation.json').read_text())['passed']
   subprocess.run([sys.executable,str(ROOT/'tools/pass11_finish.py')],cwd=ROOT,check=True)
   return
  if not a.watch:return
  time.sleep(60)
if __name__=='__main__':main()
