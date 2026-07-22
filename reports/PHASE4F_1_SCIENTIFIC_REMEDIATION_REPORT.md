# Phase 4F.1 — Scientific Evaluation Remediation

**Date:** 2026-07-23
**Branch:** `fix/phase4f-scientific-gaps`
**Status:** COMPLETE
**Base commit:** `0cb82a8` (Phase 4F audit merged to main)

---

## 1. Executive Summary

Closes 5 scientific gaps identified by the Phase 4F independent audit. The frozen statistical analysis plan now has 14 of 19 requirements implemented and validated (up from 9). Three design-level gaps remain (McNemar's test, architecture validation metrics, blast-radius interaction) requiring protocol amendment or future work.

**Key results:**
- `aggregate_run_records`: stub replaced with full macro/micro aggregation
- `paired_bootstrap_ci`: new paired analysis for H1
- `benjamini_hochberg` + `holm_correction`: multiple-comparison correction
- `non_inferiority_test`: sensitivity margins at 0.03 and 0.10
- `binomial_ci`: generalized z-score via `scipy.stats.norm.ppf`
- Bug fix: BH implementation corrected (was using descending sort + running-max, now uses ascending sort + step-down monotonicity)
- **441/441 tests pass**, ruff clean, mypy clean (src), 0 new regressions

---

## 2. Gaps Remediated

### Gap 1 — `aggregate_run_records` (AC-04)

**Problem:** Stub implementation that silently dropped None metric values without labels.

**Solution:** Full implementation in `src/benchmark/comparison/aggregator.py`:
- Per-record micro aggregation (one `EvaluationResult` per `RunRecord`)
- Macro aggregation: per-(strategy, repository) averages, then equal-weight repository averaging (not scenario-count-weighted)
- Conditional notes for failed runs
- Deterministic ordering (sorted by strategy_name, scenario_id)
- New types: `RunAggregationResult`, `IncompatibleRecordError`

**Tests:** 8 new tests in `TestAggregateRunRecords`

### Gap 2 — Paired Analysis for H1

**Problem:** H1 requires paired bootstrap CI; implementation used pooled bootstrap.

**Solution:** New methods in `src/benchmark/statistics/analysis.py`:
- `paired_bootstrap_ci()`: matches on (repository, scenario, repetition) cell
- `paired_compare()`: pairwise paired comparisons with unmatched-pair reporting
- Extended `StatisticalComparison` with `paired: bool` and `unmatched_count: int`
- Extended `StatisticalAnalysisReport` with `paired_analyses`

**Tests:** 3 new tests in `TestPairedAnalysis`

### Gap 3 — BH and Holm Corrections (DA-14)

**Problem:** No multiple-comparison correction implemented.

**Solution:** New functions in `src/benchmark/statistics/analysis.py`:
- `benjamini_hochberg()`: step-up procedure with ascending sort + step-down monotonicity enforcement
- `holm_correction()`: step-down Bonferroni with early stopping
- New `ComparisonResult` dataclass: `raw_p_value`, `adjusted_p_value`, `family`, `significant_after_correction`

**Tests:** 10 new tests (5 BH + 5 Holm)

### Gap 4 — NI Sensitivity Margins (DA-08)

**Problem:** `non_inferiority_test` only supported single margin=0.05.

**Solution:** Extended `non_inferiority_test()` in `src/benchmark/statistics/analysis.py`:
- New `sensitivity_margins` parameter (default `(0.03, 0.10)`)
- Returns 4-tuple: `(is_ni, mean_diff, ci_bounds, sensitivity_dict)`
- Sensitivity dict maps each margin to whether the NI test holds

**Tests:** 4 new tests in `TestNonInferioritySensitivity`

### Gap 5 — Generalized Binomial CI

**Problem:** `binomial_ci` used hardcoded z-scores (1.96 for 95%, 2.576 for 99%) — wrong for any other confidence level.

**Solution:** Replaced with `scipy.stats.norm.ppf(1 - alpha / 2)` in `src/benchmark/statistics/confidence_intervals.py`. Added `confidence_level` validation (must be in `(0, 1)`).

**Tests:** 5 new tests in `TestBinomialCIGeneralized`

---

## 3. Bug Fix Discovered During Remediation

**Bug:** `benjamini_hochberg` sorted p-values in descending order and used a running-max approach. This produced incorrect adjusted p-values (all dominated by the largest raw p-value).

**Root cause:** Descending sort + running-max is the wrong algorithm for BH step-up. The correct approach is ascending sort + step-down monotonicity enforcement.

**Fix:** Rewrote to sort ascending by p-value, compute `min(p * n / rank, 1)`, then enforce monotonicity by stepping down from rank n-1 to 1.

---

## 4. Quality Gates

| Gate | Result |
|------|--------|
| pytest | **441/441 passed** |
| ruff check src tests | All checks passed |
| mypy --strict src | 0 errors |
| mypy --strict src tests | 5 errors (pre-existing) |
| pip check | Clean |

---

## 5. Files Changed

### Production (5 files modified)
- `src/benchmark/comparison/aggregator.py` — `aggregate_run_records` full impl, `RunAggregationResult`, `IncompatibleRecordError`
- `src/benchmark/statistics/analysis.py` — `benjamini_hochberg()`, `holm_correction()`, `paired_bootstrap_ci()`, `paired_compare()`, `ComparisonResult`, NI sensitivity margins
- `src/benchmark/statistics/confidence_intervals.py` — generalized z-score
- `src/benchmark/comparison/__init__.py` — updated exports
- `src/benchmark/statistics/__init__.py` — updated exports

### Tests (2 files modified)
- `tests/unit/comparison/test_comparison.py` — 8 new tests
- `tests/unit/statistics/test_statistics.py` — 31 new tests

### Documentation (2 files modified)
- `reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md` — updated coverage matrix
- `reports/PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md` — this file

---

## 6. Protocol Coverage Delta

| Category | Before | After |
|----------|--------|-------|
| Implemented & validated | 9 | 14 |
| Partial | 3 | 1 |
| Missing | 7 | 3 |
| **Total requirements** | **19** | **19** |

Remaining gaps:
1. **McNemar's test** (H3) — requires architecture-level detection metric
2. **Architecture validation metrics** (H3, AC-09) — no architecture metric in evaluation
3. **Blast-radius interaction test** (H5, AC-10) — requires interaction term in mixed-effects model
