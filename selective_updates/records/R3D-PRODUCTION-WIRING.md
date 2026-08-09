# R3D Production Wiring — Root Correction

**ID:** R3D-ROOT-CORRECTION
**Date:** 2026-07-31
**Status:** FINAL FREEZE CANDIDATE — INDEPENDENT AUDIT REQUIRED
**Branch:** experiment/three-arm-smoke-v2
**Code commit:** 9e28790 (root correction), 11f88f5 (final evidence closure)
**Closure spec:** docs/R3D_FINAL_EVIDENCE_AND_REPORT_CLOSURE.md
**Report:** reports/latest_phase_report.md

---

## Requirement

Correct seven root-level R3D contract defects identified by independent GPT-5.6 Thinking audit of checkpoint `e8d5eb4`. Complete RF-2 orchestration deduplication in the same pass. Close final evidence gaps: evaluator stderr omitted from Agent/repair feedback, nominal test replacement, truthful report. Do not start R4 or later work.

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

## Final Evidence Closure (commit 11f88f5)

### Defect closed
- **Evaluator stderr omitted from Agent/repair feedback** — `_scientific_feedback_channels()` now constructs stderr from `evaluator.stderr`, `evaluator.error`, and `checks`; bounded at 1000 chars; no evaluator source, Ground Truth, or hidden descriptions.

### Test replacement
- 5 nominal R3D tests replaced with 7 public-path tests covering: entry config, monolithic migration repair, selective evaluator repair, agent evaluator revision + transcript, feedback channel content, duration aggregation, record round-trip.

### Report
- `reports/latest_phase_report.md` replaced with truthful 2269-word Git-derived report (no manually curated file lists; all scopes match `git diff --name-status`).

## Validation Gates (final closure — 11f88f5)

| Gate | Result |
|------|--------|
| pytest R3D focused (test_r3d_wiring.py) | 54 passed, 0 failed (7 public-path, 18 private-helper, 7 persistence, 1 reporting) |
| pytest focused unit + contract | 177 passed, 0 failed |
| pytest focused integration | 86 passed, 0 failed |
| pytest full suite | 1478 passed, 32 skipped, 0 failed |
| ruff (changed files) | 0 errors |
| mypy --strict (changed production) | 0 errors |
| compileall (changed files) | All OK |
| git diff --check | No whitespace errors |

## Debt Closed

- TD-R3D-001 through TD-R3D-007 (root correction)
- TD-R3D-008 — evaluator stderr omitted from Agent/repair feedback
- TD-R3D-009 — public-path regression tests incomplete
- TD-PROCESS-004, TD-PROCESS-005 (root correction)
- TD-PROCESS-006 — R3D report contained inaccurate evidence
- TD-PROCESS-007 — visible OpenCode response omitted required report

## Next

Independent GPT-5.6 Thinking audit required. After acceptance: freeze R3D → begin R4 (truthful metrics) → R5 (nine local records) → RF-4 cleanup → R6 (bundle and push) → nine real Qwen Kaggle runs → independent audit → v2.0.0-scientific-smoke tag → Pilot.
