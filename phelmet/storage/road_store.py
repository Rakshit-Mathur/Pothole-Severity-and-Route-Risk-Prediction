import json
import queue
import sqlite3
import threading
from math import asin, cos, radians, sin, sqrt
from pathlib import Path


def metres(a_lat, a_lon, b_lat, b_lon) -> float:
    dlat, dlon = radians(b_lat-a_lat), radians(b_lon-a_lon)
    x = sin(dlat/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dlon/2)**2
    return 6371000 * 2 * asin(sqrt(x))


class RoadStore:
    def __init__(self, path: str, radius_m: float = 8.0) -> None:
        self.path, self.radius = Path(path), radius_m
        self.q = queue.Queue(maxsize=500)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def point(self, row: dict, ts: str) -> None:
        if row.get("fix_ok") and row.get("hdop", 99) <= 4:
            self._put(("point", (ts, row["lat"], row["lon"], row["speed_kmh"], row.get("source", "unknown"), row.get("hdop"), row.get("sats"))))

    def pothole(self, row: tuple) -> None:
        self._put(("pothole", row))

    def _put(self, row) -> None:
        try:
            self.q.put_nowait(row)
        except queue.Full:
            if row[0] == "point":
                return
            try:
                self.q.get_nowait()
                self.q.put_nowait(row)
            except queue.Empty:
                pass

    def close(self) -> None:
        self.stop.set()
        self.thread.join(2)

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path)
        db.execute("pragma journal_mode=WAL")
        db.execute("create table if not exists path_points (ts text, lat real, lon real, speed_kmh real, source text, hdop real, sats integer)")
        cols = {x[1] for x in db.execute("pragma table_info(path_points)")}
        for name, kind in (("source", "text"), ("hdop", "real"), ("sats", "integer")):
            if name not in cols:
                db.execute(f"alter table path_points add column {name} {kind}")
        db.execute("create table if not exists potholes (id integer primary key, ts text, lat real, lon real, max_conf real, severity text, dist_m real, seen integer default 1)")
        return db

    def _pothole(self, db, row) -> None:
        ts, lat, lon, conf, severity, dist = row
        found = db.execute("select id, lat, lon, max_conf from potholes").fetchall()
        for pid, old_lat, old_lon, old_conf in found:
            if metres(lat, lon, old_lat, old_lon) <= self.radius:
                db.execute("update potholes set max_conf=?, severity=?, seen=seen+1 where id=?", (max(conf, old_conf), severity, pid))
                return
        db.execute("insert into potholes (ts,lat,lon,max_conf,severity,dist_m) values (?,?,?,?,?,?)", row)

    def _run(self) -> None:
        db = self._db()
        while not self.stop.is_set() or not self.q.empty():
            try:
                kind, row = self.q.get(timeout=.1)
            except queue.Empty:
                continue
            if kind == "point":
                db.execute("insert into path_points (ts,lat,lon,speed_kmh,source,hdop,sats) values (?,?,?,?,?,?,?)", row)
            else:
                self._pothole(db, row)
            db.commit()
        db.close()


def geojson(path: str) -> dict:
    db = sqlite3.connect(path)
    points = db.execute("select lat,lon,speed_kmh,source,hdop,sats from path_points order by rowid").fetchall()
    holes = db.execute("select id,ts,lat,lon,max_conf,severity,dist_m,seen from potholes").fetchall()
    db.close()
    features = [{"type": "Feature", "properties": {"kind": "path", "source": points[0][3] if points else "none"}, "geometry": {"type": "LineString", "coordinates": [[x[1], x[0]] for x in points]}}]
    for x in holes:
        features.append({"type": "Feature", "properties": {"kind": "pothole", "id": x[0], "time": x[1], "confidence": x[4], "severity": x[5], "distance_m": x[6], "seen": x[7]}, "geometry": {"type": "Point", "coordinates": [x[3], x[2]]}})
    return {"type": "FeatureCollection", "features": features}


def pothole_rows(path: str) -> list:
    db = sqlite3.connect(path)
    rows = db.execute("select lat,lon,severity from potholes").fetchall()
    db.close()
    return [{"lat": x[0], "lon": x[1], "severity": x[2]} for x in rows]


def stats(path: str, penalty: float = 4.0) -> dict:
    db = sqlite3.connect(path)
    points = db.execute("select lat,lon from path_points order by rowid").fetchall()
    holes = db.execute("select severity,max_conf from potholes").fetchall()
    db.close()
    distance = sum(metres(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))
    risk = sum({"LOW": 1, "MEDIUM": 3, "HIGH": 6}.get(x[0], 3) * x[1] for x in holes)
    risk_km = risk / max(distance / 1000, .05)
    score = max(0, round(100 - penalty * risk_km, 1))
    return {"potholes": len(holes), "distance_m": round(distance, 1), "risk_per_km": round(risk_km, 2), "road_score": score}


def export_geojson(db_path: str, out: str) -> None:
    Path(out).write_text(json.dumps(geojson(db_path), indent=2), encoding="utf-8")
