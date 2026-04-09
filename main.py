import aq_trends
import Map
import kenya_rainfall
import pandas as pd
from pathlib import Path
import requests

air_quality_data = pd.read_csv(r"C:\Users\victo\OneDrive\Documents\Combined CSV Files\combined_6_months_nakuru.csv",sep = ';', low_memory = False)

url = "https://data.humdata.org/api/3/action/datastore_search"

params = {
"resource_id": "d76caa45-276c-4d6c-acd5-ce49d6c0f27d",
"limit": 12500
}

headers = {
"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJicmk2Q0hKRW5nemFvU2RuQkdNakpjREZ2YlROZTRLRVVsSTVHWk9QeWZvIiwiaWF0IjoxNzc1NzE2OTQ5LCJleHAiOjE3NzgzMDg5NDl9.5dS9n612QxkEs_oqLfo4GGRZmWiveUQysqx99WDaLHU"
}

response = requests.get(url, headers=headers, params=params)
rain_data = response.json()

user_pollutant = input("Choose Pollutant: (1). P1\n(2). P2\n")

aq_df = aq_trends.aq_trend(air_quality_data, user_pollutant)
aq_arrange = aq_df.arrange_format()
aq_sort = aq_df.sort_aq_index()
aq_group = aq_df.group_pollutant()
plot_1 = aq_df.plot_trend() 

kenya_rain = kenya_rainfall.kenya_rain(rain_data)
kenya_format = kenya_rain.format_rain_data()
kenya_plot = kenya_rain.rain_trend_plot()
kenya_bar = kenya_rain.rain_bar_chart()

map = Map.AQMapTrend(r"C:\Users\victo\OneDrive\Documents\Combined CSV Files\combined_6_months_nairobi.csv")
map_lf = map.load_and_format()
map_ag = map.aggregate(user_pollutant)
map_plot = map.plot_map(output_html = 'map.html')

