"""Report compaction against its twin and placement against key-only overhead."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def idle(r,phase):return max((p for p in r['phases'] if p['phase']==phase),key=lambda p:p.get('cycle',0))['rss_bytes']
def main():
 base=ROOT/'results/pass9';rows=[];data={};failures=[]
 for path in sorted((base/'compaction').glob('*/matrix.json')):
  d=json.loads(path.read_text())
  if not d.get('complete'):continue
  name=path.parent.name;groups={}
  failures += [dict(workload=name,variant=v,**error) for v,error in d.get('failed_variants',{}).items()]
  for r in d['runs']:
   if r['repetition']>=0 and not r.get('rejected'):
    assert r['exit_status']==0 and r['output_ok'] and not r.get('model_seconds') and not r.get('replay_missing')
    assert r['environment']['FRAG_LONG_SETTLE_MS']=='10000'
    long_phases=[p for p in r['phases'] if p['phase']=='idle10']
    assert len(long_phases)==(2 if name.startswith('site-') or name=='redis-mesh' else 1)
    assert r['wall_seconds']>=10*len(long_phases)-.2,(name,r['variant'],r['wall_seconds'])
    groups.setdefault(r['variant'],[]).append(r)
  for v,rs in groups.items():
   assert sorted(r['repetition'] for r in rs)==list(range(5)),(name,v)
   metrics={k:dict(median=statistics.median(fn(r) for r in rs),min=min(fn(r) for r in rs),max=max(fn(r) for r in rs)) for k,fn in [('idle',lambda r:idle(r,'idle')),('idle10',lambda r:idle(r,'idle10')),('peak',lambda r:r['peak_rss_bytes']),('wall',lambda r:r['wall_seconds']),('cpu',lambda r:r['cpu_seconds'])]}
   data.setdefault(name,{})[v]=metrics
  audit=json.loads(path.with_suffix('.inference-audit.json').read_text())
  assert audit['matrix_sha256']==hashlib.sha256(path.read_bytes()).hexdigest() and audit['overlapping_runs']==0
 assert set(data)=={'site-pure-1','site-pure-16','site-mixed-1','site-mixed-16','redis-mesh','redis-drop','redis-sessions','sqlite','leveldb','rocksdb-cache','rocksdb-churn'},'All eleven blocks must finish before publication'
 mesh_savings={name:100*(1-vs['mesh']['idle10']['median']/vs['nomesh']['idle10']['median']) for name,vs in data.items() if 'mesh' in vs and 'nomesh' in vs}
 wins=[name for name,value in mesh_savings.items() if value>5]
 real_wins=[name for name,vs in data.items() if not name.startswith('site-') and 'mesh' in vs and vs['mesh']['idle10']['median']<.95*vs['mi']['idle10']['median']]
 headline=f"After 10 seconds, Mesh saves more than 5% RSS against nomesh on {len(wins)}/{len(mesh_savings)} comparable workloads: "+(', '.join(wins) if wins else 'none')+'. '
 headline+='Against plain mimalloc, Mesh clears 5% on these real-program workloads: '+(', '.join(real_wins) if real_wins else 'none')+'. These are descriptive five-run comparisons, not new model-admission gates.'
 if all(m['idle']['median']==m['idle10']['median'] for vs in data.values() for m in vs.values()):
  headline+=f" Normal and 10-second idle RSS medians are identical in all {sum(len(vs) for vs in data.values())} allocator/workload comparisons."
 lines=['## Mesh compaction comparison','',headline,'',f'{len(data)}/11 workload blocks processed, with {len(failures)} allocator/workload failures. Five interleaved repetitions per reported successful variant. Normal idle and 10-second idle are sampled in the same process; longer idle in the first cycle can affect the next cycle. Wall time includes all common settle periods.','',
 '| Workload | Variant | Idle MiB | 10 s idle MiB | Peak MiB | Wall s | CPU s | Idle / mi | Idle / twin | 10 s / twin |','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 if (base/'compaction-comparison.png').exists():
  lines[4:4]=['![Idle RSS and ratios against each allocator\'s own baseline](results/pass9/compaction-comparison.png)','[Vector figure](results/pass9/compaction-comparison.svg)','']
 for name,variants in data.items():
  for v,m in variants.items():
   twin='nomesh' if v in ('mesh','nomesh') else 'jev-keyonly'
   ratio=m['idle10']['median']/variants[twin]['idle10']['median'] if v!='mi' and twin in variants else None
   normal_ratio=m['idle']['median']/variants[twin]['idle']['median'] if v!='mi' and twin in variants else None
   vals=[f'{m[k]["median"]/1048576:.2f}' for k in ('idle','idle10','peak')]+[f'{m[k]["median"]:.3f}' for k in ('wall','cpu')]
   lines.append('| '+name+' | '+v+' | '+' | '.join(vals)+f" | {m['idle']['median']/variants['mi']['idle']['median']:.3f} | "+(f'{normal_ratio:.3f}' if normal_ratio is not None else '—')+' | '+(f'{ratio:.3f}' if ratio is not None else '—')+' |')
 if failures:
  lines+=['','Variants that failed are excluded from aggregates (including any earlier successful repetitions):']
  lines += [f"- {f['workload']} / {f['variant']}: {f['error']}" for f in failures]
  (base/'compaction-failures.json').write_text(json.dumps(failures,indent=2))
 lines+=['','Twin is nomesh for both Mesh variants, jev-keyonly for placement policies. Each allocator has its own baseline; a Mesh/mi difference alone does not isolate compaction. CPU is workload-process user plus system time, excluding the sidecar. Full ranges and all costs are in [compaction-summary.json](results/pass9/compaction-summary.json).']
 cache=data['rocksdb-cache'];oracle=cache['jev-table:oracle-site']['idle10'];mi=cache['mi']['idle10']
 if oracle['median']<.95*mi['median']:
  lines+=['',f"The later RocksDB-cache per-site oracle median is {100*(1-oracle['median']/mi['median']):.1f}% below mimalloc, with run ranges {oracle['min']/1048576:.2f}–{oracle['max']/1048576:.2f} MiB (oracle) and {mi['min']/1048576:.2f}–{mi['max']/1048576:.2f} MiB (mimalloc). The intervals overlap. This uses a new trace and the longer-settle workload; the earlier independent headroom gate is retained separately, and no additional database context/model experiment was added."]
 lines+=['','Mesh source revision: `2987f883b8695c07a80dc40da67c61f524460dfd` (the recipe follows master). Default randomization is unchanged; the twin differs by `DISABLE_MESHING=ON`. Dependency archives retain the exact pinned revisions. Build logs, hashes and the CMake dependency-fetch adaptation are in [builds](results/pass9/builds).',
 'This revision checks a 100 ms meshing interval on eligible frees; it does not run a background compaction thread during a completely quiet idle. Waiting longer alone therefore need not trigger another mesh pass.',
 'These are process RSS measurements, as requested. RSS counts resident mappings; PSS apportions shared pages across mappings ([Linux kernel documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html)). Because Mesh preserves virtual addresses by aliasing physical pages, RSS alone can understate its physical-memory benefit. This experiment does not measure PSS and does not equate unchanged RSS with zero physical compaction.']
 units=base/'builds/mesh-unit-results.json'
 if units.exists():
  checks=json.loads(units.read_text())
  assert checks['mesh_exit_status']==0 and checks['nomesh_exit_status']==0 and checks['measured_libraries_unchanged']
  lines+=['','Upstream unit checks pass in both configurations (meshing-specific tests are skipped by nomesh). The measured library hashes were verified unchanged before and after the checks. Logs: [Mesh](results/pass9/builds/mesh-unit.log), [nomesh](results/pass9/builds/nomesh-unit.log).']
 (base/'compaction-summary.json').write_text(json.dumps(data,indent=2));(base/'compaction-results.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
