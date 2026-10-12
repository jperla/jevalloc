"""Plot the audited compaction medians without selecting a best model policy."""
import json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'build/plot-cache'))
os.environ.setdefault('XDG_CACHE_HOME', str(ROOT / 'build/plot-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter

base = ROOT / 'results/pass9'
data = json.loads((base / 'compaction-summary.json').read_text())
names = ['site-pure-1', 'site-pure-16', 'site-mixed-1', 'site-mixed-16',
         'redis-mesh', 'redis-drop', 'redis-sessions', 'sqlite', 'leveldb',
         'rocksdb-cache', 'rocksdb-churn']
assert set(data) == set(names)
plt.rcParams.update({'font.size': 10, 'svg.hashsalt': 'jevalloc-pass9'})
fig, axes = plt.subplots(1, 2, figsize=(11.5, 7.0), sharey=True,
                         gridspec_kw={'width_ratios': [1.3, 1]})
fig.subplots_adjust(left=.17, right=.98, bottom=.20, top=.85, wspace=.16)
purple, blue = '#713f9c', '#0068a8'

def value(name, variant):
    return data[name][variant]['idle10']['median']

for i, name in enumerate(names):
    for ax in axes:
        if i % 2 == 0:
            ax.axhspan(i - .5, i + .5, color='#f5f6f8', zorder=0)
    vs = data[name]
    if 'mesh' in vs and 'nomesh' in vs:
        x = [value(name, v) / 1048576 for v in ('mesh', 'nomesh')]
        axes[0].plot(x, [i, i], color=purple, alpha=.30, linewidth=2)
        axes[1].scatter(value(name, 'mesh') / value(name, 'nomesh'), i,
                        marker='D', s=44, color=purple, zorder=3)
    for variant, marker, color, face in [('mi', 'o', '#202a35', '#202a35'),
                                         ('mesh', 'D', purple, purple),
                                         ('nomesh', 'D', purple, 'white'),
                                         ('jev-live:static-model', 's', blue, blue)]:
        if variant in vs:
            axes[0].scatter(value(name, variant) / 1048576, i, marker=marker,
                            s=44, edgecolors=color, facecolors=face, zorder=4)
    if 'jev-live:static-model' in vs:
        axes[1].scatter(value(name, 'jev-live:static-model') / value(name, 'jev-keyonly'),
                        i, marker='s', s=44, color=blue, zorder=4)

for ax in axes:
    ax.set_xscale('log', base=2)
    ax.set_ylim(len(names) - .5, -.5)
    ax.grid(axis='x', color='#dce0e5', linewidth=.7)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#9aa3ac')
    ax.tick_params(axis='y', length=0, pad=10)
axes[0].set_yticks(range(len(names)), names)
axes[0].set_xlim(16, 512)
axes[0].xaxis.set_major_locator(FixedLocator([16, 32, 64, 128, 256, 512]))
axes[0].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:g}'))
axes[0].set_xlabel('10-second idle RSS (MiB)')
axes[1].set_xlim(.08, 1.35)
axes[1].xaxis.set_major_locator(FixedLocator([.125, .25, .5, 1]))
axes[1].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:g}×'))
axes[1].axvline(1, color='#808a94', linestyle='--', linewidth=1)
axes[1].set_xlabel('RSS / own baseline')
fig.suptitle('Placement and compaction at 10-second idle', fontsize=16, weight='bold', y=.97)
fig.text(.5, .91, 'Five interleaved repetitions per allocator and workload; medians shown.',
         ha='center', color='#52606d')
fig.text(.17, .12, 'Own baseline: nomesh for Mesh; jev-keyonly for Clef.', color='#52606d')
fig.text(.17, .087, 'Clef uses request context on the two mixed workloads.', color='#52606d')
handles = [plt.Line2D([], [], marker=m, linestyle='', color=c, markerfacecolor=f,
                      markersize=7, label=label)
           for label, m, c, f in [('mimalloc', 'o', '#202a35', '#202a35'),
                                  ('Mesh', 'D', purple, purple),
                                  ('nomesh', 'D', purple, 'white'),
                                  ('Clef static-model', 's', blue, blue)]]
fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.56, .015),
           ncol=4, frameon=False)
fig.savefig(base / 'compaction-comparison.png', dpi=180)
fig.savefig(base / 'compaction-comparison.svg', metadata={'Date': None})
plt.close(fig)
