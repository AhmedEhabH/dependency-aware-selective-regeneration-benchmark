from __future__ import annotations

from dataclasses import dataclass, field

from benchmark.core.enums import ActionKind
from benchmark.core.models import ImpactPrediction


@dataclass(frozen=True)
class MetricResult:
    name: str
    value: float | None
    unit: str = ""
    details: dict[str, float | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MetricResult.name must not be empty")


class MetricComputer:
    def __init__(self, include_secondary: bool = True) -> None:
        self._include_secondary = include_secondary

    def compute_all(
        self,
        prediction: ImpactPrediction,
        ground_truth: ImpactPrediction,
    ) -> tuple[MetricResult, ...]:
        metrics: list[MetricResult] = []

        primary_metrics = self._compute_primary_metrics(prediction, ground_truth)
        metrics.extend(primary_metrics)

        if self._include_secondary:
            secondary_metrics = self._compute_secondary_metrics(prediction, ground_truth)
            metrics.extend(secondary_metrics)

        return tuple(metrics)

    def _compute_primary_metrics(
        self,
        prediction: ImpactPrediction,
        ground_truth: ImpactPrediction,
    ) -> tuple[MetricResult, ...]:
        gt_dict = self._build_action_dict(ground_truth)
        pred_dict = self._build_action_dict(prediction)

        tp, fp, tn, fn = self._compute_confusion_matrix(gt_dict, pred_dict)

        recall = self._safe_divide(tp, tp + fn) if (tp + fn) > 0 else None
        precision = self._safe_divide(tp, tp + fp) if (tp + fp) > 0 else None
        fpr = self._safe_divide(fp, fp + tn) if (fp + tn) > 0 else None
        fnr = self._safe_divide(fn, fn + tp) if (fn + tp) > 0 else None
        specificity = self._safe_divide(tn, tn + fp) if (tn + fp) > 0 else None
        f1 = (
            0.0
            if precision == 0.0 and recall == 0.0
            else self._safe_divide(2 * precision * recall, precision + recall)
            if precision is not None and recall is not None
            else None
        )

        return (
            MetricResult(
                name="recall",
                value=recall,
                unit="proportion",
                details={"tp": float(tp), "fn": float(fn), "total_pos": float(tp + fn)},
            ),
            MetricResult(
                name="precision",
                value=precision,
                unit="proportion",
                details={"tp": float(tp), "fp": float(fp), "total_pred_pos": float(tp + fp)},
            ),
            MetricResult(
                name="f1_score",
                value=f1,
                unit="proportion",
                details={"precision": precision, "recall": recall},
            ),
            MetricResult(
                name="specificity",
                value=specificity,
                unit="proportion",
                details={"tn": float(tn), "fp": float(fp), "total_neg": float(tn + fp)},
            ),
            MetricResult(
                name="false_positive_rate",
                value=fpr,
                unit="proportion",
                details={"fp": float(fp), "tn": float(tn)},
            ),
            MetricResult(
                name="false_negative_rate",
                value=fnr,
                unit="proportion",
                details={"fn": float(fn), "tp": float(tp)},
            ),
        )

    def _compute_secondary_metrics(
        self,
        prediction: ImpactPrediction,
        ground_truth: ImpactPrediction,
    ) -> tuple[MetricResult, ...]:
        gt_dict = self._build_action_dict(ground_truth)
        pred_dict = self._build_action_dict(prediction)

        all_artifacts = set(gt_dict.keys()) | set(pred_dict.keys())

        correct_predictions = sum(1 for a in all_artifacts if pred_dict.get(a) == gt_dict.get(a))
        total_predictions = len(all_artifacts)

        accuracy = self._safe_divide(correct_predictions, total_predictions) if total_predictions > 0 else None

        total_actions = len(gt_dict)
        correct_actions = sum(1 for a in gt_dict if pred_dict.get(a) == gt_dict[a])
        action_accuracy = self._safe_divide(correct_actions, total_actions) if total_actions > 0 else None

        return (
            MetricResult(
                name="accuracy",
                value=accuracy,
                unit="proportion",
                details={"correct": float(correct_predictions), "total": float(total_predictions)},
            ),
            MetricResult(
                name="action_accuracy",
                value=action_accuracy,
                unit="proportion",
                details={"correct": float(correct_actions), "total": float(total_actions)},
            ),
        )

    def _build_action_dict(self, prediction: ImpactPrediction) -> dict[str, ActionKind]:
        result: dict[str, ActionKind] = {}
        for decision in prediction.decisions:
            result[decision.artifact.path] = decision.action
        return result

    def _compute_confusion_matrix(
        self,
        gt: dict[str, ActionKind],
        pred: dict[str, ActionKind],
    ) -> tuple[int, int, int, int]:
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for artifact, gt_action in gt.items():
            pred_action = pred.get(artifact)
            if pred_action is None:
                if gt_action == ActionKind.regenerate:
                    fn += 1
                else:
                    tn += 1
            elif pred_action == gt_action:
                tp += 1
            elif pred_action == ActionKind.regenerate and gt_action == ActionKind.preserve:
                fp += 1
            elif pred_action == ActionKind.preserve and gt_action == ActionKind.regenerate:
                fn += 1
            else:
                fp += 1

        for artifact, pred_action in pred.items():
            if artifact not in gt:
                if pred_action == ActionKind.preserve:
                    tn += 1
                else:
                    fp += 1

        return tp, fp, tn, fn

    def _safe_divide(self, numerator: float | int, denominator: float | int) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator


def compute_recall(
    prediction: ImpactPrediction,
    ground_truth: ImpactPrediction,
) -> float | None:
    gt_dict = {d.artifact.path: d.action for d in ground_truth.decisions}
    pred_dict = {d.artifact.path: d.action for d in prediction.decisions}

    tp = sum(1 for a in gt_dict if pred_dict.get(a) == gt_dict[a] and gt_dict[a] == ActionKind.regenerate)
    fn = sum(1 for a in gt_dict if pred_dict.get(a) != gt_dict[a] and gt_dict[a] == ActionKind.regenerate)

    if tp + fn == 0:
        return None
    return tp / (tp + fn)


def compute_precision(
    prediction: ImpactPrediction,
    ground_truth: ImpactPrediction,
) -> float | None:
    gt_dict = {d.artifact.path: d.action for d in ground_truth.decisions}
    pred_dict = {d.artifact.path: d.action for d in prediction.decisions}

    tp = sum(1 for a in gt_dict if pred_dict.get(a) == gt_dict[a] and gt_dict[a] == ActionKind.regenerate)
    fp = sum(1 for a in pred_dict if pred_dict[a] == ActionKind.regenerate and a not in gt_dict)

    if tp + fp == 0:
        return None
    return tp / (tp + fp)


def compute_f1_score(
    prediction: ImpactPrediction,
    ground_truth: ImpactPrediction,
) -> float | None:
    recall = compute_recall(prediction, ground_truth)
    precision = compute_precision(prediction, ground_truth)

    if recall is None or precision is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_regression_pass_rate(
    prediction: ImpactPrediction,
    ground_truth: ImpactPrediction,
) -> float | None:
    gt_dict = {d.artifact.path: d.action for d in ground_truth.decisions}
    pred_dict = {d.artifact.path: d.action for d in prediction.decisions}

    regression_tests = [a for a, action in gt_dict.items() if action == ActionKind.preserve]

    if not regression_tests:
        return None

    passed = sum(1 for a in regression_tests if pred_dict.get(a) == ActionKind.preserve)
    return passed / len(regression_tests)
