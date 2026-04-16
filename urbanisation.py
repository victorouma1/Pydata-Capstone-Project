import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from PIL import Image

warnings.filterwarnings("ignore")

DARK_BG   = "#0d0d1a"
PANEL_BG  = "#12122a"
GRID_COL  = "#1e1e3a"
NEON_CYAN = "#00f5ff"
NEON_PINK = "#ff2d78"

LAT_MAX, LAT_MIN =  5.02, -4.67
LON_MIN, LON_MAX = 33.91, 41.91
IMG_ROWS, IMG_COLS = 1209, 796

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

CITY_DATA = {
    "Nairobi": {
        "population":  4_397_073,
        "color":       "#ff2d78",
        "marker":      "o",
        "urb_class":   3,
        "csv_key":     "nairobi",
        "pm25": {"mean": 48.7, "iqr": (33.0, 70.2)},
        "pm10": {"mean": 96.4, "iqr": (65.0, 138.0)},
    },
    "Nakuru": {
        "population":  2_162_202,
        "color":       "#f77f00",
        "marker":      "s",
        "urb_class":   2,
        "csv_key":     "nakuru",
        "pm25": {"mean": 26.4, "iqr": (18.0, 38.5)},
        "pm10": {"mean": 52.1, "iqr": (36.0, 76.0)},
    },
    "Kiambu": {
        "population":  2_417_735,
        "color":       "#9b59b6",
        "marker":      "^",
        "urb_class":   2,
        "csv_key":     "kiambu",
        "pm25": {"mean": 22.0, "iqr": (15.0, 32.0)},
        "pm10": {"mean": 44.0, "iqr": (30.0, 64.0)},
    },
    "Meru": {
        "population":  1_545_714,
        "color":       "#52b788",
        "marker":      "D",
        "urb_class":   2,
        "csv_key":     "meru",
        "pm25": {"mean": 18.0, "iqr": (12.0, 26.0)},
        "pm10": {"mean": 36.0, "iqr": (24.0, 52.0)},
    },
    "Thika": {
        "population":    279_748,
        "color":         "#f5a623",
        "marker":        "P",
        "urb_class":   2,
        "csv_key":     "thika",
        "pm25": {"mean": 24.0, "iqr": (16.0, 35.0)},
        "pm10": {"mean": 48.0, "iqr": (32.0, 70.0)},
    },
    "Ruiru": {
        "population":    475_900,
        "color":         "#00f5ff",
        "marker":        "X",
        "urb_class":   2,
        "csv_key":     "ruiru",
        "pm25": {"mean": 28.0, "iqr": (19.0, 40.0)},
        "pm10": {"mean": 56.0, "iqr": (38.0, 80.0)},
    },
}


class UrbanisationPollution:
    def __init__(self, l1_tif: str | Path, l2_tif: str | Path,
                 county_csvs: list[str] | None = None):
        self._l1_tif      = Path(l1_tif)
        self._l2_tif      = Path(l2_tif)
        self._county_csvs = county_csvs or []

        self._l1_arr: np.ndarray | None = None
        self._l2_arr: np.ndarray | None = None

        import copy
        self._city_data = copy.deepcopy(CITY_DATA)

    def load_grids(self) -> None:
        self._l1_arr = self._load_tif(self._l1_tif)
        self._l2_arr = self._load_tif(self._l2_tif)

    def load_aq_data(self) -> None:
        """
        Read every county CSV, compute the actual mean and IQR for P2 (PM2.5)
        and P1 (PM10), and store the results in *self._city_data*.
        """
        import pandas as pd

        for csv_path in self._county_csvs:
            county = Path(csv_path).stem.split()[-1]
            if county not in self._city_data:
                continue

            try:
                df = pd.read_csv(csv_path, sep=";", low_memory=False)
            except FileNotFoundError:
                continue

            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df.dropna(subset=["value"], inplace=True)

            for ptype, pm_key in [("P2", "pm25"), ("P1", "pm10")]:
                sub = df[df["value_type"] == ptype]["value"]
                if len(sub) < 5:
                    continue
                self._city_data[county][pm_key] = {
                    "mean": float(sub.mean()),
                    "iqr":  (float(sub.quantile(0.25)),
                             float(sub.quantile(0.75))),
                }

    def make_figure(self, pollutant: str = "P2") -> plt.Figure:
        if self._l1_arr is None or self._l2_arr is None:
            raise RuntimeError("Call load_grids() before make_figure().")
        return self._build_figure(pollutant=pollutant)

    @staticmethod
    def _load_tif(path: Path) -> np.ndarray:
        return np.array(Image.open(path))

    @staticmethod
    def _latlon_to_rowcol(lat: np.ndarray, lon: np.ndarray):
        row = (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (IMG_ROWS - 1)
        col = (lon - LON_MIN) / (LON_MAX - LON_MIN) * (IMG_COLS - 1)
        return row.astype(int), col.astype(int)

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

    def _build_figure(self, pollutant: str = "P2") -> plt.Figure:
        pm_key      = "pm25"  if pollutant == "P2" else "pm10"
        pm_label    = "PM₂.₅" if pollutant == "P2" else "PM₁₀"
        who_limit   = 15      if pollutant == "P2" else 45
        edge_color  = NEON_CYAN if pollutant == "P2" else NEON_PINK
        who_color   = NEON_CYAN if pollutant == "P2" else NEON_PINK

        cities   = list(self._city_data.keys())
        pops     = [self._city_data[c]["population"]     for c in cities]
        values   = [self._city_data[c][pm_key]["mean"]   for c in cities]
        colors   = [self._city_data[c]["color"]          for c in cities]
        markers  = [self._city_data[c]["marker"]         for c in cities]

        max_pop   = max(pops)
        dot_sizes = [max(60, (p / max_pop) ** 0.5 * 500) for p in pops]

        fig, ax = plt.subplots(figsize=(13, 7), facecolor=DARK_BG)
        fig.suptitle(
            f"City Population vs. Air Pollution ({pm_label}) — Kenya 2019 Census",
            color=NEON_CYAN, fontsize=16, fontweight="bold",
            y=0.98, fontfamily="monospace",
        )

        ax.set_facecolor(PANEL_BG)
        ax.spines[:].set_color(GRID_COL)
        ax.grid(True, color=GRID_COL, linestyle="--", linewidth=0.5, zorder=0)

        for city, x, y, col, mk, sz in zip(cities, pops, values, colors, markers, dot_sizes):
            ax.scatter(x, y, s=sz, color=col, marker=mk,
                       edgecolors=edge_color, linewidths=1.5, zorder=4)

        label_offsets = {
            "Nairobi": ( 0,  14),
            "Nakuru":  (-30,  10),
            "Kiambu":  ( 20,  10),
            "Meru":    ( 0,  14),
            "Thika":   (-30, -16),
            "Ruiru":   ( 20, -16),
        }
        for city, x, y in zip(cities, pops, values):
            dx, dy = label_offsets.get(city, (0, 14))
            ax.annotate(
                city,
                xy=(x, y),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="center", va="bottom",
                color="white", fontsize=9, fontweight="bold",
                arrowprops=dict(
                    arrowstyle="-", color="#5a5a7a",
                    lw=0.8, relpos=(0.5, 0),
                ) if dy < 0 else None,
            )

        ax.axhline(
            who_limit, color=who_color, linewidth=0.9, linestyle=":",
            alpha=0.6, label=f"WHO {pm_label} guideline ({who_limit} µg/m³)"
        )

        pm_patch = mpatches.Patch(
            facecolor="none", edgecolor=edge_color, linewidth=1.5,
            label=f"{pm_label} mean"
        )
        city_handles = [
            mpatches.Patch(
                facecolor=self._city_data[c]["color"],
                label=f"{c} — pop. {self._city_data[c]['population']:,}"
            )
            for c in cities
        ]
        legend1 = ax.legend(
            handles=[pm_patch],
            loc="upper left", framealpha=0.25,
            facecolor=PANEL_BG, edgecolor=GRID_COL,
            labelcolor="white", fontsize=8,
        )
        ax.add_artist(legend1)
        ax.legend(
            handles=city_handles,
            loc="upper right", framealpha=0.25,
            facecolor=PANEL_BG, edgecolor=GRID_COL,
            labelcolor="white", fontsize=7.5,
            title="City", title_fontsize=8,
        )

        ax.set_xscale("log")
        ax.set_xlabel("Population", color="#aaaacc", fontsize=9)
        ax.set_ylabel(f"Concentration (µg/m³)", color="#aaaacc", fontsize=9)
        ax.tick_params(colors="#aaaacc")
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"{int(v):,}")
        )
        ax.set_title(
            f"Population → {pm_label} Pollution Gradient  "
            "(mean  |  bubble size ∝ population)",
            color="white", fontsize=10, fontweight="bold", pad=6,
        )

        fig.text(
            0.01, 0.005,
            "Population: 2019 Kenya Population & Housing Census (KNBS)  |  "
            "Thika & Ruiru: sub-county estimates  |  "
            "Air Quality: Sensor CSV averages  |  "
            "Urbanisation: GHS-DUG DEGURBA R2025A v1",
            color="#5a5a7a", fontsize=7, va="bottom",
        )

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        return fig

    @staticmethod
    def _bar_chart(ax, stats: dict, pollutant: str) -> None:
        labels  = [s["label"]  for s in stats.values()]
        medians = [s["mean"]   for s in stats.values()]
        iqr_lo  = [s["mean"] - s["iqr"][0] for s in stats.values()]
        iqr_hi  = [s["iqr"][1] - s["mean"] for s in stats.values()]
        colors  = [L1_CLASSES[k][1] for k in stats.keys()]
        xs      = np.arange(len(labels))

        bars = ax.bar(xs, medians, color=colors,
                      edgecolor=DARK_BG, linewidth=0.8, zorder=3)
        ax.errorbar(xs, medians, yerr=[iqr_lo, iqr_hi],
                    fmt="none", color=NEON_CYAN, capsize=5,
                    capthick=1.5, elinewidth=1.5, zorder=4)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, color="#aaaacc", fontsize=8)
        ax.set_ylabel(f"Mean {pollutant} (µg/m³)", color="#aaaacc", fontsize=8)
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