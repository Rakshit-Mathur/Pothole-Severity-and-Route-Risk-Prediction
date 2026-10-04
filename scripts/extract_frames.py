import argparse
from pathlib import Path

import cv2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--every", type=int, default=15, help="keep one frame every N video frames")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cap, i, saved = cv2.VideoCapture(args.video), 0, 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        if i % args.every == 0:
            cv2.imwrite(str(out / f"frame_{saved:06d}.jpg"), img)
            saved += 1
        i += 1
    print(f"saved {saved} frames to {out}")


if __name__ == "__main__":
    main()
