#!/usr/bin/env python3
"""Build the Beelink report from completed runs, never the scratch macOS matrix."""
import argparse, json, math, statistics
from pathlib import Path
from common import oracle
ROOT=Path(__file__).resolve().parents[1]
STAGES=[('heuristic','first'),('heuristic','last'),('static-model','first'),('model','first'),('model','last')]
def gm(xs):return math.exp(statistics.mean(math.log(x) for x in xs))
def accuracy(data, directory):
    result=[]
    for run in data['runs']:
        if not run.get('cold'):continue
        policy=run['variant'].split(':')[1]
        trace=[json.loads(s) for s in (directory/'traces'/(run['benchmark']+'.jsonl')).read_text().splitlines()]
        truth={s['key']:s for s in trace};events=[json.loads(s) for s in (directory/Path(run.get('replay_schedule',run['decision_log'])).relative_to('results')).read_text().splitlines()]
        groups={}
        for event in events:
            if 'response' in event:groups.setdefault(event['request']['key'],[]).append(event)
        for p,stage in STAGES:
            if p!=policy:continue
            for scope in (('policy','model-only') if policy in ('model','static-model') else ('policy',)):
                site_cm=[[0]*3 for _ in range(3)];byte_cm=[[0]*3 for _ in range(3)]
                for key,decisions in groups.items():
                    if key not in truth:continue
                    decisions=sorted(decisions,key=lambda e:e['ordinal'])
                    if scope=='model-only':decisions=[e for e in decisions if e.get('raw_response')]
                    if not decisions:continue
                    event=decisions[0 if stage=='first' else -1]
                    if scope=='model-only' and stage=='first' and event['ordinal']!=0:continue
                    site=truth[key];actual=oracle(site);predicted=event['response']['class']
                    site_cm[actual][predicted]+=1;byte_cm[actual][predicted]+=site['bytes']
                count=sum(map(sum,site_cm));volume=sum(map(sum,byte_cm))
                result.append({'benchmark':run['benchmark'],'policy':policy,'stage':stage,'scope':scope,'site_confusion':site_cm,'byte_confusion':byte_cm,'sites':count,'trace_sites':len(trace),'bytes':volume,'trace_bytes':sum(s['bytes'] for s in trace),'site_accuracy':sum(site_cm[i][i] for i in range(3))/count if count else None,'byte_accuracy':sum(byte_cm[i][i] for i in range(3))/volume if volume else None})
    return result

def accuracy_markdown(rows):
    lines=['# Accuracy against the trace oracle','','Rows are oracle classes; columns are predictions. Classes: short, medium, long. Byte matrices weight each site by its total traced requested bytes. Only matching keys are scored; coverage is explicit. Policy scope includes budget defaults; model-only scope scores actual model answers and excludes unasked sites. Latest means the highest decision ordinal obtained during the cold and coverage-fill runs, including first-only sites.','']
    for r in rows:
        lines += [f"## {r['benchmark']} / {r['policy']} / {r['stage']} / {r['scope']}",'',f"Coverage: {r['sites']}/{r['trace_sites']} sites; {r['bytes']}/{r['trace_bytes']} requested bytes.",'']
        for title,key in [('Sites','site_confusion'),('Requested bytes','byte_confusion')]:
            lines += [title,'','| Oracle / predicted | short | medium | long |','|---|---:|---:|---:|']
            for name,values in zip(('short','medium','long'),r[key]):lines.append('| '+name+' | '+' | '.join(map(str,values))+' |')
            lines.append('')
    return '\n'.join(lines)

def ratio_table(summary,names,variants,metric):
    lines=['| Workload | '+' | '.join(variants)+' |','|---|'+'---:|'*len(variants)]
    for b in names:lines.append('| '+b+' | '+' | '.join(f"{summary[b,v]['relative_to_mi'][metric]:.3f}" for v in variants)+' |')
    lines.append('| Geometric mean | '+' | '.join(f"{gm([summary[b,v]['relative_to_mi'][metric] for b in names]):.3f}" for v in variants)+' |')
    return '\n'.join(lines)

def budget_report(data,names):
    text="""
## Decision budget and unasked allocation volume

`--max-model-decisions` defaults to 400 per model policy. First answers, cached answers and rechecks consume slots. Coverage-fill runs reserve the already recorded model slots, sharing the cold budget rather than creating a new allowance. Unasked sites receive medium; a site denied a recheck retains its previous class and stops rechecking. Budget fallbacks are never written into the model response cache. Replay follows recorded answers and performs no inference. Heuristic has no model budget.

Unasked means the site received no model-backed answer in that run (a CPU or Vulkan cache answer counts as asked). The numerator sums requested bytes at these sites from the allocator's exit snapshot, not the quantized decision requests or a separate trace. This counts allocation attempts reaching the live path, consistent with the live allocation clock. Cold and headline replay are reported separately; replay percentages pool requested bytes across five runs. First-seen order and time-limited execution affect coverage. End-of-run site totals add no new per-allocation counters. As with the other live counters, the exit snapshot is not globally atomic if application threads are still allocating.

| Workload | Policy | Cold unasked sites / sites | Cold unasked bytes | Cold byte share | Replay unasked sites (median) | Replay byte share |
|---|---|---:|---:|---:|---:|---:|
"""
    for b in names:
        for v in ('jev-live:static-model','jev-live:model'):
            runs=[r for r in data['runs'] if r['benchmark']==b and r['variant']==v]
            cold=next(r['model_coverage'] for r in runs if r.get('cold'))
            warm=[r['model_coverage'] for r in runs if not r.get('cold')]
            total=sum(r['allocated_bytes'] for r in warm)
            share=sum(r['unasked_bytes'] for r in warm)/total if total else 0
            text+=f"| {b} | {v} | {cold['unasked_sites']} / {cold['sites']} | {cold['unasked_bytes']} | {cold['unasked_byte_share']:.2%} | {statistics.median(r['unasked_sites'] for r in warm):g} | {share:.2%} |\n"
    return text

def probability_report(data,directory,names):
    groups={};backends={};fresh=[]
    for r in data['runs']+data.get('coverage_runs',[]):
        if not r.get('decision_log') or r['repetition']>=0:continue
        for line in (directory/Path(r['decision_log']).relative_to('results')).read_text().splitlines():
            e=json.loads(line)
            if e.get('model_seconds',0)>0:fresh.append(e)
    for r in data['runs']:
        if not r.get('cold') or r['variant'] not in ('jev-live:model','jev-live:static-model'):continue
        es=[json.loads(line) for line in (directory/Path(r['replay_schedule']).relative_to('results')).read_text().splitlines()]
        if sum(e.get('raw_response') is not None for e in es)>data['configuration']['max_model_decisions']:
            raise SystemExit('Recorded model schedule exceeds decision budget: '+r['benchmark']+' / '+r['variant'])
        values=[]
        for e in es:
            if not e.get('raw_response'):continue
            values.append(max(e['raw_response']['answers']['lifetime']['probabilities'].values()))
            backend=e.get('model_backend') or 'unknown';backends[backend]=backends.get(backend,0)+1
        groups[r['benchmark'],r['variant']]=values
    details={}
    def describe(xs):
        xs=sorted(xs)
        if not xs:return {'n':0}
        q=lambda p:xs[round((len(xs)-1)*p)]
        return {'n':len(xs),'min':min(xs),'p05':q(.05),'median':statistics.median(xs),'p95':q(.95),'max':max(xs),'mean':statistics.mean(xs),'below_0_4':sum(x<.4 for x in xs)/len(xs),'below_0_5':sum(x<.5 for x in xs)/len(xs),'at_least_0_8':sum(x>=.8 for x in xs)/len(xs)}
    text="""
## Model confidence and latency

Clef's probabilities on these prompts are often close to uniform, such as 0.38/0.29/0.33. Argmax still chooses one class; this is not evidence of calibrated confidence. The following distribution weights each recorded model-backed decision slot equally, including cached decisions and rechecks, excluding default-class fallbacks and five replay duplicates. Identical payloads at different slots can repeat a response. Percentiles select the nearest observed quantile; full summaries are in `probabilities.json`. The prompt was held fixed throughout; no shorter prompt was substituted or established here to preserve the same answers.

| Workload | Policy | Slots | Median top p | p05 | p95 | Top p < 0.4 | Top p < 0.5 |
|---|---|---:|---:|---:|---:|---:|---:|
"""
    for (b,v),xs in groups.items():
        d=describe(xs);details[b+'/'+v]=d
        if xs:text+=f"| {b} | {v} | {d['n']} | {d['median']:.3f} | {d['p05']:.3f} | {d['p95']:.3f} | {d['below_0_4']:.1%} | {d['below_0_5']:.1%} |\n"
    for v in ('jev-live:static-model','jev-live:model'):
        xs=[x for (b,p),values in groups.items() if p==v for x in values];d=describe(xs);details['all/'+v]=d
        if xs:text+=f"| All | {v} | {d['n']} | {d['median']:.3f} | {d['p05']:.3f} | {d['p95']:.3f} | {d['below_0_4']:.1%} | {d['below_0_5']:.1%} |\n"
    text+='\nRecorded model-slot origins: '+', '.join(f'{k}: {v}' for k,v in sorted(backends.items()))+'. Backend provenance stays attached through cache and schedule replay.\n\n'
    for backend in sorted({e.get('model_backend','unknown') for e in fresh}):
        es=[e for e in fresh if e.get('model_backend','unknown')==backend];seconds=[e['model_seconds'] for e in es];tokens=[e.get('usage',{}).get('input_tokens',0) for e in es]
        text+=f"New {backend} HTTP decisions: {len(es)}; latency median {statistics.median(seconds):.3f} s, range {min(seconds):.3f}–{max(seconds):.3f} s; prompt tokens median {statistics.median(tokens):g}, range {min(tokens)}–{max(tokens)}. Per-call latency, tokens, full request and raw response remain in JSONL.\n\n"
    (directory/'probabilities.json').write_text(json.dumps({'distributions':details,'backend_slots':backends},indent=2))
    return text

def historical_cold_report(directory):
    archive=directory/'before-vulkan';path=archive/'beelink.json'
    if not path.exists():return ''
    old=json.loads(path.read_text())
    text="""
## Preserved CPU cold costs before the backend switch

The resumed cold table above does not include the time previously spent populating the retained CPU cache. These original completed cold measurements are preserved separately, with their original source/library fingerprints, and excluded from headline comparisons. No model work is treated as free merely because this pass reused its answer.

| Workload | Policy | Decisions | Model s | Tokens | Blocked s | Wall s | Chip s (approx.) |
|---|---|---:|---:|---:|---:|---:|---:|
"""
    for r in old['runs']:
        text+=f"| {r['benchmark']} | {r['variant']} | {r['allocator_stats']['decisions']} | {r['model_seconds']:.3f} | {r['input_tokens']} | {r['blocked_seconds']:.3f} | {r['wall_seconds']:.3f} | {r['chip_seconds']:.3f} |\n"
    path=archive/'cfrac-jev-live-cold-0b787c30.decisions.jsonl'
    if path.exists():
        events=[json.loads(line) for line in path.read_text().splitlines()]
        seconds=sum(e.get('model_seconds',0) for e in events)
        tokens=sum(e.get('usage',{}).get('input_tokens',0) for e in events if not e.get('cache_hit'))
        text+=f"\nThe interrupted CPU cfrac model attempt recorded {sum('response' in e for e in events)} answered decisions, {seconds:.3f} model seconds and {tokens} input tokens. It has no valid completed wall/RSS/chip measurement and is not a matrix cell. An in-flight request at shutdown may have incurred additional unrecorded work. Its completed answers remain cached.\n"
    return text

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,default=ROOT/'results/beelink');a=p.parse_args();directory=a.results.resolve()
    data=json.loads((directory/'beelink.json').read_text());config=data['configuration'];names=config['workloads'];variants=config['variants'];reps=config['repetitions']
    expected={(b,v,r) for b in names for v in variants for r in range(reps)}|{(b,v,-1) for b in names for v in variants if v.startswith('jev-live:')}
    observed={(r['benchmark'],r['variant'],r['repetition']) for r in data['runs']}
    if len(data['runs'])!=len(observed):raise SystemExit('Duplicate benchmark cells')
    if any(r.get('exit_status') or not r.get('output_ok') for r in data['runs']):raise SystemExit('Unsuccessful benchmark cells')
    if observed!=expected:raise SystemExit(f'Matrix incomplete: {len(expected-observed)} missing cells; refusing to publish a complete report.')
    interference_path=directory/'interference.json'
    interference=json.loads(interference_path.read_text()) if interference_path.exists() else {}
    if interference and not interference.get('resolved'):raise SystemExit('Model-server interference audit unresolved')
    summary={(s['benchmark'],s['variant']):s for s in data['summary']}
    cost=json.loads((directory/'cost.json').read_text());livecost=json.loads((directory/'live-cost.json').read_text());tests=json.loads((directory/'tests.json').read_text());live_tests=json.loads((directory/'live-tests.json').read_text())
    acc=accuracy(data,directory);(directory/'accuracy.json').write_text(json.dumps(acc,indent=2));(directory/'accuracy.md').write_text(accuracy_markdown(acc))
    cold=[r for r in data['runs'] if r.get('cold')];warm=[r for r in data['runs'] if r['variant'].startswith('jev-live:') and not r.get('cold')]
    warm_model=sum(r['model_seconds'] for r in warm)
    coverage=data.get('coverage_runs',[])
    if warm_model or any(r['replay_missing'] for r in warm):raise SystemExit('Headline replay contains model calls or uncovered slots')
    model='jev-live:model';heur='jev-live:heuristic';oracle_variant='jev-table:oracle'
    model_wins=[b for b in names if summary[b,model]['relative_to_mi']['score']<1]
    versus_heur=[b for b in names if summary[b,model]['score']['median']<summary[b,heur]['score']['median']]
    oracle_losses=[b for b in names if summary[b,oracle_variant]['relative_to_mi']['score']>=1]
    rel=lambda v:gm([summary[b,v]['relative_to_mi']['score'] for b in names])
    rssrel=lambda v:gm([summary[b,v]['relative_to_mi']['peak_rss_bytes'] for b in names])
    text=f'''# jevalloc — Beelink experiment report

Linux is the measured platform. The completed matrix contains **{len(data['runs'])} successful runs** across {len(names)} workload configurations: five interleaved repetitions of ten variants, plus a separate cold run for each live policy. There are also {len(coverage)} separately recorded coverage-fill/probe runs, excluded from headline timings. No partial macOS first-pass matrix is used here. Changes remain uncommitted.

The replayed live model's equal-weight geometric-mean throughput-normalized time ratio is **{rel(model):.3f}× mimalloc**; heuristic **{rel(heur):.3f}×**; table oracle **{rel(oracle_variant):.3f}×**. Lower is better. The live model has a lower median than mimalloc on {len(model_wins)}/{len(names)} configurations and than the live heuristic on {len(versus_heur)}/{len(names)}. These are observed medians, not statistical significance claims.

Peak RSS geometric means are **{rssrel(model):.3f}×** for the live model, **{rssrel(heur):.3f}×** for the heuristic and **{rssrel(oracle_variant):.3f}×** for the oracle, relative to mimalloc. Peak RSS excludes the sidecar/model server.

Model faster than mimalloc: {', '.join(model_wins) or 'none'}.

Model faster than heuristic: {', '.join(versus_heur) or 'none'}.

Oracle does not beat mimalloc: {', '.join(oracle_losses) or 'none'}. On these workloads, even perfect prediction of the defined site-lifetime labels has no demonstrated performance benefit with this implementation. The oracle is an upper bound on **label accuracy**, not a mathematical optimum over allocator performance: an imperfect predictor can accidentally produce a more favorable heap layout. The policy remains plain per-thread, per-class heap segregation; no alternate purge policy is mixed into this result.

## What was implemented

`libjevalloc.so` uses ELF `LD_PRELOAD` interposition generated from mimalloc 2.2.4's override source, with real wrappers instead of aliases to symbols in another translation unit. C malloc/calloc/realloc/free, alignment, string duplication, usable-size, and the upstream C++ new/delete forms are covered. The static mimalloc core and plain mimalloc shared-library control use matching optimization, debug and frame-pointer flags. Vendor trees are unchanged. macOS keeps the generated zone/interpose integration and its pthread-key context to avoid loader-time TLS recursion.

Linux per-thread state uses `__thread` with initial-exec TLS. A bounded frame-pointer walk hashes raw return PCs; a 256-entry thread-local cache maps that raw hash to a stable normalized key, immutable table result, normalized frames and live site record. Hits skip image search and table probing. Misses normalize PCs by the registered ELF image base and hash image paths. The executable path is resolved while it is alive so offline `addr2line` can symbolize it. Stack bounds are cached; the walk checks bounds, alignment and increasing links, excludes allocator frames and stops after 64 links or the requested depth. The public key probe has its own recursion guard around Linux stack discovery.

Live mode blocks on a Unix-socket decision and coalesces same-site requests. Decisions change future allocations only. Rechecks use the site's allocation count, with intervals 1,024, 8,192, 65,536 and 524,288, then stop. Per-site counters and the allocation clock use atomics; sampled pointer records use 64 lock shards, with empty-bucket checks for unsampled frees. Default sampling is one in 64 per site. Sampled frees/live counts and bytes are estimates; histogram entries are power-of-two shares on a 65-bucket allocation-clock lifetime histogram. Counter snapshots in concurrent programs are approximate rather than a globally atomic snapshot.

Socket connect/send/receive share a monotonic deadline. Unreachable, malformed or timed-out sidecars cause the configured default class and a process-lifetime circuit breaker; failures and timeouts are recorded. The circuit breaker avoids paying a timeout for every unknown site. Per-thread blocked wall intervals include waiters for a shared decision. Internal metadata bypasses the shim. Requests count allocation attempts that reach the live path; impossible sizes above `PTRDIFF_MAX` are rejected first. Ordinary allocation failure statistics remain approximate.

`tools/jevd.py` implements heuristic, oracle, seeded random, model and static-model policies using only Python's standard library. It symbolizes and caches frames, includes at most two source snippets, and caps source/stack text. Static-model payloads omit runtime state and never recheck. The heuristic starts medium and then uses sampled lifetime histograms alone, with fixed bucket thresholds of 1 MiB (short/medium) and 64 MiB (medium/long), chosen before the matrix without fitting trace lifetimes. Clef's **probability argmax** selects the class; every probability and raw response is retained. No confidence threshold or extra policy tuning was applied.

The Beelink serves `Clef-Flash-Q8_0.gguf` with llama.cpp Vulkan on the Radeon 780M (RADV), bound to `127.0.0.1:8765`, via **`/v1/systemone`**. `scripts/model-server.sh` records the invocation: GPU offload (`-ngl 99`), four compute threads and 4,096-token batch/microbatch. The previous CPU server on 8765 and Vulkan test server on 8766 were stopped. CPU cache entries remain valid and retain their backend provenance; cache identity and prompt text did not change. The model is local and free. No TrustedRouter API key or paid API was used.

## Validation and cost

The macOS `make test` run also passed (19 workload configurations, live and replay tests); its evidence is in `results/macos-pass3/`. All 11 focused Python tests passed on both hosts.

The final Linux workload tests passed for {len(tests['workloads'])} configurations in trace and random-table modes, with exact trace-accounting invariants. Targeted tests cover C/C++ allocation forms, huge/zero sizes, alignment, realloc preservation, thread handoff, distinct and ASLR-stable keys, and exact lifetime boundaries. Live tests cover delayed replies, same-site coalescing, class changes, cross-thread frees, failure deadlines, schedule limits, static-input exclusion and probability argmax. The zero-budget integration test verifies default-only allocation, zero rechecks/inference, complete unasked-byte accounting and a matching replay. The real-server smoke test returned probabilities and input-token counts. Linux cfrac's two canonical request streams were byte-identical: **{live_tests['cfrac_byte_identical']}**, with {live_tests['cfrac_cache_hits']}/{live_tests['cfrac_requests']} second-run cache hits.

Five interleaved calibration samples of five million calls/pairs each are saved in `results/beelink/cost.json`. The key fixture has enough noinline external frames to exercise depth four; timings include wrapper and indirect-call overhead. Table lookup results are cached on raw-key hits.

| Depth | ns/key median | min | max |
|---|---:|---:|---:|
'''
    for depth,xs in cost['key_samples'].items():text+=f"| {depth} | {statistics.median(xs):.3f} | {min(xs):.3f} | {max(xs):.3f} |\n"
    text+='\n| Policy | ns per malloc/free pair median | min | max |\n|---|---:|---:|---:|\n'
    for variant,xs in cost['allocation_free_pair_samples'].items():text+=f"| {variant} | {statistics.median(xs):.3f} | {min(xs):.3f} | {max(xs):.3f} |\n"
    xs=[r['ns_per_pair'] for r in livecost['samples']];text+=f"| live heuristic, 1/64 sampling | {statistics.median(xs):.3f} | {min(xs):.3f} | {max(xs):.3f} |\n"
    text+='''
The none shim's overhead is measured rather than assumed to be zero. The live calibration includes real heuristic sidecar rechecks amortized over five million pairs. Model inference is absent from that microbenchmark; workload cold/replay costs appear below.

## Replay and measurement interpretation

The sidecar has a canonical allocator-request disk cache and a second cache for identical HTTP model payloads. Each workload/policy has its own cache directory. The resumed cfrac cold runs reuse preserved CPU decisions; they are explicitly a resumed cold phase, not empty-cache measurements. Identical-payload reuse is logged. The five headline live repetitions explicitly replay the cold decision sequence by stable site key and decision ordinal. This guarantees an idle model server during replay, including concurrent and time-limited workloads whose live statistics do not reproduce exactly. The log marks differing requests and missing decision slots. Timed workloads may end before slow cold inference reaches later rechecks. Separate cache-fill runs replay known slots and ask the real policy for unseen slots, retaining every answer. Filling continues until a full run discovers no new slots. A provisional replay that encounters an unseen slot is excluded, followed by more filling and a retry. Every accepted headline replay has complete answer coverage and zero model computation. This replay is a control for the recorded decisions, not evidence that the live policy would answer the same way on changed state.

'''
    text+=f"Replay model-compute time: **{warm_model:.6f} s**. Requests with changed state: **{sum(r['replay_drift'] for r in warm)}**. Missing recorded decision slots: **{sum(r['replay_missing'] for r in warm)}**. Per-run counts are in the JSON and decision logs.\n\n"
    text+=f"Coverage filling/probes used an additional **{sum(r.get('model_seconds',0) for r in coverage):.3f} model seconds**, **{sum(r.get('input_tokens',0) for r in coverage)} input tokens**, and {sum(r.get('new_decisions',0) for r in coverage)} newly recorded decision slots. These costs are not hidden in the five replay timings.\n\n"
    if data.get('backend_transition'):
        text+='The two old completed cfrac cold measurements and interrupted CPU attempt are archived under `results/beelink/before-vulkan/`. No headline repetitions existed at transition. Cold measurements were repeated with the retained CPU cache to apply the budget and collect actual per-site byte totals. The original code/library and cache manifest are preserved; all new decision logs identify `model_backend` and `model_origin`. See `backend-transition.json` and `provenance-beelink.json`.\n\n'
    if data.get('adopted_cold_code_provenance'):
        text+='The first two completed cfrac cold measurements were retained when coverage filling was added to the runner. Their binary/table fingerprints match the final pass; their original code fingerprints and source files are preserved in `adopted_cold_code_provenance` and `results/beelink/before-coverage-fill/`. The interrupted live-model attempt was archived and rerun cold with a fresh cache. No incomplete measurement was adopted.\n\n'
    text+='''Wall time and CPU/RSS come from the actual benchmark child via `wait4`; `/usr/bin/time` output is also retained. RSS excludes the Python sidecar and roughly 9.66 GB model file/server residency, consistent with examining the allocator decisions under a hypothetical chip. Allocator bookkeeping costs and memory remain included. The process `rss` sent to the model is mimalloc's current-RSS estimate on Linux (normally current committed memory); the independently measured peak RSS in the result tables is the OS measurement. Invalid negative upstream commit accounting is clamped to unavailable/zero. macOS physical RSS and time-driven commit/purge values can vary across identical allocation streams; its replay test checks allocator state separately and reports exact cache coverage.

“Chip time” is raw wall minus the **sum** of all threads' blocked intervals. It can be negative and is only an approximation for concurrent workloads; it is not used as the headline ranking. Model delays can also affect time-based purge and duration-limited workload behavior, so subtraction cannot reconstruct a counterfactual run.

The upstream workload arguments use 16 processors; SmartHeap uses 32 threads as bench.sh's procs×2 rule specifies. Redis 6.2.7 is built with libc allocation and frame pointers. Its upstream 100,000-request, pipeline-16 LPUSH command and flush/shutdown sequence are retained; a private Unix socket and disabled persistence isolate the test from existing services. Timing/RSS measure only the injected Redis server; redis-benchmark and redis-cli use the system allocator. The VM and desktop were left untouched. Both SmartHeap archives were checked against the upstream pinned SHA-256 values and patched only under build/. Optional rocksdb/lean/lua/gs were not added.

## Time relative to mimalloc

Lower is better. Score follows bench.sh's throughput normalization for larson, xmalloc-test, rptest, glibc-thread and Redis; other scores are wall time. Five-repetition medians and min/max for wall, CPU and RSS are in [the full table](results/beelink/beelink.md). Equal-weight geometric means are descriptive, not universal allocator rankings.

'''
    text+=ratio_table(summary,names,variants,'score')+'\n\n## Wall time relative to mimalloc\n\n'+ratio_table(summary,names,variants,'wall_seconds')+'\n\n## Peak RSS relative to mimalloc\n\n'+ratio_table(summary,names,variants,'peak_rss_bytes')+'\n'
    text+='\n## Cold live runs\n\n| Workload | Policy | Decisions | Rechecks | Cache hits | Model s | Input tokens | Blocked s | Wall s | Chip s (approx.) |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for r in cold:
        st=r['allocator_stats'];text+=f"| {r['benchmark']} | {r['variant']} | {st['decisions']} | {st['rechecks']} | {r['cache_hits']} | {r['model_seconds']:.3f} | {r['input_tokens']} | {r['blocked_seconds']:.3f} | {r['wall_seconds']:.3f} | {r['chip_seconds']:.3f} |\n"
    text+=historical_cold_report(directory)
    if interference:
        text+=f"\n## Concurrent prompt-study interference\n\nA separate `~/jevalloc/promptlab` process began submitting requests to the same model server after this pass started. It was left untouched. Cold HTTP latency during that overlap includes queueing behind its requests, so it is not isolated inference latency. {interference.get('replaced_runs',0)} potentially affected headline measurements were archived and replaced after the server became idle. The final accepted headline intervals were checked against the model-server request log. See `interference.json`, `inference-audit.json` and the archived measurements; no contaminated timing is included in the tables.\n"
    text+='\n## Additional replay coverage work\n\nThese runs fill missing decision slots or validate coverage. They are excluded from the timing matrix; all requests and responses remain in the logs.\n\n| Workload | Policy | Fill/probe runs | New decision slots | Model s | Input tokens | Total wall s |\n|---|---|---:|---:|---:|---:|---:|\n'
    for b in names:
        for v in variants:
            rs=[r for r in coverage if r['benchmark']==b and r['variant']==v]
            if rs:text+=f"| {b} | {v} | {len(rs)} | {sum(r.get('new_decisions',0) for r in rs)} | {sum(r.get('model_seconds',0) for r in rs):.3f} | {sum(r.get('input_tokens',0) for r in rs)} | {sum(r['wall_seconds'] for r in rs):.3f} |\n"
    text+=budget_report(data,names)
    text+=probability_report(data,directory,names)
    text+='\n## Accuracy against the prior trace oracle\n\nThe policy rows include default-class answers for budget-exhausted sites; model-only rows exclude unasked sites and score the first/latest actual model answer. Their smaller coverage is explicit. Only matching site keys are evaluated. Bytes weight the majority-class label of a site by all of its traced bytes. Concurrent and duration-limited cold runs can cover a different prefix of the workload. Latest is the highest decision ordinal recorded across the cold and coverage-fill runs, including sites with no recheck. [Full site and byte confusion matrices](results/beelink/accuracy.md) and [machine-readable matrices](results/beelink/accuracy.json) accompany these percentages.\n\n| Workload | Policy / stage / scope | Sites matched / traced | Byte coverage | Site accuracy | Byte-weighted accuracy |\n|---|---|---:|---:|---:|---:|\n'
    for r in acc:
        pct=lambda x:'n/a' if x is None else f'{x*100:.1f}%'
        text+=f"| {r['benchmark']} | {r['policy']} / {r['stage']} / {r['scope']} | {r['sites']} / {r['trace_sites']} | {pct(r['bytes']/r['trace_bytes'] if r['trace_bytes'] else None)} | {pct(r['site_accuracy'])} | {pct(r['byte_accuracy'])} |\n"
    text+='''
## Limits and evidence

This remains an experiment. The traces are fitted on the same workload, not held-out data. Frame pointers can be missing; dynamic image unloading/reuse, alternate stacks, post-fork synchronization and arbitrary plugins are not validated. Linux image registration is the startup image set. Keys depend on exact binaries, libraries, paths and depth. The direct-mapped raw-stack cache and stable keys are 64-bit hashes. Rebuilds can invalidate tables. Trace metadata is exact for recorded events but excludes bootstrap/reentrant work and requires orderly exit. Live sampling and counters are approximate and do not have trace mode's exact object accounting.

Small timing differences can be noise, especially tiny workloads and thread creation. The machine was not exclusively controlled; its existing VM and desktop stayed running. No external service was stopped, no system packages installed, no sudo used and no git writes performed. Raw outputs, traces, oracle/baseline tables, all decision requests/responses, source/binary fingerprints and host/model provenance are retained under [results/beelink](results/beelink). The stopped `results/first-pass.*` files remain scratch and are not evidence for this report.
'''
    (ROOT/'CODEX-REPORT.md').write_text(text)
    print(ROOT/'CODEX-REPORT.md')
if __name__=='__main__':main()
