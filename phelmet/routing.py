from .storage.road_store import metres


def route_score(coords: list, potholes: list) -> float:
    risk = 0.0
    for lat, lon in coords:
        for hole in potholes:
            if metres(lat, lon, hole["lat"], hole["lon"]) < 15:
                risk += {"LOW": 1, "MEDIUM": 3, "HIGH": 6}.get(hole["severity"], 3)
    return max(0.0, 100.0 - risk)


def safest(routes: list, potholes: list) -> dict | None:
    if not routes:
        return None
    scored = [{"id": route.get("id"), "score": route_score(route["coords"], potholes)} for route in routes]
    return max(scored, key=lambda row: row["score"])
