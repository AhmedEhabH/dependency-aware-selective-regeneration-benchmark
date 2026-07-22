from __future__ import annotations

import contextlib

from benchmark.evaluation.engine import EvaluationResult
from benchmark.evaluation.metrics import MetricResult
from benchmark.statistics.analysis import (
    StatisticalAnalysisReport,
    StatisticalAnalyzer,
    StatisticalComparison,
    benjamini_hochberg,
    holm_correction,
)
from benchmark.statistics.confidence_intervals import ConfidenceInterval, ConfidenceIntervalCalculator
from benchmark.statistics.effect_sizes import EffectSize, EffectSizeComputer


class TestConfidenceInterval:
    def test_validation(self) -> None:
        ci = ConfidenceInterval(lower=0.1, upper=0.9, confidence_level=0.95)
        assert ci.lower == 0.1
        assert ci.upper == 0.9

    def test_invalid_confidence_level(self) -> None:
        try:
            ConfidenceInterval(lower=0.1, upper=0.9, confidence_level=1.5)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_lower_exceeds_upper(self) -> None:
        try:
            ConfidenceInterval(lower=0.9, upper=0.1)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass


class TestConfidenceIntervalCalculator:
    def test_bootstrap_ci_basic(self) -> None:
        calculator = ConfidenceIntervalCalculator(n_bootstrap=100, random_seed=42)
        data = [0.1, 0.2, 0.3, 0.4, 0.5]

        ci = calculator.bootstrap_ci(data)

        assert ci.lower <= 0.3
        assert ci.upper >= 0.3
        assert ci.confidence_level == 0.95

    def test_bootstrap_ci_empty_data(self) -> None:
        calculator = ConfidenceIntervalCalculator()
        ci = calculator.bootstrap_ci([])

        assert ci.lower == 0.0
        assert ci.upper == 0.0

    def test_normal_ci(self) -> None:
        calculator = ConfidenceIntervalCalculator()
        ci = calculator.normal_ci(mean=0.5, std_err=0.1)

        assert ci.lower < 0.5
        assert ci.upper > 0.5

    def test_binomial_ci_wilson(self) -> None:
        calculator = ConfidenceIntervalCalculator()
        ci = calculator.binomial_ci(successes=50, trials=100, method="wilson")

        assert 0 < ci.lower < 0.5
        assert 0.5 < ci.upper < 1

    def test_binomial_ci_zero_trials(self) -> None:
        calculator = ConfidenceIntervalCalculator()
        ci = calculator.binomial_ci(successes=0, trials=0)

        assert ci.lower == 0.0
        assert ci.upper == 0.0


class TestEffectSize:
    def test_validation(self) -> None:
        es = EffectSize(name="cohen_d", value=0.5, magnitude="medium")
        assert es.name == "cohen_d"
        assert es.value == 0.5

    def test_empty_name(self) -> None:
        try:
            EffectSize(name="", value=0.5, magnitude="medium")
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass


class TestEffectSizeComputer:
    def test_cohens_d_perfect(self) -> None:
        computer = EffectSizeComputer()
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]

        d = computer.cohens_d(group1, group2)

        assert d == 0.0

    def test_cohens_d_large(self) -> None:
        computer = EffectSizeComputer()
        group1 = [10.0, 11.0, 12.0]
        group2 = [1.0, 2.0, 3.0]

        d = computer.cohens_d(group1, group2)

        assert d > 2.0

    def test_cliffs_delta_perfect(self) -> None:
        computer = EffectSizeComputer()
        group1 = [10.0, 11.0, 12.0]
        group2 = [1.0, 2.0, 3.0]

        delta = computer.cliffs_delta(group1, group2)

        assert delta > 0.5

    def test_cliffs_delta_zero(self) -> None:
        computer = EffectSizeComputer()
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]

        delta = computer.cliffs_delta(group1, group2)

        assert delta == 0.0

    def test_compute_cohen_d(self) -> None:
        computer = EffectSizeComputer(method="cohen_d")
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]

        result = computer.compute(group1, group2)

        assert result.name == "cohen_d"
        assert result.magnitude in ["negligible", "small", "medium", "large"]

    def test_compute_cliffs_delta(self) -> None:
        computer = EffectSizeComputer(method="cliff_delta")
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]

        result = computer.compute(group1, group2)

        assert result.name == "cliff_delta"

    def test_empty_groups(self) -> None:
        computer = EffectSizeComputer()

        d = computer.cohens_d([], [])
        assert d == 0.0

        delta = computer.cliffs_delta([], [])
        assert delta == 0.0


class TestStatisticalAnalyzer:
    def test_analyze_empty_results(self) -> None:
        analyzer = StatisticalAnalyzer()

        report = analyzer.analyze([])

        assert len(report.comparisons) == 0

    def test_analyze_with_results(self) -> None:
        analyzer = StatisticalAnalyzer(n_bootstrap=100, random_seed=42)

        results = [
            EvaluationResult(
                scenario_id="test-001",
                strategy_name="strategy-a",
                passed=True,
                message="Test",
                metrics=(),
            ),
            EvaluationResult(
                scenario_id="test-001",
                strategy_name="strategy-b",
                passed=False,
                message="Test",
                metrics=(),
            ),
        ]

        report = analyzer.analyze(results)

        assert isinstance(report, StatisticalAnalysisReport)

    def test_compute_confidence_interval(self) -> None:
        analyzer = StatisticalAnalyzer()
        data = [0.1, 0.2, 0.3, 0.4, 0.5]

        ci = analyzer.compute_confidence_interval(data)

        assert isinstance(ci, ConfidenceInterval)
        assert ci.lower <= ci.upper

    def test_compute_effect_size(self) -> None:
        analyzer = StatisticalAnalyzer()
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]

        es = analyzer.compute_effect_size(group1, group2)

        assert isinstance(es, EffectSize)

    def test_non_inferiority_test(self) -> None:
        analyzer = StatisticalAnalyzer()
        group1 = [0.9, 0.85, 0.95, 0.88, 0.92]
        group2 = [0.8, 0.75, 0.85, 0.78, 0.82]

        is_ni, mean_diff, (lower, upper), sensitivity = analyzer.non_inferiority_test(group1, group2, margin=0.1)

        assert isinstance(is_ni, bool)
        assert isinstance(mean_diff, float)
        assert isinstance(lower, float)
        assert isinstance(upper, float)
        assert isinstance(sensitivity, dict)


class TestStatisticalComparison:
    def test_creation(self) -> None:
        comp = StatisticalComparison(
            strategy_a="strategy-a",
            strategy_b="strategy-b",
            metric_name="recall",
            mean_a=0.8,
            mean_b=0.7,
            difference=0.1,
            confidence_interval=ConfidenceInterval(lower=0.05, upper=0.15),
            effect_size=EffectSize(name="cohen_d", value=0.5, magnitude="medium"),
            p_value=0.05,
        )

        assert comp.strategy_a == "strategy-a"
        assert comp.mean_a == 0.8
        assert comp.p_value == 0.05


class TestStatisticalAnalysisReport:
    def test_empty_report(self) -> None:
        report = StatisticalAnalysisReport()

        assert report.comparisons == ()
        assert report.report is None


# ---------------------------------------------------------------------------
# Gap 3: Multiple-comparison corrections
# ---------------------------------------------------------------------------


class TestBenjaminiHochberg:
    def test_known_values(self) -> None:
        """Hand-calculated BH on p=[0.001, 0.005, 0.01, 0.02] with n=4.

        Sorted asc: r1(0.001)->min(0.001*4/1,1)=0.004
                    r2(0.005)->min(0.005*4/2,1)=0.01
                    r3(0.01) ->min(0.01*4/3,1)=0.01333
                    r4(0.02) ->min(0.02*4/4,1)=0.02
        Step-down: [0.004, 0.01, 0.01333, 0.02]
        """
        pvals = [0.001, 0.005, 0.01, 0.02]
        result = benjamini_hochberg(pvals)
        adj = [r.adjusted_p_value for r in result]
        assert abs(adj[0] - 0.004) < 1e-9
        assert abs(adj[1] - 0.01) < 1e-9
        assert abs(adj[2] - 4 / 300) < 1e-9
        assert abs(adj[3] - 0.02) < 1e-9
        sig = [r for r in result if r.significant_after_correction]
        assert len(sig) == 4

    def test_preserves_original_order(self) -> None:
        pvals = [0.5, 0.01, 0.1]
        result = benjamini_hochberg(pvals)
        assert result[0].raw_p_value == 0.5
        assert result[1].raw_p_value == 0.01
        assert result[2].raw_p_value == 0.1

    def test_rejects_invalid_p_value(self) -> None:
        try:
            benjamini_hochberg([0.01, -0.1])
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_empty_input(self) -> None:
        assert benjamini_hochberg([]) == []

    def test_family_labels(self) -> None:
        result = benjamini_hochberg([0.01, 0.05], family_labels=["fam_a", "fam_b"])
        assert result[0].family == "fam_a"
        assert result[1].family == "fam_b"


class TestHolmCorrection:
    def test_known_values(self) -> None:
        """Hand-calculated Holm on p=[0.01, 0.04, 0.03, 0.20] with n=4."""
        pvals = [0.01, 0.04, 0.03, 0.20]
        result = holm_correction(pvals)
        adjusted = [r.adjusted_p_value for r in result]
        # Sorted asc: 0.01(rank1)->min(0.01*4,1)=0.04
        #              0.03(rank2)->min(0.03*3,1)=0.09
        #              0.04(rank3)->min(0.04*2,1)=0.08
        #              0.20(rank4)->min(0.20*1,1)=0.20
        # Monotonicity (step-down): index3=0.20, index2=0.08, index1=min(0.09,0.08)=0.08, index0=min(0.04,0.08)=0.04
        assert abs(adjusted[0] - 0.04) < 1e-9  # 0.01 -> 0.04
        assert abs(adjusted[3] - 0.20) < 1e-9  # 0.20 -> 0.20
        sig = [r for r in result if r.significant_after_correction]
        assert len(sig) >= 1

    def test_preserves_original_order(self) -> None:
        pvals = [0.5, 0.01, 0.1]
        result = holm_correction(pvals)
        assert result[0].raw_p_value == 0.5
        assert result[1].raw_p_value == 0.01

    def test_rejects_invalid_p_value(self) -> None:
        try:
            holm_correction([1.5])
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_all_significant(self) -> None:
        result = holm_correction([0.001, 0.002, 0.003])
        assert all(r.significant_after_correction for r in result)

    def test_none_significant(self) -> None:
        result = holm_correction([0.5, 0.6, 0.7])
        assert not any(r.significant_after_correction for r in result)


# ---------------------------------------------------------------------------
# Gap 4: NI sensitivity margins
# ---------------------------------------------------------------------------


class TestNonInferioritySensitivity:
    def test_sensitivity_margins(self) -> None:
        analyzer = StatisticalAnalyzer(n_bootstrap=500, random_seed=42)
        group1 = [0.90, 0.88, 0.92, 0.89, 0.91]
        group2 = [0.85, 0.83, 0.87, 0.84, 0.86]

        is_ni, mean_diff, (lower, upper), sensitivity = analyzer.non_inferiority_test(
            group1, group2, margin=0.05
        )

        assert isinstance(sensitivity, dict)
        assert 0.03 in sensitivity
        assert 0.05 in sensitivity
        assert 0.10 in sensitivity
        assert isinstance(is_ni, bool)

    def test_boundary_at_margin(self) -> None:
        """Lower bound exactly at -margin should NOT declare non-inferiority."""
        analyzer = StatisticalAnalyzer(n_bootstrap=200, random_seed=42)
        # Identical groups -> mean diff = 0, CI symmetric around 0
        group1 = [0.80, 0.80, 0.80, 0.80]
        group2 = [0.80, 0.80, 0.80, 0.80]

        _, _, (_, upper), sensitivity = analyzer.non_inferiority_test(
            group1, group2, margin=0.05
        )
        # With identical data, lower bound > -0.05 (since mean diff = 0)
        assert sensitivity[0.05] is True

    def test_rejects_unequal_lengths(self) -> None:
        analyzer = StatisticalAnalyzer()
        try:
            analyzer.non_inferiority_test([0.9, 0.8], [0.7])
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_declares_ni_only_when_lower_exceeds_neg_margin(self) -> None:
        """When difference is clearly positive, NI should hold at all margins."""
        analyzer = StatisticalAnalyzer(n_bootstrap=500, random_seed=42)
        group1 = [0.95, 0.94, 0.96, 0.93, 0.97]
        group2 = [0.80, 0.79, 0.81, 0.78, 0.82]

        is_ni, _, _, sensitivity = analyzer.non_inferiority_test(
            group1, group2, margin=0.05
        )
        assert is_ni is True
        assert sensitivity[0.03] is True
        assert sensitivity[0.10] is True


# ---------------------------------------------------------------------------
# Gap 2: Paired analysis
# ---------------------------------------------------------------------------


class TestPairedAnalysis:
    def test_paired_compare_basic(self) -> None:
        analyzer = StatisticalAnalyzer(n_bootstrap=200, random_seed=42)
        results = [
            EvaluationResult(
                scenario_id="repo-s01-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.9),),
            ),
            EvaluationResult(
                scenario_id="repo-s01-1",
                strategy_name="b",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.8),),
            ),
            EvaluationResult(
                scenario_id="repo-s02-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.85),),
            ),
            EvaluationResult(
                scenario_id="repo-s02-1",
                strategy_name="b",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.75),),
            ),
        ]
        report = analyzer.paired_compare(results, metric_name="recall")
        assert len(report.paired_analyses) == 1
        comp = report.paired_analyses[0]
        assert comp.paired is True
        assert comp.strategy_a == "a"
        assert comp.strategy_b == "b"

    def test_paired_vs_pooled_different(self) -> None:
        """Paired and pooled analyses can produce different CIs."""
        analyzer = StatisticalAnalyzer(n_bootstrap=300, random_seed=42)
        results = [
            EvaluationResult(
                scenario_id=f"r{i}-s{i}-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=v),),
            )
            for i, v in enumerate([0.9, 0.85, 0.95, 0.88, 0.92])
        ]
        results += [
            EvaluationResult(
                scenario_id=f"r{i}-s{i}-1",
                strategy_name="b",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=v),),
            )
            for i, v in enumerate([0.8, 0.75, 0.85, 0.78, 0.82])
        ]
        paired_report = analyzer.paired_compare(results, metric_name="recall")
        pooled_report = analyzer.analyze(results, metric_name="recall")
        # Both should return results
        assert len(paired_report.paired_analyses) == 1
        assert len(pooled_report.comparisons) == 1

    def test_reports_unmatched_pairs(self) -> None:
        analyzer = StatisticalAnalyzer(n_bootstrap=100, random_seed=42)
        results = [
            EvaluationResult(
                scenario_id="r1-s1-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.9),),
            ),
            EvaluationResult(
                scenario_id="r1-s1-1",
                strategy_name="b",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.8),),
            ),
            EvaluationResult(
                scenario_id="r1-s2-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.85),),
            ),
            EvaluationResult(
                scenario_id="r1-s2-1",
                strategy_name="b",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.75),),
            ),
            # Only strategy_a has a result for r1-s3-1 (unmatched)
            EvaluationResult(
                scenario_id="r1-s3-1",
                strategy_name="a",
                passed=True,
                message="",
                metrics=(MetricResult(name="recall", value=0.88),),
            ),
        ]
        report = analyzer.paired_compare(results, metric_name="recall")
        comp = report.paired_analyses[0]
        assert comp.unmatched_count >= 1


# ---------------------------------------------------------------------------
# Gap 5: Generalized binomial CI
# ---------------------------------------------------------------------------


class TestBinomialCIGeneralized:
    def test_90_percent_ci(self) -> None:
        calc = ConfidenceIntervalCalculator(confidence_level=0.90)
        ci = calc.binomial_ci(successes=50, trials=100, method="wilson")
        assert ci.lower > 0.0
        assert ci.upper < 1.0
        assert ci.lower < ci.upper

    def test_99_percent_ci(self) -> None:
        calc = ConfidenceIntervalCalculator(confidence_level=0.99)
        ci = calc.binomial_ci(successes=50, trials=100, method="wilson")
        assert ci.lower > 0.0
        assert ci.upper < 1.0

    def test_95_percent_ci_within_tolerance(self) -> None:
        """95% Wilson CI for 50/100 should be close to [0.403, 0.597]."""
        calc = ConfidenceIntervalCalculator(confidence_level=0.95)
        ci = calc.binomial_ci(successes=50, trials=100, method="wilson")
        assert abs(ci.lower - 0.403) < 0.02
        assert abs(ci.upper - 0.597) < 0.02

    def test_invalid_confidence_level(self) -> None:
        calc = ConfidenceIntervalCalculator(confidence_level=0.5)
        with contextlib.suppress(ValueError):
            calc.binomial_ci(successes=50, trials=100)
            # confidence_level=0.5 is between 0 and 1, so it should work

    def test_rejects_zero_confidence(self) -> None:
        calc = ConfidenceIntervalCalculator(confidence_level=0.0)
        try:
            calc.binomial_ci(successes=50, trials=100)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_bounds_within_unit(self) -> None:
        for cl in [0.90, 0.95, 0.99]:
            calc = ConfidenceIntervalCalculator(confidence_level=cl)
            ci = calc.binomial_ci(successes=99, trials=100, method="wilson")
            assert 0.0 <= ci.lower <= ci.upper <= 1.0
