from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DebugTrackSample:
    track_id: int
    timestamp_s: float
    point: tuple[int, int]
    bbox: tuple[int, int, int, int] | None
    confidence: float


@dataclass(frozen=True)
class EntryEvent:
    track_id: int
    timestamp_s: float


def save_debug_frame(config_path: str, timestamp_s: float, output_path: str) -> Path:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for debug frame rendering.") from exc

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    video_path = str(config["video_path"])
    capture = cv2.VideoCapture(video_path)
    capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)
    ok, frame = capture.read()
    capture.release()
    if not ok or frame is None:
        raise RuntimeError(f"Could not read frame at {timestamp_s}s from {video_path}")

    draw_privacy_masks(frame, config, cv2)
    draw_config_overlay(frame, config, cv2)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), frame)
    return output


def save_track_debug_frame(
    config_path: str,
    track_points_path: str,
    timestamp_s: float,
    output_path: str,
    window_s: float = 8.0,
) -> Path:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for debug frame rendering.") from exc

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    video_path = str(config["video_path"])
    capture = cv2.VideoCapture(video_path)
    capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)
    ok, frame = capture.read()
    capture.release()
    if not ok or frame is None:
        raise RuntimeError(f"Could not read frame at {timestamp_s}s from {video_path}")

    samples = load_debug_track_samples(track_points_path)
    draw_privacy_masks(frame, config, cv2)
    draw_config_overlay(frame, config, cv2)
    draw_track_points_from_samples(frame, samples, timestamp_s, window_s, cv2)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), frame)
    return output


def save_track_debug_video(
    config_path: str,
    track_points_path: str,
    start_s: float,
    end_s: float,
    output_path: str,
    trail_s: float = 6.0,
    output_fps: float = 12.0,
    width: int = 1280,
    draw_boxes: bool = False,
    tracks_path: str | None = None,
) -> Path:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for debug video rendering.") from exc

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    video_path = str(config["video_path"])
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_size = scaled_size(source_width, source_height, width)
    frame_step = max(1, round(source_fps / output_fps))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        output_size,
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create video writer: {output_path}")

    start_frame = max(0, round(start_s * source_fps))
    end_frame = max(start_frame, round(end_s * source_fps))
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    samples = load_debug_track_samples(track_points_path)
    entry_events = load_entry_events(tracks_path) if tracks_path else []

    frame_id = start_frame
    while frame_id <= end_frame:
        ok, frame = capture.read()
        if not ok:
            break
        if (frame_id - start_frame) % frame_step == 0:
            timestamp_s = frame_id / source_fps
            draw_privacy_masks(frame, config, cv2)
            draw_config_overlay(frame, config, cv2)
            draw_track_points_from_samples(frame, samples, timestamp_s, trail_s, cv2)
            if draw_boxes:
                draw_current_boxes_from_samples(frame, samples, timestamp_s, source_fps / frame_step, cv2)
            if entry_events:
                draw_entry_counter(frame, entry_events, timestamp_s, cv2)
            cv2.putText(
                frame,
                f"{timestamp_s:.1f}s",
                (24, frame.shape[0] - 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                3,
            )
            frame = cv2.resize(frame, output_size, interpolation=cv2.INTER_AREA)
            writer.write(frame)
        frame_id += 1

    writer.release()
    capture.release()
    return output


def draw_config_overlay(frame: Any, config: dict[str, Any], cv2: Any) -> None:
    draw_polygon(frame, config["traffic_roi"], (46, 204, 113), cv2, "Traffic ROI")
    draw_polygon(frame, config["interest_roi"], (52, 152, 219), cv2, "Interest ROI")
    for zone in config.get("facade_zones", []):
        draw_polygon(frame, zone["points"], (255, 0, 255), cv2, f"Zone: {zone['name']}")
    if config.get("entrance_roi"):
        draw_polygon(frame, config["entrance_roi"], (0, 0, 255), cv2, "Entrance ROI")
    else:
        p1, p2 = [tuple(point) for point in config["entrance_line"]]
        cv2.line(frame, p1, p2, (0, 0, 255), 4)
        cv2.putText(frame, "Entrance Line", p1, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        outside = tuple(config["entrance_outside_reference_point"])
        cv2.circle(frame, outside, 9, (0, 255, 255), -1)
        cv2.putText(frame, "Outside", (outside[0] + 12, outside[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)


def draw_privacy_masks(frame: Any, config: dict[str, Any], cv2: Any) -> None:
    for mask in config.get("privacy_masks", []):
        points = mask.get("points")
        if not points:
            continue
        color = tuple(mask.get("color", [32, 32, 32]))
        draw_filled_polygon(frame, points, color, cv2)


def draw_filled_polygon(frame: Any, points: list[list[int]], color: tuple[int, int, int], cv2: Any) -> None:
    import numpy as np

    polygon = np.array([[tuple(point) for point in points]], dtype=np.int32)
    cv2.fillPoly(frame, polygon, color)


def draw_polygon(frame: Any, points: list[list[int]], color: tuple[int, int, int], cv2: Any, label: str) -> None:
    tuples = [tuple(point) for point in points]
    for start, end in zip(tuples, tuples[1:] + tuples[:1]):
        cv2.line(frame, start, end, color, 3)
    if tuples:
        cv2.putText(frame, label, tuples[0], cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def load_debug_track_samples(track_points_path: str) -> list[DebugTrackSample]:
    samples = []
    with Path(track_points_path).open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            bbox = None
            if row["bbox_x1"]:
                bbox = (
                    round(float(row["bbox_x1"])),
                    round(float(row["bbox_y1"])),
                    round(float(row["bbox_x2"])),
                    round(float(row["bbox_y2"])),
                )
            samples.append(
                DebugTrackSample(
                    track_id=int(row["track_id"]),
                    timestamp_s=float(row["timestamp_s"]),
                    point=(round(float(row["x"])), round(float(row["y"]))),
                    bbox=bbox,
                    confidence=float(row["confidence"]),
                )
            )
    return samples


def load_entry_events(tracks_path: str) -> list[EntryEvent]:
    events = []
    with Path(tracks_path).open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["entered"] != "1" or not row["entry_timestamp_s"]:
                continue
            events.append(EntryEvent(track_id=int(row["track_id"]), timestamp_s=float(row["entry_timestamp_s"])))
    events.sort(key=lambda event: event.timestamp_s)
    return events


def draw_entry_counter(frame: Any, entry_events: list[EntryEvent], timestamp_s: float, cv2: Any) -> None:
    count = sum(1 for event in entry_events if event.timestamp_s <= timestamp_s)
    total = len(entry_events)
    label = f"Entries: {count}/{total}"
    origin = (24, 44)
    cv2.rectangle(frame, (14, 10), (300, 88), (0, 0, 0), -1)
    cv2.putText(frame, label, origin, cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

    recent = [event for event in entry_events if 0 <= timestamp_s - event.timestamp_s <= 3.0]
    if recent:
        recent_ids = ", ".join(str(event.track_id) for event in recent[-3:])
        cv2.putText(
            frame,
            f"+{len(recent)} entry id {recent_ids}",
            (24, 78),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )


def draw_track_points(frame: Any, track_points_path: str, timestamp_s: float, window_s: float, cv2: Any) -> None:
    draw_track_points_from_samples(frame, load_debug_track_samples(track_points_path), timestamp_s, window_s, cv2)


def draw_track_points_from_samples(
    frame: Any,
    samples: list[DebugTrackSample],
    timestamp_s: float,
    window_s: float,
    cv2: Any,
) -> None:
    start_s = timestamp_s - window_s
    end_s = timestamp_s + window_s
    by_track: dict[int, list[tuple[float, tuple[int, int]]]] = {}
    for sample in samples:
        if start_s <= sample.timestamp_s <= end_s:
            by_track.setdefault(sample.track_id, []).append((sample.timestamp_s, sample.point))

    for track_id, samples in by_track.items():
        samples.sort()
        color = track_color(track_id)
        points = [point for _time, point in samples]
        for first, second in zip(points, points[1:]):
            cv2.line(frame, first, second, color, 2)
        if points:
            cv2.circle(frame, points[-1], 6, color, -1)
            cv2.putText(
                frame,
                str(track_id),
                (points[-1][0] + 8, points[-1][1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )


def draw_current_boxes(frame: Any, track_points_path: str, timestamp_s: float, output_fps: float, cv2: Any) -> None:
    draw_current_boxes_from_samples(frame, load_debug_track_samples(track_points_path), timestamp_s, output_fps, cv2)


def draw_current_boxes_from_samples(
    frame: Any,
    samples: list[DebugTrackSample],
    timestamp_s: float,
    output_fps: float,
    cv2: Any,
) -> None:
    tolerance_s = max(0.04, 0.55 / output_fps)
    for sample in samples:
        if abs(sample.timestamp_s - timestamp_s) > tolerance_s or sample.bbox is None:
            continue
        color = track_color(sample.track_id)
        x1, y1, x2, y2 = sample.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, sample.point, 5, (0, 255, 255), -1)
        cv2.putText(
            frame,
            f"id {sample.track_id} {sample.confidence:.2f}",
            (x1, max(22, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )


def track_color(track_id: int) -> tuple[int, int, int]:
    palette = [
        (255, 99, 71),
        (255, 215, 0),
        (64, 224, 208),
        (147, 112, 219),
        (50, 205, 50),
        (255, 140, 0),
        (30, 144, 255),
    ]
    return palette[track_id % len(palette)]


def scaled_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    if target_width <= 0 or width <= target_width:
        return (width, height)
    ratio = target_width / width
    return (target_width, max(1, round(height * ratio)))
