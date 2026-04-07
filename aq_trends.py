import pandas as pd
import matplotlib.pyplot as plt

class aq_trend:
    def __init__(self, aq_data):
        self.__aq_data = aq_data
    def arrange_format(self):
        self.__aq_data['value'] = pd.to_numeric(self.__aq_data['value'], errors='coerce')
        self.__aq_data['timestamp'] = pd.to_datetime(self.__aq_data['timestamp'], format='ISO8601')
    def sort_aq_index(self):
        self.__aq_data.set_index('timestamp', inplace = True)
        self.__aq_data= self.__aq_data.sort_index()
    def group_pollutant(self):
        pollutant = input('Choose Pollutant: (1). P1\n(2). P2\n')
        grouped_aq_values = self.__aq_data.groupby('value_type').resample('D')[['value']].mean().groupby(level=0).rolling(window=3).mean()
        grouped_aq_values.dropna(inplace = True)
        self.p_df = grouped_aq_values.xs(pollutant, level=1)
        self.p_df = self.p_df.reset_index(level=0, drop=True)
    def plot_trend(self):
        aqi_levels = [
            ("Good", 0, 9, "#00e400"),
            ("Moderate", 9.1, 35.4, "#ffff00"),
            ("Unhealthy for Sensitive Groups", 35.5, 55.4, "#ff7e00"),
            ("Unhealthy", 55.5, 125.4, "#ff0000"),
            ("Very Unhealthy", 125.5, 225.4, "#8f3f97"),
            ("Hazardous", 225.5, 325.4, "#7e0023")
]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title('Air Quality (AQ) Trend')
        ax.set_ylabel('Concentration')
        for label, lo, hi, color in aqi_levels:
            ax.axhspan(lo, hi, facecolor=color, alpha=0.3, label=label)

        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self.p_df['value'].plot(ax = ax)
        plt.show()


        
