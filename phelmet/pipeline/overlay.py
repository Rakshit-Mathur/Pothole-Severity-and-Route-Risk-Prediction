import cv2
import numpy as np


def to_full(box, top: int, scale: float = 1.0):
    x, y, w, h = box
    return int(x / scale), int(y / scale + top), int(w / scale), int(h / scale)


def box_color(track: dict):
    if not track["confirmed"]:
        return (0, 255, 255)
    return {"LOW": (0, 210, 0), "MEDIUM": (0, 145, 255), "HIGH": (0, 0, 255)}.get(track["severity"], (0, 0, 255))


def put_text(img, text: str, at, color=(255, 255, 255), size=.45):
    cv2.putText(img, text, at, cv2.FONT_HERSHEY_SIMPLEX, size, color, 1, cv2.LINE_AA)


def draw_track(img, track: dict):
    x, y, w, h = track["box"]
    color = box_color(track)
    cv2.rectangle(img, (int(x), int(y)), (int(x+w), int(y+h)), color, 2 if track["confirmed"] else 1)
    put_text(img, f"pothole {track['conf']:.2f} id{track['id']}", (int(x), max(14, int(y)-5)), color)
    if track["severity"] == "ROUGH_PATCH":
        put_text(img, "rough patch", (int(x), int(y+h+16)), color)
    else:
        put_text(img, f"{track['dist']:.1f}m  tti {track['tti']:.1f}s  {track['severity'][:3]}", (int(x), int(y+h+16)), color)


def draw(img: np.ndarray, info: dict) -> np.ndarray:
    out = img.copy()
    state = info["state"]
    if state == "ROAD_NOT_VISIBLE":
        out = cv2.addWeighted(out, .45, np.full_like(out, 90), .55, 0)
        put_text(out, "ROAD NOT VISIBLE, detection skipped", (18, out.shape[0] // 2), (230, 230, 230), .55)
    else:
        pts = np.array(info["roi"], np.int32).reshape((-1, 1, 2))
        cv2.polylines(out, [pts], True, (255, 255, 0), 1)
        cv2.line(out, (0, info["horizon"]), (out.shape[1], info["horizon"]), (255, 0, 0), 1)
        for track in info["tracks"]:
            draw_track(out, track)
    put_text(out, f"{state}  {info['speed']:.1f} km/h  pitch {info['pitch']:.1f}", (8, 18))
    put_text(out, f"fps {info['fps']:.1f}  e2e {info['latency']:.1f} ms", (8, 37))
    if info.get("alert"):
        cv2.rectangle(out, (1, 1), (out.shape[1]-2, out.shape[0]-2), (0, 0, 255), 5)
        put_text(out, "WARNING", (out.shape[1] // 2-48, 30), (0, 0, 255), .7)
    return out
