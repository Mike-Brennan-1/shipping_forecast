import requests
from bs4 import BeautifulSoup
from datetime import datetime


url = "https://www.bbc.co.uk/weather/coast-and-sea/shipping-forecast"

response = requests.get(url)

sf_html = BeautifulSoup(response.content, "html.parser")


forecasts = []
regions = []
table = sf_html.find('div', attrs = {'id':"orb-modules"})

forecast_items = table.find_all("p", class_="wr-c-coastandsea-forecast__item__text")
for row in table.find_all("div", attrs = {"class" : "wr-c-coastandsea-region__region-title gs-u-mb+"}):
    regions.append(row.h3.text)

#Create list of dicts with forecast items

i = 0

for region in regions:
    forecast = {  
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Region": region,
            "Wind": forecast_items[i].text.strip(),
            "Sea State": forecast_items[i+1].text.strip(),
            "Weather": forecast_items[i+2].text.strip(),
            "Visibility" : forecast_items[i+3].text.strip()
        }
    forecasts.append(forecast)
    i = i+4

# Convert to Pd DataFrame

import pandas as pd
df = pd.DataFrame(forecasts)

#Remove punctuation
import string
df = df.apply(lambda x: x.astype(str).str.replace(f"[{string.punctuation}]", "", regex=True))

#Define function to get min/max wind readings and apply to new columns as int

def extract_min_max_wind(row):
    numbers = [int(x) for x in row if x.isnumeric()]  
    return pd.Series({"Wind min": min(numbers), "Wind max": max(numbers)})
    
df[["Wind min", "Wind max"]] = df["Wind"].apply(extract_min_max_wind).astype(int)

#Initialise new columns, set as False
df[["North", "East", "South", "West", "Northeast", "Southeast", "Southwest", "Northwest", "Calm", "Smooth", "Slight", "Moderate", "Rough", "Very rough", "High", "Very high", "Phenomenal", "Fair", "Showers", "Rain", "Drizzle", "Wintry Showers", "Thunderstorms", "Hail", "Sleet", "Snow", "Freezeing rain", "Fog", "Mist", "Very poor", "Poor", "Moderate", "Good"]] = False

#Populate wind direction
for index, text in df["Wind"].items():
    for col in df.columns[7:15]:
        if col.lower() in text.lower():
            df.at[index, col] = True


#Populate weather columns
for index, text in df["Weather"].items():
    for col in df.columns[24:34]:
        if col.lower() in text.lower():
            df.at[index, col] = True

# Populate sea state columns

for index, text in df["Sea State"].items():
    for col in df.columns[15:24]:
        if col.lower() in text.lower():
            df.at[index, col] = True

#Declare new Gale column, populate if max wind speed > 7

df["Gale"] = False

for index, number in df["Wind max"].items():
    if number > 7:
        df.at[index, "Gale"] = True

df.to_csv("sf.csv", mode="a", header=False, index=False)