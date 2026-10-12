#!/usr/bin/env python3
"""Publish complete, audited pass-8 blocks and preserve the prior report below."""
import hashlib,json,statistics
from pathlib import Path
from selection import accepted
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/pass8';MIB=2**20
policies=['jev-live:static-model','jev-live:hybrid','jev-live:heuristic']
def read(p):return json.loads(p.read_text())
def median(values):return statistics.median(list(values))
def idle(r):return max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p.get('cycle',0))
def audited(p):
 a=p.with_suffix('.inference-audit.json')
 return a.exists() and read(a)['matrix_sha256']==hashlib.sha256(p.read_bytes()).hexdigest() and read(a)['overlapping_runs']==0

def groups(data):
 result={}
 for r in data['runs']:
  if accepted(r):result.setdefault((r['benchmark'],r['variant']),[]).append(r)
 return {k:v for k,v in result.items() if len(v)==5 and {r['repetition'] for r in v}==set(range(5))}

blocks=[]
pure=OUT/'pure/matrix.json'
if pure.exists() and audited(pure):
 d=read(pure);g=groups(d)
 for b in d['configuration']['workloads']:
  if all((b,v) in g for v in ['mi','jev-table:oracle',*policies]):blocks.append((b,d,{v:rs for (name,v),rs in g.items() if name==b},pure))
for p in sorted((OUT/'real').glob('*/matrix.json')):
 d=read(p)
 if d.get('complete') and audited(p):
  b=d['configuration']['row']['name'];blocks.append((b,d,{v:rs for (name,v),rs in groups(d).items() if name==b},p))
reg=ROOT/'results/pass8-regression.json'
if not reg.exists():reg=OUT/'pass8-regression.json'
regdata=read(reg) if reg.exists() and audited(reg) else None
reggroups=groups(regdata) if regdata else {}
regnames=[b for b in regdata['configuration']['workloads'] if all((b,v) in reggroups for v in regdata['configuration']['variants'])] if regdata else []
testdata=read(OUT/'tests.json') if (OUT/'tests.json').exists() else {}
head=['# Pass 8 — model priors, runtime evidence, and real programs','',f'**Status: {sum(b.startswith("site-pure") for b,*_ in blocks)}/2 site-pure blocks; {sum(not b.startswith("site-pure") for b,*_ in blocks)}/7 real-program workload blocks; {len(regnames)}/22 regression workloads complete and audited.**','',
'The question is whether a code-only Clef-Flash lifetime prior can separate heap allocations well enough to reduce memory after load drops, and whether observed frees can safely correct it. Hybrid asks the model once per admitted site, then applies fixed runtime rules. Pass 7’s repeatedly queried policy remains available as `model-reask`; it was not rerun.','']
for b,d,g,p in blocks:
 base=median(idle(r)['rss_bytes'] for r in g['mi']);tables=[v for v in g if v.startswith('jev-table:')];best=min(median(idle(r)['rss_bytes'] for r in g[v]) for v in tables);saving=base-best
 if 'jev-live:hybrid' in g:
  h=median(idle(r)['rss_bytes'] for r in g['jev-live:hybrid']);s=median(idle(r)['rss_bytes'] for r in g['jev-live:static-model']);he=median(idle(r)['rss_bytes'] for r in g['jev-live:heuristic'])
  head.append(f'{b}: hybrid {h/MIB:.2f} MiB, static-model {s/MIB:.2f} MiB, heuristic {he/MIB:.2f} MiB; hybrid captures {(base-h)/saving:.1%} of the best table’s saving.' if saving>0 else f'{b}: the best table saves no memory; capture is undefined.')

real_blocks=[(b,d,g,p) for b,d,g,p in blocks if not b.startswith('site-pure')]
no_headroom=[b for b,d,g,p in real_blocks if not d['headroom']['eligible']]
if no_headroom:head+=['',f'**No per-site headroom on {len(no_headroom)}/{len(real_blocks)} completed real-program workloads** under the specified oracle and greedy search: '+', '.join(no_headroom)+'. Neither table saved more than 5%, so these workloads received no model decisions.']
head+=['','“No per-site headroom” means neither tested table cleared 5%; it is not a proof over all possible labellings. Search training uses three runs per flip and a strict >2% improvement. In the cache-heavy RocksDB case, training gains failed independent validation amid substantial run variability. Headline measurements are five separate interleaved runs. The oracle is a lifetime-majority table, not an RSS optimum.','',
'## Idle RSS','', '| Workload | mi MiB | Oracle MiB | Search MiB | Best table saving | Static MiB / capture | Hybrid MiB / capture | Heuristic MiB / capture |','|---|---:|---:|---:|---:|---:|---:|---:|']
detail=['# Pass 8 detailed measurements','','Five-run medians [min, max]. Live memory is the program’s own statistic; RocksDB and LevelDB estimates omit other process memory.','', '| Workload | Variant | Idle MiB [range] | Program live MiB | Peak MiB | Wall seconds [range] | Wall/mi | CPU/mi |','|---|---|---:|---:|---:|---:|---:|---:|']
search=['# Greedy search','','All-transient start; top 24 requested-byte sites; three trials per candidate; keep only >2% median idle-RSS improvement. Final measurements are independent.','']
sites_report=[];wrong_priors=[];accuracy=[];table_agreement=[];cost=['## Time and model coverage','','| Workload | Policy | Wall/mi | CPU/mi | Cold wall s | Cold+fill HTTP s | Asked sites | Byte coverage | Runtime demotions |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
for b,d,g,p in blocks:
 rss={v:median(idle(r)['rss_bytes'] for r in rs) for v,rs in g.items()};base=rss['mi'];best=min(rss[v] for v in rss if v.startswith('jev-table:'));saving=base-best
 def capture(v):return '—' if v not in rss else f'{rss[v]/MIB:.2f} / '+(f'{(base-rss[v])/saving:.1%}' if saving>0 else 'n/a')
 head.append(f'| {b} | {base/MIB:.2f} | {rss["jev-table:oracle"]/MIB:.2f} | '+(f'{rss["jev-table:search"]/MIB:.2f}' if 'jev-table:search' in rss else '—')+f' | {saving/base:.1%} | '+ ' | '.join(capture(v) for v in policies)+' |')
 basewall=median(r['wall_seconds'] for r in g['mi']);basecpu=median(r['cpu_seconds'] for r in g['mi'])
 for v,rs in g.items():
  xs=[idle(r)['rss_bytes']/MIB for r in rs];wall=[r['wall_seconds'] for r in rs]
  detail.append(f'| {b} | {v} | {median(xs):.2f} [{min(xs):.2f}, {max(xs):.2f}] | {median(idle(r)["live_bytes"] for r in rs)/MIB:.2f} | {median(r["peak_rss_bytes"] for r in rs)/MIB:.2f} | {median(wall):.3f} [{min(wall):.3f}, {max(wall):.3f}] | {median(wall)/basewall:.3f} | {median(r["cpu_seconds"] for r in rs)/basecpu:.3f} |')
  if v in policies:
   cold=next(r for r in d['runs'] if r['benchmark']==b and r['variant']==v and r['repetition']==-1);coverage=cold.get('model_coverage') or {};dem=median(sum(s['demotions'] for s in r['allocator_stats'].get('hybrid_sites',{}).values()) for r in rs) if v.endswith('hybrid') else 0
   cost.append(f'| {b} | {v.split(":")[1]} | {median(wall)/basewall:.3f} | {median(r["cpu_seconds"] for r in rs)/basecpu:.3f} | {cold["wall_seconds"]:.2f} | {cold.get("model_seconds",0)+sum(r.get("model_seconds",0) for r in d.get("coverage_runs",[]) if r["benchmark"]==b and r["variant"]==v):.2f} | {coverage.get("asked_sites","n/a")} | '+(f'{1-coverage["unasked_byte_share"]:.2%}' if coverage else 'n/a')+f' | {dem:g} |')
 if d.get('search_steps'):
  search+=['## '+b,'',f'All-transient training median: {d["search_baseline"]/MIB:.2f} MiB.','', '| Site key | Requested MiB | Candidate idle MiB | Kept | Function stack |','|---|---:|---:|---|---|']
  for s in d['search_steps']:search.append(f'| {s["key"]} | {s["bytes"]/MIB:.2f} | {s["candidate_rss"]/MIB:.2f} | {s["accepted"]} | '+ ' → '.join(f.get('function','?').split('\n')[0].replace('|','/') for f in s['frames'])+' |')
  if 'jev-live:static-model' in g:
   trace=[json.loads(line) for line in (p.parent/'trace.jsonl').read_text().splitlines()]
   wanted=set();table_labels={}
   for label in ('oracle','search'):
    table_labels[label]={k:int(v) for k,v in (line.split() for line in (p.parent/'tables'/b/(label+'.txt')).read_text().splitlines())}
    wanted.update(k for k,v in table_labels[label].items() if v==1)
   events={}
   for v in policies[:2]:
    cold=next(r for r in d['runs'] if r['variant']==v and r['repetition']==-1)
    events[v]={e['request']['key']:e for e in map(json.loads,(ROOT/cold['decision_log']).read_text().splitlines()) if e.get('ordinal')==0}
   truth={s['key']:int(s['class_bytes'][1]>s['class_bytes'][0]) for s in trace}
   static=events['jev-live:static-model']
   wrong=[k for k,e in static.items() if e.get('raw_response') and e['response']['class']==1 and truth.get(k)==0]
   accuracy.append(dict(workload=b,asked=len(static),wrong_permanent=len(wrong),wrong_permanent_keys=wrong))
   best_label=min(('oracle','search'),key=lambda label:rss['jev-table:'+label])
   permanent={k for k,v in table_labels[best_label].items() if v==1}
   queried={k for k in permanent if k in static and static[k].get('raw_response')}
   agreed={k for k in queried if static[k]['response']['class']==1}
   table_agreement.append(dict(workload=b,best_table=best_label,permanent_sites=len(permanent),asked=len(queried),agreed_permanent=len(agreed)))
   for s in trace:
    if s['key'] not in wanted:continue
    answers={}
    for v,evs in events.items():
     e=evs.get(s['key']);answers[v]=None if not e else dict(model_backed=bool(e.get('raw_response')),response=e['response'],probabilities=(e.get('raw_response') or {}).get('answers',{}).get('lifetime',{}).get('probabilities'),stack_seen=(e.get('model_request') or {}).get('state'))
    sites_report.append(dict(workload=b,key=s['key'],bytes=s['bytes'],oracle=int(s['class_bytes'][1]>s['class_bytes'][0]),table_labels={label:values.get(s['key'],0) for label,values in table_labels.items()},answers=answers))
for b in regnames:
 cold=next(r for r in regdata['runs'] if r['benchmark']==b and r['variant']=='jev-live:static-model' and r['repetition']==-1)
 truth_path=ROOT/'results/tables'/b/'oracle.txt'
 log=ROOT/cold['decision_log']
 if not (truth_path.exists() and log.exists()):continue
 truth={k:int(v) for k,v in (line.split() for line in truth_path.read_text().splitlines())}
 events=[e for e in map(json.loads,log.read_text().splitlines()) if e.get('raw_response') and e.get('ordinal')==0]
 wrong=[e['request']['key'] for e in events if e['response']['class']==1 and truth.get(e['request']['key'])==0]
 hybrid_runs=reggroups[b,'jev-live:hybrid']
 hybrid_cold=next(r for r in regdata['runs'] if r['benchmark']==b and r['variant']=='jev-live:hybrid' and r['repetition']==-1)
 hybrid_log=ROOT/hybrid_cold['decision_log']
 hybrid_events={e['request']['key']:e for e in map(json.loads,hybrid_log.read_text().splitlines()) if e.get('raw_response') and e.get('ordinal')==0} if hybrid_log.exists() else {}
 shared_wrong={k for k in wrong if k in hybrid_events and hybrid_events[k]['response']['class']==1}
 demoted=median(sum(bool(r['allocator_stats'].get('hybrid_sites',{}).get(k,{}).get('demotions')) for k in shared_wrong) for r in hybrid_runs)
 peak_ratio=median(r['peak_rss_bytes'] for r in hybrid_runs)/median(r['peak_rss_bytes'] for r in reggroups[b,'jev-live:static-model'])
 accuracy.append(dict(workload=b,kind='regression peak',asked=len(events),wrong_permanent=len(wrong),wrong_permanent_keys=wrong,shared_wrong_priors=len(shared_wrong),median_wrong_sites_demoted=demoted,hybrid_static_peak_ratio=peak_ratio))
 for e in events:
  k=e['request']['key']
  if k in wrong:wrong_priors.append(dict(workload=b,key=k,static_response=e['response'],probabilities=e['raw_response'].get('answers',{}).get('lifetime',{}).get('probabilities'),stack_seen=(e.get('model_request') or {}).get('state'),hybrid_response=hybrid_events.get(k,{}).get('response'),hybrid_samples=[r['allocator_stats'].get('hybrid_sites',{}).get(k) for r in hybrid_runs]))
head+=['','### Model decisions on real stacks','']
if table_agreement:
 for a in table_agreement:head.append(f'{a["workload"]}: the best table ({a["best_table"]}) labels {a["permanent_sites"]} sites permanent. The model was asked about {a["asked"]} of them and agreed on {a["agreed_permanent"]}. This is agreement with a table, not proof of optimality; the RSS comparison is the practical outcome.')
else:head.append('No real-program table passed the headroom gate, so the requested rule prevented model evaluation on these stacks.' if sum(not b.startswith('site-pure') for b,*_ in blocks)==7 else 'No eligible real-program model block has been published yet. Code-only model accuracy on these new program stacks has not been measured.')
head+=['','### Wrong permanent priors','','Counts below compare first-sight static-model answers to the prior trace lifetime oracle. They identify candidate corrections; measured RSS determines whether hybrid helped. Regression RSS is peak rather than idle.','']
if accuracy:
 head+=['| Workload | Asked sites | Wrong permanent | Wrong sites demoted in hybrid (median) | Hybrid/static peak RSS |','|---|---:|---:|---:|---:|']
 for a in accuracy:head.append(f'| {a["workload"]} | {a["asked"]} | {a["wrong_permanent"]} | '+(f'{a["median_wrong_sites_demoted"]:g} | {a["hybrid_static_peak_ratio"]:.3f}' if 'median_wrong_sites_demoted' in a else '— | —')+' |')
 head+=['','Demotion counts include only sites with the same wrong permanent prior in hybrid, and may include shutdown. They do not establish that a correction happened before peak RSS. Exact wrong-prior probabilities, stacks and per-run hybrid counters are in [wrong-priors.json](results/pass8/wrong-priors.json).']
else:head.append('No eligible real-program or complete regression model block has been published yet; no claim about wrong priors is made.')
(OUT/'accuracy.json').write_text(json.dumps(accuracy,indent=2))
(OUT/'wrong-priors.json').write_text(json.dumps(wrong_priors,indent=2))
head+=['','Capture = (mi − policy)/(mi − best table), undefined without positive savings. Fragmentation RSS uses the final idle point; site-pure has two cycles. Model timings replay first-sight answers, while hybrid runtime rules execute afresh during each run. No inference is included in warm headline timing. Target-process CPU excludes the model server and, for Redis, the separate client driver; wall time includes the common settle period.','',*cost,'',
'Runtime demotions above include process shutdown and therefore do not by themselves establish a useful wrong-prior correction. Per-site model probabilities and the exact stack state seen are recorded in [site-decisions.json](results/pass8/site-decisions.json). Search candidates and accepted moves, by function stack, are in [search.md](results/pass8/search.md). Full ranges, program memory, peak RSS and costs are in [details.md](results/pass8/details.md).','',
'## Runtime rule and method','',
f'Measured allocator SHA-256: `{testdata.get("library_sha256","unavailable")}`. Full Linux correctness passed for 22 workloads, with separate hybrid integration, stack, fragmentation and final-idle metric tests. Published warm matrices have matching independent audit hashes and zero inference overlap.','',
'First sight is exactly stack-v1/static-model, including a neutral program description and up to 12 function/file/line frames, without source. Admission is 64 KiB of successful requested bytes, budget 1,500. Unknown sites remain transient. Both prior probabilities are logged. All pass-8 model answers reused the shared exact-payload cache, so native HTTP inference time was zero, including coverage fills. This pass does not measure fresh-model inference latency. Cache hits still consume budget. Cold wall time includes stack symbolization and sidecar work, while HTTP inference time is reported separately. A one-shot allocation can still escape next-allocation admission. Byte coverage counts all requested bytes at answered sites, including allocations before the answer; it is not the fraction allocated under a model label. Published live counters and the allocation clock are batched and approximate.','',
'Hybrid demotes when at least 16 samples exist and at least 5% of all sampled requested bytes have been freed. Promotion requires no sampled object ever freed, P(transient)<0.7, oldest live reservoir sample older than half the allocation clock, and clock >=64 MiB. Exact cumulative sampled free totals survive reservoir replacement and thread retirement; ages use a 128-entry reservoir and the batched allocation clock. Checks occur on sampled allocations/frees and first-prior arrival. A class change affects future allocations, not existing objects. Unit tests cover threshold boundaries; allocator integration tests cover sample rates 1 and 64, confident transient retention, ambiguous promotion, and wrong-prior demotion without reasking.','',
'The first Redis Mesh search mistakenly averaged its two idle phases. Its entire search and final gate were rerun using final idle; the superseded pilot is archived under results/pass8/redis-mesh-average-idle/ and excluded here. The other six real workloads have one idle phase and are unaffected.','',
'All fragbench variants set MIMALLOC_PURGE_DELAY=0, MIMALLOC_ARENA_PURGE_MULT=1, MIMALLOC_PURGE_DECOMMITS=1; real-program settle time is 500 ms. SQLite reports sqlite3_memory_used. Redis reports used_memory, including metadata/usable sizes. RocksDB sums its memtable, table-reader and block-cache properties, and LevelDB reports approximate-memory-usage; these two are partial estimates, so RSS/live is not an exact fragmentation factor. Sources and build recipes are pinned in scripts/build-real.sh, with source/binary hashes in results/pass8/builds/. No system packages are installed.','',
'## Regression','',f'{len(regnames)}/22 workloads complete and independently audited. Peak RSS here is a regression metric, not idle fragmentation. Score is inverse throughput for duration-limited workloads, otherwise elapsed time.','',
'| Workload | mi peak MiB | Static peak MiB | Hybrid peak MiB | Heuristic peak MiB | Static score/mi | Hybrid score/mi | Heuristic score/mi |','|---|---:|---:|---:|---:|---:|---:|---:|']
for b in regnames:
 base=median(r['score'] for r in reggroups[b,'mi'])
 values=[median(r['peak_rss_bytes'] for r in reggroups[b,v])/MIB for v in ['mi',*policies]]+[median(r['score'] for r in reggroups[b,v])/base for v in policies]
 head.append('| '+b+' | '+' | '.join(f'{v:.3f}' for v in values)+' |')
head+=['','All 12 regression variants, warm wall/CPU ranges and peak RSS ranges are in [the full regression table](results/pass8/pass8-regression.md). Duration-limited peak-RSS comparisons also change the amount of work completed.','',
'### Regression model cost and coverage','','| Workload | Policy | Cold wall s | Cold+fill HTTP s | Asked sites | Cold byte coverage |','|---|---|---:|---:|---:|---:|']
if regdata:
 for b in regnames:
  for v in policies[:2]:
   r=next(r for r in regdata['runs'] if r['benchmark']==b and r['variant']==v and r['repetition']==-1)
   c=r.get('model_coverage') or {};http=r.get('model_seconds',0)+sum(f.get('model_seconds',0) for f in regdata.get('coverage_runs',[]) if f['benchmark']==b and f['variant']==v)
   coverage=f'{1-c["unasked_byte_share"]:.2%}' if c else 'n/a'
   head.append(f'| {b} | {v.split(":")[1]} | {r["wall_seconds"]:.2f} | {http:.2f} | {c.get("asked_sites",0)} | {coverage} |')
acceptance=OUT/'acceptance.json'
if acceptance.exists():
 head+=['','### Acceptance target misses','','These are diagnostic thresholds, not evidence of statistical significance. All misses remain visible. `none_time` is jev-none/mi score; `none_rss` is jev-none/mi peak RSS; `keyonly_rss` is jev-keyonly/jev-none peak RSS. The inherited `live_time` check is heuristic/oracle score; hybrid costs appear in the regression table above.','', '| Workload | Check | Ratio | Target |','|---|---|---:|---:|']
 for row in read(acceptance)['checks']:
  for metric,target in [('none_time',1.03),('none_rss',1.03),('keyonly_rss',1.03),('live_time',1.15)]:
   if row.get(metric,0)>target:head.append(f'| {row["workload"]} | {metric} | {row[metric]:.3f} | {target:.2f} |')
head+=['','The original pass-7 regression had already completed when pass 8 inspected the remote host. Its raw logs and aggregates were preserved under results/pass7-regression-partial/ with an explanatory archive note. No running matrix needed stopping. Pass-7 results below are historical and use the repeatedly queried `model` policy (now named `model-reask`).','', '## Earlier passes (history)','']
if regnames:
 worst=max(regnames,key=lambda b:median(r['score'] for r in reggroups[b,'jev-live:hybrid'])/median(r['score'] for r in reggroups[b,'mi']))
 ratio=lambda b,v:median(r['score'] for r in reggroups[b,v])/median(r['score'] for r in reggroups[b,'mi'])
 wrong_workloads=sum(a['wrong_permanent']>0 for a in accuracy if a.get('kind')=='regression peak')
 summary=f'Wrong permanent priors occur in {wrong_workloads}/22 regression workloads. Hybrid demotes many, but RSS effects are mixed and allocator overhead remains severe: {worst} costs {ratio(worst,"jev-live:hybrid"):.1f}× mimalloc, versus {ratio(worst,"jev-live:static-model"):.1f}× for static-model. The acceptance targets do not all pass. This is a fix for the site-pure classification regression, with no demonstrated benefit on the seven real-program fragmentation cases.'
 index=head.index('## Idle RSS');head[index:index]=[summary,'']
 if all(b in regnames for b in ('glibc-thread','rptest','mleak100')):
  rss=lambda b,v:median(r['peak_rss_bytes'] for r in reggroups[b,v])/MIB
  example=f'For example, hybrid lowers glibc-thread peak RSS from {rss("glibc-thread","jev-live:static-model"):.2f} to {rss("glibc-thread","jev-live:hybrid"):.2f} MiB, but its inverse-throughput score rises from {ratio("glibc-thread","jev-live:static-model"):.2f}× to {ratio("glibc-thread","jev-live:hybrid"):.2f}× mimalloc. That duration-limited comparison also changes completed work. Rptest peak RSS increases from {rss("rptest","jev-live:static-model"):.2f} to {rss("rptest","jev-live:hybrid"):.2f} MiB. The lower mleak100 median has overlapping five-run ranges. These results do not establish a general RSS benefit from correcting priors.'
  index=head.index('### Wrong permanent priors')+2;head[index:index]=[example,'']
training_audit=OUT/'search-intervals.inference-audit.json'
if training_audit.exists():
 a=read(training_audit)
 assert a['overlapping_runs']==0
 index=head.index('## Runtime rule and method')+2
 head[index:index]=[f'[Final evidence validation](results/pass8/validation.json) recomputes all search decisions and gates and verifies the measured library fingerprints. All {a["checked"]} retained greedy-search trials also pass the [independent inference audit](results/pass8/search-intervals.inference-audit.json).','']
(OUT/'details.md').write_text('\n'.join(detail)+'\n');(OUT/'search.md').write_text('\n'.join(search)+'\n');(OUT/'site-decisions.json').write_text(json.dumps(sites_report,indent=2))
(ROOT/'RESULTS.md').write_text('\n'.join(head)+(OUT/'history.md').read_text())
print(f'Published {len(blocks)} fragmentation blocks and {len(regnames)} regression workloads')
