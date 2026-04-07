import aq_trends
import pandas as pd
from pathlib import Path

air_quality_data = pd.read_csv(r"C:\Users\victo\OneDrive\Documents\Combined CSV Files\combined_6_months_nairobi.csv",sep = ';', low_memory = False)

aq_df = aq_trends.aq_trend(air_quality_data)
aq_arrange = aq_df.arrange_format()
aq_sort = aq_df.sort_aq_index()
aq_group = aq_df.group_pollutant()
plot_1 = aq_df.plot_trend() 

