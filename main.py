import streamlit as st
import pandas as pd
import requests

import aq_trends as aqt
import kenya_rainfall as kr
import Map
import urbanisation as urb

st.set_page_config(
    page_title="AQ & Rainfall Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&display=swap');

/* ── Root palette ── */
:root {
    --bg:         #0d0d1a;
    --panel:      #12122a;
    --border:     #1e1e3a;
    --neon-cyan:  #00f5ff;
    --neon-pink:  #ff2d78;
    --neon-green: #00e400;
    --text-main:  #e8e8ff;
    --text-muted: #7a7aaa;
}

/* ── App background ── */
.stApp { background-color: var(--bg); color: var(--text-main); }
[data-testid="stSidebar"] { background-color: var(--panel); border-right: 1px solid var(--border); }

/* ── Heading fonts ── */
h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    letter-spacing: 0.05em;
}
h1 { color: var(--neon-cyan) !important; text-shadow: 0 0 18px rgba(0,245,255,.45); }
h2 { color: var(--neon-pink) !important; text-shadow: 0 0 12px rgba(255,45,120,.35); }
h3 { color: var(--text-main) !important; }

/* ── Body / labels ── */
body, p, label, div { font-family: 'Space Mono', monospace; }
label, .stTextInput label, .stSelectbox label { color: var(--text-main) !important; font-size: 0.8rem; }
[data-testid="stSidebar"] label { color: var(--text-main) !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div { color: var(--text-muted); }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] strong { color: var(--neon-cyan) !important; }
.stMarkdown p { color: var(--text-muted); }

/* ── Sidebar radio buttons ── */
[data-testid="stSidebarNav"] { font-family: 'Space Mono', monospace; }
.stRadio label { color: var(--text-main) !important; font-size: 0.85rem; }
.stRadio [data-checked="true"] > div:first-child {
    background: var(--neon-cyan) !important;
    box-shadow: 0 0 10px var(--neon-cyan);
}

/* ── Selectbox / dropdown ── */
.stSelectbox > div > div {
    background-color: var(--panel) !important;
    border: 1px solid var(--neon-cyan) !important;
    color: var(--text-main) !important;
    font-family: 'Space Mono', monospace;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent;
    border: 1px solid var(--neon-cyan);
    color: var(--neon-cyan);
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    padding: 0.45rem 1.1rem;
    border-radius: 4px;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: var(--neon-cyan);
    color: var(--bg);
    box-shadow: 0 0 14px var(--neon-cyan);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--panel);
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    color: var(--neon-cyan) !important;
    border-bottom: 2px solid var(--neon-cyan) !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
}
[data-testid="stMetricValue"] {
    color: var(--neon-cyan) !important;
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.75rem; }

/* ── Divider ── */
hr { border-color: var(--border); }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--neon-cyan) !important; }

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background: var(--panel) !important;
    border: 1px dashed var(--neon-cyan) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--neon-cyan); }
</style>
""", unsafe_allow_html=True)


TREND_CSV = "combined_6_months_nairobi.csv"

COUNTY_CSV_FILES = [
    "Sep 2019 Kisumu.csv",
    "Oct 2024 Meru.csv",
    "Apr 2026 Nairobi.csv",
    "Apr 2026 Nakuru.csv",
    "Mar 2025 Kiambu.csv",
    "Jan 2021 Thika.csv",
    "Mar 2023 Ruiru.csv",
]

L1_TIF = "KEN_DUG_2026_GRID_L1_R2025A_v1.tif"
L2_TIF = "KEN_DUG_2026_GRID_L2_R2025A_v1.tif"

with st.sidebar:
    st.markdown(
        "<h2 style='text-align:center;margin-bottom:0.2rem;'>AQ DASH</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#7a7aaa;font-size:0.72rem;"
        "margin-top:0;margin-bottom:1.5rem;'>Air Quality & Rainfall</p>",
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["Overview", "Kenya AQ Map", "AQ Trends", "Urbanisation", "Kenya Rainfall", "Recommendations", "References"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    st.markdown("**Settings**")
    pollutant = st.selectbox("Pollutant", ["P1", "P2"], index=1,
                             help="P1 = PM₁₀  |  P2 = PM₂.₅")

@st.cache_data(show_spinner=False)
def load_aq_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", low_memory=False)

if page == "Overview":
    st.title("AQ & Rainfall Dashboard")
    st.markdown("##### Air Quality & Climate Intelligence for Kenya")
    st.markdown("---")

    st.markdown("## Problem Statement")
    st.markdown("""
According to the Clean Air Fund's 2020 *State of the Global Air* report, more than **5,000 premature deaths** 
in Nairobi are linked to air pollution-related illnesses. Additionally, over **two million people** across Kenya 
faced worsened food insecurity following one of the driest October–December 2025 rainy seasons on record.
""")

    st.markdown("---")
    st.markdown("## Research Questions")

    questions = [
        ("🗺️", "Does geographical location play a part in air quality?"),
        ("👥", "Is there a correlation between population and pollution?"),
        ("📈", "How has air quality changed over time in Nairobi?"),
        ("🌧️", "How does rainfall vary across counties over time?"),
        ("⚠️", "Which counties are most vulnerable or beneficial to climate extremes?"),
    ]
    for icon, q in questions:
        st.markdown(
            f"""
<div style="background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--neon-cyan);
border-radius:6px;padding:0.75rem 1rem;margin-bottom:0.6rem;font-family:'Space Mono',monospace;
color:var(--text-main);font-size:0.85rem;">{icon}&nbsp;&nbsp;{q}</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("## Data Sources")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
<div style="background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:1.2rem;height:100%;">
<h3 style="color:var(--neon-cyan)!important;font-size:0.9rem;margin-bottom:0.5rem;">📡 Sensors Africa</h3>
<p style="color:var(--text-muted);font-size:0.8rem;margin:0;">Air quality sensor readings used for PM&#x2081;&#x2080; and PM&#x2082;.&#x2085;
concentration data across Kenyan counties.</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
<div style="background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:1.2rem;height:100%;">
<h3 style="color:var(--neon-pink)!important;font-size:0.9rem;margin-bottom:0.5rem;">🌧️ Humdata (OCHA)</h3>
<p style="color:var(--text-muted);font-size:0.8rem;margin:0;">County-level rainfall records sourced from the
UN OCHA Humanitarian Data Exchange platform.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<p style='color:var(--text-muted);font-size:0.78rem;text-align:center;'>"
        "Use the sidebar to navigate between sections of the dashboard.</p>",
        unsafe_allow_html=True,
    )

elif page == "Kenya AQ Map":
    pollutant_label = "PM₂.₅" if pollutant == "P2" else "PM₁₀"
    st.title("Kenya Air Quality Map")
    st.markdown(
        f"Average **{pollutant_label}** concentration per county from sensor CSV data."
    )
    st.markdown("---")

    col_load, _ = st.columns([1, 3])
    with col_load:
        run_map = st.button("Load / Refresh Map")

    # Re-render whenever the button is pressed OR the pollutant changes
    cache_key = f"county_map_{pollutant}"
    if run_map or st.session_state.get("county_map_pollutant") != pollutant:
        with st.spinner("Aggregating county sensor data …"):
            try:
                county_map = Map.AQCountyMap(COUNTY_CSV_FILES)
                county_map.load_and_aggregate(pollutant=pollutant)
                fig = county_map.plot_map()
                st.session_state["county_map_fig"]      = fig
                st.session_state["county_map_pollutant"] = pollutant
            except Exception as e:
                st.error(f"Error building map: {e}")
                st.stop()

    if "county_map_fig" in st.session_state:
        st.plotly_chart(
            st.session_state["county_map_fig"],
            use_container_width=True,
            config={"scrollZoom": True},
        )

    with st.expander("AQI Reference", expanded=False):
        aqi_data = {
            "Category":       ["Good", "Moderate", "Unhealthy — Sensitive",
                               "Unhealthy", "Very Unhealthy", "Hazardous"],
            "PM₂.₅ (µg/m³)": ["0 – 9", "9.1 – 35.4", "35.5 – 55.4",
                               "55.5 – 125.4", "125.5 – 225.4", "225.5 – 325.4"],
            "Colour":         ["🟢", "🟡", "🟠", "🔴", "🟣", "⬛"],
        }
        st.table(pd.DataFrame(aqi_data))

elif page == "AQ Trends":
    pollutant_label = "PM₂.₅" if pollutant == "P2" else "PM₁₀"
    st.title("Air Quality Trends")
    st.markdown(
        f"3-day rolling average for **{pollutant_label}** overlaid on AQI colour bands — Nairobi."
    )
    st.markdown("---")

    run_trend = st.button("Plot Trend")

    if run_trend:
        with st.spinner("Processing …"):
            try:
                df = load_aq_csv(TREND_CSV)
                trend = aqt.aq_trend(df, pollutant)
                trend.arrange_format()
                trend.sort_aq_index()
                trend.group_pollutant()
                fig = trend.plot_trend()
                st.pyplot(fig, use_container_width=True)
                st.markdown("""
> **Generally speaking,** daily air quality in Nairobi typically fluctuates between good and moderate levels.
>
> The main source of Nairobi's PM2.5 concentrations is road transport (40%). This is primarily due to the presence of a large and aged vehicle fleet, inadequate road networks, and poorly enforced vehicle emission standards. Despite accounting for only about 9 percent of the population, the city hosts over a third of the country's about 3m vehicle fleet.[1]
>
> **Way to improve pollution level:** The introduction of fines and charges to both vehicles and factories that exceed dangerous levels of pollutive output, with the eventual replacement of these vehicles with cleaner ones to reducing the amounts of haze, smog, fumes and smoke permeating the air in Nairobi.
>
[1] Clean Air Fund - Nairobi and air pollution
""")

                st.markdown("---")
                st.markdown("### Quick Stats")
                c1, c2, c3, c4 = st.columns(4)
                series = trend.p_df["value"]
                c1.metric("Mean", f"{series.mean():.1f} µg/m³")
                c2.metric("Max",  f"{series.max():.1f} µg/m³")
                c3.metric("Min",  f"{series.min():.1f} µg/m³")

            except FileNotFoundError:
                st.error(f"CSV not found: `{TREND_CSV}`. Ensure it is in the working directory.")
            except KeyError:
                st.error(
                    f"Pollutant `{pollutant}` not found in the dataset. "
                    "Check the pollutant selector in the sidebar."
                )

elif page == "Kenya Rainfall":
    st.title("Kenya Rainfall Dashboard")
    st.markdown("County-level rainfall data sourced from OCHA/Humdata.")
    st.markdown("---")

    @st.cache_data(show_spinner=False)
    def fetch_rainfall() -> dict:
        url = "https://data.humdata.org/api/3/action/datastore_search"
        params = {"resource_id": "d76caa45-276c-4d6c-acd5-ce49d6c0f27d", "limit": 12500}
        headers = {
            "Authorization": (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                ".eyJqdGkiOiJicmk2Q0hKRW5nemFvU2RuQkdNakpjREZ2YlROZTRLRVVsSTVHWk9QeWZvIiwiaWF0IjoxNzc1NzE2OTQ5LCJleHAiOjE3NzgzMDg5NDl9"
                ".5dS9n612QxkEs_oqLfo4GGRZmWiveUQysqx99WDaLHU"
            )
        }
        r = requests.get(url, headers=headers, params=params, timeout=30)
        return r.json()

    with st.spinner("Fetching rainfall data …"):
        try:
            rain_data = fetch_rainfall()
            rain = kr.kenya_rain(rain_data)
            rain.format_rain_data()
        except Exception as e:
            st.error(f"Could not load rainfall data: {e}")
            st.stop()

    county_list = sorted(rain.rain_df["county_name"].dropna().unique())

    tab_trend, tab_bar, tab_map = st.tabs(["County Trend", "Bar Chart", "Choropleth Map"])

    with tab_trend:
        selected_county = st.selectbox("Select County", county_list, key="county_sel")
        if st.button("Plot Trend", key="btn_rain_trend"):
            fig = rain.rain_trend_plot(county=selected_county)
            st.pyplot(fig, use_container_width=True)
            st.markdown("""
> The Long Rains (March to May): These are usually the highest peaks in a normal year.
>
> The Short Rains (October to December): These appear as the secondary, slightly lower peaks on the graph. [2]
>
> [2] Kenya Meteorological Society - CLIMATE OUTLOOK FOR THE "LONG RAINS" (MARCH-MAY) 2026 SEASON AND REVIEW OF THE OCTOBER-DECEMBER 2025 "SHORT RAINS" SEASON
""")

    with tab_bar:
        direction = st.radio("Show", ["Top 5", "Bottom 5"], horizontal=True, key="rain_dir")
        if st.button("Plot Bar Chart", key="btn_rain_bar"):
            fig = rain.rain_bar_chart(top=(direction == "Top 5"))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
> The top 5 rainfall counties in Kenya are all located in the western highlands region [3]
>
> While the bottom five rainfall counties are all located in northern Kenya's arid and semi-arid regions [4]
>
> [4] IUCN - Kenya (ASAL)
""")

    with tab_map:
        if st.button("Show Choropleth Map", key="btn_rain_map"):
            try:
                fig = rain.rain_map()
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("""
> Western Kenya — Indicating the highest rainfall in the country, consistent with the influence of Lake Victoria and equatorial weather systems.
>
> Southern & Coastal Kenya (near Mombasa) — Reflecting high rainfall typical of the coastal strip influenced by the Indian Ocean monsoon.
>
> Central Kenya — Suggesting moderate rainfall which is consistent with the highland climate.
>
> Northern & Eastern Kenya — Darker teal shades indicating lower rainfall consistent with the arid and semi-arid lands (ASAL) that dominate this region.
>
> Black patches — Represents missing data.
""")
            except Exception as e:
                st.error(f"Map error: {e}. Ensure `kenyan-counties.geojson` is present.")



elif page == "Urbanisation":
    pollutant_label = "PM₂.₅" if pollutant == "P2" else "PM₁₀"
    st.title("Urbanisation & Air Pollution")
    st.markdown(
        f"Visualises how the **degree of urbanisation** (GHS-DUG DEGURBA 2026) "
        f"relates to **{pollutant_label}** concentrations across Kenya."
    )
    st.markdown("---")

    col_run, _ = st.columns([1, 3])
    with col_run:
        run_urb = st.button("Generate Figure")

    if run_urb or st.session_state.get("urb_pollutant") != pollutant:
        with st.spinner("Loading grids and computing statistics …"):
            try:
                urb_obj = urb.UrbanisationPollution(
                    l1_tif=L1_TIF,
                    l2_tif=L2_TIF,
                    county_csvs=COUNTY_CSV_FILES,
                )
                urb_obj.load_grids()
                urb_obj.load_aq_data()
                fig = urb_obj.make_figure(pollutant=pollutant)
                st.session_state["urb_fig"]      = fig
                st.session_state["urb_pollutant"] = pollutant
            except FileNotFoundError as e:
                st.error(
                    f"Raster file not found: {e}. "
                    "Ensure the GeoTIFF files are in the working directory."
                )
                st.stop()
            except Exception as e:
                st.error(f"Error generating figure: {e}")
                st.stop()

    if "urb_fig" in st.session_state:
        st.pyplot(st.session_state["urb_fig"], use_container_width=True)
        st.markdown("---")

        st.markdown("""
> **Rural areas** show the lowest pollution levels, reflecting limited traffic and industrial activity.
>
> **Towns and suburbs** exhibit moderate concentrations driven by growing vehicle fleets and localised industry.
>
> **Cities** (primarily Nairobi) record the highest values — often exceeding WHO 24-hour guidelines for both PM₂.₅ (15 µg/m³) and PM₁₀ (45 µg/m³).
>
> The uplift annotations on the gradient chart quantify the PM₂.₅ increase between each urbanisation tier.
>
> [5] GHS-DUG DEGURBA R2025A v1 — European Commission Joint Research Centre / WorldPop
""")

        with st.expander("Urbanisation Class Reference", expanded=False):
            cls_data = {
                "Level": ["L1", "L1", "L1",
                          "L2", "L2", "L2", "L2", "L2", "L2", "L2", "L2"],
                "Code":  [1, 2, 3, 10, 11, 12, 13, 21, 22, 23, 30],
                "Label": [
                    "Rural", "Town / Suburb", "City",
                    "Very Sparse Rural", "Low Density Rural", "Rural Cluster",
                    "Peri-urban / Suburb", "Semi-dense Urban", "Dense Urban",
                    "Urban Centre", "Major City Core",
                ],
            }
            st.table(pd.DataFrame(cls_data))
elif page == "Recommendations":
    st.title("Recommendations")
    st.markdown("Policy and intervention recommendations derived from the dashboard findings.")
    st.markdown("---")

    st.markdown("## Air Quality")

    def rec_card(title, body, accent="var(--neon-cyan)"):
        st.markdown(
            f"""
<div style="background:var(--panel);border:1px solid var(--border);border-left:4px solid {accent};
border-radius:8px;padding:1.1rem 1.3rem;margin-bottom:1rem;">
<p style="color:{accent};font-family:'Orbitron',monospace;font-size:0.8rem;
letter-spacing:0.06em;margin:0 0 0.5rem 0;">{title}</p>
<p style="color:var(--text-muted);font-family:'Space Mono',monospace;font-size:0.82rem;
line-height:1.6;margin:0;">{body}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    rec_card(
        "DECENTRALISE ENVIRONMENTAL MONITORING",
        "Most Green City initiatives focus on Nairobi. However, the data shows Ruiru and Thika are the "
        "real hotspots. Capitalise on this by shifting policy focus toward industrial regulation in these "
        "satellite manufacturing hubs.",
        "var(--neon-cyan)",
    )

    rec_card(
        "TARGETED INDUSTRIAL FILTERING",
        "Since Thika and Ruiru are industrial corridors, the high PM10 is likely due to manufacturing "
        "and construction dust. Implementing stricter scrubber requirements for factories in these specific "
        "zones would yield the highest return on intervention.",
        "var(--neon-cyan)",
    )

    st.markdown("---")
    st.markdown("## Rainfall")

    rec_card(
        "HIGH-RAINFALL AREAS — COLD-CHAIN & DRAINAGE",
        "For areas with high rainfall, capitalise on high yields by investing in cold-chain storage to "
        "prevent post-harvest loss during heavy rains. Focus on drainage infrastructure to prevent the "
        "landslides common in hilly terrains.",
        "var(--neon-pink)",
    )

    rec_card(
        "LOW-RAINFALL AREAS — SOLAR & DROUGHT-RESISTANT CROPS",
        "Low-rainfall areas are likely high in solar radiation. Capitalise on the lack of rain by deploying "
        "solar-powered boreholes and shifting toward drought-resistant fodder for livestock.",
        "var(--neon-pink)",
    )

elif page == "References":
    st.title("References")
    st.markdown("Sources and citations used throughout this dashboard.")
    st.markdown("---")

    references = [
        ("[1]", "Clean Air Fund", "Nairobi and Air Pollution — State of the Global Air 2020.", "https://www.cleanairfund.org"),
        ("[2]", "Kenya Meteorological Society", "Climate Outlook for the Long Rains (March-May) 2026 Season and Review of the October-December 2025 Short Rains Season.", "https://www.meteo.go.ke"),
        ("[3]", "OCHA / Humdata", "Kenya County-Level Rainfall Dataset. Humanitarian Data Exchange.", "https://data.humdata.org"),
        ("[4]", "IUCN", "Kenya Arid and Semi-Arid Lands (ASAL) — Environmental Profile.", "https://www.iucn.org"),
        ("[5]", "European Commission JRC / WorldPop", "GHS-DUG DEGURBA 2026 Grid R2025A v1 — Global Human Settlement Degree of Urbanisation.", "https://ghsl.jrc.ec.europa.eu"),
        ("[6]", "Sensors Africa", "Open air quality sensor network data for Kenya.", "https://sensors.africa")
    ]

    for num, source, title, url in references:
        st.markdown(
            f"""
<div style="background:var(--panel);border:1px solid var(--border);border-radius:6px;
padding:0.85rem 1.1rem;margin-bottom:0.7rem;display:flex;gap:1rem;align-items:flex-start;">
<span style="color:var(--neon-cyan);font-family:'Orbitron',monospace;font-size:0.78rem;
min-width:2.5rem;padding-top:2px;">{num}</span>
<div>
<p style="color:var(--text-main);font-family:'Space Mono',monospace;font-size:0.82rem;
margin:0 0 0.2rem 0;"><strong>{source}</strong> — {title}</p>
<a href="{url}" target="_blank" style="color:var(--text-muted);font-size:0.75rem;
font-family:'Space Mono',monospace;text-decoration:none;">{url}</a>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<p style='color:var(--text-muted);font-size:0.75rem;text-align:center;'>"
        "Placeholder references [7] and [8] are to be replaced with your actual citations.</p>",
        unsafe_allow_html=True,
    )