# Vision-based pothole severity and road-risk logger

## Problem

This project is a software demonstration that detects potholes in replayed video, estimates severity from visible size and darkness, and records them against a GPS travel path. It is a single-class detector and does not try to identify other road hazards.

## Approach

Frames are captured into a one-item queue, so old frames are dropped. Replay IMU pitch and angular-rate gating reject frames when the road is not visible. The remaining road ROI is checked for blur and simple road texture before a mock dark-blob detector or an ONNX YOLOv8n model runs. Confirmed detections are assigned a monocular size-based severity and written with the current GPS point to SQLite.

## System Design

The critical path is camera, capture, ROI, detector, tracker, and severity. GPS path and SQLite writes run outside that path. `docs/ARCHITECTURE.md` has the diagram.

## Latency Budget

The target capture-to-detection latency is p50 at most 120 ms and p95 at most 180 ms. The code records rolling timing values and `scripts/benchmark.py` prints the replay summary.

## Setup

```powershell
py -m pip install -e .
py -m pip install pytest
py -m pip install -e .[map]
python scripts/gen_synthetic_data.py
```

Use `py -m pip install -e .[onnx]` only when an ONNX model is available. Training and export helpers need a separately installed Ultralytics package and a local `data.yaml`.

## Running

```powershell
python -m phelmet.app --source data/sample/road.mp4 --mock-imu --mock-gps --headless
pytest -q
python scripts/benchmark.py
```

To make an annotated demo video with boxes, ROI, HUD, and severity labels, run `python scripts/demo.py`. It writes `demo_out.mp4`; use `--debug-view` with the app to see the same overlay live and press `q` to quit. Screenshot to be added.

Each confirmed pothole is logged once per temporary visual track. `data/road_log.db` stores GPS path points and geo-deduplicates potholes within the configured circular radius. Export a portable map layer with `--export-geojson data/road.geojson`, or install Flask and run `python scripts/dashboard.py` for the OpenStreetMap map view. The GeoJSON and `/api/safest-route` contract are map-provider independent: a Google Directions or OpenStreetMap route client can submit candidate coordinate paths to obtain the least-risk route.

`config.yaml` selects the mock detector and contains all normal tunables. See [the training workflow](docs/TRAINING.md) to replace it with your own ONNX pothole model.

For the presentation outline, measured runtime figures, slide content, and the live demonstration sequence, see [the presentation guide](docs/PRESENTATION_GUIDE.md).

## Results

The synthetic replay test verifies that potholes and GPS path points reach the road database. Laptop FPS, CPU use, and p50/p95 latency depend on the video and computer used.

## Limitations

Monocular distance and width are estimates from a flat-ground camera model. Night, rain, glare, shadows, and unusual road surfaces can reduce detection quality. The video camera angle must be calibrated. The mock detector is for replay only; an ONNX pothole model must be trained and evaluated separately.

## Future Work

Collect varied video, label difficult negative examples, and evaluate on held-out routes before using a trained model. A depth sensor can improve the severity estimate. Google Directions or OpenRouteService can provide live route candidates to the existing provider-independent route-risk API.

## Assumptions

- The camera is 1.55 m above the ground, has a 300 px focal length, and is pitched down 8 degrees.
- Replay is 320x240 at 20 FPS; default speed is 40 km/h if GPS speed is unavailable.
- Two sightings in three frames confirm a pothole. The same road point is geo-deduplicated inside an 8 m radius.
- Stabilization is off by default because it can cost too much latency on the Pi.
- A flat road plane is assumed for ground geometry.
