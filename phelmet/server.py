from .routing import safest
from .storage.road_store import geojson, pothole_rows, stats


def create_app(db_path: str, penalty: float = 4.0):
    try:
        from flask import Flask, jsonify
    except ImportError as e:
        raise RuntimeError("install Flask to run the map API") from e
    app = Flask(__name__, static_folder="web")

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/road.geojson")
    def road():
        return jsonify(geojson(db_path))

    @app.get("/api/stats")
    def road_stats():
        return jsonify(stats(db_path, penalty))

    @app.post("/api/safest-route")
    def safe_route():
        from flask import request
        return jsonify(safest(request.json.get("routes", []), pothole_rows(db_path)))

    return app
