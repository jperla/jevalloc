"""One definition of accepted warm observations for every report."""
def accepted(row):
    return (row.get('exit_status')==0 and row.get('output_ok') is True
            and row.get('repetition',-1)>=0
            and not any(row.get(k) for k in ('cold','coverage_fill','coverage_probe','rejected','interference','diagnostic','decision_errors','replay_missing'))
            and not row.get('allocator_stats',{}).get('failures'))

def complete_groups(data,reps=5,variants=None):
    from collections import defaultdict
    groups=defaultdict(list)
    for r in data['runs']:
        if accepted(r):groups[r['benchmark'],r['variant']].append(r)
    variants=variants or data['configuration']['variants']
    benches=[b for b in data['configuration']['workloads'] if all(len(groups[b,v])==reps and {r['repetition'] for r in groups[b,v]}==set(range(reps)) for v in variants)]
    return groups,benches
