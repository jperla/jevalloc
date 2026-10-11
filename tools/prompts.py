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
def criteria(name): return CRITERIA

def state(request,static=False,prompt='v2'):
    frames=[dict(f,address=f.get('address',f.get('addr','0x0'))) for f in request.get('frames',[])]
    symbolize([{'frames':[f for f in frames if 'function' not in f]}])
    program=request.get('program','unknown')
    description=Path(__file__).resolve().parents[1]/'descriptions'/(Path(program).name+'.txt')
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
