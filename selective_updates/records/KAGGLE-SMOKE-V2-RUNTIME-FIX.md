# Kaggle Smoke V2 Runtime Fix — Two Failed Attempts and Correction

**Phase:** Post-R6 Kaggle runtime fix (dependency-aware selective regeneration benchmark)
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-runtime-blockers`
**Status:** **FIXES APPLIED AND COMMITTED — INDEPENDENT RUNTIME-FIX AUDIT REQUIRED**
**Starting HEAD:** `9ff3c4e` (docs(state): record R6 milestone branch publication)
**Runtime fix commit:** `de3163f` `fix(kaggle): close real Smoke runtime blockers`
**Deployment pin commit:** `fb60972` `chore(deploy): pin corrected Scientific Smoke V2 bundle`
**Directive:** `..\Kaggle_Runtime_Blockers_Fix_Package\02_OPENCODE_KAGGLE_RUNTIME_FIX_DIRECTIVE.md`
**Evidence audit:** `..\Kaggle_Runtime_Blockers_Fix_Package\01_KAGGLE_TWO_RUNS_INDEPENDENT_AUDIT.md`
---

## 1. The two real Kaggle attempts (must remain visible)

Two real Kaggle Scientific Smoke V2 runs were launched from the R6-published
deployment (`54a0462` bundle / `cb25e9f` runtime). Both failed completely
before any model call. The failed experiment output directories are preserved
on the results dataset `NabilDo/selective-regeneration-experiment-results` and
must NOT be deleted.

```text
Attempt 1  exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
Attempt 2  exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
```

Both runs reported the same root-cause sequence: the very first arm/scenario
triplet failed during workspace **isolation** before any LLM call, and the
framework stopped after the first error instead of completing the matrix.
No `qwen:` identity was produced (the Kaggle model was never discovered /
never invoked), so every record failed at stage isolation with zero tokens.

## 2. Authorized scope

The fix directive required closing the exact real runtime blockers with
truthful engineering evidence, keeping R6/R5/R4 history untouched, and
stopping for an independent audit before any further Kaggle launch.

| Fix | Scope | Status |
|---|---|---|
| Shared-snapshot isolation at a stable root | `make_isolation(..., snapshot_storage_root)` threaded through `IsolationContext(snapshot_base=...)`, `_run_single_scenario_strategy`, both `main` call sites | COMPLETE (`de3163f`) |
| Kaggle Qwen fail-closed `--model-path` validation + identity `qwen:<dir>` | `_validate_cli_args` + `_get_model_identity`; never `dry-run:mock` in non-dry mode | COMPLETE (`de3163f`) |
| Session exit code on failed last run | `_decide_session_exit_code` via `session_created_run_ids`/`last_run_status` | COMPLETE (`de3163f`) |
| Batched HF upload with truthful booleans | `_upload_batch_with_retry`/`CommitOperationAdd`/`create_commit` in `hf_sync.py` | COMPLETE (`de3163f`) |
| `mark_completed(completed_with_failures=...)` | `checkpoint.py` truthful completion metadata | COMPLETE (`de3163f`) |
| Fail-closed model discovery in notebook | `discover_model()` requires config.json + >=1 weight file | COMPLETE (`fb60972` notebook) |
| Scientific run guardrail in both run cells | `_verify_scientific_run()` (status, model calls > 0, `qwen:` identity, baseline/migration/evaluator, `remote_sync.json` last_sync) | COMPLETE (`fb60972` notebook) |
| Correct HF results repo | `NabilDo/selective-regeneration-experiment-results` | COMPLETE (`fb60972` notebook) |
| Continuous-cell markdown guard + `Terminal: n/9` vocabulary | notebook session wording | COMPLETE (`fb60972` notebook) |
| Preflight guardrail integration | `TestKaggleBundleRuntimeGuardrails` (6 tests) | COMPLETE (`de3163f`) |
| Bundled notebook pin regression (CLI test) | `test_notebook_benchmark_command_args` derives pin from canonical notebook (removed hard-coded `cb25e9f`) | COMPLETE (`fb60972`) |

## 3. Commits

| Commit | Message | Contents |
|---|---|---|
| `de3163f` | `fix(kaggle): close real Smoke runtime blockers` | `seven_arm_benchmark.py`, `src/benchmark/checkpoint/checkpoint.py`, `src/benchmark/checkpoint/hf_sync.py`, `tests/unit/execution/test_isolation.py`, `tests/unit/test_cli.py`, `tests/unit/test_hf_sync.py`, `tests/integration/test_scientific_smoke_v2_production_path.py`, `tests/integration/test_kaggle_bundle_smoke_v2_preflight.py` |
| `fb60972` | `chore(deploy): pin corrected Scientific Smoke V2 bundle` | `notebooks/seven_arm_benchmark.ipynb`, `kaggle_upload/**` (rebuilt bundle), `tests/unit/test_cli.py` |

```text
SOURCE_COMMIT   = de3163f12d51c31d3f488897ed2047821da3b190
DEPLOYED_BUILD_ID = de3163f
DEPLOYED_BUNDLE = fb60972 (rebuilt via scripts/build_upload_bundle.py)
HF_RESULTS_REPO = NabilDo/selective-regeneration-experiment-results
```

## 4. Runtime fixes detail

### 4.1 Shared-snapshot isolation root

`make_isolation(snapshot_root=..., snapshot_storage_root=...)` now derives a
stable `snapshot_base` from the storage root so all arms under one session
write snapshots into `workspace/snapshots` of the same workspace tree, matching
the real production layout the Kaggle runtime uses. The previous layout let
each arm compute a different snapshot root, so the shared baseline snapshot was
not found by sibling arms and the first arm failed isolation. The new
integration test `test_r5_shared_snapshot_root_arm_child_topology_succeeds`
proves all three child arms complete a full monolithic baseline run under a
shared snapshot root.

### 4.2 Kaggle Qwen fail-closed validation

`--model-path` in non-dry-run mode now requires a directory that actually
contains a Qwen model (config + weights); otherwise CLI validation fails closed
before any run. Model identity is `qwen:<resolved-model-path>`. The mock
`dry-run:mock` identity can no longer leak into real (non-dry) sessions, which
previously masked that the real model was never loaded.

### 4.3 Session exit code on failed last run

`_decide_session_exit_code(session_created_run_ids, last_run_status, ...)`
returns non-zero when a created run ended failed; a max-runs-terminated session
whose last run failed now exits 1 instead of 0. This makes Kaggle fail loudly
instead of reporting a "successful" run that never happened.

### 4.4 Batched, truthful HF upload

HF sync now accumulates uploads and commits them in batches via the Hub API
`CommitOperationAdd`/`create_commit`. All upload booleans are checked so
`remote_sync.json` truthfully reflects what was uploaded (upload/fetch/init/
config-fetch). Allowlist includes `benchmark-results`.

### 4.5 Notebook guardrails

The bundled notebook is pinned to `de3163f`. `discover_model()` resolves the
Kaggle input model directory, validates `config.json` and at least one weight
file, and fails closed if missing. `_verify_scientific_run()` is called at the
end of both run cells and enforces: run status succeeded; total workflow model
calls > 0; model identity starts `qwen:`; baseline/migration/evaluator passed;
`remote_sync.json` last_sync in (recovery, snapshot, final_uploaded). The
continuous-cell markdown blocks further auto-run until the guardrail passes and
session status uses `Terminal: n/9` vocabulary.

## 5. Tests

| Suite | Result |
|---|---|
| Unit isolation (`test_isolation.py`) | pass — new `TestMakeIsolationSharedSnapshot` (7) |
| Unit CLI (`test_cli.py`) | 57 passed |
| Unit HF sync (`test_hf_sync.py`) | pass — new `TestHfUploaderBatchedCommits`; 6 pre-existing tests rewritten off removed `_upload_with_retry` |
| Production-path integration | pass — incl. shared-root topology test |
| Kaggle bundle preflight (`test_kaggle_bundle_smoke_v2_preflight.py`) | **15 passed** (was 9; +`TestKaggleBundleRuntimeGuardrails` 6) |
| Combined unit + integration (isolation, cli, hf_sync, production path, real smoke, todo smoke evaluator) | 254 passed / 2 skipped (after CLI pin fix) |
| Full suite (last full gate) | 1,676 passed / 32 skipped / 0 failed |

Gates: `git diff --check` clean; Ruff 0 new violations (pre-existing baseline
remains, unchanged); Mypy strict = base 5 pre-existing errors only (all new
arg-type errors resolved via typed `snapshot_base`); `py_compile` clean.

## 6. Bundle

Rebuilt only through `scripts/build_upload_bundle.py`.

```text
code     = 87 files
data     = 56 files
notebooks = 1 (18,137 bytes)
total    = 144 files / 815,004 bytes
```

Preflight suite over the rebuilt bundle = 15 passed.

## 7. Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — both failed pre-model, preserved
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6; see KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md)
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9 (attempts failed before model calls; no new launch without re-audit)
Tag = not created
Pilot = not authorized
```

## 8. Next action

The core runtime-fix audit passed (see
`..\R7A_Pre_Rerun_Hardening_Package\01_R7_RUNTIME_FIX_INDEPENDENT_AUDIT.md`).
The R7A pre-rerun hardening pass closed all four audit findings and is recorded
in `selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md`.
Independent re-audit of the R7A hardening is required before any Kaggle relaunch.
Do not relaunch Kaggle, tag, merge, or force-push before that re-audit passes.

R7A_HARDENING_REAUDIT_REQUIRED
