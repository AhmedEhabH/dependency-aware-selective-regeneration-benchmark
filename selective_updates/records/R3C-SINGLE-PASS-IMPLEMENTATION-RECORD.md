# R3C — Single-Pass Isolated Scenario Evaluator System (Corrected)

**Date:** 2026-07-29
**Status:** R3C CORRECTION SELF-GATES PASSED — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode
**Original implementation:** `0d168d0` (rejected by independent audit)
**Correction code:** `81429c1`

> **Correction note:** The original record (`0d168d0`) described an implementation that did not exist in the committed source (e.g., "validates config dict", "runs uv run -m pytest", "uses pytest JSON report", "maps to EvaluatorVerdict"). The committed production module actually copies one Python evaluator script, executes it via subprocess, and parses a three-key JSON object. This record is rewritten from the actual implementation.

---

## Implementation Summary

### Production code (`src/benchmark/execution/scenario_evaluator.py`)

Four-state evaluator architecture:

1. **Validation (`_ValidatedEvaluatorRequest`)** — Ensures evaluator asset paths are beneath `tests/evaluator_assets/`, workspace is outside project root, no symlinks in asset path, no evaluator assets in workspace. Uses `Path.relative_to` for containment.

2. **Trust (`_TrustedEvaluatorAsset`)** — Reads asset bytes and computes SHA-256 hash. Original file can change after trust without affecting copied bytes.

3. **Execution (`_EvaluatorCommandOutcome`)** — Copies trusted bytes to a temporary directory, runs the evaluator script as a subprocess with the workspace path as argument. Captures stdout/stderr/exit code.

4. **Payload parsing (`_ParsedEvaluatorPayload`)** — Parses the JSON object from stdout. Validates `{passed: bool, checks: list[str], error: str}`. Rejects unknown keys, empty checks, duplicates, and logical contradictions.

### Fixture workspace builder (`evaluator_fixture_workspaces.py`)

- Uses `run_post_generation_command` from R3B production code
- Three correct-source dicts with only the files changed by each scenario
- `_apply_single_replacement` derives 9 negative variants with exactly one mutation each
- 626 lines (reduced from 1778)

### Three evaluator assets — 29 semantic checks total

All use identical fail-closed JSON structure. Always print exactly one JSON object.

### Integration tests — 20 integration tests

- Correct variants assert exact check tuples
- Negative variants assert expected check name in error
- Baseline hash preservation, migration integrity, source isolation

### Unit tests — 57 tests (5 skipped)

- 28 input validation tests including 6 new symlink/workspace-leak tests
- 2 trusted asset tests
- 10 subprocess tests (command/env/cwd capture, 5 exception types, copy/trust)
- 12 payload parsing tests
- 7 truth-table rows calling public `run_scenario_evaluator`
- 7 isolation tests (temp directory, source isolation)

R3C_ACCEPTANCE_CORRECTION_AUDIT_REQUIRED