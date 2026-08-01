# Post-R6 R7A Pre-Rerun Runtime Hardening — Latest Phase Report

## Executive decision

Two real Kaggle Scientific Smoke V2 runs launched from the R6-published
deployment failed completely before any model call (`exp-20260801-024041`,
`exp-20260801-024624`; both 9 planned / 0 succeeded / 9 failed / 0 model calls;
first failure = workspace isolation). The real runtime blockers were closed
under the Kaggle Runtime Blockers Fix directive on branch
`fix/kaggle-smoke-v2-runtime-blockers`: runtime fix commit `de3163f`
(`fix(kaggle): close real Smoke runtime blockers`), deployment pin commit
`fb60972` (`chore(deploy): pin corrected Scientific Smoke V2 bundle`). The
independent runtime-fix audit
(`..\R7A_Pre_Rerun_Hardening_Package\01_R7_RUNTIME_FIX_INDEPENDENT_AUDIT.md`)
accepted the core fix and reproduced four bounded findings. The **R7A
pre-rerun hardening** closed all four: hardened runtime source commit `d50e89e`
(`fix(hf): make recovery sync state remotely truthful`) and hardened bundle pin
commit `4c73db6` (`chore(deploy): pin hardened Scientific Smoke V2 rerun
bundle`). Rebuilt only through `scripts/build_upload_bundle.py`. **An
independent re-audit of the R7A hardening is required before any Kaggle
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
Branch             = fix/kaggle-smoke-v2-runtime-blockers (from experiment/three-arm-smoke-v2 @ 9ff3c4e)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime fix        = de3163f  fix(kaggle): close real Smoke runtime blockers
Deployment pin     = fb60972  chore(deploy): pin corrected Scientific Smoke V2 bundle
Runtime source     = de3163f12d51c31d3f488897ed2047821da3b190
R7A hardened source = d50e89e  fix(hf): make recovery sync state remotely truthful
R7A hardened bundle = 4c73db6  chore(deploy): pin hardened Scientific Smoke V2 rerun bundle
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md
```

## The two failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
```

Both failed at the first arm/scenario triplet during workspace **isolation**
before any LLM call; no `qwen:` identity was ever produced; the framework
stopped after the first error instead of completing the matrix. These outputs
remain visible on the results dataset and must not be deleted.

## What the runtime fix changed

- **Shared-snapshot isolation root:** `make_isolation(..., snapshot_storage_root)`
  → `IsolationContext(snapshot_base=...)`, threaded through
  `_run_single_scenario_strategy` and both `main` call sites, so all arms under
  a session share `workspace/snapshots` of the same workspace tree.
- **Kaggle Qwen fail-closed `--model-path` validation + `qwen:` identity** so a
  missing/absent real model fails before any run and `dry-run:mock` identity can
  never leak into real sessions.
- **Session exit code:** `_decide_session_exit_code` returns non-zero when a
  created run ended failed (e.g., max-runs-terminated session whose last run
  failed now exits 1).
- **Batched truthful HF upload:** `_upload_batch_with_retry` /
  `CommitOperationAdd` / `create_commit`; all upload booleans checked so
  `remote_sync.json` truthfully reflects what was uploaded; allowlist includes
  `benchmark-results`.
- **`mark_completed(completed_with_failures=...)`** in `checkpoint.py`.
- **Notebook guardrails:** `discover_model()` fail-closed (config.json + >=1
  weight file required, KAGGLE_INPUT fallback), `_verify_scientific_run()` at
  the end of both run cells (status succeeded, total_workflow_model_calls > 0,
  model_identity starts `qwen:`, baseline/migration/evaluator passed,
  `remote_sync.json` last_sync in recovery/snapshot/final_uploaded),
  continuous-cell markdown blocks auto-run until guardrail passes,
  `Terminal: n/9` vocabulary, results repo =
  `NabilDo/selective-regeneration-experiment-results`.

## What the R7A hardening changed (four audit findings closed)

- **Remote recovery state is truthful (Finding A):** `upload_recovery()` writes
  `remote_sync.json` as `last_sync = recovery_uploaded` **before** `create_commit`
  and includes that exact file in the **same** recovery commit (one
  `create_commit`); on success local = committed; on failure local overwritten
  to `failed_local_safe` with the real remote path + error, failure record
  retained, `False` returned. Remote never holds `pending`.
- **Notebook status schema (Finding B):** `progress-cell` reads
  `last_sync`/`timestamp`/`remote_path`/`details` (obsolete
  `last_sync_time`/`experiments_synced`/`runs_uploaded` removed).
- **Version-compatible HF fixtures (Finding C):** `RepositoryNotFoundError`
  built with real `httpx.Request` + `httpx.Response(404, request=request)`;
  generic upload failure uses `RuntimeError`.
- **Documentation truth (Finding D):** current docs/reports use the actual final
  gate (full suite = 1,688 passed / 32 skipped / 0 failed).

## Fix evidence

```text
Shared-snapshot integration test (r5 shared root, all 3 child arms)     passed
Unit isolation TestMakeIsolationSharedSnapshot (7)                      passed
Unit CLI (test_cli.py, 58, incl. notebook sync display schema test)     passed
Unit HF sync (TestHfUploaderBatchedCommits + TestHfRecoveryStateTruth, 5
  new remote-state truth tests + 6 rewritten legacy tests)              passed
Kaggle bundle preflight (15; +TestKaggleBundleRuntimeGuardrails, 6)     passed
Full suite (final gate)                                                 1,688 passed / 32 skipped / 0 failed
```

## Bundle inventory

```text
code = 87 files; data = 56 files; notebooks = 1 (18,262 bytes); total = 144 files / 815,779 bytes
Builder = scripts/build_upload_bundle.py only; builder rerun leaves tree unchanged
```

## Exact gates

```text
git diff --check    clean
Ruff                0 new violations versus d9068fd (baseline 91, current 91)
Mypy strict         0 issues
py_compile          clean
preflight suite     15 passed
full suite (final)  1,688 passed / 32 skipped / 0 failed
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed, pending re-audit
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent re-audit of the R7A hardening → update the Kaggle code dataset +
notebook → one real cell (require 1/9 succeeded) → remaining eight real Qwen
Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Independent re-audit of the R7A pre-rerun hardening.** Do not relaunch Kaggle,
tag, merge, or force-push before that re-audit passes.

R7A_HARDENING_REAUDIT_REQUIRED
