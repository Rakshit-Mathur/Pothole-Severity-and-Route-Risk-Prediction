# Architecture

```mermaid
flowchart LR
  Vid[Replay video] --> Cap[Capture: latest frame]
  Pose[Replay IMU pose] --> ROI
  GPS[Replay GPS path] --> Store[SQLite road store]
  Cap --> ROI[Dynamic ROI, road and blur checks]
  ROI --> Det[ONNX or mock detector]
  Det --> Trk[IoU tracker]
  Trk --> Dec[Distance and severity]
  Dec --> Store
  Store --> Map[GeoJSON / map API]
```

| Stage | Target (ms) |
|---|---:|
| Capture queue | 5 |
| Pose, ROI and quality checks | 3 |
| Detector | 80 |
| Tracker and decision | 5 |
| Severity and log queue | 5 |
| End-to-end p50 | <= 120 |
| End-to-end p95 | <= 180 |

The detector runs only on the ROI. The queue has size one so the inference loop takes the newest frame. A rolling p95 above the configured budget enables every-second-frame inference until it recovers. Replay IMU gating sets `ROAD_NOT_VISIBLE`; failed ROI quality checks set `DEGRADED`. GPS path points and pothole rows are queued to SQLite using WAL mode. Potholes inside the configured circular radius update one stored location instead of creating duplicates.
