#!/usr/bin/env python3
"""Diagnostic only: invoke through bench/run.py --live-ablation for study gating."""
import argparse,json,sys,hashlib,threading,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
import run
p=argparse.ArgumentParser();p.add_argument('--mode',choices=('rare','profile','rss','peak-rss','filter-off'),required=True);p.add_argument('--benchmark',default='larson');p.add_argument('--reps',type=int,default=1);p.add_argument('--label',default='');a=p.parse_args()
name='diagnostic-'+a.mode+'-'+a.benchmark+('-'+a.label if a.label else '')
original=run.definitions
profile=ROOT/'results'/(name+'.pcs')
def definitions(procs):
    rows=original(procs)
    for r in rows:
        if a.mode=='rare':r['environment']={'JEVALLOC_SAMPLE':'1048576'}
        elif a.mode=='filter-off':r['environment']={'JEVALLOC_SAMPLE_FILTER':'0'}
        elif a.mode=='profile':r['environment']={'LD_PRELOAD':str(ROOT/'build/libjevalloc.so')+':'+str(ROOT/'build/profile-sampler.so'),'JEVALLOC_PROFILE_OUT':str(profile)}
    return rows
run.definitions=definitions
original_one=run.run_one
original_popen=run.subprocess.Popen
monitor_threads=[]
monitor_prefix=None
def monitor(proc,prefix):
    peak=0
    while proc.poll() is None:
        try:
            pid=proc.pid
            # /usr/bin/time -> measure -> benchmark (exec'd from /usr/bin/env).
            for _ in range(2):pid=int(Path(f'/proc/{pid}/task/{pid}/children').read_text().split()[0])
            status=Path(f'/proc/{pid}/status').read_text()
            current=int(re.search(r'^VmRSS:\s+(\d+)',status,re.M)[1])
            if current>peak:
                data=Path(f'/proc/{pid}/smaps').read_text();peak=current
                Path(str(prefix)+'.smaps').write_text(data)
                Path(str(prefix)+'.json').write_text(json.dumps(dict(pid=pid,rss_kib=current,unix=time.time())))
        except (OSError,IndexError,TypeError):pass
        time.sleep(.005)
def popen(*args,**kwargs):
    proc=original_popen(*args,**kwargs)
    if a.mode=='peak-rss' and args[0][0]=='/usr/bin/time':
        thread=threading.Thread(target=monitor,args=(proc,monitor_prefix),daemon=True);thread.start();monitor_threads.append(thread)
    return proc
run.subprocess.Popen=popen
def diagnostic_run(*args,**kwargs):
    global monitor_prefix
    monitor_prefix=ROOT/'results'/(name+'-'+args[1])
    if a.mode=='rss':
        row=dict(args[0]);row['environment']={'LD_PRELOAD':str(ROOT/'build/libjevalloc.so')+':'+str(ROOT/'build/rss-probe.so'),'JEVALLOC_SMAPS_OUT':str(ROOT/'results'/(name+'-'+args[1]+'.smaps'))}
        args=(row,*args[1:])
    result=original_one(*args,**kwargs)
    for thread in monitor_threads:thread.join(timeout=1)
    monitor_threads.clear();result['diagnostic']=True;return result
run.run_one=diagnostic_run
variants=['jev-none','jev-keyonly'] if a.mode in ('rss','peak-rss') else ['jev-live:heuristic'] if a.mode=='profile' else ['jev-table:oracle','jev-live:heuristic']
sys.argv=['bench/run.py','--name',name,'--benchmarks',a.benchmark,'--reps',str(a.reps),'--procs','16','--variants',*variants]
run.main()
path=ROOT/'results'/(name+'.json');data=json.loads(path.read_text())
data['diagnostic_fingerprints']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),ROOT/'tools/profile_sampler.c',ROOT/'build/profile-sampler.so',ROOT/'tools/rss_probe.c',ROOT/'build/rss-probe.so') if f.exists()}
data['diagnostic_note']='Profiling, RSS, or rare-sampling diagnostic; not acceptance or headline evidence.'
for row in data['runs']:row['diagnostic']=True
path.write_text(json.dumps(data,indent=2))
