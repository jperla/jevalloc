#!/usr/bin/env python3
"""Native two-class prompt study, using fresh trace truth and a separate cache.

Historical three-class studies remain archived. This tool does not convert them.
"""
import argparse,collections,hashlib,json,random,time,urllib.request
from pathlib import Path
from common import sites,oracle,class_bytes,CLASSES
from prompts import state,criteria,QUESTION,PROMPT_ID,fit_state,canonical

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--traces',type=Path,required=True);p.add_argument('--workloads',required=True)
    p.add_argument('--per-class',type=int,default=15);p.add_argument('--short-bytes',type=int,default=1048576,help='Quick-free observation threshold, not oracle truth')
    p.add_argument('--variants',default='v2,v2-with-runtime,v2-no-description,v2-runtime-only')
    p.add_argument('--url',default='http://127.0.0.1:8765');p.add_argument('--model',default='clef-flash')
    p.add_argument('--out',type=Path,required=True);p.add_argument('--cache',type=Path,default=Path('results/permanent-prompt-cache'))
    p.add_argument('--gate',type=Path);a=p.parse_args();a.cache.mkdir(parents=True,exist_ok=True)
    rng=random.Random(1729);sample=[]
    for workload in a.workloads.split(','):
        rows=sites(a.traces/(workload+'.jsonl'))
        for cls in range(2):
            candidates=[s for s in rows if oracle(s)==cls]
            sample.extend(rng.sample(candidates,min(a.per_class,len(candidates))))
    results=[]
    for variant in a.variants.split(','):
        for s in sample:
            while a.gate and a.gate.exists() and ' rep ' in a.gate.read_text().splitlines()[-1]:time.sleep(1)
            weights=class_bytes(s,a.short_bytes);total=max(1,s['bytes']);alive=s['never_freed_bytes']
            request=dict(program=s['program'],key=s['key'],frames=s['frames'],prior=1,site=dict(allocs=s['count'],short_bytes=a.short_bytes,short_share=round(100*weights[0]/total),long_freed_share=round(100*(weights[1]-alive)/total),alive_share=round(100*alive/total)))
            text=state(request,static=variant not in ('v2-with-runtime','v2-runtime-only'),prompt=variant)
            payload=dict(model=a.model,state=fit_state(text,a.url,120),questions=dict(lifetime=dict(type='choice',instructions=QUESTION,criteria=criteria(variant))))
            identity=dict(schema=PROMPT_ID,variant=variant,payload=payload)
            path=a.cache/(hashlib.sha256(canonical(identity).encode()).hexdigest()+'.json')
            if path.exists():raw=json.loads(path.read_text())
            else:
                req=urllib.request.Request(a.url+'/v1/systemone',data=canonical(payload).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=120) as response:raw=json.load(response)
                path.write_text(canonical(raw))
            probs=raw['answers']['lifetime']['probabilities'];pred=max(CLASSES,key=probs.__getitem__)
            results.append(dict(schema=3,class_schema=PROMPT_ID,variant=variant,key=s['key'],program=s['program'],short_bytes=a.short_bytes,truth=CLASSES[oracle(s)],pred=pred,probs=probs,request=payload,raw=raw))
            a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(results,indent=2))
        rows=[r for r in results if r['variant']==variant]
        print(variant,len(rows),sum(r['truth']==r['pred'] for r in rows)/max(1,len(rows)),flush=True)
if __name__=='__main__':main()
