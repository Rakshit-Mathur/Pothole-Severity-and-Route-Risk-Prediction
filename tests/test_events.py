import csv

from phelmet.decision import Decision
from phelmet.storage import EventLog
from phelmet.tracker import Tracker
from phelmet.types import Detection


def cfg():
    return {"camera": {"height": 240, "height_m": 1.5, "focal_px": 300, "pitch_deg": 8}, "gps": {"fallback_kmh": 40}, "tracker": {"iou_min": .2, "confirm_n": 2, "confirm_m": 3, "cooldown_s": 3, "lost_frames": 3}, "decision": {"tti_min_s": .1, "tti_max_s": 5, "rough_patch_s": 1.5}}


def test_once_and_final_conf(tmp_path):
    tr, dec = Tracker(cfg()["tracker"]), Decision(cfg())
    log = EventLog(str(tmp_path / "p.csv")); log.start()
    events = []
    for i, conf in enumerate([.4, .8, .6] + [.6] * 7):
        tracks = tr.update([Detection((10, 180, 40, 8), conf)], i, "first")
        alert = dec.choose(tracks, 11.1, True, i, 0, "alert")
        if alert:
            events.append(alert)
            track = tracks[0]
            log.log_event((track.first_ts, alert.alert_ts, track.id, alert.max_conf, alert.severity, alert.distance_m))
    assert len(events) == 1
    tr.update([], 11, "end"); tr.update([], 12, "end"); tr.update([], 13, "end")
    for old in tr.closed:
        log.done(old)
    log.flush_open(tr.tracks)
    rows = list(csv.DictReader((tmp_path / "p.csv").open()))
    assert len(rows) == 1 and float(rows[0]["max_conf"]) == .8


def test_two_tracks_and_hidden_state(tmp_path):
    tr, dec = Tracker(cfg()["tracker"]), Decision(cfg())
    log = EventLog(str(tmp_path / "two.csv")); log.start()
    assert dec.choose([], 11.1, False, 1, 0, "x") is None
    tracks = tr.update([Detection((10, 180, 40, 8), .4), Detection((100, 180, 40, 8), .5)], 0, "x")
    tracks = tr.update([Detection((10, 180, 40, 8), .8), Detection((100, 180, 40, 8), .9)], 1, "x")
    first = dec.choose(tracks, 11.1, True, 1, 0, "x")
    second = dec.choose(tracks, 11.1, True, 2, 0, "x")
    assert first and second and first.track_id != second.track_id
    for alert in (first, second):
        track = next(x for x in tracks if x.id == alert.track_id)
        log.log_event((track.first_ts, alert.alert_ts, track.id, alert.max_conf, alert.severity, alert.distance_m))
        log.done(track)
    log.flush_open([])
    assert len(list(csv.DictReader((tmp_path / "two.csv").open()))) == 2
