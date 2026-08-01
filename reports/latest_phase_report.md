# Post-R6 Kaggle Runtime Fix — Latest Phase Report

## Executive decision

Two real Kaggle Scientific Smoke V2 runs launched from the R6-published
deployment failed completely before any model call (`exp-20260801-024041`,
`exp-20260801-024624`; both 9 planned / 0 succeeded / 9 failed / 0 model calls;
first failure = workspace isolation). The real runtime blockers were closed
under the Kaggle Runtime Blockers Fix directive on branch
`fix/kaggle-smoke-v2-runtime-blockers`: runtime fix commit `de3163f`
(`fix(kaggle): close real Smoke runtime blockers`), deployment pin commit
`fb60972` (`chore(deploy): pin corrected Scientific Smoke V2 bundle`). The
corrected bundle is pinned to runtime source `de3163f12d51c31d3f488897ed2047821da3b190`
and rebuilt only through `scripts/build_upload_bundle.py`. **The fixes are
committed; an independent runtime-fix audit is required before any Kaggle
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
Deployed build id  = de3163f
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md
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

## Fix evidence

```text
Shared-snapshot integration test (r5 shared root, all 3 child arms)     passed
Unit isolation TestMakeIsolationSharedSnapshot (7)                      passed
Unit CLI (test_cli.py, 57, incl. notebook pin derived from canonical)   passed
Unit HF sync (TestHfUploaderBatchedCommits + 6 rewritten legacy tests)  passed
Kaggle bundle preflight (15; +TestKaggleBundleRuntimeGuardrails, 6)     passed
Combined unit + integration (isolation, cli, hf_sync, production path,
  real smoke, todo smoke evaluator)                                     254 passed / 2 skipped
Full suite (last full gate)                                             1,676 passed / 32 skipped / 0 failed
```

## Bundle inventory

```text
code = 87 files; data = 56 files; notebooks = 1 (18,137 bytes); total = 144 files / 815,004 bytes
Builder = scripts/build_upload_bundle.py only; preflight over rebuilt bundle = 15 passed
```

## Exact gates

```text
git diff --check    clean
Ruff                0 new violations (pre-existing baseline unchanged)
Mypy strict         base 5 pre-existing errors only (0 new)
py_compile          clean
preflight suite     15 passed
full suite (last)   1,676 passed / 32 skipped / 0 failed
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Runtime fixes  = committed (de3163f) and pinned (fb60972)
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent runtime-fix audit → relaunch nine real Qwen Scientific Smoke V2
records (3 scenarios × 3 arms × 1 repetition) with the corrected bundle.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Independent audit of the runtime fixes.** Do not relaunch Kaggle, tag, merge,
or force-push before that audit passes.

KAGGLE_RUNTIME_FIX_AUDIT_REQUIRED
