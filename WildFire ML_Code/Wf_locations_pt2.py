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
# locking coordinates and dates
random.seed(42)

for row in range(is_fire):
    # Equal opportunity for each inclusive coordinate 
    long = random.uniform(-124.4, -114.1)
    lat = random.uniform(32.5, 42.0)

    if lat < 35.0 and long < -121.0:
        long = random.uniform(-119.0, -115.0)  # Push inland for Southern CA
    elif lat >= 35.0 and lat < 39.0 and long < -123.0:
        long = random.uniform(-121.0, -119.0)  # Push inland for Central CA
    elif lat >= 39.0 and long < -124.0:
        long = random.uniform(-123.0, -120.0)  # Push inland for Northern CA

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

full_dataset = pd.concat([negatives, df], ignore_index=True)

print(full_dataset.count())




# lat 32.5, 42.0

# long -124.4, -114.1



# *************************************************========
# PHASE 4: Google Earth Engine Feature Extraction Pipeline
# *************************************************========
print("\nConverting local DataFrame into a GEE FeatureCollection...")
gee_points = geemap.pandas_to_ee(full_dataset)

# Reference Cloud Climate and Spectral Databases
era5_daily = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
modis_vegetation = ee.ImageCollection("MODIS/061/MOD13A2")

def extract_environmental_attributes(feature):
    date_str = feature.get('fire_Discovery_Time')
    row_date = ee.Date(date_str)
    point_geom = feature.geometry()
    
    # Extract structural time dimensions directly on Google's servers
    month_num = row_date.get('month')
    # Change this line inside extract_environmental_attributes:
    doy_num = row_date.getRelative('day', 'year').add(1)
    
    # --- ERA5 Weather Spatial Extraction ---
    weather_img = era5_daily.filterDate(row_date, row_date.advance(1, 'day')).first()
    
    # Cloud-side mathematical calculation for Relative Humidity (Magnus Formula)
    rh_expr = weather_img.expression(
        '100 * (exp((17.502 * (Td - 273.15)) / (240.97 + (Td - 273.15))) / '
        'exp((17.502 * (T - 273.15)) / (240.97 + (T - 273.15))))', {
            'T': weather_img.select('temperature_2m'),
            'Td': weather_img.select('dewpoint_temperature_2m')
        }
    ).rename('relative_humidity').clamp(0, 100)
    
    # Stack the new relative humidity band on top of the raw weather data
    complete_weather = weather_img.addBands(rh_expr)
    
    weather_stats = complete_weather.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point_geom,
        scale=11132
    )
    
    # --- MODIS Vegetation Spatial Extraction ---
    veg_img = modis_vegetation.filterDate(row_date.advance(-8, 'day'), row_date.advance(8, 'day')).first()
    veg_stats = veg_img.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point_geom,
        scale=1000
    )
    
    # Return features decorated with metrics and time indicators
    return feature.set(weather_stats).set(veg_stats).set({
        'month': month_num,
        'day_of_year': doy_num
    })

print("Mapping satellite metrics across all space & time coordinates...")
processed_collection = gee_points.map(extract_environmental_attributes)

print("Submitting Export Task directly to your Google Drive...")
task = ee.batch.Export.table.toDrive(
    collection=processed_collection,
    description='wildfire_ml_dataset_raw',
    folder='Wildfire_ML',              
    fileFormat='CSV',
    selectors=[                        
        'fire_Discovery_Time', 'longitude', 'latitude', 'fire_occur',
        'temperature_2m', 'total_precipitation_sum', 'dewpoint_temperature_2m',
        'volumetric_soil_water_layer_1', 'NDVI', 'EVI', 
        'relative_humidity', 'month', 'day_of_year'  # Added selectors to export the pre-engineered columns
    ]
)

task.start()
print("\n--- Success! Pipeline Running in Cloud ---")