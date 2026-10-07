import cv2
import numpy as np

from .types import Detection


class OnnxDetector:
    def __init__(self, model: str, input_size: int = 320, conf: float = 0.4,
                 nms_iou: float = .45, max_area: float = .18) -> None:
        import onnxruntime as ort
        self.session = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
        self.size = input_size
        self.conf = conf
        self.nms_iou = nms_iou
        self.max_area = max_area

    def prep(self, img: np.ndarray):
        h, w = img.shape[:2]
        scale = min(self.size / w, self.size / h)
        nw, nh = round(w * scale), round(h * scale)
        small = cv2.resize(img, (nw, nh))
        left, top = (self.size - nw) // 2, (self.size - nh) // 2
        out = np.full((self.size, self.size, 3), 114, np.uint8)
        out[top:top+nh, left:left+nw] = small
        x = cv2.cvtColor(out, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255
        return x, scale, left, top

    def detect(self, img: np.ndarray) -> list[Detection]:
        h, w = img.shape[:2]
        x, scale, left, top = self.prep(img)
        out = self.session.run(None, {self.session.get_inputs()[0].name: x})[0][0]
        if out.shape[0] < out.shape[1]:
            out = out.T
        dets = []
        for row in out:
            score = float(row[4:].max())
            if score >= self.conf:
                cx, cy, bw, bh = row[:4]
                x1, y1 = (cx-bw/2-left) / scale, (cy-bh/2-top) / scale
                bw, bh = bw / scale, bh / scale
                x1, y1 = max(0, x1), max(0, y1)
                bw, bh = min(bw, w-x1), min(bh, h-y1)
                if bw * bh <= w * h * self.max_area:
                    dets.append(Detection((x1, y1, bw, bh), score))
        boxes = [d.box for d in dets]
        keep = cv2.dnn.NMSBoxes(boxes, [d.conf for d in dets], self.conf, self.nms_iou)
        return [dets[int(i)] for i in keep]


class MockDetector:
    def __init__(self, conf: float = 0.4) -> None:
        self.conf = conf

    def detect(self, img: np.ndarray) -> list[Detection]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(gray, 42, 255, cv2.THRESH_BINARY_INV)[1]
        found = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        dets = []
        for cnt in found:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h >= 25 and w > h:
                dark = 1 - gray[y:y+h, x:x+w].mean() / 255
                dets.append(Detection((x, y, w, h), min(0.95, dark), dark))
        return dets
