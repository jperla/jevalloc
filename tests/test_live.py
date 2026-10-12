#!/usr/bin/env python3
"""Live protocol, scheduling, timeout and real-model smoke checks."""
import contextlib, json, os, socketserver, subprocess, sys, tempfile, threading, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import environment
from jevd import canonical

@contextlib.contextmanager
def fake(path, delay=0, silent=False,changing_to_short=False,invalid_class=False):
    requests=[]
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            req=json.loads(self.rfile.readline());requests.append(req)
            if silent:time.sleep(1);return
            time.sleep(delay)
            cls=(1 if req['prior'] is None else 0) if changing_to_short else len(requests)%2
            if invalid_class:cls=2
            try:self.wfile.write((canonical({'class':cls,'recheck_after':1024 if req['prior'] is None else 0})+'\n').encode())
            except BrokenPipeError:pass
    class Server(socketserver.ThreadingUnixStreamServer):daemon_threads=True
    server=Server(str(path),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield requests
    finally:server.shutdown();server.server_close();path.unlink(missing_ok=True)

def execute(path,sock,args=None,timeout=5000,sample_rate=8,min_site_bytes=0):
    env,extra=environment('jev-live:heuristic','',ROOT/'results/tables');env.update(extra)
    env.update(JEVALLOC_MIN_SITE_BYTES=str(min_site_bytes),JEVALLOC_MODE='live',JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(path),JEVALLOC_TIMEOUT_MS=str(timeout),JEVALLOC_SAMPLE=str(sample_rate))
    begin=time.monotonic();subprocess.run(args or [str(ROOT/'build/live-test')],env=env,check=True,stdout=subprocess.DEVNULL,timeout=120)
    return json.loads(path.read_text()),time.monotonic()-begin

def daemon(folder,policy,log,cache,extra=()):
    sock=folder/'jevd.sock';sock.unlink(missing_ok=True)
    p=subprocess.Popen([sys.executable,str(ROOT/'tools/jevd.py'),'--socket',str(sock),'--policy',policy,'--cache',str(cache),'--log',str(log),*extra],stdout=subprocess.DEVNULL)
    for _ in range(300):
        if sock.exists():return p,sock
        if p.poll() is not None:raise RuntimeError('jevd failed')
        time.sleep(.01)
    p.terminate();p.wait();raise RuntimeError('jevd startup timeout')

def main():
    report={}
    with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='live-') as name:
        folder=Path(name);stats=folder/'stats.json';sock=folder/'fake.sock'
        # Default admission must depend on successful requested bytes, not size
        # of the pending allocation or the number of allocation attempts.
        with fake(sock) as requests:
            data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'single'],min_site_bytes=65536)
            assert requests and all(r['site']['eligible_bytes']>=65536 for r in requests),requests
            assert any(n<65536 for n in data['site_bytes'].values()),data
            assert all(data['site_bytes'][r['key']]>=65536 for r in requests)
            report['byte_admission']=data
        with fake(sock) as requests:
            data,_=execute(stats,sock,[str(ROOT/'build/defects'),'failed-only'],sample_rate=1,min_site_bytes=65536)
            assert not any(r['size']==123 for r in requests),requests
            report['failed_allocations_never_eligible']=data
        with fake(sock,delay=.005) as requests:
            data,elapsed=execute(stats,sock)
            assert sum(data['site_bytes'].values())==data['allocation_clock'],data
            assert len(data['site_bytes'])==data['sites'],data
            assert data['failures']==0,data
            assert data['decisions']==len(requests),data
            assert data['rechecks']>0,data
            assert data['blocked_ns']>=data['decisions']*4_000_000,data
            report['delayed_changing_classes']={'stats':data,'wall_seconds':elapsed}
        with fake(sock):
            data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'environ'])
            assert data['failures']==0,data
            report['environment_storage_mutation']=data
        with fake(sock) as requests:
            data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'single'])
            assert any(r['site']['allocs']==1024 and r['prior'] is not None for r in requests),requests
            report['exact_single_thread_recheck']=data
        with fake(sock):
            data,_=execute(stats,sock,[str(ROOT/'build/stress')])
            assert data['failures']==0,data
            report['live_stress']=data
        with fake(sock):
            data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'destructors'],sample_rate=1)
            target=[key for key,n in data['site_bytes'].items() if n==4*12000*32]
            assert len(target)==1 and data['site_sampled_live'][target[0]]==0,data
            report['late_thread_destructor_frees']=data
        with fake(sock) as requests:
            data,_=execute(stats,sock,[str(ROOT/'build/defects'),'failed-only'],sample_rate=1)
            failed={r['key'] for r in requests if r['size']==123}
            assert len(failed)>=2,requests
            assert all(data['site_bytes'][key]==0 and data['site_sampled_live'][key]==0 for key in failed),data
            assert all(r['site']['allocs']==0 and r['prior'] is None for r in requests if r['key'] in failed),requests
            report['failed_allocation_accounting']=data
        with fake(sock,changing_to_short=True):
            data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'classes'])
            assert data['failures']==0 and data['rechecks']>0,data
            report['class_change_publication']=data
        with fake(sock,invalid_class=True):
            data,_=execute(stats,sock)
            assert data['failures']==1 and data['failure_errno']!=0,data
            report['reject_three_class_reply']=data
        with fake(sock,silent=True):
            data,elapsed=execute(stats,sock,timeout=50)
            assert data['timeouts']==1 and data['failures']==1 and elapsed<10,(data,elapsed)
            report['timeout']=data
        data,elapsed=execute(stats,sock,timeout=50);assert data['failures']==1 and elapsed<10
        report['unreachable']=data
        # Deterministic workload twice; heuristic evaluates current observations each time.
        logs=[]
        for i in range(2):
            log=folder/f'cache-{i}.jsonl';p,sock=daemon(folder,'heuristic',log,folder/'cache')
            try:data,_=execute(stats,sock,[str(ROOT/'build/bench/cfrac'),'17545186520507317056371138836327483792789528'])
            finally:p.terminate();p.wait()
            assert data['failures']==0,data
            logs.append([json.loads(line) for line in log.read_text().splitlines()])
        (ROOT/'results/live-cfrac-first.jsonl').write_text('\n'.join(canonical(r) for r in logs[0])+'\n')
        (ROOT/'results/live-cfrac-second.jsonl').write_text('\n'.join(canonical(r) for r in logs[1])+'\n')
        first=[canonical(r['request']) for r in logs[0]]
        second=[canonical(r['request']) for r in logs[1]]
        identical=first==second
        if sys.platform=='darwin':
            # macOS reports physical RSS; ASLR/page residency and timed purge can cross a quantization
            # boundary. Check deterministic allocator state separately, and retain
            # the complete requests plus the exact-cache coverage as evidence.
            def without_rss(rows):
                copy=json.loads(json.dumps([r['request'] for r in rows]))
                for r in copy:
                    r['process'].pop('rss',None);r['process'].pop('committed',None)
                return copy
            assert without_rss(logs[0])==without_rss(logs[1]),'allocator state differs'
            known=set(first)
            assert all(not r['replayed'] and not r['cache_hit'] for r in logs[1])
        else:
            assert identical,'cfrac requests differ'
            assert all(not r['replayed'] and not r['cache_hit'] for r in logs[1]),'heuristic was replayed/cached'
            assert [r['response'] for r in logs[0]]==[r['response'] for r in logs[1]]
        report['cfrac_byte_identical']=identical
        report['cfrac_cache_hits']=sum(r['cache_hit'] for r in logs[1])
        report['cfrac_requests']=len(logs[1])
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=2) as response:available=response.status==200
        except Exception:available=False
        if available:
            log=folder/'real.jsonl';p,sock=daemon(folder,'static-model',log,folder/'model-cache')
            try:data,_=execute(stats,sock,[str(ROOT/'build/live-test'),'single'],timeout=120000)
            finally:p.terminate();p.wait()
            rows=[json.loads(line) for line in log.read_text().splitlines()]
            assert data['failures']==0 and rows,data
            assert all('probabilities' in r['raw_response']['answers']['lifetime'] for r in rows)
            (ROOT/'results/model-smoke.jsonl').write_text(log.read_text());report['real_model']=data
        else:report['real_model']='SKIP: server absent'
    (ROOT/'results/live-tests.json').write_text(json.dumps(report,indent=2));print('LIVE TESTS PASSED',flush=True)
if __name__=='__main__':main()
