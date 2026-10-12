#!/usr/bin/env python3
"""Generate pass-9 evidence and headline text from completed matrices."""
import argparse,gzip,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from common import sites,oracle

def median(runs,field):return statistics.median(r[field] for r in runs)
def idle(r,phase='idle'):return max((p for p in r['phases'] if p['phase']==phase),key=lambda p:p.get('cycle',0))['rss_bytes']
def summarize(d):
 groups={}
 for r in d['runs']:
  if r['repetition']>=0:groups.setdefault(r['variant'],[]).append(r)
 return {v:dict(n=len(rs),idle=statistics.median(idle(r) for r in rs),idle_range=[min(idle(r) for r in rs),max(idle(r) for r in rs)],peak=median(rs,'peak_rss_bytes'),wall=median(rs,'wall_seconds'),cpu=median(rs,'cpu_seconds')) for v,rs in groups.items()}

def object_accuracy(out):
 matrix=json.loads((out/'matrix.json').read_text());cold=next(r for r in matrix['runs'] if r['variant']=='jev-live:per-alloc' and r['repetition']==-1)
 path=Path(cold['environment']['JEVALLOC_OBJECT_TRACE']);objects={};final=None
 for line in path.open():
  e=json.loads(line)
  if e['event']=='alloc':objects[e['id']]=e
  elif e['event']=='free':objects[e['id']]['death']=e['clock']
  else:final=e['clock']
 assert final is not None
 decisions=[json.loads(line) for line in (ROOT/cold['decision_log']).open()]
 by_id={(e['request']['key'],e['ordinal']):e for e in decisions if e.get('raw_response') is not None}
 rows=list(objects.values())
 for r in rows:
  r['truth']=int('death' not in r or (r['death']-r['clock'])*2>final)
  r['model_answered']=r['decided'] and (r['key'],r['ordinal']) in by_id
  if r['model_answered']:
   event=by_id[r['key'],r['ordinal']];assert event['request']['size']==r['size'];assert event['response']['class']==r['class'];r['probabilities']=event['raw_response']['answers']['lifetime']['probabilities']
 def metric(rs):
  return dict(objects=len(rs),correct=sum(r['class']==r['truth'] for r in rs),accuracy=sum(r['class']==r['truth'] for r in rs)/len(rs) if rs else None,bytes=sum(r['size'] for r in rs),correct_bytes=sum(r['size'] for r in rs if r['class']==r['truth']),permanent=sum(r['truth'] for r in rs),confusion=[[sum(r['truth']==truth and r['class']==prediction for r in rs) for prediction in (0,1)] for truth in (0,1)])
 contexts={s['key']:s['context'] for s in sites(out/'trace.jsonl')}
 for r in rows:r['context']=contexts.get(r['key'],'')
 payload_keys={k for k,c in contexts.items() if c.startswith('kind=store ')}
 payload=[r for r in rows if r['key'] in payload_keys];assert len(payload)==2400,len(payload)
 assert len(by_id)==sum(r['model_answered'] for r in rows)
 by_context={context:dict(all_payloads=metric([r for r in payload if r['context']==context]),model_answered=metric([r for r in payload if r['context']==context and r['model_answered']])) for context in sorted({r['context'] for r in payload})}
 answer=dict(by_context=by_context,payload_objects=metric(payload),final_allocation_clock=final,all_objects=metric(rows),model_answered=metric([r for r in rows if r['model_answered']]),unasked=metric([r for r in rows if not r['model_answered']]),decisions=len(decisions),model_decisions=len(by_id),http_requests=sum(e.get('model_seconds',0)>0 for e in decisions),model_seconds=cold['model_seconds'],cold_wall=cold['wall_seconds'],budget_fallbacks=sum(e.get('budget_exhausted',False) for e in decisions),note='Object truth: never freed, or alive for more than half final requested allocation volume. Confusion rows=truth transient/permanent, columns=chosen transient/permanent. Exact object logging overhead included.')
 (out/'object-accuracy.json').write_text(json.dumps(answer,indent=2));(out/'object-truth.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows));return answer

def main():
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();base=ROOT/'results/pass9';summary={};costs=[];context_coverage={};prior_examples=[];hybrid_transitions=0;hybrid_runs=0
 permanent_file=gzip.open(base/'permanent-pairs.jsonl.gz','wt');permanent_count=0
 for path in sorted(base.glob('*/matrix.json')):
  d=json.loads(path.read_text())
  if not d.get('complete') or path.parent.name in ('mesh','instrument'):continue
  name=path.parent.name;summary[name]=summarize(d)
  performance=path.parent/'performance/matrix.json'
  if performance.exists():
   measured=json.loads(performance.read_text())
   if measured.get('complete'):summary[name]=summarize(measured)
  events={};per_alloc_events={}
  for r in d['runs']+d.get('coverage_runs',[]):
   if 'decision_log' not in r:continue
   for line in (ROOT/r['decision_log']).open():
    e=json.loads(line)
    if e.get('raw_response') is not None:
     events.setdefault((r['variant'],e['request']['key']),e)
     if r['variant']=='jev-live:per-alloc' and r['repetition']==-1:
      per_alloc_events.setdefault(e['request']['key'],[]).append(dict(ordinal=e['ordinal'],size=e['request']['size'],answer=e['response']['class'],probabilities=e['raw_response']['answers']['lifetime']['probabilities']))
  if name=='site-mixed-1':
   for (variant,key),event in events.items():
    if variant not in ('jev-live:static-site','jev-live:static-model') or 'store_request_payload' not in (event.get('model_request') or {}).get('state',''):continue
    label=('transient','permanent')[event['response']['class']]
    probability=event['raw_response']['answers']['lifetime']['probabilities'][label]
    prior_examples.append(f"{event['request'].get('context') or 'no context'}: {label} (P={probability:.4f})")
  if name.startswith('site-mixed-'):
   for run in d['runs']:
    if run['repetition']>=0 and run['variant']=='jev-live:hybrid':
     hybrid_runs+=1;hybrid_transitions+=sum(s['promotions']+s['demotions'] for s in run['allocator_stats']['hybrid_sites'].values())
  coverage=dict(bytes=0,context_bytes=0,pairs=0,pairs_below_admission=0,bytes_below_admission=0)
  for s in sites(path.parent/'trace.jsonl'):
   coverage['bytes']+=s['bytes'];coverage['pairs']+=1
   if s['context']:coverage['context_bytes']+=s['bytes']
   if s['bytes']<65536:coverage['pairs_below_admission']+=1;coverage['bytes_below_admission']+=s['bytes']
   if not oracle(s):continue
   labels={}
   for v in ('jev-live:static-site','jev-live:static-model','jev-live:hybrid'):
    e=events.get((v,s['site_key'] if v=='jev-live:static-site' else s['key']))
    labels[v]=dict(answer=e['response']['class'],probabilities=e['raw_response']['answers']['lifetime']['probabilities'],state=(e.get('model_request') or {}).get('state')) if e else dict(answer=None,reason='headroom gate failed' if name.startswith('redis') and not d['headroom']['eligible'] else 'not admitted / not evaluated')
   if name=='per-alloc-small':labels['jev-live:per-alloc']=dict(decisions=per_alloc_events.get(s['key'],[]),reason=None if s['key'] in per_alloc_events else 'not admitted')
   permanent_file.write(json.dumps(dict(workload=name,key=s['key'],site_key=s['site_key'],context_signature=s['context_signature'],context=s['context'],bytes=s['bytes'],class_bytes=s['class_bytes'],models=labels),separators=(',',':'))+'\n');permanent_count+=1
  coverage['context_byte_share']=coverage['context_bytes']/coverage['bytes'];context_coverage[name]=coverage
  for r in d['runs']:
   if r['repetition']!=-1:continue
   fills=[f for f in d.get('coverage_runs',[]) if f['variant']==r['variant'] and f.get('coverage_fill')]
   cold_events=[json.loads(line) for line in (ROOT/r['decision_log']).open()]
   costs.append(dict(model_answers=sum(e.get('raw_response') is not None for e in cold_events),workload=name,variant=r['variant'],cold_wall=r['wall_seconds'],cold_and_fill_model_seconds=r['model_seconds']+sum(f['model_seconds'] for f in fills),decisions=r['allocator_stats']['decisions'],coverage=r.get('model_coverage'),pairs=r['allocator_stats']['sites']))
 permanent_file.close()
 (base/'context-coverage.json').write_text(json.dumps(context_coverage,indent=2))
 (base/'summary.json').write_text(json.dumps(summary,indent=2));(base/'costs.json').write_text(json.dumps(costs,indent=2))
 headlines=[]
 for name in ('site-mixed-1','site-mixed-16'):
  if name in summary:
   ss=summary[name];mi=ss['mi']['idle'];oc=ss['jev-table:oracle-context']['idle'];model=ss['jev-live:static-model']['idle'];hybrid=ss['jev-live:hybrid']['idle']
   headlines.append(f"{name}: context oracle saves {100*(mi-oc)/mi:.1f}% of mimalloc idle RSS; Clef/context captures {100*(mi-model)/(mi-oc):.1f}% and hybrid/context {100*(mi-hybrid)/(mi-oc):.1f}% of that saving.")
 negatives=[name for name,ss in summary.items() if name.startswith('redis') and 'jev-live:static-model' not in ss]
 if negatives:headlines.append('No validated >5% context-table headroom on '+', '.join(negatives)+'. These workloads receive no model decisions.')
 lines=['# Pass 9 — decisions from live request context','',' '.join(headlines),'','The context API requires a small change to the application at request dispatch.', '',f'Completed context workload blocks: {len(summary)}/6. Five interleaved warm repetitions per published variant.','',
 '| Workload | mi MiB | Per-site oracle | Context oracle | Code-only/site | Clef/context | Hybrid/context | Heuristic/context | Search | Per-alloc |',
 '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 order=['mi','jev-table:oracle-site','jev-table:oracle-context','jev-live:static-site','jev-live:static-model','jev-live:hybrid','jev-live:heuristic','jev-table:search','jev-live:per-alloc']
 for name,ss in summary.items():lines.append('| '+name+' | '+' | '.join(f"{ss[v]['idle']/1048576:.2f}" if v in ss else '—' for v in order)+' |')
 lines+=['','| Workload | Original sites | Context pairs | Distinct signatures | Bytes carrying context |','|---|---:|---:|---:|---:|']
 for name in summary:
  truth=json.loads((base/name/'matrix.json').read_text())['truth'];lines.append(f"| {name} | {truth['sites']} | {truth['pairs']} | {truth['contexts']} | {100*context_coverage[name]['context_byte_share']:.2f}% |")
 lines+=['','| Workload | Policy | Warm wall/mi | CPU/mi | Peak MiB | Cold wall s | Cold+fill HTTP s | Sidecar / model answers | Asked pairs |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for c in costs:
  ss=summary[c['workload']];v=ss[c['variant']];coverage=c['coverage'];lines.append(f"| {c['workload']} | {c['variant']} | {v['wall']/ss['mi']['wall']:.3f} | {v['cpu']/ss['mi']['cpu']:.3f} | {v['peak']/1048576:.2f} | {c['cold_wall']:.2f} | {c['cold_and_fill_model_seconds']:.2f} | {c['decisions']} / {c['model_answers']} | {coverage['asked_sites'] if coverage else 'n/a'} / {c['pairs']} |")
 if 'per-alloc-small' in summary:
  accuracy=object_accuracy(base/'per-alloc-small');m=accuracy['model_answered'];all_payloads=accuracy['payload_objects'];lines+=['',f"Per-allocation accuracy on model-answered objects: {m['correct']}/{m['objects']} ({100*m['accuracy']:.2f}%). Across all payloads, including the default class before admission: {all_payloads['correct']}/{all_payloads['objects']} ({100*all_payloads['accuracy']:.2f}%). {accuracy['unasked']['objects']} total objects were not model-answered. The confusion matrix and byte accuracy are in [object-accuracy.json](results/pass9/per-alloc-small/object-accuracy.json).",f"Cold per-allocation: {accuracy['model_decisions']} model decisions, {accuracy['http_requests']} HTTP requests, {accuracy['model_seconds']:.2f} model seconds, {accuracy['cold_wall']:.2f} wall seconds.", 'The small experiment has 2,400 payload allocations over two cycles, four times the normal payload size, and omits parsing/response allocations and purge pulses. This allows the rare day-TTL pair to reach admission within a 3,000-decision budget. The cold run logs exact object lifetimes. Separate five-run warm comparisons disable this logger, retain per-allocation decisions and sampling, and replay the recorded answers; headline RSS and warm timing use those measurements when complete.']
  ss=summary['per-alloc-small'];mi=ss['mi']['idle'];per=ss['jev-live:per-alloc']['idle'];oc=ss['jev-table:oracle-context']['idle']
  lines += [f"An always-transient classifier would score {sum(m['confusion'][0])}/{m['objects']} ({100*sum(m['confusion'][0])/m['objects']:.2f}%) on the same answered objects. Permanent-object recall is {m['confusion'][1][1]}/{m['permanent']} ({100*m['confusion'][1][1]/m['permanent']:.2f}%). The observed chosen class is constant within each TTL bucket across the tested requested sizes."]
  lines += ['',f"At this small scale, per-allocation placement saves {100*(mi-per)/mi:.1f}% of mimalloc idle RSS and captures {100*(mi-per)/(mi-oc):.1f}% of the context oracle's saving. High object accuracy does not imply the same RSS saving: admission leaves early allocations in the default heap, and live-decision machinery has a material fixed cost. The 119 model-answered errors are short-TTL objects that exceed the trace's half-volume lifetime threshold; 56 additional day-TTL payloads precede admission."]
 if prior_examples:lines+=['','At the shared payload stack: '+'; '.join(prior_examples)+'.',f'Hybrid makes {hybrid_transitions} class transitions across {hybrid_runs} warm mixed-workload runs.']
 lines+=['', 'The context API requires a small application change. Applications normalize and bucket the supplied text; the library copies 255 bytes plus NUL. Context applies to allocations after the dispatch hook. Redis input parsing precedes the command hook. Some context-bearing value records are logical realloc events during string trimming; the inherited in-place realloc path retains the original physical block. Context on that later event does not retroactively relocate storage, so trace classification accuracy is not a physical-placement upper bound.','',
 'Redis-drop uses colon-free numbered keys. The specified prefix rule retains these identifiers (up to 16 bytes), producing 160,292 signatures and 495,421 pairs. That defeats cache sharing and adds table/key metadata overhead; the key-only control is about 16 MiB above mimalloc. No model was run on this failed-gate workload.','',
 'Admission is 64 KiB per (site, context signature), budget 3,000. Cross-thread counter batching can delay admission. Byte coverage includes bytes allocated before an answer; it is not the fraction routed under the model label. Hybrid rules operate per pair. Cached warm runs replay recorded answers without HTTP inference; sampling and hybrid transitions still execute. The per-allocation response cache includes the full allocation request; warm ordinal replay rejects changed size, context or stack. Runtime statistics may drift.','',
 'RSS is the final idle phase, not the mean of multiple cycles. Greedy search uses the top 24 byte-heavy pairs, three runs per flip and a >2% training improvement, followed by five independent interleaved comparisons. Redis model runs require >5% validated table savings against mimalloc. Search does not prove an optimum.','',
 'CPU time is the workload process user plus system time from wait4; sidecar CPU is excluded. Wall time includes synchronous decision-service delays. Native model HTTP seconds are reported separately.','',
 'Exact permanent-pair labels, model probabilities and prompt states: [permanent-pairs.jsonl.gz](results/pass9/permanent-pairs.jsonl.gz). All measured costs: [costs.json](results/pass9/costs.json). Full median/range data: [summary.json](results/pass9/summary.json).']
 text='\n'.join(lines)+'\n';(base/'context-results.md').write_text(text)
 if a.publish:
  history=base/'prior-results.md'
  if not history.exists():history.write_text((ROOT/'RESULTS.md').read_text())
  compaction=(base/'compaction-results.md').read_text() if (base/'compaction-results.md').exists() else '## Mesh comparison\n\nPending: context measurements run first.\n'
  (ROOT/'RESULTS.md').write_text(text+'\n'+compaction+'\n## Earlier passes (history)\n\n'+history.read_text())
if __name__=='__main__':main()
