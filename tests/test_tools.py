import sys, unittest, tempfile, json, urllib.error, io
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).resolve().parents[1]/'bench')]
import common, label, baselines, run, jevd
from types import SimpleNamespace
class Tools(unittest.TestCase):
    def test_majority_bytes(self):
        self.assertEqual(common.oracle({'class_bytes':[1,9,3]}),1)
        self.assertEqual(common.oracle({'class_bytes':[0,0,0]}),1)
    def test_no_runtime_leakage(self):
        s={'key':'DEADBEEF','program':'fixture','count':999,'bytes':888,'class_bytes':[7,8,9], 'frames':[{'image':'secret','address':'123','function':'func','file':'test.c','line':7,'source':[{'line':7,'text':'malloc(42);'}],'count':999}]}
        state=json.loads(label.state(s))
        self.assertEqual(set(state),{'program','stack'})
        self.assertEqual(set(state['stack'][0]),{'function','file','line','source'})
        a=label.request_body(s,'test');s.update(count=1,bytes=2,class_bytes=[0,0,100]);self.assertEqual(a,label.request_body(s,'test'))
    def test_billed_502_never_retried(self):
        error=urllib.error.HTTPError('url',502,'error',{'x-should-retry':'false'},io.BytesIO(b'billed'))
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            with patch('urllib.request.urlopen',side_effect=error) as mock:
                for _ in range(2):
                    with self.assertRaises(RuntimeError):label.decide({'model':'m'},Path(d),'https://example.invalid','key')
                self.assertEqual(mock.call_count,1)
    def test_baselines_ignore_lifetimes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            p=Path(d);trace=p/'trace';row={'key':'1','bytes':1024,'count':4,'class_bytes':[0,0,1024]};trace.write_text(json.dumps(row));baselines.generate(trace,p/'a');row['class_bytes']=[1024,0,0];trace.write_text(json.dumps(row));baselines.generate(trace,p/'b')
            for name in ('random','size','all-short','all-long'):self.assertEqual((p/'a'/f'{name}.txt').read_bytes(),(p/'b'/f'{name}.txt').read_bytes())
    def test_live_schedule_and_static_input(self):
        service=object.__new__(jevd.Decisions)
        service.a=SimpleNamespace(policy='heuristic',max_rechecks=4)
        counts=range(5)
        self.assertEqual([service.schedule(n) for n in counts],[1024,8192,65536,524288,0])
        request={'program':'p','frames':[],'site':{'allocs':999},'process':{'rss':777},'size':333,'prior':2}
        a=jevd.state(request,True);request['site']['allocs']=123;request['size']=111
        self.assertEqual(a,jevd.state(request,True))
        self.assertNotIn('999',a);self.assertNotIn('777',a);self.assertNotIn('333',a)
    def test_heuristic_ignores_process_state(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            args=SimpleNamespace(cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='heuristic',model='none',seed=1,max_rechecks=4)
            service=jevd.Decisions(args)
            hist=[0]*65;hist[23]=65536
            request={'key':'abc','prior':1,'site':{'life_hist':hist},'process':{'alloc_clock':1}}
            self.assertEqual(service.decide(request)['class'],1)
            request['process']['alloc_clock']=2**50
            self.assertEqual(service.decide(request)['class'],1)
            service.log.close()
    def test_probability_argmax(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            args=SimpleNamespace(cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='model',model='fake',seed=1,max_rechecks=4,reasoning=False,decide_url='http://localhost',decide_path='/v1/systemone',http_timeout=1)
            service=jevd.Decisions(args)
            response={'answers':{'lifetime':{'choice':'short','probabilities':{'short':.1,'medium':.2,'long':.7}}},'usage':{'input_tokens':10}}
            with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())):
                self.assertEqual(service.decide({'key':'abc','frames':[],'site':{'allocs':1}})['class'],2)
            service.log.close()
    def test_replay_fills_missing_model_answers(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            folder=Path(d);schedule=folder/'schedule.jsonl'
            request={'key':'abc','frames':[],'site':{'allocs':1},'prior':None}
            schedule.write_text(json.dumps({'request':request,'ordinal':0,'response':{'class':2,'recheck_after':1024},'raw_response':None})+'\n')
            args=SimpleNamespace(cache=d,log=str(folder/'fill.jsonl'),table=None,replay=str(schedule),fill_replay=True,policy='model',model='fake',seed=1,max_rechecks=4,reasoning=False,decide_url='http://localhost',decide_path='/v1/systemone',http_timeout=1)
            service=jevd.Decisions(args)
            response={'answers':{'lifetime':{'probabilities':{'short':.1,'medium':.8,'long':.1}}},'usage':{'input_tokens':10}}
            with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as http:
                self.assertEqual(service.decide(request)['class'],2)
                self.assertEqual(http.call_count,0)
                request={**request,'prior':2,'site':{'allocs':1024}}
                self.assertEqual(service.decide(request)['class'],1)
                self.assertEqual(http.call_count,1)
            service.log.close();run.merge_schedule(schedule,folder/'fill.jsonl')
            args.fill_replay=False;args.log=str(folder/'replay.jsonl');service=jevd.Decisions(args)
            with patch('urllib.request.urlopen',side_effect=AssertionError('model called during replay')):
                self.assertEqual(service.decide(request)['class'],2)
                self.assertEqual(service.decide(request)['class'],1)
            service.log.close()
    def test_model_budget_and_provenance(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            args=SimpleNamespace(cache=d,log=str(Path(d)/'log'),table=None,replay=None,policy='model',model='fake',seed=1,max_rechecks=4,reasoning=False,decide_url='http://localhost',decide_path='/v1/systemone',http_timeout=1,max_model_decisions=2,model_backend='vulkan',default_class=0)
            response={'answers':{'lifetime':{'probabilities':{'short':.1,'medium':.2,'long':.7}}}}
            request={'key':'a','frames':[],'site':{'allocs':1},'prior':None}
            service=jevd.Decisions(args)
            with patch('urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(json.dumps(response).encode())) as http:
                self.assertEqual(service.decide(request),{'class':2,'recheck_after':1024})
                self.assertEqual(service.decide({**request,'prior':2}),{'class':2,'recheck_after':0})
                self.assertEqual(service.decide({**request,'key':'b'}),{'class':0,'recheck_after':0})
                self.assertEqual(service.decide({**request,'prior':2}),{'class':2,'recheck_after':0})
                self.assertEqual(http.call_count,2)
            service.log.close()
            events=[json.loads(s) for s in Path(args.log).read_text().splitlines()]
            self.assertEqual([e['budget_exhausted'] for e in events],[False,False,True,True])
            self.assertEqual(events[0]['model_backend'],'vulkan')
            service=jevd.Decisions(args)
            with patch('urllib.request.urlopen',side_effect=AssertionError('cache should survive backend change')):
                args.model_backend='different'
                service.decide(request)
                service.decide({**request,'prior':2})
                self.assertEqual(service.decide({**request,'key':'b'})['class'],0)
            service.log.close()
            events=[json.loads(s) for s in Path(args.log).read_text().splitlines()]
            self.assertEqual(events[-3]['model_backend'],'vulkan')
            self.assertTrue(events[-3]['cache_hit'])
            # A zero budget neither symbolizes nor calls the model, and writes no fake cache entry.
            args.max_model_decisions=0;service=jevd.Decisions(args)
            with patch('jevd.state',side_effect=AssertionError('unnecessary symbolization')):
                self.assertEqual(service.decide(request),{'class':0,'recheck_after':0})
            service.log.close()

    def test_replay_fill_shares_model_budget(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'build') as d:
            folder=Path(d);schedule=folder/'schedule.jsonl'
            raw={'answers':{'lifetime':{'probabilities':{'short':.8,'medium':.1,'long':.1}}}}
            request={'key':'a','frames':[],'site':{'allocs':1},'prior':None}
            schedule.write_text(json.dumps({'request':request,'ordinal':0,'response':{'class':0,'recheck_after':1024},'raw_response':raw,'model_backend':'cpu','model_origin':'legacy'})+'\n')
            args=SimpleNamespace(cache=d,log=str(folder/'log'),table=None,replay=str(schedule),fill_replay=True,policy='model',model='fake',seed=1,max_rechecks=4,max_model_decisions=1)
            service=jevd.Decisions(args)
            with patch('urllib.request.urlopen',side_effect=AssertionError('reserved cold budget must prevent further inference')):
                # An unseen site can arrive before any recorded site.
                self.assertEqual(service.decide({**request,'key':'b'}),{'class':1,'recheck_after':0})
                self.assertEqual(service.decide(request),{'class':0,'recheck_after':1024})
                self.assertEqual(service.decide({**request,'prior':0}),{'class':0,'recheck_after':0})
            service.log.close()
            events=[json.loads(s) for s in Path(args.log).read_text().splitlines()]
            self.assertEqual(events[1]['model_backend'],'cpu')
            self.assertEqual(events[1]['model_origin'],'legacy')
            run.merge_schedule(schedule,folder/'log')
            self.assertEqual(sum(json.loads(s).get('raw_response') is not None for s in schedule.read_text().splitlines()),1)

    def test_time_parse(self):
        old=run.sys.platform
        try:
            run.sys.platform='darwin'
            d=run.parse_time(' 1.23 real 2.00 user 0.50 sys\n 2048 maximum resident set size\n 4096 peak memory footprint\n')
            self.assertEqual(d['cpu_seconds'],2.5);self.assertEqual(d['peak_footprint_bytes'],4096)
        finally:run.sys.platform=old
if __name__=='__main__':unittest.main()
