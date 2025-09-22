#!/usr/bin/env python3
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Import the data from parse_gauge.py
from parse_gauge import parse_gauge_file_to_table1

def mm_to_inches(x_mm: pd.Series) -> pd.Series:
    return x_mm / 25.4

# Choose colorbar min/max based on data, with optional quantile clamp
def choose_color_limits(series: pd.Series, vmin=0.0, vmax=None, clamp_q=0.99):
    if vmax is None:
        vmax = float(series.quantile(clamp_q)) if series.size else 1.0
        if vmax <= vmin:
            vmax = vmin + 1.0
    return vmin, vmax

# Compute map extent with padding
def auto_extent(lons: pd.Series, lats: pd.Series, pad_deg=2.0):
    return [
        float(lons.min()) - pad_deg,
        float(lons.max()) + pad_deg,
        float(lats.min()) - pad_deg,
        float(lats.max()) + pad_deg,
    ]

# Returns NWS-style colormap and normalization for precipitation in inches
def get_nws_precip_cmap_and_norm(units_label="in"):
    levels_in = [
        0.01, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00, 1.25, 1.50, 1.75, 2.00,
        2.50, 3.00, 3.50, 4.00, 5.00, 6.00, 7.00, 8.00, 9.00, 10.00, 11.00, 12.00
    ]
    colors = [
        "#b3ecff", "#66d9ff", "#1fa3ff", "#0090ff", "#00e600", "#00b300", "#33cc33", "#99e600",
        "#ffff00", "#ffd700", "#ffb300", "#ff9900", "#ff6600", "#ff0000", "#e60073", "#cc00cc",
        "#8000ff", "#b266ff", "#e6e6fa", "#f0f8ff", "#e0ffff", "#f5f5dc", "#ffffe0"
    ]
    cmap = mcolors.ListedColormap(colors, name="nws_precip")
    norm = mcolors.BoundaryNorm(levels_in, cmap.N)
    return cmap, norm, levels_in

# Returns bins, colors, and marker sizes for NWS-style precipitation plotting
def get_nws_bins_and_colors():
    bins = np.array([
        0.01, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00, 1.25, 1.50, 1.75, 2.00,
        2.50, 3.00, 3.50, 4.00, 5.00
    ])
    colors = [
        "#b3ecff", "#66d9ff", "#1fa3ff", "#0090ff",
        "#00e600", "#00b300", "#33cc33", "#99e600",
        "#ffff00", "#ffd700", "#ffb300", "#ff9900",
        "#ff6600", "#ff0000", "#e60073", "#cc00cc",
        "#8000ff"
    ]
    sizes = [
        18, 18, 22, 22,
        30, 34, 38, 42,
        60, 70, 80, 90,
        110, 130, 150, 170, 200
    ]
    return bins, colors, sizes

# Assign each value to a color and size bin
def assign_bins(vals, bins, colors, sizes):
    inds = np.digitize(vals, bins, right=True)
    inds = np.clip(inds, 0, len(colors)-1)
    return np.array(colors)[inds], np.array(sizes)[inds], inds

# Plot precipitation data on a Cartopy map with NWS-style bins and colorbar
def plot_cartopy(df: pd.DataFrame, vals: pd.Series, *, units_label: str,
                 title: str, out_png: Path, vmin=0.0, vmax=None):
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except Exception as e:
        raise RuntimeError(
            "Cartopy not available. Install it or use --no-map to use the quick scatter."
        ) from e

    proj_data = ccrs.PlateCarree()
    proj_view = ccrs.LambertConformal(central_longitude=-96, central_latitude=39)

    fig = plt.figure(figsize=(10.5, 7.5), dpi=150)
    ax = plt.axes(projection=proj_view)

    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.6)
    ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=0.4, edgecolor="k")

    zeros = df[vals == 0]
    nonzeros = df[vals > 0]
    nonzero_vals = vals[vals > 0]

    # Plot zero-precip points as green pluses underneath
    if not zeros.empty:
        ax.scatter(zeros["Long."], zeros["Lat."], marker="+", color="green", s=12,
                   label="0 in", transform=proj_data, zorder=1)

    # Plot nonzero points as colored circles with black outline
    if not nonzeros.empty and units_label == "in":
        bins, colors, sizes = get_nws_bins_and_colors()
        c, s, inds = assign_bins(nonzero_vals, bins, colors, sizes)
        sc = ax.scatter(nonzeros["Long."], nonzeros["Lat."], c=c, s=s,
                        marker="o", edgecolor="black", linewidth=0.7, transform=proj_data, zorder=3)

        from matplotlib.colors import ListedColormap, BoundaryNorm
        cmap = ListedColormap(colors)
        norm = BoundaryNorm(np.concatenate(([0], bins)), len(colors))
        cbar = plt.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=cmap),
            ax=ax, orientation="vertical", fraction=0.035, pad=0.04, ticks=bins
        )
        cbar.set_label("Precipitation (inches)")
        cbar.ax.set_yticklabels([f"{b:.2f}" for b in bins])

    # fallback for mm or other units
    elif not nonzeros.empty:
        sc = ax.scatter(nonzeros["Long."], nonzeros["Lat."], c=nonzero_vals, s=30,
                        cmap="viridis", edgecolor="black", linewidth=0.7, transform=proj_data, label=">0", zorder=3)
        cbar = plt.colorbar(sc, ax=ax, orientation="vertical", fraction=0.035, pad=0.04)
        cbar.set_label(f"Precipitation ({units_label})")

    ax.set_title(title)

    xmin, xmax, ymin, ymax = auto_extent(df["Long."], df["Lat."], pad_deg=2.0)
    ax.set_extent([xmin, xmax, ymin, ymax], crs=proj_data)

    plt.tight_layout()
    fig.savefig(out_png, bbox_inches="tight")
    print(f"Wrote {out_png}")

def main():
    # Parse command-line arguments and run the plotting workflow
    ap = argparse.ArgumentParser(description="Plot gauge precip for a single MRMS gauge file.")
    ap.add_argument(
        "fname",
        nargs="?",
        default=None,
        help="Path to GAUGE_1H_MRMS_QC.YYYYMMDD.HH0000 (optional, uses parse_gauge default if omitted)"
    )
    ap.add_argument("--qc-keep", type=int, nargs="*", default=None,
                    help="QC flags to keep (e.g., --qc-keep 0). Default keeps all.")
    ap.add_argument("--hide-zeros", action="store_true", help="Filter out zero precip.")
    ap.add_argument("--units", choices=["mm", "in"], default="mm",
                    help="Units to display on the plot (and convert if needed).")
    ap.add_argument("--vmax", type=float, default=None, help="Override colorbar max.")
    ap.add_argument("--out", type=str, default=None,
                    help="Output PNG path (default: same as input, but in current directory)")
    args = ap.parse_args()

    if args.fname is None:
        from parse_gauge import FNAME
        args.fname = FNAME

    df = parse_gauge_file_to_table1(args.fname, qc_keep=set(args.qc_keep) if args.qc_keep else None)
    print("Parsed columns:", df.columns)

    data = df.copy()
    if args.hide_zeros:
        data = data[data["Obs value"] > 0]

    if data.empty:
        raise SystemExit("No rows to plot after filtering.")

    vals_mm = data["Obs value"].astype(float)
    vals_in = mm_to_inches(vals_mm)

    tmin = pd.to_datetime(data["Time"].min())
    tmax = pd.to_datetime(data["Time"].max())
    base_hour = Path(args.fname).name.split(".")[-2] + "Z"

    title = f"Gauge 1H precip — ending {base_hour} (per-gauge valid: {tmin:%Y-%m-%d %H:%MZ}..{tmax:%H:%MZ})"
    if args.out is not None:
        out_png = Path(args.out)
    else:
        plots_dir = Path(__file__).parent.parent / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        out_png = plots_dir / (Path(args.fname).stem + ".png")

    plot_cartopy(data, vals_in, units_label="in", title=title, out_png=out_png, vmax=args.vmax)

if __name__ == "__main__":
    main()