from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch, Arc
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':10,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(6.6,4.4));ax.set_aspect('equal');ax.set_xlim(-1.4,5.2);ax.set_ylim(-2.25,2.25);ax.axis('off')
for r in np.arange(1.0,4.9,.35):ax.add_patch(Circle((0,0),r,fill=False,color='#aab4c2',lw=.85))
ax.plot(0,0,'o',color='#333',ms=4);ax.text(-.15,-.3,'盘心',ha='right')
ax.add_patch(Rectangle((3.05,-.85),.86,1.7,facecolor='#ffdc9d',edgecolor='#b47915',alpha=.65,lw=1.4))
for y in [-.65,.65]:
 x=3.48; ang=np.arctan2(y,x); dx=.8*np.cos(ang);dy=.8*np.sin(ang)
 ax.add_patch(FancyArrowPatch((x,y),(x+dx,y+dy),arrowstyle='-|>',mutation_scale=13,lw=1.6,color='#a3403c'))
ax.plot([0,3.5],[0,0],ls='--',color='#444');ax.text(1.7,.12,'$r$',fontsize=14)
ax.annotate('',xy=(4.18,.85),xytext=(4.18,-.85),arrowprops=dict(arrowstyle='<->',color='#444'));ax.text(4.32,0,'$B$',fontsize=14,va='center')
ax.text(3.5,1.2,'局部照明区',ha='center');ax.text(3.9,-1.25,'局部色散方向',color='#a3403c',ha='center')
ax.text(0,-1.95,'轨道以同心圆近似，比例仅为示意',fontsize=9,color='#555')
fig.tight_layout();fig.savefig(Path(__file__).parent/'track_curvature.pdf',bbox_inches='tight');plt.close(fig)
