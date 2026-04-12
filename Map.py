import pandas as pd
import plotly.graph_objects as go


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

    @staticmethod
    def _aqi_color(val: float) -> str:
        if val <= 9:     return "#00e400"
        if val <= 35.4:  return "#ffff00"
        if val <= 55.4:  return "#ff7e00"
        if val <= 125.4: return "#ff0000"
        if val <= 225.4: return "#8f3f97"
        return "#7e0023"

    @staticmethod
    def _aqi_label(val: float) -> str:
        if val <= 9:     return "Good"
        if val <= 35.4:  return "Moderate"
        if val <= 55.4:  return "Unhealthy for Sensitive Groups"
        if val <= 125.4: return "Unhealthy"
        if val <= 225.4: return "Very Unhealthy"
        return "Hazardous"

    def plot_map(self, output_html: str | None = None) -> go.Figure:
        """
        Return a Plotly Figure with a date slider.
        Optionally also saves to *output_html* if a path is given.
        """
        df    = self.__daily_data.copy()
        dates = sorted(df["date_str"].unique())

        df["color"]     = df["concentration"].apply(self._aqi_color)
        df["aqi_label"] = df["concentration"].apply(self._aqi_label)

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
            bgcolor="#12122a",
            bordercolor="#00f5ff",
            tickcolor="#aaaacc",
            font=dict(color="white", size=10),
        )]

        aqi_legend = [
            ("#00e400", "Good  (0–9)"),
            ("#ffff00", "Moderate  (9–35)"),
            ("#ff7e00", "Unhealthy — Sensitive  (35–55)"),
            ("#ff0000", "Unhealthy  (55–125)"),
            ("#8f3f97", "Very Unhealthy  (125–225)"),
            ("#7e0023", "Hazardous  (225+)"),
        ]
        annotations = [
            dict(
                x=1.01, y=1.0 - idx * 0.048,
                xref="paper", yref="paper",
                text=f'<span style="color:{col};">■</span> {lbl}',
                showarrow=False, align="left",
                font=dict(size=11, color="white"),
                xanchor="left",
            )
            for idx, (col, lbl) in enumerate(aqi_legend)
        ]

        layout = go.Layout(
            title=dict(
                text=f"Nairobi Air Quality — {self.__pollutant} — {dates[0]}",
                font=dict(color="white", size=17),
            ),
            paper_bgcolor="#0d0d1a",
            plot_bgcolor="#12122a",
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


if __name__ == "__main__":
    import sys
    filepath  = sys.argv[1] if len(sys.argv) > 1 else "combined_6_months_nairobi.csv"
    pollutant = sys.argv[2] if len(sys.argv) > 2 else "P2"

    m = AQMapTrend(filepath)
    m.load_and_format()
    m.aggregate(pollutant=pollutant)
    m.plot_map(output_html="aq_map.html").show()
