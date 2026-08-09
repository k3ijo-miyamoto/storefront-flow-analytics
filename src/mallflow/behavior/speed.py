from __future__ import annotations

import math
from collections.abc import Sequence

from mallflow.tracking.base import TrackPoint


def segment_speeds(points: Sequence[TrackPoint]) -> list[tuple[float, float]]:
    """Return speed samples as (timestamp_s, px_per_s) for each segment end."""
    speeds: list[tuple[float, float]] = []
    for previous, current in zip(points, points[1:]):
        dt = current.timestamp_s - previous.timestamp_s
        if dt <= 0:
            continue
        dx = current.point[0] - previous.point[0]
        dy = current.point[1] - previous.point[1]
        speeds.append((current.timestamp_s, math.hypot(dx, dy) / dt))
    return speeds
