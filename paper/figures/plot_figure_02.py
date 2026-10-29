from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'figure_data'
OUTPUT = HERE.parent / 'outputs'
OUTPUT.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATA / 'figure02_mapping.csv')

INK='#243447'; BLUE='#0072B2'; GREEN='#009E73'; ORANGE='#E69F00'; PURPLE='#CC79A7'; MID='#6B7280'
LIGHT_BLUE='#EAF4FB'; LIGHT_GREEN='#E9F6F1'; LIGHT_ORANGE='#FFF5DF'; LIGHT_PURPLE='#F8EDF6'; LIGHT_GRAY='#F4F6F8'

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig, ax = plt.subplots(figsize=(11.2, 7.0))
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

ax.text(0.02,0.965,'Semantic mapping from HyP3 products to LiCSBAS2-ready GEOC',fontsize=13,fontweight='bold',color=INK,va='top')
ax.text(0.02,0.925,'Each row identifies the source representation, the scientific transformation, and the exported representation.',fontsize=9,color=MID,va='top')

# Column headers.
headers=[(0.16,'ASF HyP3 GAMMA',BLUE),(0.50,'Transformation',INK),(0.84,'LiCSBAS2 / GEOC',GREEN)]
for x,t,c in headers:
    ax.text(x,0.875,t,ha='center',va='center',fontsize=10.5,fontweight='bold',color=c)
ax.plot([0.02,0.98],[0.845,0.845],color='#D7DCE1',lw=1)

category = {
    'Unwrapped phase': ('Raster + phase datum', BLUE, LIGHT_BLUE),
    'Coherence': ('Raster transform', BLUE, LIGHT_BLUE),
    'Amplitude': ('Ancillary raster', GREEN, LIGHT_GREEN),
    'Processing DEM': ('Ancillary raster', GREEN, LIGHT_GREEN),
    'Look geometry': ('Geometry reconstruction', GREEN, LIGHT_GREEN),
    'Pair baseline': ('Network reconstruction', ORANGE, LIGHT_ORANGE),
    'Acquisition metadata': ('Metadata semantics', PURPLE, LIGHT_PURPLE),
    'QC/provenance': ('Provenance', PURPLE, LIGHT_PURPLE),
}

y_values = [0.785,0.695,0.605,0.515,0.425,0.335,0.245,0.155]
for y, r in zip(y_values, df.itertuples()):
    cat, c, light = category.get(r.concept, ('Transform', INK, LIGHT_GRAY))
    # left/right cards
    for x, text, edge, fill in [(0.16,r.hyp3_input,BLUE,LIGHT_BLUE),(0.84,r.licsbas_output,GREEN,LIGHT_GREEN)]:
        ax.add_patch(FancyBboxPatch((x-0.145,y-0.032),0.29,0.064,
                                    boxstyle='round,pad=0.006,rounding_size=0.012',
                                    facecolor=fill,edgecolor=edge,linewidth=0.9))
        ax.text(x,y,text,ha='center',va='center',fontsize=8.0,color=INK)
    # middle transformation pill
    ax.add_patch(FancyBboxPatch((0.365,y-0.034),0.27,0.068,
                                boxstyle='round,pad=0.007,rounding_size=0.014',
                                facecolor=light,edgecolor=c,linewidth=1.0))
    ax.text(0.50,y+0.010,cat,ha='center',va='center',fontsize=8.2,fontweight='bold',color=c)
    ax.text(0.50,y-0.012,r.operation,ha='center',va='top',fontsize=7.15,color=INK,wrap=True)
    # direction arrows
    ax.add_patch(FancyArrowPatch((0.31,y),(0.355,y),arrowstyle='-|>',mutation_scale=10,lw=1.0,color=MID))
    ax.add_patch(FancyArrowPatch((0.645,y),(0.69,y),arrowstyle='-|>',mutation_scale=10,lw=1.0,color=MID))

# Legend emphasizes transformation classes.
legend_items=[('Raster / phase',BLUE),('Ancillary / geometry',GREEN),('Network',ORANGE),('Metadata / provenance',PURPLE)]
x0=0.22
for i,(lab,c) in enumerate(legend_items):
    x=x0+i*0.19
    ax.scatter([x],[0.065],s=42,color=c,marker='s')
    ax.text(x+0.014,0.065,lab,va='center',fontsize=7.8,color=INK)
ax.text(0.50,0.025,'No unsupported metadata values are fabricated.',ha='center',fontsize=8.4,fontstyle='italic',color=MID)

fig.savefig(OUTPUT / 'Figure_02.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUTPUT / 'Figure_02.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUTPUT / 'Figure_02.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
