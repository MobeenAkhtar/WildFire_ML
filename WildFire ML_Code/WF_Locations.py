import requests
from pathlib import Path
import json
import pandas as pd
import random

from datetime import datetime
import ee
import geemap

try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InFORM_FireOccurrence_Public/FeatureServer/0/query"


parameter_req = {
                "where": "POOState = 'US-CA' AND FireDiscoveryDateTime >= TIMESTAMP '2025-06-01 00:00:00' AND FireDiscoveryDateTime <= TIMESTAMP '2025-12-31 23:59:59'",
                "outFields": "POOState, FireDiscoveryDateTime",
                "outSR": "4326",
                "f": "geojson"
                }

request = requests.get(url, params=parameter_req)

data = request.json()
dict_keys = data['features']

# dict_key = dict_keys[0]
# for key in data.keys():
#     print(key)
# print(dict_key)

print(len(dict_keys))

df_dict = {}
Discovery_Time, longitude, latitude = [], [], []

for dict_key in dict_keys:
    #list of fire discovery
    Discovery_Time.append(dict_key['properties'] ['FireDiscoveryDateTime']) 
    #list of corresponding coordinates
    longitude.append(dict_key['geometry'] ['coordinates'] [0])
    latitude.append(dict_key['geometry'] ['coordinates'] [1])

df_dict["fire_Discovery_Time"] = Discovery_Time
df_dict['longitude'] = longitude
df_dict['latitude'] = latitude


# path = Path('WildFire ML/fire_location.json')
# content = json.dumps(df_dict)
# path.write_text(content)

df = pd.DataFrame(df_dict)
#changing the date format  # from milliseconds to seconds #  decreasing accuracy for gee 
df['fire_Discovery_Time'] = pd.to_datetime(df['fire_Discovery_Time'], unit='ms')
df['fire_Discovery_Time'] = df['fire_Discovery_Time'].dt.strftime('%Y-%m-%d') # putting 'dt' accessor

#Adding 'fire_occur' column
df['fire_occur'] = 1


#***************************
# Adding fake values for Negatives
# Dataset = 50/50

is_fire = len(dict_keys)
fake_rows = []
random.seed(42)

for row in range(is_fire):
    # Equal opportunity for each inclusive coordinate 
    long = random.uniform(-124.4, -114.1)
    lat = random.uniform(32.5, 42.0)

    month = random.randint(6, 12)
    day = random.randint(1, 28) # 28 because 31 format is complex

    occured_date = f"2025-{month:02d}-{day:02d}"

    row = {
            "fire_Discovery_Time": occured_date,
            "longitude": long,
            "latitude": lat,
            "fire_occur": 0,
            }
    
    fake_rows.append(row)

negatives = pd.DataFrame(fake_rows)

full_datset = pd.concat([negatives, df], ignore_index=True)

print(full_datset.count())




# lat 32.5, 42.0

# long -124.4, -114.1


