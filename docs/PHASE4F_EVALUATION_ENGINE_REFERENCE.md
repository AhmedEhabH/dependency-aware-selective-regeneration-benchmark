# Phase 4F Evaluation Engine — Reference

**Version:** 1.0  
**Status:** FROZEN

---

## Overview

The Evaluation Engine provides the scientific evaluation pipeline for comparing strategy predictions against ground truth. It computes metrics, performs statistical analysis, and generates publication-ready outputs.

---

## Architecture

### Layer 5 — Evaluation

The evaluation layer sits after the execution layer (Phase 4D) and before final reporting. It processes `RunRecord` objects and produces `EvaluationResult` objects.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Evaluation Engine                           │
├─────────────────────────────────────────────────────────────────┤
│  EvaluationEngine  →  MetricComputer  →  GroundTruthComparator  │
│  ResultAggregator  →  StatisticalAnalyzer  →  NotebookExporter   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Classes and Interfaces

### EvaluationEngine

Main entry point for evaluating a single run.

```python
class EvaluationEngine:
    def evaluate(self, run_record: RunRecord, ground_truth: ImpactPrediction) -> EvaluationResult:
        ...
```

### MetricComputer

Computes all primary and secondary metrics.

```python
class MetricComputer:
    def compute_all(self, prediction: ImpactPrediction, ground_truth: ImpactPrediction) -> tuple[MetricResult, ...]:
        ...
```

### GroundTruthComparator

Compares predictions against ground truth.

```python
class GroundTruthComparator:
    def compare(self, prediction: ImpactPrediction, scenario: Scenario) -> ImpactPrediction:
        ...
    
    def compute_match_rate(self, prediction: ImpactPrediction, scenario: Scenario) -> float:
        ...
```

### ResultAggregator

Aggregates results across strategies and repositories.

```python
class ResultAggregator:
    def add_result(self, result: EvaluationResult) -> None:
        ...
    
    def aggregate_by_strategy(self) -> tuple[AggregatedMetrics, ...]:
        ...
    
    def aggregate_all(self) -> AggregatedResult:
        ...
```

### StatisticalAnalyzer

Performs statistical analysis with confidence intervals and effect sizes.

```python
class StatisticalAnalyzer:
    def analyze(self, results: list[EvaluationResult], metric_name: str = "recall") -> StatisticalAnalysisReport:
        ...
    
    def non_inferiority_test(self, group1: list[float], group2: list[float], margin: float) -> tuple[bool, float, tuple[float, float]]:
        ...
```

### NotebookExporter

Exports results in notebook-ready format.

```python
class NotebookExporter:
    def export(self, results: tuple[EvaluationResult, ...], records: tuple[RunRecord, ...] | None = None) -> dict[str, Any]:
        ...
    
    def export_to_dataframe(self, results: tuple[EvaluationResult, ...]) -> pd.DataFrame:
        ...
```

### PublicationTableBuilder

Builds publication-ready tables.

```python
class PublicationTableBuilder:
    def build_strategy_comparison_table(self, results: tuple[EvaluationResult, ...]) -> pd.DataFrame:
        ...
    
    def build_latex_table(self, df: pd.DataFrame, caption: str, label: str) -> str:
        ...
```

---

## Metrics Reference

| Metric | Formula | Threshold |
|--------|---------|-----------|
| Recall | TP / (TP + FN) | ≥ 0.80 |
| Precision | TP / (TP + FP) | ≥ 0.80 |
| F1 Score | 2 × P × R / (P + R) | — |
| Specificity | TN / (TN + FP) | — |
| FPR | FP / (FP + TN) | — |
| FNR | FN / (FN + TP) | — |
| Accuracy | Correct / Total | — |
| Action Accuracy | Correct actions / Total actions | ≥ 0.90 |

---

## Statistical Methods

### Confidence Intervals

Uses bootstrap percentile method with 1000 resamples by default.

### Effect Sizes

- **Cohen's d:** For normally distributed outcomes
- **Cliff's delta:** For non-parametric comparisons

### Non-Inferiority Testing

H2 (preservation) tests use Δ = 0.05 margin per DA-08.

---

## Export Formats

### JSON Structure

```json
{
  "version": "1.0",
  "exported_at": "2026-07-22T00:00:00Z",
  "results_count": N,
  "results": [
    {
      "scenario_id": "str",
      "strategy_name": "str",
      "passed": bool,
      "message": "str",
      "metrics": [...]
    }
  ]
}
```

### DataFrame Columns

- `Scenario`, `Strategy`, `Passed`
- Dynamic metric columns based on computed metrics

---

## Dependencies

- `numpy>=1.24,<2`
- `scipy>=1.10,<2`
- `pandas>=2.0,<3`

---

## Integration Notes

1. Load ground truth from scenario `expected_actions`
2. Run `EvaluationEngine.evaluate()` for each `RunRecord`
3. Use `ResultAggregator` to combine results
4. Apply `StatisticalAnalyzer` for comparisons
5. Export via `NotebookExporter` or `PublicationTableBuilder`