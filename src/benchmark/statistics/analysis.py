from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from benchmark.core.models import AnalysisReport, MetricValue, RunRecord
from benchmark.statistics.confidence_intervals import ConfidenceInterval, ConfidenceIntervalCalculator
from benchmark.statistics.effect_sizes import EffectSize, EffectSizeComputer

if TYPE_CHECKING:
    from benchmark.evaluation.engine import EvaluationResult


# ---------------------------------------------------------------------------
# Multiple-comparison corrections (DA-14)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComparisonResult:
    name: str
    raw_p_value: float
    adjusted_p_value: float
    family: str
    significant_after_correction: bool


def benjamini_hochberg(
    p_values: list[float],
    family_labels: list[str] | None = None,
) -> list[ComparisonResult]:
    """Benjamini-Hochberg step-up procedure within a single comparison family.

    Returns ComparisonResults preserving original ordering with adjusted
    p-values. Family labels default to ``"default"`` when not provided.
    """
    n = len(p_values)
    if n == 0:
        return []
    for i, p in enumerate(p_values):
        if not (0 <= p <= 1):
            raise ValueError(f"p-value at index {i} is {p}; must be in [0, 1]")
    labels = family_labels if family_labels is not None else ["default"] * n
    if len(labels) != n:
        raise ValueError("family_labels length must match p_values length")

    # Sort ascending by p-value (rank 1 = smallest p)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n

    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        adjusted[orig_idx] = min(p * n / rank, 1.0)

    # Enforce monotonicity: step down from rank n-1 to 1
    # adjusted[rank_i] = min(adjusted[rank_i], adjusted[rank_{i+1}])
    for i in range(n - 2, -1, -1):
        curr_idx, _ = indexed[i]
        next_idx, _ = indexed[i + 1]
        adjusted[curr_idx] = min(adjusted[curr_idx], adjusted[next_idx])

    return [
        ComparisonResult(
            name=f"test_{i}",
            raw_p_value=p_values[i],
            adjusted_p_value=adjusted[i],
            family=labels[i],
            significant_after_correction=adjusted[i] < 0.05,
        )
        for i in range(n)
    ]


def holm_correction(
    p_values: list[float],
    family_labels: list[str] | None = None,
) -> list[ComparisonResult]:
    """Holm step-down (sequential Bonferroni) procedure within a single family.

    Returns ComparisonResults preserving original ordering with adjusted
    p-values.  Family labels default to ``"default"`` when not provided.
    """
    n = len(p_values)
    if n == 0:
        return []
    for i, p in enumerate(p_values):
        if not (0 <= p <= 1):
            raise ValueError(f"p-value at index {i} is {p}; must be in [0, 1]")
    labels = family_labels if family_labels is not None else ["default"] * n
    if len(labels) != n:
        raise ValueError("family_labels length must match p_values length")

    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        val = min(p * (n - rank + 1), 1.0)
        adjusted[orig_idx] = val

    for i in range(n - 2, -1, -1):
        orig_idx_current = next(
            idx for idx, _ in sorted(enumerate(p_values), key=lambda x: x[1])[i:]
        )
        orig_idx_next = next(
            idx for idx, _ in sorted(enumerate(p_values), key=lambda x: x[1])[i + 1 :]
        )
        adjusted[orig_idx_current] = min(adjusted[orig_idx_current], adjusted[orig_idx_next])

    return [
        ComparisonResult(
            name=f"test_{i}",
            raw_p_value=p_values[i],
            adjusted_p_value=adjusted[i],
            family=labels[i],
            significant_after_correction=adjusted[i] < 0.05,
        )
        for i in range(n)
    ]


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
    paired: bool = False
    unmatched_count: int = 0


@dataclass(frozen=True)
class StatisticalAnalysisReport:
    comparisons: tuple[StatisticalComparison, ...] = ()
    report: AnalysisReport | None = None
    paired_analyses: tuple[StatisticalComparison, ...] = ()


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
        sensitivity_margins: tuple[float, ...] = (0.03, 0.10),
    ) -> tuple[bool, float, tuple[float, float], dict[float, bool]]:
        """Non-inferiority test: selective (group1) minus baseline (group2).

        Returns
        -------
        is_non_inferior : bool
            True when the lower bound of the 95% bootstrap CI for
            ``mean(group1 - group2)`` exceeds ``-margin``.
        mean_diff : float
            Observed mean difference (selective minus baseline).
        ci_bounds : tuple[float, float]
            (lower, upper) of the two-sided 95% bootstrap CI.
        sensitivity : dict[float, bool]
            Non-inferiority decision at each sensitivity margin.
        """
        if len(group1) != len(group2):
            raise ValueError(
                f"group1 length {len(group1)} != group2 length {len(group2)}; "
                "paired analysis requires equal-length groups"
            )
        if len(group1) < 2:
            raise ValueError("Need at least 2 paired observations")

        differences = [g1 - g2 for g1, g2 in zip(group1, group2, strict=True)]
        mean_diff = float(np.mean(differences))
        ci = self._ci_calculator.bootstrap_ci(differences)

        lower_bound = ci.lower
        is_non_inferior = lower_bound > -margin

        all_margins = (margin,) + tuple(m for m in sensitivity_margins if m != margin)
        sensitivity = {m: lower_bound > -m for m in sorted(all_margins)}

        return is_non_inferior, mean_diff, (ci.lower, ci.upper), sensitivity

    def paired_bootstrap_ci(
        self,
        differences: list[float],
    ) -> ConfidenceInterval:
        """Bootstrap CI on paired differences (confirmatory H1 method)."""
        if not differences:
            return ConfidenceInterval(lower=0.0, upper=0.0, confidence_level=self._confidence_level)
        return self._ci_calculator.bootstrap_ci(differences, statistic="mean")

    def paired_compare(
        self,
        results: list[EvaluationResult],
        metric_name: str = "recall",
    ) -> StatisticalAnalysisReport:
        """Paired comparison by matching on (repository, scenario, repetition).

        Each EvaluationResult is expected to have a ``scenario_id`` of the
        form ``{repository}-{scenario}-{repetition}``.  Observations are
        paired when two strategies share the same repository-scenario cell.
        Unmatched observations are reported but excluded from the paired CI.
        """
        from collections import defaultdict

        import numpy as np

        from benchmark.statistics.effect_sizes import EffectSizeComputer

        cells: dict[str, dict[str, float | None]] = defaultdict(dict)
        for result in results:
            parts = result.scenario_id.rsplit("-", 2)
            cell_key = f"{parts[0]}-{parts[1]}" if len(parts) >= 3 else result.scenario_id
            for metric in result.metrics:
                if metric.name == metric_name:
                    cells[cell_key][result.strategy_name] = metric.value

        comparisons: list[StatisticalComparison] = []
        paired_comparisons: list[StatisticalComparison] = []
        strategies = sorted({r.strategy_name for r in results})

        for i, strat_a in enumerate(strategies):
            for strat_b in strategies[i + 1 :]:
                paired_a: list[float] = []
                paired_b: list[float] = []
                unmatched = 0

                for _cell_key, vals in cells.items():
                    va = vals.get(strat_a)
                    vb = vals.get(strat_b)
                    if va is not None and vb is not None:
                        paired_a.append(va)
                        paired_b.append(vb)
                    elif va is not None or vb is not None:
                        unmatched += 1

                if len(paired_a) < 2:
                    continue

                diffs = [a - b for a, b in zip(paired_a, paired_b, strict=True)]
                mean_a = float(np.mean(paired_a))
                mean_b = float(np.mean(paired_b))
                mean_diff = float(np.mean(diffs))

                ci = self.paired_bootstrap_ci(diffs)

                effect_computer = EffectSizeComputer()
                effect_size = effect_computer.compute(paired_a, paired_b)

                from scipy import stats as sp_stats

                try:
                    _, p_val = sp_stats.wilcoxon(paired_a, paired_b, alternative="two-sided")
                    p_value = float(p_val)
                except Exception:
                    p_value = None

                comp = StatisticalComparison(
                    strategy_a=strat_a,
                    strategy_b=strat_b,
                    metric_name=metric_name,
                    mean_a=mean_a,
                    mean_b=mean_b,
                    difference=mean_diff,
                    confidence_interval=ci,
                    effect_size=effect_size,
                    p_value=p_value,
                    paired=True,
                    unmatched_count=unmatched,
                )
                comparisons.append(comp)
                paired_comparisons.append(comp)

        metrics_vals = self._build_metrics(comparisons)
        summary_lines = [f"Paired comparisons: {len(paired_comparisons)}"]
        for comp in paired_comparisons:
            unmatched_note = f" ({comp.unmatched_count} unmatched)" if comp.unmatched_count else ""
            summary_lines.append(
                f"{comp.strategy_a} vs {comp.strategy_b}: diff={comp.difference:.4f}, "
                f"CI=[{comp.confidence_interval.lower:.4f}, {comp.confidence_interval.upper:.4f}], "
                f"effect={comp.effect_size.value:.4f} ({comp.effect_size.magnitude}){unmatched_note}"
            )

        report = AnalysisReport(
            title=f"Paired Statistical Analysis: {metric_name}",
            metrics=metrics_vals,
            summary="\n".join(summary_lines),
        )

        return StatisticalAnalysisReport(
            comparisons=tuple(comparisons),
            paired_analyses=tuple(paired_comparisons),
            report=report,
        )

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
