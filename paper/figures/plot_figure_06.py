from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

BASE=Path(__file__).resolve().parent.parent
DATA=BASE/'figure_data'
OUT=BASE/'outputs'
OUT.mkdir(exist_ok=True)
p=pd.read_csv(DATA/'figure06_platform_tests.csv')
INK='#243447'; GREEN='#009E73'; ORANGE='#E69F00'; MID='#6B7280'; LIGHT='#F7F9FB'; LIGHT_GREEN='#E9F6F1'; LIGHT_BLUE='#EAF4FB'; BORDER='#E1E6EB'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig=plt.figure(figsize=(11.2,5.25)); gs=fig.add_gridspec(1,2,width_ratios=[1.08,.92],wspace=.20)

# Shared panel background bounds make panels (a) and (b) visually equal in height.
def panel_background(ax):
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    ax.add_patch(FancyBboxPatch((.005,.035),.99,.885,boxstyle='round,pad=.008,rounding_size=.018',facecolor='white',edgecolor=BORDER,linewidth=.8,zorder=0))

ax=fig.add_subplot(gs[0,0]); panel_background(ax)
ax.text(.025,.965,'(a) Production-stack validation',fontsize=10.7,fontweight='bold',color=INK,va='top')
rows=[('Pair products','504 / 504'),('Common-referenced','504 / 504'),('Ancillary missing','0'),('Ancillary problems','0'),('Baseline rank','181 / 181'),('Full GEOC readiness','true')]
y_centers=np.linspace(.825,.395,len(rows))
for (label,val),y in zip(rows,y_centers):
    ax.add_patch(FancyBboxPatch((.03,y-.035),.94,.070,boxstyle='round,pad=.006,rounding_size=.012',facecolor=LIGHT,edgecolor='none'))
    ax.add_patch(Circle((.065,y),.014,facecolor=GREEN,edgecolor='none')); ax.text(.065,y,'✓',ha='center',va='center',fontsize=7.7,color='white',fontweight='bold')
    ax.text(.10,y,label,va='center',fontsize=8.35,color=INK); ax.text(.94,y,val,va='center',ha='right',fontsize=8.65,color=INK,fontweight='bold')

ax.text(.03,.305,'Numerical diagnostics',fontsize=8.3,fontweight='bold',color=ORANGE,va='top')
metrics=[('East/north/up\nmedian norm','1.000000'),('Maximum norm error','1.19 × 10⁻⁷'),('Baseline residual RMS','0.0155 m')]
for i,(lab,val) in enumerate(metrics):
    x=.03+i*.318
    ax.add_patch(FancyBboxPatch((x,.085),.295,.155,boxstyle='round,pad=.007,rounding_size=.012',facecolor='#FFF8E8',edgecolor='none'))
    ax.text(x+.015,.197,lab,fontsize=7.0,color=MID,va='top'); ax.text(x+.015,.116,val,fontsize=8.45,color=ORANGE,fontweight='bold',va='bottom')

ax2=fig.add_subplot(gs[0,1]); panel_background(ax2)
ax2.text(.025,.965,'(b) Portability tests',fontsize=10.7,fontweight='bold',color=INK,va='top')
y_centers=np.linspace(.81,.19,len(p))
for r,y in zip(p.itertuples(),y_centers):
    env_label = 'Windows production stack' if 'Windows' in r.environment else r.environment
    face=LIGHT_BLUE if 'Windows' in r.environment else LIGHT_GREEN
    ax2.add_patch(FancyBboxPatch((.03,y-.055),.94,.110,boxstyle='round,pad=.008,rounding_size=.014',facecolor=face,edgecolor='none'))
    ax2.add_patch(Circle((.925,y),.017,facecolor=GREEN,edgecolor='none')); ax2.text(.925,y,'✓',ha='center',va='center',fontsize=8.7,color='white',fontweight='bold')
    ax2.text(.065,y+.018,env_label,fontsize=8.2,fontweight='bold',color=INK,va='center')
    ax2.text(.065,y-.020,f'{r.python}  |  {r.plot_backend}',fontsize=7.35,color=MID,va='center')

fig.savefig(OUT/'Figure_06.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUT/'Figure_06.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUT/'Figure_06.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
