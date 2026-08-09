from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


Point = tuple[int, int]


@dataclass
class DisplayState:
    source_width: int
    source_height: int
    target_width: int

    @property
    def size(self) -> tuple[int, int]:
        return scaled_size(self.source_width, self.source_height, self.target_width)

    @property
    def scale_x(self) -> float:
        return self.source_width / self.size[0]

    @property
    def scale_y(self) -> float:
        return self.source_height / self.size[1]

    def zoom_in(self) -> None:
        self.target_width = min(round(self.target_width * 1.25), self.source_width)

    def zoom_out(self) -> None:
        self.target_width = max(round(self.target_width / 1.25), 360)


@dataclass
class AnnotationState:
    store_id: str
    video_path: str
    traffic_roi: list[Point] = field(default_factory=list)
    interest_roi: list[Point] = field(default_factory=list)
    entrance_roi: list[Point] = field(default_factory=list)
    entrance_line: list[Point] = field(default_factory=list)
    outside_reference_point: list[Point] = field(default_factory=list)
    step: str = "traffic_roi"
    message: str = ""
    entrance_mode: str = "roi"
    selected_steps: list[str] | None = None

    def active_points(self) -> list[Point]:
        if self.step == "traffic_roi":
            return self.traffic_roi
        if self.step == "interest_roi":
            return self.interest_roi
        if self.step == "entrance_roi":
            return self.entrance_roi
        if self.step == "entrance_line":
            return self.entrance_line
        return self.outside_reference_point

    def add_point(self, point: Point) -> None:
        points = self.active_points()
        if self.step in {"entrance_line", "outside_reference_point"} and len(points) >= point_limit(self.step):
            points.clear()
        points.append(point)
        self.message = step_progress_message(self.step, len(points))

    def undo(self) -> None:
        points = self.active_points()
        if points:
            points.pop()
        self.message = step_progress_message(self.step, len(points))

    def advance(self) -> None:
        if not step_is_complete(self.step, self.active_points()):
            self.message = f"{step_title(self.step)} needs {point_limit(self.step)} point(s) minimum."
            return
        steps = self.steps()
        index = steps.index(self.step)
        if index < len(steps) - 1:
            self.step = steps[index + 1]
            self.message = f"Now set {step_title(self.step)}."
        else:
            self.message = "All regions are ready. Press S to save."

    def back(self) -> None:
        steps = self.steps()
        index = steps.index(self.step)
        if index > 0:
            self.step = steps[index - 1]
            self.message = f"Back to {step_title(self.step)}. Use C to clear or click more points."

    def clear_current(self) -> None:
        self.active_points().clear()
        self.message = f"Cleared {step_title(self.step)}."

    def complete(self) -> bool:
        return all(step_is_complete(step, getattr(self, step)) for step in self.steps())

    def missing_steps(self) -> list[str]:
        return [step_title(step) for step in self.steps() if not step_is_complete(step, getattr(self, step))]

    def steps(self) -> list[str]:
        if self.selected_steps is not None:
            return self.selected_steps
        if self.entrance_mode == "line":
            return ["traffic_roi", "interest_roi", "entrance_line", "outside_reference_point"]
        return ["traffic_roi", "interest_roi", "entrance_roi"]

    def to_config(self, base_config: dict[str, Any] | None = None) -> dict[str, Any]:
        config = {
            "store_id": self.store_id,
            "video_path": self.video_path,
            "traffic_roi": points_to_lists(self.traffic_roi),
            "interest_roi": points_to_lists(self.interest_roi),
            "thresholds": {
                "min_track_duration_s": 0.5,
                "slowdown_speed_threshold_px_s": 60,
                "stop_speed_threshold_px_s": 30,
                "stop_duration_threshold_s": 1.5,
            },
        }
        if self.entrance_mode == "line":
            config["entrance_line"] = points_to_lists(self.entrance_line)
            config["entrance_outside_reference_point"] = list(self.outside_reference_point[0])
        else:
            config["entrance_roi"] = points_to_lists(self.entrance_roi)
        if base_config:
            merged = dict(base_config)
            merged.update(config)
            return merged
        return config


def run_roi_editor(
    video_path: str,
    store_id: str,
    output_path: str | None = None,
    display_width: int = 1400,
    frame_time_s: float = 0.0,
    entrance_mode: str = "roi",
    only: str | None = None,
) -> Path:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for ROI annotation. Install with: pip install '.[annotation]'"
        ) from exc

    output = Path(output_path or default_config_path(store_id))
    output.parent.mkdir(parents=True, exist_ok=True)
    base_config = load_existing_config(output)

    capture = cv2.VideoCapture(video_path)
    if frame_time_s > 0:
        capture.set(cv2.CAP_PROP_POS_MSEC, frame_time_s * 1000)
    ok, frame = capture.read()
    capture.release()
    if not ok or frame is None:
        raise RuntimeError(f"Could not read the first frame from: {video_path}")

    selected_steps = [only] if only else None
    state = AnnotationState(
        store_id=store_id,
        video_path=video_path,
        entrance_mode=entrance_mode,
        selected_steps=selected_steps,
    )
    if base_config:
        hydrate_state(state, base_config)
    if only:
        state.step = only
        getattr(state, only).clear()
        state.message = f"Now reset {step_title(only)}. Existing other regions will be preserved."
    window = f"mallflow annotate: {store_id}"
    display = DisplayState(frame.shape[1], frame.shape[0], display_width)

    def on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            state.add_point((round(x * display.scale_x), round(y * display.scale_y)))
        if event == cv2.EVENT_RBUTTONDOWN:
            state.undo()

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, display.size[0], display.size[1])
    cv2.setMouseCallback(window, on_mouse)

    while True:
        canvas = draw_annotation(frame.copy(), state, cv2)
        canvas = cv2.resize(canvas, display.size, interpolation=cv2.INTER_AREA)
        cv2.imshow(window, canvas)
        key = cv2.waitKey(30) & 0xFF

        if key in {ord("q"), 27}:
            cv2.destroyWindow(window)
            raise RuntimeError("Annotation cancelled.")
        if key in {ord("u"), ord("U"), 8, 127}:
            state.undo()
        if key in {ord("c"), ord("C")}:
            state.clear_current()
        if key in {ord("p"), ord("P")}:
            state.back()
        if key in {ord("+"), ord("=")}:
            display.zoom_in()
            cv2.resizeWindow(window, display.size[0], display.size[1])
        if key in {ord("-"), ord("_")}:
            display.zoom_out()
            cv2.resizeWindow(window, display.size[0], display.size[1])
        if key in {ord("n"), 13, 32}:
            state.advance()
        if key == ord("s"):
            if state.complete():
                output.write_text(
                    yaml.safe_dump(state.to_config(base_config), sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                cv2.destroyWindow(window)
                return output
            state.message = "Cannot save yet. Missing: " + ", ".join(state.missing_steps())


def scaled_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    if target_width <= 0 or width <= target_width:
        return (width, height)
    ratio = target_width / width
    return (target_width, max(1, round(height * ratio)))


def load_existing_config(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or None


def hydrate_state(state: AnnotationState, config: dict[str, Any]) -> None:
    state.traffic_roi = lists_to_points(config.get("traffic_roi", []))
    state.interest_roi = lists_to_points(config.get("interest_roi", []))
    state.entrance_roi = lists_to_points(config.get("entrance_roi", []))
    state.entrance_line = lists_to_points(config.get("entrance_line", []))
    outside = config.get("entrance_outside_reference_point")
    if outside:
        state.outside_reference_point = [tuple(outside)]


def draw_annotation(frame: Any, state: AnnotationState, cv2: Any) -> Any:
    colors = {
        "traffic_roi": (46, 204, 113),
        "interest_roi": (52, 152, 219),
        "entrance_roi": (231, 76, 60),
        "entrance_line": (231, 76, 60),
        "outside_reference_point": (241, 196, 15),
    }
    labels = {
        "traffic_roi": "Traffic ROI: click 3+ polygon points, then Space/Enter",
        "interest_roi": "Interest ROI: click 3+ polygon points, then Space/Enter",
        "entrance_roi": "Entrance ROI: click 3+ store-inside floor points, then S",
        "entrance_line": "Entrance Line: click exactly 2 points, then Space/Enter",
        "outside_reference_point": "Outside side: click 1 point outside the store, then S",
    }

    draw_polygon(frame, state.traffic_roi, colors["traffic_roi"], cv2)
    draw_polygon(frame, state.interest_roi, colors["interest_roi"], cv2)
    draw_polygon(frame, state.entrance_roi, colors["entrance_roi"], cv2)
    draw_polyline(frame, state.entrance_line, colors["entrance_line"], cv2)
    draw_points(frame, state.outside_reference_point, colors["outside_reference_point"], cv2)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 118), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
    cv2.putText(frame, labels[state.step], (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    cv2.putText(
        frame,
        "Left click: add   Right click/U: undo   C: clear step   P: previous   Space/Enter: next   S: save",
        (16, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1,
    )
    active_count = len(state.active_points())
    status = state.message or step_progress_message(state.step, active_count)
    cv2.putText(
        frame,
        status,
        (16, 98),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (80, 220, 255),
        1,
    )
    return frame


def draw_polygon(frame: Any, points: list[Point], color: tuple[int, int, int], cv2: Any) -> None:
    draw_polyline(frame, points, color, cv2, closed=len(points) >= 3)


def draw_polyline(
    frame: Any,
    points: list[Point],
    color: tuple[int, int, int],
    cv2: Any,
    closed: bool = False,
) -> None:
    draw_points(frame, points, color, cv2)
    for start, end in zip(points, points[1:]):
        cv2.line(frame, start, end, color, 2)
    if closed and len(points) >= 3:
        cv2.line(frame, points[-1], points[0], color, 2)


def draw_points(frame: Any, points: list[Point], color: tuple[int, int, int], cv2: Any) -> None:
    for index, point in enumerate(points, start=1):
        cv2.circle(frame, point, 5, color, -1)
        cv2.putText(frame, str(index), (point[0] + 7, point[1] - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def step_is_complete(step: str, points: list[Point]) -> bool:
    return len(points) >= point_limit(step)


def point_limit(step: str) -> int:
    if step in {"traffic_roi", "interest_roi", "entrance_roi"}:
        return 3
    if step == "entrance_line":
        return 2
    return 1


def step_title(step: str) -> str:
    return {
        "traffic_roi": "Traffic ROI",
        "interest_roi": "Interest ROI",
        "entrance_roi": "Entrance ROI",
        "entrance_line": "Entrance Line",
        "outside_reference_point": "Outside Side",
    }[step]


def step_progress_message(step: str, count: int) -> str:
    required = point_limit(step)
    if step in {"traffic_roi", "interest_roi", "entrance_roi"} and count >= required:
        return f"{step_title(step)} has {count} point(s). Press Space/Enter to continue."
    if count >= required:
        return f"{step_title(step)} is ready. Press Space/Enter to continue."
    return f"{step_title(step)}: {count}/{required} point(s)."


def points_to_lists(points: list[Point]) -> list[list[int]]:
    return [[x, y] for x, y in points]


def lists_to_points(points: list[list[int]]) -> list[Point]:
    return [(int(x), int(y)) for x, y in points]


def default_config_path(store_id: str) -> str:
    normalized = (
        store_id.lower()
        .replace("'", "")
        .replace(" ", "_")
        .replace("-", "_")
    )
    return f"configs/{normalized}.yaml"
