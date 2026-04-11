import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import geopandas as gpd

class kenya_rain:
    def __init__(self,rain_data):
        self.__rain_data = rain_data
    def format_rain_data(self):
        self.rain_df = pd.DataFrame(self.__rain_data['result']['records'])
        df_pcodes = pd.read_csv('P-CODES.csv')

        df_pcodes['COUNTY CODE'] = df_pcodes['COUNTY CODE'].astype(str).str.zfill(3)
        county_mapping = df_pcodes.set_index('COUNTY CODE')['COUNTY NAME'].to_dict()

        self.rain_df['county_name'] = self.rain_df['PCODE'].str[2:5].map(county_mapping)
        self.rain_df['county_name'] = self.rain_df['county_name'].str.title()

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
        self.agg_data_1 = self.rain_df.groupby('county_name')[['rfh']].mean()
        rain_size = input('By rainfall amount would you like to see the:\n(a) top 5\n or\n (b) bottom 5: ').lower()
        top_5_rain = self.agg_data_1.nlargest(5, 'rfh')
        bottom_5_rain = self.agg_data_1.nsmallest(5, 'rfh')
        if rain_size == 'a':
            fig = px.bar(top_5_rain,x=top_5_rain.index, y = 'rfh', labels = {'x':'County Name','rfh':'10 day rainfall [mm]'})
            fig.show()
        if rain_size == 'b':
            fig = px.bar(bottom_5_rain,x = bottom_5_rain.index, y = 'rfh', labels = {'x':'County Name','rfh':'10 day rainfall [mm]'})
            fig.show()

    def rain_map(self):
        ke_counties = gpd.read_file("kenyan-counties.geojson")
        fig1 = px.choropleth_map(self.agg_data_1,geojson = ke_counties, locations = self.agg_data_1.index, 
                        featureidkey="properties.COUNTY",color="rfh", range_color = (0,20),
                        color_continuous_scale="Blues",map_style="carto-positron",zoom=3, 
                        center = {"lat": -1.291, "lon": 36.8219}, opacity=0.5)
        fig1.show()
