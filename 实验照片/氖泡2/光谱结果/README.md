# 氖泡2 光谱结果

数据：`../氖泡2照片.jpg`

## 输出

| 文件 | 说明 |
|---|---|
| `neon_spectrum.png` | 照片条带 + 光谱（原格式） |
| `neon_spectrum_aligned_color.png` | 波长对齐 + 彩色填充 |
| `spectrum_I_lambda.csv` | 光谱数据 |
| `identified_lines.csv` | 已识别峰与 FWHM |
| `meta.json` | 标定参数 |
| `evaluation.md` / `evaluation.json` | 准确度与分辨率评估 |
| `evaluation_accuracy_resolution.png` | 评估图 |

```powershell
python analyze_neon2_spectrum.py
```
