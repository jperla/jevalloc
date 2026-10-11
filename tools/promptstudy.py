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
 'server-sim': 'server-sim is a request server: it parses each request, builds a response, keeps per-client session state while a session is active, and maintains a cache index of content it has served.',
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

# ---- runtime-state renderings (round 3) -------------------------------------------
# The statistics are the site's whole-run histogram from the trace, i.e. what a live
# allocator would converge to for a busy site. This isolates one question: given the
# observations, which presentation lets the model read them correctly?
HYB = {'short': 'A temporary: freed almost immediately, before the program has allocated much more memory.',
       'medium': 'Kept for a while (many operations) and released later, well before the program ends.',
       'long': 'Stays alive for most of the program, or is never freed.'}


def human(n):
    for unit in ('bytes', 'KiB', 'MiB', 'GiB'):
        if n < 1024 or unit == 'GiB':
            return ('%d %s' % (n, unit)) if unit == 'bytes' else ('%.0f %s' % (n, unit))
        n /= 1024


def obs(site):
    h = site['lifetime_histogram']; n = max(site['count'], 1); total = site['total_allocation_bytes']
    half = max(total // 2, 1).bit_length() - 1
    q = lambda lo, hi: sum(h[lo:hi]) / n
    return {'n': n, 'total': total, 'imm': q(0, 10), 'soon': q(10, 20), 'later': q(20, half), 'most': q(half, len(h)),
            'never': site['never_freed'] / n, 'h': h}


def pct(x):
    return 'none' if x < 0.005 else 'about %d%%' % round(100 * x)


def stats_raw(site):
    o = obs(site)
    buckets = ','.join('%d:%d' % (i, round(65536 * c / o['n'])) for i, c in enumerate(o['h']) if c)
    return 'Live stats: allocs=%d never_freed=%d lifetime log2-byte buckets, shares /65536: %s\nProcess: alloc_clock=%d' % (
        o['n'], site['never_freed'], buckets, o['total'])


def stats_plain(site):
    o = obs(site)
    return ('Observed so far at this site: %d objects allocated while the program allocated %s in total. '
            'Freed almost immediately (before another 1 KiB was allocated): %s. '
            'Freed soon (before another 1 MiB was allocated): %s. '
            'Freed later, but within the first half of the run: %s. '
            'Alive for more than half of the run before being freed: %s. '
            'Never freed: %s.' % (o['n'], human(o['total']), pct(o['imm']), pct(o['soon']), pct(o['later']), pct(o['most']), pct(o['never'])))


def stats_table(site):
    o = obs(site)
    rows = [('freed within 1 KiB of further allocation', o['imm']), ('freed within 1 MiB', o['soon']),
            ('freed later, within half the run', o['later']), ('alive for more than half the run', o['most']), ('never freed', o['never'])]
    return 'Observed lifetimes at this site (%d objects, program total %s):\n' % (o['n'], human(o['total'])) + '\n'.join(
        '  %-42s %3d%%' % (k, round(100 * v)) for k, v in rows)


def stat_q(state, criteria, text='The call path below allocates heap memory; its observed behaviour so far is given. How long do objects from this site stay alive?'):
    return {'state': state, 'questions': {'lifetime': {'type': 'choice', 'instructions': text, 'criteria': criteria}}}


def code_ctx(site):
    return deep_state(site, radius=20, nsnip=3)


VARIANTS.update({
    'rt-raw-tech': lambda s: stat_q(code_ctx(s) + '\n\n' + stats_raw(s), TECH),
    'rt-raw-sem': lambda s: stat_q(code_ctx(s) + '\n\n' + stats_raw(s), HYB),
    'rt-plain-sem': lambda s: stat_q(code_ctx(s) + '\n\n' + stats_plain(s), HYB),
    'rt-plain-tech': lambda s: stat_q(code_ctx(s) + '\n\n' + stats_plain(s), TECH),
    'rt-table-sem': lambda s: stat_q(code_ctx(s) + '\n\n' + stats_table(s), HYB),
    'rt-plain-first': lambda s: stat_q(stats_plain(s) + '\n\n' + code_ctx(s), HYB),
    'rt-plain-nocode': lambda s: stat_q('Program: ' + s['program'] + '\n' + stats_plain(s), HYB),
    'rt-table-nocode': lambda s: stat_q('Program: ' + s['program'] + '\n' + stats_table(s), HYB),
    'rt-noul-plain': lambda s: noul_q(code_ctx(s) + '\n\n' + stats_plain(s)),
})

# ---- two classes (round 4): short vs long, where long = everything that is not short ----
TWO = {'short': 'A temporary: freed once the current operation is finished, before the program has allocated much more memory.',
       'long': 'Kept beyond the current operation: stored in a data structure, table, cache or global and freed much later, or never freed.'}
Q2 = 'The marked lines lead to a heap allocation. Is the allocated object a short-lived temporary or is it kept?'
Q1 = 'The marked lines lead to a heap allocation. Is the allocated object a temporary that is freed once the current operation is finished?'


def obs2(site):
    h = site['lifetime_histogram']; n = max(site['count'], 1)
    quick = sum(h[:20]) / n
    return n, quick, site['never_freed'] / n, 1 - quick - site['never_freed'] / n


def stats2_plain(site):
    n, quick, never, later = obs2(site)
    return ('Observed so far at this site: %d objects allocated. Freed quickly (before the program allocated another 1 MiB): %s. '
            'Kept longer than that before being freed: %s. Never freed: %s.' % (n, pct(quick), pct(max(later, 0)), pct(never)))


def stats2_table(site):
    n, quick, never, later = obs2(site)
    return 'Observed lifetimes at this site (%d objects):\n  freed quickly (within 1 MiB of further allocation) %3d%%\n  kept longer, freed later %3d%%\n  never freed %3d%%' % (
        n, round(100 * quick), round(100 * max(later, 0)), round(100 * never))


def choice2(state, text=Q2):
    return {'state': state, 'questions': {'lifetime': {'type': 'choice', 'instructions': text, 'criteria': TWO}}}


def noul1(state, text=Q1):
    return {'state': state, 'questions': {'temporary': {'type': 'noul', 'instructions': text}}}


QS = 'The call path allocates heap memory; its observed behaviour so far is given. Is the allocated object a short-lived temporary or is it kept?'
VARIANTS.update({
    'c2': lambda s: choice2(deep_state(s, radius=20, nsnip=3)),
    'c2-desc': lambda s: choice2(deep_state(s, radius=20, nsnip=3, desc=True)),
    'c2-desc-small': lambda s: choice2(deep_state(s, radius=6, nsnip=2, desc=True)),
    'c2-desc-stackonly': lambda s: choice2(deep_state(s, nsnip=0, desc=True)),
    'n1-desc': lambda s: noul1(deep_state(s, radius=20, nsnip=3, desc=True)),
    'rt2-plain-nocode': lambda s: choice2('Program: ' + s['program'] + '\n' + stats2_plain(s), QS),
    'rt2-table-nocode': lambda s: choice2('Program: ' + s['program'] + '\n' + stats2_table(s), QS),
    'rt2-raw-nocode': lambda s: choice2('Program: ' + s['program'] + '\n' + stats_raw(s), QS),
    'rt2-plain-code-desc': lambda s: choice2(deep_state(s, radius=20, nsnip=3, desc=True) + '\n\n' + stats2_plain(s), QS),
    'rt2-n1-plain': lambda s: noul1('Program: ' + s['program'] + '\n' + stats2_plain(s), 'The observed behaviour of an allocation site is given. Are its objects temporaries that are freed quickly?'),
})

# ---- transient vs permanent (round 5): the cut that matters for idle memory ----------
# 'short' = transient (freed at some point, even much later), 'long' = permanent.
PERM = {'short': 'Released at some point while the program keeps running: a temporary, or something held for a while (a request, a session, a work item) and then freed.',
        'long': 'Permanent: kept for the rest of the program - a cache or index entry, a global table, configuration, or anything that is never freed.'}
QP = 'The marked lines lead to a heap allocation. Is the allocated object released at some point, or is it kept for the rest of the program?'
QPS = 'The observed behaviour of an allocation site is given. Are its objects released at some point, or kept for the rest of the program?'


def statsp_plain(site):
    o = obs(site)
    return ('Observed so far at this site: %d objects allocated. Freed quickly (before the program allocated another 1 MiB): %s. '
            'Freed later, well before the end: %s. Still alive after most of the run, or never freed: %s.' % (
                o['n'], pct(o['imm'] + o['soon']), pct(o['later']), pct(o['most'] + o['never'])))


def choicep(state, text=QP):
    return {'state': state, 'questions': {'lifetime': {'type': 'choice', 'instructions': text, 'criteria': PERM}}}


def noulp(state):
    return {'state': state, 'questions': {'retained': {'type': 'noul', 'instructions': 'The marked lines lead to a heap allocation. Is the allocated object kept for the rest of the program (a cache or index entry, a global, or never freed)?'}}}


VARIANTS.update({
    'p2': lambda s: choicep(deep_state(s, radius=20, nsnip=3)),
    'p2-desc': lambda s: choicep(deep_state(s, radius=20, nsnip=3, desc=True)),
    'p2-desc-small': lambda s: choicep(deep_state(s, radius=6, nsnip=2, desc=True)),
    'pn1-desc': lambda s: noulp(deep_state(s, radius=20, nsnip=3, desc=True)),
    'rtp-plain-nocode': lambda s: choicep('Program: ' + s['program'] + '\n' + statsp_plain(s), QPS),
    'rtp-plain-code-desc': lambda s: choicep(deep_state(s, radius=20, nsnip=3, desc=True) + '\n\n' + statsp_plain(s), QPS),
})

# ---- round 6: wordings for the first-sight decision on fragbench ----------------------
QF = 'The marked lines lead to a heap allocation. Will this object be freed while the program is still running?'
FREE = {'short': 'Yes: it is freed at some point - right away, when the request finishes, or when a session or connection ends.',
        'long': 'No: it stays until the program exits - an entry added to a cache, index or global table that is never removed.'}
VARIANTS.update({
    'f2-desc': lambda s: {'state': deep_state(s, radius=20, nsnip=3, desc=True), 'questions': {'lifetime': {'type': 'choice', 'instructions': QF, 'criteria': FREE}}},
    'f2': lambda s: {'state': deep_state(s, radius=20, nsnip=3), 'questions': {'lifetime': {'type': 'choice', 'instructions': QF, 'criteria': FREE}}},
    'f2-desc-small': lambda s: {'state': deep_state(s, radius=4, nsnip=3, desc=True), 'questions': {'lifetime': {'type': 'choice', 'instructions': QF, 'criteria': FREE}}},
    'f2-desc-stack': lambda s: {'state': deep_state(s, nsnip=0, desc=True), 'questions': {'lifetime': {'type': 'choice', 'instructions': QF, 'criteria': FREE}}},
    'f2-stack': lambda s: {'state': deep_state(s, nsnip=0), 'questions': {'lifetime': {'type': 'choice', 'instructions': QF, 'criteria': FREE}}},
    'fn-desc-stack': lambda s: {'state': deep_state(s, nsnip=0, desc=True), 'questions': {'retained': {'type': 'noul', 'instructions': 'Does the allocated object stay until the program exits (an entry added to a cache, index or global table that is never removed)?'}}},
    'p2-desc-stack': lambda s: choicep(deep_state(s, nsnip=0, desc=True)),
})


def prob_true(ans):
    for k in ('noul', 'probability'):
        if k in ans:
            return ans[k]
    p = ans.get('probabilities', {})
    return p.get('true', p.get('yes', 0.0))


def decide(variant, ans):
    if 'retained' in ans and 'temporary' not in ans:
        r = prob_true(ans['retained'])
        return ('long' if r >= 0.5 else 'short'), {'temporary': 1 - r, 'retained': r}
    if 'temporary' in ans and 'retained' not in ans:
        t = prob_true(ans['temporary'])
        return ('short' if t >= 0.5 else 'long'), {'temporary': t, 'retained': 1 - t}
    if variant.startswith('noul'):
        t, r = prob_true(ans['temporary']), prob_true(ans['retained'])
        return ('short' if t >= r else 'long'), {'temporary': t, 'retained': r}
    a = ans['lifetime']
    return a['choice'], a.get('probabilities', {})


def busy(gate):
    """True while a benchmark runner is alive and inside a timed repetition."""
    if not gate or subprocess.run(['pgrep', '-f', 'bench/run.py'], capture_output=True).returncode != 0:
        return False
    try:
        return ' rep ' in open(gate).read().strip().split('\n')[-1]
    except (OSError, IndexError):
        return False


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
    ap.add_argument('--show', action='store_true', help='print each site and its answer')
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
            while busy(a.gate):
                time.sleep(3)
            try:
                r, dt = ask(a.url, a.cache, req)
            except Exception as e:
                print('ERR', v, s['key'], e, flush=True); continue
            pred, probs = decide(v, r['answers'])
            conf[(s['truth'], pred)] += 1
            if a.show:
                print('   %-9s truth=%-6s pred=%-6s %s  %s' % (v, s['truth'], pred, {k: round(x, 2) for k, x in probs.items()}, ' < '.join(f[0] for f in frames(s)[:3])), flush=True)
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
