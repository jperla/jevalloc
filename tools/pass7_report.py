#!/usr/bin/env python3
"""Render audited pass-7 observations without rewriting historical results."""
import hashlib,json,statistics,sys
from pathlib import Path
from selection import complete_groups
from common import sites,oracle
from symbolize import symbolize
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';OUT=R/'pass7'
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def med(rows,key):return statistics.median(r[key] for r in rows)
def rss(rows,frag=True):
    if not frag:return med(rows,'peak_rss_bytes')
    return statistics.median(max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p['cycle'])['rss_bytes'] for r in rows)
def fmt_capture(mi,oracle,value):return f'{(mi-value)/(mi-oracle):.1%}' if mi>oracle else 'n/a'
def verified(path,tests):
    data=read(path);audit_path=path.with_suffix('.inference-audit.json')
    if not audit_path.exists():return None
    audit=read(audit_path)
    if audit['matrix_sha256']!=digest(path) or audit['overlapping_runs']:return None
    hashes=[v for k,v in data['configuration']['fingerprints'].items() if Path(k).name=='libjevalloc.so']
    assert hashes==[tests['library_sha256']],(path,hashes)
    for r in data['runs']:
        if r['repetition']>=0:assert not r.get('model_seconds') and not r.get('replay_missing') and not r.get('decision_errors')
    return data,*complete_groups(data)
def main():
    tests=read(OUT/'tests.json');assert tests['passed'] and tests['full_suite'] and len(tests['workloads'])==22
    datasets=[]
    for family in ('pure','rest'):
        for prompt in ('stack-v1','stack-v1-nodesc'):
            path=OUT/f'{family}-{prompt}'/'matrix.json'
            if path.exists():
                got=verified(path,tests)
                if got:datasets.append((path,True,*got))
    for path in (R/'pass7-regression.json',OUT/'regression-progress.json'):
        if path.exists():
            got=verified(path,tests)
            if got:
                datasets.append((path,False,*got))
                break
    nf=sum(len(names) for _,frag,_,_,names in datasets if frag);nr=sum(len(names) for _,frag,_,_,names in datasets if not frag)
    lines=['# Pass 7 — stack-only live classification','',f'**Status: {nf}/12 fragbench prompt/workload blocks; {nr}/22 regression workloads complete and audited.** Five interleaved warm repetitions per variant. Pass-6 results below remain the historical `v-permanent-1` measurement.', '',f"Measured library SHA-256: `{tests['library_sha256']}`. Full Linux correctness passed for all 22 workloads.",'',
    'Code-only Clef captures 99.1% of the oracle idle-RSS saving on site-pure with one thread and 94.0% with 16 threads; omitting the description gives 99.1% and 94.8%. All five queried first-sight sites agree with the oracle. Runtime Clef captures only 20.6% and 14.2%: the requested confidence/age gate still admits an early, incorrect session promotion before any session ends. Redis model byte coverage rises from about 2% in pass 6 to about 99.8%; neither the mixed-site nor Redis fragmentation workloads show positive oracle savings. Timing costs and acceptance-target misses are reported below without further prompt or policy tuning.', '',
    'The default `stack-v1` includes a neutral hand-written program description and up to 12 function/file/line stack frames, without source. `stack-v1-nodesc` omits the description. The old descriptions are retained verbatim in `descriptions-leaky/`; the old prompt was not rerun. The two new prompt variants isolate the description in first-sight context; comparisons with pass 6 also include the byte gate, budget and runtime-policy changes, so they are not a source-only causal ablation. Site keys remain four frames. The oracle remains the prior-trace byte-majority transient/permanent label (permanent = never freed or alive through more than half the final allocation volume).', '',
    'All live policies admit a site only after at least 64 KiB of successful requested bytes; smaller sites remain transient. Admission is checked before the next allocation after crossing the threshold. A one-shot large allocation can therefore remain unasked; Barnes is an observed 0%-coverage case with six large one-allocation sites. Counter batching can also delay admission. Each cold model schedule has 1,500 slots shared with replay coverage fills, including cached answers and rechecks. Byte coverage counts all requested bytes from sites with a model-backed answer, including bytes allocated before the answer; it is not the fraction allocated after classification. Published totals can omit up to 4,095 unmerged allocations per still-active thread/site at exit; sample clocks and concurrent snapshots are approximate.', '',
    'For an initially transient site, runtime Clef can promote to permanent only with permanent probability at least 0.8 and oldest still-live reservoir sample age strictly above one quarter of the current requested-byte clock. The heuristic uses a uniform 128-entry reservoir, requires at least 16 entries, and examines entries strictly older than the lower count-median age: permanent requires less than 5% freed requested bytes in that cohort AND the same age gate. Otherwise transient. Freed entries remain in the reservoir; sample selection is independent of survival. Age uses surviving reservoir entries and the batched clock, not the final run length.', '',
    'Headline timings replay recorded decisions with unchanged live sampling and no inference. Cold inference and coverage-fill costs are separate below. Missing-slot probes are excluded and retried after fills. Warm request state can drift from the cold state: replay measures the recorded policy, not whether fresh inference would repeat its answers. Model-server memory is excluded. Five observations give medians and ranges, not equivalence claims. Settle time is included in fragbench wall time. The independent server-log audit found no inference overlap in the published warm runs.', '',
    '## Fragmentation', '', '| Prompt | Workload | mi idle MiB | Oracle MiB | Oracle saving | Code-only MiB / capture | Runtime MiB / capture | Heuristic MiB / capture |', '|---|---|---:|---:|---:|---:|---:|---:|']
    details=['# Pass 7 detailed warm observations','', 'RSS is final idle RSS for fragbench and peak RSS for regression. Live bytes and RSS/live apply to final-idle fragbench phases. Score is normalized inverse throughput for duration-limited regression workloads (and Redis regression), otherwise wall time; lower is better.', '', '| Prompt | Workload | Variant | RSS MiB median [min,max] | Wall s median [min,max] | CPU s | Wall/mi | CPU/mi | Live MiB | RSS/live | Peak MiB | Score/mi |', '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    costs=['| Prompt | Workload | Policy | Wall/mi | Score/mi | CPU/mi | Cold byte coverage | Warm byte coverage | Model slots / rechecks | Cold wall s | Cold+fill HTTP s |', '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    evidence=[];accuracy=[];phase_rows=[];interpret=[];reglines=[];site_findings=[];target_misses=[]
    for path,frag,data,groups,names in datasets:
        prompt=data['configuration']['prompt']
        for b in names:
            vs=('jev-live:static-model','jev-live:model','jev-live:heuristic')
            baseline=groups[b,'mi'];mi=rss(baseline,frag);ora=rss(groups[b,'jev-table:oracle'],frag)
            vals=[rss(groups[b,v],frag) for v in vs]
            if not frag:
                none=groups[b,'jev-none'];keyonly=groups[b,'jev-keyonly'];heuristic=groups[b,'jev-live:heuristic'];oracle_runs=groups[b,'jev-table:oracle']
                checks={'none_peak_rss/mi':rss(none,False)/mi,'none_score/mi':med(none,'score')/med(baseline,'score'),'keyonly_peak_rss/none':rss(keyonly,False)/rss(none,False)}
                for check,value in checks.items():
                    if value>1.03:target_misses.append(dict(benchmark=b,check=check,ratio=value,target=1.03))
                if b in ('larson','larson-sized','xmalloc-test','mstress','rptest','sh6benchN','sh8benchN'):
                    value=med(heuristic,'score')/med(oracle_runs,'score')
                    if value>1.15:target_misses.append(dict(benchmark=b,check='heuristic_score/oracle',ratio=value,target=1.15))
            headline=f'| {prompt} | {b} | {mi/2**20:.2f} | {ora/2**20:.2f} | {1-ora/mi:.1%} | '+' | '.join(f'{v/2**20:.2f} / {fmt_capture(mi,ora,v)}' for v in vals)+' |'
            if frag:lines.append(headline)
            else:reglines.append(headline)
            model,heur=vals[1],vals[2]
            interpret.append(f"{prompt}, {b}: oracle {'saves' if mi>ora else 'does not save'} memory ({ora/mi:.3f}× mi); runtime Clef {'beats' if model<heur else 'does not beat'} the heuristic on RSS ({model/heur:.3f}×). Code-only/runtime/heuristic RSS relative to oracle: "+'/'.join(f'{x/ora:.3f}×' for x in vals)+'.')
            trace=path.parent/(b+'.trace.jsonl') if frag else R/'traces'/(b+'.jsonl')
            truthrows=sites(trace);truth={s['key']:oracle(s) for s in truthrows}
            table_path=(path.parent/'tables' if frag else R/'tables')/b/'oracle.txt'
            table={key:int(cls) for key,cls in (line.split() for line in table_path.read_text().splitlines() if line.strip())}
            assert table==truth,(b,'oracle table/trace mismatch')
            if frag and b.startswith(('site-pure','site-mixed')):symbolize(truthrows)
            if frag and b.startswith('site-mixed'):
                payload=[s for s in truthrows if any(f.get('function')=='store_request_payload' for f in s['frames'])]
                assert len(payload)==1
                ceiling=max(payload[0]['class_bytes'])/payload[0]['bytes'];whole=sum(max(s['class_bytes']) for s in truthrows)/sum(s['bytes'] for s in truthrows)
                interpret.append(f'{prompt}, {b}: fixed-site classification ceiling is {ceiling:.2%} for the mixed payload site and {whole:.2%} over the workload; this does not bound RSS.')
            for v in data['configuration']['variants']:
                runs=groups[b,v]
                xs=[rss([r],frag)/2**20 for r in runs];ws=[r['wall_seconds'] for r in runs]
                details.append(f'| {prompt} | {b} | {v} | {statistics.median(xs):.2f} [{min(xs):.2f}, {max(xs):.2f}] | {statistics.median(ws):.3f} [{min(ws):.3f}, {max(ws):.3f}] | {med(runs,"cpu_seconds"):.3f} | {med(runs,"wall_seconds")/med(baseline,"wall_seconds"):.3f} | {med(runs,"cpu_seconds")/med(baseline,"cpu_seconds"):.3f} |')
                live='n/a';ratio='n/a'
                if frag:
                    idle=[max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p['cycle']) for r in runs]
                    live=f'{statistics.median(p["live_bytes"] for p in idle)/2**20:.2f}'
                    ratio=f'{statistics.median(p["fragmentation_ratio"] for p in idle):.3f}'
                details[-1]+=f' {live} | {ratio} | {med(runs,"peak_rss_bytes")/2**20:.2f} | {med(runs,"score")/med(baseline,"score"):.3f} |'
                if frag:
                    for r in runs:
                        for p in r['phases']:phase_rows.append(dict(prompt=prompt,benchmark=b,variant=v,repetition=r['repetition'],**p))
                if v not in vs:continue
                cold=next(r for r in data['runs'] if r['benchmark']==b and r['variant']==v and r.get('cold'))
                events=[json.loads(s) for s in (ROOT/cold['decision_log']).read_text().splitlines()]
                schedule=[json.loads(s) for s in (ROOT/cold['replay_schedule']).read_text().splitlines()]
                modeled=[e for e in schedule if e.get('raw_response') is not None]
                if v!='jev-live:heuristic' and not modeled:
                    interpret.append(f'{prompt}, {b}, {v[9:]}: this variant used the default class throughout, with no model-backed decisions.')
                assert len(modeled)<=1500,(b,v,'model budget')
                assert all(e['request']['site']['eligible_bytes']>=65536 for e in events),(b,v,'byte admission')
                for e in events:
                    payload=e.get('model_request')
                    if payload:
                        assert '>> ' not in payload['state']
                        if e['ordinal']==0:assert 'Observed so far' not in payload['state']
                        if prompt=='stack-v1-nodesc':assert 'About the program:' not in payload['state']
                    if e['ordinal']>0 and v=='jev-live:model' and e['response']['class']==1:
                        first=next(x for x in events if x['request']['key']==e['request']['key'] and x['ordinal']==0)
                        if first['response']['class']==0 and e.get('raw_response'):
                            assert e['raw_response']['answers']['lifetime']['probabilities']['permanent']>=.8
                            assert 4*e['request']['site']['oldest_age_bytes']>e['request']['process']['alloc_clock']
                fills=[r for r in data.get('coverage_runs',[]) if r['benchmark']==b and r['variant']==v]
                coldcov=cold.get('model_coverage');warmcov=[r.get('model_coverage') for r in runs]
                cv=f'{1-coldcov["unasked_byte_share"]:.2%}' if coldcov else 'n/a'
                wv=f'{statistics.median(1-c["unasked_byte_share"] for c in warmcov):.2%}' if coldcov else 'n/a'
                costs.append(f'| {prompt} | {b} | {v[9:]} | {med(runs,"wall_seconds")/med(baseline,"wall_seconds"):.3f} | {med(runs,"score")/med(baseline,"score"):.3f} | {med(runs,"cpu_seconds")/med(baseline,"cpu_seconds"):.3f} | {cv} | {wv} | {len(modeled)} / {sum(e["ordinal"]>0 for e in modeled)} | {cold["wall_seconds"]:.1f} | {cold.get("model_seconds",0)+sum(r.get("model_seconds",0) for r in fills):.1f} |')
                initial=[e for e in events if e.get('raw_response') and e['ordinal']==0]
                missing=[e['request']['key'] for e in initial if e['request']['key'] not in truth]
                confusion=[[0,0],[0,0]]
                if not missing:
                    for e in initial:confusion[truth[e['request']['key']]][e['response']['class']]+=1
                accuracy.append(dict(prompt=prompt,benchmark=b,variant=v,first_sight_sites=len(initial),missing_truth=missing,confusion=None if missing else confusion))
                if frag and b.startswith('site-pure'):
                    dominant=sorted(truthrows,key=lambda s:s['bytes'],reverse=True)[:4]
                    for site in dominant:
                        history=[e for e in events if e['request']['key']==site['key']]
                        if v in ('jev-live:static-model','jev-live:model'):
                            initial=next((e for e in history if e['ordinal']==0),None)
                            name=next((f.get('function') for f in site['frames'] if f.get('function') in ('parse_request_buffer','assemble_response_buffer','create_session_state','insert_cache_index')),site['key'])
                            if initial:
                                probs=initial.get('raw_response',{}).get('answers',{}).get('lifetime',{}).get('probabilities',{})
                                for e in history:
                                    if e['ordinal']>0 and e['response']['class']==1 and initial['response']['class']==0:
                                        site_state=e['request']['site'];clock=e['request']['process']['alloc_clock']
                                        prob=e.get('raw_response',{}).get('answers',{}).get('lifetime',{}).get('probabilities',{}).get('permanent',0)
                                        site_findings.append(f"{prompt}, {b}, {v[9:]}: `{name}` promoted at recheck {e['ordinal']}, permanent p={prob:.3f}, {site_state['alive_share']}% not freed so far; oldest surviving sample age {site_state['oldest_age_bytes']/2**20:.3f} MiB / current clock {clock/2**20:.3f} MiB ({site_state['oldest_age_bytes']/clock:.1%}). The specified gate admits this promotion.")
                                        break
                                site_findings.append(f'{prompt}, {b}, {v[9:]}: `{name}` first classified {initial["response"]["class"]} (oracle {truth[site["key"]]}), permanent probability {probs.get("permanent",float("nan")):.3f}; decision classes '+str([e['response']['class'] for e in history])+'.')
                        evidence.append(dict(prompt=prompt,benchmark=b,variant=v,key=site['key'],bytes=site['bytes'],truth=truth[site['key']],frames=[dict(function=f.get('function'),file=f.get('file'),line=f.get('line')) for f in site['frames']],history=history))
    lines+=['', 'Capture = (mi RSS − policy RSS)/(mi RSS − oracle RSS). It is undefined (`n/a`) when the oracle saves no memory; tiny oracle savings make this ratio unstable. Negative values are retained.', '', '## Time, model coverage and cold cost', '', 'Score is normalized inverse throughput for duration-limited regression workloads and Redis regression; otherwise it is wall time. Lower is better.', '', *costs, '', 'Model slots include coverage fills; rechecks count model-backed noninitial answers. Heuristic uses no model, so model byte coverage is n/a. HTTP time can include queueing behind the independent prompt study and is not isolated inference speed.', '', '## Regression (peak RSS)', '']
    if reglines:
        lines+=['These are peak RSS measurements of short programs, rather than idle fragmentation. All 12 variants, timing ranges and inverse-throughput score ratios are in the detailed table. Duration-limited workloads do not provide fixed-work RSS comparisons.', '', '| Prompt | Workload | mi peak MiB | Oracle MiB | Oracle saving | Code-only MiB / capture | Runtime MiB / capture | Heuristic MiB / capture |', '|---|---|---:|---:|---:|---:|---:|---:|',*reglines]
    else:lines+=['Regression is pending; no aggregate regression claim.']
    lines+=['', '## Acceptance target misses', '', 'Targets are diagnostics, not publication gates. Time targets use wall or inverse-throughput score as appropriate. These medians do not establish statistical significance. Possible causes are shim calls and scheduling/measurement variation for none-time misses, page/thread retention and accounting for RSS misses, and stack capture plus sampled lifetime tracking for live-time misses; these causes have not been independently isolated.', '', '| Workload | Check | Measured ratio | Target |', '|---|---|---:|---:|', *[f'| {r["benchmark"]} | {r["check"]} | {r["ratio"]:.3f} | {r["target"]:.2f} |' for r in target_misses]]
    lines+=['', '## Dominant site-pure decisions', '', 'Classes: 0 transient, 1 permanent. Misclassifications and any later changes are retained without prompt tuning.', '', *[x+'\n' for x in site_findings], '', '## Workload interpretation', '', *[x+'\n' for x in interpret], '', 'Detailed measurements: [warm observations](results/pass7/details.md), [phase medians](results/pass7/phases.md) and [phase records](results/pass7/phases.json), [dominant-site decisions](results/pass7/site-decisions.json), [first-sight accuracy](results/pass7/accuracy.json). Full cold, replay, fill and allocator logs remain on the test machine.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n');(OUT/'details.md').write_text('\n'.join(details)+'\n')
    for name,obj in [('site-decisions',evidence),('accuracy',accuracy),('phases',phase_rows),('target-misses',target_misses)]: (OUT/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
    from collections import defaultdict
    pg=defaultdict(list)
    for r in phase_rows:pg[tuple(r[k] for k in ('prompt','benchmark','variant','cycle','phase'))].append(r)
    phase_text=['# Pass 7 phase medians','', '| Prompt | Workload | Variant | Cycle | Phase | RSS MiB | Live MiB | RSS/live |','|---|---|---|---:|---|---:|---:|---:|']
    for key,rows in sorted(pg.items()):
        assert len(rows)==5
        phase_text.append('| '+' | '.join(map(str,key))+f' | {med(rows,"rss_bytes")/2**20:.3f} | {med(rows,"live_bytes")/2**20:.3f} | {med(rows,"fragmentation_ratio"):.3f} |')
    (OUT/'phases.md').write_text('\n'.join(phase_text)+'\n')
    print(f'Published {nf}/12 fragbench blocks and {nr}/22 regression workloads')
if __name__=='__main__':main()
