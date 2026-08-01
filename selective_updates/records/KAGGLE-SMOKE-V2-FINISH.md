# KAGGLE-SMOKE-V2-FINISH — Observable and Executable Qwen Smoke Completion (R7B)

**Change ID:** KAGGLE-SMOKE-V2-FINISH
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-finish` (from post-R6 `fix/kaggle-smoke-v2-runtime-blockers` tail)
**Directive:** `..\R7B_SMOKE_FINISH_PACKAGE\07_R7B_RESUME_TO_COMPLETION_DIRECTIVE.md`
**Status:** IMPLEMENTATION COMPLETE — INDEPENDENT AUDIT REQUIRED

## Truth

```text
latest real attempt    = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files
scientific evidence    = NONE (not scientific evidence)
R7B implementation     = complete, pending independent audit
valid real Qwen        = 0/9
Kaggle rerun           = BLOCKED until the independent audit passes
```

## What R7B closed

The post-R6 real Kaggle attempts (`exp-20260801-024041`,
`exp-20260801-024624`) failed before any model call, and a subsequent real
attempt reached 81 model calls / 47,694 tokens but produced **0 succeeded**
records (0/9) with **0 regenerated files**. R7B makes the Qwen Smoke run
**observable and executable** on Kaggle so the next real run produces
actionable diagnostics instead of a silent 0/9:

1. **Strict output normalization** (`src/benchmark/llm/output_normalization.py`):
   single-fenced JSON object extraction with regex fallback when `ast.parse`
   fails; empty/partial responses fail closed. Fixes 0% normalization coverage.
2. **Kaggle Qwen backend hardening** (`kaggle_qwen_backend.py`): Qwen
   chat-template token counting, deterministic single-`json.loads` parsing,
   `inference_mode()` + best-effort CUDA cache cleanup after every generation
   (success, OOM, and other-exception paths), one shared backend instance per
   process (single model initialization).
3. **Progress + cross-session ETA** (`seven_arm_benchmark.py`):
   `_render_progress_line` streamed per run; `_estimate_run_eta` from the
   persisted run ledger; `RUN`/`STAGE`/`REGEN`/`HF` structured log events.
4. **Deterministic dashboard** (`checkpoint/reports.py`:
   `write_dashboard_artifacts`): `dashboard_summary.json`,
   `run_matrix.csv`, `strategy_summary.csv`, `failure_summary.csv` under
   `OUTPUT_DIR/dashboard`, and HF recovery allowlist entries
   (`checkpoint/hf_sync.py`) so the dashboard survives HF sync.
5. **Notebook rewrite** (`notebooks/seven_arm_benchmark.ipynb`): live
   subprocess streaming (`_run_benchmark_live`), evidence loading
   (`_load_smoke_evidence`), dashboard display (`_display_smoke_dashboard`),
   actionable failure error (`_raise_actionable_smoke_error` +
   `ScientificSmokeExecutionError`), continuous-cell precondition
   (`_validate_continuous_precondition`), `kaggle_console.log` persistence,
   and the smoke-only cap `max_completion_tokens_per_call: 1024`
   (`configs/smoke.yaml`).

## Commits

```text
A = bff0a82  fix(kaggle): make Qwen Smoke observable and executable
             (runtime/config + directly related tests; 16 files, +1483/−46)
B = 17207bf  chore(deploy): pin final observable Smoke V2 bundle
             (notebook pinned to bff0a82, bundle rebuilt, test_cli notebook
             assertions; 14 files, +2199/−685)
```

Both pushed to `origin/fix/kaggle-smoke-v2-finish`; local/remote equality
verified after each push.

## Gates

```text
Focused set (directive §7)            all passed
  unit llm/regeneration/config/hf_sync/su0008/cli        passed
  integration production-path + su0010a                  100 passed
  cli + builder + bundle preflight                       91 passed
Full suite (final gate, §10)          1,735 passed / 32 skipped / 0 failed
Ruff                                  baseline 91 = current 91 (0 new vs b6a2031)
Mypy --strict src/benchmark           0 issues
Compileall                            clean
Builder rerun                         no diff (deterministic)
git diff --check                      clean
git status --short                    clean
Manifest audit (worktree/index/HEAD)  code 0 / data 0 / notebook 0 mismatches
```

## Notebook proof (helpers)

```text
_run_benchmark_live              Popen streaming, stderr→stdout, kaggle_console.log
_load_smoke_evidence             checkpoint/progress/failure/remote_sync/run_records/dashboard
_display_smoke_dashboard         KPI + per-run + 3x3 matrix + failure causes + charts
_raise_actionable_smoke_error    diagnosis block + ScientificSmokeExecutionError
_validate_continuous_precondition 1 succeeded / 0 failed / 8 pending + model_calls>0
                                  + migration/baseline/evaluator passed + recovery_uploaded
                                  + source/build identity match
```

## Next action

Independent audit of the R7B Smoke Finish. Kaggle rerun remains blocked until
that audit passes. No tag, no merge, no force-push, no Kaggle relaunch.

R7B_SMOKE_FINISH_AUDIT_REQUIRED
