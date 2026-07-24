# Proposed Canonical Project Structure

**Date:** 2026-07-24
**Branch:** `audit/canonical-project-architecture`
**Status:** PROPOSED (not yet implemented)
**Purpose:** Minimally invasive target tree to eliminate duplicates and normalize bundle generation.

---

## Principles

1. **Single Git root** = `project/`. No other directory is a Git root.
2. **All canonical sources** live inside `project/`.
3. **Generated derivatives** live inside `project/` and are `GENERATED_DERIVATIVE` classified.
4. **External immutable inputs** remain outside `project/`.
5. **No caches, `.git/`, or `egg-info/`** in deployment bundles.
6. **Minimize movement** — avoid restructuring files that are already correct.

---

## Proposed Target Tree

```
project/                          # Single Git root (UNCHANGED)
├── .git/                         # Git repository (UNCHANGED)
├── .gitignore                    # UNCHANGED
├── .gitattributes                # UNCHANGED
├── environment.yml               # UNCHANGED
├── requirements-dev.txt          # UNCHANGED
├── requirements-kaggle.txt       # UNCHANGED
├── requirements-lock.txt         # UNCHANGED
├── pyproject.toml                # UNCHANGED
├── LICENSE                       # UNCHANGED
├── README.md                     # UNCHANGED
├── PROTOCOL_VERSION.md           # UNCHANGED
├── SYSTEM_STATE.md               # UNCHANGED
├── TODO.md                       # UNCHANGED
├── DECISION_LOG.md               # UNCHANGED
├── seven_arm_benchmark.py        # UNCHANGED (CANONICAL)
│
├── docs/                         # UNCHANGED (30 files)
│
├── src/benchmark/                # UNCHANGED (66 .py files)
│
├── tests/                        # UNCHANGED (44 .py files)
│
├── benchmark_data/               # UNCHANGED (29 YAML files)
│   ├── manifests/
│   ├── repository_profiles/
│   └── scenarios/
│
├── configs/                      # UNCHANGED (3 YAML files)
│   ├── smoke.yaml
│   ├── pilot.yaml
│   └── research.yaml
│
├── notebooks/                    # UNCHANGED
│   └── seven_arm_benchmark.ipynb
│
├── scripts/                      # POPULATE with build script
│   └── build_upload_bundle.py    # NEW — automated bundle generation
│
├── reports/                      # UNCHANGED (30 files + audit additions)
│
├── runs/                         # UNCHANGED (gitignored, may not exist)
│
├── kaggle_upload/                # CLEANED (generated derivative)
│   ├── code/                     # CLEANED — no .git/, no caches, no egg-info
│   │   ├── seven_arm_benchmark.py
│   │   ├── pyproject.toml
│   │   ├── requirements-kaggle.txt
│   │   ├── configs/
│   │   └── src/benchmark/        # (source only, no pycache)
│   ├── data/                     # POPULATED — actual YAML files
│   │   ├── manifests/
│   │   ├── repository_profiles/
│   │   └── scenarios/
│   └── notebooks/
│       └── seven_arm_benchmark.ipynb
│
└── _auto_resume_temp/            # GITIGNORE — generate at test time
```

---

## Proposed Moves and Deletions

### Move 1: Delete outer kaggle_upload/

| Field | Value |
|-------|-------|
| Source path | `<parent>/kaggle_upload/` |
| Target path | Delete |
| Reason | Stale duplicate. Inner bundle is the canonical derivative. |
| Affected references | None (no code references outer bundle) |
| Git impact | None (outside Git) |
| Kaggle impact | None (Kaggle uses inner bundle) |
| Rollback plan | Regenerate from canonical if needed |

### Move 2: Delete outer docs/ reference copies

| Field | Value |
|-------|-------|
| Source path | `<parent>/docs/MASTER_IMPLEMENTATION_PLAN.md` |
| Target path | Delete |
| Reason | Already copied to `project/docs/` |
| Affected references | None |
| Git impact | None (outside Git) |
| Kaggle impact | None |
| Rollback plan | Copy from `project/docs/` |

### Move 3: Populate inner kaggle_upload/data/

| Field | Value |
|-------|-------|
| Source path | `project/benchmark_data/` |
| Target path | `project/kaggle_upload/data/` |
| Reason | Inner data bundle is empty; must contain data for Kaggle deployment |
| Affected references | None (kaggle_upload is a build artifact) |
| Git impact | Tracked change (new files in tracked dir) |
| Kaggle impact | Required — without this, Kaggle execution fails |
| Rollback plan | Revert commit |

### Move 4: Remove .git/ from bundle

| Field | Value |
|-------|-------|
| Source path | `project/kaggle_upload/code/.git/` |
| Target path | Delete |
| Reason | Should not be in deployment bundle |
| Affected references | None |
| Git impact | Tracked deletion |
| Kaggle impact | None (ignored anyway) |
| Rollback plan | Revert commit |

### Move 5: Remove caches from bundle

| Field | Value |
|-------|-------|
| Source paths | `project/kaggle_upload/code/**/__pycache__/`, `project/kaggle_upload/code/.mypy_cache/`, `project/kaggle_upload/code/.pytest_cache/`, `project/kaggle_upload/code/.ruff_cache/`, `project/kaggle_upload/code/src/*.egg-info/` |
| Target path | Delete |
| Reason | Should not be in deployment bundle |
| Affected references | None |
| Git impact | Tracked changes (files to remove from tracking) |
| Kaggle impact | None |
| Rollback plan | Revert commit |

### Move 6: Implement bundle build script

| Field | Value |
|-------|-------|
| Source path | N/A (new file) |
| Target path | `project/scripts/build_upload_bundle.py` |
| Reason | Automate bundle generation to prevent future drift |
| Affected references | None |
| Git impact | New tracked file |
| Kaggle impact | Indirect — ensures correct bundles |
| Rollback plan | Delete file |

### Move 7: Add _auto_resume_temp/ to .gitignore

| Field | Value |
|-------|-------|
| Source path | `project/_auto_resume_temp/` |
| Target path | No change (keep), but add to `.gitignore` |
| Reason | Temp test fixtures should not be tracked |
| Affected references | `.gitignore` |
| Git impact | Future will ignore; current tracked files need `git rm --cached` |
| Kaggle impact | None |
| Rollback plan | Revert .gitignore change |

### Move 8: Add benchmark-results.zip to .gitignore

| Field | Value |
|-------|-------|
| Source path | `project/benchmark-results.zip` |
| Target path | No change (keep), but add to `.gitignore` |
| Reason | Generated output should not be accidentally committed |
| Affected references | `.gitignore` |
| Git impact | Future will ignore |
| Kaggle impact | None |
| Rollback plan | Revert .gitignore change |

---

## What Must NOT Change

- `project/src/benchmark/` — all source files are correct
- `project/benchmark_data/` — all data files are correct
- `project/docs/` — all documentation is correct
- `project/tests/` — all tests are correct
- `project/configs/` — all configs are correct
- `project/notebooks/` — notebook is correct
- `project/reports/` — reports are correct
- `project/pyproject.toml`, `environment.yml`, requirements files — correct
- `<parent>/inputs/` — immutable, must stay outside Git
