# Map and route integration

The pipeline writes `data/road_log.db`. It contains `path_points` and geo-deduplicated `potholes`. The default mock GPS starts near Bengaluru and advances with the replay speed, so a complete travel path is available without a physical receiver.

Export provider-neutral GeoJSON after a replay:

```powershell
python -m phelmet.app --source data/sample/demo.mp4 --mock-imu --mock-gps --headless --export-geojson data/road.geojson
```

GeoJSON works directly in Leaflet/OpenStreetMap and can be imported by systems that accept standard GeoJSON. For a local map view install Flask, then run:

```powershell
python -m pip install flask
python scripts/dashboard.py --db data/road_log.db
```

Open `http://127.0.0.1:5000`. The dashboard uses OpenStreetMap tiles but only reads local API data.

For routing, obtain candidate route coordinate arrays from Google Directions, OpenRouteService, or another provider, then send them to `POST /api/safest-route` as `{"routes":[{"id":"fast","coords":[[lat,lon],...]},...]}`. The API gives every route a 0–100 risk score based on pothole severity close to its coordinates and returns the highest-scoring route. This keeps the detection/logging pipeline independent from a particular map vendor.
