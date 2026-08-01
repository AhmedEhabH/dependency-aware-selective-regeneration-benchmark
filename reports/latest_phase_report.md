# R7B Smoke Finish — Observable and Executable Qwen Smoke — Latest Phase Report

## Executive decision

Two real Kaggle Scientific Smoke V2 runs launched from the R6-published
deployment failed completely before any model call (`exp-20260801-024041`,
`exp-20260801-024624`; both 9 planned / 0 succeeded / 9 failed / 0 model calls;
first failure = workspace isolation). The real runtime blockers were closed
(runtime fix commit `de3163f`, deployment pin commit `fb60972`) and the R7A
pre-rerun hardening closed the four independently reproduced findings
(`d50e89e` + `4c73db6`). A subsequent real attempt reached **81 model calls /
47,694 tokens but produced 0 succeeded / 0 regenerated files (0/9)** — this is
**not scientific evidence**. The **R7B Smoke Finish** makes the Qwen Smoke run
**observable and executable** on branch `fix/kaggle-smoke-v2-finish`: runtime
commit `bff0a82` (`fix(kaggle): make Qwen Smoke observable and executable`)
and bundle pin `17207bf` (`chore(deploy): pin final observable Smoke V2
bundle`). Rebuilt only through `scripts/build_upload_bundle.py`. **An
independent audit of the R7B Smoke Finish is required before any Kaggle
relaunch.** No tag, merge, or force-push has been performed.

This report is the current, latest-first post-R6 report. The R6 acceptance,
freeze, and publication detail belongs to
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` and
`selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` and is
not repeated here.

## Models used

```text
Requested model:  DeepSeek V4 Flash Free through OpenCode Zen
Actual model:     opencode/deepseek-v4-flash-free
Mode:             Build
Provider:         OpenCode Zen
```

## Branch and commits

```text
Branch             = fix/kaggle-smoke-v2-finish (from the post-R6 runtime-blockers tail)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime fix        = de3163f  fix(kaggle): close real Smoke runtime blockers
Deployment pin     = fb60972  chore(deploy): pin corrected Scientific Smoke V2 bundle
R7A hardened source = d50e89e  fix(hf): make recovery sync state remotely truthful
R7A hardened bundle = 4c73db6  chore(deploy): pin hardened Scientific Smoke V2 rerun bundle
R7B runtime commit = bff0a82  fix(kaggle): make Qwen Smoke observable and executable
R7B bundle pin     = 17207bf  chore(deploy): pin final observable Smoke V2 bundle
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files (not scientific evidence)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-FINISH.md
```

## The failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
Latest real attempt  succeeded 0 / 9, 81 model calls, 47,694 tokens, 0 regenerated files
```

The first two attempts failed at the first arm/scenario triplet during
workspace **isolation** before any LLM call; the later attempt reached the
model (81 calls, 47,694 tokens) but every record failed selection/validation,
so no file was regenerated. None of these outputs are scientific evidence.
They remain visible on the results dataset and must not be deleted.

## What the R7B Smoke Finish changed

- **Strict output normalization** (`src/benchmark/llm/output_normalization.py`):
  single-fenced JSON object extraction with regex fallback when `ast.parse`
  fails; empty/partial responses fail closed (fixes 0% normalization coverage).
- **Kaggle Qwen backend** (`kaggle_qwen_backend.py`): Qwen chat-template token
  counting, deterministic single-`json.loads` parsing, `inference_mode()` +
  best-effort CUDA cache cleanup after every generation (success, OOM,
  other-exception), one shared backend instance per process (single model
  initialization).
- **Progress + cross-session ETA** (`seven_arm_benchmark.py`):
  `_render_progress_line` per run; `_estimate_run_eta` from the persisted
  ledger; `RUN`/`STAGE`/`REGEN`/`HF` structured log events.
- **Deterministic dashboard** (`checkpoint/reports.py`
  `write_dashboard_artifacts`): `dashboard_summary.json`, `run_matrix.csv`,
  `strategy_summary.csv`, `failure_summary.csv` under `OUTPUT_DIR/dashboard`,
  allowlisted for HF recovery (`checkpoint/hf_sync.py`).
- **Smoke-only cap** (`configs/smoke.yaml`): `max_completion_tokens_per_call: 1024`.
- **Notebook rewrite** (`notebooks/seven_arm_benchmark.ipynb`, pinned to
  `bff0a82`): `_run_benchmark_live` (Popen streaming, stderr→stdout,
  `kaggle_console.log`), `_load_smoke_evidence`, `_display_smoke_dashboard`,
  `_raise_actionable_smoke_error` + `ScientificSmokeExecutionError`,
  `_validate_continuous_precondition`, executable `max-runs 1` exec cell +
  guarded continuous cell.

## Fix evidence

```text
Focused set (directive §7)                                    all passed
  unit llm/regeneration/config/hf_sync/su0008/cli             passed
  integration production-path + su0010a                       100 passed
  cli + builder + bundle preflight                            91 passed
Full suite (final gate)                                       1,735 passed / 32 skipped / 0 failed
Ruff                                                          91 = 91 (0 new vs b6a2031)
Mypy strict                                                   0 issues
```

## Bundle inventory

```text
code = 88 files; data = 56 files; notebooks = 1 (31,023 bytes); total = 145 files / 858,225 bytes
Builder = scripts/build_upload_bundle.py only; builder rerun leaves tree unchanged
```

## Exact gates

```text
git diff --check    clean
Ruff                0 new versus b6a2031 (baseline 91, current 91)
Mypy strict         0 issues
compileall          clean
full suite (final)  1,735 passed / 32 skipped / 0 failed
manifest audit      code 0 / data 0 / notebook 0 mismatches (worktree/index/HEAD)
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed
R7B Smoke Finish = complete (bff0a82 + 17207bf) — observable Qwen Smoke, audit required
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent audit of the R7B Smoke Finish → update the Kaggle code dataset +
notebook → one real cell (require 1/9 succeeded) → remaining eight real Qwen
Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Independent audit of the R7B Smoke Finish.** Do not relaunch Kaggle, tag,
merge, or force-push before that audit passes.

R7B_SMOKE_FINISH_AUDIT_REQUIRED
