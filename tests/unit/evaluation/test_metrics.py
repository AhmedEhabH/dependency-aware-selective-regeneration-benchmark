from __future__ import annotations

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, ImpactDecision, ImpactPrediction
from benchmark.evaluation.metrics import (
    MetricComputer,
    MetricResult,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_regression_pass_rate,
)


def _make_prediction() -> ImpactPrediction:
    return ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="test",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                action=ActionKind.preserve,
                rationale="test",
            ),
        )
    )


def _make_ground_truth() -> ImpactPrediction:
    return ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="expected",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="expected",
            ),
        )
    )


class TestMetricResult:
    def test_validation(self) -> None:
        try:
            MetricResult(name="", value=0.5)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "name" in str(e)


class TestMetricComputer:
    def test_compute_all_metrics(self) -> None:
        computer = MetricComputer()
        prediction = _make_prediction()
        ground_truth = _make_ground_truth()

        metrics = computer.compute_all(prediction, ground_truth)

        assert len(metrics) >= 6
        metric_names = {m.name for m in metrics}
        assert "recall" in metric_names
        assert "precision" in metric_names
        assert "f1_score" in metric_names
        assert "specificity" in metric_names
        assert "false_positive_rate" in metric_names
        assert "false_negative_rate" in metric_names

    def test_compute_all_with_secondary(self) -> None:
        computer = MetricComputer(include_secondary=True)
        prediction = _make_prediction()
        ground_truth = _make_ground_truth()

        metrics = computer.compute_all(prediction, ground_truth)
        metric_names = {m.name for m in metrics}

        assert "accuracy" in metric_names
        assert "action_accuracy" in metric_names

    def test_compute_all_without_secondary(self) -> None:
        computer = MetricComputer(include_secondary=False)
        prediction = _make_prediction()
        ground_truth = _make_ground_truth()

        metrics = computer.compute_all(prediction, ground_truth)
        metric_names = {m.name for m in metrics}

        assert "accuracy" not in metric_names
        assert "action_accuracy" not in metric_names

    def test_perfect_match(self) -> None:
        computer = MetricComputer()
        prediction = _make_prediction()
        ground_truth = ImpactPrediction(
            decisions=_make_prediction().decisions
        )

        metrics = computer.compute_all(prediction, ground_truth)

        recall_metric = next(m for m in metrics if m.name == "recall")
        precision_metric = next(m for m in metrics if m.name == "precision")
        f1_metric = next(m for m in metrics if m.name == "f1_score")

        assert recall_metric.value == 1.0
        assert precision_metric.value == 1.0
        assert f1_metric.value == 1.0

    def test_empty_predictions(self) -> None:
        computer = MetricComputer()
        prediction = ImpactPrediction(decisions=())
        ground_truth = _make_ground_truth()

        metrics = computer.compute_all(prediction, ground_truth)

        assert all(m.value is None or m.value >= 0 for m in metrics)


class TestComputeRecall:
    def test_perfect_recall(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )

        recall = compute_recall(prediction, ground_truth)
        assert recall == 1.0

    def test_zero_recall(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )

        recall = compute_recall(prediction, ground_truth)
        assert recall == 0.0


class TestComputePrecision:
    def test_perfect_precision(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )

        precision = compute_precision(prediction, ground_truth)
        assert precision == 1.0

    def test_zero_precision(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )

        precision = compute_precision(prediction, ground_truth)
        assert precision == 0.0


class TestComputeF1Score:
    def test_perfect_f1(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )

        f1 = compute_f1_score(prediction, ground_truth)
        assert f1 == 1.0


class TestComputeRegressionPassRate:
    def test_all_preserved(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="expected",
                ),
            )
        )

        rate = compute_regression_pass_rate(prediction, ground_truth)
        assert rate == 1.0

    def test_some_regression(self) -> None:
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        ground_truth = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="expected",
                ),
            )
        )

        rate = compute_regression_pass_rate(prediction, ground_truth)
        assert rate == 0.0


class TestConfusionMatrixMissingArtifacts:
    """Regression tests for DEFECT 1: artifacts in GT but missing from prediction."""

    def test_missing_prediction_gt_regenerate_counts_fn(self) -> None:
        """When GT=regenerate and prediction omits artifact, should be FN (missed regeneration)."""
        computer = MetricComputer()
        gt = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )
        pred = ImpactPrediction(decisions=())  # missing artifact

        metrics = computer.compute_all(pred, gt)
        recall_m = next(m for m in metrics if m.name == "recall")
        fnr_m = next(m for m in metrics if m.name == "false_negative_rate")
        fpr_m = next(m for m in metrics if m.name == "false_positive_rate")

        # Should be FN, not FP: recall=0.0, fnr=1.0
        assert recall_m.value == 0.0
        assert fnr_m.value == 1.0
        # FPR is None because there are no negative cases (fp+tn=0)
        assert fpr_m.value is None

    def test_missing_prediction_gt_preserve_counts_tn(self) -> None:
        """When GT=preserve and prediction omits artifact, should be TN (correctly left alone)."""
        computer = MetricComputer()
        gt = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="expected",
                ),
            )
        )
        pred = ImpactPrediction(decisions=())  # missing artifact

        metrics = computer.compute_all(pred, gt)
        specificity_m = next(m for m in metrics if m.name == "specificity")
        fpr_m = next(m for m in metrics if m.name == "false_positive_rate")

        # Should be TN: specificity=1.0, fpr=0.0
        assert specificity_m.value == 1.0
        assert fpr_m.value == 0.0


class TestF1ZeroPrecision:
    """Regression tests for DEFECT 2: F1 must return 0.0 when precision or recall is 0.0."""

    def test_f1_when_precision_zero(self) -> None:
        """When precision=0.0 and recall=0.0, F1 must be 0.0, not None."""
        computer = MetricComputer()
        # GT has a.py=regenerate, pred has b.py=regenerate (wrong artifact)
        # tp=0, fp=1 (b.py), fn=1 (a.py) → precision=0.0, recall=0.0
        gt = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )
        pred = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )

        metrics = computer.compute_all(pred, gt)
        f1_m = next(m for m in metrics if m.name == "f1_score")
        assert f1_m.value == 0.0, f"F1 should be 0.0 when precision=0.0 and recall=0.0, got {f1_m.value}"

    def test_f1_when_recall_zero(self) -> None:
        """When precision=0.0 and recall=0.0, F1 must be 0.0, not None."""
        computer = MetricComputer()
        # All predictions wrong: pred flips every action
        # GT: a=regenerate, b=preserve → Pred: a=preserve, b=regenerate
        # tp=0, fp=1 (b), fn=1 (a) → precision=0.0, recall=0.0
        gt = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
                ImpactDecision(
                    artifact=ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="expected",
                ),
            )
        )
        pred = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                    rationale="test",
                ),
                ImpactDecision(
                    artifact=ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )

        metrics = computer.compute_all(pred, gt)
        f1_m = next(m for m in metrics if m.name == "f1_score")
        assert f1_m.value == 0.0, f"F1 should be 0.0 when precision=0.0 and recall=0.0, got {f1_m.value}"

    def test_f1_function_zero_precision(self) -> None:
        """Standalone compute_f1_score also returns 0.0 when both precision and recall are 0.0."""
        pred = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )
        gt = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="expected",
                ),
            )
        )
        # pred has a.py=regenerate, gt has b.py=regenerate → tp=0, fp=1, fn=1
        # precision=0.0, recall=0.0 → F1=0.0
        f1 = compute_f1_score(pred, gt)
        assert f1 == 0.0, f"compute_f1_score should return 0.0 with zero precision, got {f1}"
