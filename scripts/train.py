import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="local Ultralytics data.yaml")
    ap.add_argument("--model", default="yolov8n.pt")
    args = ap.parse_args()
    from ultralytics import YOLO
    YOLO(args.model).train(data=args.data, classes=[0])


if __name__ == "__main__":
    main()
