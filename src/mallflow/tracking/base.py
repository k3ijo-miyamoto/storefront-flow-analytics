from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

from mallflow.detection.base import Detection


@dataclass(frozen=True)
class TrackPoint:
    frame_id: int
    timestamp_s: float
    point: tuple[float, float]
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 1.0


@dataclass
class Track:
    track_id: int
    points: list[TrackPoint] = field(default_factory=list)

    def append(self, point: TrackPoint) -> None:
        self.points.append(point)

    @property
    def first_seen_s(self) -> float:
        return self.points[0].timestamp_s

    @property
    def last_seen_s(self) -> float:
        return self.points[-1].timestamp_s

    @property
    def duration_s(self) -> float:
        if not self.points:
            return 0.0
        return max(0.0, self.last_seen_s - self.first_seen_s)


class PersonTracker(Protocol):
    """Interface for same-video anonymous multi-object tracking."""

    def update(self, detections: Sequence[Detection]) -> Sequence[Track]:
        """Update tracks from detections and return active tracks."""
