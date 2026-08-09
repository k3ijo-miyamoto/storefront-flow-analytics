from mallflow.analytics.facade import summarize_zone
from mallflow.geometry.roi import PolygonROI


def test_summarize_zone_counts_entries_after_exposure():
    zone = PolygonROI("left_window", ((0, 0), (10, 0), (10, 10), (0, 10)))
    track_rows = {
        1: {"slowed": "1", "stopped": "0", "entered": "1", "entry_timestamp_s": "5.0"},
        2: {"slowed": "0", "stopped": "1", "entered": "0", "entry_timestamp_s": ""},
        3: {"slowed": "0", "stopped": "0", "entered": "1", "entry_timestamp_s": "1.0"},
    }
    track_points = {
        1: [
            {"timestamp_s": 1.0, "x": 1.0, "y": 1.0},
            {"timestamp_s": 2.0, "x": 2.0, "y": 2.0},
            {"timestamp_s": 6.0, "x": 20.0, "y": 20.0},
        ],
        2: [
            {"timestamp_s": 1.0, "x": 5.0, "y": 5.0},
            {"timestamp_s": 2.0, "x": 20.0, "y": 20.0},
        ],
        3: [
            {"timestamp_s": 2.0, "x": 5.0, "y": 5.0},
            {"timestamp_s": 3.0, "x": 6.0, "y": 6.0},
        ],
    }

    summary = summarize_zone(zone, track_rows, track_points)

    assert summary.zone == "left_window"
    assert summary.exposed_count == 3
    assert summary.slowed_count == 1
    assert summary.stopped_count == 1
    assert summary.entered_after_exposure_count == 1
    assert summary.first_touch_entry_count == 0
    assert summary.last_touch_entry_count == 0
    assert summary.exposure_to_entry_rate == 1 / 3
    assert summary.first_touch_entry_rate == 0.0
    assert summary.last_touch_entry_rate == 0.0
    assert summary.dwell_median_s == 1.0
    assert summary.median_time_to_entry_s == 4.0
