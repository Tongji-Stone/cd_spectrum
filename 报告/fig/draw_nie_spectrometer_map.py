from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image

folder = Path(__file__).resolve().parent
font = FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc')
items = [('衍射型', 'nie_fig3.png'), ('干涉型', 'nie_fig4.png'),
         ('散射型', 'nie_fig5.png'), ('荧光型', 'nie_fig6.png'),
         ('滤光片型', 'nie_fig7.png'), ('棱镜色散型', 'nie_fig8.png')]
fig = plt.figure(figsize=(12, 6.6), facecolor='white')
columns = [0.025, 0.35, 0.675]
rows = [0.56, 0.08]
width, height = 0.30, 0.35
for i, (title, filename) in enumerate(items):
    x, y = columns[i % 3], rows[i // 3]
    fig.text(x + width / 2, y + height + 0.028, title,
             ha='center', va='center', fontproperties=font, fontsize=15, color='black')
    ax = fig.add_axes([x, y, width, height])
    with Image.open(folder / filename) as im:
        ax.imshow(im)
    ax.axis('off')
fig.savefig(folder / 'nie_spectrometer_map.pdf', facecolor='white', dpi=250)
fig.savefig(folder / 'nie_spectrometer_map_preview.png', facecolor='white', dpi=180)
plt.close(fig)
