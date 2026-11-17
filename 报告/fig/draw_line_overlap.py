import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
plt.rcParams.update({'font.family':'Times New Roman','font.weight':'bold','axes.labelweight':'bold','font.size':11,'pdf.fonttype':42})
x=np.linspace(-2.5,2.5,1000);fig,axs=plt.subplots(1,2,figsize=(7.2,2.8),sharex=True,sharey=True)
for ax,sigma,title in zip(axs,[.30,.58],['(a) Narrow line profile','(b) Broad line profile']):
 a=np.exp(-.5*((x+.5)/sigma)**2);b=np.exp(-.5*((x-.5)/sigma)**2)
 ax.plot(x,a,'--',color='#4e79a7',lw=1.2);ax.plot(x,b,'--',color='#e07a3f',lw=1.2);ax.plot(x,a+b,color='#303030',lw=1.8)
 ax.set_title(title,fontweight='bold',fontsize=10);ax.set_xlabel('Relative wavelength');ax.grid(alpha=.18)
axs[0].set_ylabel('Relative intensity');fig.tight_layout();fig.savefig(Path(__file__).parent/'line_overlap.pdf');plt.close(fig)
