#!/usr/bin/env python3
"""Re-trace workloads with a deeper call stack for the prompt study (run from the repo root)."""
import argparse, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'bench'), str(ROOT / 'tools')]
import run as runner
from definitions import definitions


def quiet(log):
    """True while the benchmark matrix is not inside a timed repetition."""
    try:
        last = Path(log).read_text().strip().split('\n')[-1]
    except OSError:
        return True
    return ' rep ' not in last and not last.startswith('redis')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--depth', default='12')
    ap.add_argument('--workloads', default='cfrac,espresso,glibc-simple,rptest,larson,redis')
    ap.add_argument('--gate', default=str(ROOT / 'results/bench.log'))
    a = ap.parse_args()
    out = Path(a.out).resolve(); (out / 'traces').mkdir(parents=True, exist_ok=True)
    env0 = runner.environment

    def env(*args, **kw):
        e, extra = env0(*args, **kw)
        if 'JEVALLOC_MODE' in extra:
            extra['JEVALLOC_DEPTH'] = a.depth
        return e, extra
    runner.environment = env
    for row in definitions(16):
        if row['name'] not in a.workloads.split(','):
            continue
        path = out / 'traces' / (row['name'] + '.jsonl')
        if path.exists():
            continue
        while not quiet(a.gate):
            time.sleep(5)
        print('TRACE', row['name'], flush=True)
        runner.run_one(row, 'jev-trace', 0, out / 'logs', ROOT / 'results/tables', mode='trace', trace=path)
        print('  sites', sum(1 for _ in open(path)), flush=True)


if __name__ == '__main__':
    main()
