from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/'figure_data'
OUTPUT=HERE.parent/'outputs'
OUTPUT.mkdir(parents=True,exist_ok=True)
pts=pd.read_csv(DATA / 'figure04_hyp3_reference_points.csv')
ref=pd.read_csv(DATA / 'figure04_reference_offsets.csv')
common=pd.read_csv(DATA / 'figure04_common_reference.csv').iloc[0]

INK='#243447'; BLUE='#0072B2'; SKY='#56B4E9'; GREEN='#009E73'; ORANGE='#E69F00'; VERM='#D55E00'; MID='#6B7280'; GRID='#DCE2E8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'axes.labelsize':9.2,'axes.titlesize':9.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig=plt.figure(figsize=(11.2,6.8))
gs=fig.add_gridspec(2,2,width_ratios=[1.13,1],height_ratios=[1,1],hspace=.34,wspace=.26)

# (a) density view avoids overplotting 504 nearly overlapping reference points.
ax=fig.add_subplot(gs[:,0])
cmap=LinearSegmentedColormap.from_list('refdensity',['#F2F7FB',SKY,BLUE])
hb=ax.hexbin(pts['hyp3_ref_lon'],pts['hyp3_ref_lat'],gridsize=32,mincnt=1,cmap=cmap,linewidths=0.15,edgecolors='white')
ax.scatter(pts['hyp3_ref_lon'],pts['hyp3_ref_lat'],s=6,color=BLUE,alpha=.16,linewidth=0,zorder=2)
ax.scatter([common['lon']],[common['lat']],marker='*',s=155,color=VERM,edgecolor='white',linewidth=.7,zorder=5)
ax.set_xlabel('Longitude (°)'); ax.set_ylabel('Latitude (°)')
ax.set_title('(a) Pair-specific reference density and selected common datum',loc='left',fontweight='bold')
ax.grid(color=GRID,lw=.55,alpha=.65)
ax.spines[['top','right']].set_visible(False)
cb=fig.colorbar(hb,ax=ax,fraction=.046,pad=.03)
cb.set_label('Pair references per hexagon',fontsize=8.5)
ax.text(.02,.02,'499 unique HyP3 reference coordinates\nCommon datum: 126.6676°W, 65.3359°N',transform=ax.transAxes,
        fontsize=8,color=INK,va='bottom',bbox=dict(boxstyle='round,pad=.3',facecolor='white',edgecolor=GRID,alpha=.92))

# (b) phase-shift distribution with central 95% interval.
ax2=fig.add_subplot(gs[0,1])
vals=ref['offset_rad'].to_numpy()
q025,q975=np.quantile(vals,[.025,.975]); med=np.median(vals)
ax2.hist(vals,bins=34,color=SKY,edgecolor='white',linewidth=.6)
ax2.axvspan(q025,q975,color=BLUE,alpha=.08,label='Central 95%')
ax2.axvline(0,color=INK,lw=.9,alpha=.6)
ax2.axvline(med,color=VERM,lw=1.4,ls='--',label=f'Median = {med:.2f} rad')
ax2.set_xlabel('Applied common-reference shift (rad)'); ax2.set_ylabel('Interferograms')
ax2.set_title('(b) Distribution of additive phase shifts',loc='left',fontweight='bold')
ax2.spines[['top','right']].set_visible(False); ax2.grid(axis='y',color=GRID,lw=.5,alpha=.55)
ax2.legend(frameon=False,fontsize=7.8,loc='upper right')

# (c) reference-window quality; color encodes temporal-baseline class.
def pair_dt(pair):
    a,b=pair.split('_')
    return (pd.to_datetime(b)-pd.to_datetime(a)).days
ref['dt_days']=ref['pair_id'].map(pair_dt)
colors={12:SKY,24:GREEN,36:ORANGE}
ax3=fig.add_subplot(gs[1,1])
for dt in [12,24,36]:
    d=ref[ref['dt_days']==dt]
    ax3.scatter(d['ref_median_coherence'],d['phase_mad_rad'],s=18,color=colors[dt],alpha=.62,edgecolor='none',label=f'{dt} d')
other=ref[~ref['dt_days'].isin([12,24,36])]
if len(other):
    ax3.scatter(other['ref_median_coherence'],other['phase_mad_rad'],s=18,color=MID,alpha=.55,edgecolor='none',label='Other')
ax3.axvline(ref['ref_median_coherence'].median(),color=INK,lw=.8,ls=':',alpha=.7)
ax3.axhline(ref['phase_mad_rad'].median(),color=INK,lw=.8,ls=':',alpha=.7)
ax3.set_xlabel('Median coherence in reference window'); ax3.set_ylabel('Phase MAD in window (rad)')
ax3.set_title('(c) Window quality across interferograms',loc='left',fontweight='bold')
ax3.spines[['top','right']].set_visible(False); ax3.grid(color=GRID,lw=.5,alpha=.55)
ax3.legend(frameon=False,ncol=3,fontsize=7.6,loc='upper right')

fig.savefig(OUTPUT / 'Figure_04.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUTPUT / 'Figure_04.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUTPUT / 'Figure_04.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
