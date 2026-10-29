from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, PowerNorm
from matplotlib.lines import Line2D

BASE=Path(__file__).resolve().parent.parent
DATA=BASE/'figure_data'
OUT=BASE/'outputs'
OUT.mkdir(exist_ok=True)
pts=pd.read_csv(DATA/'figure04_hyp3_reference_points.csv')
ref=pd.read_csv(DATA/'figure04_reference_offsets.csv')
common=pd.read_csv(DATA/'figure04_common_reference.csv').iloc[0]
INK='#243447'; BLUE='#08519C'; SKY='#4292C6'; GREEN='#009E73'; ORANGE='#E69F00'; VERM='#D55E00'; GRID='#DCE2E8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'axes.labelsize':9.2,'axes.titlesize':9.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig=plt.figure(figsize=(11.2,6.65))
gs=fig.add_gridspec(2,2,width_ratios=[1.13,1],height_ratios=[1,1],hspace=.36,wspace=.26)

ax=fig.add_subplot(gs[:,0])
# Darker sequential ramp + power normalization increases contrast without using a categorical palette.
cmap=LinearSegmentedColormap.from_list('refdensity',['#6BAED6','#4292C6','#3182BD','#2171B5','#084594'])
hb=ax.hexbin(pts['hyp3_ref_lon'],pts['hyp3_ref_lat'],gridsize=32,mincnt=1,cmap=cmap,norm=PowerNorm(gamma=.72),linewidths=.20,edgecolors='white')
ax.scatter([common['lon']],[common['lat']],marker='*',s=175,color=VERM,edgecolor='white',linewidth=.8,zorder=5)
ax.set_xlabel('Longitude (°)'); ax.set_ylabel('Latitude (°)'); ax.set_title('(a) Pair-specific reference density',loc='left',fontweight='bold')
ax.grid(color=GRID,lw=.55,alpha=.55); ax.spines[['top','right']].set_visible(False)
cb=fig.colorbar(hb,ax=ax,fraction=.046,pad=.03); cb.set_label('Pair references per hexagon',fontsize=8.5)

ax2=fig.add_subplot(gs[0,1])
vals=ref['offset_rad'].to_numpy(); q025,q975=np.quantile(vals,[.025,.975]); med=np.median(vals)
ax2.hist(vals,bins=34,color='#56B4E9',edgecolor='white',linewidth=.6)
ax2.axvspan(q025,q975,color='#0072B2',alpha=.08); ax2.axvline(0,color=INK,lw=.9,alpha=.55); ax2.axvline(med,color=VERM,lw=1.4,ls='--')
ax2.set_xlabel('Applied common-reference shift (rad)'); ax2.set_ylabel('Interferograms'); ax2.set_title('(b) Additive phase shifts',loc='left',fontweight='bold')
ax2.spines[['top','right']].set_visible(False); ax2.grid(axis='y',color=GRID,lw=.5,alpha=.55)

def pair_dt(pair):
    a,b=pair.split('_'); return (pd.to_datetime(b)-pd.to_datetime(a)).days
ref['dt_days']=ref['pair_id'].map(pair_dt); colors={12:'#56B4E9',24:GREEN,36:ORANGE}
ax3=fig.add_subplot(gs[1,1])
for dt in [12,24,36]:
    d=ref[ref['dt_days']==dt]; ax3.scatter(d['ref_median_coherence'],d['phase_mad_rad'],s=18,color=colors[dt],alpha=.70,edgecolor='none')
other=ref[~ref['dt_days'].isin([12,24,36])]
if len(other): ax3.scatter(other['ref_median_coherence'],other['phase_mad_rad'],s=18,color='#6B7280',alpha=.55,edgecolor='none')
ax3.set_xlabel('Median coherence in reference window'); ax3.set_ylabel('Phase median absolute deviation (rad)'); ax3.set_title('(c) Reference-window quality',loc='left',fontweight='bold')
ax3.spines[['top','right']].set_visible(False); ax3.grid(color=GRID,lw=.5,alpha=.55)
handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor=colors[12],markeredgecolor='none',markersize=6,label='12 d'),Line2D([0],[0],marker='o',color='none',markerfacecolor=colors[24],markeredgecolor='none',markersize=6,label='24 d'),Line2D([0],[0],marker='o',color='none',markerfacecolor=colors[36],markeredgecolor='none',markersize=6,label='36 d')]
ax3.legend(handles=handles,ncol=1,frameon=False,loc='center left',bbox_to_anchor=(1.01,.52),fontsize=7.8,handletextpad=.4,borderaxespad=0)
fig.subplots_adjust(right=.90)
fig.savefig(OUT/'Figure_04.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUT/'Figure_04.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUT/'Figure_04.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
