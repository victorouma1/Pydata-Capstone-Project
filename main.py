import aq_trends
import pandas as pd

air_quality_data = pd.read_csv("Combined data (Nov 2025-Apr 2026).csv")

aq_df = aq_trends.aq_trend(air_quality_data)
aq_sort = aq_df.sort_aq_index()

plot_1 = aq_df.plot_trend() 

