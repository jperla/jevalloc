#!/usr/bin/env python3
"""Capture reproducibility metadata without modifying git or the host."""
import hashlib,json,platform,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def command(*args):
    try:return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT).strip()
    except Exception as e:return str(e)
def main():
    model=ROOT.parents[0]/'models/Clef-Flash-Q8_0.gguf'
    data={'platform':platform.platform(),'machine':platform.machine(),'cpu':command('lscpu'),'compiler':command('cc','--version'),'python':platform.python_version(),'mimalloc':command('git','-C',str(ROOT/'third_party/mimalloc'),'rev-parse','HEAD'),'bench':command('git','-C',str(ROOT/'third_party/mimalloc-bench'),'rev-parse','HEAD'),'llama':command('git','-C',str(ROOT.parent/'llama.cpp'),'rev-parse','HEAD'),'model_path':str(model),'model_bytes':model.stat().st_size if model.exists() else None,'model_invocation':(ROOT/'scripts/model-server.sh').read_text()}
    if model.exists():
        digest=hashlib.sha256()
        with model.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
        data['model_sha256']=digest.hexdigest()
    # The sync intentionally excludes .git; preserve source-checkout revisions.
    data['dependency_source_revisions']=json.loads((ROOT/'tools/dependency-revisions.json').read_text())
    data['sources']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ('src','tools','bench','tests','scripts') for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    (ROOT/'results/provenance-beelink.json').write_text(json.dumps(data,indent=2))
if __name__=='__main__':main()
