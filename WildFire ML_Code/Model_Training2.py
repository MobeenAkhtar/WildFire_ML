import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier


content = pd.read_csv('WildFire ML/wildfire_ml_dataset_raw.csv')
df = pd.DataFrame(content)
print(df.count())

#Handling missing data (Data cleaning)
df = df.dropna(subset=['temperature_2m', 'NDVI']) #There might be rows where the 'NDVI' and 'EVI' values were not present by other features were present
print(df.count())

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

coordinates_df = df[['longitude', 'latitude']]

y = df['fire_occur']

X = df.drop(columns=['fire_occur',
                      'fire_Discovery_Time',
                      'longitude',
                      'latitude'])

# reaching leaf nodes which resulted in 0 or 1
rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)

print("\nRunning The model")
mean_result = cross_val_score(rf, X, y, cv=10, scoring='accuracy', n_jobs=-1)
Total_mean = mean_result.mean() * 100
print(Total_mean)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

coordinates_test = coordinates_df.loc[X_test.index].reset_index(drop=True) # reset the scrambled data so it doesn't crash when going index 0,1,2

rf.fit(X_train, y_train)

print(coordinates_df.count())



#****************
# FOR FOLIUM MAP
#****************

import folium

# Pulls 2d array of (fire_occured and no fire) 
probability_both = rf.predict_proba(X_test)
# pulling 1d array of fire occured
probability_fire = probability_both[:, 1]

#Base MAP
hazard_map = folium.Map(location=[37.5, -119.5], zoom_start=6)

for i in range(len(probability_fire)):

    #search in [row_num, cloumn_num]
    long = coordinates_test.loc[i, 'longitude']
    lat = coordinates_test.loc[i, 'latitude']
    prob = probability_fire[i] * 100

    if prob >= 70:
        color = 'red'
        risk_label = 'Extreme'
    elif prob >= 30:
        color = 'yellow'
        risk_label = 'Medium'
    else:
        color = 'green'
        risk_label = 'Low'


    popup_message = f"""
    <strong>{risk_label}</strong><br>
    Fire Probability: {prob:.1f}%<br>
    Coordinates: {lat:.4f}, {long:.4f}
    """

    folium.CircleMarker(location=[lat, long],
                        radius=6,
                        popup= folium.Popup(popup_message, max_width=300),
                        tooltip='Click for information',
                        color= color,
                        fill=True,
                        fill_color= color,
                        opacity=0.7
                    ).add_to(hazard_map)
    
hazard_map.save('WildFire ML/Result/Map_representation.html')
# hazard_map.show_in_browser()





#*************************
# for graph in plotly
#*************************
import plotly.express as px

attribute_weights = rf.feature_importances_
features = rf.feature_names_in_

title = 'Contribution factor'
labels = {'x': 'Features',
          'y': 'Feature Weights',
          'color': 'Significance Scale',
          }

fig = px.bar(x=features,
            y=attribute_weights,
            title=title,
            labels=labels,
            color=attribute_weights,
            color_continuous_scale='temps',
            )

fig.write_html('WildFire ML/Result/Graph_representation.html')
#fig.show()






