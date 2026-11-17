import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,Rectangle,Ellipse
from matplotlib import font_manager
from pathlib import Path
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':10,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(9,3.4));ax.set_xlim(-1,11);ax.set_ylim(-2,2.4);ax.axis('off')
def arrow(x,y,xx,yy,color,lw=1.7): ax.add_patch(FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',mutation_scale=13,lw=lw,color=color))
ax.add_patch(Rectangle((0,-.5),.12,.38,color='black'));ax.add_patch(Rectangle((0,.12),.12,.38,color='black'))
ax.add_patch(Ellipse((4,0),.42,2.15,facecolor='#dceffc',edgecolor='#315572',lw=1.5))
ax.plot([9.2,10],[-1.1,1.1],lw=3,color='#333')
ax.add_patch(Rectangle((0,1.2),.22,.5,facecolor='#444'))
arrow(.12,0,3.8,.05,'#b58100');arrow(4.2,.05,9.5,.05,'#b58100')
arrow(9.5,.05,4.2,.42,'#bd423d');arrow(3.8,.42,.22,1.44,'#bd423d')
arrow(9.5,-.13,4.2,.19,'#365fac');arrow(3.8,.19,.22,1.28,'#365fac')
for x,y,t in [(0,-.85,'狭缝'),(4,-1.4,'准直 / 成像透镜'),(9.6,-1.5,'光盘光栅'),(.1,1.9,'探测器'),(6.2,.95,'衍射光返回'),(6,-.45,'入射光')]:ax.text(x,y,t,ha='center')
ax.text(5,-1.85,'光路和谱线间隔为示意',ha='center',fontsize=9,color='#555')
fig.tight_layout();fig.savefig(Path(__file__).parent/'littrow_layout.pdf',bbox_inches='tight');plt.close(fig)
