# R7C Real-Run Root Closure + Exact Root Correction — Latest Phase Report

## Executive decision

The R7C real-run root closure (`fix/kaggle-smoke-v2-real-run-root`,
`7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift
attempt `exp-20260801-123125` exposed. The prior R7C report incorrectly called
a **1,451-test subset the full suite**; the true first full suite was **23
failed / 1,759 passed / 32 skipped**, root cause = blanket `baseline_validation
=> infrastructure_nonrepairable` in `src/benchmark/execution/runner.py`. The
independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD
`6d6aa36`, pushed via bundle fast-forward) makes the exact 23 former failures
pass and corrects DRF import mapping, exact version verification, fail-fast
preflight, driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime
contract, and stale source identity. Current full gate (Windows / Python
3.11.5) = **1,790 passed / 32 skipped / 0 failed**; mypy strict 0; compileall
clean; builder rerun clean; identity test passes (`SOURCE_COMMIT=ffa179a`,
`DEPLOYED_BUILD_ID=ffa179a`). Valid real Qwen remains **0/9**; Kaggle remains
**blocked** pending the independent full-gate audit. No tag, merge, or
force-push has been performed.

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
Branch             = fix/kaggle-smoke-v2-real-run-root (from the post-R6 runtime-blockers tail)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime fix        = de3163f  fix(kaggle): close real Smoke runtime blockers
Deployment pin     = fb60972  chore(deploy): pin corrected Scientific Smoke V2 bundle
R7A hardened source = d50e89e  fix(hf): make recovery sync state remotely truthful
R7A hardened bundle = 4c73db6  chore(deploy): pin hardened Scientific Smoke V2 rerun bundle
R7B runtime commit = bff0a82  fix(kaggle): make Qwen Smoke observable and executable
R7B bundle pin     = 17207bf  chore(deploy): pin final observable Smoke V2 bundle
R7C runtime commit = 7a80e53  fix(kaggle): close environment memory and prompt contracts
R7C bundle pin     = f01b8f0  chore(deploy): pin preflighted int8 Smoke V2 bundle
R7C previous HEAD  = a4e9186  (published but broken)
R7C correction     = ffa179a  fix(kaggle): correct repair and preflight contracts
R7C correction pin = 6d6aa36  chore(deploy): pin corrected R7C preflight bundle (HEAD)
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted; not scientific evidence)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md
```

## The failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-123125  failed at runtime root (FP16 OOM; deps drifted from lock)
```

The first two attempts failed at the first arm/scenario triplet during
workspace **isolation** before any LLM call; the later attempt reached the
model (81 calls, 47,694 tokens) but every record failed selection/validation;
the root-closure attempt failed before any model call at runtime root. None of
these outputs are scientific evidence. They remain visible on the results
dataset and must not be deleted.

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
Focused regression gates                                      all passed
  r4-metric-contract + su0010a + su0011                       119 passed
  preflight 13; runner 41; cli 72; builder 11                 passed
  scientific-smoke-v2 production path 41; bundle preflight 24 passed
Full suite (final gate)                                       prior "1,451" was a SUBSET;
                                                              true first full suite 23 failed /
                                                              1,759 passed / 32 skipped;
                                                              after correction 1,790 passed /
                                                              32 skipped / 0 failed
Ruff                                                          0 new except ARG004 (identity-locked;
                                                             inherent to reviewed commit)
Mypy strict                                                   0 issues
```

## Bundle inventory

```text
code = 90 files; data = 56 files; notebooks = 1; total = 147 files / 894,993 bytes
Builder = scripts/build_upload_bundle.py only; builder rerun no content diff
```

## Exact gates

```text
git diff --check    clean
Ruff                0 new versus a4e9186 except ARG004 (identity-locked; inherent to reviewed commit)
Mypy strict         0 issues
compileall          clean
full suite (final)  1,790 passed / 32 skipped / 0 failed
identity test       test_notebook_source_commit_matches_deployed_runtime_tree passes
                    (SOURCE_COMMIT=ffa179a, DEPLOYED_BUILD_ID=ffa179a)
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed
R7B Smoke Finish = complete (bff0a82 + 17207bf)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36, HEAD 6d6aa36)
Full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite
                  23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent full-gate audit of the corrected R7C branch → update the Kaggle
code dataset + notebook → one real cell (require 1/9 succeeded) → remaining
eight real Qwen Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Independent full-gate audit of the corrected R7C branch (HEAD `6d6aa36`).**
Do not relaunch Kaggle, tag, merge, or force-push before that audit passes.

R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED
