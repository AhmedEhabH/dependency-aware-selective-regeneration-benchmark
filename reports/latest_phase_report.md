# runs_dir NameError Fix — SU-0002

**Date:** 2026-07-24  
**Status:** COMPLETE  
**Branch:** `fix/su-0002-runs-dir-nameerror` → `main` (via --no-ff merge)  
**Evidence:** NameError fixed, regression tests added, bundle rebuilt and verified

---

## Summary

Fixed `NameError: name 'runs_dir' is not defined` in `seven_arm_benchmark.py` at line 957 (START_NEW path). The variable `output_dir` (defined at line 828 from `--output-dir` CLI argument) is the correct variable. Single-line fix: `runs_dir` → `output_dir`.

---

## Deliverables

| Artifact | Status |
|----------|--------|
| `seven_arm_benchmark.py` | Fixed (line 957: `runs_dir` → `output_dir`) |
| `tests/unit/test_cli.py` | Added `TestRunsDirBugFix` with 2 regression tests |
| `kaggle_upload/code/seven_arm_benchmark.py` | Rebuilt, checksum verified |
| SU-0002 record | Created at `selective_updates/records/SU-0002-runs-dir-nameerror-fix.md` |
| CHANGE_INDEX.md | Updated with SU-0002 |
| change_metrics.jsonl | Appended SU-0002 metrics |

---

## Bundle Verification

```
Code bundle:     72 files, 293,668 bytes (CLI checksum matches canonical, normalized)
Data bundle:     29 files, 135,604 bytes (unchanged)
Notebook bundle:  1 file,   8,575 bytes (unchanged)
Total:          102 files, 437,847 bytes
Verification:    0 errors (all checksums match canonical)
```

---

## Quality Gates

| Gate | Result |
|------|--------|
| Bundle builder self-verification | PASS (0 errors) |
| `python kaggle_upload/code/seven_arm_benchmark.py --help` | PASS |
| `python seven_arm_benchmark.py --dry-run --profile smoke` | PASS (7/7 runs) |
| `python -m pytest tests/unit/test_cli.py` | 17 passed (2 new) |
| `python -m pytest tests/` | 613 passed, 2 skipped |
| `ruff check src tests seven_arm_benchmark.py scripts` | Pre-existing issues only (no new) |
| `mypy --strict src tests seven_arm_benchmark.py scripts` | Pre-existing issues only (no new) |
| `python -m pip check` | PASS (project deps clean) |
| Bundle imports from arbitrary CWD | PASS |
| 24/24 scenarios load from bundle data | PASS |
| SHA-256 manifests complete | PASS (3 manifests) |
| Frozen protocol checksums unchanged | PASS (8 docs) |

---

## Selective-Update Ledger (SU-0002)

**Change ID:** SU-0002  
**Title:** runs_dir NameError fix  
**Canonical artifacts affected:** 2 (`seven_arm_benchmark.py`, `tests/unit/test_cli.py`)  
**Derivatives regenerated:** 1 (`kaggle_upload/code/seven_arm_benchmark.py`)  
**Defects detected:** 1 (NameError in START_NEW path)  
**Defects introduced:** 0  
**Quality outcome:** preserved  
**Record:** `project/selective_updates/records/SU-0002-runs-dir-nameerror-fix.md`  
**Metrics:** `project/selective_updates/metrics/change_metrics.jsonl`

---

## Residual Risks

None identified.

---

## Next Exact Task

**SU-0003** — (next requirement from backlog)

---

## Git History

| Commit | Description |
|--------|-------------|
| `16a993e` | merge: chore/canonical-project-remediation into main (--no-ff) |
| `f47c088` | chore(structure): establish canonical project and reproducible bundles |
| `9dbd49f` | merge: audit/canonical-project-architecture into main (--no-ff) |
| `fix/su-0002-runs-dir-nameerror` | Fix runs_dir NameError, add regression tests (merge pending) |