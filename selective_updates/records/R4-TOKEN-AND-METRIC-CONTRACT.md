# R4 Token and Metric Contract — Single-Pass Completion

**ID:** R4-TOKEN-AND-METRIC-CONTRACT
**Date:** 2026-07-31
**Status:** IMPLEMENTED — INDEPENDENT AUDIT REQUIRED (not accepted, not frozen)
**Branch:** experiment/three-arm-smoke-v2
**Starting HEAD:** b8724cc
**Code commit:** e87d4ad — `fix(metrics): separate per-call limits and workflow totals`
**Docs commit:** `docs(state): record R4 completion pending audit`
**Closure specs:** docs/R4_PRECOMMIT_ROOT_AUDIT_AND_SINGLE_PASS_COMPLETION.md, docs/phase_specs/R4_FINAL_PRECOMMIT_CLOSURE.md, docs/phase_specs/R4_SINGLE_PASS_SPEC.md
**Report:** reports/latest_phase_report.md (2299 words)

---

## Audit Correction (2026-07-31)

The R4 evidence was re-audited at starting HEAD `ccdb49c` on branch `experiment/three-arm-smoke-v2` (working tree clean, `core.autocrlf=true`). Two defects were found and corrected:

### Defect A — exact workflow-budget exhaustion reopened an exhausted budget as unlimited

- **Root cause:** `0` was overloaded as both "no total workflow limit" and "configured limit exhausted". When the workflow budget was consumed exactly, the runtime remaining value hit `0`, and `resolve_completion_allowance` returned the full per-call allowance for `0`, reopening the exhausted budget as unlimited.
- **Fix:** internal representation is now `None` = unlimited runtime allowance, `0` = exhausted configured allowance, positive integer = remaining configured allowance (public config meaning of zero as unlimited preserved).
  - `budgets.py`: new `runtime_remaining_total_tokens` property returning `None` when `has_total_token_limit` is False, `max(0, _max_tokens - _state.total_tokens)` otherwise; `resolve_completion_allowance` takes `remaining_total_workflow_tokens: int | None` and returns the per-call limit for `None`, `0` for exhausted `0`, and `max(0, min(per_call, remaining - prompt))` for positive.
  - `regeneration.py`: `SharedRegenerationExecutor.execute` parameter default changed to `None`; accounting guarded by `has_limit`.
  - `iterative_agent.py`: `analyze_impact`/`revise_plan` parameter defaults changed to `None`; accounting guarded by `has_limit`.
  - `runner.py`: all five call sites pass `self._budget.runtime_remaining_total_tokens`.
- **Regression tests:** 5 groups in `tests/unit/execution/test_r4_token_and_metrics.py` (executor exact exhaustion, analyze-impact, revise-plan, unlimited-budget three-state distinction, resolver three-state) plus integration-level production-path tests in `tests/integration/test_r4_metric_contract.py`.

### Defect B — evaluator integrity was platform-dependent

- **Root cause:** committed `.sha256` fingerprints and evaluator `.py` blobs are canonical LF, but on Windows `git restore` produced CRLF working-tree bytes, so raw SHA-256 of the working tree mismatched the committed values.
- **Fix:** `.gitattributes` now pins `tests/evaluator_assets/todo_smoke_*_checks.py` to `text eol=lf`; the three working-tree files were rewritten to canonical LF without character changes.
- **Proven:** worktree SHA-256 matches committed `.sha256` for all three files (`eeb95c87…`, `74b6b141…`, `c0cd3891…`); index/worktree blobs byte-identical (`git hash-object` SAME, empty staged diff); zero CR bytes.

## Requirement

Complete R4 (token limits and truthful workflow metrics) end-to-end in one bounded pass: production corrections, real executor/Agent/boundary test rewrites, four direct verification scripts, RF-3 review, gates 9.1–9.6, code commit, detailed report, documentation commit. Do not start R5. Do not touch R5/R6/Kaggle, README, tags, evaluator assets, or hashes.

## Root Defects Fixed

1. **D1 — per-call and aggregate limits conflated** — `budgets.resolve_completion_allowance` is the single resolver (budgets.py:145-172).
2. **D2 — frozen conflict rule not enforced at construction** — `PipelineConfig`, `RunnerConfig`, `ExecutionConfig` each enforce: both zero → unlimited; one positive → it; both positive equal → it; both positive different → constructor-time ValueError.
3. **D3 — legacy aggregate fields misleading** — `total_workflow_*` now equals the exact stage sum.
4. **D4 — repair counted as initial regeneration** — `is_repair = iteration > 0` (runner.py:1348-1349).
5. **D5 — Agent budget ambiguous** — `analyze_impact`/`revise_plan` take explicit `max_completion_tokens_per_call` + `remaining_total_workflow_tokens`; `MAX_AGENT_CALLS = 8`.
6. **D6 — scientific durations not cumulative** — `_WorkflowMetricAccumulator.add_scientific` sums migration/baseline/evaluator across attempts.
7. **D7 — TokenUsage identity** — integer/bool/non-negative validation.
8. **D8 — resolved total not forwarded** — `model_metadata` shows the Runner-used value (2048/9000 in Script D at every boundary).
9. **D9 — persistence/reporting incomplete** — R4 fields forwarded through `_to_run_record_data`, `RunRecordStore` JSONL, `NotebookExporter._serialize_record`.
10. **D10 — nominal tests** — replaced with executable production-path tests; zero `assert True`.

## Test Files

- `tests/unit/execution/test_r4_token_and_metrics.py` — 66 tests (executor + Agent + accumulator + validation).
- `tests/integration/test_r4_metric_contract.py` — 31 tests (CLI/config identity, sentinel boundary trace, duration sums, agent metric separation).

## Direct Script Results (§7 acceptance)

```
A: limits [4096,4096,4096]  calls 3  success  usage 24  files 3
B: limits [20,2]  calls 2  failed closed  usage 36  third file unchanged
C1: zero backend calls
C2: exactly 8 backend calls, bounded failure
D: 2048/9000 at PipelineConfig, record_dict, RunRecordData.model_metadata, JSONL reload, report
```

## Validation Gates

| Gate | Result |
|------|--------|
| 9.1 R4 unit | 66 passed, 0 failed, 0 skipped |
| 9.2 R4 integration | 31 passed, 0 failed, 0 skipped |
| 9.3 R3D-adjacent regression | 177 passed, 0 failed |
| 9.4 evaluator integrity | 50 passed, 1 skipped (pre-existing), 0 failed |
| 9.5 full suite | 1576 passed, 32 skipped, 0 failed |
| 9.6 ruff (21 authorized files) | 0 new errors (8 pre-existing tracked + pre-existing E501/B008 in new R4 test files) |
| 9.6 mypy --strict (14 production) | 0 new errors (10 pre-existing in seven_arm_benchmark.py, verified vs HEAD worktree) |
| 9.6 compileall | exit 0 |
| 9.6 git diff --check | exit 0 |

## Debt Closed

- All R4 TD-0 and TD-1 (D1–D10). `remaining R4 TD-0 = 0`, `remaining R4 TD-1 = 0`.
- One new ARG001 (unused `max_attempts`) was introduced and immediately fixed by forwarding `max_attempts` into `model_metadata`.

## Next

Independent audit required. On acceptance: freeze R4 → R5 (nine local records) → RF-4 cleanup and rerun → R6 (bundle and push) → nine real Qwen Kaggle runs → independent results audit → v2.0.0-scientific-smoke tag → Pilot. R5 is unauthorized until the audit.
