# Helmet pothole warning system

## Problem

This project gives a helmet-mounted rider a local warning for potholes. It is a single-class detector and does not try to identify other road hazards.

## Approach

Frames are captured into a one-item queue, so old frames are dropped. IMU pitch and angular-rate gating reject frames when the road is not visible. The remaining road ROI is checked for blur and simple road texture before a mock dark-blob detector or an ONNX YOLOv8n model runs. Detections need temporal confirmation before distance, time-to-impact (TTI), severity, and a non-blocking buzzer warning are calculated.

## System Design

The critical path is camera, capture, ROI, detector, tracker, decision, and warning. GPS, telemetry, and optional dashboard work are outside that path. `docs/ARCHITECTURE.md` has the diagram.

## Latency Budget

The target from capture to warning is p50 at most 120 ms and p95 at most 180 ms on a Pi 5. The code records rolling timing values and `scripts/benchmark.py` prints the replay summary. Hardware results are to be measured on hardware.

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

`config.yaml` selects the mock detector and contains all normal tunables. `phelmet.hardware` contains Pi Camera, USB camera, MPU6050, NMEA GPS, and GPIO-buzzer adapters; these require their platform packages and hardware.

## Results

The synthetic replay test verifies that an alert can pass through the pipeline. FPS, CPU use, and p50/p95 latency are to be measured on hardware.

## Limitations

Monocular distance and width are estimates from a flat-ground camera model. Night, rain, glare, shadows, and unusual road surfaces can reduce detection quality. Helmet mount angle must be calibrated, and MPU6050 axes must be aligned with the camera. The mock detector is for replay only; an ONNX pothole model must be trained and evaluated separately.

## Future Work

Before field testing: calibrate mount angle, check IMU axes, wait for GPS fix, verify buzzer wiring, use Pi 5 active cooling and a suitable power bank, then check for thermal throttling. A depth-sensor fusion hook and NCNN backend can be added later. Storage, map dashboard, and safest-route modules were deliberately left out of this small core build.

## Assumptions

- The camera is 1.55 m above the ground, has a 300 px focal length, and is pitched down 8 degrees.
- Replay is 320x240 at 20 FPS; default speed is 40 km/h if GPS speed is unavailable.
- A warning is considered between 0.8 and 2.5 seconds TTI, with a speed adjustment.
- Two sightings in three frames confirm a pothole; a track has a 3-second cooldown.
- Stabilization is off by default because it can cost too much latency on the Pi.
- A flat road plane is assumed for ground geometry.
