from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'figure_data'
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)
INK='#243447'; BLUE='#0072B2'; GREEN='#009E73'; ORANGE='#E69F00'; VERM='#D55E00'
LIGHT_BLUE='#EAF4FB'; LIGHT_GREEN='#E9F6F1'; LIGHT_ORANGE='#FFF5DF'; LIGHT_GRAY='#F4F6F8'; MID='#657384'

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
fig, ax = plt.subplots(figsize=(11.2,4.7))
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

# Four balanced processing domains.
bands=[
    (0.018,0.09,0.155,0.75,'SOURCE',LIGHT_GRAY,INK),
    (0.188,0.09,0.245,0.75,'AUDIT & PLAN',LIGHT_BLUE,BLUE),
    (0.448,0.09,0.305,0.75,'CONVERT & RECONSTRUCT',LIGHT_GREEN,GREEN),
    (0.768,0.09,0.215,0.75,'VALIDATE & EXPORT',LIGHT_ORANGE,ORANGE),
]
for x,y,w,h,title,face,accent in bands:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.006,rounding_size=.018',facecolor=face,edgecolor='none',zorder=0))
    ax.add_patch(FancyBboxPatch((x,y),.008,h,boxstyle='round,pad=0,rounding_size=.006',facecolor=accent,edgecolor='none',zorder=1))
    ax.text(x+.018,y+h-.045,title,va='top',fontsize=8.6,fontweight='bold',color=accent,zorder=5)

# A single, ordered processing path prevents crossed/hidden arrows.
pos={
    'A':(.096,.48),
    'B':(.310,.62), 'C':(.310,.31),
    'D':(.600,.62), 'E':(.600,.31),
    'F':(.875,.62), 'G':(.875,.31),
}
box_cfg={
    'A':(.135,.205,INK),'B':(.190,.185,BLUE),'C':(.190,.185,BLUE),
    'D':(.225,.185,GREEN),'E':(.225,.185,GREEN),'F':(.165,.185,ORANGE),'G':(.165,.185,VERM)
}
content={
    'A':('HyP3 GAMMA\nproducts','phase • coherence\namplitude • elevation\nlook vectors'),
    'B':('Preflight &\nnetwork audit','inventory • footprint • graph'),
    'C':('Common-reference\nplan','candidate scoring • reusable plan'),
    'D':('Common-grid\nconversion','phase harmonization • coherence scaling'),
    'E':('Network &\ngeometry','baseline least squares • viewing geometry'),
    'F':('Validation &\nprovenance','structure • completeness • audit trail'),
    'G':('LiCSBAS2-ready\nGEOC','pair stack • metadata • baselines'),
}

for nid,(x,y) in pos.items():
    w,h,edge=box_cfg[nid]
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.010,rounding_size=.018',facecolor='white',edgecolor=edge,linewidth=1.45,zorder=4))
    title,sub=content[nid]
    ax.text(x,y+.035,title,ha='center',va='center',color=INK,fontsize=7.75,fontweight='bold' if nid in {'A','G'} else 'semibold',zorder=5)
    ax.text(x,y-.050,sub,ha='center',va='center',color=MID,fontsize=5.95,linespacing=1.25,zorder=5)

# Orthogonal arrows routed only through whitespace between cards.
def ortho_arrow(points, color):
    verts=[]; codes=[]
    for i,(x,y) in enumerate(points):
        verts.append((x,y)); codes.append(MplPath.MOVETO if i==0 else MplPath.LINETO)
    path=MplPath(verts,codes)
    ax.add_patch(PathPatch(path,fill=False,lw=1.55,edgecolor=color,capstyle='round',joinstyle='round',zorder=2))
    # arrowhead on final segment
    x1,y1=points[-2]; x2,y2=points[-1]
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=11.5,linewidth=0,color=color,zorder=3))

# A -> B
wa,ha,_=box_cfg['A']; wb,hb,_=box_cfg['B']
ortho_arrow([(pos['A'][0]+wa/2,pos['A'][1]),(.190,pos['A'][1]),(.190,pos['B'][1]),(pos['B'][0]-wb/2-.006,pos['B'][1])],BLUE)
# B -> C (vertical)
ortho_arrow([(pos['B'][0],pos['B'][1]-hb/2), (pos['C'][0],pos['C'][1]+box_cfg['C'][1]/2+.006)],BLUE)
# C -> D
wc,hc,_=box_cfg['C']; wd,hd,_=box_cfg['D']
ortho_arrow([(pos['C'][0]+wc/2,pos['C'][1]),(.445,pos['C'][1]),(.445,pos['D'][1]),(pos['D'][0]-wd/2-.006,pos['D'][1])],GREEN)
# D -> E
ortho_arrow([(pos['D'][0],pos['D'][1]-hd/2),(pos['E'][0],pos['E'][1]+box_cfg['E'][1]/2+.006)],GREEN)
# E -> F
we,he,_=box_cfg['E']; wf,hf,_=box_cfg['F']
ortho_arrow([(pos['E'][0]+we/2,pos['E'][1]),(.758,pos['E'][1]),(.758,pos['F'][1]),(pos['F'][0]-wf/2-.006,pos['F'][1])],ORANGE)
# F -> G
ortho_arrow([(pos['F'][0],pos['F'][1]-hf/2),(pos['G'][0],pos['G'][1]+box_cfg['G'][1]/2+.006)],VERM)

ax.text(.018,.955,'HyP3-to-LiCSBAS processing architecture',ha='left',va='top',fontsize=13.2,fontweight='bold',color=INK)
fig.savefig(OUT/'Figure_01.png',dpi=600,bbox_inches='tight',facecolor='white')
fig.savefig(OUT/'Figure_01.tif',dpi=600,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(OUT/'Figure_01.pdf',bbox_inches='tight',facecolor='white')
plt.close(fig)
