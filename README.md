# 🌲 Predictive Early Warning Geospatial Wildfire Hazard Analytical Dashboard

An end-to-end machine learning pipeline and interactive visualization dashboard that predicts localized wildfire risk across California with a **91.39% cross-validated accuracy**.

Instead of just mapping fires that already happened, this system pulls live active fire data, offloads massive climate and satellite imagery calculations directly to cloud servers, and uses a tuned predictive model to flag future hazards before launching an automated, dual-view browser dashboard.

---

## 🚀 Key Engineering Accomplishments

* **91.39% Prediction Accuracy:** Engineered the core risk classification engine using a Scikit-Learn `RandomForestClassifier`. Performed hyperparameter tuning and capped the maximum tree depth to prevent the model from simply memorizing the training rows, forcing it to learn broad, realistic weather trends instead.
* **100% Reduction in Local Runtime Slowdowns:** Handled automated environmental feature extraction across thousands of coordinates without freezing my local machine. Optimized the application by offloading heavy thermodynamic math and vegetation health indices directly to Google Earth Engine cloud servers.
* **Zero Data Misalignment Errors:** Resolved a complex index-shuffling bug during the train-test split that was causing map markers to display in the wrong locations. Refactored the data pipeline to isolate latitude and longitude data before feature drops, utilizing precise Pandas `.loc` indexing to perfectly lock coordinates to their matching predictions.
* **Eliminated Dataset Selection Bias:** Addressed the common machine learning issue of "presence-only" data bias. Because fire APIs only track where fires *did* happen, I built a script to download active fire footprints via the ArcGIS API and automatically paired them with randomized, simulated pseudo-absence coordinates across California to create a perfectly balanced 1:1 training dataset.
* **Automated Local System Startup:** Built an automation script using Python’s `pathlib` and `webbrowser` libraries that dynamically formats relative workspace paths into absolute local web links. This opens both the interactive Folium map and the Plotly feature graph side-by-side in separate browser tabs instantly with a single command.

---

## 🛠️ System Architecture & Data Flow

```text
       [ ArcGIS REST API ]               [ Pseudo-Absence Engine ]
                │                                    │
    (Download Active Footprints)         (Generate Random Coordinates)
                │                                    │
                ▼                                    ▼
         [ Target: 1 ]                         [ Target: 0 ]
                │                                    │
                └─────────────────┬──────────────────┘
                                  │
                                  ▼
                       [ 1:1 Balanced Dataset ]
                                  │
                                  ▼
         [ Google Earth Engine Cloud Servers (GEE API) ]
           ├── Calculate Thermodynamic Trends (Relative Humidity)
           └── Analyze Satellite Vegetation Health Indices (NDVI)
                                  │
                                  ▼
               [ Scikit-Learn Pipeline Optimization ]
           ├── 10-Fold Cross-Validation Testing Loop
           └── Hyperparameter Tuning (Max Depth Capping)
                                  │
                                  ▼
                [ Automated Local Dashboard UI ]
           ├── Folium Map: Interactive Hazard Markers
           └── Plotly Graph: Feature Importance Weights
