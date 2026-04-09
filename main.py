import aq_trends
import Map
import pandas as pd
from pathlib import Path

air_quality_data = pd.read_csv(r"C:\Users\victo\OneDrive\Documents\Combined CSV Files\combined_6_months_nakuru.csv",sep = ';', low_memory = False)

user_pollutant = input("Choose Pollutant: (1). P1\n(2). P2\n")

aq_df = aq_trends.aq_trend(air_quality_data, user_pollutant)
aq_arrange = aq_df.arrange_format()
aq_sort = aq_df.sort_aq_index()
aq_group = aq_df.group_pollutant()
plot_1 = aq_df.plot_trend() 

map = Map.AQMapTrend(r"C:\Users\victo\OneDrive\Documents\Combined CSV Files\combined_6_months_nairobi.csv")
map_lf = map.load_and_format()
map_ag = map.aggregate(user_pollutant)
map_plot = map.plot_map(output_html = 'map.html')
