#!/usr/bin/env python3
"""Label sites through TrustedRouter; never send observed trace statistics."""
import argparse, hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path
from common import CLASSES, sites, oracle, write_table

def state(site):
    # Explicit allowlist: do not serialize the site or frame dictionaries wholesale.
    return json.dumps({'program':site.get('program','unknown'),'stack':[
        {k:f.get(k) for k in ('function','file','line','source')} for f in site['frames']]},sort_keys=True)

def request_body(site, model, reasoning=False):
    body={'model':model,'state':state(site),'questions':{'lifetime':{
        'type':'choice','instructions':'Predict lifetime using only static program context. Time is cumulative bytes requested by the entire process. Choose the class accounting for most requested bytes at this site.',
        'criteria':{'short':'Typically freed before another 1 MiB is allocated.',
                    'medium':'Neither short nor long.',
                    'long':'Typically never freed, or lives for more than half of total program allocation volume.'}}}}
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('sites');p.add_argument('--model',required=True);p.add_argument('-o','--output',required=True);p.add_argument('--reasoning',action='store_true');p.add_argument('--cache',default=str(Path(__file__).resolve().parents[1]/'results/model-cache'));a=p.parse_args()
    cache=Path(a.cache);cache.mkdir(parents=True,exist_ok=True);rows=sites(a.sites);entries=[];matrix=[[0]*3 for _ in range(3)];raw=[]
    for s in rows:
        body=request_body(s,a.model,a.reasoning)
        response=decide(body,cache,os.environ.get('TR_BASE_URL','https://api.trustedrouter.com'),os.environ.get('TRUSTEDROUTER_API_KEY'))
        cls=CLASSES.index(response['answers']['lifetime']['choice']);entries.append((s['key'],cls));raw.append({'key':s['key'],'request':body,'response':response})
        matrix[oracle(s)][cls]+=1
    write_table(a.output,entries);Path(a.output+'.responses.json').write_text(json.dumps(raw,indent=2))
    print(f'Site accuracy vs same-run hindsight oracle: {sum(matrix[i][i] for i in range(3)) / max(1,len(rows)):.2%}')
    print('Confusion matrix: rows=oracle, columns=model; short, medium, long')
    for row in matrix:print(row)
if __name__=='__main__':main()
