import argparse
from pathlib import Path

import cv2


def boxes(mask):
    gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    found = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    h, w = img.shape
    out = []
    for cnt in found:
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw * bh >= 20:
            out.append(f"0 {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}")
    return out


def make_split(root: Path, out: Path, split: str, picks: list[int], size: int):
    rgb_dir, mask_dir = root / split / "rgb", root / split / "mask"
    img_dir, lab_dir = out / "images" / split, out / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lab_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for path in sorted(rgb_dir.glob("*.mp4")):
        mask_path = mask_dir / path.name
        rgb, mask = cv2.VideoCapture(str(path)), cv2.VideoCapture(str(mask_path))
        for i in picks:
            rgb.set(cv2.CAP_PROP_POS_FRAMES, i)
            mask.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, frame = rgb.read()
            ok_mask, mask_frame = mask.read()
            if not ok or not ok_mask:
                continue
            name = f"{path.stem}_{i:02d}"
            frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)
            mask_frame = cv2.resize(mask_frame, (size, size), interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(str(img_dir / f"{name}.jpg"), frame)
            (lab_dir / f"{name}.txt").write_text("\n".join(boxes(mask_frame)), encoding="utf-8")
            saved += 1
        rgb.release(); mask.release()
    print(f"{split}: saved {saved} labelled frames")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/pothole_video/pothole_video")
    ap.add_argument("--out", default="data/potholes")
    ap.add_argument("--size", type=int, default=320)
    ap.add_argument("--frames", default="12,36")
    args = ap.parse_args()
    picks = [int(x) for x in args.frames.split(",")]
    root, out = Path(args.root), Path(args.out)
    make_split(root, out, "train", picks, args.size)
    make_split(root, out, "val", picks, args.size)


if __name__ == "__main__":
    main()
