from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE=Path(__file__).resolve().parent.parent
DATA=BASE/'figure_data'
OUT=BASE/'outputs'
OUT.mkdir(exist_ok=True)
df=pd.read_csv(DATA/'figure02_mapping.csv')
# Remove defensive wording from the visual while preserving the scientific mapping.
df.loc[df['concept']=='Acquisition metadata','operation']='Direct + transparently derived fields'
df.loc[df['concept']=='QC/provenance','operation']='Audit trail + transformation records'
df.loc[df['concept']=='Processing DEM','operation']='Warp processing digital elevation model'
df.loc[df['concept']=='Look geometry','operation']='Convert angles to unit line-of-sight components'
df.loc[df['concept']=='Acquisition metadata','hyp3_input']='UTCTime, heading,\nslant range, elevation source'

INK='#243447'; BLUE='#0072B2'; GREEN='#009E73'; ORANGE='#E69F00'; PURPLE='#CC79A7'; MID='#6B7280'
LIGHT_BLUE='#EAF4FB'; LIGHT_GREEN='#E9F6F1'; LIGHT_ORANGE='#FFF5DF'; LIGHT_PURPLE='#F8EDF6'; LIGHT_GRAY='#F4F6F8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig,ax=plt.subplots(figsize=(11.2,6.75)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

ax.text(.02,.965,'Semantic mapping from HyP3 products to the LiCSBAS2 geocoded (GEOC) structure',fontsize=13,fontweight='bold',color=INK,va='top')
headers=[(.16,'Alaska Satellite Facility (ASF) HyP3',BLUE),(.50,'Transformation',INK),(.84,'LiCSBAS2 / GEOC',GREEN)]
for x,t,c in headers: ax.text(x,.885,t,ha='center',va='center',fontsize=9.2,fontweight='bold',color=c)
ax.plot([.02,.98],[.852,.852],color='#D7DCE1',lw=1)

category={
'Unwrapped phase':('Raster + phase datum',BLUE,LIGHT_BLUE),'Coherence':('Raster transform',BLUE,LIGHT_BLUE),
'Amplitude':('Ancillary raster',GREEN,LIGHT_GREEN),'Processing DEM':('Ancillary raster',GREEN,LIGHT_GREEN),
'Look geometry':('Geometry reconstruction',GREEN,LIGHT_GREEN),'Pair baseline':('Network reconstruction',ORANGE,LIGHT_ORANGE),
'Acquisition metadata':('Metadata semantics',PURPLE,LIGHT_PURPLE),'QC/provenance':('Quality control / provenance',PURPLE,LIGHT_PURPLE)}

y_values=[.795,.705,.615,.525,.435,.345,.255,.165]
for y,r in zip(y_values,df.itertuples()):
    cat,c,light=category.get(r.concept,('Transform',INK,LIGHT_GRAY))
    for x,text,edge,fill in [(.16,r.hyp3_input,BLUE,LIGHT_BLUE),(.84,r.licsbas_output,GREEN,LIGHT_GREEN)]:
        ax.add_patch(FancyBboxPatch((x-.145,y-.031),.29,.062,boxstyle='round,pad=.006,rounding_size=.012',facecolor=fill,edgecolor=edge,linewidth=.9))
        ax.text(x,y,text,ha='center',va='center',fontsize=7.95,color=INK)
    ax.add_patch(FancyBboxPatch((.365,y-.033),.27,.066,boxstyle='round,pad=.007,rounding_size=.014',facecolor=light,edgecolor=c,linewidth=1.0))
    ax.text(.50,y+.010,cat,ha='center',va='center',fontsize=8.15,fontweight='bold',color=c)
    ax.text(.50,y-.013,r.operation,ha='center',va='top',fontsize=7.05,color=INK)
    ax.add_patch(FancyArrowPatch((.31,y),(.355,y),arrowstyle='-|>',mutation_scale=10,lw=1.0,color=MID))
    ax.add_patch(FancyArrowPatch((.645,y),(.69,y),arrowstyle='-|>',mutation_scale=10,lw=1.0,color=MID))

legend=[('Raster / phase',BLUE),('Ancillary / geometry',GREEN),('Network',ORANGE),('Metadata / provenance',PURPLE)]
for i,(lab,c) in enumerate(legend):
    x=.22+i*.19; ax.scatter([x],[.065],s=42,color=c,marker='s'); ax.text(x+.014,.065,lab,va='center',fontsize=7.8,color=INK)

fig.savefig(OUT/'Figure_02.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUT/'Figure_02.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUT/'Figure_02.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
