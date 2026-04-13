"""
AQ & Rainfall Dashboard — Streamlit entry point
Run:  streamlit run main.py
"""

import streamlit as st
import pandas as pd
import requests

import aq_trends as aqt
import kenya_rainfall as kr
import Map

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
/* AFTER */
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
        ["Nairobi AQ Map", "AQ Trends", "Kenya Rainfall"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    st.markdown("**Settings**")
    pollutant = st.selectbox("Pollutant", ["P1", "P2"], index=1,
                             help="P1 = PM₁₀  |  P2 = PM₂.₅")

    st.markdown("---")
    st.markdown("**Data Source**")
    csv_county = st.text_input(
        "County name", value="nairobi",
        help="e.g. nairobi, meru, kisumu"
    ).strip().lower().replace(" ", "_")
    csv_duration = st.radio("Duration", ["6 months", "Years"], horizontal=True)
    if csv_duration == "6 months":
        aq_csv = f"combined_6_months_{csv_county}.csv"
    else:
        csv_years = st.number_input("Number of years", min_value=1, max_value=20, value=1, step=1)
        aq_csv = f"combined_{csv_years}_year_{csv_county}.csv"
    st.caption(f"`{aq_csv}`")



@st.cache_data(show_spinner=False)
def load_aq_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", low_memory=False)


if page == "Nairobi AQ Map":
    st.title("Nairobi Air Quality Map")
    st.markdown("Sensor readings across Nairobi with a **date slider** to scrub through time.")
    st.markdown("---")

    col_load, _ = st.columns([1, 3])
    with col_load:
        run_map = st.button("Load / Refresh Map")

    if run_map or st.session_state.get("map_fig") is not None:
        with st.spinner("Crunching sensor data …"):
            try:
                df = load_aq_csv(aq_csv)
                aq_map_obj = Map.AQMapTrend(aq_csv)
                aq_map_obj.load_and_format()
                aq_map_obj.aggregate(pollutant=pollutant)
                fig = aq_map_obj.plot_map()          # returns go.Figure
                st.session_state["map_fig"] = fig
            except FileNotFoundError:
                st.error(f"CSV not found: `{aq_csv}`. Update the path in the sidebar.")
                st.stop()

    if "map_fig" in st.session_state:
        st.plotly_chart(
            st.session_state["map_fig"],
            use_container_width=True,
            config={"scrollZoom": True},
        )

    # AQI reference card
    with st.expander("AQI Reference", expanded=False):
        aqi_data = {
            "Category":      ["Good", "Moderate", "Unhealthy — Sensitive", "Unhealthy", "Very Unhealthy", "Hazardous"],
            "PM₂.₅ (µg/m³)":["0 – 9", "9.1 – 35.4", "35.5 – 55.4", "55.5 – 125.4", "125.5 – 225.4", "225.5 – 325.4"],
            "Colour":        ["🟢", "🟡", "🟠", "🔴", "🟣", "⬛"],
        }
        st.table(pd.DataFrame(aqi_data))


elif page == "AQ Trends":
    st.title("Air Quality Trends")
    st.markdown("3-day rolling average overlaid on AQI colour bands.")
    st.markdown("---")

    run_trend = st.button("Plot Trend")

    if run_trend:
        with st.spinner("Processing …"):
            try:
                df = load_aq_csv(aq_csv)
                trend = aqt.aq_trend(df, pollutant)
                trend.arrange_format()
                trend.sort_aq_index()
                trend.group_pollutant()
                fig = trend.plot_trend()
                st.pyplot(fig, use_container_width=True)
                st.markdown("""
> **Generally speaking,** daily air quality in Nairobi typically fluctuates between good and moderate levels.
>
> **Main cause of pollution:** A large number of vehicles, including cars, motorbikes and trucks, many of which are older and produce far more pollution than their newer counterparts would.
>
> **Way to improve pollution level:** The introduction of fines and charges to both vehicles and factories that exceed dangerous levels of pollutive output, with the eventual replacement of these vehicles with cleaner ones to reducing the amounts of haze, smog, fumes and smoke permeating the air in Nairobi.
""")
                # Quick stats
                st.markdown("---")
                st.markdown("### Quick Stats")
                c1, c2, c3, c4 = st.columns(4)
                series = trend.p_df["value"]
                c1.metric("Mean",    f"{series.mean():.1f} µg/m³")
                c2.metric("Max",     f"{series.max():.1f} µg/m³")
                c3.metric("Min",     f"{series.min():.1f} µg/m³")
                #c4.metric("Std Dev", f"{series.std():.1f} µg/m³")

            except FileNotFoundError:
                st.error(f"CSV not found: `{aq_csv}`.")
            except KeyError:
                st.error(f"Pollutant `{pollutant}` not found in the dataset. "
                         "Check the pollutant selector in the sidebar.")


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
> The Short Rains (October to December): These appear as the secondary, slightly lower peaks on the graph.
""")

    with tab_bar:
        direction = st.radio("Show", ["Top 5", "Bottom 5"], horizontal=True, key="rain_dir")
        if st.button("Plot Bar Chart", key="btn_rain_bar"):
            fig = rain.rain_bar_chart(top=(direction == "Top 5"))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
> The top 5 rainfall counties in Kenya are all located in the western highlands region
>                      
> While the bottom five rainfall counties are all located in northern Kenya's arid and semi-arid regions
""")

    with tab_map:
        if st.button("Show Choropleth Map", key="btn_rain_map"):
            try:
                fig = rain.rain_map()
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("""
> Western Kenya — Indicating the highest rainfall in the country, Consistent with the influence of Lake Victoria and equatorial weather systems.
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


