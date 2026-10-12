"""Read-only progress summary for the long pass-9 benchmark launchers."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]/'results/pass9'
for name in ('stage.txt','context.status','validation.status','mesh-build.status','long-settle-build.status','compaction.status'):
 p=base/name
 if p.exists():print(name+': '+p.read_text().strip())
total=0;complete=0
for p in sorted((base/'compaction').glob('*/matrix.json')):
 d=json.loads(p.read_text());rs=[r for r in d['runs'] if r['repetition']>=0 and not r.get('rejected')]
 total+=len(rs);complete+=bool(d.get('complete'))
 print(p.parent.name+': '+str(len(rs))+' warm runs'+(' COMPLETE' if d.get('complete') else ' in progress'))
 for variant,failure in d.get('failed_variants',{}).items():print('  '+variant+' failed: '+failure['error'])
print(f'Compaction: {complete}/11 blocks; {total}/385 planned warm runs')
p=base/'compaction.log'
if p.exists():print('\n'.join(p.read_text().splitlines()[-3:]))
