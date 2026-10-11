"""Validate source attribution, TTL mixture, trace accounting and phase live bytes."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools'),str(ROOT/'tests')]
from run import run_one
from test import validate_trace
from symbolize import symbolize
from common import oracle
names={'parse_request_buffer','assemble_response_buffer','create_session_state','insert_cache_index'}
text=subprocess.check_output(['nm','-n',str(ROOT/'build/server-sim')],text=True)
addresses={line.split()[-1]:line.split()[0] for line in text.splitlines() if line.split() and line.split()[-1] in names}
assert set(addresses)==names and len(set(addresses.values()))==4,addresses
out=ROOT/'results/pass6/frag-validation';out.mkdir(parents=True,exist_ok=True)
report={'wrapper_addresses':addresses,'workloads':[]}
for tier in ('site-pure','site-mixed'):
 for threads in (1,16):
  name=f'{tier}-{threads}'
  row=dict(name=name,binary='../server-sim',args=[str(threads),tier,'400000','250'],stdin=None,expect='fragbench OK')
  trace=out/(name+'.jsonl');r=run_one(row,'jev-trace',0,out/'logs',out/'tables',mode='trace',trace=trace)
  ss=validate_trace(trace);symbolize(ss)
  for cycle in (0,1):
   phases={p['phase']:p for p in r['phases'] if p['cycle']==cycle}
   assert phases['idle']['live_bytes']==phases['drop']['live_bytes']<phases['peak']['live_bytes']
  if tier=='site-pure':
   seen={f['function'] for s in ss for f in s['frames']}
   assert names<=seen,(names,seen)
   for s in ss:
    functions={f['function'] for f in s['frames']}
    if functions & names:
     expected=int('insert_cache_index' in functions)
     assert oracle(s)==expected,(name,functions,s['class_bytes'])
  else:
   payload=[s for s in ss if any(f['function']=='store_request_payload' for f in s['frames'])]
   assert len(payload)==1,(name,'TTL choices must share one site',len(payload))
   for s in payload:
    share=s['fixed_s_class_bytes'][0]/s['bytes']
    assert .4<share<.6,(name,share)
    assert .03<s['never_freed_bytes']/s['bytes']<.07,s
  report['workloads'].append(dict(name=name,sites=len(ss),class_bytes=[sum(s['class_bytes'][i] for s in ss) for i in range(2)],oracle_correct_byte_share=sum(max(s['class_bytes']) for s in ss)/sum(s['bytes'] for s in ss)))
(out/'checks.json').write_text(json.dumps(report,indent=2));print('FRAGBENCH CORRECTNESS PASSED')
