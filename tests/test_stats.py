from mallflow.analytics.stats import beta_posterior_summary, pairwise_comparisons


def test_beta_posterior_summary_uses_uniform_prior():
    summary = beta_posterior_summary(
        {"store_id": "A", "passerby_count": 10, "entry_count": 2},
        "entry",
        samples=10_000,
        seed=1,
    )

    assert summary.successes == 2
    assert summary.trials == 10
    assert summary.alpha == 3
    assert summary.beta == 9
    assert summary.observed_rate == 0.2
    assert summary.posterior_mean == 0.25
    assert 0.05 < summary.credible_interval_95[0] < 0.15
    assert 0.45 < summary.credible_interval_95[1] < 0.6


def test_pairwise_comparison_probability_favors_higher_rate():
    comparisons = pairwise_comparisons(
        [
            {"store_id": "A", "passerby_count": 100, "entry_count": 20},
            {"store_id": "B", "passerby_count": 100, "entry_count": 5},
        ],
        "entry",
        samples=20_000,
        seed=2,
    )

    assert comparisons[0].left_store_id == "A"
    assert comparisons[0].right_store_id == "B"
    assert comparisons[0].probability_left_greater > 0.99
