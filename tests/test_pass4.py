"""Acceptance selection and versioned-prompt regression checks."""
import io,json,sys,unittest,subprocess,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selection import complete_groups
import prompts
class Pass4(unittest.TestCase):
    def test_exact_warm_repetitions(self):
        rows=[dict(benchmark='b',variant=v,repetition=i,exit_status=0,output_ok=True) for v in ('mi','jev') for i in range(5)]
        data=dict(configuration=dict(workloads=['b'],variants=['mi','jev']),runs=rows)
        self.assertEqual(complete_groups(data)[1],['b'])
        data['runs']=rows+[dict(rows[0],repetition=-1,cold=True)]
        self.assertEqual(complete_groups(data)[1],['b'])
        data['runs']=rows+[dict(rows[0])]
        self.assertEqual(complete_groups(data)[1],[])
        data['runs']=[dict(r,decision_errors=1) if r is rows[-1] else r for r in rows]
        self.assertEqual(complete_groups(data)[1],[])
    def test_native_two_class_prompt(self):
        self.assertEqual(set(prompts.criteria('v2')),{'transient','permanent'})
        self.assertEqual(prompts.PROMPT_ID,'transient-permanent-v1')
        request=dict(program='fixture',frames=[],prior=1,site=dict(allocs=1024,short_share=70,long_freed_share=20,alive_share=10))
        self.assertIn('Freed quickly',prompts.state(request))
        self.assertNotIn('Observed so far',prompts.state(request,True))
    def test_v2_context_and_token_limit(self):
        frames=[dict(addr=hex(i+1),image='fixture',function=f'fn{i}',file='test.c',line=21,source=[dict(line=j,text='long_variable_name();'*10) for j in range(1,42)]) for i in range(12)]
        with patch('prompts.symbolize'):
            text=prompts.state(dict(program='fixture',frames=frames,prior=1,site=dict(allocs=1024,short_share=70,long_freed_share=20,alive_share=10)),prompt="v2")
        self.assertIn('fn11',text);self.assertEqual(text.count('>> 21:'),3)
        def token_response(req,**kw):
            text=json.loads(req.data)['content']
            return io.BytesIO(json.dumps({'tokens':list(range(len(text)//2))}).encode())
        with patch('urllib.request.urlopen',side_effect=token_response):
            fitted=prompts.fit_state(text,'http://localhost',1)
        self.assertLess(len(fitted)//2,3000);self.assertEqual(fitted.count('>> 21:'),3)
        self.assertIn('Not freed so far: about 10%',fitted)
    def test_heuristic_survival(self):
        self.assertEqual(len(prompts.criteria('v2')),2)
    def test_accuracy_requires_truth_for_every_decision(self):
        script=Path(__file__).resolve().parents[1]/'tools/live_accuracy.py'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);artifact=root/'fragbench';(artifact/'tables'/'b').mkdir(parents=True)
            (artifact/'tables'/'b'/'oracle.txt').write_text('1 0\n')
            log=artifact/'decisions.jsonl'
            event=dict(request=dict(key='1'),ordinal=0,response={'class':0})
            log.write_text(json.dumps(event)+'\n')
            matrix=dict(runs=[dict(cold=True,benchmark='b',variant='jev-live:model',decision_log='results/fragbench/decisions.jsonl')])
            (artifact/'matrix.json').write_text(json.dumps(matrix))
            cmd=[sys.executable,str(script),str(root),'--matrix','fragbench/matrix.json']
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            event['request']['key']='2';log.write_text(json.dumps(event)+'\n')
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('accuracy withheld',result.stderr)
if __name__=='__main__':unittest.main()
