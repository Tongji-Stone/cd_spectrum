"""
Beautified neon spectrum figure (does not overwrite neon_spectrum.png):
  - top: photo flipped horizontally, x-axis aligned to wavelength
  - bottom: I(λ) with visible-spectrum color fill under the curve
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "氖泡_裁剪.jpg"
OUT = Path(__file__).resolve().parent
META = OUT / "meta.json"
CSV = OUT / "spectrum_I_lambda.csv"
LINES = OUT / "identified_lines.csv"


def wavelength_to_rgb(lam: np.ndarray) -> np.ndarray:
    """Approximate visible spectrum colors (nm) -> RGB in [0,1]. Based on Dan Bruton."""
    lam = np.asarray(lam, dtype=float)
    r = np.zeros_like(lam)
    g = np.zeros_like(lam)
    b = np.zeros_like(lam)

    # piecewise
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

    # intensity falloff at edges
    factor = np.ones_like(lam)
    m = (lam >= 380) & (lam < 420)
    factor[m] = 0.3 + 0.7 * (lam[m] - 380) / (420 - 380)
    m = (lam >= 700) & (lam <= 780)
    factor[m] = 0.3 + 0.7 * (780 - lam[m]) / (780 - 700)
    factor[(lam < 380) | (lam > 780)] = 0.0

    rgb = np.stack([r, g, b], axis=-1) * factor[..., None]
    # gamma
    rgb = np.clip(rgb, 0, 1) ** 0.8
    return rgb


def fill_spectrum_color(ax, lam, I, n_seg=400):
    """Fill under curve with wavelength-colored vertical strips."""
    lam = np.asarray(lam, float)
    I = np.asarray(I, float)
    # resample for smooth color bands
    lam_u = np.linspace(lam.min(), lam.max(), n_seg)
    I_u = np.interp(lam_u, lam, I)
    rgb = wavelength_to_rgb(lam_u)
    for i in range(len(lam_u) - 1):
        ax.fill_between(
            [lam_u[i], lam_u[i + 1]],
            [0, 0],
            [I_u[i], I_u[i + 1]],
            color=rgb[i],
            linewidth=0,
            alpha=0.95,
        )
    ax.plot(lam, I, color="0.15", lw=1.15, solid_capstyle="round")


def main():
    meta = json.loads(META.read_text(encoding="utf-8"))
    a = float(meta["calibration"]["a"])
    b = float(meta["calibration"]["b_nm_per_px"])
    y_row = int(meta["dispersion_row_y"])
    rms = float(meta["calibration"]["rms_residual_nm"])

    spec = np.genfromtxt(CSV, delimiter=",", names=True)
    lam = np.asarray(spec["lambda_nm"], float)
    I = np.asarray(spec["I"], float)
    order = np.argsort(lam)
    lam, I = lam[order], I[order]
    Is = uniform_filter1d(I, 3)

    lines = np.genfromtxt(LINES, delimiter=",", names=True, dtype=None, encoding="utf-8")
    line_nm = np.asarray(lines["lambda_ref_nm"], float)

    rgb = np.asarray(Image.open(IMG).convert("RGB"))
    h, w, _ = rgb.shape
    # flip horizontally so short λ (green) is on the left, matching λ axis
    rgb_flip = np.fliplr(rgb)

    # wavelength at original x: λ = a + b*x
    # after flip, column j corresponds to original x = (w-1) - j
    # left edge j=0 -> λ_left = a + b*(w-1)
    # right edge j=w-1 -> λ_right = a
    lam_left = a + b * (w - 1)
    lam_right = a + b * 0.0

    xlim = (530.0, 710.0)
    # crop strip vertically around spectrum
    half = 90
    y0, y1 = max(0, y_row - half), min(h, y_row + half + 1)
    strip = rgb_flip[y0:y1]

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.figure(figsize=(11.5, 7.2), dpi=160, facecolor="white")
    gs = GridSpec(2, 1, height_ratios=[1.0, 1.25], hspace=0.08, figure=fig)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)

    # --- top: flipped photo in wavelength coordinates ---
    ax0.imshow(
        strip,
        aspect="auto",
        extent=[lam_left, lam_right, half, -half],
        interpolation="bilinear",
    )
    ax0.set_xlim(*xlim)
    ax0.set_ylim(half, -half)
    ax0.set_ylabel("空间 (相对)")
    ax0.set_title("氖泡衍射光谱", fontsize=13, pad=8)
    ax0.tick_params(labelbottom=False)
    for nm in line_nm:
        if xlim[0] <= nm <= xlim[1]:
            ax0.axvline(nm, color="white", alpha=0.22, lw=0.7)
    # subtle top/bottom dark vignette bars already from image

    # --- bottom: colored spectrum ---
    m = (lam >= xlim[0]) & (lam <= xlim[1])
    fill_spectrum_color(ax1, lam[m], Is[m], n_seg=500)
    ymax = float(np.percentile(Is[m], 99.5)) * 1.08
    ax1.set_ylim(0, ymax)
    ax1.set_xlim(*xlim)
    for nm in line_nm:
        if xlim[0] <= nm <= xlim[1]:
            ax1.axvline(nm, color="0.2", alpha=0.18, lw=0.7)
    ax1.set_xlabel("波长 λ (nm)", fontsize=12)
    ax1.set_ylabel("相对光强 I", fontsize=12)
    ax1.set_title(f"Ne I 光谱  标定 RMS = {rms:.2f} nm", fontsize=12, pad=6)
    ax1.grid(True, axis="y", alpha=0.25)
    ax1.grid(True, axis="x", alpha=0.15)

    # shared neat spines
    for ax in (ax0, ax1):
        for spine in ax.spines.values():
            spine.set_color("0.55")
            spine.set_linewidth(0.8)

    out_png = OUT / "neon_spectrum_aligned_color.png"
    fig.savefig(out_png, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print("wrote", out_png)
    print(f"photo λ extent after flip: [{lam_left:.1f}, {lam_right:.1f}] nm")


if __name__ == "__main__":
    main()
