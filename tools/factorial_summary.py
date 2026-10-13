import re,collections,os,sys
rows=[l.split("|") for l in open((sys.argv[1] if len(sys.argv) > 1 else "results/pass11/results.md")) if re.match(r"\| (plausible|seed\d) \|",l)]
d={}
for r in rows:
    naming,wl,th,pol=[x.strip() for x in r[1:5]]
    d[(naming,wl,th,pol)]=float(r[5].split("[")[0])
namings=sorted({k[0] for k in d}); 
for g in ("0.6","0.7","0.8"):
    win=collections.Counter(); worse=collections.Counter(); best=collections.Counter()
    print("gate",g)
    for n in namings:
        cells=[]
        for wl in ("site-pure","site-mixed"):
            for th in ("1","16"):
                mi=d[(n,wl,th,"mi")]; m=d[(n,wl,th,"model-"+g)]; ne=d[(n,wl,th,"neutral-"+g)]; ru=d[(n,wl,th,"rule-"+g)]
                tag=("WIN " if m<ru-2 and m<ne-2 and m<mi-2 else "") + ("worse-than-mi" if m>mi+2 else "")
                cells.append("%s/%s: mi %.0f model %.0f neutral %.0f rule %.0f %s"%(wl[5:],th,mi,m,ne,ru,tag))
                win[n]+= (m<ru-2 and m<ne-2 and m<mi-2); worse[n]+= m>mi+2
        print("  %-9s wins %d/4  worse-than-mi %d/4 | "%(n,win[n],worse[n])+" ; ".join(cells))
