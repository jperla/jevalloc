#!/usr/bin/env python3
"""Publish measured two-class results, with honest completeness and target misses."""
import hashlib,json,statistics,subprocess,sys
from pathlib import Path
from selection import complete_groups
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bench'))
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def capture(script,*args):return subprocess.check_output([sys.executable,str(ROOT/'tools'/script),*map(str,args)],text=True)
def metrics(rows):
    phase=[max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p['cycle']) for r in rows]
    return dict(rss=statistics.median(p['rss_bytes'] for p in phase),time=statistics.median(r['wall_seconds'] for r in rows))
def verified(path):
    d=read(path);groups,names=complete_groups(d)
    audit_path=path.with_suffix('.inference-audit.json')
    if not audit_path.exists():raise SystemExit('Missing inference audit: '+str(path))
    audit=read(audit_path)
    if audit.get('matrix_sha256')!=sha(path) or audit['overlapping_runs']:raise SystemExit('Stale/failed inference audit: '+str(path))
    hashes=[v for k,v in d['configuration']['fingerprints'].items() if Path(k).name=='libjevalloc.so']
    if hashes!=[tests['library_sha256']]:raise SystemExit('Matrix/test library mismatch')
    for r in d['runs']:
        if r['repetition']>=0 and (r.get('model_seconds') or r.get('replay_missing') or r.get('decision_errors')):raise SystemExit('Invalid warm run')
    return d,groups,names

tests=read(R/'pass5/tests.json')
if not tests.get('passed') or not tests.get('full_suite'):raise SystemExit('Full Linux suite required')
frag,fg,fb=verified(R/'fragbench-two/matrix.json')
if len(fb)!=6:raise SystemExit('Fragmentation matrix incomplete')
reg_path=R/'pass5-regression.json';reg=None;rb=[]
if reg_path.exists() and reg_path.with_suffix('.inference-audit.json').exists():reg,rg,rb=verified(reg_path)
sens_path=R/'frag-sensitivity/matrix.json';sensitivity=None;sb=[]
if sens_path.exists() and sens_path.with_suffix('.inference-audit.json').exists():sensitivity,sg,sb=verified(sens_path)
status='complete' if reg and len(rb)==22 and len(sb)==6 else 'fragmentation complete; sensitivity or regression pending/incomplete'
lines=['# jevalloc — two lifetime classes',f'\n**Status: {status}.** Five interleaved warm repetitions per completed workload. Full Linux correctness passed on the measured library.',f"\nLibrary SHA-256: `{tests['library_sha256']}`.",'''
Classes are **short = 0** (freed before another S requested bytes are allocated) and
**long = 1** (everything else, including never freed), with S = 1 MiB by default.
Unknown sites default to long. Allocator keys use four normalized frames; model
evidence captures up to twelve. The oracle assigns one byte-majority class per site
from a prior trace; ties choose long. It is not a per-object classifier or an RSS bound.

Program descriptions are hand-written from source/docs in `descriptions/`. Prompt v2
asks whether the allocation is a temporary or kept, with up to twelve named frames,
three marked ±20-line snippets and a description. Model rechecks add quantised sampled
byte percentages in plain sentences. Static-model omits those observations and never
rechecks. Native two-class decisions have schema 2 and cannot reuse three-class caches.
The default prompt was selected while the independent round-4 study was still running.

## Fragmentation
''',capture('frag_summary.py',R/'fragbench-two/matrix.json').replace('# Fragmentation results\n','',1)]
phase_lines=['# All fragmentation phase medians','', '| Workload | Variant | Cycle | Phase | RSS MiB | Live MiB | RSS/live |', '|---|---|---:|---|---:|---:|---:|']
for b in fb:
    for v in frag['configuration']['variants']:
        phase_keys=sorted({(p['cycle'],p['phase']) for r in fg[b,v] for p in r['phases']})
        for cycle,phase in phase_keys:
            observations=[p for r in fg[b,v] for p in r['phases'] if (p['cycle'],p['phase'])==(cycle,phase)]
            if len(observations)!=5:raise SystemExit('Incomplete phase observations')
            med=lambda k:statistics.median(p[k] for p in observations)
            phase_lines.append(f"| {b} | {v} | {cycle} | {phase} | {med('rss_bytes')/2**20:.3f} | {med('live_bytes')/2**20:.3f} | {med('fragmentation_ratio'):.3f} |")
(R/'pass5/phases.md').write_text('\n'.join(phase_lines)+'\n')
lines+=['All peak, drop and idle phase medians are in [phases.md](results/pass5/phases.md); raw observations retain per-repetition values.']
from trace_distribution import distribution
distributions={b:distribution(R/'fragbench-two'/(b+'.trace.jsonl'),R/'fragbench-two/tables'/b/'oracle.txt') for b in fb}
if any(d['oracle_mismatches'] for d in distributions.values()):raise SystemExit('Oracle table/trace mismatch')
(R/'pass5/trace-distributions.json').write_text(json.dumps(distributions,indent=2))
lines+=['Actual object-byte lifetime shares and majority-site assignments are recorded separately in [trace-distributions.json](results/pass5/trace-distributions.json); every oracle table label matches its trace.']
gate=read(R/'frag-instrument/gate.json')
_,_,instrument_workloads=verified(R/'frag-instrument/matrix.json')
if len(instrument_workloads)!=2:raise SystemExit('Instrument observations incomplete')
if gate['library_sha256']!=tests['library_sha256'] or gate['server_sha256']!=frag['configuration']['fingerprints']['build/server-sim']:raise SystemExit('Instrument build mismatch')
lines+=['\n## Instrument and sensitivity\n',f"The nominal two-class instrument {'passes' if gate['passed'] else 'does not pass'} its strict lower-RSS-at-every-idle comparison. This is reported separately from correctness.",'| Workload | Cycle | Key-only MiB | Oracle MiB | Oracle/key |','|---|---:|---:|---:|---:|']
for r in gate['comparisons']:lines.append(f"| {r['workload']} | {r['cycle']} | {r['keyonly']/2**20:.3f} | {r['oracle']/2**20:.3f} | {r['oracle']/r['keyonly']:.4f} |")
lines+=['''
The original high-volume synthetic workload retains sessions until a load drop.
At 1 MiB, almost all session bytes and all cache bytes are long, so two classes no
longer separate those two populations. The archived three-class instrument's large
improvement is not evidence for this two-class policy. The site-pure lifetimes and scale are preserved. The mixed tier explicitly uses
seeded TTL data (50% immediate, 45% load-drop, 5% never freed); trace checks require
one mixed allocation PC. GCC identical-code folding is disabled for server-sim,
and an opaque TTL helper prevents branch threading from splitting the mixed site.
The earlier partial matrix with folded debug identities is archived and excluded. Random labels
can split sessions from cache entries despite disagreeing with fixed-S truth; when
they reduce RSS, they demonstrate that the allocation mechanism still works and
that label accuracy is not the same objective as resident fragmentation.
''']
if sensitivity:
    lines+=['Oracle sensitivity: table-only controls, no model. Median final-idle RSS.','| Workload | RSS MiB at S=64 KiB | RSS MiB at S=1 MiB | RSS MiB at S=16 MiB |','|---|---:|---:|---:|']
    for b in sb:lines.append('| '+b+' | '+' | '.join(f"{metrics(sg[b,v])['rss']/2**20:.3f}" for v in ('jev-table:oracle-65536','jev-table:oracle','jev-table:oracle-16777216'))+' |')
else:lines+=['Sensitivity measurements are pending.']
lines+=['\n## Model budget and accuracy\n','Each cold model policy has 400 decisions shared with coverage fills. Identical native two-class model payloads share a raw response cache across policies/workloads; cached answers still consume decision slots, and original backend provenance is retained. Headline runs replay recorded answers with unchanged live instrumentation and no inference. Changed request states are logged: this measures the recorded policy, not whether the model would choose the same answers on warm state. Model server memory is excluded from allocator RSS.','| Workload | Policy | Cold decisions | Cold unasked byte share | Warm unasked byte share |','|---|---|---:|---:|---:|']
accuracy=[]
datasets=[(frag,fg,fb,R/'fragbench-two/tables')]
if reg:datasets.append((reg,rg,rb,R/'tables'))
for dataset,groups,benches,table_root in datasets:
 for b in benches:
    truth=dict(line.split() for line in (table_root/b/'oracle.txt').read_text().splitlines())
    for v in ('jev-live:heuristic','jev-live:static-model','jev-live:model'):
        cold=next(r for r in dataset['runs'] if r['benchmark']==b and r['variant']==v and r.get('cold'))
        events=[json.loads(l) for l in (ROOT/cold['decision_log']).read_text().splitlines()]
        if v!='jev-live:heuristic':
            c=cold['model_coverage'];warm=[r['model_coverage'] for r in groups[b,v]];den=sum(r['allocated_bytes'] for r in warm)
            lines.append(f"| {b} | {v.split(':')[1]} | {sum(e.get('raw_response') is not None for e in events)} | {c['unasked_byte_share']:.2%} | {sum(r['unasked_bytes'] for r in warm)/den:.2%} |")
        for scope in ('policy','model-only'):
            selected=[e for e in events if 'response' in e and (scope=='policy' or e.get('raw_response'))]
            unknown=sum(e['request']['key'] not in truth for e in selected)
            for stage in ('first','rechecks','final'):
                subset=[e for e in selected if e['ordinal']==0] if stage=='first' else [e for e in selected if e['ordinal']>0] if stage=='rechecks' else list({e['request']['key']:e for e in sorted(selected,key=lambda e:e['ordinal'])}.values())
                matched=[e for e in subset if e['request']['key'] in truth];cm=[[0,0],[0,0]]
                for e in matched:cm[int(truth[e['request']['key']])][e['response']['class']]+=1
                byte_totals=cold['allocator_stats']['site_bytes']
                accuracy.append(dict(decision_log=cold['decision_log'],workload=b,policy=v,scope=scope,stage=stage,truth_sites=len(truth),observed_sites=len(byte_totals),matched_sites=sum(k in truth for k in byte_totals),total_successful_bytes=sum(byte_totals.values()),matched_successful_bytes=sum(n for k,n in byte_totals.items() if k in truth),observations=len(subset),matched=len(matched),unknown=len(subset)-len(matched),confusion=cm,accuracy=None if unknown or not matched else sum(cm[i][i] for i in range(2))/len(matched)))
(R/'pass5/accuracy.json').write_text(json.dumps(accuracy,indent=2))
lines+=['','Cold accuracy populations and two-class confusion matrices are in [accuracy.json](results/pass5/accuracy.json). Rechecks are repeated decisions, not independent sites. Scores are withheld if any decision key lacks matching trace truth. Budget defaults are separated from model-backed answers.','']
lines+=['\n## Cold inference and replay coverage cost\n','These costs are outside the warm timings. HTTP time includes queueing behind the independent prompt study; it is not isolated inference speed. Cached responses retain their original provenance. Coverage fills share the same 400-slot schedule budget.','| Workload | Policy | Final model slots | Cold HTTP s | Fill/probe HTTP s | Cold wall s | Warm changed requests |','|---|---|---:|---:|---:|---:|---:|']
for dataset,groups,benches,table_root in datasets:
 for b in benches:
  for v in ('jev-live:static-model','jev-live:model'):
    cold=next(r for r in dataset['runs'] if r['benchmark']==b and r['variant']==v and r.get('cold'))
    from run import schedule_path
    path=ROOT/cold['replay_schedule'] if cold.get('replay_schedule') else schedule_path({'name':b},v,(ROOT/cold['decision_log']).parent)
    events=[json.loads(l) for l in path.read_text().splitlines()]
    slots=sum(e.get('raw_response') is not None for e in events)
    if slots>400:raise SystemExit('Shared cold/fill budget exceeded')
    fills=[r for r in dataset.get('coverage_runs',[]) if r['benchmark']==b and r['variant']==v]
    lines.append(f"| {b} | {v.split(':')[1]} | {slots} | {cold['model_seconds']:.1f} | {sum(r.get('model_seconds',0) for r in fills):.1f} | {cold['wall_seconds']:.1f} | {sum(r.get('replay_drift',0) for r in groups[b,v])} |")
lines+=['\n## mimalloc-bench regression\n']
if reg:
    rd={b:distribution(R/'traces'/(b+'.jsonl'),R/'tables'/b/'oracle.txt') for b in rb}
    if any(d['oracle_mismatches'] for d in rd.values()):raise SystemExit('Regression oracle table/trace mismatch')
    (R/'pass5/regression-trace-distributions.json').write_text(json.dumps(rd,indent=2))
    lines+=['Regression object-byte shares and majority-site shares are in [regression-trace-distributions.json](results/pass5/regression-trace-distributions.json).']
    lines+=['```text',capture('matrix_summary.py',reg_path),'```','Time means elapsed time or inverse-throughput score as appropriate; duration-limited workloads do not provide fixed-work RSS comparisons. RSS × score rows additionally show memory per throughput.']
    proc=subprocess.run([sys.executable,str(ROOT/'tools/acceptance.py'),str(reg_path),'--output',str(R/'pass5/acceptance-targets.json')],capture_output=True,text=True)
    if proc.returncode not in (0,1):raise RuntimeError(proc.stderr)
    targets=read(R/'pass5/acceptance-targets.json')
    lines+=['\n### Remaining performance target misses\n','| Workload | Metric | Measured ratio | Target | Suspected cause |','|---|---|---:|---:|---|']
    for r in targets['checks']:
        for key,target in (('none_time',1.03),('none_rss',1.03),('keyonly_rss',1.03),('live_time',1.15)):
            if r.get(key,0)>target:
                cause='Capture and sampled pointer/statistics work remain on the true-live path.' if key=='live_time' else 'Additional wrapper/startup instructions.' if key=='none_time' else 'Page fault/accounting and thread/segment retention; five-run peaks can form different clusters.'
                lines.append(f"| {r['workload']} | {key} | {r[key]:.4f} | {target:.2f} | {cause} |")
else:lines+=['Regression has not completed; no aggregate claim is made. The interrupted three-class acceptance completed 21/22 workloads and is archived in results/pass5/prior.']
lines+=['''
## Measurement limits and interpretation

The short heap's costly error is a retained object pinning temporary pages. Long
remains the conservative unknown-site default. All-short/all-long controls above
show the cost of each uniform policy, but do not directly test changing only the
unknown-site fallback.

Live lifetimes sample one allocation in 64 per thread/site and use a batched global
byte clock. Success counters merge every 4,096 allocations, at decisions and thread
exit. This preserves a true-live path during replay, but multithreaded lifetime and
recheck timing are approximate. Surviving sampled bytes count as long before their
future free is known. Active workers may leave up to 4,095 unmerged allocations per
thread/site in the exit snapshot; joined threads publish all successes.

Synthetic live bytes are requested bytes; Redis used_memory includes metadata and
usable-size effects. Every fragmentation variant uses MIMALLOC_PURGE_DELAY=0,
MIMALLOC_ARENA_PURGE_MULT=1 and MIMALLOC_PURGE_DECOMMITS=1, with the same settle/pulse.
Five repetitions show medians and ranges, not statistical equivalence. Raw phase,
stdout/stderr, replay/fill and inference-audit records remain on the test machine.

The pass-4 fixes are preserved. Pass 5 additionally copies the sidecar socket path
before applications can overwrite environment storage (Redis setproctitle), and
retains each site's first model stack so cache collisions cannot change recheck
source context. Linux supports startup images only; dynamic loading/unloading and
post-fork synchronization remain outside the validated set.
''']
text='\n'.join(lines).replace('\n| Workload','\n\n| Workload');(ROOT/'RESULTS.md').write_text(text)
(R/'pass5/report.md').write_text(text.replace('(results/pass5/','('))
with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write('\n## Pass 5 measured report\n\n'+text+'\n')
print(status)
