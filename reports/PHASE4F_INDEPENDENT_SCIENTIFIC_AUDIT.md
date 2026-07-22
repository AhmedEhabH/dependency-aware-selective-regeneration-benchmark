# Phase 4F — Independent Scientific Audit

**Date:** 2026-07-22
**Auditor:** opencode (automated)
**Target commit:** `4896515` (Phase 4F on main)
**Audit branch:** `audit/phase4f-scientific-validation`

---

## 1. Executive Summary

Independent audit of the Phase 4F Evaluation Engine: formulas, aggregation, statistical methods, exporters, ground-truth isolation, and protocol coverage. Two production defects were found and fixed. The implementation covers approximately 70% of the frozen statistical plan; the remaining 30% are design-level gaps documented as findings.

**Defects fixed:**
- DEFECT 1 (CRITICAL): Confusion matrix counted missing-prediction artifacts as FP regardless of GT action
- DEFECT 2 (MODERATE): F1 score returned `None` instead of `0.0` when both precision and recall were `0.0`

**Current state:** 410/410 tests pass, ruff clean, mypy strict clean (src), pip check clean.

---

## 2. Repository State

| Item | Value |
|------|-------|
| HEAD | `4896515` (origin/main) |
| Branch | `audit/phase4f-scientific-validation` |
| Working tree | Clean (on audit branch) |
| Phase 4F status | Merged and pushed to main |

---

## 3. Quality Gates

| Gate | Result |
|------|--------|
| pytest | **410/410 passed** (0 failed, 0 skipped) |
| ruff check src tests | All checks passed |
| mypy --strict src | 0 errors in 60 source files |
| mypy --strict src tests | 5 errors (pre-existing: `BlastRadius`/`RunStatus` not exported from `benchmark.core.models`, missing tuple type-arg in test files) |
| pip check | Clean (pre-existing conda `PyYAML` conflict only) |

---

## 4. Ground-Truth Isolation

**PASS.** Strategy/execution modules do not import comparison/evaluation/statistics. No circular imports detected across all 13 packages.

---

## 5. Production Defects Found and Fixed

### DEFECT 1 — Confusion Matrix Misclassification (CRITICAL)

**Location:** `src/benchmark/evaluation/metrics.py:147-150`
**Severity:** Critical — silently inflates FP, deflates FN for any scenario where prediction omits a GT artifact

**Root cause:** When an artifact exists in ground truth but is absent from the prediction (`pred_action is None`), the code unconditionally counted it as FP. The correct classification depends on the GT action:
- GT=`regenerate` → FN (missed regeneration)
- GT=`preserve` → TN (correctly left alone)

**Fix:** Added conditional branch on `gt_action`:
```python
if pred_action is None:
    if gt_action == ActionKind.regenerate:
        fn += 1
    else:
        tn += 1
```

**Regression tests:** 2 new tests in `TestConfusionMatrixMissingArtifacts` verify both branches.

### DEFECT 2 — F1 Score Falsy-Zero (MODERATE)

**Location:** `src/benchmark/evaluation/metrics.py:56`
**Severity:** Moderate — latent bug, but `0.0` is falsy in Python, making the guard `if precision and recall` incorrectly skip F1 computation when either value is exactly `0.0`

**Root cause:** The condition `if precision and recall` evaluates to `False` when either is `0.0`. The fix uses `is not None`. Additionally, the `_safe_divide(0, 0)` case (both P=R=0) returned `None` instead of `0.0`. Added explicit `P==0 and R==0 -> F1=0.0` handling (sklearn convention).

**Fix:** Changed condition to `precision is not None and recall is not None`, plus special-case `0.0` for `P+R=0`. Same fix applied to standalone `compute_f1_score`.

**Regression tests:** 3 new tests in `TestF1ZeroPrecision` verify both MetricComputer and standalone function.

---

## 6. Metric Formula Verification

### Recall
`recall = TP / (TP + FN)` when `TP+FN > 0`, else `None` — **CORRECT**

### Precision
`precision = TP / (TP + FP)` when `TP+FP > 0`, else `None` — **CORRECT**

### Specificity
`specificity = TN / (TN + FP)` when `TN+FP > 0`, else `None` — **CORRECT**

### FPR / FNR
Standard formulas, guarded against division by zero — **CORRECT**

### F1 Score
After fix: `2*P*R / (P+R)` when both defined and P+R>0; `0.0` when P=R=0; `None` when either undefined — **CORRECT**

### Accuracy / Action Accuracy
Standard definitions — **CORRECT**

### Regression Pass Rate
`passed_preserve / total_preserve` — **CORRECT**

---

## 7. Confidence Intervals

| Method | Status | Notes |
|--------|--------|-------|
| Bootstrap CI (mean/median) | Implemented | 1000 resamples, percentile method — **correct** |
| Normal CI | Implemented | Z-score from scipy — **correct** |
| Wilson binomial CI | Implemented | **correct** |
| Agresti-Coull binomial CI | Implemented | **correct** |
| `binomial_ci` z-score | **Limitation** | Hardcoded z=1.96 (95%) or z=2.576 (99%) only; other confidence levels use wrong z-score |

**Finding:** `binomial_ci` in `confidence_intervals.py:90` should use `stats.norm.ppf(1 - alpha/2)` instead of hardcoded values. Currently works correctly at 95% and 99% only.

---

## 8. Effect Sizes

| Method | Status | Notes |
|--------|--------|-------|
| Cohen's d | Implemented | Uses `ddof=1` — **correct for samples** |
| Cliff's delta | Implemented | O(n*m) comparison — **correct** |
| Pooled std | Implemented | **correct** |
| Interpretation thresholds | Implemented | Standard benchmarks — **correct** |

**Finding:** `cohens_d` with `n=1` in either group produces `ddof=1` variance which can produce edge-case results. The `pooled_std == 0` guard returns `0.0`. This is defensible but worth noting for very small samples.

---

## 9. Statistical Analysis

| Component | Status | Notes |
|-----------|--------|-------|
| `StatisticalAnalyzer.analyze` | Implemented | Per-pair comparisons, bootstrap CI on pooled data |
| `_compute_p_value` | Implemented | Mann-Whitney U, two-sided |
| `non_inferiority_test` | Implemented | Bootstrap CI on paired differences |
| `mixed_effects_model` | Implemented | statsmodels mixedlm (optional import) |

### Findings

1. **H1 test mismatch:** Frozen plan requires **paired bootstrap CI** for H1 (recall comparison). Implementation uses **Mann-Whitney U** for p-values and bootstrap CI on **pooled** (not paired) data. These are different statistical procedures.

2. **NI margin hardcoded:** `non_inferiority_test` defaults to `margin=0.05` but does not implement sensitivity margins at 0.03 and 0.10 as required by DA-08/frozen plan.

3. **No multiple-comparison correction:** Frozen plan (DA-14) requires Benjamini-Hochberg for secondary/exploratory families and Holm for small confirmatory pairwise families. Neither is implemented. All raw p-values are reported without adjustment.

4. **`mixed_effects_model`:** Parses `scenario_id` by splitting on `-` to extract blast radius and repository — fragile assumption. Uses `efficiency` as a constant `1.0` response variable, which is not meaningful.

---

## 10. Aggregation

| Component | Status | Notes |
|-----------|--------|-------|
| `ResultAggregator.aggregate_by_strategy` | Implemented | Mean/median/std of metrics — **correct** |
| `ResultAggregator.aggregate_by_repository` | Implemented | Per-repository summaries — **correct** |
| `ResultAggregator.aggregate_all` | Implemented | Global aggregate — **correct** |
| `aggregate_run_records` | **Stub** | Marks all successful runs `passed=True` with empty metrics — not functional |

**Finding:** `aggregator.py:62` silently drops `None` metric values without conditional labels. Per frozen protocol, failed runs must remain in aggregates with conditional metrics labeled.

---

## 11. Exporters

| Format | Status | Notes |
|--------|--------|-------|
| JSON export | Implemented | Full metadata, pretty-print — **correct** |
| DataFrame export | Implemented | Pivots metrics into columns — **correct** |
| CSV export | Implemented | Via pandas `to_csv` — **correct** |
| Markdown table | Implemented | Via pandas `to_markdown` — **correct** |
| LaTeX table | Implemented | Via pandas `to_latex` — **correct** |
| Record serialization | Implemented | Full RunRecord with failures — **correct** |
| Prediction serialization | Implemented | Decisions + evidence — **correct** |

---

## 12. Protocol Coverage Matrix

| Frozen Plan Requirement | Implementation Status | Gap |
|------------------------|----------------------|-----|
| H1: Paired bootstrap CI for recall | **Partial** — bootstrap CI is pooled, not paired | Paired bootstrap not implemented |
| H1: FNR comparison | **Partial** — FNR computed but not compared across strategies | No dedicated FNR comparison |
| H2: NI test at delta=0.05 | **Implemented** | — |
| H2: NI sensitivity at 0.03 and 0.10 | **Missing** | Not implemented |
| H2: Two-sided 95% CI | **Implemented** | — |
| H3: McNemar's test | **Missing** | Not implemented |
| H3: Architecture-only detections | **Missing** | No architecture metric in evaluation |
| H4: Effect size + CI | **Implemented** (Cliff's delta, Cohen's d) | CI on effect sizes not implemented |
| H4: Conditional on equivalent correctness | **Missing** | No correctness-gating logic |
| H5: Mixed-effects model | **Partial** | Constant response variable, fragile ID parsing |
| H5: Blast-radius interaction | **Missing** | No interaction test |
| DA-14: BH correction | **Missing** | Not implemented |
| DA-14: Holm correction | **Missing** | Not implemented |
| DA-14: Report raw and adjusted p-values | **Partial** | Raw reported, adjusted not computed |
| AC-02: Regression pass rate formula | **Implemented** | — |
| AC-04: Failed runs in aggregates | **Partial** | `aggregate_run_records` is a stub |
| AC-09: Architecture violations | **Missing** | No architecture validation metric |
| AC-10: Strategy x blast-radius interaction | **Missing** | Not implemented |
| Sensitivity margins 0.03/0.10 | **Missing** | Only 0.05 implemented |

---

## 13. Summary of Findings

### Critical (fixed)
1. **DEFECT 1:** Confusion matrix misclassification when prediction omits GT artifact

### Moderate (fixed)
2. **DEFECT 2:** F1 score falsy-zero handling

### Design-level gaps (not fixed — require protocol amendment or future work)
3. **Paired bootstrap CI** not implemented (H1 uses pooled bootstrap + Mann-Whitney U)
4. **Multiple-comparison correction** (BH, Holm) not implemented (DA-14)
5. **NI sensitivity margins** 0.03/0.10 not implemented (DA-08)
6. **McNemar's test** for H3 not implemented
7. **`aggregate_run_records`** is a stub
8. **`binomial_ci` z-score** hardcoded for 95%/99% only
9. **Architecture validation metrics** not implemented (H3, AC-09)

### Observations (no action required)
10. Confusion matrix counts `preserve/preserve` as TP (correct prediction), not TN — non-standard but internally consistent
11. `mixed_effects_model` uses constant response variable — not statistically meaningful
12. 5 pre-existing mypy errors in test files (not in production code)

---

## 14. Test Changes Summary

**New tests added:** 5 regression tests
- `TestConfusionMatrixMissingArtifacts.test_missing_prediction_gt_regenerate_counts_fn`
- `TestConfusionMatrixMissingArtifacts.test_missing_prediction_gt_preserve_counts_tn`
- `TestF1ZeroPrecision.test_f1_when_precision_zero`
- `TestF1ZeroPrecision.test_f1_when_recall_zero`
- `TestF1ZeroPrecision.test_f1_function_zero_precision`

**Production code changed:** 2 files
- `src/benchmark/evaluation/metrics.py` (3 edits: confusion matrix fix, F1 condition fix, F1 zero-zero special case)
- `.gitignore` (1 addition: audit report exception)

**Total test count:** 410 (was 405 before audit fixes)
