# COMSOL 环状光谱仿真

透射式环状光谱光路（光源与屏分居光盘两侧，屏中心开孔），用射线光学建整盘→屏。

## 依赖

- COMSOL Multiphysics ≥ 6.4
- 许可证：Ray Optics（必需）、Wave Optics（单元效率，可选）
- 批处理：`comsolcompile.exe` / `comsolbatch.exe`（`bin\win64\`）

## 主文件

| 文件 | 作用 |
|---|---|
| `ray_ring_3d.java` | **3D 环状光谱主模型**（多波长、径向周期光栅、屏距 `L` 可调） |
| `ray_ring_2d.java` | 2D 截面验证（过盘心切片） |
| `wave_grating_cell.java` | 波动光学单周期单元（算衍射效率，尚未耦合进射线段） |
| `analyze_ring.py` | 落点半径 ρ(λ) 与理论 L·tanβ 对照 |
| `plot_ring_3d.java` | 导出轨迹 PNG |
| `ring_3d.png` | 已验证的轨迹图（DVD，L=100 mm） |

默认盘型：DVD，`d = 0.74 µm`；波长 400–700 nm；屏距 `L = 100 mm`。

## 批处理示例（Windows）

```powershell
$cc = "D:\COMSOL64\Multiphysics\bin\win64\comsolcompile.exe"
$cb = "D:\COMSOL64\Multiphysics\bin\win64\comsolbatch.exe"
Set-Location 模拟\comsol
& $cc ray_ring_3d.java
& $cb -inputfile ray_ring_3d.class -outputfile ray_ring_3d.mph
```

求解后产物为 `ray_ring_3d_Model.mph`（含解，体积大，不入库）。

## 验证结果（DVD，L=100 mm）

环半径 ρ = L·tanβ，sinβ = λ/d；406–694 nm 与理论误差约 0.6%–1.6%。
紫色在内、红色在外。
