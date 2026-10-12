"""Source-built real applications with fixed peak/drop workloads."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OPTIONS={'MIMALLOC_PURGE_DELAY':'0','MIMALLOC_ARENA_PURGE_MULT':'1','MIMALLOC_PURGE_DECOMMITS':'1','JEVALLOC_DEPTH':'4','JEVALLOC_MODEL_DEPTH':'12'}
def definitions():
 common=dict(stdin=None,expect='fragbench OK',environment=OPTIONS,gate_inference=True,prompt='stack-v1')
 rows=[dict(common,name='sqlite',binary='sqlite-driver',args=[]),dict(common,name='leveldb',binary='leveldb-driver',args=[str(ROOT/'build/real/leveldb-data')]),dict(common,name='redis-sessions',binary='redis-server',args=['--activedefrag','no'],redis_driver='sessions')]
 for name,cache,write,sequence in [('rocksdb-cache',64<<20,16<<20,'fillseq,flush,readrandom,fragpeak,compact,fragidle'),('rocksdb-churn',1<<20,2<<20,'fillseq,overwrite,readrandom,overwrite,fragpeak,compact,fragidle')]:
  args=[f'--db={ROOT}/build/real/{name}-data',f'--benchmarks={sequence}','--num=120000','--reads=120000','--threads=16','--value_size=1024',f'--cache_size={cache}',f'--write_buffer_size={write}','--compression_type=none','--cache_type=lru_cache','--seed=1729','--max_background_jobs=4','--use_existing_db=0']
  rows.append(dict(common,name=name,binary='db_bench',args=args))
 return rows
