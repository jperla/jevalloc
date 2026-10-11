#!/usr/bin/env python3
"""Symbolize normalized return PCs; attach +/-12 lines only from benchmark sources."""
import argparse, json, re, subprocess, sys
from pathlib import Path
from common import sites
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'third_party/mimalloc-bench/bench'

_CACHE={}

def symbolize(rows):
    cache=_CACHE
    for s in rows:
        for frame in s['frames']:
            key=(frame['image'],frame['address'])
            if key not in cache:
                image, address=key
                # Return PCs point after the call; subtract one for source attribution.
                addr=hex(int(address,16)-1)
                if sys.platform=='darwin':
                    cmd=['atos','-o',image,addr]
                else:
                    cmd=['addr2line','-f','-C','-e',image,addr]
                try:
                    text=subprocess.check_output(cmd,text=True,stderr=subprocess.DEVNULL).strip()
                except (OSError,subprocess.CalledProcessError): text='unresolved'
                info={'function':text,'file':None,'line':None,'source':[]}
                match=re.search(r'\(([^()]+):(\d+)\)\s*$',text) if sys.platform=='darwin' else re.search(r'\n(.+):(\d+)',text)
                if match:
                    filename,line=match.group(1),int(match.group(2));info['file']=filename;info['line']=line
                    info['function']=text.split(' (in ')[0] if sys.platform=='darwin' else text.splitlines()[0]
                    candidates=[Path(filename)] if Path(filename).is_absolute() else list(SOURCE.rglob(filename))
                    for path in candidates:
                        path=path.resolve()
                        if (SOURCE in path.parents or ROOT/'build/extras' in path.parents or ROOT/'fragbench' in path.parents) and path.is_file():
                            lines=path.read_text(errors='replace').splitlines()
                            info['file']=str(path.relative_to(ROOT))
                            info['source']=[{'line':i+1,'text':lines[i]} for i in range(max(0,line-21),min(len(lines),line+20))]
                            break
                cache[key]=info
            frame.update(cache[key])
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace');p.add_argument('-o','--output');a=p.parse_args()
    rows=symbolize(sites(a.trace));f=open(a.output,'w') if a.output else sys.stdout
    for s in rows: f.write(json.dumps(s)+'\n')
    if a.output:f.close()
if __name__=='__main__':main()
