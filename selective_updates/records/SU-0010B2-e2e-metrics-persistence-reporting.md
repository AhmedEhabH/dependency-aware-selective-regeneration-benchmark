# SU-0010B2 — End-to-End Metrics Persistence and Reporting

**Change ID:** SU-0010B2
**Title:** End-to-End Metrics Persistence and Reporting
**Date:** 2026-07-26
**Requirement or defect:** SU-0010A added end-to-end workflow metrics to `RunRecord`, but the serialization layer (`RunRecordData`), checkpoint/load/resume path, and reporting layer (per-run, aggregate, cross-session) did not preserve or report these metrics. The new fields (selection_*, regeneration_*, functional_validation_*, total_workflow_*, artifact counts) were lost at the serialization boundary.

## Current persistence path

1. `RunRecord` (models.py) → `_run_single_scenario_strategy` (seven_arm_benchmark.py) converts to dict → `RunRecordData(**dict)` constructed in main loop → `RunRecordStore.append()` writes JSONL
2. `RunRecordData` is loaded via `RunRecordData(**data)` in `persistence.py:173`
3. `reports.py` functions (`_build_results_agg_from_records`, `_build_per_strategy_detail_rows`, `_compute_token_totals`) read `RunRecordData` and export reporting artifacts
4. `reporting.py` `NotebookExporter._serialize_record` serializes `RunRecord` for notebook export

## Gaps found

| Layer | Gap |
|-------|-----|
| `persistence.py:RunRecordData` | Missing all end-to-end fields (selection_*, regeneration_*, functional_validation_*, total_workflow_*, artifact counts) |
| `reports.py:_build_results_agg_from_records` | Only serialized legacy fields (token_usage, duration_seconds, model_calls); no end-to-end metrics |
| `reports.py:_build_per_strategy_detail_rows` | Same gap |
| `reports.py:_compute_token_totals` | Only computed legacy token totals; no workflow totals |
| `reports.py:rebuild_experiment_reports` | No `workflow_totals` in audit; no per-strategy aggregate metrics |
| `reporting.py:_serialize_record` | Only serialized legacy fields |
| `seven_arm_benchmark.py` dict conversion | Does not extract new fields from `RunRecord` (forbidden file — remains as known gap) |

## Production Files Changed

| File | Modification |
|------|-------------|
| `src/benchmark/checkpoint/persistence.py` | Added 19 end-to-end fields to `RunRecordData` with backward-compatible defaults |
| `src/benchmark/checkpoint/reports.py` | Updated `_build_results_agg_from_records` to include all new fields; updated `_build_per_strategy_detail_rows` to include new fields; added `_compute_workflow_totals` with `effective_workflow_tokens` compatibility metric; added `_is_end_to_end_record` detection rule; added per-strategy aggregate metrics (validation tri-state, workflow sums/means); added `workflow_totals` to audit report |
| `src/benchmark/statistics/reporting.py` | Updated `_serialize_record` to include all 19 new fields |

## Test Files Modified

| File | Modification |
|------|-------------|
| `tests/unit/test_checkpoint.py` | Added `TestEndToEndMetricsRoundTrip` (12 tests): round-trip, validation tri-state (None/True/False), numeric types, historical compatibility, checkpoint/resume context, idempotent append, conflicting append |
| `tests/unit/statistics/test_reporting.py` | Added `test_serialize_record_with_end_to_end_metrics` and `test_serialize_record_with_functional_validation_none` |
| `tests/unit/test_su0008_cross_session_reporting.py` | Added `TestB2EndToEndMetricsCrossSession` (12 tests): full round-trip, e2e success report, validation failure, empty scope, validation missing (None excluded from denom), historical record, failed run metrics preserved, checkpoint round-trip, mixed-type aggregate, zero-run no division by zero, benchmark summary aggregate |

## Fields Proven by Round-Trip

All 19 end-to-end fields verified:
- selection_prompt_tokens, selection_completion_tokens, selection_total_tokens, selection_model_calls, selection_duration_seconds
- regeneration_prompt_tokens, regeneration_completion_tokens, regeneration_total_tokens, regeneration_model_calls, regeneration_duration_seconds
- functional_validation_duration_seconds, functional_validation_passed
- total_workflow_tokens, total_workflow_model_calls, total_workflow_duration_seconds
- selected_artifact_count, regenerated_artifact_count, preserved_artifact_count, unresolved_human_review_count

## Historical Compatibility Behavior

Records without new fields load with defaults (0 for int/float fields, None for functional_validation_passed). No checkpoint version bump required.

## Reporting Compatibility Rule

End-to-end record detection uses `_is_end_to_end_record()`: returns True if any evidence field is non-default (functional_validation_passed is not None, or any metric > 0). Correctly identifies empty-scope e2e runs (zero artifact counts, validation passed, total_workflow_tokens=0).

## Validation Tri-State Aggregation

- `True` → executed and passed (counted in denominator)
- `False` → executed and failed (counted in denominator)
- `None` → not executed (excluded from denominator; pass_rate is None when no executed validations)

## Effective Workflow Tokens Rule

- End-to-end record → `total_workflow_tokens`
- Historical impact-only record → `token_usage.total`
- Named `effective_workflow_tokens` in workflow_totals

## Targeted Test Results

| File | Collected | Passed | Failed | Skipped |
|------|-----------|--------|--------|---------|
| `tests/unit/test_checkpoint.py` | 42 | 42 | 0 | 0 |
| `tests/unit/statistics/test_reporting.py` | 17 | 17 | 0 | 0 |
| `tests/unit/test_su0008_cross_session_reporting.py` | 36 | 36 | 0 | 0 |

## Full Suite Results

```
collected: 902
passed:    897
failed:    0
skipped:   5
```

## Ruff

`ruff check` on changed files: 4 pre-existing errors (ARG001 + 3 E501). Zero new errors introduced.

## Mypy

`mypy --strict` on changed files: zero errors.

## pip-check

Pre-existing environment issues only (conda environment). No new dependency issues.

## Bundle

Code bundle: 75 files, 397,217 bytes — build and verified.

## Code/Data/Notebook Status

- Code Dataset: `kaggle_upload/code/` regenerated — updated for deployment
- Data Dataset: `kaggle_upload/data/` not modified
- Notebook: `kaggle_upload/notebooks/` not modified

## Entry-Point Correction (SU-0010B2 follow-up)

The benchmark entry-point conversion gap was closed in a focused correction:

| Item | Value |
|------|-------|
| Original reporting implementation commit | `4a4da45` |
| Entry-point correction commit | `e964c82` |
| Final branch HEAD | `e964c82` |
| Production file modified | `seven_arm_benchmark.py` + derivative |
| Test file modified | `tests/unit/test_cli.py` |
| Helper added | `_to_run_record_data()` — converts record_dict + metadata → RunRecordData with all 19 end-to-end fields |

The `_to_run_record_data` helper extracts every scoped metric from `record_dict` using backward-compatible defaults (integers → 0, durations → 0.0, functional_validation_passed → None). The `_run_single_scenario_strategy` function now forwards all 19 end-to-end fields from `RunRecord` into the intermediate dict. The inline `RunRecordData` construction in `main()` was replaced with a call to `_to_run_record_data`.

No coercion: None stays None, False stays False, booleans are not cast to integers, durations are not cast to strings. Selection tokens are not added to total workflow tokens. `token_usage` is not modified. No metric is double-counted.

### Targeted Test Results (with entry-point conversion tests)

| File | Collected | Passed | Failed | Skipped |
|------|-----------|--------|--------|---------|
| `tests/unit/test_cli.py` | 25 | 25 | 0 | 0 |
| `tests/unit/test_checkpoint.py` | 42 | 42 | 0 | 0 |
| `tests/unit/statistics/test_reporting.py` | 17 | 17 | 0 | 0 |
| `tests/unit/test_su0008_cross_session_reporting.py` | 36 | 36 | 0 | 0 |

### Full Suite Results

```
collected: 910
passed:    905
failed:    0
skipped:   5
```

### Ruff

`ruff check` on changed files: 18 pre-existing errors. Zero new errors introduced.

### Mypy

`mypy --strict` on changed files: 7 pre-existing errors. Zero new errors introduced.

### Bundle

Code bundle: 75 files, 401,870 bytes — build and verified.

## Remaining Scientific Blockers (post-correction)

None. All SU-0010B2 gaps are resolved.
