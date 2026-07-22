from __future__ import annotations

from benchmark.evaluation.engine import EvaluationResult
from benchmark.statistics.analysis import StatisticalAnalysisReport, StatisticalAnalyzer, StatisticalComparison
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

        is_ni, mean_diff, (lower, upper) = analyzer.non_inferiority_test(group1, group2, margin=0.1)

        assert isinstance(is_ni, bool)
        assert isinstance(mean_diff, float)
        assert isinstance(lower, float)
        assert isinstance(upper, float)


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
