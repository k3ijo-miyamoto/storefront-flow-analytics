from __future__ import annotations

from collections.abc import Sequence

from mallflow.detection.base import Detection, PersonDetector


class NullPersonDetector(PersonDetector):
    """Detector placeholder used before ML backends are wired in."""

    def detect(self, frame: object, frame_id: int, timestamp_s: float) -> Sequence[Detection]:
        return []


class OpenCVHogPersonDetector(PersonDetector):
    """OpenCV HOG person detector for local MVP analysis.

    This is a lightweight baseline backend. It does not identify faces or infer
    demographic attributes.
    """

    def __init__(self, max_width: int = 960, min_confidence: float = 0.0) -> None:
        import cv2

        self._cv2 = cv2
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self._max_width = max_width
        self._min_confidence = min_confidence

    def detect(self, frame: object, frame_id: int, timestamp_s: float) -> Sequence[Detection]:
        cv2 = self._cv2
        image = frame
        scale = 1.0
        height, width = image.shape[:2]
        if self._max_width > 0 and width > self._max_width:
            scale = self._max_width / width
            image = cv2.resize(image, (self._max_width, round(height * scale)), interpolation=cv2.INTER_AREA)

        rects, weights = self._hog.detectMultiScale(
            image,
            winStride=(8, 8),
            padding=(16, 16),
            scale=1.05,
        )

        detections: list[Detection] = []
        for rect, weight in zip(rects, weights):
            confidence = float(weight)
            if confidence < self._min_confidence:
                continue
            x, y, w, h = rect
            x1 = x / scale
            y1 = y / scale
            x2 = (x + w) / scale
            y2 = (y + h) / scale
            detections.append(
                Detection(
                    frame_id=frame_id,
                    timestamp_s=timestamp_s,
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                )
            )
        return detections


class UltralyticsPersonDetector(PersonDetector):
    """Ultralytics YOLO person detector.

    Only COCO class 0 (person) is emitted. The detector stores no crops or
    identifying attributes.
    """

    def __init__(
        self,
        model_path: str,
        image_size: int = 960,
        confidence_threshold: float = 0.25,
        device: str | None = None,
    ) -> None:
        from ultralytics import YOLO

        self._model = YOLO(model_path)
        self._image_size = image_size
        self._confidence_threshold = confidence_threshold
        self._device = device

    def detect(self, frame: object, frame_id: int, timestamp_s: float) -> Sequence[Detection]:
        kwargs: dict[str, object] = {
            "imgsz": self._image_size,
            "conf": self._confidence_threshold,
            "classes": [0],
            "verbose": False,
        }
        if self._device:
            kwargs["device"] = self._device

        results = self._model.predict(frame, **kwargs)
        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                confidence = float(box.conf[0].item())
                detections.append(
                    Detection(
                        frame_id=frame_id,
                        timestamp_s=timestamp_s,
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                    )
                )
        return detections
