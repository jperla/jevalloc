"""Native two-class prompts; cache namespace is independent of legacy prompts."""
from pathlib import Path
from symbolize import symbolize
import json

PROMPT_ID = 'transient-permanent-v1'
QUESTION = 'The marked lines lead to a heap allocation. Is the allocated object released at some point, or is it kept for the rest of the program?'
CRITERIA = {
 'transient': 'Released at some point while the program keeps running: a temporary, or something held for a while (a request, a session, a work item) and then freed.',
 'permanent': 'Permanent: kept for the rest of the program - a cache or index entry, a global table, configuration, or anything that is never freed.'}
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'))
STACK_QUESTION = 'The marked lines lead to a heap allocation. Will this object be freed while the program is still running?'
STACK_CRITERIA = {
 'transient': 'Yes: it is freed at some point - right away, when the request finishes, or when a session or connection ends.',
 'permanent': 'No: it stays until the program exits - an entry added to a cache, index or global table that is never removed.'}
PROMPTS = ['stack-v1', 'stack-v1-nodesc', 'v2', 'v2-no-description', 'v2-runtime-only']
def criteria(name): return STACK_CRITERIA if name.startswith('stack-v1') else CRITERIA
def question(name): return STACK_QUESTION if name.startswith('stack-v1') else QUESTION

def stack_state(request, static, prompt):
    frames=[dict(f,address=f.get('address',f.get('addr','0x0'))) for f in request.get('frames',[])[:12]]
    symbolize([{'frames':[f for f in frames if 'function' not in f]}])
    program=request.get('program','unknown')
    lines=['Program: '+program]
    description=Path(__file__).resolve().parents[1]/'descriptions'/(Path(program).name+'.txt')
    if prompt=='stack-v1' and description.exists():lines.append('About the program: '+description.read_text().strip())
    lines.append('Call stack of the allocation to classify (innermost first):')
    for f in frames:
        function=str(f.get('function','?')).split('\n')[0][:160]
        lines.append(f"  {function}  ({f.get('file') or '?'}:{f.get('line') or '?'})")
    if not static and request.get('prior') is not None:
        site=request.get('site',{})
        age=site.get('oldest_age_bytes',0)
        volume=f'{age:,} bytes'
        lines.append(f"Observed so far at this site: {site.get('allocs',0):,} objects allocated. Freed quickly (before the program allocated another 1 MiB): about {site.get('short_share',0)}%. Freed later: about {site.get('long_freed_share',0)}%. Not freed so far: about {site.get('alive_share',0)}%. The oldest objects from this site have existed while the program allocated another {volume}.")
        if site.get('alive_share')==100:
            lines.append('Nothing from this site has been freed yet, which is also what a long-lived but eventually freed object looks like early on.')
    return '\n'.join(lines)

def state(request,static=False,prompt='stack-v1'):
    if prompt.startswith('stack-v1'):return stack_state(request,static,prompt)
    frames=[dict(f,address=f.get('address',f.get('addr','0x0'))) for f in request.get('frames',[])]
    symbolize([{'frames':[f for f in frames if 'function' not in f]}])
    program=request.get('program','unknown')
    description=Path(__file__).resolve().parents[1]/'descriptions-leaky'/(Path(program).name+'.txt')
    lines=['Program: '+program]
    if prompt!='v2-no-description' and description.exists(): lines.append('Program description (hand-written): '+description.read_text().strip())
    lines.append('Stack (innermost first):')
    lines += [str(f.get('function','?')).split('\n')[0][:160] for f in frames[:12]]
    included=0
    for f in frames:
        if not f.get('source') or included==3:continue
        included+=1;center=f['line'];lines.append(f"{f['file']}:{center}")
        lines += [f"{'>>' if x['line']==center else '  '} {x['line']}: {x['text'][:140]}" for x in f['source'] if abs(x['line']-center)<=20]
    if not static and request.get('prior') is not None:
        site=request.get('site',{});threshold=site.get('short_bytes',1048576)
        unit='1 MiB' if threshold==1048576 else f'{threshold:,} bytes'
        lines.append(f"Observed so far at this site: {site.get('allocs',0):,} objects allocated. Freed quickly (before the program allocated another {unit}): about {site.get('short_share',0)}%. Freed later: about {site.get('long_freed_share',0)}%. Not freed so far: about {site.get('alive_share',0)}%.")
        lines.append('Percentages are sampled requested-byte shares; not freed so far means still alive at this observation. Counts and percentages are quantised; the allocation clock is batched.')
    if prompt=='v2-runtime-only' and not static:
        lines=[line for line in lines if line.startswith(('Program:', 'Observed so far', 'Percentages'))]
    return '\n'.join(lines)

def fit_state(text,url,timeout):
    """Fit code context while preserving the description and runtime sentences."""
    import re,urllib.request
    original=text.splitlines()
    def tokens(value):
        req=urllib.request.Request(url.rstrip('/')+'/tokenize',data=json.dumps({'content':value,'add_special':False}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=timeout) as response:return len(json.load(response)['tokens'])
    code=re.compile(r'^(?:>>|  ) \d+:')
    def clipped(width):
        return '\n'.join(line[:width] if code.match(line) else line for line in original)
    try:
        for width in (140,105,78,58,43,32,24,16,8):
            candidate=clipped(width)
            if tokens(candidate)<3000:return candidate
    except (OSError,ValueError,KeyError):pass
    # Conservative UTF-8 fallback keeps metadata and the marked call lines.
    keep=[line for line in original if not code.match(line) or line.startswith('>>')]
    candidate='\n'.join(keep)
    if len(candidate.encode())<=2800:return candidate
    # Protect runtime observations even if unusually long stack names exhaust space.
    runtime=[line for line in keep if line.startswith(('Observed so far','Percentages'))]
    tail='\n'.join(runtime);budget=max(0,2800-len(tail.encode())-1)
    prefix='\n'.join(line for line in keep if line not in runtime)
    return prefix.encode()[:budget].decode(errors='ignore')+'\n'+tail
