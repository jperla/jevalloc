#!/usr/bin/env python3
"""Replace headline blocks that overlapped inference; retain every excluded record."""
import hashlib, json, os, shutil, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bench'),str(ROOT/'tools')]
from run import DEFAULT_VARIANTS, run_one, save, prepare_replay
from definitions import definitions
from audit_inference import audit

def main():
    directory=ROOT/'results';status=directory/'bench.status'
    while not status.exists():time.sleep(60)
    if status.read_text().strip()!='0':raise SystemExit('Main matrix failed; refusing repair')
    interference=json.loads((directory/'interference.json').read_text())
    external=Path(f"/proc/{interference['external_pid']}/stat")
    while external.exists():
        try:
            if external.read_text().rsplit(')',1)[1].split()[0]=='Z':break
        except FileNotFoundError:break
        print('Waiting for external prompt study to finish',flush=True);time.sleep(60)
    path=directory/'beelink.json';data=json.loads(path.read_text());config=data['configuration']
    for name,digest in config['fingerprints'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise SystemExit('Fingerprint changed: '+name)
    rows={r['name']:r for r in definitions(config['procs'])}
    data.setdefault('excluded_interference_runs',[])
    for generation in range(3):
        result=audit(directory,ROOT.parent/'model-server.log')
        (directory/f'inference-audit-before-repair-{generation}.json').write_text(json.dumps(result,indent=2))
        affected={r['benchmark'] for r in result['headline_runs'] if r['overlapping_tasks']}
        if not affected:break
        print('Replace complete interleaved blocks: '+', '.join(sorted(affected)),flush=True)
        original=[r for r in data['runs'] if r['repetition']>=0 and r['benchmark'] in affected]
        data['excluded_interference_runs'].extend(original)
        for name in config['workloads']:
            if name not in affected:continue
            row=rows[name]
            for rep in range(config['repetitions']):
                variants=config['variants'][rep%len(config['variants']):]+config['variants'][:rep%len(config['variants'])]
                for variant in variants:
                    print(f'Replacement {name} {variant} repetition {rep+1}',flush=True)
                    for attempt in range(6):
                        r=run_one(row,variant,rep,directory/'logs'/data['name'],directory/'tables',attempt=100+generation*10+attempt,max_model_decisions=config['max_model_decisions'])
                        if not r.get('replay_missing'):break
                        r['coverage_probe']=True;data['coverage_runs'].append(r);save(path,data)
                        prepare_replay(row,variant,directory/'logs'/data['name'],directory/'tables',7200,data,path,config['max_model_decisions'])
                    else:raise RuntimeError('Replacement replay did not converge')
                    data['runs']=[old for old in data['runs'] if (old['benchmark'],old['variant'],old['repetition'])!=(name,variant,rep)]
                    r['replaces_interference']=True;data['runs'].append(r);save(path,data)
    result=audit(directory,ROOT.parent/'model-server.log')
    if result['overlapping_runs']:raise SystemExit('Inference still overlaps headline measurements')
    interference.update(resolved=True,resolved_unix=time.time(),replaced_runs=len(data['excluded_interference_runs']),accepted_headline_runs=len(result['headline_runs']))
    (directory/'interference.json').write_text(json.dumps(interference,indent=2))
    (directory/'excluded-interference.json').write_text(json.dumps(data['excluded_interference_runs'],indent=2))
    shutil.copy2(ROOT.parent/'model-server.log',directory/'model-server-vulkan.log')
    print('Inference audit clean; excluded records and original logs retained',flush=True)
if __name__=='__main__':main()
