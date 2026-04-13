import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


AQI_LEVELS = [
    ("Good",                           0,     9,     "#00e400"),  
    ("Moderate",                       9.1,   35.4,  "#ffe600"),  
    ("Unhealthy for Sensitive Groups", 35.5,  55.4,  "#ff8c00"),  
    ("Unhealthy",                      55.5,  125.4, "#ff2020"),  
    ("Very Unhealthy",                 125.5, 225.4, "#cc44ff"),  
    ("Hazardous",                      225.5, 325.4, "#ff00aa"),  
]

DARK_BG   = "#0d0d1a"
PANEL_BG  = "#12122a"
NEON_CYAN = "#00f5ff"
GRID_COL  = "#1e1e3a"


class aq_trend:
    def __init__(self, aq_data: pd.DataFrame, pollutant: str):
        self._aq_data  = aq_data.copy()
        self.pollutant = pollutant

    def arrange_format(self):
        self._aq_data["value"]     = pd.to_numeric(self._aq_data["value"],     errors="coerce")
        self._aq_data["lat"]       = pd.to_numeric(self._aq_data["lat"],       errors="coerce")
        self._aq_data["timestamp"] = pd.to_datetime(self._aq_data["timestamp"], format="ISO8601")

    def sort_aq_index(self):
        self._aq_data.set_index("timestamp", inplace=True)
        self._aq_data.sort_index(inplace=True)

    def group_pollutant(self):
        grouped = (
            self._aq_data
            .groupby("value_type")
            .resample("D")[["value"]]
            .mean()
            .groupby(level=0)
            .rolling(window=3)
            .mean()
        )
        grouped.dropna(inplace=True)
        self.p_df = grouped.xs(self.pollutant, level=1)
        self.p_df = self.p_df.reset_index(level=0, drop=True)


    def plot_trend(self) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)

        for label, lo, hi, color in AQI_LEVELS:
            ax.axhspan(lo, hi, facecolor=color, alpha=0.38, label=label)
            ax.axhline(lo, color=color, linewidth=0.6, alpha=0.55, linestyle=":")


        ax.plot(
            self.p_df.index,
            self.p_df["value"],
            color=NEON_CYAN,
            linewidth=2.2,
            label=f"{self.pollutant} (3-day avg)",
        )

        ax.set_title(
            f"Air Quality Trend — {self.pollutant}",
            color="white", fontsize=16, fontweight="bold", pad=14,
        )
        ax.set_ylabel("Concentration (µg/m³)", color="#aaaacc", fontsize=12)
        ax.set_xlabel("Date", color="#aaaacc", fontsize=12)
        ax.tick_params(colors="#aaaacc")
        ax.spines[:].set_color(GRID_COL)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(True, color=GRID_COL, linestyle="--", linewidth=0.6)
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            framealpha=0.15,
            labelcolor="white",
            facecolor=PANEL_BG,
            edgecolor=GRID_COL,
            fontsize=9,
        )

        fig.tight_layout()
        return fig
    