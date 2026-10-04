# Training a pothole model from your own videos

This is a complete local workflow for a one-class pothole detector. Keep one route or one recording session wholly in validation/test; adjacent video frames are too similar to place randomly on both sides of a split.

## 1. Record and choose videos

Record forward-looking road videos covering different roads, pothole sizes, camera angles, lighting, shadows, dry/wet surfaces, and negative scenes with repairs, manholes, patches, leaves, and cracks. Do not use only clips where potholes are obvious. Remove videos you do not have permission to use.

Begin with several hundred distinct potholes and at least as many difficult negative frames. More varied locations matter more than many almost-identical frames from one drive.

## 2. Extract candidate frames

Create a separate training environment, then extract every 15th frame as a starting point. Use a larger interval for slow video or a smaller interval around short pothole events.

```powershell
py -m venv .venv-train
.\.venv-train\Scripts\Activate.ps1
py -m pip install ultralytics opencv-python
python scripts/extract_frames.py videos\route_01.mp4 data\raw\route_01 --every 15
```

Review the images and delete near-duplicates, unusable blur, and frames that do not add variation. Keep selected negative images too; they get an empty label file.

## 3. Annotate exactly one class

Use any annotation tool that exports **YOLO detection** labels. Make a single class named `pothole`. Draw a tight rectangle around the visible pothole boundary; do not label shadows, repaired patches, speed breakers, or manholes as potholes. Be consistent when the edge is partly hidden by glare or water.

For every image `frame_000123.jpg`, the matching text file must be `frame_000123.txt`. Each pothole uses one line:

```text
0 x_center y_center width height
```

All four coordinates are normalized from 0 to 1. An image with no pothole needs a same-named empty `.txt` file.

## 4. Split the dataset

Arrange files like this; do the route/session split before copying files.

```text
data/potholes/
  images/train/   labels/train/
  images/val/     labels/val/
  images/test/    labels/test/
```

Use approximately 70% train, 20% validation, and 10% test. `data/potholes.yaml` already names class 0 as `pothole`. Check that every image has a corresponding label file and that no route is represented in both train and test.

## 5. Train

Start from the small pretrained YOLO checkpoint. Train at 320 pixels because this project runs inference at 320; use 640 only if small distant potholes are missed and the speed trade-off is acceptable.

```powershell
python scripts/train.py data/potholes.yaml --model yolov8n.pt
```

The project wrapper currently uses 100 epochs and 320 input pixels. The resulting best checkpoint is normally under `runs/detect/train/weights/best.pt`. On Windows, keep training under the script entry point as provided rather than pasting training code into an interactive multiprocessing session. Ultralytics documents its train, validation, and export modes in its [training guide](https://docs.ultralytics.com/modes/train) and [CLI guide](https://docs.ultralytics.com/usage/cli).

## 6. Validate before export

Use the held-out test routes only once you have selected a candidate from validation results. Inspect false positives and false negatives in videos, not only mAP. In this project, a false positive warning is especially distracting, while a missed close pothole is unsafe.

```powershell
yolo detect val model=runs/detect/train/weights/best.pt data=data/potholes.yaml split=test imgsz=320
```

Check precision, recall, and mAP50-95, then replay a video that was never used for training. Add its failure cases to a future training split rather than silently editing the test split.

## 7. Export to ONNX and connect it

```powershell
python scripts/export.py runs/detect/train/weights/best.pt --size 320
Copy-Item runs\detect\train\weights\best.onnx models\pothole.onnx
```

Change `detector.kind` from `mock` to `onnx` in `config.yaml`, then run replay again. Keep the inference size in `config.yaml` equal to the export size. ONNX is a supported Ultralytics export format; see the [official export guide](https://docs.ultralytics.com/modes/export).

## 8. Iterate safely

Version the dataset manifest, label rules, train command, checkpoint, validation metrics, and replay videos. Do not mix the synthetic generator into the training dataset. Improve data diversity and annotation consistency before changing thresholds or model size.
