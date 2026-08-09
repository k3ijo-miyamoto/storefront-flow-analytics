from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Any

import yaml

from mallflow.geometry.roi import PolygonROI


@dataclass(frozen=True)
class FacadeZoneSummary:
    zone: str
    exposed_count: int
    slowed_count: int
    stopped_count: int
    entered_after_exposure_count: int
    first_touch_entry_count: int
    last_touch_entry_count: int
    exposure_to_entry_rate: float
    first_touch_entry_rate: float
    last_touch_entry_rate: float
    dwell_median_s: float
    median_time_to_entry_s: float | None


def summarize_facade_zones(
    config_path: str,
    tracks_path: str,
    track_points_path: str,
    output_path: str,
) -> Path:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    zones = load_facade_zones(config)
    track_rows = load_track_rows(tracks_path)
    track_points = load_track_points(track_points_path)
    summaries = [summarize_zone(zone, track_rows, track_points) for zone in zones]
    first_touch_entries, last_touch_entries = assign_entry_touches(zones, track_rows, track_points)
    summaries = [
        replace_entry_touch_counts(summary, first_touch_entries, last_touch_entries)
        for summary in summaries
    ]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() in {".yaml", ".yml"}:
        payload = {
            "store_id": config["store_id"],
            "facade_zones": [asdict(summary) for summary in summaries],
        }
        output.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    else:
        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(asdict(summaries[0]).keys()))
            writer.writeheader()
            for summary in summaries:
                writer.writerow(asdict(summary))
    return output


def load_facade_zones(config: dict[str, Any]) -> list[PolygonROI]:
    raw_zones = config.get("facade_zones") or []
    if not raw_zones:
        raise ValueError("Config is missing facade_zones.")
    return [
        PolygonROI(str(zone["name"]), tuple(tuple(point) for point in zone["points"]))
        for zone in raw_zones
    ]


def load_track_rows(tracks_path: str) -> dict[int, dict[str, str]]:
    rows = {}
    with Path(tracks_path).open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            rows[int(row["track_id"])] = row
    return rows


def load_track_points(track_points_path: str) -> dict[int, list[dict[str, float]]]:
    points: dict[int, list[dict[str, float]]] = {}
    with Path(track_points_path).open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            track_id = int(row["track_id"])
            points.setdefault(track_id, []).append(
                {
                    "timestamp_s": float(row["timestamp_s"]),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                }
            )
    for values in points.values():
        values.sort(key=lambda point: point["timestamp_s"])
    return points


def summarize_zone(
    zone: PolygonROI,
    track_rows: dict[int, dict[str, str]],
    track_points: dict[int, list[dict[str, float]]],
) -> FacadeZoneSummary:
    exposed_track_ids = []
    slowed = 0
    stopped = 0
    entered_after_exposure = 0
    dwell_values = []
    time_to_entry_values = []

    for track_id, points in track_points.items():
        zone_points = [point for point in points if zone.contains((point["x"], point["y"]))]
        if not zone_points:
            continue
        row = track_rows.get(track_id)
        if row is None:
            continue

        exposed_track_ids.append(track_id)
        if row["slowed"] == "1":
            slowed += 1
        if row["stopped"] == "1":
            stopped += 1
        dwell_values.append(zone_dwell_s(zone, points))

        entry_timestamp = parse_optional_float(row["entry_timestamp_s"])
        first_exposure = zone_points[0]["timestamp_s"]
        if row["entered"] == "1" and entry_timestamp is not None and first_exposure <= entry_timestamp:
            entered_after_exposure += 1
            time_to_entry_values.append(max(0.0, entry_timestamp - first_exposure))

    exposed_count = len(exposed_track_ids)
    return FacadeZoneSummary(
        zone=zone.name,
        exposed_count=exposed_count,
        slowed_count=slowed,
        stopped_count=stopped,
        entered_after_exposure_count=entered_after_exposure,
        first_touch_entry_count=0,
        last_touch_entry_count=0,
        exposure_to_entry_rate=entered_after_exposure / exposed_count if exposed_count else 0.0,
        first_touch_entry_rate=0.0,
        last_touch_entry_rate=0.0,
        dwell_median_s=median(dwell_values) if dwell_values else 0.0,
        median_time_to_entry_s=median(time_to_entry_values) if time_to_entry_values else None,
    )


def assign_entry_touches(
    zones: list[PolygonROI],
    track_rows: dict[int, dict[str, str]],
    track_points: dict[int, list[dict[str, float]]],
) -> tuple[dict[str, int], dict[str, int]]:
    first_touch_counts = {zone.name: 0 for zone in zones}
    last_touch_counts = {zone.name: 0 for zone in zones}

    for track_id, row in track_rows.items():
        if row["entered"] != "1":
            continue
        entry_timestamp = parse_optional_float(row["entry_timestamp_s"])
        if entry_timestamp is None:
            continue
        touches = zone_touches_before_entry(zones, track_points.get(track_id, []), entry_timestamp)
        if not touches:
            continue
        first_touch_counts[touches[0][1]] += 1
        last_touch_counts[touches[-1][1]] += 1

    return first_touch_counts, last_touch_counts


def zone_touches_before_entry(
    zones: list[PolygonROI],
    points: list[dict[str, float]],
    entry_timestamp: float,
) -> list[tuple[float, str]]:
    touches = []
    seen = set()
    for point in points:
        timestamp = point["timestamp_s"]
        if timestamp > entry_timestamp:
            break
        for zone in zones:
            if zone.name in seen:
                continue
            if zone.contains((point["x"], point["y"])):
                touches.append((timestamp, zone.name))
                seen.add(zone.name)
                break
    return touches


def replace_entry_touch_counts(
    summary: FacadeZoneSummary,
    first_touch_entries: dict[str, int],
    last_touch_entries: dict[str, int],
) -> FacadeZoneSummary:
    first_count = first_touch_entries[summary.zone]
    last_count = last_touch_entries[summary.zone]
    return FacadeZoneSummary(
        zone=summary.zone,
        exposed_count=summary.exposed_count,
        slowed_count=summary.slowed_count,
        stopped_count=summary.stopped_count,
        entered_after_exposure_count=summary.entered_after_exposure_count,
        first_touch_entry_count=first_count,
        last_touch_entry_count=last_count,
        exposure_to_entry_rate=summary.exposure_to_entry_rate,
        first_touch_entry_rate=first_count / summary.exposed_count if summary.exposed_count else 0.0,
        last_touch_entry_rate=last_count / summary.exposed_count if summary.exposed_count else 0.0,
        dwell_median_s=summary.dwell_median_s,
        median_time_to_entry_s=summary.median_time_to_entry_s,
    )


def zone_dwell_s(zone: PolygonROI, points: list[dict[str, float]]) -> float:
    duration = 0.0
    for previous, current in zip(points, points[1:]):
        if zone.contains((previous["x"], previous["y"])) and zone.contains((current["x"], current["y"])):
            duration += max(0.0, current["timestamp_s"] - previous["timestamp_s"])
    return duration


def parse_optional_float(value: str) -> float | None:
    if value == "":
        return None
    return float(value)
