# Project Root and Path Policy — v1.0

**Phase:** 3.5 — Static Architecture Audit and Project Map  
**Date:** 2026-07-22  
**Status:** FROZEN

---

## 1. Canonical Project Root

The canonical Git repository root is:

```
C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\
```

All paths in this document and all derived documents are relative to this canonical root unless explicitly stated otherwise.

## 2. Outer Directory (Outside Git)

The outer directory at `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\` contains files outside the Git repository. These are NOT part of the benchmark project and must not be committed.

### Contents of outer directory

| Path | Status | Action |
|------|--------|--------|
| `docs/OPENCODE_EXECUTION_GUIDE.md` | Outside Git | Copy into project/docs/; keep root copy for reference |
| `docs/MASTER_IMPLEMENTATION_PLAN.md` | Outside Git | Copy into project/docs/; keep root copy for reference |
| `docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md` | Outside Git | Already superseded by project/docs/; stale |
| `docs/HUMAN_DECISIONS_REQUIRED.md` | Outside Git | Already superseded; stale |
| `inputs/paper/` | Outside Git | Contains the authoritative paper PDF and TEX; must remain immutable |
| `benchmark_data/` | Outside Git | Stale duplicate of project/benchmark_data/; should be deleted |

## 3. Directory Classification

| Directory | Inside Git | Type | Immutable | Created In | Notes |
|-----------|-----------|------|-----------|------------|-------|
| `docs/` | Yes | Documentation | Yes (protocol docs); No (architecture docs) | Phase 0+ | 8 frozen protocol docs + new Phase 3.5 docs |
| `benchmark_data/` | Yes | Benchmark data | Yes (manifests, profiles); No (scenarios may be refined per DA-07) | Phase 3 | Contains manifests, profiles, scenarios |
| `src/benchmark/` | Yes | Source code | No | Phase 0 (scaffold) | Phase 4 will implement |
| `tests/` | Yes | Tests | No | Phase 0 (scaffold) | Phase 4+ will implement |
| `reports/` | Yes | Reports | No | Phase 0 | Phase reports, architecture reports, environment reports |
| `notebooks/` | Yes | Notebooks | No | Phase 0 (empty) | Phase 8 will populate |
| `scripts/` | Yes | Scripts | No | Phase 0 (empty) | Phase 4+ will populate |
| `configs/` | Yes | Configuration | Yes (when frozen) | Phase 4 | Execution profiles (smoke, pilot, research) |
| `private_evaluation/` | Yes | Private data | Yes | Phase 4 | Hidden tests, ground truth, scoring oracle |
| `runs/` | Yes | Run output | No (add to .gitignore) | Phase 4 | Generated run data; do not commit |
| `kaggle_upload/` | Yes | Upload bundle | No | Phase 9 | Temporary build output for Kaggle |
| `release/` | Yes | Release | Yes (when tagged) | Phase 9 | Release candidate artifacts |

## 4. External Source Inputs

The `inputs/` directory at the outer level (outside Git) contains the authoritative source materials:

| File | Status | Description |
|------|--------|-------------|
| `inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.pdf` | Immutable | Original paper PDF |
| `inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.tex` | Immutable | Original paper LaTeX source |

These files must never be modified. They are the authoritative constraint for all scientific decisions.

## 5. Generated and Cache Directories

| Path | Handling |
|------|----------|
| `.mypy_cache/` | Already ignored; safe to delete periodically |
| `.ruff_cache/` | Already ignored; safe to delete periodically |
| `__pycache__/` | Standard Python cache; add to .gitignore |
| `runs/` | Add to .gitignore; contains generated run records |
| `notebooks/kaggle/` | Only committed with cleared outputs |

## 6. Duplicate Structure Remediation

The following duplicates exist between the outer directory and the Git repository:

| Outer Directory | Git Repository | Severity | Remediation |
|----------------|---------------|----------|-------------|
| `docs/` (4 files) | `project/docs/` (8+ files) | HIGH | Copy OPENCODE_EXECUTION_GUIDE.md and MASTER_IMPLEMENTATION_PLAN.md into project/docs/; delete root docs/ files that are superseded; document plan |
| `benchmark_data/` | `project/benchmark_data/` | MEDIUM | Root benchmark_data/ is a stale subset; delete root-level benchmark_data/ after confirming project/benchmark_data/ is complete |
| `inputs/` | (none) | LOW | inputs/ belongs outside Git; this is correct |

### Remediation Plan

1. Copy `docs/OPENCODE_EXECUTION_GUIDE.md` (outer) → `project/docs/OPENCODE_EXECUTION_GUIDE.md` (ensure present if not already)
2. Copy `docs/MASTER_IMPLEMENTATION_PLAN.md` (outer) → `project/docs/MASTER_IMPLEMENTATION_PLAN.md`
3. Compare root `benchmark_data/` files with `project/benchmark_data/` to verify completeness
4. Run `Remove-Item -Recurse docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md docs/HUMAN_DECISIONS_REQUIRED.md` in outer dir
5. Run `Remove-Item -Recurse benchmark_data` in outer dir (after verification)
6. Update `.gitignore` to ignore generated directories (`runs/`, `__pycache__/`)
7. Commit all changes

## 7. Path Reference Convention

All documentation must reference files relative to the canonical root (`project/`).

```markdown
<!-- Correct -->
See `docs/FINAL_RESEARCH_PROTOCOL.md`

<!-- Incorrect -->
See `project/docs/FINAL_RESEARCH_PROTOCOL.md`
```

The outer directory prefix (`project/`) is omitted because the canonical root IS `project/`.

For the rare case where the outer directory must be referenced, prefix with `outer/`:
```markdown
See `outer/inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.pdf`
```
