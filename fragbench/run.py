#!/usr/bin/env python3
"""Trace, validate the instrument, then run the interleaved fragmentation matrix."""
import argparse, hashlib, json, signal, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import run_one,save,merge_schedule,schedule_path,prepare_replay,DEFAULT_VARIANTS
from common import sites,oracle,write_table
from baselines import generate
from selection import complete_groups
OPTIONS={'MIMALLOC_PURGE_DELAY':'0','MIMALLOC_ARENA_PURGE_MULT':'1','MIMALLOC_PURGE_DECOMMITS':'1','JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12'}
def definitions():
    rows=[]
    for tier in ('site-pure','site-mixed'):
        for n in (1,16):rows.append(dict(name=f'{tier}-{n}',binary='../server-sim',args=[str(n),tier,'400000','250'],stdin=None,expect='fragbench OK',environment=OPTIONS))
    for mode in ('mesh','drop'):rows.append(dict(name='redis-'+mode,binary='redis-server',args=['--activedefrag','no'],stdin=None,expect='fragbench OK',redis_driver=mode,environment=OPTIONS))
    for row in rows:row['gate_inference']=True
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--benchmarks',nargs='+');p.add_argument('--max-model-decisions',type=int,default=1500);p.add_argument('--instrument',action='store_true');p.add_argument('--sensitivity',action='store_true');p.add_argument('--allow-negative-instrument',action='store_true',help='Continue after investigating a measured negative instrument; keep its failure visible');p.add_argument('--prompt',choices=['stack-v1','stack-v1-nodesc','v2','v2-no-description','v2-runtime-only'],default='stack-v1');p.add_argument('--short-bytes',type=int,default=1048576);p.add_argument('--resume',action='store_true');p.add_argument('--name',default='fragbench');p.add_argument('--reps',type=int,default=5);p.add_argument('--variants',nargs='+',default=DEFAULT_VARIANTS);a=p.parse_args()
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    out=ROOT/'results'/a.name;out.mkdir(parents=True,exist_ok=True);tables=out/'tables';logs=out/'logs';path=out/'matrix.json'
    rows=definitions()
    if a.benchmarks:
        if set(a.benchmarks)-{r['name'] for r in rows}:p.error('Unknown benchmarks')
        rows=[r for r in rows if r['name'] in a.benchmarks]
    for row in rows:row['prompt']=a.prompt;row['environment']={**OPTIONS,'JEVALLOC_SHORT_BYTES':str(a.short_bytes)}
    if a.instrument or a.sensitivity:rows=[r for r in rows if r['name'].startswith('site-pure')]
    binary_sha=hashlib.sha256((ROOT/'build/server-sim').read_bytes()).hexdigest()
    if not a.instrument and not a.sensitivity:
        gate=json.loads((ROOT/'results/frag-instrument/gate.json').read_text())
        if gate.get('class_schema')!='transient-permanent-v1' or gate.get('server_sha256')!=binary_sha or gate.get('environment')!=OPTIONS or gate.get('short_bytes')!=a.short_bytes:raise SystemExit('instrument workload/options changed')
        if not gate['passed'] and not a.allow_negative_instrument:raise SystemExit('instrument gate failed; investigate before explicitly continuing')
        if gate['library_sha256']!=hashlib.sha256((ROOT/'build/libjevalloc.so').read_bytes()).hexdigest():raise SystemExit('instrument gate belongs to another library')
    variants=['mi','jev-keyonly','jev-table:oracle','jev-table:random'] if a.instrument else (['mi','jev-table:oracle-P-25','jev-table:oracle','jev-table:oracle-P-90','jev-table:oracle-P-never','jev-table:oracle-S-65536','jev-table:oracle-S-1048576','jev-table:oracle-S-16777216'] if a.sensitivity else a.variants)
    files=['build/server-sim','build/bench/redis-server','build/libjevalloc.so','build/libmimalloc.so','build/measure','bench/run.py','fragbench/run.py','fragbench/redis_workload.py','tools/common.py','tools/baselines.py','tools/selection.py','tools/jevd.py','tools/prompts.py','tools/symbolize.py']
    files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'descriptions').glob('*.txt'))]
    fingerprints={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    configuration=dict(variants=variants,repetitions=a.reps,workloads=[r['name'] for r in rows],environment=OPTIONS,negative_instrument_accepted=a.allow_negative_instrument,class_schema="transient-permanent-v1",short_bytes=a.short_bytes,permanent_thresholds=[25,50,90,"never"],fixed_s_thresholds=[65536,1048576,16777216],prompt=a.prompt,key_depth=4,model_depth=12,max_model_decisions=a.max_model_decisions,fingerprints=fingerprints)
    data=json.loads(path.read_text()) if a.resume and path.exists() else dict(name=a.name,runs=[],coverage_runs=[],configuration=configuration)
    if data['configuration']!=configuration:raise SystemExit('Resume inputs or fingerprints changed')
    if a.instrument:(out/'gate.json').unlink(missing_ok=True)
    for row in rows:
        name=row['name'];trace=out/(name+'.trace.jsonl')
        if not (a.resume and trace.exists()):
            print(name,'TRACE',flush=True)
            run_one(row,'jev-trace',0,logs,tables,mode='trace',trace=trace)
            ss=sites(trace);generate(trace,tables/name);write_table(tables/name/'oracle.txt',[(s['key'],oracle(s)) for s in ss])
            for threshold in (65536,1048576,16777216):write_table(tables/name/f'oracle-S-{threshold}.txt',[(s['key'],oracle(s,threshold)) for s in ss])
            for threshold in (25,50,90,'never'):write_table(tables/name/f'oracle-P-{threshold}.txt',[(s['key'],oracle(s,permanent_percent=threshold)) for s in ss])
            (out/(name+'.truth.json')).write_text(json.dumps(dict(sites=len(ss),class_bytes=[sum(s['class_bytes'][i] for s in ss) for i in range(2)],oracle_correct_byte_share=sum(max(s['class_bytes']) for s in ss)/sum(s['bytes'] for s in ss)),indent=2))
        for v in variants:
            if not v.startswith('jev-live:'):continue
            if not any(r['benchmark']==name and r['variant']==v and r['repetition']==-1 for r in data['runs']):
                print(name,v,'COLD',flush=True);r=run_one(row,v,-1,logs,tables,max_model_decisions=a.max_model_decisions);data['runs'].append(r);save(path,data)
            if any(not any(r['benchmark']==name and r['variant']==v and r['repetition']==rep for r in data['runs']) for rep in range(a.reps)):
                cold=next(r for r in data['runs'] if r['benchmark']==name and r['variant']==v and r['repetition']==-1)
                merge_schedule(schedule_path(row,v,logs),ROOT/cold['decision_log'])
                prepare_replay(row,v,logs,tables,7200,data,path,a.max_model_decisions)
        for rep in range(a.reps):
            for v in variants[rep%len(variants):]+variants[:rep%len(variants)]:
                if any(r['benchmark']==name and r['variant']==v and r['repetition']==rep for r in data['runs']):continue
                for attempt in range(6):
                    print(name,v,f'rep {rep+1}/{a.reps} attempt {attempt+1}',flush=True)
                    r=run_one(row,v,rep,logs,tables,attempt=attempt,max_model_decisions=a.max_model_decisions)
                    if not r.get('replay_missing'):break
                    r['coverage_probe']=True;data['coverage_runs'].append(r);save(path,data);prepare_replay(row,v,logs,tables,7200,data,path,a.max_model_decisions)
                else:raise RuntimeError('Replay coverage did not converge')
                if not r['phases']:raise RuntimeError('Missing phase measurements')
                data['runs'].append(r);save(path,data)
    if a.instrument:
        groups,complete=complete_groups(data)
        if len(complete)!=len(rows):raise SystemExit("Instrument needs five accepted observations for every variant/workload")
        comparisons=[]
        for row in rows:
            for cycle in (0,1):
                def median(v):
                    values=[]
                    for r in groups[row['name'],v]:
                        phases=[p for p in r['phases'] if p['phase']=='idle' and p['cycle']==cycle]
                        if len(phases)!=1:raise SystemExit('Instrument needs one idle phase per cycle and repetition')
                        values.append(phases[0]['rss_bytes'])
                    return statistics.median(values)
                comparisons.append(dict(workload=row['name'],cycle=cycle,oracle=median('jev-table:oracle'),keyonly=median('jev-keyonly'),mi=median('mi'),random=median('jev-table:random')))
        gate=dict(class_schema="transient-permanent-v1",short_bytes=a.short_bytes,passed=a.reps==5 and all(c['oracle']<c['keyonly'] and c['oracle']<c['mi']*.5 and c['oracle']<=c['random'] for c in comparisons),server_sha256=binary_sha,environment=OPTIONS,repetitions=a.reps,comparisons=comparisons,library_sha256=hashlib.sha256((ROOT/'build/libjevalloc.so').read_bytes()).hexdigest())
        (out/'gate.json').write_text(json.dumps(gate,indent=2));print(json.dumps(gate),flush=True)
        if gate.get('class_schema')!='transient-permanent-v1' or gate.get('server_sha256')!=binary_sha or gate.get('environment')!=OPTIONS or gate.get('short_bytes')!=a.short_bytes:raise SystemExit('instrument workload/options changed')
        if not gate['passed']:raise SystemExit('Instrument FAIL; investigate before matrix')
if __name__=='__main__':main()
