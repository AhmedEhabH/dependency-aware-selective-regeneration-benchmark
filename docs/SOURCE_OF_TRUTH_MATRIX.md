# Source of Truth Matrix

**Audit Date:** 2026-07-24
**Branch:** `audit/canonical-project-architecture`
**Purpose:** Exhaustive designation of canonical sources, with classification of every duplicate path.

---

## Classification Legend

| Classification | Meaning |
|---------------|---------|
| **CANONICAL** | The authoritative copy. All other copies are derivatives. |
| **GENERATED_DERIVATIVE** | Machine-generated copy of a canonical source. Must be regenerable. |
| **EXTERNAL_IMMUTABLE_INPUT** | External data, never modified, outside Git. |
| **RUNTIME_OUTPUT** | Non-deterministic output produced during execution. |
| **STALE_DUPLICATE** | Previously-generated derivative that no longer matches its canonical source. |
| **TEMPORARY** | Should not persist. Safe to delete after verification. |
| **UNKNOWN_REQUIRES_DECISION** | Duplicate with uncertain ownership or purpose. Requires researcher/engineering decision. |

---

## Sources of Truth

### Project Source

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Source code | **CANONICAL** | `project/src/benchmark/` | 66 .py files, all Git-tracked. Package root. |
| CLI entry point | **CANONICAL** | `project/seven_arm_benchmark.py` | Root-level script. Git-tracked. |
| Package config | **CANONICAL** | `project/pyproject.toml` | Build/lint/test configuration. Git-tracked. |

### Benchmark Data

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Scenarios (24) | **CANONICAL** | `project/benchmark_data/scenarios/*.yaml` | Git-tracked. Contains expected actions (ground truth). |
| Manifests (2) | **CANONICAL** | `project/benchmark_data/manifests/` | Git-tracked. |
| Repository profiles (3) | **CANONICAL** | `project/benchmark_data/repository_profiles/` | Git-tracked. |

### Notebooks

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Benchmark notebook | **CANONICAL** | `project/notebooks/seven_arm_benchmark.ipynb` | Git-tracked. |
| Inner bundle copy | **GENERATED_DERIVATIVE** | `project/kaggle_upload/notebooks/seven_arm_benchmark.ipynb` | SHA-256 matches canonical. |
| Outer bundle copy | **STALE_DUPLICATE** | `<parent>/kaggle_upload/notebooks/seven_arm_benchmark.ipynb` | SHA-256 differs from canonical. |

### Kaggle Code Bundle

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Inner bundle | **GENERATED_DERIVATIVE** | `project/kaggle_upload/code/` | Source files match canonical (66/66). Contains `.git/`, caches, egg-info — should not. |
| Outer bundle | **STALE_DUPLICATE** | `<parent>/kaggle_upload/code/` | Does NOT contain `.git/` or caches, but `seven_arm_benchmark.py` and `hf_sync.py` content-differ from canonical. |

### Kaggle Data Bundle

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Inner bundle | **STALE_DUPLICATE** / **UNKNOWN** | `project/kaggle_upload/data/` | ***EMPTY*** — no data files present at all. |
| Outer bundle | **GENERATED_DERIVATIVE** (populated) | `<parent>/kaggle_upload/data/` | Contains all 29 data YAML files, all matching canonical SHA-256. `UNKNOWN_REQUIRES_DECISION` — the populated data bundle lives outside Git while the Git-tracked one is empty. |

### Execution Configurations

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Smoke profile | **CANONICAL** | `project/configs/smoke.yaml` | Git-tracked. |
| Pilot profile | **CANONICAL** | `project/configs/pilot.yaml` | Git-tracked. |
| Research profile | **CANONICAL** | `project/configs/research.yaml` | Git-tracked. |
| Inner bundle configs | **GENERATED_DERIVATIVE** | `project/kaggle_upload/code/configs/` | Only CRLF differences from canonical. |
| Outer bundle configs | **STALE_DUPLICATE** | `<parent>/kaggle_upload/code/configs/` | Only CRLF differences from canonical. |

### State Files

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| System state | **CANONICAL** | `project/SYSTEM_STATE.md` | Git-tracked. |
| TODO list | **CANONICAL** | `project/TODO.md` | Git-tracked. |
| Decision log | **CANONICAL** | `project/DECISION_LOG.md` | Git-tracked. |
| Protocol version | **CANONICAL** | `project/PROTOCOL_VERSION.md` | Git-tracked. |

### Results

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Local runs | **RUNTIME_OUTPUT** | `project/runs/` | Gitignored. Currently does not exist. |
| Results ZIP | **RUNTIME_OUTPUT** | `project/benchmark-results.zip` | Git untracked. Origin unknown. |
| Kaggle runs | **RUNTIME_OUTPUT** | `/kaggle/working/runs/` | Kaggle only. |

### Experiment Checkpoints

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Local checkpoint | **RUNTIME_OUTPUT** | `project/_auto_resume_temp/` | Git-tracked (empty dir structure). Used for auto-resume tests. |
| HF remote recovery | **RUNTIME_OUTPUT** | Remote: HuggingFace Dataset | Not examined. |

### Frozen Protocol

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Final Research Protocol | **CANONICAL** | `project/docs/FINAL_RESEARCH_PROTOCOL.md` | Frozen. SHA-256 verified. |
| Companion docs (7) | **CANONICAL** | `project/docs/` | Frozen. SHA-256 verified. |
| Phase 3.5+ architecture docs | **CANONICAL** | `project/docs/` | Not frozen but authoritative. |

### External Inputs

| Aspect | Classification | Path | Notes |
|--------|---------------|------|-------|
| Paper PDF | **EXTERNAL_IMMUTABLE_INPUT** | `<parent>/inputs/paper/MSc_Proposal_*.pdf` | Outside Git. Immutable. |
| Paper LaTeX | **EXTERNAL_IMMUTABLE_INPUT** | `<parent>/inputs/paper/MSc_Proposal_*.tex` | Outside Git. Immutable. |

### Duplicate Path Resolution

| Path | Classification | Resolution |
|------|---------------|------------|
| `<parent>/kaggle_upload/` (full) | **STALE_DUPLICATE** | Should be deleted once inner bundle is fixed (data populated, caches cleaned). |
| `<parent>/kaggle_upload/code/` | **STALE_DUPLICATE** | Content differs. Delete after ensuring inner bundle is correct. |
| `<parent>/kaggle_upload/data/` | **UNKNOWN_REQUIRES_DECISION** | Data content is correct but lives outside Git. Should be migrated to inner bundle. |
| `<parent>/kaggle_upload/notebooks/` | **STALE_DUPLICATE** | Hash differs. Delete after verifying inner bundle. |
| `<parent>/docs/` (2 files) | **GENERATED_DERIVATIVE** | Reference copies outside Git. Phase 3.6 was supposed to copy them in, which was done. These are legacy duplicates. |
| `project/kaggle_upload/data/` (empty) | **STALE_DUPLICATE** | Currently empty. Must be populated with actual data. |
| `project/kaggle_upload/code/.git/` | **TEMPORARY** (incorrectly bundled) | Full Git repo inside deployment bundle. Must be removed. |
| `project/kaggle_upload/code/__pycache__/` | **TEMPORARY** (incorrectly bundled) | Caches inside deployment bundle. Must be excluded. |
| `project/kaggle_upload/code/.mypy_cache/` | **TEMPORARY** (incorrectly bundled) | Caches inside deployment bundle. Must be excluded. |
| `project/kaggle_upload/code/.pytest_cache/` | **TEMPORARY** (incorrectly bundled) | Caches inside deployment bundle. Must be excluded. |
| `project/kaggle_upload/code/.ruff_cache/` | **TEMPORARY** (incorrectly bundled) | Caches inside deployment bundle. Must be excluded. |
| `project/kaggle_upload/code/src/*.egg-info/` | **TEMPORARY** (incorrectly bundled) | Package metadata inside deployment bundle. Must be excluded. |
| `project/kaggle_upload/code/benchmark_data/` (empty) | **TEMPORARY** | Empty placeholder. Data should be in `data/` bundle, not `code/`. |
