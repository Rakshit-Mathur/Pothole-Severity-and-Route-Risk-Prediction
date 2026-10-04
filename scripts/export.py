import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--size", type=int, default=320)
    args = ap.parse_args()
    from ultralytics import YOLO
    YOLO(args.model).export(format="onnx", imgsz=args.size)


if __name__ == "__main__":
    main()
