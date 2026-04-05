import pandas as pd
import matplotlib.pyplot as plt

class aq_trend:
    def __init__(self, aq_data):
        self.__aq_data = aq_data
    def sort_aq_index(self):
        self.__aq_data.timestamp = pd.to_datetime(self.__aq_data.timestamp, format='%d/%m/%Y %H:%M')
        self.__aq_data.set_index('timestamp', inplace = True)
        self.__aq_data= self.__aq_data.sort_index()
    def plot_trend(self):
        grouped_aq_values = self.__aq_data.groupby('value_type').resample('D')[['value']].mean().groupby(level=0).rolling(window=3).mean()
        grouped_aq_values.dropna(inplace = True)

        p2_df = grouped_aq_values.xs('P2', level=1)
        p2_df = p2_df.reset_index(level=0, drop=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title('Air Quality (AQ) Trend')
        ax.set_ylabel('AQ Value')

        p2_df['value'].plot(ax = ax)
        plt.show()


        
