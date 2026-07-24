# Next Change Impact Plan — `runs_dir` NameError Fix

**Date:** 2026-07-24
**Issue:** `NameError: runs_dir is not defined`
**Branch:** `audit/canonical-project-architecture`
**Status:** PLANNED (not yet implemented)
**Purpose:** Identify every artifact affected by the fix before implementation begins.

---

## 1. Defect Identification

| Field | Value |
|-------|-------|
| Defect | `NameError: runs_dir is not defined` |
| Symptom | Code references variable `runs_dir` that is not yet defined in the current scope |
| Likely location | `seven_arm_benchmark.py` or a module it imports |
| Likely cause | Variable `runs_dir` expected to be defined from a `--output-dir` argument parsing but the variable binding is missing or scoped incorrectly |

---

## 2. Canonical Source File Affected

| Artifact | Path | Likelihood |
|----------|------|-----------|
| Main CLI script | `project/seven_arm_benchmark.py` | **HIGH** — CLI arg parsing and output directory setup |
| Runner module | `src/benchmark/execution/runner.py` | **MEDIUM** — might reference runs_dir from config |
| Pipeline module | `src/benchmark/execution/pipeline.py` | **MEDIUM** — might reference runs_dir |
| Checkpoint module | `src/benchmark/checkpoint/checkpoint.py` | **LOW** — accepts output_dir as parameter |

Expected fix scope: 1–3 lines in `seven_arm_benchmark.py` (likely defining `runs_dir = output_dir` or similar).

---

## 3. Tests Affected

| Test | Path | Likely Impact |
|------|------|--------------|
| CLI tests | `tests/unit/test_cli.py` | **HIGH** — if CLI argument parsing is tested |
| Real smoke test | `tests/integration/test_real_smoke.py` | **MEDIUM** — if it invokes the CLI |
| Pipeline tests | `tests/unit/execution/test_pipeline.py` | **LOW** — tests module directly, not CLI |
| Runner tests | `tests/unit/execution/test_runner.py` | **LOW** — tests module directly |

Expected test impact: 0–2 test files may need assertions added or updated.

---

## 4. Notebook

| Aspect | Assessment |
|--------|-----------|
| Affected? | **NO** — notebook calls CLI with `--output-dir /kaggle/working/runs`; the CLI bug is in local path resolution, not in the flag handling |
| Unaffected? | Yes — notebook cells 7/8 construct `--output-dir` argument correctly |
| Requires notebook update? | No |

---

## 5. Bundle Artifacts Requiring Regeneration

| Bundle | Regeneration Needed | Files |
|--------|-------------------|-------|
| Inner `kaggle_upload/code/` | **YES** — `seven_arm_benchmark.py` is in the bundle | 1 file |
| Outer `kaggle_upload/code/` | **YES** — `seven_arm_benchmark.py` is in the bundle | 1 file |
| Inner `kaggle_upload/data/` | No | — |
| Outer `kaggle_upload/data/` | No | — |
| Inner `kaggle_upload/notebooks/` | No | — |
| Outer `kaggle_upload/notebooks/` | No | — |

All bundles must be regenerated after fix, even if only 1 file changed. Per SELECTIVE_PROJECT_UPDATE_POLICY, only the affected derivative should be regenerated.

---

## 6. Documentation Requiring Update

| Document | Update Needed |
|----------|--------------|
| `docs/KAGGLE_EXECUTION_GUIDE.md` | **No** — notebook commands use `--output-dir` correctly |
| `docs/HUGGINGFACE_RESULTS_PERSISTENCE.md` | **No** — references `--output-dir` flag |
| `docs/PROJECT_ROOT_AND_PATH_POLICY.md` | **No** — path policy unchanged |
| `SYSTEM_STATE.md` | **Yes** — mark fix as completed |
| `TODO.md` | **Yes** — mark task as completed |
| `DECISION_LOG.md` | **Yes** — add decision entry for the fix |
| `reports/latest_phase_report.md` | **Yes** — update |
| `reports/PROJECT_HEALTH_REPORT.md` | **Yes** — update |

---

## 7. Artifacts That Must Remain Untouched

- All frozen protocol documents (`docs/FINAL_RESEARCH_PROTOCOL.md`, companions)
- All scenario YAMLs (`benchmark_data/scenarios/*.yaml`)
- All repository profiles (`benchmark_data/repository_profiles/*.yaml`)
- All manifests (`benchmark_data/manifests/*.yaml`)
- All source modules except the one containing the bug
- All test modules (unless they contain assertions about `runs_dir`)
- All config profiles (`configs/*.yaml`)

---

## 8. Expected Minimal Diff

```
1 file changed, 1 insertion(+), 0 deletions(-)
# or:
1 file changed, 2 insertions(+), 1 deletion(-)

In seven_arm_benchmark.py:
-  (runs_dir missing)
+ runs_dir = output_dir
+ os.makedirs(runs_dir, exist_ok=True)
```

---

## 9. Expected Validation Commands

```bash
# 1. Run CLI help (verify no crash)
python seven_arm_benchmark.py --help

# 2. Run dry-run smoke (verify pipeline completes)
python seven_arm_benchmark.py --dry-run --profile smoke

# 3. Run relevant tests
python -m pytest tests/unit/test_cli.py -v --tb=short

# 4. Run full test suite
python -m pytest tests/ -v --tb=short

# 5. Run quality gates
ruff check src/benchmark/ seven_arm_benchmark.py tests/
mypy src/benchmark/ seven_arm_benchmark.py
pip check
```

---

## 10. Expected Bundle Synchronization Actions

```bash
# Regenerate inner bundle
Copy-Item seven_arm_benchmark.py kaggle_upload/code/

# Verify checksum
$can = (Get-FileHash seven_arm_benchmark.py).Hash
$bun = (Get-FileHash kaggle_upload/code/seven_arm_benchmark.py).Hash
if ($can -ne $bun) { throw "Checksum mismatch" }
```

---

## 11. Auto-Resume Retest Impact

| Aspect | Assessment |
|--------|-----------|
| Affected? | **LOW** — auto-resume tests check checkpoint/resume logic, not CLI arg parsing |
| Related test file | `tests/unit/test_checkpoint.py` |
| Requires re-run? | Yes — run full test suite to ensure no regression |
| Risk of regression | Low — the fix is isolated to CLI path setup |

```bash
python -m pytest tests/unit/test_checkpoint.py tests/unit/test_cli.py -v --tb=short
```
