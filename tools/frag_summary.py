#!/usr/bin/env python3
"""Phase metrics and paired oracle/model comparisons; accepted complete blocks only."""
import argparse,json,statistics
from pathlib import Path
from selection import complete_groups
p=argparse.ArgumentParser();p.add_argument('matrix');a=p.parse_args();data=json.loads(Path(a.matrix).read_text());g,bs=complete_groups(data)
print('# Fragmentation results\n\nWarm medians [min, max] of five interleaved repetitions. RSS uses the final idle point; all phase measurements remain in JSON. Time includes the common settle period.\n')
print('| Workload | Variant | Idle RSS MiB | Live MiB | RSS/live | Peak MiB | Time s | CPU s | RSS/mi | Time/mi |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
def metrics(rows):
    idle=[max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p['cycle']) for r in rows]
    med=lambda xs:statistics.median(xs)
    return dict(cpu=med(r['cpu_seconds'] for r in rows),rss_min=min(p['rss_bytes'] for p in idle),rss_max=max(p['rss_bytes'] for p in idle),time_min=min(r['wall_seconds'] for r in rows),time_max=max(r['wall_seconds'] for r in rows),rss=med(p['rss_bytes'] for p in idle),live=med(p['live_bytes'] for p in idle),ratio=med(p['fragmentation_ratio'] for p in idle),peak=med(r['peak_rss_bytes'] for r in rows),time=med(r['wall_seconds'] for r in rows))
for b in bs:
    m={v:metrics(g[b,v]) for v in data['configuration']['variants']};base=m['mi']
    for v,x in m.items():print(f"| {b} | {v} | {x['rss']/2**20:.2f} [{x['rss_min']/2**20:.2f}, {x['rss_max']/2**20:.2f}] | {x['live']/2**20:.2f} | {x['ratio']:.3f} | {x['peak']/2**20:.2f} | {x['time']:.3f} [{x['time_min']:.3f}, {x['time_max']:.3f}] | {x['cpu']:.3f} | {x['rss']/base['rss']:.3f} | {x['time']/base['time']:.3f} |")
    truth_path=Path(a.matrix).parent/(b+'.truth.json')
    if b.startswith('site-mixed') and truth_path.exists():
        truth=json.loads(truth_path.read_text())
        print(f"\n{b}: a fixed per-site majority label classifies {100*truth['oracle_correct_byte_share']:.2f}% of traced requested bytes correctly. This is the classification ceiling for this trace; it does not bound idle RSS.\n")
    oracle=m['jev-table:oracle'];heuristic=m['jev-live:heuristic'];model=m['jev-live:model'];static=m['jev-live:static-model']
    saved=base['rss']-oracle['rss']
    print(f"\nOracle saves {saved/2**20:.2f} MiB ({saved/base['rss']:.1%}) against plain mimalloc.")
    for label,values in (('Code-only Clef',static),('Clef with runtime',model),('No-model heuristic',heuristic)):
        capture=f"{(base['rss']-values['rss'])/saved:.1%} of the oracle saving" if saved>0 else 'capture undefined because the oracle saves no memory'
        print(f"{label}: {capture}; idle RSS/oracle {values['rss']/oracle['rss']:.3f}, wall/mi {values['time']/base['time']:.3f}, CPU/mi {values['cpu']/base['cpu']:.3f}.")
    print(f"\n{b}, observed medians: oracle {'beats' if oracle['rss']<base['rss'] else 'does not beat'} mimalloc on idle RSS ({oracle['rss']/base['rss']:.3f}×). Live Clef {'beats' if model['rss']<heuristic['rss'] else 'does not beat'} the heuristic ({model['rss']/heuristic['rss']:.3f}× RSS, {model['time']/heuristic['time']:.3f}× wall time, {model['cpu']/heuristic['cpu']:.3f}× target CPU time). Clef/oracle: {model['rss']/oracle['rss']:.3f}× RSS, {model['time']/oracle['time']:.3f}× wall, {model['cpu']/oracle['cpu']:.3f}× CPU; heuristic/oracle: {heuristic['rss']/oracle['rss']:.3f}× RSS, {heuristic['time']/oracle['time']:.3f}× wall, {heuristic['cpu']/oracle['cpu']:.3f}× CPU. Clef/mi target CPU: {model['cpu']/base['cpu']:.3f}×.\n")
print(f'Complete workloads: {len(bs)}/{len(data["configuration"]["workloads"])}. No equivalence claims are made from five repetitions. Site-mixed TTL choices cannot be separated by a fixed per-site label; trace truth files record the byte-majority classification ceiling, which is not an RSS optimum.')
