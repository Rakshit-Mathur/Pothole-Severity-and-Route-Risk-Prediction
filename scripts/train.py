import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="local Ultralytics data.yaml")
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--size", type=int, default=320)
    ap.add_argument("--batch", type=int, default=-1)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    from ultralytics import YOLO
    YOLO(args.model).train(data=args.data, epochs=args.epochs, imgsz=args.size,
                           batch=args.batch, device=args.device, workers=2,
                           name="pothole", exist_ok=True)


if __name__ == "__main__":
    main()
