import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Arc, Polygon
from matplotlib import font_manager
from pathlib import Path

out = Path(__file__).resolve().parent
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':10,'mathtext.fontset':'stix','pdf.fonttype':42})
def arrow(ax,a,b,color='black', lw=1.5):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color=color,lw=lw))

fig,ax=plt.subplots(figsize=(7,3.7)); ax.set_xlim(-3.3,3.3); ax.set_ylim(-.8,3.25); ax.axis('off'); ax.set_aspect('equal')
ax.plot([-3,3],[0,0],color='#333333',lw=3)
for x in [i*.4-2.8 for i in range(15)]: ax.plot([x-.09,x+.09],[-.21,0],color='#555',lw=.8)
ax.plot([0,0],[0,2.9],ls='--',color='#666',lw=1)
arrow(ax,(-2.05,2.45),(0,0),'#c98700',2); arrow(ax,(0,0),(2.55,2.15),'#b33437',2)
ax.add_patch(Arc((0,0),1.4,1.4,theta1=90,theta2=130,color='#444'))
ax.add_patch(Arc((0,0),1.9,1.9,theta1=40,theta2=90,color='#444'))
ax.text(-.55,.9,r'$\alpha$',fontsize=14); ax.text(.55,1.05,r'$\beta$',fontsize=14)
ax.text(-2.8,2.55,'入射光'); ax.text(1.9,2.3,'衍射光'); ax.text(.08,2.78,'法线'); ax.text(1.45,-.57,'光栅表面'); ax.text(-1.05,-.58,'周期 $d$')
fig.tight_layout(); fig.savefig(out/'grating_geometry.pdf',bbox_inches='tight'); plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(10,3.6),gridspec_kw={'width_ratios':[1.1,1]})
for a in axs: a.set_xlim(0,10); a.set_ylim(0,5); a.axis('off')
a=axs[0]
a.text(5,4.65,'(a) 可调谐 F–P 干涉单元',ha='center',weight='bold')
for x in [3,7]: a.add_patch(Arc((x,2.5),.45,2.9,theta1=85,theta2=275,lw=1.5)); a.add_patch(Arc((x,2.5),.45,2.9,theta1=-95,theta2=95,lw=1.5))
for x in [4.55,5.3]: a.add_patch(Rectangle((x,1.6),.15,1.8,facecolor='#777',edgecolor='black'))
a.add_patch(Polygon([(0.9,2.5),(3,3.15),(3,1.85)],facecolor='#f7cfbb',alpha=.6)); a.add_patch(Rectangle((3,1.85),4,1.3,facecolor='#f7cfbb',alpha=.5)); a.add_patch(Polygon([(7,1.85),(7,3.15),(9.2,2.5)],facecolor='#c1dfcf',alpha=.8))
arrow(a,(.9,2.5),(9.2,2.5)); a.annotate('',xy=(5.3,3.7),xytext=(4.7,3.7),arrowprops={'arrowstyle':'<->'}); a.text(5,3.95,'腔长 $h$',ha='center')
for x,t in [(1,'入射小孔'),(3,'准直镜'),(4.95,'F–P 腔'),(7,'聚焦镜'),(9,'出射小孔')]: a.text(x,.85,t,ha='center',fontsize=9)
b=axs[1]; b.text(5,4.65,'(b) 微型曲面光栅光谱仪',ha='center',weight='bold')
b.add_patch(Rectangle((1,3.45),3.1,.25,facecolor='#888')); b.add_patch(Rectangle((5.25,3.45),3.5,.25,facecolor='#aaa'))
b.text(2.5,3.95,'线阵探测器',ha='center'); b.text(5,3.95,'入射狭缝',ha='center',fontsize=9)
b.add_patch(Arc((5,2),5.4,1.3,theta1=190,theta2=350,lw=3)); b.text(5,.75,'反射式曲面光栅',ha='center')
arrow(b,(5,3.5),(5,1.37),'#aa8012',1.5)
for x,c in [(1.7,'#c43c36'),(2.5,'#279461'),(3.4,'#3157ad')]: arrow(b,(5,1.37),(x,3.45),c,1.5)
fig.tight_layout(); fig.savefig(out/'zhong_fp_grating.pdf',bbox_inches='tight'); plt.close(fig)
