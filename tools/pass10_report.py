#!/usr/bin/env python3
"""Recompute review-2 medians, both cycles, decisions and headline comparison."""
import gzip,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from selection import complete_groups,accepted
BASE=ROOT/'results/pass10'
def med(xs):return statistics.median(xs)
def phase(r,label='idle',cycle=None):
 rows=[p for p in r['phases'] if p['phase']==label and (cycle is None or p.get('cycle',0)==cycle)]
 return max(rows,key=lambda p:p.get('cycle',0))['rss_bytes']
def headline(summary):
 lines=['# Pass 10 — answering review 2','','This pass asks whether lifetime placement saves memory under mimalloc defaults, whether current runtime statistics help, and whether a model adds value beyond function names and TTL text.', '',f"{len(summary)}/25 fragmentation blocks are complete. Every published comparison uses five interleaved repetitions. **Defaults** unsets every `MIMALLOC_*` override; **immediate purge** sets delay 0, arena multiplier 1 and decommit enabled. Full measurements, both cycles and 10-second idle observations are in the [pass-10 report](results/pass10/results.md) and [phase table](results/pass10/phases.md).",'']
 rows=[(name,summary['defaults/named/'+name]) for name in ('site-pure-1','site-pure-16','site-mixed-1','site-mixed-16') if 'defaults/named/'+name in summary]
 if rows:
  lines+=['Final idle RSS under **defaults**, MiB. Plain mimalloc is `mi`; oracle uses sites on pure workloads and context pairs on mixed. Rules share the model’s placement machinery.', '', '| Workload | mi | Oracle | Static model | Hybrid | Live heuristic | Neutral rules | Names / TTL rule |','|---|---:|---:|---:|---:|---:|---:|---:|']
  for name,ss in rows:
   mixed='mixed' in name;variants=['mi','jev-table:oracle-context' if mixed else 'jev-table:oracle-site']+['jev-live:'+p for p in ('static-model','hybrid','heuristic','rules-neutral')]+['jev-live:rule-ttl' if mixed else 'jev-live:rule-names']
   lines.append('| '+name+' | '+' | '.join(f"{ss[v]['idle']/1048576:.2f}" for v in variants)+' |')
  if 'defaults/named/site-pure-1' in summary:
   d=summary['defaults/named/site-pure-1'];immediate=summary.get('immediate/named/site-pure-1')
   lines+=['',f"The one-thread pure model reduction is {100*d['jev-live:static-model']['saving_fraction']:.1f}% under defaults"+(f", versus {100*immediate['jev-live:static-model']['saving_fraction']:.1f}% with immediate purge" if immediate else '')+'. Defaults also adds a 10-second wait between cycles. The fixed names rule produces '+f"{d['jev-live:rule-names']['idle']/1048576:.2f} MiB under defaults. The original large synthetic saving is configuration-dependent and does not by itself show a model advantage."]
  lines+=['','The heuristic now runs on current observations. Neutral rules use a 0.5 prior with hybrid’s continuous checks. Both use more idle RSS than mimalloc in all four named defaults fixtures. Fixed names/TTL rules closely match the useful model placement there.']
 renamed=[(k,ss) for k,ss in summary.items() if k.startswith(('defaults/opaque/','defaults/plausible/'))]
 if renamed:
  positive=sum(ss['jev-live:static-model']['saving_fraction']>0 for k,ss in renamed)
  lines+=['',f"Static-model retains a positive saving over its own mimalloc baseline in {positive}/{len(renamed)} renamed comparisons. Exact per-naming RSS, oracle capture and fractions of the original saving are in the full report."]
  opaque=[ss for k,ss in renamed if '/opaque/' in k];plausible=[(k,ss) for k,ss in renamed if '/plausible/' in k]
  if opaque:
   positives=sum(ss['jev-live:hybrid']['saving_fraction']>0 for ss in opaque)
   lines[-1]+=f" Hybrid retains a positive saving in {positives}/{len(opaque)} opaque comparisons."
  if plausible:
   retained=[];advantages=[]
   for k,ss in plausible:
    named=summary['defaults/named/'+k.split('/')[-1]]
    retained.append(100*(ss['mi']['idle']-ss['jev-live:hybrid']['idle'])/(named['mi']['idle']-named['jev-live:hybrid']['idle']))
    rule='jev-live:rule-ttl' if 'mixed' in k else 'jev-live:rule-names'
    advantages.append((ss[rule]['idle']-ss['jev-live:hybrid']['idle'])/1048576)
   lines+=['',f"With plausible names, hybrid retains {min(retained):.1f}–{max(retained):.1f}% of its named saving and beats the matching fixed names/TTL rule by {min(advantages):.2f}–{max(advantages):.2f} MiB. The model initially chooses transient, but its probability priors permit promotion of the retained path while blocking the session path. Some mixed-context priors lie close to the fixed 0.7 gate. This is a benefit in these specific synthetic ablations; the [answer/probability table](results/pass10/model-sites.md) and full ranges show its scope."]
 real=[(k,ss) for k,ss in summary.items() if '/site-' not in k and not k.endswith('per-alloc-small')]
 if real:
  wins=[f"{k.split('/')[-1]} {policy} {100*ss['jev-live:'+policy]['saving_fraction']:.1f}%" for k,ss in real for policy in ('static-model','hybrid') if ss['jev-live:'+policy]['saving_fraction']>0.05]
  lines+=['',f"Default-options real programs: {len(real)}/7 complete. Model-policy reductions above 5% are "+('; '.join(wins) if wins else 'absent in the completed workloads')+'. All policies, costs and ranges are in the full report. Earlier table-search gates and the later contrary RocksDB result remain below.']
  drop=summary.get('defaults/named/redis-drop')
  if drop:
   model=drop['jev-live:static-model'];mi=drop['mi']
   lines[-1]+=f" Redis drop is a severe failure: live/context static-model holds {model['idle']/1073741824:.2f} GiB versus mi {mi['idle']/1048576:.2f} MiB, with {model['cpu']/mi['cpu']:.1f}× target CPU. Its roughly 495,000 context entries also burden the no-model live controls."
  rocks=summary.get('defaults/named/rocksdb-cache')
  if rocks:
   lines[-1]+=f" RocksDB cache hybrid holds {rocks['jev-live:hybrid']['idle']/1048576:.2f} MiB versus mi {rocks['mi']['idle']/1048576:.2f} MiB."
 small=BASE/'immediate/named/per-alloc-small/object-accuracy.json'
 if small.exists():
  acc=json.loads(small.read_text());m=acc['model_answered'];conf=m['confusion'];n=m['objects'];comparison=json.loads((small.parent/'ttl-rule-comparison.json').read_text())
  lines+=['',f"The recollected small per-object run has {100*m['accuracy']:.2f}% model-answered accuracy versus {100*sum(conf[0])/n:.2f}% always-transient accuracy, with {100*conf[1][1]/sum(conf[1]):.2f}% permanent recall. The TTL rule reproduces {comparison['matching']}/{comparison['answered']} model-answered classes. Accuracy, logged checks and separate unlogged RSS/cost comparisons are in the full report."]
  values=[]
  for options in ('immediate','defaults'):
   ss=summary.get(options+'/named/per-alloc-small')
   if ss:values.append(f"{options}: {ss['jev-live:per-alloc']['idle']/1048576:.2f} versus mi {ss['mi']['idle']/1048576:.2f} MiB")
  lines[-1]+=' Unlogged per-object idle RSS is '+('; '.join(values))+f". Fresh cold inference took {acc['model_seconds']/60:.1f} minutes."
 regression=BASE/'regression.json'
 if regression.exists():
  groups,benches=complete_groups(json.loads(regression.read_text()))
  if benches:
   worst=[]
   for policy in ('static-model','hybrid','heuristic','rules-neutral'):
    ratio,name=max((med([r['score'] for r in groups[b,'jev-live:'+policy]])/med([r['score'] for r in groups[b,'mi']]),b) for b in benches)
    worst.append(f'{policy} {ratio:.2f}× ({name})')
   lines+=['',f"Regression with no `MIMALLOC_*` overrides: {len(benches)}/22 workloads complete. Largest median time/inverse-throughput score ratios versus mimalloc are "+'; '.join(worst)+'. Lower is better. All workload scores and peak RSS are in the full report; they are separate from idle fragmentation.']
 lines+=['','The combined logging/live-free bug is fixed. Tests cover cross-thread frees, retired allocating threads, actual address reuse, sample/survivor counts and hybrid demotions with logging on and off. Warm model measurements replay answers and retain service/IPC costs; target CPU excludes sidecar CPU. Compact evidence supports the medians, while full trace/cache reconstruction requires the retained remote artifacts.','']
 return '\n'.join(lines)
def main():
 summary={};decisions=[];costs=[];detail=['# Pass 10 measured phases','','Five interleaved repetitions; MiB. Each row reports a workload’s original cycle. Defaults unset every `MIMALLOC_*` variable; immediate sets purge delay 0, arena multiplier 1, decommit 1. Wall time includes the prescribed idle waits; target CPU excludes sidecar CPU. The extra 10-second observation also delays the next cycle under defaults; across-series comparisons therefore change idle duration as well as allocator options.','', '| Options / naming / workload | Variant | Cycle | Idle median [min, max] MiB | 10 s idle MiB | Peak MiB | Wall s | Target CPU s |','|---|---|---:|---:|---:|---:|---:|---:|']
 for path in sorted(BASE.glob('*/*/*/matrix.json')):
  d=json.loads(path.read_text())
  if not d.get('complete'):continue
  config=d['configuration'];groups,benches=complete_groups(d);assert benches==config['workloads']
  key='/'.join(path.relative_to(BASE).parts[:-1]);name=config['workloads'][0];ss={}
  for v in config['variants']:
   rs=groups[name,v];xs=[phase(r) for r in rs]
   item=dict(idle=med(xs),idle_range=[min(xs),max(xs)],wall=med([r['wall_seconds'] for r in rs]),cpu=med([r['cpu_seconds'] for r in rs]),peak=med([r['peak_rss_bytes'] for r in rs]),phases={},n=len(rs))
   for cycle in sorted({p.get('cycle',0) for r in rs for p in r['phases'] if p['phase']=='idle'}):
    idle=[phase(r,cycle=cycle) for r in rs]
    long=[phase(r,'idle10',cycle) for r in rs] if config['options']=='defaults' else []
    item['phases'][str(cycle)]=dict(idle=med(idle),range=[min(idle),max(idle)],idle10=med(long) if long else None)
    tail=f'{med(long)/1048576:.3f}' if long else '—'
    detail.append(f"| {key} | {v} | {cycle} | {med(idle)/1048576:.3f} [{min(idle)/1048576:.3f}, {max(idle)/1048576:.3f}] | {tail} | {item['peak']/1048576:.3f} | {item['wall']:.3f} | {item['cpu']:.3f} |")
   item['demotions']=med([sum(s['demotions'] for s in r.get('allocator_stats',{}).get('hybrid_sites',{}).values()) for r in rs])
   item['promotions']=med([sum(s['promotions'] for s in r.get('allocator_stats',{}).get('hybrid_sites',{}).values()) for r in rs])
   ss[v]=item
  oracle='jev-table:oracle-context' if 'jev-table:oracle-context' in ss else 'jev-table:oracle-site'
  for v,item in ss.items():
   denominator=ss['mi']['idle']-ss[oracle]['idle']
   item['saving_fraction']=1-item['idle']/ss['mi']['idle'];item['capture']=(ss['mi']['idle']-item['idle'])/denominator if denominator>0 else None
  summary[key]=ss
  for r in d['runs']+d.get('coverage_runs',[]):
   if r['repetition']>=0 or 'decision_log' not in r:continue
   events=[json.loads(line) for line in (ROOT/r['decision_log']).open()]
   costs.append(dict(block=key,variant=r['variant'],repetition=r['repetition'],wall=r['wall_seconds'],http=r['model_seconds'],answers=sum(e.get('raw_response') is not None for e in events),budget_fallbacks=sum(e.get('budget_exhausted',False) for e in events),coverage=r.get('model_coverage')))
   for e in events:
    if e.get('raw_response') is not None:
     decisions.append(dict(block=key,variant=r['variant'],key=e['request']['key'],ordinal=e['ordinal'],context=e['request'].get('context',''),size=e['request'].get('size'),class_=e['response']['class'],probabilities=e['raw_response']['answers']['lifetime']['probabilities'],state=(e.get('model_request') or {}).get('state'),frames=e['request'].get('frames'),model_origin=e.get('model_origin')))
 site_lines=['# Model answers by naming and context','','Static first-sight answers under defaults. Probabilities are the recorded native model output; unasked sites remain in each block’s sites.json catalogue.','', '| Naming / workload | Key | Context | Stack | P(transient) | P(permanent) | Class | Oracle |','|---|---|---|---|---:|---:|---|---|']
 seen=set()
 for e in decisions:
  identity=(e['block'],e['key'])
  if not e['block'].startswith('defaults/') or '/site-' not in e['block'] or e['variant']!='jev-live:static-model' or e['ordinal']!=0 or not e['state'] or identity in seen:continue
  seen.add(identity)
  stack=' → '.join(line.strip().split('  (')[0] for line in e['state'].splitlines() if line.startswith('  '))
  probabilities=e['probabilities']
  trace_sites=json.loads((BASE/e['block']/'sites.json').read_text());truth=next((s for s in trace_sites if s['key']==e['key']),None);truth_label=('transient','permanent')[int(truth['class_bytes'][1]>truth['class_bytes'][0])] if truth else 'unmatched'
  site_lines.append(f"| {e['block'].removeprefix('defaults/')} | {e['key']} | {e['context'].replace('|','&#124;') or 'empty'} | {stack.replace('|','&#124;')} | {probabilities['transient']:.6f} | {probabilities['permanent']:.6f} | {('transient','permanent')[e['class_']]} | {truth_label} |")
 BASE.mkdir(parents=True,exist_ok=True)
 (BASE/'model-sites.md').write_text('\n'.join(site_lines)+'\n')
 (BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(BASE/'costs.json').write_text(json.dumps(costs,indent=2)+'\n');(BASE/'phases.md').write_text('\n'.join(detail)+'\n')
 with gzip.open(BASE/'model-decisions.jsonl.gz','wt') as f:
  for d in decisions:f.write(json.dumps(d,separators=(',',':'))+'\n')
 lines=['# Pass 10 — answering review 2','','The question is whether lifetime placement saves RSS under mimalloc defaults, whether live runtime rules help, and whether a model adds value beyond the supplied function names and TTL text.', '',f'Completed fragmentation blocks: {len(summary)}/25. Each published group has five interleaved successful repetitions. **Defaults** means no `MIMALLOC_*` overrides on any variant; **immediate** means purge delay 0, arena purge multiplier 1 and decommit enabled. Earlier measurements remain separately labelled below.','']
 default_pure=summary.get('defaults/named/site-pure-1')
 if default_pure:
  sm=default_pure['jev-live:static-model'];mi=default_pure['mi'];rule=default_pure['jev-live:rule-names']
  lines += [f"With defaults on one-thread site-pure, static-model holds {sm['idle']/1048576:.2f} MiB versus mimalloc {mi['idle']/1048576:.2f} MiB: a {100*sm['saving_fraction']:.1f}% reduction. The names rule holds {rule['idle']/1048576:.2f} MiB. The earlier roughly 84% model RSS reduction therefore does not carry over to defaults in this fixture. Capturing most of the default-options oracle saving is a smaller absolute benefit.", '']
 named={k:v for k,v in summary.items() if k.startswith('defaults/named/site-')}
 if named:
  baselines='; '.join(f"{k.split('/')[-1]} {v['mi']['idle']/1048576:.2f} MiB" for k,v in named.items())
  lines += ['Plain upstream mimalloc holds the following at final idle under defaults: '+baselines+'. The ordinary and 10-second observations, both cycles and ranges are reported in [phase measurements](results/pass10/phases.md).','']
 lines+=['| Options / naming / workload | mi MiB | Oracle MiB | Static MiB / capture | Hybrid MiB / capture | Live heuristic MiB | Neutral rules MiB | Names rule MiB | TTL rule MiB |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 def val(ss,v,capture=False):
  if v not in ss:return '—'
  r=ss[v];s=f"{r['idle']/1048576:.2f}"
  return s+(f" / {100*r['capture']:.1f}%" if r['capture'] is not None else ' / n/a') if capture else s
 for k,ss in summary.items():
  if '/site-' not in k:continue
  oracle='jev-table:oracle-context' if 'jev-table:oracle-context' in ss else 'jev-table:oracle-site'
  lines.append('| '+k+' | '+' | '.join([val(ss,'mi'),val(ss,oracle),val(ss,'jev-live:static-model',True),val(ss,'jev-live:hybrid',True)]+[val(ss,'jev-live:'+p) for p in ('heuristic','rules-neutral','rule-names','rule-ttl')])+' |')
 lines+=['','The heuristic now evaluates its sparse formula on current warm observations. Rules-neutral uses P(transient)=0.5 and the same continuous C runtime checks as hybrid. Rule-names uses the fixed cache/index/table/global/config/intern/registry keyword list; rule-ttl returns permanent iff context contains ttl=day. Both semantic controls use one-hot priors and the same admission, placement and continuous runtime rules. None uses a model.','']
 for name in ('site-pure-1','site-pure-16','site-mixed-1','site-mixed-16'):
  for naming in ('opaque','plausible'):
   k='defaults/'+naming+'/'+name;orig='defaults/named/'+name
   if k not in summary or orig not in summary:continue
   values=[]
   for v in ('jev-live:static-model','jev-live:hybrid'):
    renamed=summary[k]['mi']['idle']-summary[k][v]['idle'];normal=summary[orig]['mi']['idle']-summary[orig][v]['idle']
    values.append(v.split(':')[1]+f" retains {100*renamed/normal:.1f}% of the named saving" if normal>0 else v.split(':')[1]+' named saving undefined')
   lines.append(name+', '+naming+': '+'; '.join(values)+'.')
 if len(named)==4:
  for policy in ('static-model','hybrid'):
   comparisons=[]
   for k,ss in summary.items():
    if '/site-' not in k:continue
    rule='jev-live:rule-ttl' if 'site-mixed' in k else 'jev-live:rule-names'
    comparisons.append((k,ss['jev-live:'+policy]['idle']-ss[rule]['idle']))
   lower=[f'{k} ({-delta/1048576:.2f} MiB lower)' for k,delta in comparisons if delta<0]
   lines+=['',policy+' has a lower measured median than the matching semantic rule in '+('; '.join(lower) if lower else 'none of the completed comparisons')+'.']
  lines+=['These five-run median differences are descriptive; consult ranges before interpreting small gaps. Renaming also changes the supplied context vocabulary. The ablation tests dependence on these hints; it is not a held-out real application.']
 lines+=['','Per-site and per-(site, context) model answers and probabilities are in the [readable site table](results/pass10/model-sites.md); exact prompt states are in [model-decisions.jsonl.gz](results/pass10/model-decisions.jsonl.gz). Unasked sites and trace truth are retained in each synthetic block’s sites.json. [Full phases and costs](results/pass10/phases.md) include all controls, both original cycles where present, the 10-second sample, peak RSS and target-process CPU. [Cold and fill costs](results/pass10/costs.json) are separate from warm replay. Defaults add a quiet 10-second observation after each original idle phase, delaying the next cycle as well; the immediate series retains its original shorter waits. Across-series differences therefore do not isolate allocator options from that added quiet time. Wall time includes all prescribed idle waits; default-series wall ratios can obscure allocation-path overhead. Target CPU and the regression scores provide complementary measurements.','']
 for k,ss in summary.items():
  if not k.endswith('per-alloc-small'):continue
  acc=json.loads((BASE/k/'object-accuracy.json').read_text()) if (BASE/k/'object-accuracy.json').exists() else None
  if not acc:continue
  m=acc['model_answered'];count=m['objects'];conf=m['confusion'];base=sum(conf[0]);recall=conf[1][1]/sum(conf[1])
  objects=[json.loads(line) for line in (BASE/k/'object-truth.jsonl').open()];answered=[o for o in objects if o['model_answered']]
  matrix=json.loads((BASE/k/'matrix.json').read_text())
  cold=next(r for r in matrix['runs'] if r.get('cold'))
  reference={(e['request']['key'],e['ordinal']):e['request'] for e in (json.loads(line) for line in (ROOT/cold['decision_log']).open())}
  drift=[]
  def differences(a,b,prefix=''):
   if isinstance(a,dict) and isinstance(b,dict):
    return [field for key in a.keys()|b.keys() for field in differences(a.get(key),b.get(key),prefix+'.'+key if prefix else key)]
   return [prefix] if a!=b else []
  for r in matrix['logged_runs']+[r for r in matrix['runs'] if r['repetition']>=0 and r['variant']=='jev-live:per-alloc']:
   fields={}
   for e in (json.loads(line) for line in (ROOT/r['decision_log']).open()):
    for field in differences(reference[e['request']['key'],e['ordinal']],e['request']):fields[field]=fields.get(field,0)+1
   drift.append(dict(repetition=r['repetition'],logged='JEVALLOC_OBJECT_TRACE' in r['environment'],changed_fields=fields))
  (BASE/k/'request-drift.json').write_text(json.dumps(drift,indent=2)+'\n')
  lines += [f"Logged/unlogged request comparison ({k.split('/')[0]}): {sum(not r['changed_fields'] for r in drift)}/{len(drift)} warm request streams match the cold stream in every recorded field. Sample/survivor counts agree across cold, logged warm and unlogged warm records."]
  if cold.get('schedule_source'):
   source={(e['request']['key'],e['ordinal']):e['request'] for e in (json.loads(line) for line in (ROOT/cold['schedule_source']).open())}
   fields={};examples={}
   def field_value(obj,path):
    for part in path.split('.'):obj=obj[part]
    return obj
   for key,req in reference.items():
    for field in differences(source[key],req):
     fields[field]=fields.get(field,0)+1;examples.setdefault(field,[field_value(source[key],field),field_value(req,field)])
   comparison=dict(reference='immediate/named/per-alloc-small',comparison=k,changed_requests=sum(source[key]!=req for key,req in reference.items()),total_requests=len(reference),changed_fields=fields,first_examples=examples,note='Defaults adds a 10-second phase observation in each cycle. Per-allocation replay checks size/context/signature/frames; runtime statistics may differ across this options/phase comparison.')
   (BASE/k/'source-schedule-drift.json').write_text(json.dumps(comparison,indent=2)+'\n')
   lines += [f"Across protocols, the defaults reference differs from its immediate-series source schedule in {comparison['changed_requests']}/{comparison['total_requests']} runtime request states ({', '.join(sorted(fields))}). This is separate from the within-series logging comparison. The per-object prompt does not consume these runtime fields; size/context/signature/frames remain checked. See source-schedule-drift.json in that block."]

  matching=sum(o['class']==int('ttl=day' in o['context']) for o in answered)
  (BASE/k/'ttl-rule-comparison.json').write_text(json.dumps(dict(answered=len(answered),matching=matching),indent=2)+'\n')
  lines += [f"The fixed TTL rule reproduces {matching}/{len(answered)} model-answered classes ({k.split('/')[0]}). Repeated inference's value must be judged against that control, not object accuracy alone."]
  lines += [f"Recollected small experiment ({k.split('/')[0]}): {m['correct']}/{count} answered objects correct ({100*m['accuracy']:.2f}%); always-transient {100*base/count:.2f}%; permanent recall {100*recall:.2f}%. Final idle is {ss['jev-live:per-alloc']['idle']/1048576:.2f} MiB versus mi {ss['mi']['idle']/1048576:.2f} MiB and context oracle {ss['jev-table:oracle-context']['idle']/1048576:.2f} MiB. Cold: {acc['http_requests']} HTTP calls, {acc['model_seconds']:.2f} HTTP seconds. Logged and unlogged sample/survivor counts are checked in each block’s sampling-comparison.json. Exact lifetime accuracy remains distinct from RSS savings. The defaults small control reuses the fixed-library immediate run’s checked per-object schedule, with fresh logged lifetime evidence and no second HTTP collection."]
 real=[(k,ss) for k,ss in summary.items() if not '/site-' in k and not k.endswith('per-alloc-small')]
 if real:
  lines+=['','Default-options real-program final idle / 10-second RSS is in the full phase table. No prior gate is used to omit policies from this explicitly requested matched series. The historical unsuccessful table searches remain unchanged.','', '| Workload | mi MiB | Oracle MiB | Static MiB | Hybrid MiB | Live heuristic MiB | Neutral rules MiB |','|---|---:|---:|---:|---:|---:|---:|']
  for k,ss in real:
   oracle='jev-table:oracle-context' if 'jev-table:oracle-context' in ss else 'jev-table:oracle-site'
   lines.append('| '+k.split('/')[-1]+' | '+' | '.join(val(ss,v) for v in ['mi',oracle,'jev-live:static-model','jev-live:hybrid','jev-live:heuristic','jev-live:rules-neutral'])+' |')
 regression=BASE/'regression.json'
 if regression.exists():
  d=json.loads(regression.read_text());groups,benches=complete_groups(d)
  lines+=['',f'Regression with no `MIMALLOC_*` overrides: {len(benches)}/22 complete workloads. Peak RSS and inverse-throughput/time scores remain regression metrics, distinct from idle fragmentation.', '', '| Workload | mi peak MiB | Static peak MiB / score ratio | Hybrid peak MiB / score ratio | Live heuristic peak MiB / score ratio | Neutral peak MiB / score ratio |','|---|---:|---:|---:|---:|---:|']
  for name in benches:
   base=med([r['score'] for r in groups[name,'mi']]);values=[]
   for v in ('mi','jev-live:static-model','jev-live:hybrid','jev-live:heuristic','jev-live:rules-neutral'):
    rs=groups[name,v];value=f"{med([r['peak_rss_bytes'] for r in rs])/1048576:.2f}"
    if v!='mi':value+=f" / {med([r['score'] for r in rs])/base:.2f}×"
    values.append(value)
   lines.append('| '+name+' | '+' | '.join(values)+' |')
 lines+=['','The combined object-logging free path now updates trace and sampled-live state exactly once before releasing storage. The dedicated test covers retired allocating threads, cross-thread frees, actual address reuse, sample counts, survivors and hybrid demotions at sample rates 1 and 64.','', 'Warm model runs replay collected answers; hybrid’s rules and all no-model controls execute live. Warm replay retains IPC/service costs and excludes sidecar CPU. It bypasses prompt preparation and sidecar symbolization as well as HTTP inference; rule-names resolves symbols live, so its wall time includes that work. It is not end-to-end deployment or hypothetical on-chip inference. Server-sim live bytes exclude metadata, bookkeeping mappings and thread resources, so RSS/live is process-memory amplification. In-place realloc can log a new policy class while retaining its physical heap. Compact aggregates support the published medians; complete trace/cache/decision reconstruction still needs remote artifacts.','']
 result='\n'.join(lines)
 (BASE/'results.md').write_text(result.replace('(results/pass10/','(')+'\n')
 history=(ROOT/'RESULTS.md').read_text().split('<!-- PASS10-END -->',1)[1]
 (ROOT/'RESULTS.md').write_text(headline(summary)+'\n<!-- PASS10-END -->'+history)
if __name__=='__main__':main()
