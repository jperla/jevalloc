#!/usr/bin/env python3
"""Plot complete, audited fragmentation blocks; no cold or partial groups."""
import argparse,hashlib,json,math,statistics
from pathlib import Path
from selection import complete_groups
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('matrix',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=json.loads(a.matrix.read_text());audit=json.loads(a.matrix.with_suffix('.inference-audit.json').read_text())
assert d['configuration']['class_schema']=='transient-permanent-v1'
assert audit['overlapping_runs']==0 and audit['matrix_sha256']==hashlib.sha256(a.matrix.read_bytes()).hexdigest()
g,names=complete_groups(d);assert names
variants=['mi','jev-table:oracle','jev-live:heuristic','jev-live:static-model','jev-live:model']
labels=['mimalloc','Oracle','Heuristic','Clef: code only','Clef: runtime']
colors=['#64748b','#1565c0','#2b8c5a','#d08b2c','#725ac1']
fig,axes=plt.subplots(math.ceil(len(names)/2),2,figsize=(11,3.35*math.ceil(len(names)/2)+1),squeeze=False)
for ax,b in zip(axes.flat,names):
    med,lo,hi=[],[],[]
    for v in variants:
        values=[max((p for p in r['phases'] if p['phase']=='idle'),key=lambda p:p['cycle'])['rss_bytes']/2**20 for r in g[b,v]]
        mid=statistics.median(values);med.append(mid);lo.append(mid-min(values));hi.append(max(values)-mid)
    ax.barh(range(len(variants)),med,color=colors,height=.62,xerr=[lo,hi],error_kw=dict(ecolor='#18212c',capsize=2,lw=.8))
    for i,value in enumerate(med):ax.text(value+max(med)*.035,i,f'{value:.1f}',va='center',fontsize=9)
    ax.set(yticks=range(len(labels)),yticklabels=labels,xlabel='Final-idle RSS (MiB)',title=b,xlim=(0,max(med)*1.25))
    ax.invert_yaxis();ax.set_axisbelow(True);ax.grid(axis='x',alpha=.16)
    for edge in ('top','right','left'):ax.spines[edge].set_visible(False)
for ax in list(axes.flat)[len(names):]:ax.set_visible(False)
fig.suptitle('Transient/permanent allocation: idle memory',fontsize=17,y=.98)
fig.text(.5,.94,'Five interleaved warm repetitions per block; lower RSS is better.',ha='center',fontsize=10)
fig.text(.5,.02,'Bars: medians. Whiskers: min–max. Accepted blocks only; zero audited model-inference overlaps.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.91));a.output.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(a.output.with_suffix('.png'),dpi=160);plt.rcParams['svg.fonttype']='none';fig.savefig(a.output.with_suffix('.svg'))
