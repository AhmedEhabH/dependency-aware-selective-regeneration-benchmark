# Canonical Architecture Audit Report

**Date:** 2026-07-24
**Phase:** Documentation-first canonical architecture and artifact audit
**Branch:** `audit/canonical-project-architecture`
**Status:** COMPLETE (non-destructive documentation-only phase)

---

## Summary

Documentation-first canonical architecture audit completed. All 10 required documents created. No structural remediation or production-code changes performed.

---

## Documents Created

| Document | Path | Purpose |
|----------|------|---------|
| CANONICAL_ARTIFACT_INVENTORY.md | `docs/CANONICAL_ARTIFACT_INVENTORY.md` | Exhaustive inventory of all artifact groups with 22-field record each |
| PROJECT_ENTITIES_AND_DATA_FLOWS.md | `docs/PROJECT_ENTITIES_AND_DATA_FLOWS.md` | Entity definitions + 5 Mermaid data-flow diagrams |
| SOURCE_OF_TRUTH_MATRIX.md | `docs/SOURCE_OF_TRUTH_MATRIX.md` | Canonical source designations, duplicate classification |
| IMPLEMENTED_ARCHITECTURE_BASELINE.md | `docs/IMPLEMENTED_ARCHITECTURE_BASELINE.md` | What code actually does vs what docs claim |
| SELECTIVE_PROJECT_UPDATE_POLICY.md | `docs/SELECTIVE_PROJECT_UPDATE_POLICY.md` | Workflow for minimal-regeneration changes |
| PROPOSED_CANONICAL_PROJECT_STRUCTURE.md | `docs/PROPOSED_CANONICAL_PROJECT_STRUCTURE.md` | Target tree with 8 proposed moves |
| NEXT_CHANGE_IMPACT_PLAN.md | `docs/NEXT_CHANGE_IMPACT_PLAN.md` | Impact analysis for the `runs_dir` NameError fix |
| ARTIFACT_DRIFT_AUDIT.md | `reports/ARTIFACT_DRIFT_AUDIT.md` | SHA-256 comparisons across all bundles |
| STRUCTURE_AND_ARCHITECTURE_PROBLEMS.md | `reports/STRUCTURE_AND_ARCHITECTURE_PROBLEMS.md` | 14 issues documented with severity/impact/remediation |
| CANONICAL_ARCHITECTURE_AUDIT_REPORT.md | `reports/CANONICAL_ARCHITECTURE_AUDIT_REPORT.md` | This report |

---

## Findings Summary

### Duplicate Structures Found

1. **Duplicate `kaggle_upload/`** — `<parent>/kaggle_upload/` (outer, stale) vs `project/kaggle_upload/` (inner, current)
2. **Outer docs/** — `<parent>/docs/` with 2 reference copies
3. **Empty inner data bundle** — `project/kaggle_upload/data/` is empty; `<parent>/kaggle_upload/data/` is populated

### Canonical Source Recommendations

| Artifact | Recommended Source | Status |
|----------|-------------------|--------|
| Source code | `project/src/benchmark/` | CANONICAL |
| CLI script | `project/seven_arm_benchmark.py` | CANONICAL |
| Scenarios | `project/benchmark_data/scenarios/` | CANONICAL |
| Configs | `project/configs/` | CANONICAL |
| Notebook | `project/notebooks/` | CANONICAL |
| Code bundle | `project/kaggle_upload/code/` | GENERATED_DERIVATIVE (needs cleanup) |
| Data bundle | `<parent>/kaggle_upload/data/` → should migrate to `project/kaggle_upload/data/` | STALE_DUPLICATE (currently) |

### Artifact Drift Summary

| Comparison | Result |
|-----------|--------|
| Inner code bundle vs canonical | **66/66 MATCH** (fully synchronized) |
| Outer code bundle vs canonical | **62/66 MATCH**, 1 content mismatch, 3 line-ending only |
| Outer data bundle vs canonical | **29/29 MATCH** (fully synchronized) |
| Inner data bundle | **EMPTY** (synchronization failure) |
| Inner notebook bundle vs canonical | **MATCH** |
| Outer notebook bundle vs canonical | **Line-ending only** |

### Proposed Target Structure

Single Git root at `project/`. Clean inner `kaggle_upload/` (remove `.git/`, caches, `egg-info`; populate `data/`). Delete outer duplicates. Implement automated bundle build script.

### Proposed Minimal Remediation Sequence

1. Implement `scripts/build_upload_bundle.py`
2. Clean inner `kaggle_upload/` bundle (remove `.git/`, caches, `egg-info`)
3. Populate inner `kaggle_upload/data/` from `benchmark_data/`
4. Delete outer `<parent>/kaggle_upload/`
5. Delete outer `<parent>/docs/` reference copies
6. Add `_auto_resume_temp/` and `benchmark-results.zip` to `.gitignore`
7. Normalize line endings

### Exact Affected-Artifact List for `runs_dir` Fix

- **Primary:** `project/seven_arm_benchmark.py` (1–3 lines)
- **Tests:** Possibly `tests/unit/test_cli.py`
- **Bundles:** Inner and outer `kaggle_upload/code/seven_arm_benchmark.py` (regenerate)
- **Documentation:** `SYSTEM_STATE.md`, `TODO.md`, `DECISION_LOG.md`, `reports/latest_phase_report.md`, `reports/PROJECT_HEALTH_REPORT.md`
- **Notebook:** UNCHANGED
- **Data bundles:** UNCHANGED

### Human Decisions Required

1. **Delete outer `kaggle_upload/`?** — Yes recommended. Engineering decision.
2. **Delete outer `docs/`?** — Yes recommended. Already copied in Phase 3.6.
3. **Populate inner `kaggle_upload/data/` from `benchmark_data/`?** — Yes recommended. Critical for Kaggle deployment.
4. **Remove `.git/` from inner bundle?** — Yes recommended. Engineering decision.
5. **Implement bundle build script?** — Yes recommended. Prevents future drift.
6. **Add `_auto_resume_temp/` to `.gitignore`?** — Yes recommended.
7. **Normalize line endings (CRLF→LF)?** — Low priority, but prevents false SHA-256 mismatches.
8. **Update SOFTWARE_ARCHITECTURE.md** to include `checkpoint/`, `comparison/`, `selection/` packages?

---

## Declaration

```
Documentation-first canonical architecture audit completed.
No structural remediation or production-code changes performed.
Next action requires researcher-approved remediation plan.
```

The `runs_dir` defect is NOT fixed in this phase.

**Branch:** `audit/canonical-project-architecture`
