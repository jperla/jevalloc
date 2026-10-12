#!/usr/bin/env python3
"""Sequential, interleaved allocator benchmark matrix. Oracle is a byte-majority site label from a prior trace."""
import urllib.request
import argparse, datetime, hashlib, json, os, platform, re, signal, statistics, subprocess, sys, time
from pathlib import Path
from definitions import ROOT, definitions
sys.path.insert(0,str(ROOT/'tools'))
from selection import accepted
LIVE_RULE_POLICIES = ('heuristic', 'rules-neutral', 'rule-names', 'rule-ttl')
DEFAULT_VARIANTS=['sys','mi','jev-none','jev-keyonly','jev-table:oracle','jev-table:random','jev-table:size','jev-table:all-transient','jev-table:all-permanent','jev-live:heuristic','jev-live:static-model','jev-live:hybrid']

def environment(variant, name, tables, mode='run', trace=None):
    env={k:v for k,v in os.environ.items() if not (k.startswith('JEVALLOC_') or k.startswith('MIMALLOC_') or k in ('DYLD_INSERT_LIBRARIES','LD_PRELOAD'))}
    extra={}
    if variant!='sys':
        lib=ROOT/'build'/({'mi':'libmimalloc','mesh':'libmesh','nomesh':'libnomesh'}.get(variant,'libjevalloc'))
        extra['DYLD_INSERT_LIBRARIES' if sys.platform=='darwin' else 'LD_PRELOAD']=str(lib)+('.dylib' if sys.platform=='darwin' else '.so')
    if variant.startswith('jev-'):
        extra['JEVALLOC_MODE']=mode
        if variant in ('jev-none','jev-keyonly','jev-explicit'):
            extra['JEVALLOC_POLICY']=variant[4:]
            if variant in ('jev-keyonly','jev-explicit'):extra['JEVALLOC_TABLE']=str(Path(tables).resolve()/name/'oracle.txt')
        elif variant.startswith('jev-table:'):extra['JEVALLOC_TABLE']=str(Path(tables).resolve()/name/(variant.split(':')[1]+'.txt'))
        elif variant.startswith('jev-live:'):extra['JEVALLOC_MODE']='live'
        elif variant.startswith('jev-model:'):extra['JEVALLOC_TABLE']=str(Path(variant.split(':',1)[1]).resolve())
        elif variant in ('jev-oracle','jev-random','jev-size'):extra['JEVALLOC_TABLE']=str(Path(tables).resolve()/name/(variant[4:]+'.txt'))
        if trace:extra['JEVALLOC_TRACE_OUT']=str(Path(trace).resolve())
    return env,extra

def parse_time(text):
    out={}
    if sys.platform=='darwin':
        m=re.search(r'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',text)
        if m:out.update(zip(('time_wall_seconds','user_seconds','sys_seconds'),map(float,m.groups())))
        for field,label in [('peak_rss_bytes','maximum resident set size'),('peak_footprint_bytes','peak memory footprint')]:
            m=re.search(r'(\d+)\s+'+label,text);out[field]=int(m[1]) if m else None
    else:
        for field,label in [('user_seconds','User time (seconds)'),('sys_seconds','System time (seconds)'),('peak_rss_bytes','Maximum resident set size (kbytes)')]:
            m=re.search(re.escape(label)+r':\s*([\d.]+)',text);out[field]=float(m[1]) if m else None
        if out.get('peak_rss_bytes') is not None:out['peak_rss_bytes']=int(out['peak_rss_bytes']*1024)
        out['peak_footprint_bytes']=None
    if out.get('user_seconds') is not None and out.get('sys_seconds') is not None:out['cpu_seconds']=out['user_seconds']+out['sys_seconds']
    return out

def score(name, output, wall):
    # Match bench.sh's useful-work metric for duration-limited workloads.
    if name.startswith('larson'):
        m=re.search(r'relative time:\s*([\d.]+)',output);return (float(m[1]),'relative_seconds') if m else (wall,'wall_seconds')
    if name=='xmalloc-test':
        m=re.search(r'rtime:\s*([\d.]+)',output);return (float(m[1]),'relative_seconds') if m else (wall,'wall_seconds')
    if name=='rptest':
        m=re.search(r'(\d+) memory ops/CPU second',output);return (2000000/int(m[1]),'relative_seconds') if m and int(m[1]) else (wall,'wall_seconds')
    if name=='glibc-thread':
        m=re.search(r'(\d+) iterations',output);return (1000000000/int(m[1]),'relative_seconds') if m and int(m[1]) else (wall,'wall_seconds')
    if name=='redis':
        values=re.findall(r'([\d.]+) requests per second',output)
        if values and float(values[-1]):return 2000000/float(values[-1]),'relative_seconds'
    return wall,'wall_seconds'

def schedule_path(row,variant,outdir):
    return Path(outdir)/(row['name']+'-'+hashlib.sha256(variant.encode()).hexdigest()[:8]+'.schedule.jsonl')

def merge_schedule(path,log):
    entries={}
    for source in (path,Path(log)):
        if not source.exists():continue
        for line in source.read_text().splitlines():
            event=json.loads(line)
            if 'response' in event and not event.get('replay_missing'):
                entries.setdefault((event['request']['key'],event['ordinal']),event)
    temp=path.with_suffix('.tmp')
    temp.write_text(''.join(json.dumps(entries[key],sort_keys=True,separators=(',',':'))+'\n' for key in sorted(entries)))
    temp.replace(path)

def wait_model_idle():
    """Drain an already-running prompt-study request after publishing the rep marker.

    The independent study sees that marker and stops submitting. Nothing is paused
    or killed. Missing /slots is recorded as unavailable, not an idle assertion.
    """
    deadline=time.monotonic()+300;quiet=None
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/slots',timeout=2) as response:slots=json.load(response)
        except OSError:return 'unavailable'
        if any(s.get('is_processing') for s in slots):quiet=None
        elif quiet is None:quiet=time.monotonic()
        elif time.monotonic()-quiet>=1:return 'idle-before-run'
        time.sleep(.2)
    raise RuntimeError('model server did not become idle after warm rep marker')

def run_one(row,variant,rep,outdir,tables,timeout=7200,mode='run',trace=None,attempt=0,max_model_decisions=3000):
    if rep<0:timeout=max(timeout,86400)
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    label='cold' if rep==-1 else (f'fill{-rep-2}' if rep<-1 else str(rep))
    tag=f"{row['name']}-{variant.split(':')[0]}-{label}"
    if ':' in variant:tag+='-'+hashlib.sha256(variant.encode()).hexdigest()[:8]
    if attempt:tag+=f'-attempt{attempt}'
    stdout=outdir/(tag+'.stdout');stderr=outdir/(tag+'.stderr');timing=outdir/(tag+'.time')
    env,extra=environment(variant,row['name'],tables,mode,trace)
    extra.update(row.get('environment',{}))
    if variant in ('jev-table:oracle-site','jev-live:static-site'):extra['JEVALLOC_CONTEXT']='0'
    cmd=[str(ROOT/'build/bench'/row['binary']),*row['args']]
    sidecar=None;decision_log=outdir/(tag+'.decisions.jsonl');stats=outdir/(tag+'.stats.json')
    if variant.startswith('jev-live:'):
        sock=ROOT/'build'/('jvd-'+hashlib.sha256(tag.encode()).hexdigest()[:12]+'.sock')
        sock.unlink(missing_ok=True);decision_log.unlink(missing_ok=True);stats.unlink(missing_ok=True)
        policy=variant.split(':')[1]
        if policy=='static-site':policy='static-model'
        if policy in ('hybrid','rules-neutral','rule-names','rule-ttl'):extra['JEVALLOC_HYBRID']='1'
        if policy=='per-alloc':extra['JEVALLOC_PER_ALLOC']='1'
        service=[sys.executable,str(ROOT/'tools/jevd.py'),'--socket',str(sock),'--policy',policy,'--prompt',row.get('prompt','stack-v1'),'--short-bytes',str(extra.get('JEVALLOC_SHORT_BYTES',1048576)),'--max-model-decisions',str(max_model_decisions),'--model-cache',str(row.get('model_cache',ROOT/'results/pass7/model-cache')),'--cache',str(outdir/'cache'/row['name']/policy),'--log',str(decision_log),'--table',str(Path(tables)/row['name']/'oracle.txt')]
        if len(variant.split(':'))>2:service+=['--model',variant.split(':',2)[2]]
        replay=schedule_path(row,variant,outdir)
        if rep!=-1 and policy not in LIVE_RULE_POLICIES:
            service+=['--replay',str(replay)]
            if rep<-1:service+=['--fill-replay']
        sidecar=subprocess.Popen(service,stdout=subprocess.DEVNULL,stderr=open(outdir/(tag+'.jevd.stderr'),'w'))
        for _ in range(1000):
            if sock.exists():break
            if sidecar.poll() is not None:raise RuntimeError('jevd failed to start')
            time.sleep(.01)
        else:sidecar.terminate();sidecar.wait();raise RuntimeError('jevd startup timeout')
        extra.update(JEVALLOC_SOCKET=str(sock),JEVALLOC_STATS_OUT=str(stats.resolve()),JEVALLOC_TIMEOUT_MS='600000')
    redis_socket=ROOT/'build/redis-bench.sock'
    if row['name']=='redis' or row.get('redis_driver'):
        redis_socket.unlink(missing_ok=True)
        cmd += ['--port','0','--unixsocket',str(redis_socket),'--save','','--appendonly','no']
    measure=outdir/(tag+'.measure.json')
    timed=['/usr/bin/time','-l' if sys.platform=='darwin' else '-v','-o',str(timing.resolve()),str(ROOT/'build/measure'),str(measure.resolve()),'/usr/bin/env',*[k+'='+v for k,v in extra.items()],*cmd]
    measure.unlink(missing_ok=True)
    host_before={'load_average':list(os.getloadavg())}
    if sys.platform=='linux':
        memory=Path('/proc/meminfo').read_text()
        for field in ('MemAvailable','SwapFree','SwapTotal'):
            match=re.search(r'^'+field+r':\s+(\d+)',memory,re.M)
            if match:host_before[field+'_bytes']=int(match[1])*1024
    inference_gate=wait_model_idle() if rep>=0 and mode=='run' and row.get('gate_inference') else 'not-requested'
    started_unix=time.time();start=time.monotonic()
    with open(row['stdin'] or os.devnull,'rb') as inp,open(stdout,'wb') as out,open(stderr,'wb') as err:
        process=subprocess.Popen(timed,cwd=outdir,env=env,stdin=inp,stdout=out,stderr=err,start_new_session=True)
        try:
            if row['name']=='redis' or row.get('redis_driver'):
                deadline=time.monotonic()+timeout
                while not redis_socket.exists():
                    if process.poll() is not None:raise RuntimeError('Redis server exited before readiness')
                    if time.monotonic()>deadline:raise subprocess.TimeoutExpired(cmd,timeout)
                    time.sleep(.05)
                cli=[str(ROOT/'build/bench/redis-cli'),'-s',str(redis_socket)]
                if row.get('redis_driver'):
                    subprocess.run([sys.executable,str(ROOT/'fragbench/redis_workload.py'),str(redis_socket),row['redis_driver']],env={**env,**{k:v for k,v in extra.items() if k.startswith('FRAG_')}},check=True,stdout=out,stderr=err,timeout=timeout)
                else:
                    time.sleep(1);subprocess.run([*cli,'flushall'],env=env,check=True,stdout=out,stderr=err,timeout=timeout)
                    time.sleep(1);subprocess.run([str(ROOT/'build/bench/redis-benchmark'),'-s',str(redis_socket),'-r','1000000','-n','100000','-q','-P','16','lpush','a','1','2','3','4','5','lrange','a','1','5'],env=env,check=True,stdout=out,stderr=err,timeout=timeout)
                    time.sleep(1);subprocess.run([*cli,'flushall'],env=env,check=True,stdout=out,stderr=err,timeout=timeout)
                    time.sleep(1);subprocess.run([*cli,'shutdown','nosave'],env=env,check=True,stdout=out,stderr=err,timeout=timeout)
            code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL)
            process.wait()
            code=124
        except BaseException:
            os.killpg(process.pid,signal.SIGKILL)
            process.wait()
            raise
        finally:
            if sidecar is not None:
                sidecar.terminate();sidecar.wait(timeout=10);sock.unlink(missing_ok=True)
    wall=time.monotonic()-start
    output=stdout.read_text(errors='replace');errors=stderr.read_text(errors='replace')
    expected=not row['expect'] or re.search(row['expect'],output) is not None
    clean=not re.search(r'memory corruption|assertion.*failed|mimalloc: error|ERROR:',errors,re.I)
    record={'inference_gate':inference_gate,'started_unix':started_unix,'finished_unix':time.time(),'host_before':host_before,'benchmark':row['name'],'variant':variant,'repetition':rep,'command':cmd,'stdin':row['stdin'],'environment':extra,'exit_status':code,'output_ok':bool(expected and clean),'wall_seconds':wall,'stdout':str(stdout.relative_to(ROOT)),'stderr':str(stderr.relative_to(ROOT))}
    record.update(parse_time(timing.read_text() if timing.exists() else ''))
    if measure.exists():
        record['time_exit_status']=code
        record.update(json.loads(measure.read_text()))
        code=record['exit_status']
        record['cpu_seconds']=record['user_seconds']+record['sys_seconds']
    record['score'],record['score_metric']=score(row['name'],output,record['wall_seconds'])
    record['phases']=[json.loads(line) for line in output.splitlines() if line.startswith('{"phase":')]
    if sidecar is not None:
        if not stats.exists():raise RuntimeError('missing live allocator stats: '+str(stats))
        record['allocator_stats']=json.loads(stats.read_text());record['blocked_seconds']=record['allocator_stats']['blocked_ns']/1e9
        record['chip_seconds']=record['wall_seconds']-record['blocked_seconds']
        record['chip_time_note']='Approximation: sums blocked intervals across threads; can be negative.'
        events=[json.loads(line) for line in decision_log.read_text().splitlines()]
        record['decision_log']=str(decision_log.relative_to(ROOT));record['cold']=rep==-1;record['coverage_fill']=rep<-1;record['replay_schedule']=str(replay.relative_to(ROOT))
        site_bytes=record['allocator_stats'].get('site_bytes',{})
        asked={e['request']['key'] for e in events if e.get('raw_response') is not None}
        unasked=set(site_bytes)-asked
        overflow_bytes=record['allocator_stats'].get('metadata',{}).get('overflow_bytes',0)
        record['model_coverage']={'sites':len(site_bytes),'asked_sites':len(asked & set(site_bytes)),
            'unasked_sites':len(unasked),'allocated_bytes':sum(site_bytes.values())+overflow_bytes,
            'untracked_overflow_bytes':overflow_bytes,
            'unasked_bytes':sum(site_bytes[k] for k in unasked)+overflow_bytes,
            'unasked_byte_share':(sum(site_bytes[k] for k in unasked)+overflow_bytes)/(sum(site_bytes.values())+overflow_bytes) if sum(site_bytes.values())+overflow_bytes else 0,
            'max_model_decisions':max_model_decisions,
            'budget_fallbacks':sum(bool(e.get('budget_exhausted')) for e in events)} if policy in ('model','model-reask','static-model','hybrid','per-alloc') else None
        record['decision_execution']='live-current-statistics' if policy in LIVE_RULE_POLICIES else ('cold' if rep==-1 else 'replay')
        record['cache_hits']=sum(bool(e.get('cache_hit')) for e in events)
        record['model_seconds']=sum(e.get('model_seconds',0) for e in events)
        record['input_tokens']=sum(e.get('usage',{}).get('input_tokens',0) for e in events if not e.get('cache_hit'))
        record['replay_drift']=sum(bool(e.get('request_drift')) for e in events)
        record['new_decisions']=sum(bool(e.get('cache_fill')) for e in events)
        record['replay_missing']=sum(bool(e.get('replay_missing')) for e in events)
        record['decision_errors']=sum('error' in e for e in events)
        record['dollars']=sum(e.get('usage',{}).get('dollars',0) for e in events if not e.get('cache_hit'))
        if record['allocator_stats']['failures'] or record['decision_errors']:raise RuntimeError('live decision failure: '+str(stats))
    if code or not expected or not clean:raise RuntimeError(f'{tag}: exit={code}, expected_output={expected}, clean={clean}; see {stdout}, {stderr}')
    if record.get('peak_rss_bytes') is None or record.get('cpu_seconds') is None:raise RuntimeError(f'Missing timing data: {timing}')
    return record

def summarize(records):
    groups={}
    for r in records:
        if accepted(r):groups.setdefault((r['benchmark'],r['variant']),[]).append(r)
    summary=[]
    for (b,v),runs in groups.items():
        row={'benchmark':b,'variant':v,'repetitions':len(runs),'score_metric':runs[0]['score_metric']}
        for metric in ('wall_seconds','user_seconds','sys_seconds','cpu_seconds','peak_rss_bytes','peak_footprint_bytes','score'):
            xs=[r[metric] for r in runs if r.get(metric) is not None]
            if xs:row[metric]={'median':statistics.median(xs),'min':min(xs),'max':max(xs)}
        summary.append(row)
    bases={s['benchmark']:s for s in summary if s['variant']=='mi'}
    for s in summary:
        if s['benchmark'] in bases:
            s['relative_to_mi']={m:s[m]['median']/bases[s['benchmark']][m]['median'] for m in ('wall_seconds','cpu_seconds','peak_rss_bytes','peak_footprint_bytes','score') if m in s and bases[s['benchmark']][m]['median']>0}
    return summary

def markdown(data):
    lines=['# '+data['name'],'','Oracle is fitted and evaluated on the same workload (prior-trace byte-majority site control). Model cold runs are reported separately; warm model policies replay decisions without HTTP inference. Heuristic and fixed rule controls evaluate current-run observations and do not replay decisions.','',
           'Ratios are variant / plain mimalloc; lower is better. Score follows bench.sh throughput normalization for larson, xmalloc-test, rptest, and glibc-thread; otherwise score is wall time. Wall and score are both recorded. RSS and footprint are bytes in JSON.','',
           '| Benchmark | Variant | Wall s median [min, max] | Score / mi | CPU s median [min, max] | CPU / mi | RSS MiB [min, max] | RSS / mi | Footprint MiB [min, max] |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for s in data['summary']:
        w=s['wall_seconds'];c=s['cpu_seconds'];r=s['peak_rss_bytes'];f=s.get('peak_footprint_bytes');rel=s.get('relative_to_mi',{})
        fmt=lambda v:f"{v['median']/1048576:.1f} [{v['min']/1048576:.1f}, {v['max']/1048576:.1f}]" if v else 'n/a'
        lines.append(f"| {s['benchmark']} | {s['variant']} | {w['median']:.3f} [{w['min']:.3f}, {w['max']:.3f}] | {rel.get('score',float('nan')):.3f} | {c['median']:.3f} [{c['min']:.3f}, {c['max']:.3f}] | {rel.get('cpu_seconds',float('nan')):.3f} | {fmt(r)} | {rel.get('peak_rss_bytes',float('nan')):.3f} | {fmt(f)} |")
    return '\n'.join(lines)+'\n'

def save(path,data):
    data['summary']=summarize(data['runs']);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(path);path.with_suffix('.md').write_text(markdown(data))

def prepare_replay(row,variant,outdir,tables,timeout,data,path,max_model_decisions=3000):
    if variant.split(':')[1] in LIVE_RULE_POLICIES:return
    replay=schedule_path(row,variant,outdir)
    for _ in range(12):
        index=sum(r.get('coverage_fill',False) and r['benchmark']==row['name'] and r['variant']==variant for r in data['coverage_runs'])
        print(f"{row['name']} {variant} CACHE FILL {index+1}",flush=True)
        result=run_one(row,variant,-2-index,outdir,tables,timeout,max_model_decisions=max_model_decisions)
        merge_schedule(replay,ROOT/result['decision_log'])
        data['coverage_runs'].append(result);save(path,data)
        if not result['new_decisions']:return
    raise RuntimeError('Replay coverage did not converge after 12 cache-fill runs')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prompt',choices=['stack-v1','stack-v1-nodesc','v2','v2-no-description','v2-runtime-only'],default='stack-v1');p.add_argument('--short-bytes',type=int,default=1048576);p.add_argument('--name',default='first-pass');p.add_argument('--reps',type=int,default=5);p.add_argument('--variants',nargs='+',default=DEFAULT_VARIANTS);p.add_argument('--benchmarks',nargs='+');p.add_argument('--tables',default=str(ROOT/'results/tables'));p.add_argument('--procs',type=int,default=8 if sys.platform=='darwin' else 16);p.add_argument('--timeout',type=int,default=7200);p.add_argument('--resume',action='store_true');p.add_argument('--allow-cold-upgrade',action='store_true',help='Adopt completed cold-only records across a runner/sidecar coverage change; preserve old code fingerprints');p.add_argument('--max-model-decisions',type=int,default=3000);a=p.parse_args()
    if a.max_model_decisions<0:p.error('max-model-decisions must be nonnegative')
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    signal.signal(signal.SIGINT,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    invalid=[v for v in a.variants if v not in DEFAULT_VARIANTS and not v.startswith(('jev-model:','jev-live:')) and v not in ('jev-oracle','jev-random','jev-size','jev-explicit')]
    if invalid:p.error('Unknown allocator variants: '+', '.join(invalid))
    path=ROOT/'results'/(a.name+'.json');path.parent.mkdir(exist_ok=True)
    rows=definitions(a.procs)
    for row in rows:row['gate_inference']=True;row['prompt']=a.prompt;row['environment']={'JEVALLOC_SHORT_BYTES':str(a.short_bytes)}
    if a.benchmarks:
        unknown=set(a.benchmarks)-{r['name'] for r in rows}
        if unknown:p.error('Unknown benchmarks: '+', '.join(sorted(unknown)))
        rows=[r for r in rows if r['name'] in a.benchmarks]
    if not rows or a.reps<1:p.error('No workloads or invalid repetitions')
    files={ROOT/'build/bench'/r['binary'] for r in rows}
    files.update(Path(r['stdin']) for r in rows if r['stdin'])
    for r in rows:
        _,extra=environment('jev-keyonly',r['name'],a.tables)
        for v in a.variants:
            _,extra=environment(v,r['name'],a.tables)
            if extra.get('JEVALLOC_TABLE'):files.add(Path(extra['JEVALLOC_TABLE']))
    files.update(ROOT/p for p in ('tools/common.py','tools/selection.py','tools/jevd.py','tools/prompts.py','tools/symbolize.py','bench/definitions.py','bench/run.py','build/measure'))
    if any(r['name']=='redis' for r in rows):files.update(ROOT/'build/bench'/p for p in ('redis-cli','redis-benchmark'))
    suffix='.dylib' if sys.platform=='darwin' else '.so'
    files.update((ROOT/'build'/('lib'+name+suffix)) for name in ('jevalloc','mimalloc'))
    files.update((ROOT/'descriptions').glob('*.txt'))
    fingerprint={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files)}
    configuration={'prompt':a.prompt,'class_schema':'transient-permanent-v1','short_bytes':a.short_bytes,'max_model_decisions':a.max_model_decisions,'repetitions':a.reps,'variants':a.variants,'workloads':[r['name'] for r in rows],'procs':a.procs,'fingerprints':fingerprint}
    data=json.loads(path.read_text()) if a.resume and path.exists() else {'name':a.name,'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'platform':platform.platform(),'processor_count':a.procs,'oracle':'prior-trace byte-majority site control','runs':[]}
    previous=data.get('configuration',configuration)
    if previous!=configuration:
        allowed={str(ROOT/'tools/jevd.py'),str(ROOT/'bench/run.py')}
        def stable(config):
            return {**config,'fingerprints':{k:v for k,v in config['fingerprints'].items() if k not in allowed}}
        if not (a.allow_cold_upgrade and all(r.get('cold') for r in data['runs']) and stable(previous)==stable(configuration)):
            p.error('Resume configuration or binary/table fingerprints changed')
        data['adopted_cold_code_provenance']=previous
    data.setdefault('coverage_runs',[])
    if (ROOT/'results/backend-transition.json').exists():data['backend_transition']=json.loads((ROOT/'results/backend-transition.json').read_text())
    data['configuration']=configuration
    done={(r['benchmark'],r['variant'],r['repetition']) for r in data['runs']}
    outdir=ROOT/'results/logs'/a.name
    for row in rows:
        for variant in a.variants:
            if not variant.startswith('jev-live:'):continue
            if (row['name'],variant,-1) not in done:
                print(f"{row['name']} {variant} COLD",flush=True)
                result=run_one(row,variant,-1,outdir,a.tables,a.timeout,max_model_decisions=a.max_model_decisions)
                data['runs'].append(result);save(path,data)
            cold=next(r for r in data['runs'] if r['benchmark']==row['name'] and r['variant']==variant and r.get('cold'))
            replay=schedule_path(row,variant,outdir)
            cold['replay_schedule']=str(replay.relative_to(ROOT))
            merge_schedule(replay,ROOT/cold['decision_log'])
            prepare_replay(row,variant,outdir,a.tables,a.timeout,data,path,a.max_model_decisions)
        for rep in range(a.reps):
            variants=a.variants[rep%len(a.variants):]+a.variants[:rep%len(a.variants)]
            for variant in variants:
                if (row['name'],variant,rep) in done:continue
                for attempt in range(6):
                    print(f"{row['name']} {variant} rep {rep+1}/{a.reps} attempt {attempt+1}",flush=True)
                    result=run_one(row,variant,rep,outdir,a.tables,a.timeout,attempt=attempt,max_model_decisions=a.max_model_decisions)
                    if not result.get('replay_missing'):break
                    result['coverage_probe']=True;data['coverage_runs'].append(result);save(path,data)
                    prepare_replay(row,variant,outdir,a.tables,a.timeout,data,path,a.max_model_decisions)
                else:raise RuntimeError('Replay still has unseen decision slots after six attempts')
                data['runs'].append(result);save(path,data)
    print(path)
if __name__=='__main__':
    if '--live-ablation' in sys.argv:
        sys.argv.remove('--live-ablation')
        import runpy
        runpy.run_path(str(ROOT/'tools/live_ablation.py'),run_name='__main__')
    elif '--fragbench' in sys.argv:
        sys.argv.remove('--fragbench')
        import runpy
        runpy.run_path(str(ROOT/'fragbench/run.py'),run_name='__main__')
    else:main()
