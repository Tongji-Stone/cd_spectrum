"""
Neon bulb line spectrum from 氖泡_裁剪.jpg.

Calibration: match measured peaks to known Ne I emission lines
(green 540.06 nm + yellow 585.25 nm as primary anchors, then refine).
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
OUT.mkdir(exist_ok=True)

# Strong visible Ne I lines (nm, air), roughly ordered by typical strength/visibility
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


def extract_profile(rgb: np.ndarray, half: int = 28):
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    y0 = int(np.argmax(lum.sum(1)))
    y0, y1 = max(0, y0 - half), min(rgb.shape[0], y0 + half + 1)
    band = rgb[y0:y1].mean(0)
    lin = (band / 255.0) ** 2.2
    I = lin.sum(1)
    return y0, band, I, lin


def find_peaks(I: np.ndarray, win: int = 8, min_prom: float = 0.08):
    Is = uniform_filter1d(I.astype(float), 3)
    peaks = []
    w = len(Is)
    for i in range(win, w - win):
        if Is[i] != Is[i - win : i + win + 1].max():
            continue
        if Is[i] < 0.05:
            continue
        base = float(np.percentile(Is[max(0, i - 45) : i + 46], 20))
        prom = float(Is[i] - base)
        if prom >= min_prom:
            peaks.append({"x": float(i), "I": float(Is[i]), "prom": prom})
    return peaks, Is


def classify_color(rgb_u8: np.ndarray) -> str:
    r, g, b = [float(v) for v in rgb_u8]
    if g > r + 15 and g > b + 15:
        return "green"
    if r > 200 and g > 160 and (r + g) / 2 - b > 80:
        return "yellow"
    if r > g + 25:
        return "red"
    if r > 180 and g > 80:
        return "orange"
    return "other"


def initial_calibration(peaks, band):
    """Use isolated green + brightest yellow as anchors."""
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
    # λ = a + b x
    b = (lg - ly) / (xg - xy)
    a = ly - b * xy
    return {"a": a, "b": b, "green": green, "yellow": yellow}


def match_lines(peaks, a, b, max_err_nm=2.8):
    """Greedy match peaks to unused Ne lines within tolerance."""
    used = set()
    matches = []
    # sort by prominence so strong lines claim first
    for p in sorted(peaks, key=lambda q: -q["prom"]):
        lam_pred = a + b * p["x"]
        # only match in neon visible range
        if lam_pred < 520 or lam_pred > 720:
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
    matches.sort(key=lambda m: m["x_px"])
    return matches


def refine_calibration(matches):
    xs = np.array([m["x_px"] for m in matches], float)
    ys = np.array([m["lambda_ref_nm"] for m in matches], float)
    # linear least squares λ = a + b x
    A = np.column_stack([np.ones_like(xs), xs])
    coef, _, _, _ = np.linalg.lstsq(A, ys, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    pred = a + b * xs
    resid = pred - ys
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


def main():
    print("loading", IMG.name)
    rgb = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
    y_row, band, I, lin = extract_profile(rgb)
    peaks, Is = find_peaks(I)
    print(f"row y≈{y_row}, peaks={len(peaks)}")

    init = initial_calibration(peaks, band)
    a0, b0 = init["a"], init["b"]
    print(
        f"anchors: yellow x={init['yellow']['x']:.0f}→585.25, "
        f"green x={init['green']['x']:.0f}→540.06; b={b0:.5f} nm/px"
    )

    matches = match_lines(peaks, a0, b0, max_err_nm=3.5)
    print(f"initial matches: {len(matches)}")
    a, b, resid = refine_calibration(matches)
    # rematch with refined scale
    matches = match_lines(peaks, a, b, max_err_nm=2.5)
    a, b, resid = refine_calibration(matches)
    rms = float(np.sqrt(np.mean(resid**2)))
    print(f"refined: λ = {a:.4f} + {b:.6f}·x ; N={len(matches)} rms={rms:.3f} nm")

    x = np.arange(len(I), dtype=float)
    lam = a + b * x
    # spectrum only over useful range covering lines
    m = (lam >= 520) & (lam <= 720) & np.isfinite(I)
    # if b<0, lam decreases with x — sort for plotting
    order = np.argsort(lam[m])
    lam_s = lam[m][order]
    I_s = I[m][order]
    R_s = lin[m, 0][order]
    G_s = lin[m, 1][order]
    B_s = lin[m, 2][order]

    # FWHM for unsaturated-ish lines (prom high but I not fully clipped)
    for mtc in matches:
        mtc["FWHM_nm"] = fwhm_nm(x, Is, mtc["x_px"], b)

    # pick a few clean lines for resolution estimate (avoid saturated yellow core if clipped)
    res_candidates = [
        m_
        for m_ in matches
        if m_["lambda_ref_nm"] in (540.056, 585.249, 640.225, 650.653, 703.241)
        or (520 < m_["lambda_ref_nm"] < 710 and m_["prom"] > 0.2)
    ]
    # unique by ref
    seen = set()
    res_lines = []
    for m_ in sorted(res_candidates, key=lambda q: q["FWHM_nm"]):
        key = round(m_["lambda_ref_nm"], 3)
        if key in seen:
            continue
        seen.add(key)
        res_lines.append(m_)
        if len(res_lines) >= 6:
            break

    np.savetxt(
        OUT / "spectrum_I_lambda.csv",
        np.column_stack([lam_s, I_s, R_s, G_s, B_s]),
        delimiter=",",
        header="lambda_nm,I,R_lin,G_lin,B_lin",
        comments="",
    )
    # peaks table
    peak_rows = [
        "x_px,lambda_fit_nm,lambda_ref_nm,residual_nm,I,prom,FWHM_nm,color"
    ]
    for m_ in matches:
        peak_rows.append(
            f"{m_['x_px']:.2f},{a+b*m_['x_px']:.3f},{m_['lambda_ref_nm']:.3f},"
            f"{(a+b*m_['x_px'])-m_['lambda_ref_nm']:.3f},{m_['I']:.4f},{m_['prom']:.4f},"
            f"{m_['FWHM_nm']:.3f},{m_['color']}"
        )
    (OUT / "identified_lines.csv").write_text("\n".join(peak_rows) + "\n", encoding="utf-8")

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
        "resolution_note": (
            "Neon lines are narrow; measured FWHM is a practical estimate of instrument "
            "Δλ (still includes slight source width, focus, and saturation for bright lines)."
        ),
        "FWHM_examples_nm": [
            {
                "lambda_ref_nm": m_["lambda_ref_nm"],
                "FWHM_nm": m_["FWHM_nm"],
                "R": m_["lambda_ref_nm"] / m_["FWHM_nm"] if m_["FWHM_nm"] > 0 else None,
            }
            for m_ in res_lines
        ],
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), dpi=150, gridspec_kw={"height_ratios": [1.0, 1.15]})

    # strip preview
    ax = axes[0]
    ymid = y_row
    strip = rgb[max(0, ymid - 80) : ymid + 81].astype(np.uint8)
    ax.imshow(strip, aspect="auto", extent=[0, rgb.shape[1], 80, -80])
    for m_ in matches:
        ax.axvline(m_["x_px"], color="w", alpha=0.35, lw=0.6)
    ax.set_title("氖泡衍射谱线（裁剪图）与已识别峰")
    ax.set_xlabel("x (px)")
    ax.set_ylabel("相对行")

    ax = axes[1]
    ax.plot(lam_s, I_s, color="0.75", lw=0.7, label="原始")
    Is_plot = uniform_filter1d(I_s, 3)
    ax.plot(lam_s, Is_plot, "k-", lw=1.35, label="平滑")
    ymax = float(np.percentile(I_s, 99.5)) * 1.12
    ax.set_ylim(0, ymax)
    for m_ in matches:
        ax.axvline(m_["lambda_ref_nm"], color="#d62728", alpha=0.25, lw=0.8)
        ax.plot(m_["lambda_ref_nm"], m_["I"], "o", color="#d62728", ms=3.5)
        ax.text(
            m_["lambda_ref_nm"],
            ymax * 0.97,
            f"{m_['lambda_ref_nm']:.1f}",
            rotation=90,
            fontsize=7,
            va="top",
            ha="center",
            color="#444",
        )
    ax.set_xlim(530, 710)
    ax.set_xlabel("波长 λ (nm)")
    ax.set_ylabel("相对光强 I")
    ax.set_title(f"氖原子光谱  λ = {a:.2f} + ({b:.4f})·x    标定残差 RMS = {rms:.2f} nm")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT / "neon_spectrum.png", dpi=200)
    plt.close()

    # clean spectrum-only figure
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    ax.fill_between(lam_s, Is_plot, alpha=0.2, color="#1f77b4")
    ax.plot(lam_s, I_s, color="#9ecae1", lw=0.7)
    ax.plot(lam_s, Is_plot, color="#1f77b4", lw=1.8)
    for m_ in matches:
        ax.axvline(m_["lambda_ref_nm"], color="#c44e52", alpha=0.3, lw=0.9)
    ax.set_xlim(530, 710)
    ax.set_ylim(0, None)
    ax.set_xlabel("波长 λ (nm)", fontsize=12)
    ax.set_ylabel("相对光强 I", fontsize=12)
    ax.set_title("氖泡衍射光谱（Ne I）", fontsize=13)
    ax.grid(True, alpha=0.3)
    # annotation table-like on figure
    labels = ", ".join(f"{m_['lambda_ref_nm']:.1f}" for m_ in matches[:12])
    if len(matches) > 12:
        labels += ", ..."
    ax.text(
        0.01,
        0.98,
        f"已识别 {len(matches)} 条 Ne 线；RMS={rms:.2f} nm\n{labels}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.75, edgecolor="0.8"),
    )
    fig.tight_layout()
    fig.savefig(OUT / "neon_spectrum_I_vs_lambda.png", dpi=220)
    plt.close()

    print("wrote", OUT / "neon_spectrum_I_vs_lambda.png")
    print("matched lines:")
    for m_ in matches:
        print(
            f"  {m_['lambda_ref_nm']:8.3f} nm  x={m_['x_px']:7.1f}  "
            f"resid={a+b*m_['x_px']-m_['lambda_ref_nm']:+.2f}  FWHM≈{m_['FWHM_nm']:.2f} nm"
        )
    if res_lines:
        print("resolution examples R=λ/FWHM:")
        for m_ in res_lines[:5]:
            print(f"  {m_['lambda_ref_nm']:.1f} nm → Δλ≈{m_['FWHM_nm']:.2f} nm, R≈{m_['lambda_ref_nm']/m_['FWHM_nm']:.0f}")


if __name__ == "__main__":
    main()
