#!/usr/bin/env python3
"""Detached publication after the supervisor exits; failed gates remain explicit."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';pid=int((R/'pass4.pid').read_text())
while not (R/'pass4.status').exists():
    try:os.kill(pid,0)
    except ProcessLookupError:raise SystemExit('Supervisor disappeared without a status file; publication withheld')
    time.sleep(30)
status=int((R/'pass4.status').read_text())
if status==0:
    # The supervisor publishes before marking complete. Avoid wrapping the execution
    # record in a second copy of the same report when both processes finish.
    if (R/'pass4-stage.txt').read_text().strip()!='complete':
        subprocess.run([sys.executable,str(ROOT/'tools/pass4_report.py')],check=True)
else:
    stage=(R/'pass4-stage.txt').read_text().strip()
    report=ROOT/'RESULTS.md';text=report.read_text();start=text.index('**Status:');end=text.index('\n\n',start)
    text=text[:start]+f'**Status: incomplete — validation stopped (exit {status}, stage: {stage}).** Long model/regression matrices were not started unless all preceding gates passed. See CODEX-REPORT.md and the remote logs.'+text[end:]
    gate=R/'acceptance-final-gate.json'
    if gate.exists():
        data=json.loads(gate.read_text());lines=['## Final acceptance measurements','',f"Complete workloads: {data['complete_workloads']}/{data['expected_workloads']}; gate passed: {data['passed']}.",'','| Workload | none time/mi | none RSS/mi | key RSS/none | live time/oracle | Fix 1 | Fix 2 |','|---|---:|---:|---:|---:|---|---|']
        for c in data['checks']:
            live=f"{c['live_time']:.3f}" if 'live_time' in c else '—'
            lines.append(f"| {c['workload']} | {c['none_time']:.3f} | {c['none_rss']:.3f} | {c['keyonly_rss']:.3f} | {live} | {c['fix1_pass']} | {c.get('fix2_pass','—')} |")
        text+='\n'+'\n'.join(lines)+'\n'
    report.write_text(text)
    with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write(f'\nFinalizer: validation stopped at {stage}, exit {status}. No success or completed-model claim is published.\n')
    print('Recorded validation stop:',stage,status,flush=True)
