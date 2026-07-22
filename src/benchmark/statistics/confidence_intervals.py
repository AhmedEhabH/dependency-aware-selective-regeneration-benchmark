from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConfidenceInterval:
    lower: float
    upper: float
    confidence_level: float = 0.95
    method: str = "bootstrap"

    def __post_init__(self) -> None:
        if not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if self.lower > self.upper:
            raise ValueError("lower bound cannot exceed upper bound")


class ConfidenceIntervalCalculator:
    def __init__(
        self,
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000,
        random_seed: int | None = None,
    ) -> None:
        self._confidence_level = confidence_level
        self._n_bootstrap = n_bootstrap
        self._random_seed = random_seed

    def bootstrap_ci(
        self,
        data: list[float],
        statistic: str = "mean",
    ) -> ConfidenceInterval:
        if not data:
            return ConfidenceInterval(lower=0.0, upper=0.0, confidence_level=self._confidence_level)

        rng = np.random.default_rng(self._random_seed)
        data_array = np.array(data)

        bootstrap_stats: list[float] = []
        for _ in range(self._n_bootstrap):
            sample = rng.choice(data_array, size=len(data_array), replace=True)
            if statistic == "mean":
                bootstrap_stats.append(float(np.mean(sample)))
            elif statistic == "median":
                bootstrap_stats.append(float(np.median(sample)))
            elif statistic == "std":
                bootstrap_stats.append(float(np.std(sample)))
            else:
                bootstrap_stats.append(float(np.mean(sample)))

        alpha = 1 - self._confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        lower = float(np.percentile(bootstrap_stats, lower_percentile))
        upper = float(np.percentile(bootstrap_stats, upper_percentile))

        return ConfidenceInterval(lower=lower, upper=upper, confidence_level=self._confidence_level)

    def normal_ci(
        self,
        mean: float,
        std_err: float,
    ) -> ConfidenceInterval:
        from scipy import stats

        alpha = 1 - self._confidence_level
        z_score = stats.norm.ppf(1 - alpha / 2)

        lower = mean - z_score * std_err
        upper = mean + z_score * std_err

        return ConfidenceInterval(lower=lower, upper=upper, confidence_level=self._confidence_level)

    def binomial_ci(
        self,
        successes: int,
        trials: int,
        method: str = "wilson",
    ) -> ConfidenceInterval:
        if not 0 < self._confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if trials == 0:
            return ConfidenceInterval(lower=0.0, upper=0.0, confidence_level=self._confidence_level)

        from scipy import stats

        p = successes / trials
        alpha = 1 - self._confidence_level
        z = float(stats.norm.ppf(1 - alpha / 2))

        if method == "wilson":
            denominator = 1 + z**2 / trials
            center = (p + z**2 / (2 * trials)) / denominator
            margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denominator
            lower = max(0.0, center - margin)
            upper = min(1.0, center + margin)
        elif method == "agresti_coull":
            z2 = z**2
            n_tilde = trials + z2
            p_tilde = (successes + z2 / 2) / n_tilde
            margin = z * np.sqrt(p_tilde * (1 - p_tilde) / n_tilde)
            lower = max(0.0, p_tilde - margin)
            upper = min(1.0, p_tilde + margin)
        else:
            lower = max(0.0, p - z * np.sqrt(p * (1 - p) / trials))
            upper = min(1.0, p + z * np.sqrt(p * (1 - p) / trials))

        return ConfidenceInterval(lower=lower, upper=upper, confidence_level=self._confidence_level)
