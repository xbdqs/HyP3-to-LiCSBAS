from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'figure_data'
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)
df = pd.read_csv(DATA / 'figure05_baseline_residuals.csv')

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 8.8,
    'axes.labelsize': 9.2,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'savefig.dpi': 600,
})

# Color-blind-friendly palette (Okabe-Ito inspired)
BLUE = '#0072B2'
ORANGE = '#D55E00'
DARK = '#4D4D4D'
GRID = '#D9D9D9'

fig, axs = plt.subplots(
    1, 2,
    figsize=(11.2, 4.75),
    gridspec_kw={'width_ratios': [1.0, 1.18]},
)

# ---- (a) Pair-baseline reconstruction ----
ax = axs[0]
obs = df['observed_hyp3_baseline_m'].to_numpy()
rec = df['reconstructed_pair_baseline_m'].to_numpy()
lo = min(obs.min(), rec.min())
hi = max(obs.max(), rec.max())
pad = (hi - lo) * 0.035
lo_plot, hi_plot = lo - pad, hi + pad

ax.scatter(
    obs, rec,
    s=18,
    alpha=0.68,
    color=BLUE,
    edgecolor='white',
    linewidth=0.25,
    zorder=3,
)
ax.plot(
    [lo_plot, hi_plot], [lo_plot, hi_plot],
    color=DARK,
    lw=1.15,
    ls='--',
    zorder=2,
)
ax.set_xlim(lo_plot, hi_plot)
ax.set_ylim(lo_plot, hi_plot)
ax.set_xlabel('Observed HyP3 pair baseline (m)')
ax.set_ylabel('Reconstructed pair baseline (m)')
ax.set_aspect('equal', adjustable='box')
ax.spines[['top', 'right']].set_visible(False)
ax.grid(lw=0.55, color=GRID, alpha=0.75, zorder=0)

# ---- (b) Residuals through time ----
def midpoint(pair):
    a, b = pair.split('_')
    d1 = pd.to_datetime(a)
    d2 = pd.to_datetime(b)
    return d1 + (d2 - d1) / 2

ax = axs[1]
df['mid_date'] = df['pair_id'].map(midpoint)
df['residual_cm'] = df['residual_m'] * 100
ax.scatter(
    df['mid_date'], df['residual_cm'],
    s=18,
    alpha=0.72,
    color=ORANGE,
    edgecolor='white',
    linewidth=0.2,
    zorder=3,
)
ax.axhline(0, color=DARK, lw=1.05, zorder=2)
ax.set_xlabel('Interferogram midpoint date')
ax.set_ylabel('Baseline residual (cm)')
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', lw=0.55, color=GRID, alpha=0.75, zorder=0)

# Reserve dedicated space for aligned panel headings and a shared legend.
fig.subplots_adjust(left=0.085, right=0.985, bottom=0.205, top=0.845, wspace=0.26)
fig.canvas.draw()

# Panel labels and headings are figure-level text, aligned to each axes' left edge.
for ax_i, panel, title in [
    (axs[0], '(a)', 'Pair-baseline reconstruction'),
    (axs[1], '(b)', 'Reconstruction residuals through time'),
]:
    pos = ax_i.get_position()
    y = pos.y1 + 0.035
    fig.text(pos.x0, y, panel, fontsize=10.8, fontweight='bold', ha='left', va='bottom')
    fig.text(pos.x0 + 0.038, y, title, fontsize=9.8, fontweight='bold', ha='left', va='bottom')

# Shared legend below both panels: no overlap with data or axes labels.
legend_handles = [
    Line2D([0], [0], marker='o', linestyle='None', markersize=5.5,
           markerfacecolor=BLUE, markeredgecolor='white', markeredgewidth=0.3,
           label='HyP3 vs reconstructed pairs'),
    Line2D([0], [0], color=DARK, lw=1.15, ls='--', label='1:1 reference'),
    Line2D([0], [0], marker='o', linestyle='None', markersize=5.5,
           markerfacecolor=ORANGE, markeredgecolor='white', markeredgewidth=0.3,
           label='Reconstruction residuals'),
    Line2D([0], [0], color=DARK, lw=1.05, label='Zero-residual reference'),
]
fig.legend(
    handles=legend_handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.035),
    ncol=4,
    frameon=False,
    handlelength=2.0,
    columnspacing=1.7,
    handletextpad=0.55,
    fontsize=8.4,
)

for ext, kwargs in [
    ('png', {'dpi': 600}),
    ('tif', {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}}),
    ('pdf', {}),
]:
    fig.savefig(OUT / f'Figure_05.{ext}', bbox_inches='tight', facecolor='white', **kwargs)

plt.close(fig)
