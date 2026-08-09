from mallflow.geometry.roi import PolygonROI


def test_polygon_roi_contains_inside_outside_and_boundary_points():
    roi = PolygonROI(
        name="traffic",
        vertices=((100, 300), (1000, 300), (1000, 700), (100, 700)),
    )

    assert roi.contains((500, 500))
    assert roi.contains((100, 500))
    assert not roi.contains((50, 500))
    assert not roi.contains((500, 250))
