#!/usr/bin/env python3
"""Finalize wording only after the complete experiment passes its remote audit."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/pass11';MIB=1048576
def main():
 validation=json.loads((BASE/'validation.json').read_text());assert validation['passed']
 assert (BASE/'stage.txt').read_text().strip()=='complete' and int((BASE/'status').read_text())==0
 for name,digest in validation['matrix_sha256'].items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest,name
 s=json.loads((BASE/'summary.json').read_text());assert s['factorial_complete']==24 and s['redis_complete']==4
 counts=s['counts'];assert len(counts)==12 and all(c['available']==6 for c in counts)
 findings=['# Pass 11 findings','','All 24 factorial blocks (2400 runs), four Redis blocks (220 runs), and both diagnostic option sets are complete and inference-audited. Pass 10’s remaining accepted groups and validation were already complete at this pass’s initial inspection and are committed.','']
 gate_words=[]
 for gate in ('0.6','0.7','0.8'):
  rs=[r for r in s['paired_comparisons'] if r['gate']==gate];names=sorted({r['naming'] for r in rs});assert len(names)==6
  winners=[];supported=[]
  for n in names:
   ns=[r for r in rs if r['naming']==n];assert len(ns)==4
   if all(r['rule']['median']<0 and r['neutral']['median']<0 for r in ns):winners.append(n)
   if all(r['rule']['high']<0 and r['neutral']['high']<0 for r in ns):supported.append(n)
  gate_words.append(f'{len(winners)}/6 at {gate}')
  findings.append(f'Gate {gate}: {len(winners)}/6 namings beat both controls by paired median in all four workload/thread conditions ({", ".join(winners) or "none"}); {len(supported)}/6 do so with both pointwise 95% intervals below zero in every condition ({", ".join(supported) or "none"}).')
  for c in counts:
   if c['gate']==gate:findings.append(f"- {c['workload']}, {c['threads']} threads: beats both controls {c['beat_both']}/6 by paired median, {c['beat_both_intervals']}/6 with both intervals below zero; worse than mi {c['worse_mi']}/6 by paired median.")
  findings.append('')
 findings+=['These counts refer to six fixed namings of two author-designed workloads, not six independent applications. Ten repetitions quantify run variability with frozen priors; the five new mappings each have fresh inference, not ten independent model draws. Pointwise bootstrap intervals are not a family-wide multiple-comparison guarantee. The historical 0.7 plausible-name benefit remains in the record regardless of these additional outcomes.','']
 def redis(n,o,v):return next(r for r in s['redis'] if (r['naming'],r['options'],r['variant'])==(n,o,v))
 un=redis('unnormalized','defaults','jev-live:static-model');mi=redis('unnormalized','defaults','mi')
 findings+= [f"Guarded unnormalized Redis/defaults static/context: idle {un['idle']['median']/MIB:.3f} MiB versus mi {mi['idle']['median']/MIB:.3f} MiB; target CPU {un['cpu']['median']:.6f} s versus {mi['cpu']['median']:.6f} s. Its raw metadata peak median is {un['metadata_peak']['median']/MIB:.3f} MiB; registered pairs {un['pairs']['median']:.0f}; overflow allocations {un['overflow']['median']:.0f}, covering {un['overflow_bytes']['median']/MIB:.3f} requested MiB. Historical unguarded static/context held 4246.531 MiB. This is a boundedness fix; metadata reservations are not a byte-for-byte attribution of RSS.",'']
 diagnostics=[]
 for options in ('defaults','immediate'):
  for policy in ('mi','jev-table:oracle-site','jev-live:static-model'):
   rows=[r for r in s['diagnostic'] if r['options']==options and r['variant']==policy+'/collect' and r['phase']['cycle']==1]
   at={r['phase']['phase']:r for r in rows};before=at['idle10'];default=at['collected-default'];after=at['collected-all-heaps']
   assert before['phase']['live_bytes']==after['phase']['live_bytes']
   b=before['statistics'];a=after['statistics'];released=(b['committed']-a['committed'])/MIB
   valid_commit=b['committed']>=0 and a['committed']>=0
   text=f"{options}, {policy}: idle10 RSS {before['phase']['rss_bytes']/MIB:.3f} MiB, after mi_collect(true) {default['phase']['rss_bytes']/MIB:.3f} MiB, after tagged-heap collection {after['phase']['rss_bytes']/MIB:.3f} MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are {b['area_used']/MIB:.3f}/{b['area_committed']/MIB:.3f} MiB."
   if valid_commit:text+=f' Reported committed bytes fall by {released:.3f} MiB.'
   else:text+=' The reported committed counters are negative and unusable as absolute committed-byte estimates; raw values are retained.'
   rss_drop=(before['phase']['rss_bytes']-after['phase']['rss_bytes'])/MIB
   if valid_commit and released>8 and rss_drop>8:text+=' The large RSS release without workload frees demonstrates deferred reclamation at ten seconds; this retained RSS cannot all be described as irreducible live-page fragmentation.'
   elif rss_drop<2 and (b['area_committed']-b['area_used']-b['empty_area_committed'])/MIB>8:text+=' Forced collection barely changes RSS while heap areas with live blocks contain substantial unused capacity; this supports live-page pinning as the dominant remaining heap cost in this run.'
   else:text+=' Forced collection changes RSS little in this run; the exact counter split remains in the phase table.'
   diagnostics.append(text)
 findings+=diagnostics+['','Mimalloc committed/reserved counters include sparsely touched arenas and are not resident-byte counts; subtracting live bytes from those counters is not an RSS decomposition. The diagnostic uses separate MI_STAT=2 libraries and one observation per policy/options/collection condition. Heap-area inspection can collect delayed frees. It diagnoses this workload/protocol, not an allocator-wide guarantee; RSS also includes bookkeeping, thread resources and metadata. Both option sets preserve identical histories through the final idle10 before the intervention.','']
 (BASE/'findings.md').write_text('\n\n'.join(findings)+'\n')
 worse=sum(r['mi']['median']>0 for r in s['paired_comparisons'])
 headline=f'''# Pass 11 — answering review 3

Separating lifetimes substantially reduces idle RSS in an author-designed synthetic server: roughly 84% in the one-thread pure case with immediate purge, but 23% under the tested default-options protocol, where the reduction persists at ten seconds. Simple names/TTL rules match the model on the original fixture; opaque names remove its benefit, while the historical plausible renaming gives a threshold-sensitive advantage to model probabilities combined with runtime rules: **4 of 16 server comparisons against the matching names/TTL rule**. In the completed six-naming factorial, model+rules beats both controls by paired median in all four workload/thread conditions for {', '.join(gate_words)}; it is worse than plain mimalloc in {worse}/72 naming/workload/thread/gate comparisons. These synthetic conditions do not establish a general model advantage. All pass-10 evidence and the requested pass-11 measurements and audits are complete, and the compact measurement groups and audits are committed in this repository; full traces, logs and model caches remain on the test machine.

The metadata guard bounds state before allocation and falls back without registering another pair. Guarded unnormalized Redis/defaults static/context holds {un['idle']['median']/MIB:.2f} MiB versus mi {mi['idle']['median']/MIB:.2f} MiB, with {un['metadata_peak']['median']/MIB:.2f} MiB raw metadata peak, compared with the historical 4.15 GiB failure. The full 22-workload Linux correctness suite and concurrent budget/cross-thread-free tests pass. [Findings](results/pass11/findings.md) give the gate-specific counts, paired confidence intervals, Redis CPU/overflow results, and matched purge diagnosis; [full tables](results/pass11/results.md) retain medians, ranges, phases, and promotion identities/times. The historical real-program defaults tests show no model reduction above 5% and include severe regressions; the boundedness fix does not turn them into evidence for model value.

'''
 p=ROOT/'RESULTS.md';old=p.read_text();marker='# Pass 10 — answering review 2';assert marker in old;p.write_text(headline+old[old.index(marker):])
 p=BASE/'README.md';text=p.read_text();text=text.replace('# Pass 11 evidence (collection running)','# Pass 11 evidence (complete)').replace('# Pass 11 evidence (pending)','# Pass 11 evidence (complete)')
 text=text.replace('Missing or incomplete\nfactorial, Redis and diagnostic artifacts remain pending. `validation.json` is\npending until all groups and their inference-overlap audits pass.','All requested factorial, Redis and diagnostic artifacts and `validation.json`\nare now present and complete. Earlier partial snapshots were explicitly pending.')
 p.write_text(text)
 digest=hashlib.sha256((BASE/'validation.json').read_bytes()).hexdigest();stamp=BASE/'finalized.json'
 if not stamp.exists():
  with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write('\nPass 11 final audit passed: '+str(validation['accepted_warm_runs'])+' accepted warm runs in '+str(validation['matrices'])+' matrices, plus separately labelled diagnostics. All requested groups are complete and synchronized locally; RESULTS.md is updated, full results/findings/priors/transitions are in results/pass11. No Git writes were performed.\n\n'+'\n\n'.join(findings[3:])+'\n')
 stamp.write_text(json.dumps(dict(complete=True,validation_sha256=digest),indent=2)+'\n')
 print('Pass 11 finalized; all requested groups and audits complete.')
if __name__=='__main__':main()
