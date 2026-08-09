from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from mallflow.behavior.events import TrackBehavior


@dataclass(frozen=True)
class StoreMetrics:
    store_id: str
    video_duration_s: float
    unique_tracks: int
    passerby_count: int
    exposed_count: int
    slowdown_count: int
    stop_count: int
    entry_count: int
    traffic_rate_per_min: float
    exposure_rate: float
    stop_rate: float
    entry_rate: float
    stop_to_entry_conversion: float
    dwell_median_s: float
    dwell_p25_s: float
    dwell_p75_s: float


def summarize_store(store_id: str, video_duration_s: float, tracks: list[TrackBehavior]) -> StoreMetrics:
    passerby = [track for track in tracks if track.passerby]
    stopped = [track for track in tracks if track.stopped]
    dwell_values = sorted(track.interest_dwell_s for track in tracks if track.interest_dwell_s > 0)
    minutes = video_duration_s / 60.0 if video_duration_s > 0 else 0.0

    return StoreMetrics(
        store_id=store_id,
        video_duration_s=video_duration_s,
        unique_tracks=len(tracks),
        passerby_count=len(passerby),
        exposed_count=sum(1 for track in tracks if track.exposed),
        slowdown_count=sum(1 for track in tracks if track.slowed),
        stop_count=len(stopped),
        entry_count=sum(1 for track in tracks if track.entered),
        traffic_rate_per_min=_safe_div(len(passerby), minutes),
        exposure_rate=_safe_div(sum(1 for track in tracks if track.exposed), len(passerby)),
        stop_rate=_safe_div(len(stopped), len(passerby)),
        entry_rate=_safe_div(sum(1 for track in tracks if track.entered), len(passerby)),
        stop_to_entry_conversion=_safe_div(
            sum(1 for track in stopped if track.entered),
            len(stopped),
        ),
        dwell_median_s=median(dwell_values) if dwell_values else 0.0,
        dwell_p25_s=_percentile(dwell_values, 25),
        dwell_p75_s=_percentile(dwell_values, 75),
    )


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    weight = rank - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight
