import argparse
import glob

import cv2
import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", help="glob for chessboard images")
    ap.add_argument("--cols", type=int, default=9)
    ap.add_argument("--rows", type=int, default=6)
    args = ap.parse_args()
    obj = np.zeros((args.rows*args.cols, 3), np.float32)
    obj[:, :2] = np.mgrid[0:args.cols, 0:args.rows].T.reshape(-1, 2)
    objs, corners, shape = [], [], None
    for path in glob.glob(args.images):
        img = cv2.imread(path); gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ok, pts = cv2.findChessboardCorners(gray, (args.cols, args.rows))
        if ok: objs.append(obj); corners.append(pts); shape = gray.shape[::-1]
    _, mat, _, _, _ = cv2.calibrateCamera(objs, corners, shape, None, None)
    print("focal_px", mat[0, 0])


if __name__ == "__main__":
    main()
