import cv2
import numpy as np

from .types import Detection


class OnnxDetector:
    def __init__(self, model: str, input_size: int = 320, conf: float = 0.4) -> None:
        import onnxruntime as ort
        self.session = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
        self.size = input_size
        self.conf = conf

    def detect(self, img: np.ndarray) -> list[Detection]:
        h, w = img.shape[:2]
        small = cv2.resize(img, (self.size, self.size))
        x = cv2.cvtColor(small, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255
        out = self.session.run(None, {self.session.get_inputs()[0].name: x})[0][0]
        if out.shape[0] < out.shape[1]:
            out = out.T
        dets = []
        for row in out:
            score = float(row[4:].max())
            if score >= self.conf:
                cx, cy, bw, bh = row[:4]
                dets.append(Detection(((cx-bw/2)*w/self.size, (cy-bh/2)*h/self.size, bw*w/self.size, bh*h/self.size), score))
        boxes = [d.box for d in dets]
        keep = cv2.dnn.NMSBoxes(boxes, [d.conf for d in dets], self.conf, .45)
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
