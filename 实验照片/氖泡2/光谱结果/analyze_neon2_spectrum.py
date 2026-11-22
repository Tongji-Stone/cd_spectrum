"""
Neon bulb #2 spectrum from 氖泡2照片.jpg — same pipeline as 氖泡:
calibrate with Ne I lines, pretty aligned color figure, accuracy/resolution eval.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "氖泡2照片.jpg"
OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)

NE_LINES_NM = np.array(
    [
        540.056,
        585.249,
        588.189,
        594.483,
        597.553,
        603.000,
        607.434,
        609.616,
        614.306,
        616.359,
        621.728,
        626.649,
        633.443,
        638.299,
        640.225,
        650.653,
        659.895,
        667.828,
        671.704,
        692.947,
        703.241,
    ],
    dtype=float,
)


def find_spectrum_row(rgb: np.ndarray) -> int:
    """Avoid watermark; pick row with strongest chroma in mid-right region."""
    h = rgb.shape[0]
    y_max = int(h * 0.85)
    chroma = rgb[:y_max].max(2) - rgb[:y_max].min(2)
    x0, x1 = int(rgb.shape[1] * 0.40), int(rgb.shape[1] * 0.95)
    row_score = chroma[:, x0:x1].sum(1)
    return int(np.argmax(row_score))


def extract_profile(rgb: np.ndarray, y0: int, half: int = 40):
    y_a, y_b = max(0, y0 - half), min(rgb.shape[0], y0 + half + 1)
    band = rgb[y_a:y_b].mean(0)
    lin = (band / 255.0) ** 2.2
    I = lin.sum(1)
    return band, I, lin


def find_peaks(I: np.ndarray, win: int = 10, min_prom: float = 0.08):
    Is = uniform_filter1d(I.astype(float), 5)
    peaks = []
    w = len(Is)
    for i in range(win, w - win):
        if Is[i] != Is[i - win : i + win + 1].max():
            continue
        if Is[i] < 0.05:
            continue
        base = float(np.percentile(Is[max(0, i - 55) : i + 56], 15))
        prom = float(Is[i] - base)
        if prom >= min_prom:
            peaks.append({"x": float(i), "I": float(Is[i]), "prom": prom})
    return peaks, Is


def classify_color(rgb_u8: np.ndarray) -> str:
    r, g, b = [float(v) for v in rgb_u8]
    if g > r + 10 and g > b + 10:
        return "green"
    if r > 200 and g > 150 and (r + g) / 2 - b > 70:
        return "yellow"
    if r > g + 20:
        return "red"
    if r > 170 and g > 70:
        return "orange"
    return "other"


def initial_calibration(peaks, band):
    green = None
    yellows = []
    for p in peaks:
        x = int(round(p["x"]))
        tag = classify_color(band[x])
        p["color"] = tag
        if tag == "green":
            if green is None or p["prom"] > green["prom"]:
                green = p
        if tag == "yellow":
            yellows.append(p)
    if green is None or not yellows:
        raise RuntimeError("failed to find green/yellow anchors")
    yellow = max(yellows, key=lambda p: p["I"])
    xg, xy = green["x"], yellow["x"]
    lg, ly = 540.056, 585.249
    b = (lg - ly) / (xg - xy)
    a = ly - b * xy
    return {"a": a, "b": b, "green": green, "yellow": yellow}


def match_lines(peaks, a, b, max_err_nm=3.5, lam_lo=530, lam_hi=715):
    used = set()
    matches = []
    for p in sorted(peaks, key=lambda q: -q["prom"]):
        lam_pred = a + b * p["x"]
        if lam_pred < lam_lo or lam_pred > lam_hi:
            continue
        # skip near-zero-order white/purple (very high I and not red/yellow/green)
        if p.get("color") == "other" and p["I"] > 1.5:
            continue
        errs = np.abs(NE_LINES_NM - lam_pred)
        order = np.argsort(errs)
        chosen = None
        for j in order:
            if errs[j] > max_err_nm:
                break
            if j in used:
                continue
            chosen = j
            break
        if chosen is None:
            continue
        used.add(chosen)
        matches.append(
            {
                "x_px": p["x"],
                "I": p["I"],
                "prom": p["prom"],
                "color": p.get("color", ""),
                "lambda_pred_nm": float(lam_pred),
                "lambda_ref_nm": float(NE_LINES_NM[chosen]),
                "residual_nm": float(lam_pred - NE_LINES_NM[chosen]),
            }
        )
    matches.sort(key=lambda m: m["lambda_ref_nm"])
    return matches


def refine_calibration(matches):
    xs = np.array([m["x_px"] for m in matches], float)
    ys = np.array([m["lambda_ref_nm"] for m in matches], float)
    A = np.column_stack([np.ones_like(xs), xs])
    coef, _, _, _ = np.linalg.lstsq(A, ys, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    resid = (a + b * xs) - ys
    return a, b, resid


def fwhm_nm(x, I, peak_x, k_nm_per_px):
    i = int(round(peak_x))
    half = I[i] / 2.0
    L = i
    while L > 0 and I[L] > half:
        L -= 1
    R = i
    while R < len(I) - 1 and I[R] > half:
        R += 1

    def cross(i1, i2):
        y1, y2 = I[i1], I[i2]
        if y2 == y1:
            return float(i2)
        return float(i1 + (half - y1) / (y2 - y1) * (i2 - i1))

    xL = cross(L, L + 1) if L < i else float(L)
    xR = cross(R - 1, R) if R > i else float(R)
    return abs(xR - xL) * abs(k_nm_per_px)


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
    factor[m] = 0.3 + 0.7 * (lam[m] - 380) / (420 - 380)
    m = (lam >= 700) & (lam <= 780)
    factor[m] = 0.3 + 0.7 * (780 - lam[m]) / (780 - 700)
    factor[(lam < 380) | (lam > 780)] = 0.0
    rgb = np.stack([r, g, b], axis=-1) * factor[..., None]
    return np.clip(rgb, 0, 1) ** 0.8


def fill_spectrum_color(ax, lam, I, n_seg=500):
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
            alpha=0.95,
        )
    ax.plot(lam, I, color="0.15", lw=1.15)


def main():
    print("loading", IMG.name)
    rgb = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
    y_row = find_spectrum_row(rgb)
    band, I, lin = extract_profile(rgb, y_row)
    peaks, Is = find_peaks(I)
    for p in peaks:
        p["color"] = classify_color(band[int(round(p["x"]))])
    print(f"row y≈{y_row}, peaks={len(peaks)}")

    init = initial_calibration(peaks, band)
    a0, b0 = init["a"], init["b"]
    print(
        f"anchors: yellow x={init['yellow']['x']:.0f}→585.25, "
        f"green x={init['green']['x']:.0f}→540.06; b={b0:.5f} nm/px"
    )

    matches = match_lines(peaks, a0, b0, max_err_nm=4.0)
    print(f"initial matches: {len(matches)}")
    if len(matches) < 4:
        raise RuntimeError("too few matched lines")
    a, b, resid = refine_calibration(matches)
    matches = match_lines(peaks, a, b, max_err_nm=2.8)
    a, b, resid = refine_calibration(matches)
    rms = float(np.sqrt(np.mean(resid**2)))
    print(f"refined: λ = {a:.4f} + {b:.6f}·x ; N={len(matches)} rms={rms:.3f} nm")

    x = np.arange(len(I), dtype=float)
    lam = a + b * x
    m = (lam >= 520) & (lam <= 720) & np.isfinite(I)
    order = np.argsort(lam[m])
    lam_s = lam[m][order]
    I_s = I[m][order]
    R_s, G_s, B_s = lin[m, 0][order], lin[m, 1][order], lin[m, 2][order]

    for mtc in matches:
        mtc["FWHM_nm"] = fwhm_nm(x, Is, mtc["x_px"], b)
        mtc["lambda_fit_nm"] = a + b * mtc["x_px"]
        mtc["residual_nm"] = mtc["lambda_fit_nm"] - mtc["lambda_ref_nm"]

    np.savetxt(
        OUT / "spectrum_I_lambda.csv",
        np.column_stack([lam_s, I_s, R_s, G_s, B_s]),
        delimiter=",",
        header="lambda_nm,I,R_lin,G_lin,B_lin",
        comments="",
    )
    peak_rows = ["x_px,lambda_fit_nm,lambda_ref_nm,residual_nm,I,prom,FWHM_nm,color"]
    for m_ in matches:
        peak_rows.append(
            f"{m_['x_px']:.2f},{m_['lambda_fit_nm']:.3f},{m_['lambda_ref_nm']:.3f},"
            f"{m_['residual_nm']:.3f},{m_['I']:.4f},{m_['prom']:.4f},"
            f"{m_['FWHM_nm']:.3f},{m_['color']}"
        )
    (OUT / "identified_lines.csv").write_text("\n".join(peak_rows) + "\n", encoding="utf-8")

    clean = [m_ for m_ in matches if m_["FWHM_nm"] < 5.0]
    res_lines = sorted(clean, key=lambda q: q["FWHM_nm"])[:6]
    meta = {
        "image": IMG.name,
        "dispersion_row_y": y_row,
        "calibration": {
            "model": "lambda_nm = a + b * x_px",
            "a": a,
            "b_nm_per_px": b,
            "n_matched_lines": len(matches),
            "rms_residual_nm": rms,
            "primary_anchors": {
                "yellow_585.249": init["yellow"]["x"],
                "green_540.056": init["green"]["x"],
            },
        },
        "matched_lines_nm": [m_["lambda_ref_nm"] for m_ in matches],
        "FWHM_examples_nm": [
            {
                "lambda_ref_nm": m_["lambda_ref_nm"],
                "FWHM_nm": m_["FWHM_nm"],
                "R": m_["lambda_ref_nm"] / m_["FWHM_nm"],
            }
            for m_ in res_lines
        ],
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # --- classic dual panel (like neon_spectrum.png) ---
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), dpi=150, gridspec_kw={"height_ratios": [1.0, 1.15]})
    half = 100
    y0, y1 = max(0, y_row - half), min(rgb.shape[0], y_row + half + 1)
    strip = rgb[y0:y1].astype(np.uint8)
    axes[0].imshow(strip, aspect="auto", extent=[0, rgb.shape[1], half, -half])
    for m_ in matches:
        axes[0].axvline(m_["x_px"], color="w", alpha=0.35, lw=0.6)
    axes[0].set_title("氖泡2衍射谱线与已识别峰")
    axes[0].set_xlabel("x (px)")
    axes[0].set_ylabel("相对行")

    Is_plot = uniform_filter1d(I_s, 3)
    ymax = float(np.percentile(I_s, 99.5)) * 1.12
    axes[1].plot(lam_s, I_s, color="0.75", lw=0.7, label="原始")
    axes[1].plot(lam_s, Is_plot, "k-", lw=1.35, label="平滑")
    axes[1].set_ylim(0, ymax)
    for m_ in matches:
        axes[1].axvline(m_["lambda_ref_nm"], color="#d62728", alpha=0.25, lw=0.8)
        axes[1].plot(m_["lambda_ref_nm"], m_["I"], "o", color="#d62728", ms=3.5)
        axes[1].text(
            m_["lambda_ref_nm"],
            ymax * 0.97,
            f"{m_['lambda_ref_nm']:.1f}",
            rotation=90,
            fontsize=7,
            va="top",
            ha="center",
            color="#444",
        )
    axes[1].set_xlim(530, 710)
    axes[1].set_xlabel("波长 λ (nm)")
    axes[1].set_ylabel("相对光强 I")
    axes[1].set_title(f"氖原子光谱  λ = {a:.2f} + ({b:.4f})·x    标定残差 RMS = {rms:.2f} nm")
    axes[1].legend(loc="upper right", fontsize=9)
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "neon_spectrum.png", dpi=200)
    plt.close()

    # --- beautified: flip only if needed so short λ is on the left ---
    h, w, _ = rgb.shape
    # original: λ = a + b*x
    # want left=short λ for display. If b>0 already short→left after... wait:
    # b>0: small x = short λ. Photo already has green on left. No flip.
    # b<0: need flip.
    if b < 0:
        rgb_show = np.fliplr(rgb.astype(np.uint8))
        lam_left = a + b * (w - 1)
        lam_right = a
    else:
        rgb_show = rgb.astype(np.uint8)
        lam_left = a
        lam_right = a + b * (w - 1)

    strip2 = rgb_show[y0:y1]
    xlim = (530.0, 710.0)
    fig = plt.figure(figsize=(11.5, 7.2), dpi=160, facecolor="white")
    gs = GridSpec(2, 1, height_ratios=[1.0, 1.25], hspace=0.08, figure=fig)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax0.imshow(strip2, aspect="auto", extent=[lam_left, lam_right, half, -half], interpolation="bilinear")
    ax0.set_xlim(*xlim)
    ax0.set_ylim(half, -half)
    ax0.set_ylabel("空间 (相对)")
    ax0.set_title("氖泡衍射光谱", fontsize=13, pad=8)
    ax0.tick_params(labelbottom=False)
    for nm in [m_["lambda_ref_nm"] for m_ in matches]:
        if xlim[0] <= nm <= xlim[1]:
            ax0.axvline(nm, color="white", alpha=0.22, lw=0.7)

    mm = (lam_s >= xlim[0]) & (lam_s <= xlim[1])
    fill_spectrum_color(ax1, lam_s[mm], Is_plot[mm])
    ax1.set_ylim(0, float(np.percentile(Is_plot[mm], 99.5)) * 1.08)
    ax1.set_xlim(*xlim)
    for nm in [m_["lambda_ref_nm"] for m_ in matches]:
        if xlim[0] <= nm <= xlim[1]:
            ax1.axvline(nm, color="0.2", alpha=0.18, lw=0.7)
    ax1.set_xlabel("波长 λ (nm)", fontsize=12)
    ax1.set_ylabel("相对光强 I", fontsize=12)
    ax1.set_title(f"Ne I 光谱  标定 RMS = {rms:.2f} nm", fontsize=12, pad=6)
    ax1.grid(True, axis="y", alpha=0.25)
    ax1.grid(True, axis="x", alpha=0.15)
    fig.savefig(OUT / "neon_spectrum_aligned_color.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()

    # --- evaluation ---
    res = np.array([m_["residual_nm"] for m_ in matches])
    fwhm = np.array([m_["FWHM_nm"] for m_ in matches])
    lam_ref = np.array([m_["lambda_ref_nm"] for m_ in matches])
    R = lam_ref / fwhm
    clean_m = fwhm < 5.0
    eval_meta = {
        "wavelength_accuracy": {
            "n_lines": int(len(res)),
            "rms_residual_nm": float(np.sqrt(np.mean(res**2))),
            "mean_residual_nm": float(res.mean()),
            "median_abs_residual_nm": float(np.median(np.abs(res))),
            "max_abs_residual_nm": float(np.max(np.abs(res))),
            "frac_within_0p5_nm": float((np.abs(res) < 0.5).mean()),
            "frac_within_1_nm": float((np.abs(res) < 1.0).mean()),
        },
        "resolution": {
            "best_FWHM_nm": float(fwhm.min()),
            "best_R": float(R.max()),
            "best_line_nm": float(lam_ref[np.argmax(R)]),
            "median_FWHM_clean_nm": float(np.median(fwhm[clean_m])) if clean_m.any() else None,
            "median_R_clean": float(np.median(R[clean_m])) if clean_m.any() else None,
            "n_clean_lines": int(clean_m.sum()),
        },
        "compare_to_neon1": {
            "neon1_rms_nm": 0.356,
            "neon1_best_FWHM_nm": 1.24,
            "neon1_best_R": 437,
        },
    }
    (OUT / "evaluation.json").write_text(json.dumps(eval_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    fig, axes = plt.subplots(2, 1, figsize=(9.5, 7.2), dpi=150)
    ax = axes[0]
    ax.axhline(0, color="0.5", lw=0.8)
    ax.axhline(0.5, color="orange", ls=":", lw=1, label="±0.5 nm")
    ax.axhline(-0.5, color="orange", ls=":", lw=1)
    ax.plot(lam_ref, res, "o-", color="#1f77b4", ms=5)
    ax.set_xlabel("标准波长 λ_ref (nm)")
    ax.set_ylabel("残差 λ_fit − λ_ref (nm)")
    ax.set_title(f"波长准确度：残差  RMS={np.sqrt(np.mean(res**2)):.2f} nm")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    cols = np.where(clean_m, "#2ca02c", "#d62728")
    ax.scatter(lam_ref, fwhm, c=cols, s=40, zorder=3)
    ax.scatter([], [], c="#2ca02c", s=40, label="较干净 (FWHM<5)")
    ax.scatter([], [], c="#d62728", s=40, label="过曝/重叠偏宽")
    ax.set_xlabel("λ (nm)")
    ax.set_ylabel("FWHM (nm)")
    ax.set_title("分辨率：谱线半高宽")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, max(14.0, float(fwhm.max()) * 1.05))
    fig.tight_layout()
    fig.savefig(OUT / "evaluation_accuracy_resolution.png", dpi=200)
    plt.close()

    rms_v = float(np.sqrt(np.mean(res**2)))
    md = f"""# 氖泡2 光谱结果评估

## 总评

识别 **{len(matches)}** 条 Ne I 线；波长标定 RMS = **{rms_v:.2f} nm**；最佳 FWHM ≈ **{fwhm.min():.2f} nm**（R≈{R.max():.0f}）。

## 与氖泡1对比

| 指标 | 氖泡1 | 氖泡2 |
|---|---|---|
| 匹配线数 | 18 | {len(matches)} |
| 波长 RMS | 0.36 nm | {rms_v:.2f} nm |
| 最佳 FWHM | 1.24 nm | {fwhm.min():.2f} nm |
| 最佳 R | ≈437 | ≈{R.max():.0f} |
| 干净线中位 FWHM | ≈2.7 nm | {float(np.median(fwhm[clean_m])) if clean_m.any() else float('nan'):.2f} nm |

## 波长准确度

- 中位\\|残差\\| = {np.median(np.abs(res)):.3f} nm
- 最大\\|残差\\| = {np.max(np.abs(res)):.3f} nm @ {lam_ref[np.argmax(np.abs(res))]:.1f} nm
- \\|残差\\|<0.5 nm：{(np.abs(res)<0.5).sum()}/{len(res)}

## 分辨率

- 较干净线（FWHM<5）中位 Δλ ≈ {float(np.median(fwhm[clean_m])) if clean_m.any() else float('nan'):.2f} nm，中位 R ≈ {float(np.median(R[clean_m])) if clean_m.any() else float('nan'):.0f}
- 过曝/重叠线的 FWHM 偏大，不用于报分辨率
"""
    (OUT / "evaluation.md").write_text(md, encoding="utf-8")

    print("wrote", OUT / "neon_spectrum_aligned_color.png")
    print("matched lines:")
    for m_ in matches:
        print(
            f"  {m_['lambda_ref_nm']:8.3f}  resid={m_['residual_nm']:+.2f}  "
            f"FWHM≈{m_['FWHM_nm']:.2f} nm  R≈{m_['lambda_ref_nm']/m_['FWHM_nm']:.0f}"
        )
    print(
        f"EVAL rms={rms_v:.3f} bestFWHM={fwhm.min():.2f} bestR={R.max():.0f} "
        f"cleanMedFWHM={float(np.median(fwhm[clean_m])) if clean_m.any() else float('nan'):.2f}"
    )


if __name__ == "__main__":
    main()
