from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/'figure_data'
OUTPUT=HERE.parent/'outputs'
OUTPUT.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(DATA / 'figure06_validation_metrics.csv')
p=pd.read_csv(DATA / 'figure06_platform_tests.csv')

INK='#243447'; BLUE='#0072B2'; GREEN='#009E73'; ORANGE='#E69F00'; VERM='#D55E00'; SKY='#56B4E9'; MID='#6B7280'; GRID='#DCE2E8'; LIGHT='#F7F9FB'; LIGHT_GREEN='#E9F6F1'; LIGHT_BLUE='#EAF4FB'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig=plt.figure(figsize=(11.2,5.7))
gs=fig.add_gridspec(1,2,width_ratios=[1.08,.92],wspace=.20)

# (a) Validation gates: a visual scorecard, not a raw table.
ax=fig.add_subplot(gs[0,0]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.02,.965,'(a) Real MGX production validation',fontsize=10.7,fontweight='bold',color=INK,va='top')
ax.text(.02,.915,'Readiness gates',fontsize=8.3,fontweight='bold',color=BLUE,va='top')
rows=[
    ('Pair products','504 / 504','complete'),
    ('Common-referenced','504 / 504','complete'),
    ('Ancillary missing','0','none'),
    ('Ancillary problems','0','none'),
    ('Baseline rank','181 / 181','full rank'),
    ('Full GEOC readiness','true','ready'),
]
y=.84
for label,val,note in rows:
    ax.add_patch(FancyBboxPatch((.02,y-.045),.96,.075,boxstyle='round,pad=.006,rounding_size=.012',facecolor=LIGHT,edgecolor='none'))
    ax.add_patch(Circle((.055,y-.007),.015,facecolor=GREEN,edgecolor='none'))
    ax.text(.055,y-.007,'✓',ha='center',va='center',fontsize=8,color='white',fontweight='bold')
    ax.text(.09,y,label,va='center',fontsize=8.4,color=INK)
    ax.text(.72,y,val,va='center',ha='right',fontsize=8.5,color=INK,fontweight='bold')
    ax.text(.95,y,note,va='center',ha='right',fontsize=7.5,color=MID)
    y-=.105

ax.text(.02,.19,'Numerical diagnostics',fontsize=8.3,fontweight='bold',color=ORANGE,va='top')
diag=[('ENU median norm','1.000000'),('ENU max norm error','1.19 × 10⁻⁷'),('Baseline RMS residual','0.0155 m')]
y=.125
for label,val in diag:
    ax.text(.05,y,label,va='center',fontsize=8.0,color=INK)
    ax.text(.95,y,val,va='center',ha='right',fontsize=8.2,color=ORANGE,fontweight='bold')
    y-=.055

# (b) Portability tests shown as cards with backend emphasis.
ax2=fig.add_subplot(gs[0,1]); ax2.set_xlim(0,1); ax2.set_ylim(0,1); ax2.axis('off')
ax2.text(.02,.965,'(b) Portability and plotting-backend tests',fontsize=10.7,fontweight='bold',color=INK,va='top')
y=.855
for r in p.itertuples():
    face=LIGHT_BLUE if 'Windows' in r.environment else LIGHT_GREEN
    edge=BLUE if 'Windows' in r.environment else GREEN
    ax2.add_patch(FancyBboxPatch((.02,y-.065),.96,.105,boxstyle='round,pad=.008,rounding_size=.014',facecolor=face,edgecolor='none'))
    ax2.add_patch(Circle((.93,y-.012),.018,facecolor=GREEN,edgecolor='none'))
    ax2.text(.93,y-.012,'✓',ha='center',va='center',fontsize=9,color='white',fontweight='bold')
    ax2.text(.055,y+.010,r.environment,fontsize=8.3,fontweight='bold',color=INK,va='center')
    ax2.text(.055,y-.025,f'{r.python}  |  {r.plot_backend}',fontsize=7.45,color=MID,va='center')
    y-=.145
ax2.text(.02,.08,'The plotting fallback changes presentation only; scientific rasters and metadata use the same code path.',fontsize=7.7,color=MID,va='top',wrap=True)

fig.savefig(OUTPUT / 'Figure_06.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUTPUT / 'Figure_06.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUTPUT / 'Figure_06.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
