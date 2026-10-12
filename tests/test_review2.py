"""Review-2 controls: evaluate current statistics, fixed semantic rules, no model."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from jevd import Decisions, LIVE_RULE_POLICIES
class Review2(unittest.TestCase):
 def service(self,tmp,policy):
  return SimpleNamespace(prompt='stack-v1',cache=tmp,log=tmp+'/log',table=None,replay=None,policy=policy,model='none',seed=1729,max_rechecks=4)
 def test_live_heuristic(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=self.service(tmp,'heuristic');d=Decisions(a)
   r=dict(key='x',frames=[],site=dict(cohort_count=16,older_sampled_bytes=8192,older_freed_bytes=0,oldest_age_bytes=100),process=dict(alloc_clock=200))
   self.assertEqual(d.decide(r)['class'],1)
   changed=copy.deepcopy(r);changed['site']['older_freed_bytes']=8192
   self.assertEqual(d.decide(changed)['class'],0);d.log.close()
   for policy in LIVE_RULE_POLICIES:
    a.policy=policy;a.replay=tmp+'/log'
    with self.assertRaisesRegex(ValueError,'must not replay'):Decisions(a)
 def test_fixed_rules(self):
  for policy,fn,context,cls,prior in [('rules-neutral','cache','ttl=day',0,.5),('rule-names','insert_CACHE_index','',1,0.),('rule-names','conn_attach','ttl=day',0,1.),('rule-ttl','cache','ttl=day',1,0.),('rule-ttl','cache','class=c',0,1.)]:
   with self.subTest(policy=policy,fn=fn,context=context), tempfile.TemporaryDirectory() as tmp:
    d=Decisions(self.service(tmp,policy))
    with patch('jevd.symbolize',side_effect=lambda rows:rows),patch('jevd.urllib.request.urlopen',side_effect=AssertionError('model forbidden')):
     answer=d.decide(dict(key='x',frames=[dict(function=fn)],context=context))
    self.assertEqual(answer,{'class':cls,'recheck_after':0,'prior_transient':prior,'prior_permanent':1-prior})
    self.assertEqual(d.model_decisions,0);d.log.close()
if __name__=='__main__':unittest.main()
