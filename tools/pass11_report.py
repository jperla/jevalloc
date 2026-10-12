#!/usr/bin/env python3
"""Recompute pass-11 tables and paired intervals from individual observations."""
import hashlib,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/pass11';MIB=1048576
def stats(xs):return dict(median=statistics.median(xs),min=min(xs),max=max(xs))
def idle(r,phase='idle'):return max((p for p in r['phases'] if p['phase']==phase),key=lambda p:p.get('cycle',0))['rss_bytes']
def interval(xs):
 rng=random.Random(110011);values=sorted(statistics.median(rng.choices(xs,k=len(xs))) for _ in range(20000))
 def quantile(p):
  i=(len(values)-1)*p;lo=int(i);return values[lo]+(values[min(lo+1,len(values)-1)]-values[lo])*(i-lo)
 return dict(median=statistics.median(xs),low=quantile(.025),high=quantile(.975),paired_differences=xs)
def fmt(s,scale=1):return f"{s['median']/scale:.3f} [{s['min']/scale:.3f}, {s['max']/scale:.3f}]"
def audited(path,data):
 audit_path=path.with_suffix('.inference-audit.json')
 if not data.get('complete') or not audit_path.exists():return False
 audit=json.loads(audit_path.read_text())
 return audit['overlapping_runs']==0 and audit['matrix_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 report=['# Pass 11 — review 3','','All statuses below describe artifacts present in this working tree. Full design and all mapping/order seeds were frozen in CODEX-REPORT.md before inference. No Git commit is implied.','']
 cells=[];comparisons=[];redis=[];transitions=[];complete=0;total=0
 for path in sorted((BASE/'factorial').glob('*/*/*/matrix.json')):
  d=json.loads(path.read_text());parts=path.relative_to(BASE).parts;naming,workload,threads=parts[1:4]
  if not audited(path,d):total+=len(d['runs']);continue
  complete+=1;total+=len(d['runs']);groups={v:sorted([r for r in d['runs'] if r['variant']==v],key=lambda r:r['repetition']) for v in d['configuration']['variants']}
  for v,rs in groups.items():
   assert len(rs)==10 and [r['repetition'] for r in rs]==list(range(10))
   promotions=[sum(s['promotions'] for s in r.get('allocator_stats',{}).get('hybrid_sites',{}).values()) for r in rs]
   cells.append(dict(naming=naming,workload=workload,threads=int(threads),variant=v,idle=stats([idle(r) for r in rs]),idle10=stats([idle(r,'idle10') for r in rs]),cpu=stats([r['cpu_seconds'] for r in rs]),promotions=stats(promotions)))
   for r in rs:
    for key,events in r.get('allocator_stats',{}).get('transitions',{}).items():transitions.append(dict(naming=naming,workload=workload,threads=int(threads),variant=v,repetition=r['repetition'],key=key,**events))
  for gate in ('0.6','0.7','0.8'):
   row=dict(naming=naming,workload=workload,threads=int(threads),gate=gate)
   for control in ('rule','neutral','mi'):
    variant='mi' if control=='mi' else control+'-'+gate
    row[control]=interval([(idle(a)-idle(b))/MIB for a,b in zip(groups['model-'+gate],groups[variant])])
   comparisons.append(row)
 report += [f'Factorial: **{complete}/24 blocks complete**, {total}/2400 warm records present. Incomplete blocks remain pending and do not enter comparisons.','',
 'Per cell, idle RSS and promotions are medians [min, max] over ten randomized repetitions. Both cycles, 10-second observations, target CPU, and exact per-site transition clocks/times remain in each matrix. Model/neutral/rule use the same replay transport; only the controlled prior and induced initial class differ. Cold inference and probes are excluded.','',
 '| Naming | Workload | Threads | Policy / gate | Idle MiB [range] | Promotions [range] |','|---|---|---:|---|---:|---:|']
 for c in cells:report.append(f"| {c['naming']} | {c['workload']} | {c['threads']} | {c['variant']} | {fmt(c['idle'],MIB)} | {fmt(c['promotions'])} |")
 report+=['','Paired effect is median(model − control), MiB; negative favors model. Intervals resample paired repetition blocks, 20000 draws, percentile 95%, seed 110011. These intervals describe repeated runs of fixed priors, not variation across model draws or real applications.','',
 '| Naming | Workload | Threads | Gate | Model − rule [95% interval] | Model − neutral [95% interval] | Model − mi [95% interval] |','|---|---|---:|---:|---:|---:|---:|']
 for c in comparisons:
  ef=lambda s:f"{s['median']:.3f} [{s['low']:.3f}, {s['high']:.3f}]"
  report.append(f"| {c['naming']} | {c['workload']} | {c['threads']} | {c['gate']} | {ef(c['rule'])} | {ef(c['neutral'])} | {ef(c['mi'])} |")
 counts=[]
 report+=['','Counts are per gate/workload/thread across six namings. A descriptive win requires both paired medians below zero; an interval-supported win requires both upper bounds below zero. Pending namings are never counted as losses.','',
 '| Gate | Workload | Threads | Available / 6 | Beat both, medians | Beat both, intervals | Worse than mi, median |','|---|---|---:|---:|---:|---:|---:|']
 for gate in ('0.6','0.7','0.8'):
  for workload in ('site-pure','site-mixed'):
   for threads in (1,16):
    rs=[r for r in comparisons if (r['gate'],r['workload'],r['threads'])==(gate,workload,threads)]
    c=dict(gate=gate,workload=workload,threads=threads,available=len(rs),beat_both=sum(r['rule']['median']<0 and r['neutral']['median']<0 for r in rs),beat_both_intervals=sum(r['rule']['high']<0 and r['neutral']['high']<0 for r in rs),worse_mi=sum(r['mi']['median']>0 for r in rs));counts.append(c)
    report.append(f"| {gate} | {workload} | {threads} | {len(rs)}/6 | {c['beat_both']} | {c['beat_both_intervals']} | {c['worse_mi']} |")
 for gate in ('0.6','0.7','0.8'):
  names={r['naming'] for r in comparisons if r['gate']==gate};allwin=[]
  for name in names:
   rs=[r for r in comparisons if r['gate']==gate and r['naming']==name]
   if len(rs)==4 and all(r['rule']['median']<0 and r['neutral']['median']<0 for r in rs):allwin.append(name)
  report.append(f'\nAt gate {gate}, namings beating both controls in all four workload/thread conditions: {len(allwin)}/6 ({", ".join(sorted(allwin)) or "none yet"}).')
 report+=['','Per-site promotions/demotions, identities, monotonic nanoseconds, and allocation-byte clocks are in [transitions.json](transitions.json), with name/context keys in each `priors.json`. Events beyond the first 32 per site are explicitly counted; no truncated sequences are treated as complete.','']
 done=0
 for path in sorted((BASE/'redis').glob('*/*/matrix.json')):
  d=json.loads(path.read_text());parts=path.relative_to(BASE).parts;naming,options=parts[1:3]
  if not audited(path,d):continue
  done+=1
  for v in d['configuration']['variants']:
   rs=[r for r in d['runs'] if r['variant']==v];assert len(rs)==5
   metadata=[r.get('allocator_stats',{}).get('metadata',{}) for r in rs]
   redis.append(dict(naming=naming,options=options,variant=v,idle=stats([idle(r) for r in rs]),cpu=stats([r['cpu_seconds'] for r in rs]),metadata_peak=stats([m.get('peak_bytes',0) for m in metadata]),pairs=stats([m.get('pairs',0) for m in metadata]),overflow=stats([m.get('overflow_allocations',0) for m in metadata]),overflow_bytes=stats([m.get('overflow_bytes',0) for m in metadata])))
 report += [f'Redis: **{done}/4 blocks complete**. Five repetitions per policy; idle RSS/target CPU and metadata reservations below. Target CPU excludes the sidecar. Metadata is raw reserved structure/index/sample storage, excludes allocator rounding, fixed arrays (reported in matrices), and general thread stack caches; it is not an RSS decomposition. Overflow uses the default class. A zero metadata value for mi/key-only means live instrumentation is absent.','',
 '| Context | Options | Policy | Idle MiB [range] | Target CPU s [range] | Metadata peak MiB [range] | Pairs [range] | Overflow allocations [range] | Overflow requested MiB [range] |','|---|---|---|---:|---:|---:|---:|---:|---:|']
 for r in redis:report.append(f"| {r['naming']} | {r['options']} | {r['variant']} | {fmt(r['idle'],MIB)} | {fmt(r['cpu'])} | {fmt(r['metadata_peak'],MIB)} | {fmt(r['pairs'])} | {fmt(r['overflow'])} | {fmt(r['overflow_bytes'],MIB)} |")
 diag=[]
 report+=['','Purge diagnostic (separate MI_STAT=2 build, one run per policy/options/collection mode; not performance estimates). Both option sets use identical two-cycle and ten-second histories. Heap-area traversal may collect delayed frees. Default-heap collection and subsequent tagged-heap collection are distinct observations. Negative signed committed values are retained as reported but are invalid absolute memory estimates. Committed/reserved counters include sparsely touched arenas and are not RSS; cumulative purge totals are not a resident-byte decomposition.','',
 '| Options | Policy | Cycle | Phase | RSS MiB | Committed MiB | Reserved MiB | Purged cumulative MiB | Live block MiB | Area committed MiB | Empty-area committed MiB |','|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
 for path in sorted((BASE/'diagnostic').glob('*/matrix.json')):
  d=json.loads(path.read_text())
  if not audited(path,d):continue
  for r in d['runs']:
   for phase in r['phases']:
    stat=next(s for s in r['allocator_phases'] if (s['cycle'],s['mi_phase'])==(phase['cycle'],phase['phase']))
    diag.append(dict(options=path.parent.name,variant=r['variant'],phase=phase,statistics=stat))
    report.append(f"| {path.parent.name} | {r['variant']} | {phase['cycle']} | {phase['phase']} | {phase['rss_bytes']/MIB:.3f} | {stat['committed']/MIB:.3f} | {stat['reserved']/MIB:.3f} | {stat['purged']/MIB:.3f} | {stat['area_used']/MIB:.3f} | {stat['area_committed']/MIB:.3f} | {stat['empty_area_committed']/MIB:.3f} |")
 if not diag:report+=['','Diagnostic artifacts: pending.']
 summary=dict(factorial_complete=complete,redis_complete=done,cells=cells,paired_comparisons=comparisons,counts=counts,redis=redis,diagnostic=diag)
 promotion_lines=['# Transition identities and allocation-clock timing','','Each row groups recorded transitions by naming/workload/thread/policy/site/destination class. Clock MiB is cumulative sampled-policy allocation-byte time, not wall time or elapsed seconds. Absolute monotonic nanoseconds and repetition identities remain in transitions.json. A destination of 1 is promotion; 0 is demotion. Counts span all ten repetitions.','', '| Naming | Workload | Threads | Policy / gate | Site / context | Destination | Events | Clock MiB median [range] |','|---|---|---:|---|---|---:|---:|---:|']
 grouped={}
 for t in transitions:
  for event in t['events']:
   key=(t['naming'],t['workload'],t['threads'],t['variant'],t['key'],event['class'])
   grouped.setdefault(key,[]).append(event['allocation_clock'])
 mappings={m['name']:set(m['functions'].values()) for m in json.loads((BASE/'design.json').read_text())['mappings']}
 for (n,w,th,v,k,cls),values in sorted(grouped.items()):
  priors=json.loads((BASE/'factorial'/n/w/'priors.json').read_text());prior=next(p for p in priors if p['key']==k)
  funcs=[f.get('function','?') for f in prior['frames'] if f.get('function') in mappings[n]]
  label=(funcs[0] if funcs else k)+' / '+(prior['context'] or '(empty)')+' / '+k
  promotion_lines.append(f'| {n} | {w} | {th} | {v} | {label} | {cls} | {len(values)} | {fmt(stats(values),MIB)} |')
 (BASE/'promotions.md').write_text('\n'.join(promotion_lines)+'\n')
 report+=['','See [promotion identities and timing](promotions.md) for per-site event counts and allocation-clock medians/ranges.']
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(BASE/'transitions.json').write_text(json.dumps(transitions,indent=2)+'\n')
 (BASE/'results.md').write_text('\n'.join(report)+'\n')
 print(f'Factorial {complete}/24; Redis {done}/4; diagnostic phases {len(diag)}')
if __name__=='__main__':main()
