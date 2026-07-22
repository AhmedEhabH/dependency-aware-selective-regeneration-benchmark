from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from benchmark.core.models import AnalysisReport, MetricValue, RunRecord
from benchmark.statistics.confidence_intervals import ConfidenceInterval, ConfidenceIntervalCalculator
from benchmark.statistics.effect_sizes import EffectSize, EffectSizeComputer

if TYPE_CHECKING:
    from benchmark.evaluation.engine import EvaluationResult


@dataclass(frozen=True)
class StatisticalComparison:
    strategy_a: str
    strategy_b: str
    metric_name: str
    mean_a: float
    mean_b: float
    difference: float
    confidence_interval: ConfidenceInterval
    effect_size: EffectSize
    p_value: float | None = None


@dataclass(frozen=True)
class StatisticalAnalysisReport:
    comparisons: tuple[StatisticalComparison, ...] = ()
    report: AnalysisReport | None = None


class StatisticalAnalyzer:
    def __init__(
        self,
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000,
        random_seed: int | None = None,
    ) -> None:
        self._confidence_level = confidence_level
        self._n_bootstrap = n_bootstrap
        self._random_seed = random_seed
        self._ci_calculator = ConfidenceIntervalCalculator(
            confidence_level=confidence_level,
            n_bootstrap=n_bootstrap,
            random_seed=random_seed,
        )
        self._effect_size_computer = EffectSizeComputer()

    def analyze(
        self,
        results: list[EvaluationResult],
        metric_name: str = "recall",
    ) -> StatisticalAnalysisReport:
        if not results:
            return StatisticalAnalysisReport()

        strategy_data: dict[str, list[float]] = {}
        for result in results:
            for metric in result.metrics:
                if metric.name == metric_name and metric.value is not None:
                    strategy_data.setdefault(result.strategy_name, []).append(metric.value)

        comparisons: list[StatisticalComparison] = []
        strategies = list(strategy_data.keys())

        for i, strategy_a in enumerate(strategies):
            for strategy_b in strategies[i + 1 :]:
                data_a = strategy_data[strategy_a]
                data_b = strategy_data[strategy_b]

                if not data_a or not data_b:
                    continue

                mean_a = float(np.mean(data_a))
                mean_b = float(np.mean(data_b))
                difference = mean_a - mean_b

                ci = self._ci_calculator.bootstrap_ci(data_a + data_b)

                effect_size = self._effect_size_computer.compute(data_a, data_b)

                p_value = self._compute_p_value(data_a, data_b)

                comparisons.append(
                    StatisticalComparison(
                        strategy_a=strategy_a,
                        strategy_b=strategy_b,
                        metric_name=metric_name,
                        mean_a=mean_a,
                        mean_b=mean_b,
                        difference=difference,
                        confidence_interval=ci,
                        effect_size=effect_size,
                        p_value=p_value,
                    )
                )

        metrics = self._build_metrics(comparisons)
        summary = self._build_summary(comparisons)

        report = AnalysisReport(
            title=f"Statistical Analysis: {metric_name}",
            metrics=metrics,
            summary=summary,
        )

        return StatisticalAnalysisReport(comparisons=tuple(comparisons), report=report)

    def _compute_p_value(self, group1: list[float], group2: list[float]) -> float | None:
        try:
            from scipy import stats

            statistic, p_value = stats.mannwhitneyu(group1, group2, alternative="two-sided")
            return float(p_value)
        except Exception:
            return None

    def _build_metrics(self, comparisons: list[StatisticalComparison]) -> tuple[MetricValue, ...]:
        metrics: list[MetricValue] = []

        for comp in comparisons:
            metrics.append(
                MetricValue(
                    name=f"{comp.strategy_a}_vs_{comp.strategy_b}_{comp.metric_name}_diff",
                    value=comp.difference,
                    unit="proportion",
                )
            )
            if comp.p_value is not None:
                metrics.append(
                    MetricValue(
                        name=f"{comp.strategy_a}_vs_{comp.strategy_b}_p_value",
                        value=comp.p_value,
                        unit="p-value",
                    )
                )

        return tuple(metrics)

    def _build_summary(self, comparisons: list[StatisticalComparison]) -> str:
        lines = [f"Total comparisons: {len(comparisons)}"]
        for comp in comparisons:
            lines.append(
                f"{comp.strategy_a} vs {comp.strategy_b}: diff={comp.difference:.4f}, "
                f"CI=[{comp.confidence_interval.lower:.4f}, {comp.confidence_interval.upper:.4f}], "
                f"effect={comp.effect_size.value:.4f} ({comp.effect_size.magnitude})"
            )
        return "\n".join(lines)

    def compute_confidence_interval(
        self,
        data: list[float],
        statistic: str = "mean",
    ) -> ConfidenceInterval:
        return self._ci_calculator.bootstrap_ci(data, statistic=statistic)

    def compute_effect_size(
        self,
        group1: list[float],
        group2: list[float],
    ) -> EffectSize:
        return self._effect_size_computer.compute(group1, group2)

    def non_inferiority_test(
        self,
        group1: list[float],
        group2: list[float],
        margin: float = 0.05,
    ) -> tuple[bool, float, tuple[float, float]]:
        differences = [g1 - g2 for g1, g2 in zip(group1, group2, strict=True)]
        mean_diff = float(np.mean(differences))
        ci = self._ci_calculator.bootstrap_ci(differences)

        lower_bound = ci.lower
        is_non_inferior = lower_bound > -margin

        return is_non_inferior, mean_diff, (ci.lower, ci.upper)

    def mixed_effects_model(
        self,
        data: list[RunRecord],
    ) -> AnalysisReport | None:
        try:
            import statsmodels.formula.api as smf

            from benchmark.core.enums import RunStatus

            df_data = []
            for record in data:
                if record.status == RunStatus.succeeded and record.prediction:
                    df_data.append(
                        {
                            "efficiency": 1.0,
                            "blast_radius": record.identity.scenario_id.split("-")[1]
                            if "-" in record.identity.scenario_id
                            else "unknown",
                            "strategy": record.identity.strategy_name,
                            "repository": record.identity.scenario_id.split("-")[0]
                            if "-" in record.identity.scenario_id
                            else "unknown",
                        }
                    )

            if not df_data:
                return None

            import pandas as pd

            df = pd.DataFrame(df_data)

            model = smf.mixedlm(
                "efficiency ~ blast_radius * strategy",
                df,
                groups=df["repository"],
            )
            result = model.fit()

            return AnalysisReport(
                title="Mixed Effects Model: efficiency ~ blast_radius * strategy",
                summary=str(result.summary()),
            )
        except Exception:
            return None
