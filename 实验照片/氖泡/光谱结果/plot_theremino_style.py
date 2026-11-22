"""
Theremino Spectrometer–style spectrum figures (shared look for 氖泡 / 氖泡2).

Layout mimics Theremino UI:
  - cream window background
  - top: photo strip aligned to wavelength (flip if needed)
  - bottom: light-blue grid, λ scale on TOP, rainbow fill, yellow peak labels
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d

# Visual constants (Theremino-like)
BG_CREAM = "#F5F0E6"
PLOT_BG = "#E8EEF5"
GRID_MAJOR = "#A8B4C4"
GRID_MINOR = "#C8D2DE"
PEAK_LINE = "#E02020"
LABEL_FACE = "#FFE566"
LABEL_EDGE = "#333333"
CURVE = "#1A1A1A"


def wavelength_to_rgb(lam: np.ndarray) -> np.ndarray:
    lam = np.asarray(lam, dtype=float)
    r = np.zeros_like(lam)
    g = np.zeros_like(lam)
    b = np.zeros_like(lam)
    m = (lam >= 380) & (lam < 440)
    r[m] = -(lam[m] - 440) / (440 - 380)
    b[m] = 1.0
    m = (lam >= 440) & (lam < 490)
    g[m] = (lam[m] - 440) / (490 - 440)
    b[m] = 1.0
    m = (lam >= 490) & (lam < 510)
    g[m] = 1.0
    b[m] = -(lam[m] - 510) / (510 - 490)
    m = (lam >= 510) & (lam < 580)
    r[m] = (lam[m] - 510) / (580 - 510)
    g[m] = 1.0
    m = (lam >= 580) & (lam < 645)
    r[m] = 1.0
    g[m] = -(lam[m] - 645) / (645 - 580)
    m = (lam >= 645) & (lam <= 780)
    r[m] = 1.0
    factor = np.ones_like(lam)
    m = (lam >= 380) & (lam < 420)
    factor[m] = 0.35 + 0.65 * (lam[m] - 380) / (420 - 380)
    m = (lam >= 700) & (lam <= 780)
    factor[m] = 0.35 + 0.65 * (780 - lam[m]) / (780 - 700)
    out = (lam < 380) | (lam > 780)
    factor[out] = 0.15
    rgb = np.stack([r, g, b], axis=-1) * factor[..., None]
    # outside visible → dark gray (Theremino style)
    rgb[out] = 0.25
    return np.clip(rgb, 0, 1) ** 0.85


def fill_colored(ax, lam, I, n_seg=600):
    lam_u = np.linspace(float(lam.min()), float(lam.max()), n_seg)
    I_u = np.interp(lam_u, lam, I)
    rgb = wavelength_to_rgb(lam_u)
    for i in range(len(lam_u) - 1):
        ax.fill_between(
            [lam_u[i], lam_u[i + 1]],
            [0, 0],
            [I_u[i], I_u[i + 1]],
            color=rgb[i],
            linewidth=0,
            zorder=2,
        )
    ax.plot(lam, I, color=CURVE, lw=1.05, zorder=3)


def render(dataset_dir: Path, img_path: Path, title: str, xlim=(530.0, 710.0)):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import FancyBboxPatch

    meta = json.loads((dataset_dir / "meta.json").read_text(encoding="utf-8"))
    a = float(meta["calibration"]["a"])
    b = float(meta["calibration"]["b_nm_per_px"])
    y_row = int(meta["dispersion_row_y"])
    rms = float(meta["calibration"]["rms_residual_nm"])

    spec = np.genfromtxt(dataset_dir / "spectrum_I_lambda.csv", delimiter=",", names=True)
    lam = np.asarray(spec["lambda_nm"], float)
    I = np.asarray(spec["I"], float)
    order = np.argsort(lam)
    lam, I = lam[order], I[order]
    Is = uniform_filter1d(I, 3)

    lines = np.genfromtxt(
        dataset_dir / "identified_lines.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    line_nm = np.asarray(lines["lambda_ref_nm"], float)
    # intensity at nearest sample for label height
    line_I = []
    for nm in line_nm:
        j = int(np.argmin(np.abs(lam - nm)))
        line_I.append(float(Is[j]))
    line_I = np.asarray(line_I)

    rgb = np.asarray(Image.open(img_path).convert("RGB"))
    h, w, _ = rgb.shape
    if b < 0:
        rgb_show = np.fliplr(rgb)
        lam_left = a + b * (w - 1)
        lam_right = a
    else:
        rgb_show = rgb
        lam_left, lam_right = a, a + b * (w - 1)

    half = 95
    y0, y1 = max(0, y_row - half), min(h, y_row + half + 1)
    strip = rgb_show[y0:y1]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.figure(figsize=(12.0, 7.6), dpi=170, facecolor=BG_CREAM)
    gs = GridSpec(
        2,
        1,
        height_ratios=[0.85, 1.55],
        hspace=0.12,
        figure=fig,
        left=0.07,
        right=0.98,
        top=0.92,
        bottom=0.08,
    )
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1])

    # --- top photo strip (Theremino webcam panel) ---
    ax0.set_facecolor("black")
    ax0.imshow(
        strip,
        aspect="auto",
        extent=[lam_left, lam_right, 1, 0],
        interpolation="bilinear",
        zorder=1,
    )
    ax0.set_xlim(*xlim)
    ax0.set_ylim(1, 0)
    ax0.set_yticks([])
    ax0.tick_params(bottom=False, labelbottom=False, top=False, labeltop=False)
    for sp in ax0.spines.values():
        sp.set_color("#444")
        sp.set_linewidth(1.2)
    ax0.set_title(title, fontsize=14, color="#222", pad=10, fontweight="medium")

    # --- bottom Theremino spectrum plot ---
    ax1.set_facecolor(PLOT_BG)
    ax1.xaxis.set_ticks_position("top")
    ax1.xaxis.set_label_position("top")
    ax1.tick_params(axis="x", which="both", top=True, bottom=False, labeltop=True, labelbottom=False)
    ax1.tick_params(axis="y", labelsize=9, colors="#333")
    ax1.tick_params(axis="x", labelsize=10, colors="#222")

    # grids like Theremino
    ax1.set_xticks(np.arange(xlim[0], xlim[1] + 1e-6, 10), minor=False)
    ax1.set_xticks(np.arange(xlim[0], xlim[1] + 1e-6, 2), minor=True)
    ax1.grid(True, which="major", color=GRID_MAJOR, lw=0.9, zorder=0)
    ax1.grid(True, which="minor", color=GRID_MINOR, lw=0.45, zorder=0)

    mm = (lam >= xlim[0]) & (lam <= xlim[1])
    fill_colored(ax1, lam[mm], Is[mm])

    ymax = float(np.percentile(Is[mm], 99.7)) * 1.12
    ax1.set_ylim(0, ymax)
    ax1.set_xlim(*xlim)

    # faint green reference (Theremino)
    ax1.axhline(ymax * 0.5, color="#8A9A4A", lw=0.9, alpha=0.55, zorder=1)

    # peak markers: red line + yellow label at bottom
    for nm, iv in zip(line_nm, line_I):
        if not (xlim[0] <= nm <= xlim[1]):
            continue
        ax1.axvline(nm, color=PEAK_LINE, lw=0.85, alpha=0.85, zorder=4)
        # yellow label box near baseline
        ax1.annotate(
            f"{nm:.0f}",
            xy=(nm, 0),
            xytext=(nm, ymax * 0.02),
            ha="center",
            va="bottom",
            fontsize=7.5,
            color="#111",
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.18",
                facecolor=LABEL_FACE,
                edgecolor=LABEL_EDGE,
                linewidth=0.7,
            ),
            zorder=5,
        )

    ax1.set_xlabel("λ (nm)", fontsize=11, labelpad=6)
    ax1.set_ylabel("相对光强", fontsize=11)
    ax1.text(
        0.995,
        0.97,
        f"标定 RMS = {rms:.2f} nm   N = {len(line_nm)}",
        transform=ax1.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        color="#333",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#BBB", alpha=0.9),
        zorder=6,
    )

    for sp in ax1.spines.values():
        sp.set_color("#555")
        sp.set_linewidth(1.0)

    out = dataset_dir / "neon_spectrum_theremino_style.png"
    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor())
    plt.close()
    print("wrote", out)
    return out


def main():
    root = Path(r"C:\Users\qiann\Desktop\TJPT光栅\实验照片")
    jobs = [
        (
            root / "氖泡" / "光谱结果",
            root / "氖泡" / "氖泡_裁剪.jpg",
            "氖泡衍射光谱",
        ),
        (
            root / "氖泡2" / "光谱结果",
            root / "氖泡2" / "氖泡2照片.jpg",
            "氖泡2衍射光谱",
        ),
    ]
    # optional single-dir CLI
    if len(sys.argv) >= 3:
        jobs = [(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "氖泡光谱")]
    for d, img, title in jobs:
        if not (d / "meta.json").exists():
            print("skip missing meta", d)
            continue
        render(d, img, title)


if __name__ == "__main__":
    main()
