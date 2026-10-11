"""Exercise reservoir replacement, delayed frees, and classification changes in C."""
import json,subprocess,tempfile
from pathlib import Path
from test_live import ROOT,daemon,execute
with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='permanent-') as name:
    folder=Path(name);binary=folder/'fixture'
    subprocess.run(['cc','-g','-O0','-fno-builtin','-fno-omit-frame-pointer',str(ROOT/'tests/permanent.c'),'-o',str(binary)],check=True)
    reports=[]
    for sample in (1,64):
        log=folder/f'live-{sample}.jsonl';process,sock=daemon(folder,'heuristic',log,folder/f'cache-{sample}')
        try:stats,_=execute(folder/'stats.json',sock,[str(binary)],sample_rate=sample)
        finally:process.terminate();process.wait()
        assert not stats['failures'],stats
        events=[json.loads(line) for line in log.read_text().splitlines()]
        keys={e['request']['key'] for e in events if e['request']['site']['allocs']>=8192}
        assert len(keys)==1,keys
        rows=[e for e in events if e['request']['key'] in keys]
        assert [e['response']['class'] for e in rows]==[0,1,0],rows
        assert rows[1]['request']['site']['older_sampled_bytes']>0
        assert rows[1]['request']['site']['older_freed_bytes']==0
        assert rows[2]['request']['site']['older_freed_bytes']>0
        reports.append(dict(sample_rate=sample,events=rows))
    out=ROOT/'results/pass7/validation';out.mkdir(parents=True,exist_ok=True)
    (out/'permanent-heuristic.json').write_text(json.dumps(reports,indent=2))
print('PERMANENT HEURISTIC INTEGRATION PASSED')
