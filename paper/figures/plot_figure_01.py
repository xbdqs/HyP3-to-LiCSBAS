from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'figure_data'
OUTPUT = HERE.parent / 'outputs'
OUTPUT.mkdir(parents=True, exist_ok=True)
nodes = pd.read_csv(DATA / 'figure01_nodes.csv').set_index('id')

# Colorblind-safe, publication-oriented palette.
INK = '#243447'
BLUE = '#0072B2'
SKY = '#56B4E9'
GREEN = '#009E73'
ORANGE = '#E69F00'
VERMILION = '#D55E00'
LIGHT_BLUE = '#EAF4FB'
LIGHT_GREEN = '#E9F6F1'
LIGHT_ORANGE = '#FFF5DF'
LIGHT_GRAY = '#F4F6F8'
MID_GRAY = '#6B7280'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 9,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'savefig.dpi': 600,
})

fig, ax = plt.subplots(figsize=(11.2, 5.0))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Four workflow bands make the logic scannable without crossing arrows.
bands = [
    (0.015, 0.08, 0.16, 0.80, 'SOURCE', LIGHT_GRAY, INK),
    (0.19, 0.08, 0.24, 0.80, 'AUDIT & PLAN', LIGHT_BLUE, BLUE),
    (0.45, 0.08, 0.30, 0.80, 'CONVERT & RECONSTRUCT', LIGHT_GREEN, GREEN),
    (0.77, 0.08, 0.215, 0.80, 'VALIDATE & EXPORT', LIGHT_ORANGE, ORANGE),
]
for x, y, w, h, title, face, accent in bands:
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.006,rounding_size=0.018',
                                facecolor=face, edgecolor='none', zorder=0))
    ax.add_patch(FancyBboxPatch((x, y), 0.008, h,
                                boxstyle='round,pad=0,rounding_size=0.006',
                                facecolor=accent, edgecolor='none', zorder=1))
    ax.text(x + 0.018, y + h - 0.045, title, color=accent,
            fontsize=8.4, fontweight='bold', va='top')

# Manual positions chosen for a clean left-to-right narrative.
pos = {
    'A': (0.095, 0.48),
    'B': (0.305, 0.64),
    'C': (0.305, 0.34),
    'D': (0.555, 0.64),
    'E': (0.655, 0.34),
    'F': (0.835, 0.64),
    'G': (0.895, 0.34),
}
box_cfg = {
    'A': (0.125, 0.18, 'white', INK),
    'B': (0.18, 0.16, 'white', BLUE),
    'C': (0.18, 0.16, 'white', BLUE),
    'D': (0.205, 0.16, 'white', GREEN),
    'E': (0.205, 0.16, 'white', GREEN),
    'F': (0.16, 0.16, 'white', ORANGE),
    'G': (0.16, 0.16, 'white', VERMILION),
}

for nid, (x, y) in pos.items():
    w, h, face, edge = box_cfg[nid]
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                                boxstyle='round,pad=0.012,rounding_size=0.020',
                                facecolor=face, edgecolor=edge, linewidth=1.4, zorder=3))
    label = nodes.loc[nid, 'label']
    label_overrides = {
        'B':'Preflight &\nnetwork audit',
        'C':'Common-reference\nplanning',
        'D':'Common grid &\nphase/coherence conversion',
        'E':'Baseline inversion &\nancillary reconstruction',
        'F':'Validation &\nprovenance',
        'G':'LiCSBAS2-ready\nGEOC',
    }
    label = label_overrides.get(nid, label)
    ax.text(x, y, label, ha='center', va='center', color=INK,
            fontsize=9.1, fontweight='semibold' if nid in {'A','G'} else 'normal',
            linespacing=1.25, zorder=4)

# Clean orthogonal flow. Secondary arrows are dashed.
def arrow(a, b, color, rad=0.0, dashed=False):
    x1, y1 = pos[a]; x2, y2 = pos[b]
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle='-|>', mutation_scale=12,
                                connectionstyle=f'arc3,rad={rad}',
                                linewidth=1.35, color=color,
                                linestyle='--' if dashed else '-',
                                shrinkA=46, shrinkB=46, zorder=2))

arrow('A','B',BLUE,rad=0.04)
arrow('A','C',BLUE,rad=-0.04)
arrow('B','D',GREEN)
arrow('C','D',GREEN,rad=-0.08)
arrow('C','E',GREEN)
arrow('D','E',GREEN,rad=-0.10,dashed=True)
arrow('D','F',ORANGE)
arrow('E','F',ORANGE,rad=0.08)
arrow('F','G',VERMILION,rad=-0.06)

# Small evidence labels reinforce what each stage produces.
ax.text(0.305, 0.50, 'inventory • network • footprints', ha='center', va='center',
        fontsize=7.6, color=MID_GRAY)
ax.text(0.600, 0.49, 'common grid • phase datum • baselines • E/N/U', ha='center', va='center',
        fontsize=7.6, color=MID_GRAY)
ax.text(0.865, 0.49, 'QC • provenance • restart-safe outputs', ha='center', va='center',
        fontsize=7.6, color=MID_GRAY)

# Persistent provenance lane.
ax.plot([0.20, 0.965], [0.145, 0.145], color=MID_GRAY, linewidth=0.8, alpha=0.5)
ax.text(0.205, 0.118, 'Machine-readable audit trail: plan → offsets → conversion records → validation',
        ha='left', va='top', fontsize=7.8, color=MID_GRAY)

ax.text(0.015, 0.965, 'HyP3-to-LiCSBAS processing architecture',
        ha='left', va='top', fontsize=13, fontweight='bold', color=INK)
ax.text(0.015, 0.925,
        'Scientific transformations are separated from downstream LiCSBAS2 quality control.',
        ha='left', va='top', fontsize=9, color=MID_GRAY)

fig.savefig(OUTPUT / 'Figure_01.png', dpi=600, bbox_inches='tight', facecolor='white')
fig.savefig(OUTPUT / 'Figure_01.tif', dpi=600, bbox_inches='tight', facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUTPUT / 'Figure_01.pdf', bbox_inches='tight', facecolor='white')
plt.close(fig)
