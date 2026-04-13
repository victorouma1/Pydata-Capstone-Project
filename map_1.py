import time
import math
import requests
import folium
from folium import Popup, Marker, Icon
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 

TOKEN = "1b0fb24cf120a74cce4bf4dfe0b43428f8700f7f"  

# Africa bounding box
AFRICA_NORTH =  37.0  
AFRICA_SOUTH = -35.0   
AFRICA_WEST  = -18.0   
AFRICA_EAST  =  52.0   


TILE_DEGREES = 5

MAX_WORKERS  = 10  
RETRY_LIMIT  = 3    
RETRY_DELAY  = 2    

OUTPUT_FILE  = "africa_aqi_map.html"




def generate_africa_tiles(tile_deg: float) -> list[str]:
    """
    Divide Africa's bounding box into a regular grid.
    Returns a list of 'north,west,south,east' bounding-box strings.
    """
    tiles = []
    lat_steps = math.ceil((AFRICA_NORTH - AFRICA_SOUTH) / tile_deg)
    lon_steps = math.ceil((AFRICA_EAST  - AFRICA_WEST)  / tile_deg)

    for i in range(lat_steps):
        south = AFRICA_SOUTH + i * tile_deg
        north = min(south + tile_deg, AFRICA_NORTH)
        for j in range(lon_steps):
            west = AFRICA_WEST + j * tile_deg
            east = min(west + tile_deg, AFRICA_EAST)
            tiles.append(f"{north},{west},{south},{east}")

    return tiles



def fetch_stations_for_tile(bbox: str, retries: int = RETRY_LIMIT) -> list[dict]:
    """Fetch all AQI stations inside one bounding box tile, with retries."""
    url = f"https://api.waqi.info/v2/map/bounds/?latlng={bbox}&token={TOKEN}"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "ok":
                return data["data"]
            raise RuntimeError(data.get("data", "Unknown API error"))
        except (requests.RequestException, RuntimeError):
            if attempt == retries:
                return []
            time.sleep(RETRY_DELAY)
    return []


def fetch_all_stations(tile_deg: float = TILE_DEGREES) -> list[dict]:
    """
    Fetch stations for every Africa tile in parallel and de-duplicate by UID.
    Returns a flat, de-duplicated list of station dicts.
    """
    tiles = generate_africa_tiles(tile_deg)
    print(f"🌍 Africa grid: {len(tiles)} tiles ({tile_deg}° × {tile_deg}°), "
          f"{MAX_WORKERS} parallel workers\n")

    all_stations: dict[int, dict] = {}   # uid → station (auto de-duplication)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_stations_for_tile, tile): tile for tile in tiles}
        try:
            progress = tqdm(as_completed(futures), total=len(tiles), unit="tile")
        except NameError:
            progress = as_completed(futures)

        for future in progress:
            for station in future.result():
                uid = station.get("uid")
                if uid and uid not in all_stations:
                    all_stations[uid] = station

    print(f"\n✅ Collected {len(all_stations)} unique stations across Africa.")
    return list(all_stations.values())



AQI_SCALE = [
    (50,           "green",      "Good"),
    (100,          "lightgreen", "Moderate"),
    (150,          "orange",     "Unhealthy for Sensitive Groups"),
    (200,          "red",        "Unhealthy"),
    (300,          "purple",     "Very Unhealthy"),
    (float("inf"), "darkred",    "Hazardous"),
]


def aqi_colour(aqi) -> tuple[str, str]:
    try:
        v = int(aqi)
    except (TypeError, ValueError):
        return "gray", "Unknown"
    for threshold, colour, label in AQI_SCALE:
        if v <= threshold:
            return colour, label
    return "darkred", "Hazardous"



def build_popup(station: dict) -> str:
    name     = station.get("station", {}).get("name", "Unknown")
    aqi      = station.get("aqi", "N/A")
    colour, category = aqi_colour(aqi)
    ts       = station.get("station", {}).get("time", "")
    time_str = f"<small>Updated: {ts}</small><br>" if ts else ""

    return (
        f"<div style='font-family:sans-serif;min-width:180px'>"
        f"<b>{name}</b><br>"
        f"<span style='color:{colour}'><b>AQI: {aqi}</b> — {category}</span><br>"
        f"{time_str}"
        f"</div>"
    )


def build_africa_map(stations: list[dict]) -> folium.Map:
    """Render all stations onto a Folium map centred and fitted on Africa."""
    africa_map = folium.Map(
        location=[0, 20],          
        zoom_start=4,
        tiles="OpenStreetMap",
        prefer_canvas=True,       
    )

    africa_map.fit_bounds([
        [AFRICA_SOUTH, AFRICA_WEST],
        [AFRICA_NORTH, AFRICA_EAST],
    ])

    print(f"📍 Adding {len(stations)} markers to map…")
    for station in stations:
        lat = station.get("lat")
        lon = station.get("lon")
        aqi = station.get("aqi", -1)
        name = station.get("station", {}).get("name", "Unknown")

        if lat is None or lon is None:
            continue

        colour, category = aqi_colour(aqi)

        Marker(
            location=[lat, lon],
            popup=Popup(build_popup(station), max_width=250),
            tooltip=f"{name} | AQI: {aqi} ({category})",
            icon=Icon(color=colour, icon="cloud", prefix="fa"),
        ).add_to(africa_map)

    return africa_map

if __name__ == "__main__":
    print("=" * 55)
    print("  WAQI Africa AQI Map Builder")
    print("=" * 55)

    stations = fetch_all_stations(tile_deg=TILE_DEGREES)

    africa_map = build_africa_map(stations)

    africa_map.save(OUTPUT_FILE)
    print(f"\n🗺  Saved → '{OUTPUT_FILE}'  |  Open in any browser to explore.")