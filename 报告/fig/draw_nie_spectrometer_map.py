from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from matplotlib.font_manager import FontProperties
from PIL import Image

folder = Path(__file__).resolve().parent
font = FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc')
fig = plt.figure(figsize=(7.4, 9.0), facecolor='white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
ax.text(.11, .5, '光谱仪\n技术方案', ha='center', va='center',
        fontproperties=font, fontsize=12, linespacing=1.6, color='black')
# A single left brace groups the six branches; it is part of the diagram.
verts = [(.245, .93), (.218, .93), (.218, .87), (.218, .80),
         (.218, .62), (.218, .55), (.19, .50),
         (.218, .45), (.218, .38), (.218, .20),
         (.218, .13), (.218, .07), (.245, .07)]
codes = [MplPath.MOVETO] + [MplPath.CURVE4] * 12
ax.add_patch(PathPatch(MplPath(verts, codes), fill=False, color='black', lw=1.15))
rows = [.67, .39, .11]
cols = [.27, .635]
width, height = .335, .235
items = [('衍射型', 'nie_fig3.png'), ('干涉型', 'nie_fig4.png'),
         ('散射型', 'nie_fig5.png'), ('荧光型', 'nie_fig6.png'),
         ('滤光片型', 'nie_fig7.png'), ('棱镜色散型', 'nie_fig8.png')]
for i, (title, filename) in enumerate(items):
    x, y = cols[i % 2], rows[i // 2]
    ax.text(x + width / 2, y + height - .012, title, ha='center', va='center',
            fontproperties=font, fontsize=11, color='black')
    image_ax = fig.add_axes([x, y, width, height - .035])
    image_ax.imshow(Image.open(folder / filename))
    image_ax.axis('off')
fig.savefig(folder / 'nie_spectrometer_map.pdf', facecolor='white', dpi=250)
