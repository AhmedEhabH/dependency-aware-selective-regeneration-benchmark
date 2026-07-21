# Project Structure Conflict Report — v1.0

**Phase:** 3.5 — Static Architecture Audit and Project Map  
**Date:** 2026-07-22  
**Status:** DOCUMENTED (not yet remediated)

---

## 1. Critical Finding: Duplicate Directory Structure

The project has a **split directory layout** where files exist both at the outer directory and inside the Git repository, creating ambiguity about the canonical source of truth.

### Root Cause

Earlier OpenCode sessions wrote some files to the outer directory (`C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\`) while the Git repository is at `project/`. This created two partial, overlapping file trees.

---

## 2. Inventory of Conflicts

### Conflict C1: `docs/` (outside Git) vs `project/docs/` (inside Git)

| Outside Git (stale) | Inside Git (authoritative) | Action |
|---------------------|---------------------------|--------|
| `OPENCODE_EXECUTION_GUIDE.md` | (missing) | Copy into project/docs/ |
| `MASTER_IMPLEMENTATION_PLAN.md` | (missing) | **Already exists** at project/docs/ — duplicate with different content |
| `FINAL_RESEARCH_PROTOCOL_DECISIONS.md` | (superseded) | Stale — all decisions incorporated into `RESEARCHER_DECISIONS_DA_AC.md` |
| `HUMAN_DECISIONS_REQUIRED.md` | (superseded) | Stale — all decisions resolved in Phase 2B |
| (missing) | `FINAL_RESEARCH_PROTOCOL.md` | Authoritative — keep |
| (missing) | 7 other frozen protocol docs | Authoritative — keep |
| (missing) | 8 Phase 3.5 architecture docs | Authoritative — keep |

**Remediation:**
1. Copy `OPENCODE_EXECUTION_GUIDE.md` and `MASTER_IMPLEMENTATION_PLAN.md` into `project/docs/` (or preserve if already there)
2. Delete root `docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md` and `docs/HUMAN_DECISIONS_REQUIRED.md`
3. Ensure root `docs/` is NOT tracked by Git

### Conflict C2: `benchmark_data/` (outside Git) vs `project/benchmark_data/` (inside Git)

The root-level `benchmark_data/` contains a subset of files:
- Has `repository_profiles/djangocms.yaml` and `repository_profiles/saleor.yaml` (missing `todo.yaml`)
- Has all scenario YAML files (24 files) — appears complete
- Missing `manifests/` directory entirely

The `project/benchmark_data/` has the FULL set:
- `manifests/repositories.yaml` and `manifests/repository_versions.yaml`
- `repository_profiles/todo.yaml`, `djangocms.yaml`, `saleor.yaml`
- All 24 scenario YAML files

**Assessment:** The root `benchmark_data/` is a stale partial duplicate. The project version is more complete.

**Remediation:**
1. Verify `project/benchmark_data/scenarios/` has all 24 files (confirmed)
2. Delete root `benchmark_data/` directory
3. Confirm no references to root `benchmark_data/` paths exist in any documentation

### Conflict C3: `inputs/` (outside Git, no Git counterpart)

The `inputs/` directory containing the authoritative paper exists ONLY outside Git. This is correct by design — source inputs are immutable and outside version control.

**Remediation:** No change needed.

---

## 3. Missing Expected Directories

| Directory | Expected | Status | Phase to Create |
|-----------|----------|--------|-----------------|
| `configs/` | Execution profiles | Missing | Phase 4 |
| `private_evaluation/` | Hidden tests, ground truth | Missing | Phase 6 |
| `runs/` | Generated run output | Missing | Phase 4 |
| `kaggle_upload/` | Kaggle upload bundle | Missing | Phase 9 |
| `release/` | Release candidate artifacts | Missing | Phase 9 |
| `repositories/` | Cloned repos for execution | Missing | Phase 4 |
| `benchmark_data/controlled_repo_spec/` | Todo specification | Missing | Phase 3 (deferred) |
| `benchmark_data/public_tests/` | Public-facing tests | Missing | Phase 6 |
| `benchmark_data/graph_specs/` | Graph specifications | Missing | Phase 6 |
| `notebooks/local/` | Local notebook adapter | Missing | Phase 8 |
| `notebooks/kaggle/` | Kaggle notebook | Missing | Phase 8 |

---

## 4. Stale Files

| File | Reason for Staleness |
|------|---------------------|
| `outer/docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md` | Superseded by project/docs/RESEARCHER_DECISIONS_DA_AC.md |
| `outer/docs/HUMAN_DECISIONS_REQUIRED.md` | All decisions resolved in Phase 2B |

---

## 5. Naming Inconsistencies

Several scenario YAML files use non-standard `blast_radius` values inconsistent with the taxonomy:

| Scenario File | Current `blast_radius` | Expected (per taxonomy) |
|---------------|----------------------|------------------------|
| `djangocms-loc-001.yaml` | `single_model_layer` | `localized` |
| `saleor-loc-001.yaml` | `single_model_and_graphql_type` | `localized` |

These should be corrected to match `localized | moderate | cross_cutting` per `docs/SCENARIO_TAXONOMY.md`.

---

## 6. Cache and Generated Files

| Path | Type | Ignored? |
|------|------|----------|
| `project/.mypy_cache/` | Generated | Yes (.gitignore present) |
| `project/.ruff_cache/` | Generated | Yes (.gitignore present) |
| `project/**/__pycache__/` | Generated | **No** — add to .gitignore |
| `project/runs/` | Generated (future) | **No** — add to .gitignore |

---

## 7. Git Status

```
Repository: project/.git
Branch: main
Last commit: e56068c (Phase 0)
Status: Working tree has uncommitted files from Phase 3 and Phase 3.5
```

Files NOT committed:
- `benchmark_data/` (29 files)
- `reports/` (8 files from Phases 3/3.5)
- `docs/` (8 architecture docs from Phase 3.5)
- Various other files

---

## 8. Remediation Plan

### Before Phase 4A begins:

1. **Copy root docs into project**
   ```powershell
   Copy-Item "..\docs\OPENCODE_EXECUTION_GUIDE.md" "docs\OPENCODE_EXECUTION_GUIDE.md"
   ```

2. **Delete stale root directories**
   ```powershell
   Remove-Item -Recurse "..\benchmark_data"
   Remove-Item "..\docs\FINAL_RESEARCH_PROTOCOL_DECISIONS.md"
   Remove-Item "..\docs\HUMAN_DECISIONS_REQUIRED.md"
   ```

3. **Update .gitignore**
   Add: `__pycache__/`, `runs/`, `*.egg-info/`, `.env`

4. **Fix scenario blast_radius values**
   - djangocms-loc-001.yaml: `single_model_layer` → `localized`
   - saleor-loc-001.yaml: `single_model_and_graphql_type` → `localized`

5. **Commit Phase 3 and Phase 3.5 work**
   ```bash
   git add -A && git commit -m "Phase 3 + Phase 3.5: repo/scenario prep, architecture audit, project map"
   ```
