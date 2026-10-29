from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/'figure_data'
OUTPUT=HERE.parent/'outputs'
OUTPUT.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(DATA / 'figure05_baseline_residuals.csv')

INK='#243447'; BLUE='#0072B2'; SKY='#56B4E9'; ORANGE='#E69F00'; VERM='#D55E00'; GREEN='#009E73'; MID='#6B7280'; GRID='#DCE2E8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'axes.labelsize':9.2,'axes.titlesize':9.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig,axs=plt.subplots(1,2,figsize=(11.2,4.7),gridspec_kw={'width_ratios':[1,1.18]})

# (a) Parity plot, deliberately light because the reconstruction is nearly exact.
ax=axs[0]
obs=df['observed_hyp3_baseline_m'].to_numpy(); rec=df['reconstructed_pair_baseline_m'].to_numpy()
lo=min(obs.min(),rec.min()); hi=max(obs.max(),rec.max())
ax.scatter(obs,rec,s=17,color=BLUE,alpha=.62,edgecolor='white',linewidth=.25)
ax.plot([lo,hi],[lo,hi],color=INK,lw=1.0,ls='--',label='1:1')
ax.set_xlabel('Observed HyP3 pair baseline (m)'); ax.set_ylabel('Reconstructed pair baseline (m)')
ax.set_title('(a) Pair-baseline reconstruction',loc='left',fontweight='bold')
ax.spines[['top','right']].set_visible(False); ax.grid(color=GRID,lw=.5,alpha=.55)
ax.set_aspect('equal',adjustable='box')

# (b) Residuals through time reveal whether mismatch is systematic.
ax=axs[1]
def midpoint(pair):
    a,b=pair.split('_')
    d1=pd.to_datetime(a); d2=pd.to_datetime(b)
    return d1+(d2-d1)/2
df['mid_date']=df['pair_id'].map(midpoint)
df['residual_cm']=df['residual_m']*100.0
out=np.abs(df['residual_m'])>0.05
ax.scatter(df.loc[~out,'mid_date'],df.loc[~out,'residual_cm'],s=14,color=SKY,alpha=.58,edgecolor='none',label='|r| ≤ 5 cm')
ax.scatter(df.loc[out,'mid_date'],df.loc[out,'residual_cm'],s=28,color=VERM,alpha=.9,edgecolor='white',linewidth=.3,label='|r| > 5 cm',zorder=4)
ax.axhline(0,color=INK,lw=.9)
ax.axhline(5,color=ORANGE,lw=.8,ls='--',alpha=.75); ax.axhline(-5,color=ORANGE,lw=.8,ls='--',alpha=.75)
ax.set_xlabel('Interferogram midpoint date'); ax.set_ylabel('Baseline residual (cm)')
ax.set_title('(b) Network residuals through time',loc='left',fontweight='bold')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color=GRID,lw=.5,alpha=.55)
ax.legend(frameon=False,fontsize=7.7,loc='upper left')

rms=np.sqrt(np.mean(df['residual_m']**2)); med=np.median(np.abs(df['residual_m'])); mx=np.max(np.abs(df['residual_m']))
ax.text(.985,.03,f'RMS = {rms:.4f} m\nMedian |r| = {med:.4f} m\nMax |r| = {mx:.3f} m',transform=ax.transAxes,
        ha='right',va='bottom',fontsize=8,color=INK,bbox=dict(boxstyle='round,pad=.3',facecolor='white',edgecolor=GRID,alpha=.94))

fig.tight_layout(w_pad=2.2)
fig.savefig(OUTPUT / 'Figure_05.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUTPUT / 'Figure_05.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUTPUT / 'Figure_05.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
