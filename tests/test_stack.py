"""Prompt contract and transient promotion boundary, including cached/replayed answers."""
import io,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import prompts,jevd
class Stack(unittest.TestCase):
    def test_prompt_contract(self):
        r=dict(program='server-sim',frames=[dict(function='create_session_state',file='server.c',line=42,source=[dict(line=42,text='SECRET SOURCE')])]*15,prior=None,site=dict(allocs=4096,alive_share=100,oldest_age_bytes=300000))
        for variant in ('stack-v1','stack-v1-nodesc'):
            text=prompts.state(r,prompt=variant)
            self.assertEqual(text.count('  create_session_state  (server.c:42)'),12)
            self.assertNotIn('SECRET',text);self.assertNotIn('Observed',text)
            self.assertEqual('About the program:' in text,variant=='stack-v1')
            observed=prompts.state({**r,'prior':0},prompt=variant)
            self.assertIn('another 300,000 bytes.',observed)
            self.assertIn('Nothing from this site has been freed yet',observed)
            self.assertEqual(text,prompts.state({**r,'prior':0},static=True,prompt=variant))
        self.assertEqual(prompts.question('stack-v1'),'The marked lines lead to a heap allocation. Will this object be freed while the program is still running?')
    def test_promotion_boundaries_and_cache(self):
        for probability,age,expected in ((.79,26,0),(.8,25,0),(.8,26,1)):
            with tempfile.TemporaryDirectory(dir=ROOT/'build') as d:
                args=SimpleNamespace(prompt='stack-v1',cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='model',model='fake',seed=1,max_rechecks=4,reasoning=False,decide_url='http://localhost',decide_path='/v1/systemone',http_timeout=1)
                first=dict(key='session',program='test',frames=[],prior=None,site=dict(eligible_bytes=65536),process=dict(alloc_clock=100))
                second={**first,'prior':0,'site':dict(oldest_age_bytes=age)}
                for cached in (False,True):
                    responses=[dict(answers=dict(lifetime=dict(probabilities=dict(transient=.9,permanent=.1)))),dict(answers=dict(lifetime=dict(probabilities=dict(transient=1-probability,permanent=probability))))]
                    service=jevd.Decisions(args)
                    with patch('jevd.fit_state',side_effect=lambda s,*a:s),patch('urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(json.dumps(responses.pop(0)).encode())) as http:
                        self.assertEqual(service.decide(first)['class'],0)
                        self.assertEqual(service.decide(second)['class'],expected)
                        self.assertEqual(http.call_count,0 if cached else 2)
                    service.log.close()
    def test_heuristic_age_and_free_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as d:
            args=SimpleNamespace(prompt='stack-v1',cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='heuristic',model='none',seed=1,max_rechecks=4)
            service=jevd.Decisions(args)
            for age,freed,expected in ((25,0,0),(26,0,1),(26,50,0)):
                r=dict(key='cohort',site=dict(cohort_count=128,older_sampled_bytes=1000,older_freed_bytes=freed,oldest_age_bytes=age),process=dict(alloc_clock=100))
                self.assertEqual(service.decide(r)['class'],expected)
            service.log.close()
if __name__=='__main__':unittest.main()
