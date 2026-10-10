"""First-sight vs recheck accuracy of live model decisions against the oracle table.

usage: live_accuracy.py <results dir containing tables/ and logs/beelink/>
"""
import json,glob,collections,os,sys
R=sys.argv[1] if len(sys.argv)>1 else "results"
for w in ("cfrac","espresso"):
    truth={l.split()[0]:int(l.split()[1]) for l in open(f"{R}/tables/{w}/oracle.txt") if l.strip()}
    for f in sorted(glob.glob(f"{R}/logs/beelink/{w}-jev-live-*.decisions.jsonl")):
        rows=[json.loads(l) for l in open(f)]
        if not rows: continue
        mr=[r for r in rows if r.get("raw_response")]
        if not mr: continue
        first=collections.Counter(); re=collections.Counter(); last={}
        for r in rows:
            k=r["request"]["key"]; 
            if k not in truth or "response" not in r: continue
            ok=(r["response"]["class"]==truth[k], truth[k])
            (first if r["request"].get("prior") is None else re)[ok]+=1
            last[k]=r["response"]["class"]
        def fmt(c):
            n=sum(c.values()); a=sum(v for (ok,t),v in c.items() if ok)
            per=" ".join("%s %d/%d"%("SML"[t], c[(True,t)], c[(True,t)]+c[(False,t)]) for t in range(3))
            return "%d/%d=%.2f [%s]"%(a,n,a/max(n,1),per)
        fin=collections.Counter((last[k]==truth[k],truth[k]) for k in last)
        print(w, os.path.basename(f)[-28:-16], "rows",len(rows),"model",len(mr),"| first-sight",fmt(first),"| rechecks",fmt(re),"| final per site",fmt(fin))
        ex=[r for r in mr if r["request"].get("prior") is not None and r.get("model_request")][:1]
        if ex and w=="cfrac": print("   sample recheck state tail:", repr(ex[0]["model_request"]["state"][-420:]))
