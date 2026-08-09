from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


Point = tuple[float, float]


class CrossingDirection(str, Enum):
    NONE = "NONE"
    NEGATIVE_TO_POSITIVE = "NEGATIVE_TO_POSITIVE"
    POSITIVE_TO_NEGATIVE = "POSITIVE_TO_NEGATIVE"


@dataclass(frozen=True)
class LineSegment:
    start: Point
    end: Point

    def side(self, point: Point) -> float:
        x1, y1 = self.start
        x2, y2 = self.end
        px, py = point
        return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def line_crossing_direction(
    previous: Point,
    current: Point,
    line: LineSegment,
    eps: float = 1e-9,
) -> CrossingDirection:
    if not _segments_intersect(previous, current, line.start, line.end, eps):
        return CrossingDirection.NONE

    prev_side = line.side(previous)
    curr_side = line.side(current)

    if abs(prev_side) <= eps or abs(curr_side) <= eps:
        if abs(prev_side) <= eps and abs(curr_side) <= eps:
            return CrossingDirection.NONE
        return CrossingDirection.NONE

    if prev_side < 0 < curr_side:
        return CrossingDirection.NEGATIVE_TO_POSITIVE
    if prev_side > 0 > curr_side:
        return CrossingDirection.POSITIVE_TO_NEGATIVE
    return CrossingDirection.NONE


def crossed_from_outside_to_inside(
    previous: Point,
    current: Point,
    entrance_line: LineSegment,
    outside_side: float,
) -> bool:
    direction = line_crossing_direction(previous, current, entrance_line)
    if direction is CrossingDirection.NONE:
        return False
    prev_side = entrance_line.side(previous)
    curr_side = entrance_line.side(current)
    return prev_side * outside_side > 0 and curr_side * outside_side < 0


def _segments_intersect(a: Point, b: Point, c: Point, d: Point, eps: float) -> bool:
    def orientation(p: Point, q: Point, r: Point) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: Point, q: Point, r: Point) -> bool:
        return (
            min(p[0], r[0]) - eps <= q[0] <= max(p[0], r[0]) + eps
            and min(p[1], r[1]) - eps <= q[1] <= max(p[1], r[1]) + eps
        )

    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)

    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True
    if abs(o1) <= eps and on_segment(a, c, b):
        return True
    if abs(o2) <= eps and on_segment(a, d, b):
        return True
    if abs(o3) <= eps and on_segment(c, a, d):
        return True
    if abs(o4) <= eps and on_segment(c, b, d):
        return True
    return False
