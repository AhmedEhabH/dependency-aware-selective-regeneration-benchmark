# Canonical Structure Remediation — Phase 3.7

**Date:** 2026-07-24  
**Status:** COMPLETE  
**Branch:** `chore/canonical-project-remediation` → `main` (via --no-ff merge)  
**Evidence:** Reproducible bundles, selective-update ledger, outer duplicates removed

---

## Summary

Documentation-first architecture audit findings implemented. Inner `project/kaggle_upload/` rebuilt from canonical sources via deterministic script `scripts/build_upload_bundle.py`. Selective-update ledger `project/selective_updates/` established. Outer stale duplicates removed. No frozen protocol documents modified. `runs_dir` defect deferred to SU-0002.

---

## Deliverables

| Artifact | Status |
|----------|--------|
| `scripts/build_upload_bundle.py` | Created, verified |
| `project/kaggle_upload/code/` (72 files) | Populated, no forbidden items |
| `project/kaggle_upload/data/` (29 files) | 24 scenarios + 2 manifests + 3 profiles, checksums verified |
| `project/kaggle_upload/notebooks/` (1 file) | Populated, matches canonical |
| `project/selective_updates/` | Created with SU-0001 |
| `.gitignore` | Updated (auto-resume temp, results zip, caches) |
| `_auto_resume_temp/` | Deleted |
| `benchmark-results.zip` | Deleted |
| Outer `<parent>/kaggle_upload/` | Deleted (verified match) |
| Outer `<parent>/docs/` | Deleted (verified stale) |

---

## Bundle Verification

```
Code bundle:     72 files, 293,662 bytes
Data bundle:     29 files, 135,604 bytes (24 scenarios, 2 manifests, 3 profiles)
Notebook bundle:  1 file,   8,575 bytes
Total:          102 files, 437,841 bytes
Verification:    0 errors (all checksums match canonical, normalized)
Forbidden items: 0
Package tree:    kaggle_upload/code/src/benchmark/ (correct, not flattened)
```

---

## Quality Gates

| Gate | Result |
|------|--------|
| Bundle builder self-verification | PASS (0 errors) |
| `python kaggle_upload/code/seven_arm_benchmark.py --help` | PASS |
| `python -m pytest tests/` | 611 passed, 2 skipped |
| `ruff check src tests seven_arm_benchmark.py scripts` | Pre-existing issues only (no new) |
| `mypy --strict src tests seven_arm_benchmark.py scripts` | Pre-existing issues only (no new) |
| `python -m pip check` | PASS (project deps clean) |
| Bundle imports from arbitrary CWD | PASS |
| 24/24 scenarios load from bundle data | PASS |
| SHA-256 manifests complete | PASS (3 manifests) |
| Ledger links resolve | PASS |
| `change_metrics.jsonl` valid JSONL | PASS |
| Frozen protocol checksums unchanged | PASS (8 docs) |

---

## Selective-Update Ledger (SU-0001)

**Change ID:** SU-0001  
**Title:** Canonical structure remediation  
**Canonical artifacts affected:** 13 (script, .gitignore, docs, state files)  
**Derivatives regenerated:** 102 bundle files  
**Defects detected:** 5 (empty data bundle, polluted code bundle, no builder, no ledger, stale outer)  
**Defects introduced:** 0  
**Quality outcome:** preserved  
**Record:** `project/selective_updates/records/SU-0001-canonical-structure-remediation.md`  
**Metrics:** `project/selective_updates/metrics/change_metrics.jsonl`  

---

## Residual Risks

1. **SU-0002 — `runs_dir` NameError** — Not fixed this phase; planned as minimal selective fix
2. **Outer deletion** — Completed; PowerShell commands used (auto-delete from Git root not possible)
3. **Pre-existing lint/type issues** — Unchanged; not introduced by this remediation

---

## Next Exact Task

**SU-0002 — Selective `runs_dir` NameError fix**  
- Affected: `src/benchmark/execution/pipeline.py` (failure path)
- Test: `tests/unit/execution/test_pipeline.py`
- Bundle: Rebuild via `scripts/build_upload_bundle.py`
- Ledger: SU-0002 record

---

## Git History

| Commit | Description |
|--------|-------------|
| `ae6efa6` | docs: audit canonical architecture and artifact ownership (on audit branch) |
| `9dbd49f` | merge: audit/canonical-project-architecture into main (--no-ff) |
| `chore/canonical-project-remediation` | Remediation commits (multiple, --no-ff merge pending) |