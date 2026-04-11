from openaq import OpenAQ
import json
import pandas as pd
import plotly.express as px

client = OpenAQ(api_key='f2341992e796fa02ab9f4776986c518e3985b1877fdbe547eaade6132f0bb790')

res = client.parameters.latest(parameters_id=2)
data_string = res.json()
data_string

world_aq_data = json.loads(data_string)
world_aq_data

world_aq_df = pd.json_normalize(world_aq_data['results'])
world_aq_df.dropna(inplace=True)
world_aq_df['datetime.utc'] = pd.to_datetime(world_aq_df['datetime.utc'], 
                                                     format="ISO8601", utc = True)
world_aq_df['datetime.local'] = pd.to_datetime(world_aq_df['datetime.local'], 
                                                      format="ISO8601", utc = True)
df_clean = world_aq_df[world_aq_df['value'] >= 0]

color_map = {
    "Good": "#00e400",
    "Moderate": "#ffff00",
    "Unhealthy for Sensitive Groups": "#ff7e00",
    "Unhealthy": "#ff0000",
    "Very Unhealthy": "#8f3f97",
    "Hazardous": "#7e0023"
}

fig = px.scatter_geo(
    df_clean,
    lat="coordinates.latitude",
    lon="coordinates.longitude",
    color="value",                 
    size="value",                  
    size_max=20,                   
    hover_name="locationsId",      
    hover_data=["value"],
    color_discrete_map=color_map,                                
    projection="natural earth",
    title="OpenAQ Air Quality Measurements"
)
fig.show()