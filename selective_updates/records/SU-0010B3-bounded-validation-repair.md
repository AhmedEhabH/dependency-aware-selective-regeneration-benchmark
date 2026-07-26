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

## Correction — Merge-Blocking Gaps (commit on fix/su-0010b3-bounded-validation-repair)

Three merge-blocking correctness gaps were closed in a single correction commit:

### Gap 1 — Token budget not actually enforced

**Problem:** `self._budget.record_attempt()` was called with zero tokens for every attempt. The actual LLM token usage produced by `SharedRegenerationExecutor` was never recorded in `BudgetManager`, so `max_tokens` could not bound repair.

**Fix:** Added `BudgetManager.record_tokens(tokens: int)` method that validates `tokens >= 0`, increments `state.total_tokens`, updates the current attempt snapshot token count, and marks the budget exhausted when `total_tokens >= max_tokens`. `max_tokens=0` preserves unlimited behavior.

**Token flow after fix:** After every generation attempt, `self._budget.record_tokens(exec_result.total_tokens)` is called with actual token usage. The initial attempt may execute even if its resulting tokens exceed the configured budget (actual usage is known only afterward). Before starting a new repair attempt, `can_attempt` blocks if `state.exhausted` is set from cumulative token budget exhaustion.

### Gap 2 — Successful repair loses previous-attempt history

**Problem:** Repair-success `RunRecord` returned `status=succeeded` but omitted `all_failures`, dropping previous validation-attempt `FailureRecord`s.

**Fix:** Added `failures=tuple(all_failures)` to the repair-success `RunRecord` constructor. A first-attempt success still has no repair-failure history.

### Gap 3 — Timeout test does not exercise timeout between attempts

**Problem:** `test_timeout_stops_repair` expired the budget before the initial generation.

**Fix:** Replaced with a test using an injectable `BudgetManager` clock that advances past the timeout threshold during the first generation call, proving: (1) initial generation executes, (2) initial validation fails, (3) timeout becomes exhausted after that attempt, (4) no repair generation executes, (5) final record status is `failed`.

### Original bounded-repair commit

`ace6322`

### Correction commit

`0190a20`

### Semantics

- `max_tokens` is the maximum cumulative regeneration token budget across initial regeneration and every repair regeneration attempt
- `max_tokens=0` remains unlimited
- After every generation attempt, account for actual `exec_result.total_tokens` via `record_tokens()`
- Before starting a new repair attempt, stop if consumed regeneration tokens have reached or exceeded `max_tokens`
- No additional repair attempt is permitted after the cumulative token budget is exhausted
- Successful repair retains previous validation-failure history in `RunRecord.failures`
- First-attempt success has no repair-failure history
- Timeout after the initial attempt prevents repair (proven by injectable clock, not sleeps)
- Selection-token behavior remains unchanged

## Production files changed

| File | Modification |
|------|-------------|
| `src/benchmark/execution/budgets.py` | Added `record_tokens(tokens: int)` method for actual token accounting |
| `src/benchmark/execution/runner.py` | Added `self._budget.record_tokens(exec_result.total_tokens)` after each generation in `_run_regeneration_flow` and `_run_regeneration_repair_flow`; added `failures=tuple(all_failures)` to repair-success `RunRecord` |
| `src/benchmark/execution/regeneration.py` | Added `REPAIR_CONTEXT_PROMPT_TEMPLATE`; added optional `repair_context` parameter to `execute()` and `_execute_async()`; appended repair context when provided |

## Test files changed

| File | Modification |
|------|-------------|
| `tests/unit/execution/test_budgets.py` | Added 6 new tests for `record_tokens()`: accumulation, negative rejection, unlimited `max_tokens=0`, exhaustion, below-limit allowance |
| `tests/integration/test_su0010a_regeneration.py` | Renamed `TestSingleAttempt` to `TestBoundedRepairAttempts`; updated tests to reflect bounded-repair behavior; added 9 new tests; corrected `test_token_budget_stops_repair` and `test_timeout_stops_repair`; added `max_tokens` parameter to `_make_runner` |

## Tests added (correction)

1. `test_record_tokens_accumulates` — `record_tokens()` accumulates across attempts
2. `test_record_tokens_negative_raises` — negative token accounting rejected
3. `test_max_tokens_zero_unlimited` — `max_tokens=0` remains unlimited
4. `test_record_tokens_exhausts_budget` — token exhaustion sets `can_attempt=False`
5. `test_record_tokens_below_limit_still_allows` — below-limit tokens still allow attempts
6. `test_token_budget_stops_repair` (corrected) — initial generation tokens exhaust budget, prove call count
7. `test_token_budget_exhausted_after_initial_no_repair` — initial attempt token usage prevents repair
8. `test_token_budget_exhausted_after_one_repair` — token budget prevents second repair
9. `test_max_attempts_behavior_unchanged` — `max_attempts` still includes the initial attempt
10. `test_repair_success_preserves_failure_history` — successful repair retains validation-failure records
11. `test_first_attempt_success_no_repair_history` — first-attempt success has no repair-failure history
12. `test_timeout_stops_repair` (corrected) — timeout after initial attempt prevents repair, prove call count
13. `test_metrics_double_counted_not_duplicated` — every executed attempt counted exactly once

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
