# SU-0010B3 — Functional Validation and Bounded Repair

**Change ID:** SU-0010B3
**Title:** Functional Validation and Bounded Repair
**Date:** 2026-07-26
**Requirement:** SU-0010B3 — connect bounded repair to the regeneration path using the smallest production change.

## Previous behavior

Regeneration flow performed: selection → regeneration → functional validation → final success/failure.
A failed functional validation ended the run immediately. `max_attempts` had no effect on regeneration runs.

## New bounded-repair flow

selection → initial regeneration → validation → bounded repair attempt when validation fails → revalidation → final classified RunRecord

### Repair trigger

Repair occurs only when:
- regeneration completed;
- functional validation executed;
- functional validation failed (`functional_validation_passed=False`);
- remaining budget permits another attempt;
- no infrastructure, harness_defect, or timeout failures present.

Non-repairable failures (missing validation command, isolation failure, protocol violation, unsupported strategy, infrastructure failure) do not enter repair.

### Maximum-attempt interpretation

`max_attempts` = total generation attempts, including the initial attempt.

- `max_attempts=1` → initial attempt only, zero repair attempts
- `max_attempts=2` → initial attempt, at most one repair attempt
- `max_attempts=3` → initial attempt, at most two repair attempts

### Workspace semantics

Each repair attempt starts from the current failed mutable workspace and receives the previous validation failure output as repair context. Source repository and staged active snapshot remain unchanged.

### Repair context

Each repair prompt receives:
- failed validation exit code;
- failed validation stdout (up to 1000 chars);
- failed validation stderr (up to 1000 chars).

No Ground Truth content is included in repair context.

### Validation after repair

Every repair attempt is followed by the same functional validation command. Success requires `functional_validation_passed=True`.

### Failure classification

- Validation failed and budget remains → repairable attempt failure
- Validation failed and attempts exhausted → final failed RunRecord
- Timeout → timed_out or failed (per existing project semantics)
- Missing validation command → harness/configuration failure, no repair

### Metrics

Selection metrics are counted once. Regeneration tokens, model calls, and duration are summed across all generation attempts (initial + repair). Functional validation duration is summed across every validation execution. Total workflow metrics reflect the sum of all stages.

## Production files changed

| File | Modification |
|------|-------------|
| `src/benchmark/execution/runner.py` | Added `_is_repairable_failure`, `_run_regeneration_repair_flow`; modified `run()` to enter repair loop; added `_last_prediction` and `_last_val_result` for repair context; added try-except around `record_attempt()` for graceful timeout handling |
| `src/benchmark/execution/regeneration.py` | Added `REPAIR_CONTEXT_PROMPT_TEMPLATE`; added optional `repair_context` parameter to `execute()` and `_execute_async()`; appended repair context when provided |

## Test files changed

| File | Modification |
|------|-------------|
| `tests/integration/test_su0010a_regeneration.py` | Renamed `TestSingleAttempt` to `TestBoundedRepairAttempts`; updated tests to reflect bounded-repair behavior; added 9 new tests |

## Tests added

1. `test_validation_success_no_repair` — one generation, one validation, no repair
2. `test_validation_failure_triggers_repair` — 3 attempts (1 initial + 2 repair)
3. `test_generation_rejection_no_repair` — generation failures do not trigger repair
4. `test_max_attempts_bounds_repair` — correct call count with 2 artifacts × 3 attempts
5. `test_max_attempts_1_no_repair` — max_attempts=1 disables repair
6. `test_validation_failure_then_repair_success` — repair succeeds with content-checking validation
7. `test_non_repairable_missing_validation` — no repair when validation_command is absent
8. `test_repair_context_contains_validation_evidence` — repair prompt includes failure evidence, no Ground Truth
9. `test_selection_metrics_counted_once` — selection metrics not duplicated
10. `test_regeneration_and_validation_metrics_aggregated` — metrics summed across attempts
11. `test_token_budget_stops_repair` — token budget exhaustion stops repair
12. `test_timeout_stops_repair` — timeout stops repair

## Limitations

- Architecture validation is not implemented beyond the functional/regression validation command provided by the repository.
- Standalone architecture validation is not implemented unless an existing repository command provides it.

## Code/Data/Notebook status

- Code Dataset: regenerated (`kaggle_upload/code/`)
- Data Dataset: unchanged (not modified)
- Notebook: unchanged (not modified)

## Next step

- SU-0011 — iterative repository agent (authorization required)
- Scientific Smoke and Pilot remain unauthorized
