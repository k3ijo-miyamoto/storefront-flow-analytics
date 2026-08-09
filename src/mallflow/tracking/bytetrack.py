from __future__ import annotations

from collections.abc import Sequence

from mallflow.detection.base import Detection
from mallflow.tracking.base import PersonTracker, Track


class ByteTrackPersonTracker(PersonTracker):
    """Adapter placeholder for a future ByteTrack backend."""

    def update(self, detections: Sequence[Detection]) -> Sequence[Track]:
        raise NotImplementedError("ByteTrack backend is planned for Phase 2.")
