from mallflow.detection.base import Detection
from mallflow.tracking.centroid import CentroidPersonTracker


def test_centroid_tracker_does_not_reconnect_expired_tracks():
    tracker = CentroidPersonTracker(max_distance_px=50, max_missing=1)

    tracker.update([Detection(0, 0.0, (0, 0, 20, 40), 1.0)])
    tracker.update([])
    tracker.update([])
    tracker.update([Detection(3, 3.0, (5, 0, 25, 40), 1.0)])

    tracks = tracker.all_tracks()

    assert len(tracks) == 2
    assert tracks[0].track_id == 1
    assert tracks[1].track_id == 2
