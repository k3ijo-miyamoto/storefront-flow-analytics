from mallflow.geometry.line_crossing import (
    CrossingDirection,
    LineSegment,
    crossed_from_outside_to_inside,
    line_crossing_direction,
)


def test_line_crossing_detects_side_transition():
    line = LineSegment((400, 250), (700, 250))

    assert line_crossing_direction((500, 300), (500, 200), line) == CrossingDirection.POSITIVE_TO_NEGATIVE
    assert line_crossing_direction((500, 200), (500, 300), line) == CrossingDirection.NEGATIVE_TO_POSITIVE
    assert line_crossing_direction((500, 300), (600, 320), line) == CrossingDirection.NONE


def test_outside_to_inside_depends_on_configured_outside_side():
    line = LineSegment((400, 250), (700, 250))
    outside_side = line.side((500, 300))

    assert crossed_from_outside_to_inside((500, 300), (500, 200), line, outside_side)
    assert not crossed_from_outside_to_inside((500, 200), (500, 300), line, outside_side)


def test_line_crossing_requires_crossing_the_finite_entrance_segment():
    line = LineSegment((400, 250), (700, 250))

    assert line_crossing_direction((900, 300), (900, 200), line) == CrossingDirection.NONE
