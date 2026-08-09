from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class BetaPosteriorSummary:
    store_id: str
    metric: str
    successes: int
    trials: int
    alpha: float
    beta: float
    observed_rate: float
    posterior_mean: float
    credible_interval_95: tuple[float, float]


@dataclass(frozen=True)
class BetaComparisonSummary:
    metric: str
    left_store_id: str
    right_store_id: str
    probability_left_greater: float


def summarize_beta_binomial(
    metrics_paths: list[str],
    output_path: str,
    metric: str = "entry",
    samples: int = 100_000,
    seed: int = 42,
) -> Path:
    metrics_rows = [load_metrics(path) for path in metrics_paths]
    posterior_summaries = [
        beta_posterior_summary(row, metric, samples=samples, seed=seed + index)
        for index, row in enumerate(metrics_rows)
    ]
    comparisons = pairwise_comparisons(metrics_rows, metric, samples=samples, seed=seed)
    payload = {
        "metric": metric,
        "posteriors": [asdict(summary) for summary in posterior_summaries],
        "comparisons": [asdict(comparison) for comparison in comparisons],
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output


def load_metrics(path: str) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def beta_posterior_summary(
    metrics: dict[str, Any],
    metric: str,
    samples: int = 100_000,
    seed: int = 42,
) -> BetaPosteriorSummary:
    successes, trials = success_trials(metrics, metric)
    alpha = successes + 1
    beta = trials - successes + 1
    draws = beta_draws(alpha, beta, samples, seed)
    lower, upper = quantile(draws, 0.025), quantile(draws, 0.975)
    return BetaPosteriorSummary(
        store_id=str(metrics["store_id"]),
        metric=metric,
        successes=successes,
        trials=trials,
        alpha=alpha,
        beta=beta,
        observed_rate=safe_div(successes, trials),
        posterior_mean=alpha / (alpha + beta),
        credible_interval_95=(lower, upper),
    )


def pairwise_comparisons(
    metrics_rows: list[dict[str, Any]],
    metric: str,
    samples: int = 100_000,
    seed: int = 42,
) -> list[BetaComparisonSummary]:
    comparisons = []
    posterior_draws = {}
    for index, metrics in enumerate(metrics_rows):
        successes, trials = success_trials(metrics, metric)
        posterior_draws[str(metrics["store_id"])] = beta_draws(successes + 1, trials - successes + 1, samples, seed + index)

    for left_index, left in enumerate(metrics_rows):
        for right in metrics_rows[left_index + 1 :]:
            left_id = str(left["store_id"])
            right_id = str(right["store_id"])
            probability = mean_greater(posterior_draws[left_id], posterior_draws[right_id])
            comparisons.append(
                BetaComparisonSummary(
                    metric=metric,
                    left_store_id=left_id,
                    right_store_id=right_id,
                    probability_left_greater=probability,
                )
            )
    return comparisons


def success_trials(metrics: dict[str, Any], metric: str) -> tuple[int, int]:
    trials = int(metrics["passerby_count"])
    success_key = {
        "entry": "entry_count",
        "exposure": "exposed_count",
        "stop": "stop_count",
    }.get(metric)
    if success_key is None:
        raise ValueError(f"Unsupported beta-binomial metric: {metric}")
    successes = int(metrics[success_key])
    if successes > trials:
        raise ValueError(f"{success_key} cannot exceed passerby_count.")
    return successes, trials


def beta_draws(alpha: float, beta: float, samples: int, seed: int):
    import numpy as np

    generator = np.random.default_rng(seed)
    return generator.beta(alpha, beta, size=samples)


def quantile(values: Any, probability: float) -> float:
    import numpy as np

    return float(np.quantile(values, probability))


def mean_greater(left: Any, right: Any) -> float:
    import numpy as np

    return float(np.mean(left > right))


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
