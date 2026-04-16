import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Colour / label helpers shared by both classes
# ---------------------------------------------------------------------------

DARK_BG   = "#0d0d1a"
PANEL_BG  = "#12122a"
GRID_COL  = "#1e1e3a"

_AQI_BANDS = [
    (9,     "#00e400", "Good  (0–9)"),
    (35.4,  "#ffff00", "Moderate  (9–35)"),
    (55.4,  "#ff7e00", "Unhealthy — Sensitive  (35–55)"),
    (125.4, "#ff0000", "Unhealthy  (55–125)"),
    (225.4, "#8f3f97", "Very Unhealthy  (125–225)"),
    (float("inf"), "#7e0023", "Hazardous  (225+)"),
]


def _aqi_color(val: float) -> str:
    for threshold, col, _ in _AQI_BANDS:
        if val <= threshold:
            return col
    return "#7e0023"


def _aqi_label(val: float) -> str:
    for threshold, _, label in _AQI_BANDS:
        if val <= threshold:
            return label
    return "Hazardous  (225+)"


# ---------------------------------------------------------------------------
# County coordinate lookup (approximate centroids)
# ---------------------------------------------------------------------------

COUNTY_COORDS: dict[str, tuple[float, float]] = {
    "Nairobi": (-1.286, 36.817),
    "Kisumu":  (-0.092, 34.768),
    "Meru":    ( 0.047, 37.649),
    "Nakuru":  (-0.303, 36.080),
    "Kiambu":  (-1.031, 36.831),
    "Thika":   (-1.033, 37.069),
    "Ruiru":   (-1.157, 36.960),
}

# ---------------------------------------------------------------------------
# AQCountyMap  — bubble map showing per-county average AQ
# ---------------------------------------------------------------------------

class AQCountyMap:
    """
    Loads one CSV per county, computes the average concentration for the
    selected pollutant, then renders a Plotly bubble map with a dark theme.
    """

    def __init__(self, csv_files: list[str]):
        self._csv_files   = csv_files
        self._county_data: pd.DataFrame | None = None
        self._pollutant   = "P2"

    # ------------------------------------------------------------------
    def load_and_aggregate(self, pollutant: str = "P2") -> None:
        """Read every CSV, filter by *pollutant*, compute the mean."""
        self._pollutant = pollutant
        records: list[dict] = []

        for fp in self._csv_files:
            county = Path(fp).stem.split()[-1]   # "Apr 2026 Nairobi" → "Nairobi"
            if county not in COUNTY_COORDS:
                continue

            try:
                df = pd.read_csv(fp, sep=";", low_memory=False)
            except FileNotFoundError:
                continue

            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            sub = df[df["value_type"] == pollutant]["value"].dropna()
            if sub.empty:
                continue

            avg = float(sub.mean())
            records.append(
                dict(
                    county=county,
                    avg=avg,
                    lat=COUNTY_COORDS[county][0],
                    lon=COUNTY_COORDS[county][1],
                    n=len(sub),
                )
            )

        self._county_data = pd.DataFrame(records)

    # ------------------------------------------------------------------
    def plot_map(self) -> go.Figure:
        """Return a Plotly Figure with AQI-coloured bubbles per county."""
        df = self._county_data.copy()

        df["color"]     = df["avg"].apply(_aqi_color)
        df["aqi_label"] = df["avg"].apply(_aqi_label)

        # Scale bubble size: range ≈ [35, 70] px so small values stay visible
        lo, hi = df["avg"].min(), df["avg"].max()
        span   = max(hi - lo, 1)
        df["size"] = 35 + 35 * (df["avg"] - lo) / span

        hover = df.apply(
            lambda r: (
                f"<b>{r['county']}</b><br>"
                f"{self._pollutant}: {r['avg']:.1f} µg/m³<br>"
                f"AQI: {r['aqi_label']}<br>"
                f"Readings: {int(r['n']):,}"
            ),
            axis=1,
        )

        trace = go.Scattermap(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers+text",
            marker=dict(
                size=df["size"],
                color=df["color"],
                opacity=0.88,
                sizemode="diameter",
            ),
            text=df["avg"].apply(lambda x: f"{x:.0f}"),
            textposition="middle center",
            textfont=dict(color="white", size=13, family="Space Mono, monospace"),
            hovertext=hover,
            hoverinfo="text",
            name="",
        )

        # AQI legend as paper-space annotations (right side)
        annotations = [
            dict(
                x=1.01, y=1.0 - i * 0.06,
                xref="paper", yref="paper",
                text=f'<span style="color:{col};">■</span>  {lbl}',
                showarrow=False, align="left",
                font=dict(size=10, color="white"),
                xanchor="left",
            )
            for i, (_, col, lbl) in enumerate(_AQI_BANDS)
        ]

        pollutant_label = "PM₂.₅" if self._pollutant == "P2" else "PM₁₀"
        layout = go.Layout(
            title=dict(
                text=f"Kenya Average Air Quality by County — {pollutant_label} ({self._pollutant})",
                font=dict(color="white", size=17),
            ),
            paper_bgcolor=DARK_BG,
            plot_bgcolor=PANEL_BG,
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=-0.5, lon=37.0),
                zoom=5.2,
            ),
            margin=dict(l=0, r=230, t=60, b=0),
            height=680,
            annotations=annotations,
            font=dict(color="white", family="Space Mono, monospace"),
            hoverlabel=dict(
                bgcolor=PANEL_BG,
                bordercolor="#00f5ff",
                font_color="white",
                font_family="Space Mono, monospace",
            ),
        )

        return go.Figure(data=[trace], layout=layout)


# ---------------------------------------------------------------------------
# AQMapTrend  — original date-slider map (kept for reference)
# ---------------------------------------------------------------------------

class AQMapTrend:
    def __init__(self, filepath: str):
        self.__filepath   = filepath
        self.__aq_data    = None
        self.__daily_data = None
        self.__pollutant  = "P2"

    def load_and_format(self):
        self.__aq_data = pd.read_csv(self.__filepath, sep=";", low_memory=False)
        self.__aq_data["value"]     = pd.to_numeric(self.__aq_data["value"],     errors="coerce")
        self.__aq_data["lat"]       = pd.to_numeric(self.__aq_data["lat"],       errors="coerce")
        self.__aq_data["lon"]       = pd.to_numeric(self.__aq_data["lon"],       errors="coerce")
        self.__aq_data["timestamp"] = pd.to_datetime(
            self.__aq_data["timestamp"], format="ISO8601", utc=True
        )
        self.__aq_data["date"] = self.__aq_data["timestamp"].dt.date

    def aggregate(self, pollutant: str = "P2"):
        self.__pollutant = pollutant
        filtered = self.__aq_data[self.__aq_data["value_type"] == pollutant].copy()
        self.__daily_data = (
            filtered
            .groupby(["date", "sensor_id", "lat", "lon", "location"], as_index=False)["value"]
            .mean()
            .rename(columns={"value": "concentration"})
        )
        self.__daily_data["date_str"] = self.__daily_data["date"].astype(str)

    def plot_map(self, output_html: str | None = None) -> go.Figure:
        df    = self.__daily_data.copy()
        dates = sorted(df["date_str"].unique())

        df["color"]     = df["concentration"].apply(_aqi_color)
        df["aqi_label"] = df["concentration"].apply(_aqi_label)

        traces = []
        for date in dates:
            sub = df[df["date_str"] == date]
            traces.append(
                go.Scattermap(
                    lat=sub["lat"],
                    lon=sub["lon"],
                    mode="markers",
                    marker=dict(size=14, color=sub["color"], opacity=0.9),
                    text=sub.apply(
                        lambda r: (
                            f"<b>Sensor {r['sensor_id']}</b><br>"
                            f"Location: {r['location']}<br>"
                            f"{self.__pollutant}: {r['concentration']:.1f} µg/m³<br>"
                            f"AQI: {r['aqi_label']}"
                        ),
                        axis=1,
                    ),
                    hoverinfo="text",
                    name=date,
                    visible=False,
                )
            )

        traces[0].visible = True

        steps = [
            dict(
                method="update",
                args=[
                    {"visible": [i == idx for i in range(len(dates))]},
                    {"title": f"Nairobi Air Quality — {self.__pollutant} — {date}"},
                ],
                label=date,
            )
            for idx, date in enumerate(dates)
        ]

        sliders = [dict(
            active=0,
            currentvalue=dict(prefix="Date: ", visible=True, xanchor="center",
                              font=dict(color="#00f5ff", size=14)),
            pad=dict(t=55),
            steps=steps,
            bgcolor=PANEL_BG,
            bordercolor="#00f5ff",
            tickcolor="#aaaacc",
            font=dict(color="white", size=10),
        )]

        annotations = [
            dict(
                x=1.01, y=1.0 - idx * 0.048,
                xref="paper", yref="paper",
                text=f'<span style="color:{col};">■</span> {lbl}',
                showarrow=False, align="left",
                font=dict(size=11, color="white"),
                xanchor="left",
            )
            for idx, (_, col, lbl) in enumerate(_AQI_BANDS)
        ]

        layout = go.Layout(
            title=dict(
                text=f"Nairobi Air Quality — {self.__pollutant} — {dates[0]}",
                font=dict(color="white", size=17),
            ),
            paper_bgcolor=DARK_BG,
            plot_bgcolor=PANEL_BG,
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=-1.286, lon=36.817),
                zoom=10,
            ),
            sliders=sliders,
            margin=dict(l=0, r=220, t=60, b=0),
            height=700,
            annotations=annotations,
            font=dict(color="white"),
        )

        fig = go.Figure(data=traces, layout=layout)
        if output_html:
            fig.write_html(output_html)
        return fig