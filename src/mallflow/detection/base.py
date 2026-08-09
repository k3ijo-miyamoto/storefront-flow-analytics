from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Detection:
    frame_id: int
    timestamp_s: float
    bbox: BBox
    confidence: float
    class_name: str = "person"

    @property
    def foot_point(self) -> tuple[float, float]:
        x1, _y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, y2)


class PersonDetector(Protocol):
    """Interface for same-frame anonymous person detection."""

    def detect(self, frame: object, frame_id: int, timestamp_s: float) -> Sequence[Detection]:
        """Return person detections for a frame."""
