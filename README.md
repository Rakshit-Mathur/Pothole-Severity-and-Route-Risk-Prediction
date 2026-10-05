# Helmet pothole warning system

## Problem

This project is a software demonstration of a helmet-pothole warning pipeline. It gives a local warning for potholes from replayed video. It is a single-class detector and does not try to identify other road hazards.

## Approach

Frames are captured into a one-item queue, so old frames are dropped. Replay IMU pitch and angular-rate gating reject frames when the road is not visible. The remaining road ROI is checked for blur and simple road texture before a mock dark-blob detector or an ONNX YOLOv8n model runs. Detections need temporal confirmation before distance, time-to-impact (TTI), severity, and a non-blocking console warning are calculated.

## System Design

The critical path is camera, capture, ROI, detector, tracker, decision, and warning. GPS, telemetry, and optional dashboard work are outside that path. `docs/ARCHITECTURE.md` has the diagram.

## Latency Budget

The target from capture to warning is p50 at most 120 ms and p95 at most 180 ms for the intended real-time pipeline. The code records rolling timing values and `scripts/benchmark.py` prints the replay summary.

## Setup

```powershell
py -m pip install -e .
py -m pip install pytest
python scripts/gen_synthetic_data.py
```

Use `py -m pip install -e .[onnx]` only when an ONNX model is available. Training and export helpers need a separately installed Ultralytics package and a local `data.yaml`.

## Running

```powershell
python -m phelmet.app --source data/sample/road.mp4 --mock-imu --mock-gps --headless
pytest -q
python scripts/benchmark.py
```

To make an annotated demo video with boxes, ROI, HUD, and warning moments, run `python scripts/demo.py`. It writes `demo_out.mp4`; use `--debug-view` with the app to see the same overlay live and press `q` to quit. Screenshot to be added.

Each confirmed pothole produces one console event and a final row in `logs/potholes.csv` when its track ends. Use `--log-file another.csv` to choose a different log file.

`config.yaml` selects the mock detector and contains all normal tunables. See [the training workflow](docs/TRAINING.md) to replace it with your own ONNX pothole model.

## Results

The synthetic replay test verifies that an alert can pass through the pipeline. Laptop FPS, CPU use, and p50/p95 latency depend on the video and computer used.

## Limitations

Monocular distance and width are estimates from a flat-ground camera model. Night, rain, glare, shadows, and unusual road surfaces can reduce detection quality. The video camera angle must be calibrated. The mock detector is for replay only; an ONNX pothole model must be trained and evaluated separately.

## Future Work

Collect varied video, label difficult negative examples, and evaluate on held-out routes before using a trained model. A depth-estimation hook can be added later. Storage, map dashboard, safest-route, and all hardware integration were deliberately left out of this software demonstration.

## Assumptions

- The camera is 1.55 m above the ground, has a 300 px focal length, and is pitched down 8 degrees.
- Replay is 320x240 at 20 FPS; default speed is 40 km/h if GPS speed is unavailable.
- A warning is considered between 0.8 and 2.5 seconds TTI, with a speed adjustment.
- Two sightings in three frames confirm a pothole; a track has a 3-second cooldown.
- Stabilization is off by default because it can cost too much latency on the Pi.
- A flat road plane is assumed for ground geometry.
