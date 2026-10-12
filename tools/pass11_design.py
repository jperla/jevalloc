#!/usr/bin/env python3
"""Generate the fixed pass-11 design; --declare must precede any experiment."""
import argparse,hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FRAGMENTS='conn sess req resp buf obj entry node item ctx msg pkt slot rec blk hdr str vec map pool task job peer port path name field value data chunk stream frame event flag link list queue group token handle'.split()
VERBS='new get put add make init attach build alloc push'.split()
FUNCTIONS='parse_request_buffer assemble_response_buffer create_session_state insert_cache_index store_request_payload'.split()
def design():
 maps=[dict(name='plausible',seed=None,functions=dict(zip(FUNCTIONS,'buf_get resp_build conn_attach entry_put obj_new'.split())),contexts={'0':'a','short':'b','day':'c'})]
 for seed in range(1,6):
  rng=random.Random(seed);names=[]
  while len(names)<5:
   name=rng.choice(FRAGMENTS)+'_'+rng.choice(VERBS)
   if name not in names:names.append(name)
  letters=list('abc');rng.shuffle(letters)
  maps.append(dict(name=f'seed{seed}',seed=seed,functions=dict(zip(FUNCTIONS,names)),contexts=dict(zip(['0','short','day'],letters))))
 variants=[f'{source}-{gate}' for gate in ('0.6','0.7','0.8') for source in ('model','neutral','rule')]+['mi']
 orders=[]
 for ni,m in enumerate(maps):
  for wi,workload in enumerate(['site-pure','site-mixed']):
   for ti,threads in enumerate([1,16]):
    for rep in range(10):
     seed=110000+ni*1000+wi*100+ti*10+rep
     order=variants[:];random.Random(seed).shuffle(order)
     orders.append(dict(naming=m['name'],workload=workload,threads=threads,repetition=rep,seed=seed,variants=order))
 return dict(fragments=FRAGMENTS,verbs=VERBS,mappings=maps,orders=orders,bootstrap_seed=110011,bootstrap_resamples=20000)
def main():
 p=argparse.ArgumentParser();p.add_argument('--declare',action='store_true');a=p.parse_args();d=design()
 path=ROOT/'results/pass11/design.json';body=json.dumps(d,indent=2)+'\n'
 if path.exists():assert path.read_text()==body,'Declared design must never change'
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body)
 if a.declare:
  text='''
### Pass 11 factorial — frozen before any inference or measurement

Six namings: existing plausible plus Python random.Random seeds 1–5. The fixed
40-fragment list and ten verbs below are the complete sampling vocabulary.
For each function in original source order, draw one fragment and one verb
uniformly, join with underscore, retry exact duplicate names only. After five
names, shuffle [a,b,c] with the same RNG to assign the zero/short/day lifetimes.
No filtering by apparent semantics or model response and no post-result edits.

Fragments: %s.
Verbs: %s.

All mappings (original function -> new name; context lifetime -> class letter):

%s

Factors: gates 0.6/0.7/0.8 x prior model/neutral/matching rule x pure/mixed x
1/16 threads x six namings x ten repetitions = 2160 policy observations, plus
240 paired plain-mi observations. Defaults remove all MIMALLOC_* overrides.
400000 objects, settle 250 ms, two cycles, 10-second idle observations in both
cycles, identical phase histories for every variant. Workload RNG remains
1729+worker ID as before; naming seeds and class permutations are the holdout.
Description text is byte-identical to descriptions/server-sim-plausible.txt.
The plausible naming reuses its pass-10 recorded probabilities. For each new
mapping collect fresh stack-v1 static code-only model answers at one thread,
with a fresh dedicated model cache and at most 3000 decisions including fills;
reuse the frozen answer by key at 16 threads and at every gate. Coverage probes
precede warm runs. Unexpected warm keys invalidate that attempt and are filled
under the same budget, with all rejected/fill records retained. No gate or
prior selection based on RSS. Record every probability and prompt.

Model and neutral use identical hybrid replay transport, schedule keys,
first-sight IPC and runtime rules. Neutral replaces raw transient/permanent
probabilities with 0.5/0.5 and initial class with transient (tie convention);
all other request/answer scheduling stays identical. Matching rule remains
pass-10 literal names keywords on pure and literal ttl=day on mixed; it does
not decode the concealed class permutation. It also uses hybrid runtime checks
at each gate. It is evaluated from symbolized names/context once and encoded
in the same replay transport with one-hot probabilities, eliminating the
previous live-symbolization timing asymmetry. This is the same rule semantics,
not an oracle based on lifetime assignments. Any model permanent initial
class remains visible; priors include initial placement as well as vetoes.

Within each naming/workload/thread/repetition block shuffle all ten variants
with Python random.Random(seed). Seed = 110000 + naming_index*1000 +
workload_index*100 + thread_index*10 + repetition, indices in the list orders
above (pure then mixed; 1 then 16). Complete orders and seeds are design.json.
Sequential target runs, no concurrent inference. Record both-cycle ordinary
and 10-second RSS, target CPU, metadata, every site's promotion/demotion counts,
and first 32 transition identities/monotonic times/allocation clocks per pair;
report any event truncation, never interpret missing events as none.

Primary endpoint: final-cycle ordinary idle RSS. Per cell report median and
min/max over ten runs. Pair each model-minus-rule and model-minus-neutral
RSS by repetition; estimator is median of the ten paired differences. Bootstrap
20000 resamples of the ten paired blocks, percentile 2.5/97.5 interval, Python
Random seed 110011 reset for each comparison. Report differences in MiB,
negative favors model; descriptive median wins and both-upper-bounds-below-zero
wins separately. Report for each gate/workload/thread the number out of six
namings beating both controls and number worse than mi. Also count namings
that win all four workload/thread conditions per gate. No pooling these
fixtures into independent applications or claiming calibrated probabilities.

Redis guard follow-up: normalized and retained unnormalized binaries x defaults
and immediate-purge x mi, key-only, static/site, static/context, hybrid/context,
live heuristic/context, neutral/context, names/context, TTL/context. Five
repetitions, randomized block order seed 111000 + naming_index*100 +
options_index*10 + repetition; explicit target CPU and metadata bytes, final
idle and 10-second RSS. Cold and coverage work excluded from warm groups.

Diagnostic: site-pure-1, 400000 objects, two cycles and identical 10-second
history for defaults and immediate purge, mi/oracle-site/static-model. Record
mimalloc's own reserved/committed/purged statistics at every phase. Separate
labelled runs for each policy/options invoke mi_collect(true) on the allocating
worker at each final idle10; these forced-collection runs are diagnostics,
never included in factorial or ordinary RSS groups. No claims about memory
being irreducible solely from passive waiting. Diagnostic statistics may
require a separately labelled MI_STAT-enabled allocator build.

Design SHA256: %s. No factorial result has been collected at declaration.
'''%(', '.join(FRAGMENTS),', '.join(VERBS),'\n'.join('- '+m['name']+': '+json.dumps({'functions':m['functions'],'contexts':m['contexts']},sort_keys=True) for m in d['mappings']),hashlib.sha256(body.encode()).hexdigest())
  with (ROOT/'CODEX-REPORT.md').open('a') as f:f.write(text)
  print(text)
if __name__=='__main__':main()
