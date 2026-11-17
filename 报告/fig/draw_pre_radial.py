from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent
x=np.genfromtxt(p/'pre_radial.csv',delimiter=',',names=True)
plt.rcParams.update({'font.family':'Times New Roman','font.weight':'bold','axes.labelweight':'bold','font.size':11,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(6.2,3.6))
for key,col in [('R','#c43c39'),('G','#268856'),('B','#315aa2')]:ax.plot(x['rho_px'],x[key],color=col,lw=1.5,label=key)
ax.set_xlabel('Radius (pixel)');ax.set_ylabel('Mean channel value (a.u.)');ax.grid(alpha=.2);ax.legend(frameon=False,ncol=3);fig.tight_layout();fig.savefig(p/'pre_radial.pdf');plt.close(fig)
