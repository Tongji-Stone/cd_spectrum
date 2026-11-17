import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
plt.rcParams.update({'font.family':'Times New Roman','font.weight':'bold','axes.labelweight':'bold','font.size':11,'pdf.fonttype':42})
lam=np.linspace(400,700,301); fig,ax=plt.subplots(figsize=(6.4,3.8))
for d,label in [(1600,'CD, d = 1600 nm'),(740,'DVD, d = 740 nm')]:
 theta=np.degrees(np.arcsin(lam/(2*d))); ax.plot(lam,theta,lw=2,label=label)
ax.set(xlabel='Wavelength (nm)',ylabel='Littrow angle (degrees)',xlim=(400,700)); ax.grid(alpha=.25); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(Path(__file__).parent/'littrow.pdf'); plt.close(fig)
