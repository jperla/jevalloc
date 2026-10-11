#!/usr/bin/env python3
"""Deterministic RESP client. Mesh PLDI'19 §6.3 sizes/counts, and peak/drop.

Mesh source: https://raw.githubusercontent.com/plasma-umass/Mesh/master/mesh-pldi19-powers.pdf
Adaptation: fixed work rather than a 7.5-second wall deadline; active defrag disabled.
"""
import concurrent.futures, json, os, random, socket, sys, time
from pathlib import Path
class Redis:
    def __init__(self,path):
        self.s=socket.socket(socket.AF_UNIX);self.s.settimeout(86400);self.s.connect(path);self.f=self.s.makefile('rb')
    def read(self):
        line=self.f.readline();kind=line[:1];value=line[1:-2]
        if kind==b'-':raise RuntimeError(value.decode())
        if kind in (b'+',b':'):return value
        if kind==b'$':
            n=int(value)
            if n<0:return None
            value=self.f.read(n);assert self.f.read(2)==b'\r\n';return value
        if kind==b'*':return [self.read() for _ in range(int(value))]
        raise RuntimeError('invalid RESP '+repr(line))
    def pipeline(self,commands):
        commands=list(commands)
        chunks=[]
        for args in commands:
            args=[x if isinstance(x,bytes) else str(x).encode() for x in args]
            chunks.append(b'*'+str(len(args)).encode()+b'\r\n'+b''.join(b'$'+str(len(x)).encode()+b'\r\n'+x+b'\r\n' for x in args))
        self.s.sendall(b''.join(chunks));return [self.read() for _ in commands]
    def cmd(self,*args):return self.pipeline([args])[0]
    def close(self):self.f.close();self.s.close()
def info(client,section):
    return dict(line.split(':',1) for line in client.cmd('INFO',section).decode().splitlines() if ':' in line)
def main():
    path,mode=sys.argv[1:3];client=Redis(path)
    client.cmd('CONFIG','SET','activedefrag','no')
    pid=int(info(client,'server')['process_id'])
    def measure(phase,cycle=0):
        time.sleep(.5);m=info(client,'memory');rss=int(Path(f'/proc/{pid}/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE');live=int(m['used_memory'])
        print(json.dumps(dict(phase=phase,cycle=cycle,rss_bytes=rss,live_bytes=live,used_memory_rss=int(m['used_memory_rss']),fragmentation_ratio=rss/live,live_metric='Redis used_memory (includes allocator usable sizes and metadata)')),flush=True)
    rng=random.Random(1729)
    if mode=='mesh':
        client.cmd('CONFIG','SET','maxmemory','100mb');client.cmd('CONFIG','SET','maxmemory-policy','allkeys-lru')
        for cycle,(count,size) in enumerate(((700000,240),(170000,492))):
            for begin in range(0,count,1000):client.pipeline(('SET',f'{cycle}:{rng.getrandbits(64):016x}',b'x'*size) for _ in range(min(1000,count-begin)))
            measure('idle',cycle)
    else:
        client.cmd('CONFIG','SET','maxmemory','0')
        # Sixteen clients create large request buffers while the keyspace grows.
        def load(worker):
            c=Redis(path)
            try:
                for start in range(worker*10000,(worker+1)*10000,256):
                    c.pipeline(('SET',f'k{i}',b'x'*(1024+(i%4)*256)) for i in range(start,min(start+256,(worker+1)*10000)))
            finally:c.close()
        with concurrent.futures.ThreadPoolExecutor(16) as pool:list(pool.map(load,range(16)))
        measure('peak');keys=list(range(160000));rng.shuffle(keys)
        for i in range(0,144000,1000):client.pipeline(('DEL',f'k{k}') for k in keys[i:min(i+1000,144000)])
        measure('drop');measure('idle')
    print('fragbench OK',flush=True)
    # Shutdown closes the connection without a reply on some Redis versions.
    try:client.cmd('SHUTDOWN','NOSAVE')
    except RuntimeError:pass
    client.close()
if __name__=='__main__':main()
