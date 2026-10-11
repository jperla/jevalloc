#!/usr/bin/env python3
"""Label sites through TrustedRouter; never send observed trace statistics."""
import argparse, hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path
from prompts import question, criteria, PROMPTS, state as prompt_state
from common import CLASSES, sites, oracle, write_table

def state(site, prompt="stack-v1"):
    # The static prompt allowlists code context; no trace outcome fields are sent.
    return prompt_state(site,static=True,prompt=prompt)

def request_body(site, model, reasoning=False, prompt="stack-v1"):
    body={'model':model,'state':state(site,prompt),'questions':{'lifetime':{
        'type':'choice','instructions': question(prompt), 'criteria': criteria(prompt)}}}
    if reasoning: body['reasoning']=True
    return body

def decide(body, cache, base, api_key):
    encoded=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
    digest=hashlib.sha256(encoded).hexdigest()
    path=cache/(digest+'.json')
    if path.exists():
        record=json.loads(path.read_text())
        if 'error' in record: raise RuntimeError(f'Cached billed/error response: {path}; no retry')
        return record
    if not api_key: raise RuntimeError('TRUSTEDROUTER_API_KEY is required for an uncached request')
    req=urllib.request.Request(base.rstrip('/')+'/v1/decide',data=encoded,headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=180) as response: record=json.load(response)
            path.write_text(json.dumps(record,indent=2));return record
        except urllib.error.HTTPError as e:
            raw=e.read().decode(errors='replace')
            if e.code==502 and e.headers.get('x-should-retry','').lower()=='false':
                path.write_text(json.dumps({'error':raw,'status':502,'billed':True}));raise RuntimeError('Billed 502; cached and not retried') from e
            if e.code not in (429,500,502,503,504) or attempt==2: raise
            time.sleep(2**attempt)
    raise AssertionError('unreachable')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('sites');p.add_argument('--prompt',choices=PROMPTS,default='stack-v1');p.add_argument('--short-bytes',type=int,default=None);p.add_argument('--model',required=True);p.add_argument('-o','--output',required=True);p.add_argument('--reasoning',action='store_true');p.add_argument('--cache',default=str(Path(__file__).resolve().parents[1]/'results/model-cache'));a=p.parse_args()
    cache=Path(a.cache);cache.mkdir(parents=True,exist_ok=True);rows=sites(a.sites);entries=[];matrix=[[0]*2 for _ in range(2)];raw=[]
    for s in rows:
        body=request_body(s,a.model,a.reasoning,a.prompt)
        response=decide(body,cache,os.environ.get('TR_BASE_URL','https://api.trustedrouter.com'),os.environ.get('TRUSTEDROUTER_API_KEY'))
        cls=max(range(2),key=lambda i:response['answers']['lifetime']['probabilities'][CLASSES[i]]);entries.append((s['key'],cls));raw.append({'key':s['key'],'request':body,'response':response})
        matrix[oracle(s,a.short_bytes)][cls]+=1
    write_table(a.output,entries);Path(a.output+'.responses.json').write_text(json.dumps(raw,indent=2))
    print(f'Site accuracy vs same-run hindsight oracle: {sum(matrix[i][i] for i in range(2)) / max(1,len(rows)):.2%}')
    print('Confusion matrix: rows=oracle, columns=model; transient, permanent')
    for row in matrix:print(row)
if __name__=='__main__':main()
