from __future__ import annotations

from pathlib import Path
from typing import Any


def stabilize_video(
    input_path: str,
    output_path: str,
    reference_time_s: float = 54.0,
    start_s: float = 0.0,
    end_s: float | None = None,
    output_fps: float = 10.0,
    width: int = 1280,
    feature_width: int = 960,
    max_features: int = 3000,
    match_keep_ratio: float = 0.25,
    side_by_side: bool = False,
) -> Path:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("OpenCV and NumPy are required for video stabilization.") from exc

    capture = cv2.VideoCapture(input_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {input_path}")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_size = scaled_size(source_width, source_height, width)
    writer_size = (output_size[0] * 2, output_size[1]) if side_by_side else output_size
    frame_step = max(1, round(source_fps / output_fps))

    reference = read_frame_at(capture, reference_time_s, source_fps)
    if reference is None:
        capture.release()
        raise RuntimeError(f"Could not read reference frame at {reference_time_s}s")
    reference_gray, reference_scale = prepare_gray(reference, feature_width, cv2)
    detector = cv2.ORB_create(nfeatures=max_features)
    reference_keypoints, reference_descriptors = detector.detectAndCompute(reference_gray, None)
    if reference_descriptors is None or not reference_keypoints:
        capture.release()
        raise RuntimeError("Could not find enough reference features for stabilization.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        writer_size,
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create video writer: {output_path}")

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    identity = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    previous_transform = identity

    start_frame = max(0, round(start_s * source_fps))
    end_frame = round(end_s * source_fps) if end_s is not None else int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0) - 1
    end_frame = max(start_frame, end_frame)
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_id = start_frame
    while frame_id <= end_frame:
        ok, frame = capture.read()
        if not ok:
            break
        if (frame_id - start_frame) % frame_step == 0:
            gray, current_scale = prepare_gray(frame, feature_width, cv2)
            transform = estimate_transform_to_reference(
                gray,
                current_scale,
                detector,
                matcher,
                reference_keypoints,
                reference_descriptors,
                reference_scale,
                source_width,
                source_height,
                previous_transform,
                cv2,
                np,
                match_keep_ratio,
            )
            previous_transform = transform
            stabilized = cv2.warpAffine(
                frame,
                transform,
                (source_width, source_height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
            timestamp_s = frame_id / source_fps
            cv2.putText(
                stabilized,
                f"stabilized {timestamp_s:.1f}s",
                (24, source_height - 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                3,
            )
            stabilized = cv2.resize(stabilized, output_size, interpolation=cv2.INTER_AREA)
            if side_by_side:
                original = cv2.resize(frame, output_size, interpolation=cv2.INTER_AREA)
                cv2.putText(original, "original", (24, output_size[1] - 28), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                writer.write(cv2.hconcat([original, stabilized]))
            else:
                writer.write(stabilized)
        frame_id += 1

    writer.release()
    capture.release()
    return output


def read_frame_at(capture: Any, timestamp_s: float, fps: float) -> Any | None:
    capture.set(1, max(0, round(timestamp_s * fps)))
    ok, frame = capture.read()
    return frame if ok else None


def prepare_gray(frame: Any, target_width: int, cv2: Any) -> tuple[Any, float]:
    height, width = frame.shape[:2]
    if target_width > 0 and width > target_width:
        scale = target_width / width
        frame = cv2.resize(frame, (target_width, max(1, round(height * scale))), interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray, scale


def estimate_transform_to_reference(
    current_gray: Any,
    current_scale: float,
    detector: Any,
    matcher: Any,
    reference_keypoints: list[Any],
    reference_descriptors: Any,
    reference_scale: float,
    source_width: int,
    source_height: int,
    fallback_transform: Any,
    cv2: Any,
    np: Any,
    match_keep_ratio: float,
) -> Any:
    current_keypoints, current_descriptors = detector.detectAndCompute(current_gray, None)
    if current_descriptors is None or not current_keypoints:
        return fallback_transform

    matches = sorted(matcher.match(current_descriptors, reference_descriptors), key=lambda match: match.distance)
    keep = max(12, round(len(matches) * match_keep_ratio))
    matches = matches[:keep]
    if len(matches) < 6:
        return fallback_transform

    current_points = np.float32([current_keypoints[match.queryIdx].pt for match in matches])
    reference_points = np.float32([reference_keypoints[match.trainIdx].pt for match in matches])
    current_points /= current_scale
    reference_points /= reference_scale

    transform, inliers = cv2.estimateAffinePartial2D(
        current_points,
        reference_points,
        method=cv2.RANSAC,
        ransacReprojThreshold=max(source_width, source_height) * 0.01,
    )
    if transform is None or inliers is None or int(inliers.sum()) < 6:
        return fallback_transform
    return transform.astype(np.float32)


def scaled_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    if target_width <= 0 or width <= target_width:
        return (width, height)
    ratio = target_width / width
    return (target_width, max(1, round(height * ratio)))
