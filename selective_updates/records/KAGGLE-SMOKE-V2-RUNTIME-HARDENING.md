# Kaggle Smoke V2 — Pre-Rerun Runtime Hardening (R7A)

**Phase ID:** R7A-PRE-RERUN-HARDENING
**Ledger ID:** KAGGLE-SMOKE-V2-RUNTIME-HARDENING
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-runtime-blockers`
**Status:** **COMPLETE — INDEPENDENT RE-AUDIT REQUIRED BEFORE KAGGLE**
**Starting HEAD:** `d9068fd` (docs(state): record Kaggle Smoke V2 runtime fix)
**Directive:** `..\R7A_Pre_Rerun_Hardening_Package\02_OPENCODE_R7A_HARDENING_DIRECTIVE.md`
**Independent audit:** `..\R7A_Pre_Rerun_Hardening_Package\01_R7_RUNTIME_FIX_INDEPENDENT_AUDIT.md`
---

## 1. Purpose

The independent audit accepted the core Kaggle runtime fix (shared-snapshot
isolation root, Qwen fail-closed validation, failed-run exit code, batched HF
commits, notebook guardrails) and reproduced four bounded findings to close
before any further Kaggle execution:

| Finding | Root cause |
|---|---|
| A — remote recovery state uploaded as `pending` | `upload_recovery()` wrote `pending` before the commit, committed that file, then rewrote local to `recovery_uploaded`; remote held `pending` |
| B — notebook status cell used an obsolete schema | inspection cell read `last_sync_time`/`experiments_synced`/`runs_uploaded`; actual schema is `last_sync`/`timestamp`/`remote_path`/`details` |
| C — two HF test fixtures library-version sensitive | `RepositoryNotFoundError("not found")` / `HfHubHTTPError("mock upload failure")` fail on newer constructors requiring an HTTP response |
| D — current documentation trailed the final gate | docs still reported `1,676 passed / 32 skipped` and pending Commit C / branch push, though complete |

## 2. Authorized scope executed

Modified only the directive-authorized functional files:

```text
src/benchmark/checkpoint/hf_sync.py
tests/unit/test_hf_sync.py
notebooks/seven_arm_benchmark.ipynb
tests/unit/test_cli.py
kaggle_upload/** (generated only through scripts/build_upload_bundle.py)
```

No isolation, strategy, Runner, metrics, scenario, evaluator, controlled-data,
Pilot, or Research change. No new architecture. No merge. No tag. No Kaggle run.

## 3. Finding A closure — truthful remote recovery state

`upload_recovery()` now:

1. Builds the recovery file list from `RECOVERY_FILES` (a stale status file is excluded).
2. Writes `remote_sync.json` **before** `create_commit` with:
   ```json
   {
     "last_sync": "recovery_uploaded",
     "remote_path": "<recovery path>",
     "details": "all recovery files uploaded"
   }
   ```
3. Includes that exact file in the **same** recovery commit (one `create_commit`).
4. On success, leaves the local file identical to the committed file.
5. On failure, overwrites the local file with `last_sync = failed_local_safe`,
   preserving the actual remote path and error details, retains
   `remote_sync_failure.json`, and returns `False`.
6. Never uploads `pending` as the final remote state; never creates a second
   recovery-status commit.

Failure state is `failed_local_safe`; success state is `recovery_uploaded`.

## 4. Finding B closure — notebook status schema

The `progress-cell` inspection cell now reads and prints:

```text
Last sync status   <- last_sync
Timestamp          <- timestamp
Remote path        <- remote_path
Details            <- details
```

and no longer references `last_sync_time` / `experiments_synced` /
`runs_uploaded`. Guardrail logic (`last_sync`) and execution commands unchanged.

## 5. Finding C closure — version-compatible HF fixtures

- `RepositoryNotFoundError` is built with a valid `httpx.Request` and
  `httpx.Response(404, request=request)`, passed as `response=response`.
- The generic uploader failure path now raises `RuntimeError("mock upload failure")`
  (production catches generic exceptions).
- No version conditionals; no obsolete library pin.

Compatibility target: current Windows environment + `huggingface_hub` 1.x
constructor contract.

## 6. Finding D closure — documentation truth

Current state/reports updated to the actual final gate; historical phase counts
preserved. Full suite final gate: **1,688 passed / 32 skipped / 0 failed**.

## 7. Commits

| Commit | Message | Contents |
|---|---|---|
| `d50e89e` | `fix(hf): make recovery sync state remotely truthful` | `src/benchmark/checkpoint/hf_sync.py`, `tests/unit/test_hf_sync.py` (TestHfRecoveryStateTruth, 5 new tests; version-compatible fixtures) |
| `4c73db6` | `chore(deploy): pin hardened Scientific Smoke V2 rerun bundle` | `notebooks/seven_arm_benchmark.ipynb` (status schema + new source/build pin), `tests/unit/test_cli.py` (`test_notebook_sync_display_uses_current_schema`), `kaggle_upload/**` (rebuilt bundle) |
| docs commit | `docs(audit): record pre-rerun runtime hardening` | documentation truth + this ledger |

```text
HARDENED_RUNTIME_SOURCE_COMMIT = d50e89ee511b9dcf6e577e62ba4d9bb47014b6fc
HARDENED_RUNTIME_BUILD_ID     = d50e89e
HARDENED_DEPLOYMENT_BUNDLE    = 4c73db6 (rebuilt via scripts/build_upload_bundle.py)
HF_RESULTS_REPO               = NabilDo/selective-regeneration-experiment-results
```

## 8. Tests

New exact remote-state truth tests (`tests/unit/test_hf_sync.py`):

```text
TestHfRecoveryStateTruth
  test_recovery_commit_contains_recovery_uploaded_state
  test_successful_recovery_local_state_matches_committed_state
  test_failed_recovery_sets_failed_local_safe
  test_failed_recovery_preserves_failure_record
  test_recovery_still_uses_exactly_one_create_commit
```

Notebook schema test (`tests/unit/test_cli.py`):

```text
test_notebook_sync_display_uses_current_schema
```

| Suite | Result |
|---|---|
| Unit HF sync (`test_hf_sync.py`) | 79 passed / 1 skipped |
| Unit CLI (`test_cli.py`) | 58 passed |
| Bundle builder (`test_build_upload_bundle.py`) | 10 passed |
| Kaggle bundle preflight (`test_kaggle_bundle_smoke_v2_preflight.py`) | 15 passed |
| Full suite (final gate) | **1,688 passed / 32 skipped / 0 failed** |

Gates: compileall clean; Ruff 0 new violations versus `d9068fd` (baseline 91, current 91);
Mypy strict 0 issues; `git diff --check` clean; builder rerun leaves tree unchanged;
worktree/index/HEAD manifests: code 87 / data 56 / notebook 1 — 0 mismatches.

## 9. Bundle

Rebuilt only through `scripts/build_upload_bundle.py`.

```text
code     = 87 files / 625,307 bytes
data     = 56 files / 172,210 bytes
notebooks = 1 (18,262 bytes)
total    = 144 files / 815,779 bytes
```

## 10. Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze 4b2dd27)
Two failed Kaggle attempts preserved (exp-20260801-024041, exp-20260801-024624)
Core runtime blockers = fixed (de3163f) and accepted by independent audit
Remote sync truth defect = closed (d50e89e)
Notebook status schema = corrected (4c73db6)
HF tests = version-compatible (d50e89e)
Runtime hardening = complete, pending independent re-audit
Valid Qwen results = 0/9
Kaggle rerun = BLOCKED until independent re-audit
Tag = not created
Merge = not performed
Pilot = not authorized
```

## 11. Next action

Short independent re-audit of the R7A hardening (R7A_HARDENING_REAUDIT_REQUIRED).
After re-audit: update the Kaggle code dataset + notebook, run one real cell,
require 1/9 succeeded, then continue the remaining eight cells.

R7A_HARDENING_REAUDIT_REQUIRED
