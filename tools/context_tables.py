"""Build pair-majority and site-majority controls from one context trace."""
from collections import defaultdict
from common import oracle,write_table

def context_tables(rows,directory):
    from pathlib import Path
    directory=Path(directory)
    totals=defaultdict(lambda:[0,0])
    for row in rows:
        for i in (0,1):totals[row['site_key']][i]+=row['class_bytes'][i]
    write_table(directory/'oracle-site.txt',((k,int(v[1]>v[0])) for k,v in totals.items()))
    pairs=[(r['key'],oracle(r)) for r in rows]
    write_table(directory/'oracle-context.txt',pairs)
    write_table(directory/'oracle.txt',pairs)
    write_table(directory/'all-transient.txt',((r['key'],0) for r in rows))
    return dict(pairs=len(rows),sites=len(totals),contexts=len({r['context_signature'] for r in rows}),
                oracle_site_correct_bytes=sum(max(v) for v in totals.values()),
                oracle_context_correct_bytes=sum(max(r['class_bytes']) for r in rows),
                allocated_bytes=sum(r['bytes'] for r in rows))
