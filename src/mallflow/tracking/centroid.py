from __future__ import annotations

import math
from collections.abc import Sequence

from mallflow.detection.base import Detection
from mallflow.tracking.base import PersonTracker, Track, TrackPoint


class CentroidPersonTracker(PersonTracker):
    """Simple same-video anonymous tracker based on foot-point distance."""

    def __init__(self, max_distance_px: float = 160.0, max_missing: int = 8) -> None:
        self._max_distance_px = max_distance_px
        self._max_missing = max_missing
        self._next_track_id = 1
        self._tracks: dict[int, Track] = {}
        self._missing: dict[int, int] = {}

    def update(self, detections: Sequence[Detection]) -> Sequence[Track]:
        active_track_ids = {
            track_id
            for track_id in self._tracks
            if self._missing.get(track_id, 0) <= self._max_missing
        }
        unmatched_tracks = set(active_track_ids)
        unmatched_detections = set(range(len(detections)))
        pairs: list[tuple[float, int, int]] = []

        for track_id in active_track_ids:
            track = self._tracks[track_id]
            if not track.points:
                continue
            last_point = track.points[-1].point
            for detection_index, detection in enumerate(detections):
                pairs.append((_distance(last_point, detection.foot_point), track_id, detection_index))

        for distance, track_id, detection_index in sorted(pairs):
            if distance > self._max_distance_px:
                continue
            if track_id not in unmatched_tracks or detection_index not in unmatched_detections:
                continue
            self._append_detection(track_id, detections[detection_index])
            unmatched_tracks.remove(track_id)
            unmatched_detections.remove(detection_index)

        for detection_index in sorted(unmatched_detections):
            self._start_track(detections[detection_index])

        for track_id in unmatched_tracks:
            self._missing[track_id] = self._missing.get(track_id, 0) + 1

        return [
            track
            for track_id, track in self._tracks.items()
            if self._missing.get(track_id, 0) <= self._max_missing
        ]

    def all_tracks(self) -> list[Track]:
        return sorted(self._tracks.values(), key=lambda track: track.track_id)

    def _start_track(self, detection: Detection) -> None:
        track_id = self._next_track_id
        self._next_track_id += 1
        self._tracks[track_id] = Track(track_id=track_id)
        self._append_detection(track_id, detection)

    def _append_detection(self, track_id: int, detection: Detection) -> None:
        self._tracks[track_id].append(
            TrackPoint(
                frame_id=detection.frame_id,
                timestamp_s=detection.timestamp_s,
                point=detection.foot_point,
                bbox=detection.bbox,
                confidence=detection.confidence,
            )
        )
        self._missing[track_id] = 0


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
