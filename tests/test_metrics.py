from mallflow.analytics.metrics import summarize_store
from mallflow.behavior.events import TrackBehavior
from mallflow.behavior.state_machine import BehaviorState


def behavior(**kwargs):
    defaults = dict(
        track_id=1,
        first_seen_s=0.0,
        last_seen_s=1.0,
        track_duration_s=1.0,
        state=BehaviorState.PASSERBY,
        passerby=True,
        exposed=False,
        slowed=False,
        stopped=False,
        entered=False,
        interest_dwell_s=0.0,
        stop_duration_s=0.0,
        direction="OTHER",
        entry_timestamp_s=None,
        tracking_confidence=1.0,
    )
    defaults.update(kwargs)
    return TrackBehavior(**defaults)


def test_summarize_store_counts_and_rates():
    metrics = summarize_store(
        "STORE_A",
        video_duration_s=120,
        tracks=[
            behavior(track_id=1, exposed=True, slowed=True, stopped=True, entered=True, interest_dwell_s=4.0),
            behavior(track_id=2, exposed=True, interest_dwell_s=2.0),
            behavior(track_id=3),
        ],
    )

    assert metrics.unique_tracks == 3
    assert metrics.passerby_count == 3
    assert metrics.exposed_count == 2
    assert metrics.stop_count == 1
    assert metrics.entry_count == 1
    assert metrics.traffic_rate_per_min == 1.5
    assert metrics.entry_rate == 1 / 3
    assert metrics.stop_to_entry_conversion == 1.0
    assert metrics.dwell_median_s == 3.0
