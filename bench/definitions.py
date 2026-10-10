"""Upstream bench.sh workloads; Linux defaults to the Beelink's 16 threads."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'third_party/mimalloc-bench/bench'

def definitions(procs=None):
    if procs is None:procs=8 if sys.platform=='darwin' else 16
    rows=[]
    def add(name, binary, *args, stdin=None, expect=None):
        rows.append({'name':name,'binary':binary,'args':[str(x) for x in args], 'stdin':str(stdin) if stdin else None,'expect':expect})
    add('cfrac','cfrac','17545186520507317056371138836327483792789528',expect=r'17545186520507317056371138836327483792789528 = 856070387728264 \* 20495027946319472471219512627')
    add('espresso','espresso',SOURCE/'espresso/largest.espresso')
    add('barnes','barnes',stdin=SOURCE/'barnes/input',expect=r'COMPUTEEND')
    for name in ('larson','larson-sized'):
        add(name,name,5,8,1000,5000,100,4141,procs,expect=r'Throughput =\s*[0-9]+')
    add('xmalloc-test','xmalloc-test','-w',procs,'-t',5,'-s',64,expect=r'rtime:')
    for name in ('cache-scratch','cache-thrash'):
        add(name+'1',name,1,1000,1,2000000,procs)
        if procs!=1:add(name+'N',name,procs,1000,1,2000000,procs)
    add('mstress','mstress',procs,50,25,expect=rf'start with {procs} threads with a 50% load-per-thread and 25 iterations')
    add('rptest','rptest',procs,0,1,2,500,1000,100,8,16000,expect=r'memory ops/CPU second')
    add('glibc-simple','glibc-simple')
    add('glibc-thread','glibc-thread',procs,expect=r'[0-9]+ iterations')
    add('alloc-test1','alloc-test',1,expect=r'threads made [0-9]+ alloc/dealloc operations')
    if procs!=1:add('alloc-testN','alloc-test',min(procs,16),expect=r'threads made [0-9]+ alloc/dealloc operations')
    add('malloc-large','malloc-large')
    add('mleak10','mleak',5,expect=r'Using 10 threads with 100\*5 iterations')
    add('mleak100','mleak',50,expect=r'Using 10 threads with 100\*50 iterations')
    if sys.platform!='darwin':
        for name in ('sh6bench','sh8bench'):
            if (ROOT/'build/bench'/name).exists():add(name+'N',name,procs*2)
        if (ROOT/'build/bench/redis-server').exists():
            add('redis','redis-server',expect=r'requests per second')
    return rows
