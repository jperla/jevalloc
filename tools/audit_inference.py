#!/usr/bin/env python3
"""Check accepted headline intervals against actual llama-server inference intervals."""
import argparse, json, re, time
from pathlib import Path

def audit(directory, server_log):
    data=json.loads((directory/'beelink.json').read_text())
    runtime=json.loads((directory/'vulkan-runtime.json').read_text())
    # Linux /proc start ticks and boot time anchor the logger's elapsed timestamps.
    # Allow one second on each side for initialization and filesystem timestamp precision.
    anchor=runtime['process_start_unix'];margin=1.0
    starts={};intervals=[]
    for line in server_log.read_text(errors='replace').splitlines():
        stamp=re.match(r'^(\d+)\.(\d{2})\.(\d{3})\.(\d{3})\s',line)
        task=re.search(r'\| task\s+(\d+)\s+\|',line)
        if not stamp or not task:continue
        minute,second,milli,micro=map(int,stamp.groups())
        now=anchor+minute*60+second+milli/1000+micro/1e6;key=int(task[1])
        if 'launch_slot_' in line:starts[key]=now
        elif 'release:' in line and key in starts:intervals.append({'task':key,'start':starts.pop(key),'end':now})
    intervals.extend({'task':k,'start':v,'end':time.time()} for k,v in starts.items())
    checked=[]
    for r in data['runs']:
        if r['repetition']<0:continue
        measure=directory/Path(r['stdout']).relative_to('results').with_suffix('.measure.json')
        end=measure.stat().st_mtime;start=end-r['wall_seconds']
        overlaps=[i['task'] for i in intervals if i['start']-margin<end and i['end']+margin>start]
        checked.append({'benchmark':r['benchmark'],'variant':r['variant'],'repetition':r['repetition'],'start_unix':start,'end_unix':end,'overlapping_tasks':overlaps})
    result={'captured_unix':time.time(),'server_pid':runtime['pid'],'server_start_unix':anchor,'margin_seconds':margin,'method':'Benchmark child end = remote measure JSON mtime; start = end minus measured child wall. Model intervals = launch_slot/release log timestamps plus process start. One-second conservative margin. Run on the original remote filesystem before rsync.', 'inference_intervals':intervals,'headline_runs':checked,'overlapping_runs':sum(bool(r['overlapping_tasks']) for r in checked)}
    (directory/'inference-audit.json').write_text(json.dumps(result,indent=2))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',type=Path,default=Path('results'))
    p.add_argument('--server-log',type=Path,default=Path.home()/'jevalloc/model-server.log')
    a=p.parse_args();result=audit(a.results,a.server_log)
    print(json.dumps({'checked':len(result['headline_runs']),'overlapping_runs':result['overlapping_runs']}))
if __name__=='__main__':main()
