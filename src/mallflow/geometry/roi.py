from __future__ import annotations

from dataclasses import dataclass


Point = tuple[float, float]


@dataclass(frozen=True)
class PolygonROI:
    name: str
    vertices: tuple[Point, ...]

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError("A polygon ROI requires at least three vertices.")

    def contains(self, point: Point, include_boundary: bool = True) -> bool:
        if include_boundary and self._on_boundary(point):
            return True

        x, y = point
        inside = False
        n = len(self.vertices)
        for i in range(n):
            x1, y1 = self.vertices[i]
            x2, y2 = self.vertices[(i + 1) % n]
            intersects = (y1 > y) != (y2 > y)
            if intersects:
                x_at_y = (x2 - x1) * (y - y1) / (y2 - y1) + x1
                if x < x_at_y:
                    inside = not inside
        return inside

    def _on_boundary(self, point: Point, eps: float = 1e-9) -> bool:
        px, py = point
        for start, end in zip(self.vertices, self.vertices[1:] + self.vertices[:1]):
            x1, y1 = start
            x2, y2 = end
            cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
            if abs(cross) > eps:
                continue
            dot = (px - x1) * (px - x2) + (py - y1) * (py - y2)
            if dot <= eps:
                return True
        return False
