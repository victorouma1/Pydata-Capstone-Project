import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

class kenya_rain:
    def __init__(self,rain_data):
        self.__rain_data = rain_data
    def format_rain_data(self):
        self.rain_df = pd.DataFrame(self.__rain_data['result']['records'])
        pcode_to_county = {
            "KE019": "Nyeri",
            "KE004": "Mombasa",
            "KE010": "Marsabit",
            "KE047": "Nairobi",
            "KE008": "Wajir",
            "KE043": "Homa Bay",
            "KE023": "Turkana",
            "KE037": "Lugari"
        }
        self.rain_df['county_name'] = self.rain_df['PCODE'].map(pcode_to_county)
        self.rain_df.date = pd.to_datetime(self.rain_df.date, format="ISO8601")
        self.rain_df.dropna(inplace = True)
    def rain_trend_plot(self):
        user_county = input('Enter a county: ').title()
        region_data = self.rain_df[self.rain_df['county_name'] == user_county]
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=region_data, x='date', y='rfh', label='Actual Rainfall')
        sns.lineplot(data=region_data, x='date', y='rfh_avg', label='Average Rainfall', linestyle='--')
        plt.title(f'Rainfall Trends for {user_county}')
        plt.show()
    def rain_bar_chart(self):
        agg_data_1 = self.rain_df.groupby('county_name')[['rfh']].mean()
        fig = px.bar(agg_data_1,x=agg_data_1.index, y = 'rfh', labels = {'x':'County Name','rfh':'10 day rainfall [mm]'})
        fig.show()