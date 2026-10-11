#!/usr/bin/env python3
"""Unix-socket lifetime decision service. Standard library only."""
import argparse, hashlib, json, math, os, socketserver, threading, time, urllib.request
from pathlib import Path
from common import CLASSES
from symbolize import symbolize

from prompts import criteria, state, canonical, fit_state, PROMPT_ID, QUESTION, question, PROMPTS
CRITERIA=criteria('v2')

class Decisions:
    def __init__(self,args):
        self.a=args;self.prompt=getattr(args,'prompt','stack-v1');self.lock=threading.Lock();self.ordinal={};self.first_class={};self.model_decisions=0
        self.max_model_decisions=getattr(args,"max_model_decisions",1500)
        self.cache=Path(args.cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.model_cache=Path(getattr(args,'model_cache',None) or self.cache);self.model_cache.mkdir(parents=True,exist_ok=True)
        self.log=open(args.log,'a',buffering=1)
        self.oracle={}
        if args.table:
            self.oracle={k:int(v) for k,v in (line.split() for line in Path(args.table).read_text().splitlines() if line.strip())}
        self.replay={}
        if args.replay:
            for line in Path(args.replay).read_text().splitlines():
                r=json.loads(line)
                if r.get('schema')!=4 or r.get('class_schema')!=PROMPT_ID or r.get('prompt')!=self.prompt:
                    self.log.close();raise ValueError('Replay prompt version mismatch')
                self.replay[(r['request']['key'],r['ordinal'])]=r
            # Reserve existing model slots: coverage fills share the cold budget.
            self.model_decisions=sum(e.get('raw_response') is not None for e in self.replay.values())
    def schedule(self,ordinal):
        if self.a.policy=='static-model' or ordinal>=self.a.max_rechecks:return 0
        return 1024*8**ordinal
    def decide(self,request):
        # Serialize model work, cache writes and the ordinal stream.
        arrival=time.monotonic()
        with self.lock:
            begin=time.monotonic();
            if request.get('site',{}).get('short_bytes',getattr(self.a,'short_bytes',1048576))!=getattr(self.a,'short_bytes',1048576): raise ValueError('short threshold mismatch')
            key=request['key'];ordinal=self.ordinal.get(key,0);self.ordinal[key]=ordinal+1
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
                cls=getattr(self.a,'default_class',0);recheck=0;missing=True
            elif model_policy and self.model_decisions>=self.max_model_decisions:
                cls=request.get('prior')
                if cls is None:cls=getattr(self.a,'default_class',0)
                recheck=0;budget_exhausted=True
            else:
                if self.a.policy in ('model','static-model'):
                    payload={'model':self.a.model,'state':state(request,self.a.policy=='static-model',self.prompt),'questions':{'lifetime':{'type':'choice','instructions':question(self.prompt),'criteria':criteria(self.prompt)}}}
                    payload['state']=fit_state(payload['state'],self.a.decide_url,self.a.http_timeout)
                    if self.a.reasoning:payload['reasoning']=True
                identity={'version':3,'class_schema':PROMPT_ID,'policy':self.a.policy,'model':self.a.model,'seed':self.a.seed,'max_rechecks':self.a.max_rechecks,'request':request,'payload':payload,'oracle':self.oracle.get(key)}
                if self.prompt!='v1':identity['prompt']=self.prompt
                digest=hashlib.sha256(canonical(identity).encode()).hexdigest();path=self.cache/(digest+'.json')
                if path.exists():
                    saved=json.loads(path.read_text());cls=saved['class'];raw=saved.get('raw_response');hit=True
                    backend=saved.get('model_backend','cpu' if raw else None);origin=saved.get('model_origin',path.name if raw else None)
                else:
                    if self.a.policy in ('model','static-model'):
                        headers={'Content-Type':'application/json'}
                        if os.environ.get('JEVALLOC_DECIDE_KEY'):headers['Authorization']='Bearer '+os.environ['JEVALLOC_DECIDE_KEY']
                        req=urllib.request.Request(self.a.decide_url.rstrip('/')+'/'+self.a.decide_path.lstrip('/'),data=canonical(payload).encode(),headers=headers)
                        model_identity={'class_schema':PROMPT_ID,'prompt':self.prompt,'payload':payload}
                        model_cache=self.model_cache/('model-'+hashlib.sha256(canonical(model_identity).encode()).hexdigest()+'.json')
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
                        if set(probabilities)!=set(CLASSES) or not all(math.isfinite(float(probabilities[c])) and float(probabilities[c])>=0 for c in CLASSES) or sum(float(probabilities[c]) for c in CLASSES)<=0:raise ValueError('invalid probabilities')
                        cls=max(range(2),key=lambda i:float(probabilities[CLASSES[i]]))
                    elif self.a.policy=='heuristic':
                        site=request.get('site',{})
                        older=site.get('older_sampled_bytes',0);freed=site.get('older_freed_bytes',0)
                        cls=int(site.get('cohort_count',0)>=16 and older>0 and 20*freed<older and 4*site.get('oldest_age_bytes',0)>request.get('process',{}).get('alloc_clock',0))
                    elif self.a.policy=='oracle':cls=self.oracle.get(key,0)
                    else:cls=int(hashlib.sha256(f'{self.a.seed}:{key}'.encode()).hexdigest(),16)%2
                    saved={'class':cls,'raw_response':raw,'model_backend':backend,'model_origin':origin};temp=path.with_suffix('.tmp');temp.write_text(canonical(saved));temp.replace(path)
            if model_policy and raw is not None and not replayed:
                if not model_seconds:self.model_decisions+=1
                if self.model_decisions>=self.max_model_decisions:recheck=0
            promotion_blocked=False
            # Preserve the first-sight label across cache hits and replay fills.
            # Replay executes the recorded policy, including the recorded guard.
            if ordinal==0:self.first_class[key]=cls
            if not replayed and raw is not None and self.a.policy=='model' and ordinal>0 and self.first_class.get(key)==0 and cls==1:
                probability=float(raw['answers']['lifetime']['probabilities']['permanent']) if raw else 0
                mature=4*request.get('site',{}).get('oldest_age_bytes',0)>request.get('process',{}).get('alloc_clock',0)
                if probability<0.8 or not mature:cls=0;promotion_blocked=True
            if cls not in (0,1): raise ValueError('class must be 0 or 1')
            response={'class':cls,'recheck_after':recheck}
            self.log.write(canonical({'schema':4,'promotion_blocked':promotion_blocked,'class_schema':PROMPT_ID,'prompt':self.prompt,'request':request,'ordinal':ordinal,'model_request':payload,'raw_response':raw,'response':response,'cache_hit':hit,'replayed':replayed,'request_drift':drift,'replay_missing':missing,'model_seconds':model_seconds,'cache_fill':filling,'budget_exhausted':budget_exhausted,'model_backend':backend,'model_origin':origin,'model_decisions_used':self.model_decisions,'max_model_decisions':self.max_model_decisions,'queue_seconds':begin-arrival,'latency_seconds':time.monotonic()-arrival,'usage':raw.get('usage',{}) if raw else {}})+'\n')
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
                self.server.decisions.log.write(canonical({'prompt':self.server.decisions.prompt,'error':str(e),'request_text':locals().get('line',b'').decode(errors='replace')})+'\n')
            # Closing the connection makes the allocator apply its fallback.

class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads=True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--socket',default=os.environ.get('JEVALLOC_SOCKET'),required=not bool(os.environ.get('JEVALLOC_SOCKET')))
    p.add_argument('--prompt',choices=PROMPTS,default='stack-v1')
    p.add_argument('--policy',choices=['model','static-model','heuristic','oracle','random'],default='model')
    p.add_argument('--model',default='clef-flash');p.add_argument('--decide-url',default='http://127.0.0.1:8765');p.add_argument('--decide-path',default='/v1/systemone')
    p.add_argument('--reasoning',action='store_true');p.add_argument('--max-rechecks',type=int,default=4);p.add_argument('--seed',type=int,default=1729)
    p.add_argument('--model-cache',help='Optional shared native two-class model payload cache; answers still consume the per-policy budget');p.add_argument('--cache',default='results/cache');p.add_argument('--log',default='results/decisions.jsonl');p.add_argument('--table');p.add_argument('--http-timeout',type=float,default=120);p.add_argument('--replay');p.add_argument('--fill-replay',action='store_true')
    p.add_argument('--max-model-decisions',type=int,default=1500,help='Model-backed answers per run, including cache hits, replay and rechecks; HTTP attempts also consume budget')
    p.add_argument('--default-class',type=int,choices=range(2),default=0)
    p.add_argument('--short-bytes',type=int,default=1048576)
    p.add_argument('--model-backend',default='vulkan')
    a=p.parse_args()
    if a.short_bytes<=0:p.error('short-bytes must be positive')
    if a.max_rechecks<0:p.error('max-rechecks must be nonnegative')
    if a.max_model_decisions<0:p.error('max-model-decisions must be nonnegative')
    decisions=Decisions(a)
    with Server(a.socket,Handler) as server:
        server.decisions=decisions
        try:server.serve_forever()
        finally:Path(a.socket).unlink(missing_ok=True)
if __name__=='__main__':main()
