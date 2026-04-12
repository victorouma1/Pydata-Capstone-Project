from openaq import OpenAQ
import json
import pandas as pd
import plotly.express as px


class air_q_map:
    def __init__(self, api_key: str):
        self.__client = OpenAQ(api_key=api_key)

    def format_data(self):
        res = self.__client.parameters.latest(parameters_id=2)
        world_aq_data = json.loads(res.json())
        world_aq_df = pd.json_normalize(world_aq_data["results"])

        world_aq_df["datetime.utc"]   = pd.to_datetime(world_aq_df["datetime.utc"],   format="ISO8601", utc=True)
        world_aq_df["datetime.local"] = pd.to_datetime(world_aq_df["datetime.local"], format="ISO8601", utc=True)
        self.df_clean = world_aq_df[world_aq_df["value"] >= 0]

    def plot_map(self) -> px.scatter_geo:
        """Return a dark-themed Plotly world scatter-geo figure."""
        fig = px.scatter_geo(
            self.df_clean,
            lat="coordinates.latitude",
            lon="coordinates.longitude",
            color="value",
            size="value",
            size_max=22,
            hover_name="locationsId",
            hover_data=["value"],
            projection="natural earth",
            title="OpenAQ — Global Air Quality (PM₂.₅)",
            color_continuous_scale=["#00e400", "#ffff00", "#ff7e00",
                                    "#ff0000", "#8f3f97", "#7e0023"],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="#0d0d1a",
            geo=dict(
                bgcolor="#12122a",
                showland=True,  landcolor="#1a1a2e",
                showocean=True, oceancolor="#0d0d1a",
                showcoastlines=True, coastlinecolor="#2a2a4a",
                showframe=False,
            ),
            font_color="white",
            title_font_size=16,
            coloraxis_colorbar=dict(title="PM₂.₅ (µg/m³)", tickfont=dict(color="white")),
            margin=dict(l=0, r=0, t=50, b=0),
            height=600,
        )
        return fig
