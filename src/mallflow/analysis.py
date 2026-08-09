from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from mallflow.analytics.metrics import summarize_store
from mallflow.behavior.events import BehaviorThresholds, TrackBehavior, evaluate_track
from mallflow.detection.detector import OpenCVHogPersonDetector, UltralyticsPersonDetector
from mallflow.geometry.line_crossing import LineSegment
from mallflow.geometry.roi import PolygonROI
from mallflow.tracking.centroid import CentroidPersonTracker
from mallflow.tracking.base import Track
from mallflow.tracking.ultralytics_bytetrack import run_ultralytics_bytetrack


TRACK_COLUMNS = [
    "video_id",
    "store_id",
    "track_id",
    "first_seen_s",
    "last_seen_s",
    "track_duration_s",
    "passerby",
    "exposed",
    "slowed",
    "stopped",
    "entered",
    "interest_dwell_s",
    "stop_duration_s",
    "direction",
    "entry_timestamp_s",
    "tracking_confidence",
]

TRACK_POINT_COLUMNS = [
    "video_id",
    "store_id",
    "track_id",
    "frame_id",
    "timestamp_s",
    "x",
    "y",
    "bbox_x1",
    "bbox_y1",
    "bbox_x2",
    "bbox_y2",
    "confidence",
]


def analyze_video(
    config_path: str,
    output_dir: str = "outputs",
    sample_fps: float = 1.0,
    detector_width: int = 960,
    detector_backend: str = "hog",
    tracker_backend: str = "centroid",
    model_path: str | None = None,
    confidence_threshold: float = 0.25,
    tracker_config: str = "bytetrack.yaml",
    device: str | None = None,
    start_s: float | None = None,
    end_s: float | None = None,
    max_frames: int | None = None,
) -> dict[str, Path]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for analysis.") from exc

    config = load_config(config_path)
    video_path = str(config["video_path"])
    store_id = str(config["store_id"])
    video_id = Path(video_path).stem

    if tracker_backend == "bytetrack":
        if detector_backend != "yolo":
            raise ValueError("--tracker bytetrack requires --detector yolo.")
        if not model_path:
            raise ValueError("--model is required when --tracker bytetrack is used.")
        tracks, video_duration_s = run_ultralytics_bytetrack(
            video_path=video_path,
            model_path=model_path,
            image_size=detector_width,
            confidence_threshold=confidence_threshold,
            sample_fps=sample_fps,
            tracker_config=tracker_config,
            device=device,
            start_s=start_s,
            end_s=end_s,
            max_frames=max_frames,
        )
        behaviors = evaluate_tracks(config, tracks)
        outputs = write_outputs(output_dir, video_id, store_id, video_duration_s, behaviors, tracks)
        outputs["config"] = Path(config_path)
        return outputs

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    video_duration_s = frame_count / fps if fps else 0.0
    frame_step = max(1, round(fps / sample_fps)) if sample_fps > 0 else 1
    start_frame = max(0, round((start_s or 0.0) * fps))
    end_frame = round(end_s * fps) if end_s is not None else None
    if start_frame:
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    detector = make_detector(detector_backend, detector_width, model_path, confidence_threshold)
    tracker = CentroidPersonTracker(max_distance_px=180.0, max_missing=max(2, round(sample_fps * 4)))

    frame_id = start_frame
    processed = 0
    while True:
        if end_frame is not None and frame_id > end_frame:
            break
        ok, frame = capture.read()
        if not ok:
            break
        if frame_id % frame_step == 0:
            timestamp_s = frame_id / fps
            detections = detector.detect(frame, frame_id, timestamp_s)
            tracker.update(detections)
            processed += 1
            if max_frames is not None and processed >= max_frames:
                break
        frame_id += 1

    capture.release()

    behaviors = evaluate_tracks(config, tracker.all_tracks())
    outputs = write_outputs(output_dir, video_id, store_id, video_duration_s, behaviors, tracker.all_tracks())
    outputs["config"] = Path(config_path)
    return outputs


def make_detector(
    detector_backend: str,
    detector_width: int,
    model_path: str | None,
    confidence_threshold: float,
):
    if detector_backend == "hog":
        return OpenCVHogPersonDetector(max_width=detector_width)
    if detector_backend == "yolo":
        if not model_path:
            raise ValueError("--model is required when --detector yolo is used.")
        return UltralyticsPersonDetector(
            model_path=model_path,
            image_size=detector_width,
            confidence_threshold=confidence_threshold,
        )
    raise ValueError(f"Unsupported detector backend: {detector_backend}")


def load_config(config_path: str) -> dict[str, Any]:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    required = [
        "store_id",
        "video_path",
        "traffic_roi",
        "interest_roi",
    ]
    missing = [key for key in required if key not in config or config[key] in (None, [])]
    if not config.get("entrance_roi"):
        for key in ["entrance_line", "entrance_outside_reference_point"]:
            if key not in config or config[key] in (None, []):
                missing.append(key)
    if missing:
        raise ValueError(f"Config is missing required values: {', '.join(missing)}")
    return config


def evaluate_tracks(config: dict[str, Any], tracks: list[Any]) -> list[TrackBehavior]:
    traffic_roi = PolygonROI("traffic", tuple(tuple(point) for point in config["traffic_roi"]))
    interest_roi = PolygonROI("interest", tuple(tuple(point) for point in config["interest_roi"]))
    entrance_roi = None
    entrance_line = None
    outside_side = None
    if config.get("entrance_roi"):
        entrance_roi = PolygonROI("entrance", tuple(tuple(point) for point in config["entrance_roi"]))
    else:
        entrance_line = LineSegment(tuple(config["entrance_line"][0]), tuple(config["entrance_line"][1]))
        outside_side = entrance_line.side(tuple(config["entrance_outside_reference_point"]))
    thresholds = BehaviorThresholds(**config.get("thresholds", {}))

    return [
        evaluate_track(
            track,
            traffic_roi,
            interest_roi,
            entrance_line,
            outside_side,
            thresholds,
            entrance_roi,
        )
        for track in tracks
        if len(track.points) >= 2
    ]


def write_outputs(
    output_dir: str,
    video_id: str,
    store_id: str,
    video_duration_s: float,
    behaviors: list[TrackBehavior],
    tracks: list[Track],
) -> dict[str, Path]:
    root = Path(output_dir)
    tracks_dir = root / "tracks"
    metrics_dir = root / "metrics"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    safe_store = store_id.lower().replace("'", "").replace(" ", "_")
    tracks_path = tracks_dir / f"{safe_store}_tracks.csv"
    track_points_path = tracks_dir / f"{safe_store}_track_points.csv"
    metrics_path = metrics_dir / f"{safe_store}_metrics.yaml"

    with tracks_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRACK_COLUMNS)
        writer.writeheader()
        for behavior in behaviors:
            writer.writerow(track_row(video_id, store_id, behavior))

    with track_points_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRACK_POINT_COLUMNS)
        writer.writeheader()
        for track in tracks:
            for point in track.points:
                writer.writerow(track_point_row(video_id, store_id, track.track_id, point))

    metrics = summarize_store(store_id, video_duration_s, behaviors)
    metrics_path.write_text(yaml.safe_dump(asdict(metrics), sort_keys=False), encoding="utf-8")
    return {"tracks": tracks_path, "track_points": track_points_path, "metrics": metrics_path}


def track_row(video_id: str, store_id: str, behavior: TrackBehavior) -> dict[str, object]:
    return {
        "video_id": video_id,
        "store_id": store_id,
        "track_id": behavior.track_id,
        "first_seen_s": round(behavior.first_seen_s, 3),
        "last_seen_s": round(behavior.last_seen_s, 3),
        "track_duration_s": round(behavior.track_duration_s, 3),
        "passerby": int(behavior.passerby),
        "exposed": int(behavior.exposed),
        "slowed": int(behavior.slowed),
        "stopped": int(behavior.stopped),
        "entered": int(behavior.entered),
        "interest_dwell_s": round(behavior.interest_dwell_s, 3),
        "stop_duration_s": round(behavior.stop_duration_s, 3),
        "direction": behavior.direction,
        "entry_timestamp_s": "" if behavior.entry_timestamp_s is None else round(behavior.entry_timestamp_s, 3),
        "tracking_confidence": round(behavior.tracking_confidence, 3),
    }


def track_point_row(video_id: str, store_id: str, track_id: int, point: Any) -> dict[str, object]:
    bbox = point.bbox or ("", "", "", "")
    return {
        "video_id": video_id,
        "store_id": store_id,
        "track_id": track_id,
        "frame_id": point.frame_id,
        "timestamp_s": round(point.timestamp_s, 3),
        "x": round(point.point[0], 3),
        "y": round(point.point[1], 3),
        "bbox_x1": "" if bbox[0] == "" else round(bbox[0], 3),
        "bbox_y1": "" if bbox[1] == "" else round(bbox[1], 3),
        "bbox_x2": "" if bbox[2] == "" else round(bbox[2], 3),
        "bbox_y2": "" if bbox[3] == "" else round(bbox[3], 3),
        "confidence": round(point.confidence, 3),
    }
