#!/usr/bin/env python3
"""Unix-socket lifetime decision service. Standard library only."""
import argparse, hashlib, json, math, os, socketserver, threading, time, urllib.request
from pathlib import Path
from common import CLASSES
from symbolize import symbolize

CRITERIA={'short':'Freed before another 1 MiB is allocated.', 'medium':'Neither short nor long.', 'long':'Lives until exit or over half of total program allocation volume.'}
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'))

def state(request, static=False):
    frames=[dict(f,address=f.get('address',f.get('addr','0x0'))) for f in request.get('frames',[])]
    symbolize([{'frames':frames}])
    lines=['Program: '+request.get('program','unknown'), 'Stack:']
    for f in frames[:4]:lines.append(str(f.get('function','?')).split('\n')[0][:120])
    included=0
    for f in frames:
        if f.get('source') and included<2:
            center=f['line'];lines.append(f"{f['file']}:{center}")
            lines.extend(f"{s['line']}: {s['text'][:100]}" for s in f['source'] if abs(s['line']-center)<=6)
            included+=1
    code='\n'.join(lines)[:1200]
    if static:return code
    site=request.get('site',{});process=request.get('process',{})
    hist=','.join(f'{i}:{v}' for i,v in enumerate(site.get('life_hist',[])) if v) or 'empty'
    return (code+f"\nLive stats (powers of two; frees/live sampled): size={request.get('size')} prior={request.get('prior')} "
            + ' '.join(f'{k}={site.get(k,0)}' for k in ('allocs','frees','live','bytes'))
            + f" lifetime log2-byte buckets, shares /65536: {hist}\nProcess: "
            + ' '.join(f'{k}={v}' for k,v in process.items()))

class Decisions:
    def __init__(self,args):
        self.a=args;self.lock=threading.Lock();self.ordinal={};self.model_decisions=0
        self.max_model_decisions=getattr(args,"max_model_decisions",400)
        self.cache=Path(args.cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.log=open(args.log,'a',buffering=1)
        self.oracle={}
        if args.table:
            self.oracle={k:int(v) for k,v in (line.split() for line in Path(args.table).read_text().splitlines() if line.strip())}
        self.replay={}
        if args.replay:
            for line in Path(args.replay).read_text().splitlines():
                r=json.loads(line);self.replay[(r['request']['key'],r['ordinal'])]=r
            # Reserve existing model slots: coverage fills share the cold budget.
            self.model_decisions=sum(e.get('raw_response') is not None for e in self.replay.values())
    def schedule(self,ordinal):
        if self.a.policy=='static-model' or ordinal>=self.a.max_rechecks:return 0
        return 1024*8**ordinal
    def decide(self,request):
        # Serialize model work, cache writes and the ordinal stream.
        arrival=time.monotonic()
        with self.lock:
            begin=time.monotonic();key=request['key'];ordinal=self.ordinal.get(key,0);self.ordinal[key]=ordinal+1
            raw=None;model_seconds=0.;hit=False;replayed=False;drift=False;missing=False
            budget_exhausted=False;backend=None;origin=None
            model_policy=self.a.policy in ("model","static-model")
            recheck=self.schedule(ordinal)
            payload=None
            old=self.replay.get((key,ordinal)) if self.a.replay else None
            filling=bool(self.a.replay and old is None and getattr(self.a,'fill_replay',False))
            if old is not None:
                cls=old['response']['class'];recheck=old['response']['recheck_after'];raw=old.get('raw_response');hit=True;replayed=True
                drift=canonical(request)!=canonical(old['request'])
                budget_exhausted=old.get('budget_exhausted',False)
                backend=old.get('model_backend');origin=old.get('model_origin')
            elif self.a.replay and not filling:
                cls=getattr(self.a,'default_class',1);recheck=0;missing=True
            elif model_policy and self.model_decisions>=self.max_model_decisions:
                cls=request.get('prior')
                if cls is None:cls=getattr(self.a,'default_class',1)
                recheck=0;budget_exhausted=True
            else:
                if self.a.policy in ('model','static-model'):
                    payload={'model':self.a.model,'state':state(request,self.a.policy=='static-model'),'questions':{'lifetime':{'type':'choice','instructions':'Predict the lifetime of bytes allocated at this site. Choose long when short and long overlap.','criteria':CRITERIA}}}
                    if self.a.reasoning:payload['reasoning']=True
                identity={'version':1,'policy':self.a.policy,'model':self.a.model,'seed':self.a.seed,'max_rechecks':self.a.max_rechecks,'request':request,'payload':payload,'oracle':self.oracle.get(key)}
                digest=hashlib.sha256(canonical(identity).encode()).hexdigest();path=self.cache/(digest+'.json')
                if path.exists():
                    saved=json.loads(path.read_text());cls=saved['class'];raw=saved.get('raw_response');hit=True
                    backend=saved.get('model_backend','cpu' if raw else None);origin=saved.get('model_origin',path.name if raw else None)
                else:
                    if self.a.policy in ('model','static-model'):
                        headers={'Content-Type':'application/json'}
                        if os.environ.get('JEVALLOC_DECIDE_KEY'):headers['Authorization']='Bearer '+os.environ['JEVALLOC_DECIDE_KEY']
                        req=urllib.request.Request(self.a.decide_url.rstrip('/')+'/'+self.a.decide_path.lstrip('/'),data=canonical(payload).encode(),headers=headers)
                        model_cache=self.cache/('model-'+hashlib.sha256(canonical(payload).encode()).hexdigest()+'.json')
                        if model_cache.exists():
                            raw=json.loads(model_cache.read_text());hit=True
                            provenance=model_cache.with_suffix('.provenance.json')
                            meta=json.loads(provenance.read_text()) if provenance.exists() else {'backend':'cpu'}
                            backend=meta['backend'];origin=model_cache.name
                        else:
                            start=time.monotonic()
                            # Reserve before I/O so failed requests cannot exceed the budget.
                            self.model_decisions+=1
                            with urllib.request.urlopen(req,timeout=self.a.http_timeout) as response:raw=json.load(response)
                            model_seconds=time.monotonic()-start
                            temp=model_cache.with_suffix('.tmp');temp.write_text(canonical(raw));temp.replace(model_cache)
                            backend=getattr(self.a,'model_backend','unspecified');origin=model_cache.name
                            model_cache.with_suffix('.provenance.json').write_text(canonical({'backend':backend,'created_unix':time.time()}))
                        probabilities=raw['answers']['lifetime']['probabilities']
                        if not all(math.isfinite(float(probabilities[c])) and float(probabilities[c])>=0 for c in CLASSES):raise ValueError('invalid probabilities')
                        cls=max(range(3),key=lambda i:float(probabilities[CLASSES[i]]))
                    elif self.a.policy=='heuristic':
                        hist=request.get('site',{}).get('life_hist',[]);weights=[0,0,0]
                        for i,share in enumerate(hist):
                            life=0 if i==0 else 2**(i-1)
                            c=0 if life<1048576 else (1 if life<64*1048576 else 2)
                            weights[c]+=share
                        cls=max(range(3),key=lambda i:weights[i]) if request.get('prior') is not None and sum(weights) else 1
                    elif self.a.policy=='oracle':cls=self.oracle.get(key,1)
                    else:cls=int(hashlib.sha256(f'{self.a.seed}:{key}'.encode()).hexdigest(),16)%3
                    saved={'class':cls,'raw_response':raw,'model_backend':backend,'model_origin':origin};temp=path.with_suffix('.tmp');temp.write_text(canonical(saved));temp.replace(path)
            if model_policy and raw is not None and not replayed:
                if not model_seconds:self.model_decisions+=1
                if self.model_decisions>=self.max_model_decisions:recheck=0
            response={'class':cls,'recheck_after':recheck}
            self.log.write(canonical({'request':request,'ordinal':ordinal,'model_request':payload,'raw_response':raw,'response':response,'cache_hit':hit,'replayed':replayed,'request_drift':drift,'replay_missing':missing,'model_seconds':model_seconds,'cache_fill':filling,'budget_exhausted':budget_exhausted,'model_backend':backend,'model_origin':origin,'model_decisions_used':self.model_decisions,'max_model_decisions':self.max_model_decisions,'queue_seconds':begin-arrival,'latency_seconds':time.monotonic()-arrival,'usage':raw.get('usage',{}) if raw else {}})+'\n')
            return response

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            line=self.rfile.readline(65537)
            if len(line)>65536:raise ValueError('request too large')
            result=self.server.decisions.decide(json.loads(line))
            self.wfile.write((canonical(result)+'\n').encode())
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:
            with self.server.decisions.lock:
                self.server.decisions.log.write(canonical({'error':str(e),'request_text':locals().get('line',b'').decode(errors='replace')})+'\n')
            # Closing the connection makes the allocator apply its fallback.

class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads=True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--socket',default=os.environ.get('JEVALLOC_SOCKET'),required=not bool(os.environ.get('JEVALLOC_SOCKET')))
    p.add_argument('--policy',choices=['model','static-model','heuristic','oracle','random'],default='model')
    p.add_argument('--model',default='clef-flash');p.add_argument('--decide-url',default='http://127.0.0.1:8765');p.add_argument('--decide-path',default='/v1/systemone')
    p.add_argument('--reasoning',action='store_true');p.add_argument('--max-rechecks',type=int,default=4);p.add_argument('--seed',type=int,default=1729)
    p.add_argument('--cache',default='results/cache');p.add_argument('--log',default='results/decisions.jsonl');p.add_argument('--table');p.add_argument('--http-timeout',type=float,default=120);p.add_argument('--replay');p.add_argument('--fill-replay',action='store_true')
    p.add_argument('--max-model-decisions',type=int,default=400,help='Model-backed answers per run, including cache hits, replay and rechecks; HTTP attempts also consume budget')
    p.add_argument('--default-class',type=int,choices=range(3),default=1)
    p.add_argument('--model-backend',default='vulkan')
    a=p.parse_args()
    if a.max_rechecks<0:p.error('max-rechecks must be nonnegative')
    if a.max_model_decisions<0:p.error('max-model-decisions must be nonnegative')
    decisions=Decisions(a)
    with Server(a.socket,Handler) as server:
        server.decisions=decisions
        try:server.serve_forever()
        finally:Path(a.socket).unlink(missing_ok=True)
if __name__=='__main__':main()
