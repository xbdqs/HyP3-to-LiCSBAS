from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

BASE=Path(__file__).resolve().parent.parent
DATA=BASE/'figure_data'
OUT=BASE/'outputs'
OUT.mkdir(exist_ok=True)
edges=pd.read_csv(DATA/'figure03_network_edges.csv',dtype={'date1':str,'date2':str})
b=pd.read_csv(DATA/'figure03_acquisition_baselines.csv',dtype={'date':str})
b['dt']=pd.to_datetime(b['date'],format='%Y%m%d')
bmap=dict(zip(b['date'],b['bperp_m'])); dmap=dict(zip(b['date'],b['dt']))
INK='#243447'; BLUE='#0072B2'; SKY='#56B4E9'; GREEN='#009E73'; ORANGE='#E69F00'; VERM='#D55E00'; GRID='#DCE2E8'
edge_colors={12:SKY,24:GREEN,36:ORANGE}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9.5,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig,ax=plt.subplots(figsize=(11.2,5.25))
for r in edges.itertuples():
    d1=str(r.date1); d2=str(r.date2); dtb=int(r.temporal_baseline_days)
    ax.plot([dmap[d1],dmap[d2]],[bmap[d1],bmap[d2]],color=edge_colors.get(dtb,'#9CA3AF'),linewidth=.62,alpha=.34,zorder=1)
ax.scatter(b['dt'],b['bperp_m'],s=17,color=BLUE,edgecolor='white',linewidth=.25,zorder=3)
master='20230115'; mb=b.loc[b['date']==master].iloc[0]
ax.scatter([mb['dt']],[mb['bperp_m']],s=110,marker='*',color=VERM,edgecolor='white',linewidth=.7,zorder=5)
leaf='20220905'; lb=b.loc[b['date']==leaf].iloc[0]
ax.scatter([lb['dt']],[lb['bperp_m']],s=60,facecolors='white',edgecolors=INK,linewidth=1.2,zorder=5)
ax.axhline(0,color=INK,lw=.8,alpha=.5,zorder=0)
ax.set_ylabel('Perpendicular baseline relative to 2023-01-15 (m)'); ax.set_xlabel('Acquisition date')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.grid(axis='y',color=GRID,lw=.6,alpha=.8); ax.spines[['top','right']].set_visible(False); ax.margins(x=.01)
handles=[Line2D([0],[0],color=SKY,lw=2,label='12 d'),Line2D([0],[0],color=GREEN,lw=2,label='24 d'),Line2D([0],[0],color=ORANGE,lw=2,label='36 d'),Line2D([0],[0],marker='*',color='none',markerfacecolor=VERM,markeredgecolor='white',markersize=10,label='Baseline datum'),Line2D([0],[0],marker='o',color='none',markerfacecolor='white',markeredgecolor=INK,markersize=6,label='Leaf acquisition')]
fig.legend(handles=handles,ncol=5,frameon=False,loc='upper center',bbox_to_anchor=(.5,.995),fontsize=8.2,columnspacing=1.5,handlelength=2.0)
fig.subplots_adjust(top=.88,bottom=.13,left=.09,right=.99)
fig.savefig(OUT/'Figure_03.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUT/'Figure_03.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUT/'Figure_03.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
