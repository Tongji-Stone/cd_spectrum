# 氖泡衍射光谱

数据来源：`../氖泡_裁剪.jpg`

## 标定

- 模型：\(\lambda = a + b\,x\)
- 主锚点：黄线 **585.249 nm**、绿线 **540.056 nm**
- 多线最小二乘精修后：已识别 **18** 条 Ne I 线，残差 **RMS ≈ 0.36 nm**

## 输出

| 文件 | 说明 |
|---|---|
| `neon_spectrum_I_vs_lambda.png` | \(I(\lambda)\) 光谱图 |
| `neon_spectrum.png` | 照片条带 + 光谱 |
| `spectrum_I_lambda.csv` | 光谱数据 |
| `identified_lines.csv` | 已识别峰与 FWHM |
| `meta.json` | 标定参数 |
| `analyze_neon_spectrum.py` | 分析脚本 |

```powershell
python analyze_neon_spectrum.py
```

## 分辨率（可用）

氖线本身很窄，谱线 FWHM 可近似作仪器 \(\Delta\lambda\)（亮线若过曝/重叠会偏大）。  
较干净的例子：绿线 540.06 nm，FWHM ≈ 1.2 nm → \(R\approx 440\)。
