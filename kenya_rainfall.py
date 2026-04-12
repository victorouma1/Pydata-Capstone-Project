import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import geopandas as gpd


DARK_BG   = "#0d0d1a"
PANEL_BG  = "#12122a"
NEON_PINK = "#ff2d78"
NEON_CYAN = "#00f5ff"
GRID_COL  = "#1e1e3a"


class kenya_rain:
    def __init__(self, rain_data: dict, pcodes_csv: str = "P-CODES.csv",
                 geojson_path: str = "kenyan-counties.geojson"):
        self._rain_data   = rain_data
        self._pcodes_csv  = pcodes_csv
        self._geojson     = geojson_path

    # ------------------------------------------------------------------ #
    def format_rain_data(self):
        self.rain_df = pd.DataFrame(self._rain_data["result"]["records"])

        df_pcodes = pd.read_csv(self._pcodes_csv)
        df_pcodes["COUNTY CODE"] = df_pcodes["COUNTY CODE"].astype(str).str.zfill(3)
        county_mapping = df_pcodes.set_index("COUNTY CODE")["COUNTY NAME"].to_dict()

        self.rain_df["county_name"] = self.rain_df["PCODE"].str[2:5].map(county_mapping)
        self.rain_df["county_name"] = self.rain_df["county_name"].str.title()
        self.rain_df["date"]        = pd.to_datetime(self.rain_df["date"], format="ISO8601")
        self.rain_df.dropna(inplace=True)

        self.agg_data = self.rain_df.groupby("county_name")[["rfh"]].mean()

    def rain_trend_plot(self, county: str) -> plt.Figure:
        """Return a dark-themed line chart for *county*."""
        region = self.rain_df[self.rain_df["county_name"] == county]

        fig, ax = plt.subplots(figsize=(12, 5), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)

        sns.lineplot(data=region, x="date", y="rfh",
                     label="Actual Rainfall", color=NEON_CYAN, linewidth=2, ax=ax)
        sns.lineplot(data=region, x="date", y="rfh_avg",
                     label="Average Rainfall", color=NEON_PINK,
                     linewidth=1.6, linestyle="--", ax=ax)

        ax.set_title(f"Rainfall Trends — {county}",
                     color="white", fontsize=16, fontweight="bold", pad=12)
        ax.set_xlabel("Date", color="#aaaacc")
        ax.set_ylabel("10-day Rainfall (mm)", color="#aaaacc")
        ax.tick_params(colors="#aaaacc")
        ax.spines[:].set_color(GRID_COL)
        ax.grid(True, color=GRID_COL, linestyle="--", linewidth=0.6)
        ax.legend(framealpha=0.15, labelcolor="white",
                  facecolor=PANEL_BG, edgecolor=GRID_COL)

        fig.tight_layout()
        return fig

    def rain_bar_chart(self, top: bool = True) -> px.bar:
        """Return a Plotly bar chart for the top-5 or bottom-5 counties."""
        subset = (self.agg_data.nlargest(5, "rfh")
                  if top else self.agg_data.nsmallest(5, "rfh"))
        title  = ("Top 5 Counties by Rainfall" if top
                  else "Bottom 5 Counties by Rainfall")

        fig = px.bar(
            subset,
            x=subset.index,
            y="rfh",
            labels={"x": "County", "rfh": "10-day Rainfall (mm)"},
            title=title,
            color="rfh",
            color_continuous_scale=["#00f5ff", "#ff2d78"],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="#0d0d1a",
            plot_bgcolor="#12122a",
            font_color="white",
            title_font_size=16,
            coloraxis_showscale=False,
        )
        fig.update_traces(marker_line_color="#0d0d1a", marker_line_width=0.8)
        return fig

    def rain_map(self) -> px.choropleth_map:
        """Return a Plotly choropleth map of average rainfall by county."""
        ke_counties = gpd.read_file(self._geojson)

        fig = px.choropleth_map(
            self.agg_data,
            geojson=ke_counties,
            locations=self.agg_data.index,
            featureidkey="properties.COUNTY",
            color="rfh",
            range_color=(0, 20),
            color_continuous_scale=["#0d0d1a", "#00f5ff"],
            map_style="carto-darkmatter",
            zoom=5,
            center={"lat": -1.291, "lon": 36.8219},
            opacity=0.75,
            title="Average 10-day Rainfall by County (mm)",
        )
        fig.update_layout(
            paper_bgcolor="#0d0d1a",
            font_color="white",
            title_font_size=16,
            margin=dict(l=0, r=0, t=50, b=0),
            height=600,
        )
        return fig
