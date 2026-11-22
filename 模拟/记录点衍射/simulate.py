"""Coherent scalar diffraction of marks on a local patch of optical disc."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DISC = {"DVD": (0.74, 0.40 / 3), "CD": (1.60, 0.83 / 3)}
CASES = (
    ("continuous", "Continuous"),
    ("0101", "0101 aligned"),
    ("0100", "0100 aligned"),
    ("0101_shifted", "0101 shifted by track"),
    ("random", "Random 3T–11T"),
    ("half_aperture", "Half radial aperture"),
)


def make_mask(case, tracks, cells, seed):
    """Rows are radial track indices. Columns are tangential cells of length T."""
    rng = np.random.default_rng(seed)
    y = np.arange(cells)
    if case == "continuous":
        return np.ones((tracks, cells), dtype=bool)
    if case == "half_aperture":
        return np.broadcast_to((np.arange(tracks) < tracks // 2)[:, None], (tracks, cells))
    if case in {"0101", "0100", "0101_shifted"}:
        period = 12 if case == "0100" else 6
        shift = rng.integers(period, size=(tracks, 1)) if case.endswith("shifted") else 0
        row = ((y + shift) % period) >= 3
        # 0101 = land/pit/land/pit, 0100 = land/pit/land/land.
        if case == "0100":
            row = ((y + shift) % period // 3) == 1
        return np.broadcast_to(row, (tracks, cells))

    mask = np.empty((tracks, cells), dtype=bool)
    for row in mask:
        # Crop a stationary window of alternating pit/land runs well after startup.
        runs = rng.integers(3, 12, size=cells + 128)
        marks = np.repeat((np.arange(len(runs)) + rng.integers(2)) % 2, runs)
        start = rng.integers(128, 256)
        row[:] = marks[start:start + cells]
    return mask


def fwhm(x, y):
    peak = np.argmax(y)
    half = y[peak] / 2
    left = np.flatnonzero(y[:peak] < half)[-1]
    right = peak + np.flatnonzero(y[peak:] < half)[0]
    lo = np.interp(half, y[left:left + 2], x[left:left + 2])
    hi = np.interp(half, y[right - 1:right + 1][::-1], x[right - 1:right + 1][::-1])
    return hi - lo


def diffraction(mask, cell_um, wavelength_um, radial_kernel, accepted_half_angle):
    tracks, cells = mask.shape
    nfft = 4 * cells
    fy = np.fft.rfftfreq(nfft, cell_um)
    accepted = wavelength_um * fy <= np.sin(np.deg2rad(accepted_half_angle))
    # Integrate a rectangular T cell exactly within the scalar mask model.
    cell_envelope = np.sinc(fy * cell_um)
    slots = np.empty((tracks, np.count_nonzero(accepted)), dtype=complex)
    tangential = np.zeros_like(fy)
    coherent_at_order = np.zeros_like(fy, dtype=complex)
    for start in range(0, tracks, 32):
        rows = slice(start, start + 32)
        field = np.fft.rfft(mask[rows], n=nfft, axis=1) * cell_envelope / cells
        slots[rows] = field[:, accepted]
        tangential += np.sum(np.abs(field)**2, axis=0) / tracks
        coherent_at_order += field.sum(axis=0) / tracks
    # For real masks, +/- tangential frequencies carry equal power.
    field = radial_kernel @ slots
    power = np.abs(field)**2
    profile = power[:, 0] + 2 * power[:, 1:].sum(axis=1)
    return power[:, 0], profile, wavelength_um * fy, tangential, np.abs(coherent_at_order)**2


def simulate(disc, radial_mm, tangential_mm, alpha, wavelength_nm, acceptance, seed, output):
    pitch, cell = DISC[disc]
    wavelength = wavelength_nm / 1000
    u = np.sin(np.deg2rad(alpha)) - wavelength / pitch
    if abs(u) >= 1:
        raise ValueError("The +1 radial order cannot propagate at these settings.")
    if np.sin(np.deg2rad(acceptance)) >= np.sqrt(1-u*u):
        raise ValueError("Reduce vertical acceptance so the selected radial order can propagate.")
    tracks = round(radial_mm * 1000 / pitch)
    cells = 12 * round(tangential_mm * 1000 / cell / 12)
    if tracks < 20 or cells < 24:
        raise ValueError("Use a patch spanning at least 20 tracks and 24 tangential cells.")
    # t is frequency detuning in units of the continuous aperture's first zero.
    t = np.linspace(-4, 4, 801)
    track_index = np.arange(tracks) - (tracks - 1) / 2
    kernel = np.exp(-2j * np.pi * np.outer(t, track_index / tracks)) / tracks
    offset_nm = t * wavelength_nm / tracks
    main = np.abs(t) <= 1
    fig, (ax_masks, ax_line, ax_y) = plt.subplots(
        1, 3, figsize=(16, 4.8), gridspec_kw={"width_ratios": [1, 1.25, 1.25]},
        layout="constrained",
    )
    rows = []
    for index, (case, label) in enumerate(CASES):
        mask = make_mask(case, tracks, cells, seed)
        center, profile, v, ypower, at_order = diffraction(mask, cell, wavelength, kernel, acceptance)
        if index == 0:
            ref_energy = np.trapezoid(profile[main], t[main])
            ref_y = ypower[0]
        limit = np.sqrt(1 - u*u)
        period_cells = {"0101": 6, "0100": 12, "0101_shifted": 6}.get(case)
        satellite_v = wavelength / (period_cells * cell) if period_cells else None
        propagating_satellite = satellite_v is not None and satellite_v < limit
        satellite_index = np.argmin(np.abs(v - satellite_v)) if propagating_satellite else None
        rows.append({
            "case": case,
            "pit_fraction": mask.mean(),
            "center_peak_relative": center[len(t) // 2],
            "center_fwhm_nm": fwhm(offset_nm, center),
            "accepted_fwhm_nm": fwhm(offset_nm, profile),
            "accepted_core_energy_relative": np.trapezoid(profile[main], t[main]) / ref_energy,
            "first_satellite_deg": np.rad2deg(np.arcsin(satellite_v)) if propagating_satellite else "",
            "first_satellite_at_radial_order_relative": (
                at_order[satellite_index] if propagating_satellite else ""
            ),
        })
        color = f"C{index}"
        ax_line.plot(offset_nm, profile / profile.max(), label=label, color=color,
                     linestyle=["-", "--", ":", "-.", (0, (4, 2, 1, 2)), "-"][index])
        visible = v < limit
        ax_y.plot(np.rad2deg(np.arcsin(v[visible])), 10 * np.log10(np.maximum(ypower[visible] / ref_y, 1e-9)),
                  color=color, alpha=0.85, label=label)
        if case != "half_aperture":
            ax_masks.imshow(mask[:6, :48], aspect="auto", interpolation="nearest",
                            cmap="Blues", vmin=0, vmax=1,
                            extent=(0, 48, index + 0.72, index + 0.08))
    n_masks = len(CASES) - 1
    ax_masks.set(xlim=(0, 48), ylim=(n_masks, 0), xlabel="Along-track position (T)",
                 title="Pits (blue) on 6 adjacent tracks")
    ax_masks.set_yticks(np.arange(n_masks) + 0.4, [label for _, label in CASES[:n_masks]])
    ax_line.set(xlabel="Wavelength-equivalent offset (nm)", ylabel="Intensity / own peak",
                title=f"Spectral line within ±{acceptance:g}° across dispersion")
    ax_line.legend(fontsize=8)
    ax_y.axvspan(0, acceptance, color="0.8", alpha=0.5)
    ax_y.set(xlabel="Tangential angle coordinate asin(v) (deg)", ylabel="Relative power (dB)",
             title="Tangential power summed across radial frequencies",
             ylim=(-65, 2), xlim=(0, np.rad2deg(np.arcsin(limit))))
    for ax in (ax_line, ax_y):
        ax.grid(alpha=0.2)
    fig.suptitle(f"{disc} | {tracks*pitch/1000:.3f} × {cells*cell/1000:.3f} mm patch | "
                 f"{tracks} tracks | λ = {wavelength_nm:g} nm | α = {alpha:g}°")
    fig.savefig(output / f"{disc}.png", dpi=160)
    plt.close(fig)
    with (output / f"{disc}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return tracks, cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc", choices=[*DISC, "both"], default="both")
    parser.add_argument("--radial-mm", type=float, default=1.0)
    parser.add_argument("--tangential-mm", type=float, default=0.25)
    parser.add_argument("--alpha", type=float, default=65)
    parser.add_argument("--wavelength-nm", type=float, default=589)
    parser.add_argument("--acceptance-deg", type=float, default=1)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("结果"))
    args = parser.parse_args()
    if not (0 <= args.alpha < 90 and 0 < args.acceptance_deg < 90 and args.wavelength_nm > 0):
        parser.error("Use 0 <= alpha < 90, 0 < acceptance < 90, and positive wavelength.")
    args.output.mkdir(parents=True, exist_ok=True)
    discs = DISC if args.disc == "both" else [args.disc]
    for disc in discs:
        tracks, cells = simulate(disc, args.radial_mm, args.tangential_mm, args.alpha,
                                 args.wavelength_nm, args.acceptance_deg, args.seed, args.output)
        print(f"{disc}: {tracks} tracks, {cells} cells per track")


if __name__ == "__main__":
    main()
