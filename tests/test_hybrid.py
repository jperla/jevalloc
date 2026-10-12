"""The hybrid protocol keeps the code-only prior through caches and replay."""
import io,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import jevd
class Hybrid(unittest.TestCase):
 def test_prior_cache_and_replay(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'build') as d:
   args=SimpleNamespace(prompt='stack-v1',cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='hybrid',model='fake',seed=1,max_rechecks=4,reasoning=False,decide_url='http://localhost',decide_path='/v1/systemone',http_timeout=1)
   request=dict(key='session',program='test',frames=[],prior=None,site=dict(eligible_bytes=65536),process=dict(alloc_clock=100))
   raw=dict(answers=dict(lifetime=dict(probabilities=dict(transient=.9,permanent=.1))))
   for cached in (False,True):
    service=jevd.Decisions(args)
    with patch('jevd.fit_state',side_effect=lambda s,*a:s),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(raw).encode())) as http:
     result=service.decide(request)
     self.assertEqual(result,{'class':0,'recheck_after':0,'prior_transient':.9,'prior_permanent':.1})
     self.assertEqual(http.call_count,0 if cached else 1)
    service.log.close()
   args.replay=args.log;args.log=str(Path(d)/'replayed')
   service=jevd.Decisions(args)
   with patch('urllib.request.urlopen',side_effect=AssertionError('replay called model')):
    self.assertEqual(service.decide(request),result)
   service.log.close()
if __name__=='__main__':unittest.main()
