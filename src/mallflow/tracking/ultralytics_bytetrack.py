from __future__ import annotations

from pathlib import Path

from mallflow.tracking.base import Track, TrackPoint


def run_ultralytics_bytetrack(
    video_path: str,
    model_path: str,
    image_size: int,
    confidence_threshold: float,
    sample_fps: float,
    tracker_config: str = "bytetrack.yaml",
    device: str | None = None,
    start_s: float | None = None,
    end_s: float | None = None,
    max_frames: int | None = None,
) -> tuple[list[Track], float]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for video tracking.") from exc
    from ultralytics import YOLO

    if not Path(model_path).exists():
        raise RuntimeError(f"YOLO model does not exist: {model_path}")

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration_s = frame_count / fps if fps else 0.0
    frame_step = max(1, round(fps / sample_fps)) if sample_fps > 0 else 1
    start_frame = max(0, round((start_s or 0.0) * fps))
    end_frame = round(end_s * fps) if end_s is not None else None
    if start_frame:
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    model = YOLO(model_path)
    tracks: dict[int, Track] = {}
    frame_id = start_frame
    processed = 0

    while True:
        if end_frame is not None and frame_id > end_frame:
            break
        ok, frame = capture.read()
        if not ok:
            break
        if frame_id % frame_step != 0:
            frame_id += 1
            continue

        timestamp_s = frame_id / fps
        result = model.track(
            frame,
            persist=True,
            tracker=tracker_config,
            classes=[0],
            imgsz=image_size,
            conf=confidence_threshold,
            device=device,
            verbose=False,
        )[0]
        boxes = result.boxes
        if boxes is not None and boxes.id is not None:
            for box, track_id_value in zip(boxes, boxes.id.int().tolist()):
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                confidence = float(box.conf[0].item())
                track_id = int(track_id_value)
                track = tracks.setdefault(track_id, Track(track_id=track_id))
                track.append(
                    TrackPoint(
                        frame_id=frame_id,
                        timestamp_s=timestamp_s,
                        point=((x1 + x2) / 2.0, y2),
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                    )
                )

        processed += 1
        if max_frames is not None and processed >= max_frames:
            break
        frame_id += 1

    capture.release()
    return sorted(tracks.values(), key=lambda track: track.track_id), duration_s
