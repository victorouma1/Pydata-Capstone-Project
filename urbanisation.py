"""
urbanisation.py
───────────────
Module that visualises the relationship between degree of urbanisation
(GHS-DUG DEGURBA) and air-quality pollution in Kenya.

Inputs
------
l1_tif  : path to KEN_DUG_2026_GRID_L1_R2025A_v1.tif  (3-class DEGURBA)
l2_tif  : path to KEN_DUG_2026_GRID_L2_R2025A_v1.tif  (9-class DEGURBA)
aq_csv  : path to sensor CSV (optional; falls back to literature values)
"""

import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from PIL import Image

warnings.filterwarnings("ignore")

# ── Colour palette ────────────────────────────────────────────────────────────
DARK_BG   = "#0d0d1a"
PANEL_BG  = "#12122a"
GRID_COL  = "#1e1e3a"
NEON_CYAN = "#00f5ff"
NEON_PINK = "#ff2d78"

# ── Raster extent (Kenya) ─────────────────────────────────────────────────────
LAT_MAX, LAT_MIN =  5.02, -4.67
LON_MIN, LON_MAX = 33.91, 41.91
IMG_ROWS, IMG_COLS = 1209, 796

# ── Class definitions ─────────────────────────────────────────────────────────
L1_CLASSES = {
    1: ("Rural",         "#3a7d44"),
    2: ("Town / Suburb", "#f5a623"),
    3: ("City",          "#ff2d78"),
}

L2_CLASSES = {
    10: ("Very Sparse Rural",   "#1b4332"),
    11: ("Low Density Rural",   "#2d6a4f"),
    12: ("Rural Cluster",       "#52b788"),
    13: ("Peri-urban / Suburb", "#d4a017"),
    21: ("Semi-dense Urban",    "#f77f00"),
    22: ("Dense Urban",         "#d62828"),
    23: ("Urban Centre",        "#9b2226"),
    30: ("Major City Core",     "#ff2d78"),
}

# ── Fallback literature values ────────────────────────────────────────────────
LITERATURE_PM25 = {
    1: {"median": 12.1, "iqr": (8.0,  16.8),  "label": "Rural"},
    2: {"median": 26.4, "iqr": (18.0, 38.5),  "label": "Town / Suburb"},
    3: {"median": 48.7, "iqr": (33.0, 70.2),  "label": "City"},
}
LITERATURE_PM10 = {
    1: {"median": 24.3, "iqr": (16.0, 34.0),  "label": "Rural"},
    2: {"median": 52.1, "iqr": (36.0, 76.0),  "label": "Town / Suburb"},
    3: {"median": 96.4, "iqr": (65.0, 138.0), "label": "City"},
}


class UrbanisationPollution:
    """
    Encapsulates loading, processing, and plotting urbanisation vs. pollution.

    Parameters
    ----------
    l1_tif : str | Path
        Path to the Level-1 (3-class) GHS-DUG DEGURBA raster.
    l2_tif : str | Path
        Path to the Level-2 (9-class) GHS-DUG DEGURBA raster.
    aq_csv : str | Path | None
        Optional path to the sensor CSV (same semicolon-delimited format
        used by the rest of the dashboard).  When *None* or the file is
        missing, representative literature medians are used instead.
    """

    def __init__(self, l1_tif: str | Path, l2_tif: str | Path,
                 aq_csv: str | Path | None = None):
        self._l1_tif = Path(l1_tif)
        self._l2_tif = Path(l2_tif)
        self._aq_csv = Path(aq_csv) if aq_csv else None

        self._l1_arr: np.ndarray | None = None
        self._l2_arr: np.ndarray | None = None
        self._stats_pm25: dict = LITERATURE_PM25
        self._stats_pm10: dict = LITERATURE_PM10
        self.data_source: str  = "Literature-based representative medians (WHO/UNEP East Africa)"

    # ── Public API ────────────────────────────────────────────────────────────

    def load_grids(self) -> None:
        """Load the L1 and L2 DEGURBA rasters from disk."""
        self._l1_arr = self._load_tif(self._l1_tif)
        self._l2_arr = self._load_tif(self._l2_tif)

    def load_aq_data(self) -> None:
        """
        Load sensor CSV and compute per-class statistics.
        If the CSV is absent, the instance keeps the literature fallback values.
        """
        if self._aq_csv is None or not self._aq_csv.exists():
            return  # keep defaults

        import pandas as pd

        df = pd.read_csv(self._aq_csv, sep=";", low_memory=False)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["lat"]   = pd.to_numeric(df["lat"],   errors="coerce")
        df["lon"]   = pd.to_numeric(df["lon"],   errors="coerce")
        df.dropna(subset=["value", "lat", "lon"], inplace=True)

        rows, cols = self._latlon_to_rowcol(df["lat"].values, df["lon"].values)
        rows = np.clip(rows, 0, IMG_ROWS - 1)
        cols = np.clip(cols, 0, IMG_COLS - 1)

        df["urb_class"] = self._l1_arr[rows, cols]
        df = df[df["urb_class"].isin(L1_CLASSES.keys())]

        stats = self._class_stats(df)
        self._stats_pm25 = stats.get("P2", LITERATURE_PM25)
        self._stats_pm10 = stats.get("P1", LITERATURE_PM10)
        self.data_source = f"Sensor CSV – {self._aq_csv.name}"

    def make_figure(self) -> plt.Figure:
        """Build and return the full urbanisation-vs-pollution figure."""
        if self._l1_arr is None or self._l2_arr is None:
            raise RuntimeError("Call load_grids() before make_figure().")
        return self._build_figure()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load_tif(path: Path) -> np.ndarray:
        return np.array(Image.open(path))

    @staticmethod
    def _latlon_to_rowcol(lat: np.ndarray, lon: np.ndarray):
        row = (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (IMG_ROWS - 1)
        col = (lon - LON_MIN) / (LON_MAX - LON_MIN) * (IMG_COLS - 1)
        return row.astype(int), col.astype(int)

    @staticmethod
    def _class_stats(df) -> dict:
        results = {}
        for ptype in ["P1", "P2"]:
            sub = df[df["value_type"] == ptype]
            stats = {}
            for cls in sorted(L1_CLASSES.keys()):
                vals = sub[sub["urb_class"] == cls]["value"]
                if len(vals) < 5:
                    continue
                stats[cls] = {
                    "median": float(vals.median()),
                    "iqr":    (float(vals.quantile(0.25)), float(vals.quantile(0.75))),
                    "label":  L1_CLASSES[cls][0],
                    "n":      len(vals),
                }
            results[ptype] = stats
        return results

    @staticmethod
    def _build_rgba(arr: np.ndarray, class_map: dict) -> np.ndarray:
        h, w = arr.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        for cls, (_, hex_col) in class_map.items():
            r = int(hex_col[1:3], 16)
            g = int(hex_col[3:5], 16)
            b = int(hex_col[5:7], 16)
            rgba[arr == cls] = [r, g, b, 220]
        rgba[arr == 0] = [13, 13, 26, 80]
        return rgba

    def _style_map_ax(self, ax, title: str, rgba: np.ndarray) -> None:
        lat_ticks = np.linspace(LAT_MAX, LAT_MIN, 5)
        lon_ticks = np.linspace(LON_MIN, LON_MAX, 5)
        pos       = np.linspace(0, 1, 5)

        ax.imshow(rgba, aspect="auto", origin="upper", extent=[0, 1, 0, 1])
        ax.set_facecolor(DARK_BG)
        ax.set_title(title, color="white", fontsize=12, fontweight="bold", pad=6)
        ax.set_yticks(pos)
        ax.set_yticklabels([f"{t:.1f}°" for t in lat_ticks[::-1]],
                           color="#aaaacc", fontsize=7)
        ax.set_xticks(pos)
        ax.set_xticklabels([f"{t:.1f}°" for t in lon_ticks],
                           color="#aaaacc", fontsize=7)
        ax.tick_params(length=3)
        for sp in ax.spines.values():
            sp.set_color(GRID_COL)

    @staticmethod
    def _bar_chart(ax, stats: dict, pollutant: str) -> None:
        labels  = [s["label"]  for s in stats.values()]
        medians = [s["median"] for s in stats.values()]
        iqr_lo  = [s["median"] - s["iqr"][0] for s in stats.values()]
        iqr_hi  = [s["iqr"][1] - s["median"] for s in stats.values()]
        colors  = [L1_CLASSES[k][1] for k in stats.keys()]
        xs      = np.arange(len(labels))

        bars = ax.bar(xs, medians, color=colors,
                      edgecolor=DARK_BG, linewidth=0.8, zorder=3)
        ax.errorbar(xs, medians, yerr=[iqr_lo, iqr_hi],
                    fmt="none", color=NEON_CYAN, capsize=5,
                    capthick=1.5, elinewidth=1.5, zorder=4)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, color="#aaaacc", fontsize=8)
        ax.set_ylabel(f"Median {pollutant} (µg/m³)", color="#aaaacc", fontsize=8)
        ax.tick_params(colors="#aaaacc")
        ax.set_facecolor(PANEL_BG)
        ax.spines[:].set_color(GRID_COL)
        ax.grid(True, axis="y", color=GRID_COL,
                linestyle="--", linewidth=0.5, zorder=0)
        ax.set_title(f"{pollutant} by Urbanisation Class",
                     color="white", fontsize=9, fontweight="bold", pad=5)
        for bar, med in zip(bars, medians):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{med:.1f}", ha="center", va="bottom",
                    color="white", fontsize=7, fontweight="bold")

    def _build_figure(self) -> plt.Figure:
        fig = plt.figure(figsize=(20, 13), facecolor=DARK_BG)
        fig.suptitle(
            "Urbanisation vs. Air Pollution — Kenya 2026",
            color=NEON_CYAN, fontsize=19, fontweight="bold",
            y=0.97, fontfamily="monospace",
        )

        gs = gridspec.GridSpec(
            3, 3, figure=fig,
            wspace=0.38, hspace=0.48,
            left=0.05, right=0.97, top=0.92, bottom=0.06,
        )

        ax_l1   = fig.add_subplot(gs[0:2, 0])
        ax_l2   = fig.add_subplot(gs[0:2, 1])
        ax_pie  = fig.add_subplot(gs[0, 2])
        ax_pm25 = fig.add_subplot(gs[1, 2])
        ax_pm10 = fig.add_subplot(gs[2, 0])
        ax_scat = fig.add_subplot(gs[2, 1:3])

        # ── Maps ──────────────────────────────────────────────────────────────
        rgba_l1 = self._build_rgba(self._l1_arr, L1_CLASSES)
        self._style_map_ax(ax_l1,
                           "Degree of Urbanisation — Level 1\n(GHS-DUG DEGURBA)",
                           rgba_l1)
        ax_l1.legend(
            handles=[mpatches.Patch(color=col, label=lbl)
                     for _, (lbl, col) in L1_CLASSES.items()],
            loc="lower left", framealpha=0.25,
            facecolor=PANEL_BG, edgecolor=GRID_COL,
            labelcolor="white", fontsize=8,
        )

        rgba_l2 = self._build_rgba(self._l2_arr, L2_CLASSES)
        self._style_map_ax(ax_l2,
                           "Degree of Urbanisation — Level 2\n(GHS-DUG DEGURBA)",
                           rgba_l2)
        ax_l2.legend(
            handles=[mpatches.Patch(color=col, label=lbl)
                     for _, (lbl, col) in L2_CLASSES.items()],
            loc="lower left", framealpha=0.25,
            facecolor=PANEL_BG, edgecolor=GRID_COL,
            labelcolor="white", fontsize=7,
        )

        # ── Pie ───────────────────────────────────────────────────────────────
        counts = {k: (self._l1_arr == k).sum() for k in L1_CLASSES}
        wedges, texts, autotexts = ax_pie.pie(
            [counts[k] for k in L1_CLASSES],
            labels=[L1_CLASSES[k][0] for k in L1_CLASSES],
            colors=[L1_CLASSES[k][1] for k in L1_CLASSES],
            autopct="%1.1f%%", startangle=140,
            textprops=dict(color="white", fontsize=8),
            wedgeprops=dict(edgecolor=DARK_BG, linewidth=1.5),
            pctdistance=0.75,
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color(DARK_BG)
            at.set_fontweight("bold")
        ax_pie.set_facecolor(DARK_BG)
        ax_pie.set_title("Land Area by\nUrbanisation Class",
                         color="white", fontsize=10, fontweight="bold", pad=4)

        # ── Bar charts ────────────────────────────────────────────────────────
        self._bar_chart(ax_pm25, self._stats_pm25, "PM₂.₅")
        self._bar_chart(ax_pm10, self._stats_pm10, "PM₁₀")

        # ── Gradient scatter ──────────────────────────────────────────────────
        ax_scat.set_facecolor(PANEL_BG)
        ax_scat.spines[:].set_color(GRID_COL)
        ax_scat.grid(True, color=GRID_COL, linestyle="--", linewidth=0.5, zorder=0)

        cls_keys  = sorted(self._stats_pm25.keys())
        xs        = np.arange(len(cls_keys))
        pm25_meds = [self._stats_pm25[k]["median"] for k in cls_keys]
        pm10_meds = [self._stats_pm10[k]["median"] for k in cls_keys]
        pm25_lo   = [self._stats_pm25[k]["iqr"][0] for k in cls_keys]
        pm25_hi   = [self._stats_pm25[k]["iqr"][1] for k in cls_keys]
        pm10_lo   = [self._stats_pm10[k]["iqr"][0] for k in cls_keys]
        pm10_hi   = [self._stats_pm10[k]["iqr"][1] for k in cls_keys]
        xlabels   = [self._stats_pm25[k]["label"]  for k in cls_keys]

        ax_scat.fill_between(xs, pm25_lo, pm25_hi, color=NEON_CYAN, alpha=0.15, zorder=1)
        ax_scat.fill_between(xs, pm10_lo, pm10_hi, color=NEON_PINK,  alpha=0.15, zorder=1)
        ax_scat.plot(xs, pm25_meds, "o-", color=NEON_CYAN, linewidth=2.2,
                     markersize=8, zorder=3, label="PM₂.₅ median")
        ax_scat.plot(xs, pm10_meds, "s-", color=NEON_PINK,  linewidth=2.2,
                     markersize=8, zorder=3, label="PM₁₀  median")
        ax_scat.axhline(15, color=NEON_CYAN, linewidth=0.9, linestyle=":",
                        alpha=0.6, label="WHO PM₂.₅ guideline (15 µg/m³)")
        ax_scat.axhline(45, color=NEON_PINK,  linewidth=0.9, linestyle=":",
                        alpha=0.6, label="WHO PM₁₀  guideline (45 µg/m³)")

        ax_scat.set_xticks(xs)
        ax_scat.set_xticklabels(xlabels, color="#aaaacc", fontsize=9)
        ax_scat.set_ylabel("Concentration (µg/m³)", color="#aaaacc", fontsize=9)
        ax_scat.tick_params(colors="#aaaacc")
        ax_scat.set_title(
            "Urbanisation → Pollution Gradient  (median ± IQR)",
            color="white", fontsize=10, fontweight="bold", pad=6,
        )
        ax_scat.legend(
            loc="upper left", framealpha=0.2,
            facecolor=PANEL_BG, edgecolor=GRID_COL,
            labelcolor="white", fontsize=8,
        )

        for i in range(len(cls_keys) - 1):
            uplift = pm25_meds[i + 1] - pm25_meds[i]
            mid_x  = (xs[i] + xs[i + 1]) / 2
            mid_y  = max(pm25_meds[i], pm25_meds[i + 1]) + 2
            ax_scat.annotate(
                f"+{uplift:.1f}",
                xy=(mid_x, mid_y), ha="center", va="bottom",
                color=NEON_CYAN, fontsize=9, fontweight="bold",
            )

        fig.text(
            0.01, 0.005,
            f"Urbanisation: GHS-DUG DEGURBA R2025A v1 (WorldPop)  |  "
            f"Air Quality: {self.data_source}  |  Resolution: 1 km",
            color="#5a5a7a", fontsize=7, va="bottom",
        )

        return fig