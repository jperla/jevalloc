"""Per-allocation prompt, exact-request response caching, and replay safety."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from jevd import Decisions
from prompts import state

class Realtime(unittest.TestCase):
 def test_prompt(self):
  r={'program':'fixture','context':'ttl=day','per_alloc':True,'size':123,'frames':[{'function':'store','file':'fixture.c','line':1}]}
  s=state(r,True)
  self.assertIn('What the program is doing right now: ttl=day',s)
  self.assertIn('Requested allocation size: 123 bytes',s)
  self.assertNotIn('Observed so far',s)
 def test_requests(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=SimpleNamespace(prompt='stack-v1',cache=tmp,model_cache=tmp,log=tmp+'/log',table=None,replay=None,policy='per-alloc',max_rechecks=4,max_model_decisions=3000,model='clef-flash',seed=1729,short_bytes=1048576,decide_url='http://localhost:8765',decide_path='/v1/systemone',http_timeout=5,reasoning=False,model_backend='test')
   response={'answers':{'lifetime':{'probabilities':{'transient':.3,'permanent':.7}}}}
   class Reply:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(response).encode()
   r={'key':'1','program':'fixture','context':'ttl=day','per_alloc':True,'size':123,'frames':[],'site':{'allocs':64,'eligible_bytes':65536},'prior':None}
   with patch('jevd.fit_state',side_effect=lambda text,*_:text),patch('jevd.urllib.request.urlopen',return_value=Reply()) as http:
    d=Decisions(a)
    try:
     self.assertEqual(d.decide(r),{'class':1,'recheck_after':1,'per_allocation':1})
     second=copy.deepcopy(r);second['size']=124
     self.assertEqual(d.decide(second)['class'],1)
     third=copy.deepcopy(r);third['site']['allocs']=65
     d.decide(third)
     self.assertEqual(http.call_count,3) # no reuse by signature or identical prompt
     d.decide(r)
     self.assertEqual(http.call_count,3) # full exact request replay is free
     self.assertEqual(d.model_decisions,4)
    finally:d.log.close()
   a.replay=tmp+'/log';a.log=tmp+'/replay-log'
   d=Decisions(a)
   try:
    changed=copy.deepcopy(r);changed['size']=999
    with self.assertRaisesRegex(ValueError,'object mismatch'):d.decide(changed)
   finally:d.log.close()
if __name__=='__main__':unittest.main()
