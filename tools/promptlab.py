#!/usr/bin/env python3
"""Prompt study: which context lets Clef predict a site's lifetime class?

Scores prompt variants against the oracle table on a class-balanced sample of
allocation sites. Uses only what is knowable before the program runs.
"""
import argparse, collections, functools, hashlib, json, os, random, subprocess, sys, time, urllib.request

CLASSES = ['short', 'medium', 'long']
TECH = {'short': 'Freed before another 1 MiB is allocated.', 'medium': 'Neither short nor long.',
        'long': 'Lives until exit or over half of total program allocation volume.'}
SEM = {'short': 'A temporary: scratch space or an intermediate value that this function or its caller frees once the current operation is finished.',
       'medium': 'Kept in a data structure for a while (many operations) and released later, well before the program ends.',
       'long': 'Stored in a global, a table, a cache or another structure that lasts for most of the program, or never freed.'}


@functools.lru_cache(None)
def addr2line(image, addr):
    a = max(int(addr, 16) - 1, 0)
    out = subprocess.run(['addr2line', '-f', '-C', '-e', image, hex(a)], capture_output=True, text=True).stdout.split('\n')
    fn = out[0] if out else '??'
    loc = out[1].split(' ')[0] if len(out) > 1 else '??:0'
    path, _, line = loc.rpartition(':')
    return fn, path, int(line) if line.isdigit() else 0


@functools.lru_cache(None)
def source(path):
    try:
        return open(path, errors='replace').read().split('\n')
    except OSError:
        return []


def snippet(path, line, radius):
    src = source(path)
    if not src or not line:
        return ''
    lo, hi = max(1, line - radius), min(len(src), line + radius)
    return '\n'.join(('>> ' if i == line else '   ') + src[i - 1].replace('\t', '  ')[:140] for i in range(lo, hi + 1))


def frames(site):
    out = []
    for f in site['frames']:
        fn, path, line = addr2line(f['image'], f.get('address') or f.get('addr'))
        out.append((fn, path, line, os.path.basename(f['image'])))
    return out


def state_text(site, radius, nsnip):
    fr = frames(site)
    lines = ['Program: ' + site['program'], 'Call stack of the allocation (innermost first):']
    lines += ['  %s  (%s:%d)' % (fn, os.path.basename(path), line) for fn, path, line, _ in fr]
    n = 0
    for fn, path, line, _ in fr:
        s = snippet(path, line, radius)
        if s and n < nsnip:
            lines += ['', 'Source of %s, the line marked >> is on the call path:' % fn, s]
            n += 1
    return '\n'.join(lines)


def v_baseline(site):
    return {'state': state_text(site, 6, 2), 'questions': {'lifetime': {'type': 'choice',
            'instructions': 'Predict the lifetime of bytes allocated at this site. Choose long when short and long overlap.', 'criteria': TECH}}}


def v_semantic(site):
    return {'state': state_text(site, 6, 2), 'questions': {'lifetime': {'type': 'choice',
            'instructions': 'The marked lines allocate heap memory. How long does the allocated object stay alive before it is freed?', 'criteria': SEM}}}


def v_wide(site):
    q = v_semantic(site)
    q['state'] = state_text(site, 20, 3)
    return q


def v_noul(site):
    return {'state': state_text(site, 20, 3), 'questions': {
        'temporary': {'type': 'noul', 'instructions': 'The marked lines allocate heap memory. Is the allocated object a temporary that is freed soon, by this function or its caller, once the current operation is finished?'},
        'retained': {'type': 'noul', 'instructions': 'The marked lines allocate heap memory. Is the allocated object stored in a global, table, cache or other structure that stays alive for most of the program (or never freed)?'}}}


def v_json(site):
    fr = frames(site)
    st = {'program': site['program'], 'task': 'classify the lifetime of the heap object allocated on this call path',
          'call_stack_innermost_first': [{'function': fn, 'file': os.path.basename(p), 'line': l,
                                          'code': snippet(p, l, 8)} for fn, p, l, _ in fr[:3]]}
    return {'state': st, 'questions': {'lifetime': {'type': 'choice',
            'instructions': 'How long does the allocated object stay alive before it is freed?', 'criteria': SEM}}}


VARIANTS = {'baseline': v_baseline, 'semantic': v_semantic, 'wide': v_wide, 'noul': v_noul, 'json': v_json}

DESC = {
 'cfrac': 'cfrac factors one large integer with the continued-fraction method; it does arbitrary-precision arithmetic on heap-allocated numbers (palloc/pnew allocate a number, pdestroy/pfree release it).',
 'espresso': 'espresso minimises a boolean logic function (PLA); it builds and discards many sets, covers and cubes while it iterates.',
 'glibc-simple': 'glibc-simple is a micro-benchmark that allocates and frees blocks of fixed sizes in loops.',
 'rptest': 'rptest is a multi-threaded allocator stress test: each thread repeatedly allocates batches of random-size blocks, frees some, and passes others to other threads.',
 'larson': 'larson simulates a server: threads keep an array of blocks alive and repeatedly replace random slots with newly allocated blocks.',
 'redis-server': 'redis-server is an in-memory key-value database serving client commands; zmalloc/zcalloc/zrealloc are its malloc wrappers, sds are its strings, robj its values; some objects are per-command temporaries and others are stored in the keyspace or in server-wide state.',
}


def func_body(path, line, cap=80):
    src = source(path)
    if not src or not line:
        return ''
    lo = line
    while lo > 1 and not (src[lo - 1][:1] not in (' ', '\t', '', '{', '}', '#', '/', '*') and '(' in src[lo - 1]):
        lo -= 1
    hi = line
    while hi < len(src) and not src[hi - 1].startswith('}'):
        hi += 1
    if hi - lo > cap:
        lo, hi = max(lo, line - cap // 2), min(hi, line + cap // 2)
    return '\n'.join(('>> ' if i == line else '   ') + src[i - 1].replace('\t', '  ')[:140] for i in range(lo, hi + 1))


def stack_lines(fr):
    return ['  %s  (%s:%d)' % (fn, os.path.basename(path), line) for fn, path, line, _ in fr]


def deep_state(site, radius=10, nsnip=5, which='inner', desc=False, examples=None, body=False, nframes=12):
    fr = [f for f in frames(site)][:nframes]
    lines = ['Program: ' + site['program']]
    if desc:
        lines += ['About the program: ' + DESC.get(site['program'], '')]
    if examples:
        lines += ['', 'Lifetimes measured at allocation sites of OTHER programs, for reference:']
        for ex in examples:
            lines += ['- ' + ' <- '.join(fn for fn, _, _, _ in frames(ex)[:4]) + '  => ' + ex['truth']]
        lines += ['']
    lines += ['Call stack of the allocation to classify (innermost first):'] + stack_lines(fr)
    with_src = [f for f in fr if source(f[1]) and f[2]]
    chosen = with_src[:nsnip] if which == 'inner' else with_src[-nsnip:]
    for fn, path, line, _ in chosen:
        text = func_body(path, line) if body else snippet(path, line, radius)
        lines += ['', 'Source of %s, the line marked >> is on the call path:' % fn, text]
    return '\n'.join(lines)[:11000]


def choice_q(state):
    return {'state': state, 'questions': {'lifetime': {'type': 'choice',
            'instructions': 'The marked lines lead to a heap allocation. How long does the allocated object stay alive before it is freed?', 'criteria': SEM}}}


def noul_q(state):
    return {'state': state, 'questions': {
        'temporary': {'type': 'noul', 'instructions': 'The marked lines lead to a heap allocation. Is the allocated object a temporary that is freed soon, by one of these functions, once the current operation is finished?'},
        'retained': {'type': 'noul', 'instructions': 'The marked lines lead to a heap allocation. Is the allocated object stored in a global, table, cache or other structure that stays alive for most of the program (or never freed)?'}}}


def fewshot(site):
    rng = random.Random(site['key'])
    pool = [s for s in SAMPLE if s['program'] != site['program']]
    ex = []
    for c in CLASSES:
        cand = [s for s in pool if s['truth'] == c]
        rng.shuffle(cand)
        ex += cand[:3]
    rng.shuffle(ex)
    return ex


SAMPLE = []
VARIANTS.update({
    'wide4': lambda s: choice_q(deep_state(s, radius=20, nsnip=3, nframes=4)),
    'deep': lambda s: choice_q(deep_state(s)),
    'outer': lambda s: choice_q(deep_state(s, which='outer')),
    'func': lambda s: choice_q(deep_state(s, nsnip=3, body=True)),
    'desc': lambda s: choice_q(deep_state(s, desc=True)),
    'fewshot': lambda s: choice_q(deep_state(s, nsnip=3, examples=fewshot(s))),
    'desc-fewshot': lambda s: choice_q(deep_state(s, nsnip=3, desc=True, examples=fewshot(s))),
    'noul-deep': lambda s: noul_q(deep_state(s)),
    'noul-desc': lambda s: noul_q(deep_state(s, desc=True)),
})


def prob_true(ans):
    for k in ('noul', 'probability'):
        if k in ans:
            return ans[k]
    p = ans.get('probabilities', {})
    return p.get('true', p.get('yes', 0.0))


def decide(variant, ans):
    if variant.startswith('noul'):
        t, r = prob_true(ans['temporary']), prob_true(ans['retained'])
        return ('short' if t >= r else 'long'), {'temporary': t, 'retained': r}
    a = ans['lifetime']
    return a['choice'], a.get('probabilities', {})


def ask(url, cache_dir, req):
    body = dict(req, model='clef-flash')
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    p = os.path.join(cache_dir, h + '.json')
    if os.path.exists(p):
        return json.load(open(p)), 0.0
    t = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json'}), timeout=600))
    json.dump(r, open(p, 'w'))
    return r, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='results')
    ap.add_argument('--workloads', default='cfrac,redis,espresso,glibc-simple,rptest,larson')
    ap.add_argument('--per-class', type=int, default=12)
    ap.add_argument('--variants', default=','.join(VARIANTS))
    ap.add_argument('--url', default='http://127.0.0.1:8765/v1/systemone')
    ap.add_argument('--out', default='promptlab.json')
    ap.add_argument('--cache', default='promptlab-cache')
    ap.add_argument('--traces', default=None, help='trace dir whose own class_bytes give the truth')
    ap.add_argument('--gate', default=None, help='benchmark log; wait while it is inside a timed repetition')
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    rng = random.Random(7)
    sample = []
    for w in a.workloads.split(','):
        by = collections.defaultdict(list)
        if a.traces:
            for l in open(f'{a.traces}/{w}.jsonl'):
                s = json.loads(l)
                if s.get('frames') and sum(s['class_bytes']):
                    s['truth'] = CLASSES[max(range(3), key=lambda i: s['class_bytes'][i])]
                    by[s['truth']].append(s)
        else:
            cls = {l.split()[0]: int(l.split()[1]) for l in open(f'{a.results}/tables/{w}/oracle.txt') if l.strip() and l[0] != '#'}
            for l in open(f'{a.results}/traces/{w}.jsonl'):
                s = json.loads(l)
                if s.get('key') in cls and s.get('frames'):
                    s['truth'] = CLASSES[cls[s['key']]]
                    by[s['truth']].append(s)
        for c in CLASSES:
            rng.shuffle(by[c])
            sample += by[c][:a.per_class]
    SAMPLE[:] = sample
    print('sample', len(sample), collections.Counter(s['truth'] for s in sample), flush=True)
    rows = []
    for v in a.variants.split(','):
        conf = collections.Counter(); secs = []; toks = []
        for s in sample:
            req = VARIANTS[v](s)
            while a.gate and ' rep ' in (open(a.gate).read().strip().split('\n') or [''])[-1]:
                time.sleep(3)
            try:
                r, dt = ask(a.url, a.cache, req)
            except Exception as e:
                print('ERR', v, s['key'], e, flush=True); continue
            pred, probs = decide(v, r['answers'])
            conf[(s['truth'], pred)] += 1
            if dt: secs.append(dt)
            toks.append((r.get('usage') or {}).get('input_tokens', 0))
            rows.append({'variant': v, 'program': s['program'], 'key': s['key'], 'truth': s['truth'], 'pred': pred, 'probs': probs, 'seconds': dt})
        n = sum(conf.values()); acc = sum(conf[(c, c)] for c in CLASSES) / max(n, 1)
        rec = [conf[(c, c)] / max(sum(conf[(c, p)] for p in CLASSES), 1) for c in CLASSES]
        print(f'{v:9s} n={n} acc={acc:.2f} balanced={sum(rec)/3:.2f} recall S/M/L={rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f} '
              f'pred S/M/L={sum(conf[(c,"short")] for c in CLASSES)}/{sum(conf[(c,"medium")] for c in CLASSES)}/{sum(conf[(c,"long")] for c in CLASSES)} '
              f'tok~{sum(toks)//max(len(toks),1)} sec~{sum(secs)/max(len(secs),1):.1f}', flush=True)
        b = [(r['truth'], ('short' if r['probs'].get('short', r['probs'].get('temporary', 0)) >= r['probs'].get('long', r['probs'].get('retained', 0)) else 'long'), r['program'])
             for r in rows if r['variant'] == v and r['truth'] != 'medium']
        rs = sum(t == p for t, p, _ in b if t == 'short') / max(sum(t == 'short' for t, _, _ in b), 1)
        rl = sum(t == p for t, p, _ in b if t == 'long') / max(sum(t == 'long' for t, _, _ in b), 1)
        per = collections.defaultdict(lambda: [0, 0])
        for t, p, g in b:
            per[g][0] += t == p; per[g][1] += 1
        print(f'          short-vs-long n={len(b)} acc={sum(t == p for t, p, _ in b)/max(len(b),1):.2f} balanced={(rs+rl)/2:.2f} recallS={rs:.2f} recallL={rl:.2f} ' + ' '.join(f'{g}:{x}/{y}' for g, (x, y) in per.items()), flush=True)
        json.dump(rows, open(a.out, 'w'))


if __name__ == '__main__':
    main()
