#!/usr/bin/env python3
"""Check explicit benchmark intervals against server inference, on the remote host."""
import argparse,json,re,time,statistics,os,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('matrix',type=Path);p.add_argument('--runtime',type=Path,default=Path('results/interim-run1/vulkan-runtime.json'));p.add_argument('--server-log',type=Path,default=Path.home()/'jevalloc/model-server.log');a=p.parse_args()
x=json.loads(a.matrix.read_text());runtime=json.loads(a.runtime.read_text())
cmd=Path('/proc')/str(runtime['pid'])/'cmdline'
if not cmd.exists() or b'llama-server' not in cmd.read_bytes():raise SystemExit('Server process changed; refresh runtime/log anchor before audit')
# PID identity and the logger clock are different checks. /proc process start
# precedes common/log.cpp's system_clock-based logger origin by about 206 ms on
# this build. Calibrate the latter from adjacent release and LRU t_last entries:
# server-context.cpp writes t_last_used=ggml_time_us() (CLOCK_MONOTONIC) immediately
# after its release log. Use recent pairs to avoid wall/monotonic clock drift.
proc_start=int((Path('/proc')/str(runtime['pid'])/'stat').read_text().rsplit(')',1)[1].split()[19])/os.sysconf('SC_CLK_TCK')
boot=int(re.search(r'^btime (\d+)$',Path('/proc/stat').read_text(),re.M)[1])
if abs(boot+proc_start-runtime['process_start_unix'])>1:raise SystemExit('Server PID was reused; refresh runtime provenance')
lines=a.server_log.read_text(errors='replace').splitlines();last={};pairs=[]
def elapsed(line):
    m=re.match(r'^(\d+)\.(\d{2})\.(\d{3})\.(\d{3})\s',line)
    if not m:return None
    minute,second,ms,us=map(int,m.groups());return minute*60+second+ms/1000+us/1e6
for line in lines:
    stamp=elapsed(line);slot=re.search(r'id\s+(\d+)\s+\|',line)
    if stamp is None or not slot:continue
    sid=int(slot[1])
    if 'release:' in line:last[sid]=stamp
    used=re.search(r'selected slot by LRU, t_last = (\d+)',line)
    if used and sid in last:pairs.append(dict(log_release_seconds=last[sid],monotonic_release_seconds=int(used[1])/1e6))
if len(pairs)<3:raise SystemExit('No reliable logger calibration pairs; publication withheld')
before=time.time();mono=time.monotonic();after=time.time();offset=(before+after)/2-mono
recent=pairs[-10:];origins=[offset+p['monotonic_release_seconds']-p['log_release_seconds'] for p in recent]
spread=max(origins)-min(origins)
if spread>.01:raise SystemExit('Logger calibration spread exceeds 10 ms; inspect clocks')
anchor=statistics.median(origins)
calibration=dict(logger_start_unix=anchor,process_start_unix=runtime['process_start_unix'],spread_seconds=spread,wall_minus_monotonic=offset,pairs=recent,source='common/log.cpp t_us; tools/server/server-context.cpp release/t_last_used; ggml/src/ggml.c ggml_time_us')
active={};intervals=[]
for line in lines:
    stamp=re.match(r'^(\d+)\.(\d{2})\.(\d{3})\.(\d{3})\s',line);task=re.search(r'\| task\s+(\d+)\s+\|',line)
    if not stamp or not task:continue
    m,s,ms,us=map(int,stamp.groups());now=anchor+60*m+s+ms/1000+us/1e6;t=int(task[1])
    if 'launch_slot_' in line:active[t]=now
    elif 'release:' in line and t in active:intervals.append((active.pop(t),now,t))
intervals.extend((start,time.time(),t) for t,start in active.items())
rows=[]
for r in x['runs']:
    if r['repetition']<0:continue
    if 'started_unix' not in r:raise SystemExit('missing interval timestamps')
    overlaps=[t for start,end,t in intervals if start<r['finished_unix'] and end>r['started_unix']]
    rows.append(dict(benchmark=r['benchmark'],variant=r['variant'],repetition=r['repetition'],tasks=overlaps))
result=dict(matrix_sha256=hashlib.sha256(a.matrix.read_bytes()).hexdigest(),server_pid=runtime['pid'],source_log=str(a.server_log),checked=len(rows),overlapping_runs=sum(bool(r['tasks']) for r in rows),runs=rows,clock_calibration=calibration,clock_note='Explicit wall-clock benchmark intervals. Logger origin calibrated from recent paired wall-log/CLOCK_MONOTONIC release timestamps; PID start independently verified. Calibration is approximate at sub-millisecond logging granularity.')
a.matrix.with_suffix('.inference-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='runs'}))
raise SystemExit(bool(result['overlapping_runs']))
