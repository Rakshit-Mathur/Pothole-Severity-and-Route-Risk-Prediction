import time

from phelmet.routing import safest
from phelmet.storage.road_store import RoadStore, geojson


def test_dedup_path_and_route(tmp_path):
    path = str(tmp_path / "road.db")
    store = RoadStore(path, 8)
    store.start()
    store.point({"lat": 12.0, "lon": 77.0, "speed_kmh": 40}, "a")
    store.point({"lat": 12.00001, "lon": 77.00001, "speed_kmh": 40}, "b")
    store.pothole(("a", 12.0, 77.0, .7, "MEDIUM", 5))
    store.pothole(("b", 12.00001, 77.00001, .9, "HIGH", 5))
    time.sleep(.2)
    store.close()
    data = geojson(path)
    holes = [x for x in data["features"] if x["properties"]["kind"] == "pothole"]
    assert len(holes) == 1 and holes[0]["properties"]["confidence"] == .9
    out = safest([{"id": "bad", "coords": [[12, 77]]}, {"id": "good", "coords": [[13, 78]]}], [{"lat": 12, "lon": 77, "severity": "HIGH"}])
    assert out["id"] == "good"
