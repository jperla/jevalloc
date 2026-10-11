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
    if d['configuration'].get('class_schema')!='transient-permanent-v1':raise SystemExit('Wrong class boundary')
    audit_path=path.with_suffix('.inference-audit.json')
    if not audit_path.exists():raise SystemExit('Missing inference audit: '+str(path))
    audit=read(audit_path)
    if audit.get('matrix_sha256')!=sha(path) or audit['overlapping_runs']:raise SystemExit('Stale/failed inference audit: '+str(path))
    hashes=[v for k,v in d['configuration']['fingerprints'].items() if Path(k).name=='libjevalloc.so']
    if hashes!=[tests['library_sha256']]:raise SystemExit('Matrix/test library mismatch')
    for r in d['runs']:
        if r['repetition']>=0 and (r.get('model_seconds') or r.get('replay_missing') or r.get('decision_errors')):raise SystemExit('Invalid warm run')
    return d,groups,names

tests=read(R/'pass6/tests.json')
if not tests.get('passed') or not tests.get('full_suite'):raise SystemExit('Full Linux suite required')
frag,fg,fb=verified(R/'fragbench-permanent/matrix.json')
if len(fb)!=6:raise SystemExit('Fragmentation matrix incomplete')
reg_path=R/'pass6-regression.json';reg=None;rb=[]
if reg_path.exists() and reg_path.with_suffix('.inference-audit.json').exists():reg,rg,rb=verified(reg_path)
sens_path=R/'frag-sensitivity/matrix.json';sensitivity=None;sb=[]
if sens_path.exists() and sens_path.with_suffix('.inference-audit.json').exists():sensitivity,sg,sb=verified(sens_path)
status='complete' if reg and len(rb)==22 and len(sb)==2 else 'fragmentation and sensitivity complete; regression pending/incomplete' if len(sb)==2 else 'fragmentation complete; sensitivity and regression pending/incomplete'
headline=['| Workload | mi idle MiB | Oracle | Heuristic | Code-only Clef | Runtime Clef | Oracle saving vs mi |', '|---|---:|---:|---:|---:|---:|---:|']
for b in fb:
    v=('mi','jev-table:oracle','jev-live:heuristic','jev-live:static-model','jev-live:model')
    rss=[metrics(fg[b,name])['rss'] for name in v]
    headline.append('| '+b+' | '+' | '.join(f'{value/2**20:.2f}' for value in rss)+f' | {1-rss[1]/rss[0]:.1%} |')
headline='\n'.join(headline)+'\n'
lines=['# jevalloc — transient and permanent allocations',f'\n**Status: {status}.** Five interleaved warm repetitions per completed workload. Full Linux correctness passed on the measured library.',f"\nLibrary SHA-256: `{tests['library_sha256']}`.",'''
Classes are **transient = 0** and **permanent = 1**. Permanent means never freed,
or alive for strictly more than half the program's final requested allocation volume.
The oracle chooses the byte-majority label per site from a prior trace, with ties
transient. Unknown sites default transient. Keys use four frames; model context
uses twelve named frames and three marked ±20-line source snippets plus hand-written
program descriptions. The oracle is a classification control, not an RSS optimum.

The prompt asks whether the object is released while the program keeps running or
kept for the rest of the program. Runtime rechecks add sampled requested-byte shares
freed quickly, freed later and not freed so far. Static-model omits runtime state
and never rechecks. Schema 3 and transient-permanent-v1 cache identities reject
short/long replay and response caches. No completed round-5 study was present at
start, so the wording in SPEC-PERMANENT is used.

The no-model heuristic maintains a deterministic uniform 128-entry reservoir of
sampled allocation births and free status per site. With at least 16 entries, take
the count median age (lower median for an even count), select strictly older entries,
and choose permanent if their freed requested bytes are strictly under 5% of their
total bytes. With no such evidence choose transient. Births stay in the reservoir
after free; replacement is independent of survival. It needs no final-run length.

## Fragmentation
''',headline,capture('frag_summary.py',R/'fragbench-permanent/matrix.json').replace('# Fragmentation results\n','',1)]
lines += ['![Audited synthetic idle RSS](results/pass6/progress/synthetic-rss.png)', 'The figure shows the four synthetic workloads; Redis measurements are in the tables.']
phase_lines=['# All fragmentation phase medians','', '| Workload | Variant | Cycle | Phase | RSS MiB | Live MiB | RSS/live |', '|---|---|---:|---|---:|---:|---:|']
for b in fb:
    for v in frag['configuration']['variants']:
        phase_keys=sorted({(p['cycle'],p['phase']) for r in fg[b,v] for p in r['phases']})
        for cycle,phase in phase_keys:
            observations=[p for r in fg[b,v] for p in r['phases'] if (p['cycle'],p['phase'])==(cycle,phase)]
            if len(observations)!=5:raise SystemExit('Incomplete phase observations')
            med=lambda k:statistics.median(p[k] for p in observations)
            phase_lines.append(f"| {b} | {v} | {cycle} | {phase} | {med('rss_bytes')/2**20:.3f} | {med('live_bytes')/2**20:.3f} | {med('fragmentation_ratio'):.3f} |")
(R/'pass6/phases.md').write_text('\n'.join(phase_lines)+'\n')
lines+=['All peak, drop and idle phase medians are in [phases.md](results/pass6/phases.md); raw observations retain per-repetition values.']
from trace_distribution import distribution
distributions={b:distribution(R/'fragbench-permanent'/(b+'.trace.jsonl'),R/'fragbench-permanent/tables'/b/'oracle.txt') for b in fb}
if any(d['oracle_mismatches'] for d in distributions.values()):raise SystemExit('Oracle table/trace mismatch')
(R/'pass6/trace-distributions.json').write_text(json.dumps(distributions,indent=2))
from common import sites
from symbolize import symbolize
hard=[]
for b in fb:
    if not b.startswith('site-mixed'):continue
    rows=sites(R/'fragbench-permanent'/(b+'.trace.jsonl'));symbolize(rows)
    payload=[r for r in rows if any(f.get('function')=='store_request_payload' for f in r['frames'])]
    if len(payload)!=1:raise SystemExit('Mixed allocation PC split or missing')
    row=payload[0];ceiling=max(row['class_bytes'])/row['bytes']
    overall=sum(max(r['class_bytes']) for r in rows)/sum(r['bytes'] for r in rows)
    hard.append(dict(workload=b,payload_key=row['key'],payload_class_bytes=row['class_bytes'],payload_ceiling=ceiling,whole_workload_ceiling=overall))
    lines += [f"{b}: the single mixed payload site has a {ceiling:.2%} byte-majority classification ceiling; the whole-workload ceiling is {overall:.2%}. A fixed label cannot separate the payload's permanent and transient objects; neither percentage bounds attainable RSS."]
(R/'pass6/hard-tier-ceiling.json').write_text(json.dumps(hard,indent=2))
lines+=['Actual object-byte lifetime shares and majority-site assignments are recorded separately in [trace-distributions.json](results/pass6/trace-distributions.json); every oracle table label matches its trace.']
gate=read(R/'frag-instrument/gate.json')
_,_,instrument_workloads=verified(R/'frag-instrument/matrix.json')
if len(instrument_workloads)!=2:raise SystemExit('Instrument observations incomplete')
if gate['library_sha256']!=tests['library_sha256'] or gate['server_sha256']!=frag['configuration']['fingerprints']['build/server-sim']:raise SystemExit('Instrument build mismatch')
lines+=['\n## Instrument and sensitivity\n',f"The transient/permanent instrument {'passes' if gate['passed'] else 'does not pass'} the requirement of oracle idle RSS at or below random and below half of plain mimalloc at every idle point. This is reported separately from correctness.",'| Workload | Cycle | mi MiB | Random MiB | Oracle MiB | Oracle/mi | Oracle/random |','|---|---:|---:|---:|---:|---:|---:|']
for r in gate['comparisons']:lines.append(f"| {r['workload']} | {r['cycle']} | {r['mi']/2**20:.3f} | {r['random']/2**20:.3f} | {r['oracle']/2**20:.3f} | {r['oracle']/r['mi']:.4f} | {r['oracle']/r['random']:.4f} |")
lines+=['''
The synthetic workload is unchanged from the corrected pass-5 version. Four
lifetime wrapper names remain distinct; seeded TTL data cannot split the mixed
allocation PC. The previous fixed-S oracle merged sessions with permanent cache
entries. That wrong-boundary finding is preserved in results/pass5-shortlong on
the test machine and the local results/pass5/progress snapshots: single-thread
mimalloc/oracle/random idle RSS was 280.22/280.07/42.55 MiB. All four synthetic
short/long blocks completed; Redis was stopped during cold decision collection.
Those measurements are historical and are not combined with this pass.
''']
historical=R/'pass5-shortlong/pass5/progress/fragbench-synthetic-complete.json'
if historical.exists():
    old=read(historical);old_groups,old_names=complete_groups(old)
    old_audit=read(historical.with_suffix('.inference-audit.json'))
    if old_audit['matrix_sha256']!=sha(historical) or old_audit['overlapping_runs']:raise SystemExit('Historical audit mismatch')
    lines += ['Historical wrong-boundary result (short/long at S=1 MiB), idle RSS MiB:', '| Workload | mi | Fixed-S oracle | Random | Heuristic | Static Clef | Adaptive Clef |', '|---|---:|---:|---:|---:|---:|---:|']
    for b in old_names:
        lines.append('| '+b+' | '+' | '.join(f"{metrics(old_groups[b,v])['rss']/2**20:.2f}" for v in ('mi','jev-table:oracle','jev-table:random','jev-live:heuristic','jev-live:static-model','jev-live:model'))+' |')
if sensitivity:
    lines+=['Oracle sensitivity: table-only controls, no model. Median final-idle RSS.', '| Workload | >25% | >50% | >90% | Never freed only | S=64 KiB | S=1 MiB | S=16 MiB |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for b in sb:lines.append('| '+b+' | '+' | '.join(f"{metrics(sg[b,v])['rss']/2**20:.3f}" for v in ('jev-table:oracle-P-25','jev-table:oracle','jev-table:oracle-P-90','jev-table:oracle-P-never','jev-table:oracle-S-65536','jev-table:oracle-S-1048576','jev-table:oracle-S-16777216'))+' |')
else:lines+=['Sensitivity measurements are pending.']
lines+=['\n## Model budget and accuracy\n','Each cold model policy has 400 decisions shared with coverage fills. Identical native two-class model payloads share a raw response cache across policies/workloads; cached answers still consume decision slots, and original backend provenance is retained. Headline runs replay recorded answers with unchanged live instrumentation and no inference. Changed request states are logged: this measures the recorded policy, not whether the model would choose the same answers on warm state. Model server memory is excluded from allocator RSS.','| Workload | Policy | Cold decisions | Model rechecks | Cold unasked byte share | Warm unasked byte share |','|---|---|---:|---:|---:|---:|']
accuracy=[]
no_runtime=[]
site_evidence=[]
default_evidence=[]
datasets=[(frag,fg,fb,R/'fragbench-permanent/tables')]
if reg:datasets.append((reg,rg,rb,R/'tables'))
for dataset,groups,benches,table_root in datasets:
 for b in benches:
    truth=dict(line.split() for line in (table_root/b/'oracle.txt').read_text().splitlines())
    major=[]
    if b.startswith('site-pure'):
        traced=sites(R/'fragbench-permanent'/(b+'.trace.jsonl'));symbolize(traced)
        major=sorted(traced,key=lambda s:s['bytes'],reverse=True)[:4]
    for v in ('jev-live:heuristic','jev-live:static-model','jev-live:model'):
        cold=next(r for r in dataset['runs'] if r['benchmark']==b and r['variant']==v and r.get('cold'))
        events=[json.loads(l) for l in (ROOT/cold['decision_log']).read_text().splitlines()]
        for site in major:
            timeline=[]
            for event in events:
                if event.get('request',{}).get('key')!=site['key'] or 'response' not in event:continue
                observed=event['request']['site']
                timeline.append(dict(ordinal=event['ordinal'],class_=event['response']['class'],allocs=observed['allocs'],quick_freed_percent=observed['short_share'],later_freed_percent=observed['long_freed_share'],alive_percent=observed['alive_share'],older_bytes=observed['older_sampled_bytes'],older_freed_bytes=observed['older_freed_bytes'],probabilities=(event.get('raw_response') or {}).get('answers',{}).get('lifetime',{}).get('probabilities')))
            site_evidence.append(dict(workload=b,policy=v,decision_log=cold['decision_log'],key=site['key'],stack=[f.get('function','?') for f in site['frames'][:4]],bytes=site['bytes'],oracle=int(truth[site['key']]),timeline=timeline))
        if v!='jev-live:heuristic':
            c=cold['model_coverage'];warm=[r['model_coverage'] for r in groups[b,v]];den=sum(r['allocated_bytes'] for r in warm)
            lines.append(f"| {b} | {v.split(':')[1]} | {sum(e.get('raw_response') is not None for e in events)} | {sum(e.get('raw_response') is not None and e.get('ordinal',0)>0 for e in events)} | {c['unasked_byte_share']:.2%} | {sum(r['unasked_bytes'] for r in warm)/den:.2%} |")
        if v!='jev-live:heuristic':
            asked={e['request']['key'] for e in events if e.get('raw_response') is not None}
            sizes=cold['allocator_stats']['site_bytes'];unasked={k:n for k,n in sizes.items() if k not in asked}
            permanent=sum(n for k,n in unasked.items() if truth.get(k)=='1');transient=sum(n for k,n in unasked.items() if truth.get(k)=='0')
            default_evidence.append(dict(workload=b,policy=v,permanent_bytes=permanent,transient_bytes=transient,unknown_bytes=sum(unasked.values())-permanent-transient))
        if v=='jev-live:model' and not any(e.get('raw_response') is not None and e.get('ordinal',0)>0 for e in events):no_runtime.append(b)
        for scope in ('policy','model-only'):
            selected=[e for e in events if 'response' in e and (scope=='policy' or e.get('raw_response'))]
            unknown=sum(e['request']['key'] not in truth for e in selected)
            for stage in ('first','rechecks','final'):
                subset=[e for e in selected if e['ordinal']==0] if stage=='first' else [e for e in selected if e['ordinal']>0] if stage=='rechecks' else list({e['request']['key']:e for e in sorted(selected,key=lambda e:e['ordinal'])}.values())
                matched=[e for e in subset if e['request']['key'] in truth];cm=[[0,0],[0,0]]
                for e in matched:cm[int(truth[e['request']['key']])][e['response']['class']]+=1
                byte_totals=cold['allocator_stats']['site_bytes']
                accuracy.append(dict(decision_log=cold['decision_log'],workload=b,policy=v,scope=scope,stage=stage,truth_sites=len(truth),observed_sites=len(byte_totals),matched_sites=sum(k in truth for k in byte_totals),total_successful_bytes=sum(byte_totals.values()),matched_successful_bytes=sum(n for k,n in byte_totals.items() if k in truth),observations=len(subset),matched=len(matched),unknown=len(subset)-len(matched),confusion=cm,accuracy=None if unknown or not matched else sum(cm[i][i] for i in range(2))/len(matched)))
if no_runtime:lines += ['No model-backed runtime recheck occurred in: '+', '.join(no_runtime)+'. The adaptive label in those rows does not establish an effect of runtime input; inspect budget/coverage before attributing results to it.']
(R/'pass6/site-decisions.json').write_text(json.dumps(site_evidence,indent=2))
lines += ['Dominant site-pure decision histories, probabilities and observed free shares are in [site-decisions.json](results/pass6/site-decisions.json). Changes affect future allocations only; earlier permanent objects can continue pinning pages.']
(R/'pass6/accuracy.json').write_text(json.dumps(accuracy,indent=2))
(R/'pass6/default-evidence.json').write_text(json.dumps(default_evidence,indent=2))
permanent_default=sum(x['permanent_bytes'] for x in default_evidence);transient_default=sum(x['transient_bytes'] for x in default_evidence)
lines += [f"Among unasked cold-model bytes with matching prior-trace site truth, {transient_default/(transient_default+permanent_default):.1%} belong to majority-transient sites. This aggregate {'supports transient' if transient_default>=permanent_default else 'argues for permanent'} as the classification fallback, not necessarily the memory-optimal fallback; the tested default remains transient. Policies and workloads contribute separate observations, not independent samples." if transient_default+permanent_default else 'No matched unasked cold bytes establish a fallback preference.']

lines+=['','Cold accuracy populations and two-class confusion matrices are in [accuracy.json](results/pass6/accuracy.json). Rechecks are repeated decisions, not independent sites. Scores are withheld if any decision key lacks matching trace truth. Budget defaults are separated from model-backed answers.','']
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
    (R/'pass6/regression-trace-distributions.json').write_text(json.dumps(rd,indent=2))
    lines+=['Regression object-byte shares and majority-site shares are in [regression-trace-distributions.json](results/pass6/regression-trace-distributions.json).']
    lines+=['```text',capture('matrix_summary.py',reg_path),'```','Time means elapsed time or inverse-throughput score as appropriate; duration-limited workloads do not provide fixed-work RSS comparisons. RSS × score rows additionally show memory per throughput.']
    proc=subprocess.run([sys.executable,str(ROOT/'tools/acceptance.py'),str(reg_path),'--output',str(R/'pass6/acceptance-targets.json')],capture_output=True,text=True)
    if proc.returncode not in (0,1):raise RuntimeError(proc.stderr)
    targets=read(R/'pass6/acceptance-targets.json')
    lines+=['\n### Remaining performance target misses\n','| Workload | Metric | Measured ratio | Target | Suspected cause |','|---|---|---:|---:|---|']
    for r in targets['checks']:
        for key,target in (('none_time',1.03),('none_rss',1.03),('keyonly_rss',1.03),('live_time',1.15)):
            if r.get(key,0)>target:
                cause='Capture and sampled pointer/statistics work remain on the true-live path.' if key=='live_time' else 'Additional wrapper/startup instructions.' if key=='none_time' else 'Page fault/accounting and thread/segment retention; five-run peaks can form different clusters.'
                lines.append(f"| {r['workload']} | {key} | {r[key]:.4f} | {target:.2f} | {cause} |")
else:lines+=['Regression has not completed; no aggregate claim is made. The interrupted three-class acceptance completed 21/22 workloads and is archived in results/pass5/prior.']
lines+=['''
## Measurement limits and interpretation

Unknown sites default transient because most requested allocation volume is
expected to be released. The all-transient/all-permanent controls are reported;
they do not directly test changing only the fallback for unseen sites. Neither
uniform control isolates the effect of changing that fallback alone.

Live lifetimes sample one allocation in 64 per thread/site. Success counters merge
every 4,096 allocations, at decisions and thread exit. Replay retains the same
instrumentation. Batched clocks, finite reservoirs and concurrent snapshots are
approximate; active workers can leave 4,095 unmerged allocations per thread/site
at exit. Retired sampled owners survive until their final cross-thread free.

Synthetic live bytes are requested bytes; Redis used_memory includes metadata and
usable-size effects. Every fragmentation variant uses MIMALLOC_PURGE_DELAY=0,
MIMALLOC_ARENA_PURGE_MULT=1 and MIMALLOC_PURGE_DECOMMITS=1, with the same settle/pulse.
Oracle-saving capture is (mi RSS - policy RSS)/(mi RSS - oracle RSS), undefined when the oracle saves no memory. It may be negative or exceed 100%; a small oracle saving makes the fraction unstable. Five repetitions show medians and ranges, not statistical equivalence. Raw phase,
stdout/stderr, replay/fill and inference-audit records remain on the test machine.

The pass-4 and pass-5 fixes are preserved, including copying the sidecar socket path
before applications can overwrite environment storage (Redis setproctitle), and
retaining each site's first model stack so cache collisions cannot change recheck
source context. Linux supports startup images only; dynamic loading/unloading and
post-fork synchronization remain outside the validated set.
''']
text='\n'.join(lines).replace('\n| Workload','\n\n| Workload');(ROOT/'RESULTS.md').write_text(text)
(R/'pass6/report.md').write_text(text.replace('(results/pass6/','('))
with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write('\n## Pass 6 measured report\n\n'+text+'\n')
print(status)
