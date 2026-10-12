#!/usr/bin/env python3
"""Full workloads in trace and random-table run mode, plus targeted correctness."""
import argparse, json, os, subprocess, sys, time, hashlib, resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from definitions import definitions
from run import environment,run_one
from common import sites,oracle,write_table
from baselines import generate

def validate_trace(path):
    rows=sites(path);assert rows, path
    for s in rows:
        assert s['schema']==3 and s['class_schema']=='transient-permanent-v1',s
        assert sum(s['class_bytes'])==s['bytes'],s
        assert sum(s['fixed_s_class_bytes'])==s['bytes'],s
        p=s['permanent_bytes_by_percent']
        assert s['never_freed_bytes']<=p['90']<=p['50']<=p['25']<=s['bytes'],s
        assert s['class_bytes'][1]==p['50'],s
        assert sum(s['lifetime_histogram'])+s['never_freed']==s['count'],s
        assert sum(s['lifetime_histogram_bytes'])+s['never_freed_bytes']==s['bytes'],s
        assert len(s['frames'])<=16,s
    assert sum(s['bytes'] for s in rows)==rows[0]['total_allocation_bytes']
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--benchmarks',nargs='+');args=parser.parse_args()
    out=ROOT/'results';traces=out/'traces';traces.mkdir(parents=True,exist_ok=True)
    env,extra=environment('jev','',out/'tables');env.update(extra)
    # environment('jev') does not set run flags but loads jevalloc.
    subprocess.run([sys.executable,str(ROOT/'tests/test_tools.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_stack.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_pass4.py')],check=True)
    for policy in ('none','keyonly','segregate'):
        e=dict(env,JEVALLOC_POLICY=policy);subprocess.run([str(ROOT/'build/stress')],env=e,check=True)
    subprocess.run([str(ROOT/'build/defects')],env=env,check=True)
    for depth in (1,4,16):
        for policy in ('none','segregate'):
            e=dict(env,JEVALLOC_DEPTH=str(depth),JEVALLOC_POLICY=policy)
            a=subprocess.check_output([str(ROOT/'build/site-test')],env=e);b=subprocess.check_output([str(ROOT/'build/site-test')],env=e)
            assert a==b,(a,b);assert len(set(a.split()))==2
    # The table's narrow parser must retain full-width keys and reject overflow
    # or truncated rows without allowing malformed input to select a heap.
    fixture=out/'parser-fixture.txt'
    def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for text,valid in [('FFFFFFFFFFFFFFFF 1\n0x0000000000000001 00\n',True),
                       ('10000000000000000 0\n',False),('1 2\n',False),('ff',False)]:
        fixture.write_text(text)
        e=dict(env,JEVALLOC_POLICY='keyonly',JEVALLOC_TABLE=str(fixture))
        result=subprocess.run([str(ROOT/'build/site-test')],env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,preexec_fn=no_core)
        assert (result.returncode==0)==valid,(text,result.returncode)
    fixture.unlink()
    e=dict(env,JEVALLOC_MODE='trace',JEVALLOC_TRACE_OUT=str(out/'stress.jsonl'));subprocess.run([str(ROOT/'build/stress')],env=e,check=True);validate_trace(out/'stress.jsonl')
    stress_sites=sites(out/'stress.jsonl')
    for size in range(135791,135803):
        assert any(s['count']==1 and s['bytes']==size and s['never_freed']==0 for s in stress_sites),size
    e['JEVALLOC_TRACE_OUT']=str(out/'lifetimes.jsonl');subprocess.run([str(ROOT/'build/lifetimes')],env=e,check=True);ss=validate_trace(out/'lifetimes.jsonl')
    for size,cls in ((12345,0),(23456,0),(34567,1),(45678,1)):
        found=[s for s in ss if s['bytes']==size and s['count']==1];assert len(found)==1,(size,found);assert found[0]['class_bytes'][cls]==size,(size,found)
    for size,life in ((12345,0),(23456,2*1048576),(34567,4*1048576)):
        row=next(s for s in ss if s['bytes']==size and s['count']==1)
        for percent in (25,50,90):
            expected=size if life*100>row['total_allocation_bytes']*percent else 0
            assert row['permanent_bytes_by_percent'][str(percent)]==expected,row
    # Fixed-S control: strict boundary and arbitrary configured threshold.
    for threshold,expected in ((2*1048576,1),(2*1048576+1,0)):
        e['JEVALLOC_SHORT_BYTES']=str(threshold)
        subprocess.run([str(ROOT/'build/lifetimes')],env=e,check=True)
        found=next(s for s in validate_trace(out/'lifetimes.jsonl') if s['bytes']==23456 and s['count']==1)
        assert found['short_bytes']==threshold and found['fixed_s_class_bytes'][expected]==23456,found
    e.pop('JEVALLOC_SHORT_BYTES')
    report={'checks':['tools','stress none/keyonly/segregate/trace','site stability depth 1/4/16','exact lifetime boundaries'],'workloads':[]}
    if args.benchmarks and (out/'tests.json').exists():report=json.loads((out/'tests.json').read_text());report['passed']=False
    for row in definitions(8 if sys.platform=='darwin' else 16):
        if args.benchmarks and row['name'] not in args.benchmarks:continue
        name=row['name'];print(f'TRACE {name}',flush=True);path=traces/(name+'.jsonl')
        trace=run_one(row,'jev-trace',0,out/'logs/tests',out/'tables',mode='trace',trace=path)
        ss=validate_trace(path);dest=out/'tables'/name;generate(path,dest);write_table(dest/'oracle.txt',((s['key'],oracle(s)) for s in ss))
        print(f'RANDOM RUN {name} ({len(ss)} sites)',flush=True)
        run=run_one(row,'jev-random',0,out/'logs/tests',out/'tables')
        if name in ('cfrac','espresso'):
            # Deterministic textual outputs must agree across modes.
            assert (ROOT/trace['stdout']).read_bytes()==(ROOT/run['stdout']).read_bytes(),name
        report['workloads']=[r for r in report['workloads'] if r['name']!=name]
        report['workloads'].append({'name':name,'sites':len(ss),'trace':trace,'run':run})
        (out/'tests.json').write_text(json.dumps(report,indent=2))
    subprocess.run([str(ROOT/'build/hybrid-test')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_hybrid.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_combined.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_live_limits.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_review2.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_context.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_realtime_policy.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_headroom.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_hybrid_integration.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_live.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_permanent.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_replay.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/test_budget.py')],check=True)
    report['full_suite']=not bool(args.benchmarks)
    report['library_sha256']=hashlib.sha256((ROOT/'build'/('libjevalloc.dylib' if sys.platform=='darwin' else 'libjevalloc.so')).read_bytes()).hexdigest()
    report['passed']=True;(out/'tests.json').write_text(json.dumps(report,indent=2));print('ALL TESTS PASSED',flush=True)
if __name__=='__main__':main()
