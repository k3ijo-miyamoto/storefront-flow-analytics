from __future__ import annotations

from dataclasses import dataclass

from mallflow.behavior.speed import segment_speeds
from mallflow.behavior.state_machine import BehaviorState, TrackStateMachine
from mallflow.geometry.line_crossing import LineSegment, crossed_from_outside_to_inside
from mallflow.geometry.roi import PolygonROI
from mallflow.tracking.base import Track


@dataclass(frozen=True)
class BehaviorThresholds:
    min_track_duration_s: float = 0.5
    slowdown_speed_threshold_px_s: float = 60.0
    stop_speed_threshold_px_s: float = 30.0
    stop_duration_threshold_s: float = 1.5
    entrance_min_inside_points: int = 2


@dataclass(frozen=True)
class TrackBehavior:
    track_id: int
    first_seen_s: float
    last_seen_s: float
    track_duration_s: float
    state: BehaviorState
    passerby: bool
    exposed: bool
    slowed: bool
    stopped: bool
    entered: bool
    interest_dwell_s: float
    stop_duration_s: float
    direction: str
    entry_timestamp_s: float | None
    tracking_confidence: float


def evaluate_track(
    track: Track,
    traffic_roi: PolygonROI,
    interest_roi: PolygonROI,
    entrance_line: LineSegment | None = None,
    entrance_outside_side: float | None = None,
    thresholds: BehaviorThresholds | None = None,
    entrance_roi: PolygonROI | None = None,
) -> TrackBehavior:
    thresholds = thresholds or BehaviorThresholds()
    machine = TrackStateMachine()

    passerby = track.duration_s >= thresholds.min_track_duration_s and any(
        traffic_roi.contains(point.point) for point in track.points
    )
    if passerby:
        machine.mark_passerby()

    exposed = any(interest_roi.contains(point.point) for point in track.points)
    if exposed:
        machine.mark_exposed()

    interest_dwell_s = _duration_inside(track, interest_roi)
    stop_duration_s = _continuous_slow_duration(
        track,
        interest_roi,
        speed_threshold_px_s=thresholds.stop_speed_threshold_px_s,
    )

    slowed = any(
        speed < thresholds.slowdown_speed_threshold_px_s
        and interest_roi.contains(_point_at_timestamp(track, timestamp))
        for timestamp, speed in segment_speeds(track.points)
    )
    if slowed:
        machine.mark_slowed()

    stopped = stop_duration_s >= thresholds.stop_duration_threshold_s
    if stopped:
        machine.mark_stopped()

    if entrance_roi is not None:
        entry_timestamp_s = _entry_timestamp_by_roi(track, entrance_roi, thresholds.entrance_min_inside_points)
    elif entrance_line is not None and entrance_outside_side is not None:
        entry_timestamp_s = _entry_timestamp(track, entrance_line, entrance_outside_side)
    else:
        entry_timestamp_s = None
    entered = entry_timestamp_s is not None and (passerby or exposed)
    if entered:
        machine.mark_entered()

    return TrackBehavior(
        track_id=track.track_id,
        first_seen_s=track.first_seen_s,
        last_seen_s=track.last_seen_s,
        track_duration_s=track.duration_s,
        state=machine.state,
        passerby=passerby,
        exposed=exposed,
        slowed=slowed,
        stopped=stopped,
        entered=entered,
        interest_dwell_s=interest_dwell_s,
        stop_duration_s=stop_duration_s,
        direction=_direction(track),
        entry_timestamp_s=entry_timestamp_s,
        tracking_confidence=_mean_confidence(track),
    )


def _duration_inside(track: Track, roi: PolygonROI) -> float:
    duration = 0.0
    for previous, current in zip(track.points, track.points[1:]):
        if roi.contains(previous.point) and roi.contains(current.point):
            duration += max(0.0, current.timestamp_s - previous.timestamp_s)
    return duration


def _continuous_slow_duration(track: Track, roi: PolygonROI, speed_threshold_px_s: float) -> float:
    longest = 0.0
    current_run = 0.0
    for previous, current in zip(track.points, track.points[1:]):
        dt = current.timestamp_s - previous.timestamp_s
        if dt <= 0:
            continue
        dx = current.point[0] - previous.point[0]
        dy = current.point[1] - previous.point[1]
        speed = (dx * dx + dy * dy) ** 0.5 / dt
        if roi.contains(previous.point) and roi.contains(current.point) and speed < speed_threshold_px_s:
            current_run += dt
            longest = max(longest, current_run)
        else:
            current_run = 0.0
    return longest


def _entry_timestamp(track: Track, entrance_line: LineSegment, outside_side: float) -> float | None:
    for previous, current in zip(track.points, track.points[1:]):
        if crossed_from_outside_to_inside(previous.point, current.point, entrance_line, outside_side):
            return current.timestamp_s
    return None


def _entry_timestamp_by_roi(track: Track, entrance_roi: PolygonROI, min_inside_points: int = 2) -> float | None:
    was_outside = False
    for index, point in enumerate(track.points):
        inside = entrance_roi.contains(point.point)
        if inside and was_outside:
            inside_points = sum(1 for candidate in track.points[index:] if entrance_roi.contains(candidate.point))
            if inside_points >= min_inside_points:
                return point.timestamp_s
            return None
        if not inside:
            was_outside = True
    return None


def _direction(track: Track) -> str:
    if len(track.points) < 2:
        return "OTHER"
    dx = track.points[-1].point[0] - track.points[0].point[0]
    dy = track.points[-1].point[1] - track.points[0].point[1]
    if abs(dx) < abs(dy) or abs(dx) < 1e-9:
        return "OTHER"
    return "LEFT_TO_RIGHT" if dx > 0 else "RIGHT_TO_LEFT"


def _mean_confidence(track: Track) -> float:
    if not track.points:
        return 0.0
    return sum(point.confidence for point in track.points) / len(track.points)


def _point_at_timestamp(track: Track, timestamp_s: float) -> tuple[float, float]:
    for point in track.points:
        if point.timestamp_s == timestamp_s:
            return point.point
    return track.points[-1].point
