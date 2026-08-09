from mallflow.behavior.events import BehaviorThresholds, evaluate_track
from mallflow.behavior.state_machine import BehaviorState, TrackStateMachine
from mallflow.geometry.line_crossing import LineSegment
from mallflow.geometry.roi import PolygonROI
from mallflow.tracking.base import Track, TrackPoint


def test_state_machine_allows_direct_entry_and_keeps_terminal_state():
    machine = TrackStateMachine()

    machine.mark_passerby()
    machine.mark_entered()
    machine.mark_stopped()

    assert machine.state == BehaviorState.ENTERED


def test_synthetic_track_passes_exposes_stops_and_enters_once():
    traffic = PolygonROI("traffic", ((0, 250), (1000, 250), (1000, 700), (0, 700)))
    interest = PolygonROI("interest", ((250, 120), (850, 120), (850, 500), (250, 500)))
    entrance = LineSegment((400, 180), (700, 180))
    outside_side = entrance.side((500, 350))
    track = Track(
        track_id=17,
        points=[
            TrackPoint(0, 0.0, (100, 550)),
            TrackPoint(1, 1.0, (300, 450)),
            TrackPoint(2, 2.0, (320, 440)),
            TrackPoint(3, 3.0, (325, 438)),
            TrackPoint(4, 4.0, (330, 436)),
            TrackPoint(5, 5.0, (500, 160)),
            TrackPoint(6, 6.0, (520, 130)),
        ],
    )

    behavior = evaluate_track(
        track,
        traffic,
        interest,
        entrance,
        outside_side,
        BehaviorThresholds(stop_duration_threshold_s=1.5),
    )

    assert behavior.passerby
    assert behavior.exposed
    assert behavior.slowed
    assert behavior.stopped
    assert behavior.entered
    assert behavior.entry_timestamp_s == 5.0
    assert behavior.state == BehaviorState.ENTERED
    assert behavior.stop_duration_s >= 2.0


def test_synthetic_quick_false_positive_is_not_passerby():
    traffic = PolygonROI("traffic", ((0, 250), (1000, 250), (1000, 700), (0, 700)))
    interest = PolygonROI("interest", ((250, 120), (850, 120), (850, 500), (250, 500)))
    entrance = LineSegment((400, 180), (700, 180))
    outside_side = entrance.side((500, 350))
    track = Track(
        track_id=9,
        points=[
            TrackPoint(0, 0.0, (100, 550)),
            TrackPoint(1, 0.2, (110, 540)),
        ],
    )

    behavior = evaluate_track(track, traffic, interest, entrance, outside_side)

    assert not behavior.passerby
    assert not behavior.entered
    assert behavior.state == BehaviorState.UNSEEN


def test_synthetic_track_enters_by_entrance_roi():
    traffic = PolygonROI("traffic", ((0, 250), (1000, 250), (1000, 700), (0, 700)))
    interest = PolygonROI("interest", ((250, 120), (850, 120), (850, 500), (250, 500)))
    entrance_roi = PolygonROI("entrance", ((400, 120), (700, 120), (700, 250), (400, 250)))
    track = Track(
        track_id=18,
        points=[
            TrackPoint(0, 0.0, (500, 500)),
            TrackPoint(1, 1.0, (500, 300)),
            TrackPoint(2, 2.0, (500, 200)),
            TrackPoint(3, 3.0, (520, 190)),
        ],
    )

    behavior = evaluate_track(track, traffic, interest, thresholds=BehaviorThresholds(), entrance_roi=entrance_roi)

    assert behavior.entered
    assert behavior.entry_timestamp_s == 2.0


def test_synthetic_track_starting_inside_entrance_roi_is_not_entry():
    traffic = PolygonROI("traffic", ((0, 250), (1000, 250), (1000, 700), (0, 700)))
    interest = PolygonROI("interest", ((250, 120), (850, 120), (850, 500), (250, 500)))
    entrance_roi = PolygonROI("entrance", ((400, 120), (700, 120), (700, 250), (400, 250)))
    track = Track(
        track_id=19,
        points=[
            TrackPoint(0, 0.0, (500, 200)),
            TrackPoint(1, 1.0, (510, 210)),
        ],
    )

    behavior = evaluate_track(track, traffic, interest, thresholds=BehaviorThresholds(), entrance_roi=entrance_roi)

    assert not behavior.entered


def test_synthetic_track_touching_entrance_roi_once_is_not_entry():
    traffic = PolygonROI("traffic", ((0, 250), (1000, 250), (1000, 700), (0, 700)))
    interest = PolygonROI("interest", ((250, 120), (850, 120), (850, 500), (250, 500)))
    entrance_roi = PolygonROI("entrance", ((400, 120), (700, 120), (700, 250), (400, 250)))
    track = Track(
        track_id=20,
        points=[
            TrackPoint(0, 0.0, (500, 500)),
            TrackPoint(1, 1.0, (500, 200)),
            TrackPoint(2, 2.0, (300, 300)),
        ],
    )

    behavior = evaluate_track(track, traffic, interest, thresholds=BehaviorThresholds(), entrance_roi=entrance_roi)

    assert not behavior.entered
