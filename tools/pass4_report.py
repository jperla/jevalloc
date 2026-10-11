#!/usr/bin/env python3
"""Publish completed pass-4 results only after tests, gates and audits pass."""
import json,subprocess,sys,hashlib
from pathlib import Path
from selection import complete_groups
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
# Recompute against the exact matrix being published; a stale gate file is not evidence.
subprocess.run([sys.executable,str(ROOT/'tools/acceptance.py'),str(R/'acceptance-final.json'),'--output',str(R/'acceptance-final-gate.json')],check=True,stdout=subprocess.DEVNULL)
for name in ('acceptance-final-gate.json','frag-instrument/gate.json','tests.json'):
    if not json.loads((R/name).read_text()).get('passed'):raise SystemExit('Unpassed validation: '+name)
for name in ('acceptance-final.inference-audit.json','fragbench/matrix.inference-audit.json','pass4.inference-audit.json'):
    audit=json.loads((R/name).read_text())
    if audit['overlapping_runs']:raise SystemExit('Inference overlap: '+name)
    matrix=R/name.replace('.inference-audit.json','.json')
    if audit.get('matrix_sha256')!=hashlib.sha256(matrix.read_bytes()).hexdigest():raise SystemExit('Stale inference audit: '+name)
frag=json.loads((R/'fragbench/matrix.json').read_text());reg=json.loads((R/'pass4.json').read_text())
acceptance=json.loads((R/'acceptance-final.json').read_text());tests=json.loads((R/'tests.json').read_text())
def library_hash(data):
    values=[v for k,v in data['configuration']['fingerprints'].items() if Path(k).name=='libjevalloc.so']
    if len(values)!=1:raise SystemExit('Missing or ambiguous library fingerprint')
    return values[0]
if not tests.get('full_suite'):raise SystemExit('Full make test has not passed on this build')
if len({library_hash(d) for d in (acceptance,frag,reg)}|{tests.get('library_sha256')})!=1:raise SystemExit('Validation and matrices refer to different libraries')
validated_hash=tests['library_sha256']
if hashlib.sha256((ROOT/'build/libjevalloc.so').read_bytes()).hexdigest()!=validated_hash:raise SystemExit('Current library differs from the validated build')
if json.loads((R/'frag-instrument/gate.json').read_text())['library_sha256']!=validated_hash:raise SystemExit('Instrument refers to a different library')

for data in (frag,reg):
    _,complete=complete_groups(data)
    if len(complete)!=len(data['configuration']['workloads']):raise SystemExit('Incomplete or rejected matrix')
    for r in data['runs']:
        if r['repetition']>=0 and (r.get('model_seconds') or r.get('replay_missing')):raise SystemExit('Warm model work or missing replay')
fragmentation=subprocess.check_output([sys.executable,str(ROOT/'tools/frag_summary.py'),str(R/'fragbench/matrix.json')],text=True)
regression=subprocess.check_output([sys.executable,str(ROOT/'tools/matrix_summary.py'),str(R/'pass4.json')],text=True)
notes='''
The oracle is a byte-majority label per site from a separate trace of the same workload.
Site-mixed includes data-dependent TTL choices that a fixed site label cannot separate;
the truth JSON files record that classification ceiling, not an RSS upper bound.
Live clocks merge with 4,096-success thread/site batches, decisions and thread exit and lifetimes sample 1/64 per thread/site.
Rechecks are approximate across threads. Replay retains the true-live instrumentation.
Success totals include every allocation from joined/exited threads; snapshots of
active workers omit their unmerged batches (up to 4,095 allocations per thread/site).
Cold inference and coverage fills are excluded from headline medians. Each model policy
has a 400-decision cold budget shared with fills. Prompt v2, key depth 4, model depth 12.

Phase RSS is measured from /proc after common settle/purge settings. Synthetic live
bytes are requested bytes; Redis used_memory includes metadata and usable-size effects.
The sidecar/model server is excluded from allocator RSS. Model/heuristic comparisons
refer to observed medians; five repetitions do not establish statistical equivalence.
Duration-limited regression scores are inverse throughput, not elapsed time.
The rss/rate rows additionally normalize peak RSS by throughput, using paired
RSS × score observations. They do not establish a fixed-work fragmentation effect.
Per-repetition observations and per-workload min/max ranges are retained in
`results/pass4.json` and its companion `results/pass4.md`.
'''
result='# jevalloc — pass 4 results\n\n**Status: complete.** Full Linux tests, both acceptance gates, and inference audits passed. Five interleaved warm repetitions; full data remain under results/fragbench and results/pass4.json.\n\nValidated library SHA-256: `'+validated_hash+'`.\n\n'+fragmentation+'\n## mimalloc-bench regression\n\n```text\n'+regression+'```\n'+notes
(ROOT/'RESULTS.md').write_text(result)
execution=ROOT/'CODEX-REPORT.md';(R/'pass4-execution.md').write_text(execution.read_text())
execution.write_text(result+'\n## Implementation and execution record\n\n'+(R/'pass4-execution.md').read_text())
print('Published completed RESULTS.md and CODEX-REPORT.md')
