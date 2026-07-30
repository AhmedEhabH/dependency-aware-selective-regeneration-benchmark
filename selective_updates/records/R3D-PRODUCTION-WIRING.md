# R3D Production Wiring — Root Correction

**ID:** R3D-ROOT-CORRECTION
**Date:** 2026-07-30
**Status:** ROOT CORRECTED — INDEPENDENT AUDIT REQUIRED
**Branch:** experiment/three-arm-smoke-v2
**Code commit:** 9e28790

---

## Requirement

Correct seven root-level R3D contract defects identified by independent GPT-5.6 Thinking audit of checkpoint `e8d5eb4`. Complete RF-2 orchestration deduplication in the same pass. Do not start R4 or later work.

## Defects Fixed

1. **validation_command in pre-flight** — public `pre_flight_check` compared `validation_command` against hardcoded string; all callers failed closed. Moved to `_validate_scientific_configuration`, removed duplicate late checks.
2. **repair eligibility** — `functional_validation_passed` gate blocked evaluator and generation_guard repair. Removed; all three repairable stages (migration, evaluator, generation_guard) trigger repair.
3. **second bounded generation** — blocked by defect #2. Enabled by repair eligibility fix.
4. **transcript preservation** — Agent tool transcript dropped from RunRecord. Added `selection_tool_transcript` to both success/failure return paths + reporting serializer.
5. **repair duration** — `val_dur` used `functional_validation_duration_seconds` (small). Changed to `total_validation_full_sequence_duration_seconds` (migration + baseline + evaluator sum).
6. **executor feedback** — `revise_plan` received no failure context when executor failed. Added `last_feedback_channels` with sci_failure/executor error text.
7. **nominal R3D tests** — 0% public-path coverage. Complete replacement with 54 public-path tests.

## RF-2 (Orchestration Deduplication)

- Removed pre-flight `validation_command` check from `seven_arm_benchmark.py`
- Removed duplicate late checks from `_run_regeneration_flow` and `_run_iterative_flow`
- Single enforcement point: `_validate_scientific_configuration` in runner.py

## Files Changed

| File | Change | Lines |
|------|--------|-------|
| `src/benchmark/execution/runner.py` | 6 root fixes + RF-2 dedup | +72/-46 |
| `seven_arm_benchmark.py` | Pre-flight removal | +0/-7 |
| `src/benchmark/statistics/reporting.py` | selection_tool transcript serializer | +7/-1 |
| `tests/unit/execution/test_r3d_wiring.py` | 54 public-path tests (new) | +998/-0 |
| `tests/integration/test_su0010a_regeneration.py` | Bounded repair assertion | +34/-0 |

## Validation Gates

| Gate | Result |
|------|--------|
| pytest R3D focused (test_r3d_wiring.py) | 54 passed, 0 failed |
| pytest focused unit + contract | 163 passed, 0 failed |
| pytest focused integration | 122 passed, 0 failed |
| pytest full suite | 1478 passed, 32 skipped, 0 failed |
| ruff (changed files) | 0 errors |
| mypy --strict (changed production) | 0 errors |
| compileall (changed files) | All OK |
| git diff --check | No whitespace errors |

## Debt Closed

- TD-R3D-001 through TD-R3D-007
- TD-PROCESS-004, TD-PROCESS-005

## Next

Independent GPT-5.6 Thinking audit required. After acceptance: unblock R4, R5, R6, Kaggle, Pilot, merge, stable tag.
