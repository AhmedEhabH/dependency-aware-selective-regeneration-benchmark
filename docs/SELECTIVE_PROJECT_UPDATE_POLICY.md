# Selective Project Update Policy

**Date:** 2026-07-24
**Branch:** `audit/canonical-project-architecture`
**Status:** ADOPTED (chore/canonical-project-remediation)
**Purpose:** Define required workflow for future changes to minimize regeneration scope.

---

## Rationale

The project has canonical sources and generated derivatives. Currently, every change requires implicit full-bundle regeneration. A selective policy reduces engineering time and agent token usage by regenerating only affected artifacts. A selective-update ledger at `project/selective_updates/` records every change for traceability and impact measurement.

---

## Pre-Change Reading Order

Before modifying production code, benchmark data, notebooks, or deployment bundles, read:

1. `selective_updates/README.md` — ledger purpose and conventions
2. `selective_updates/CHANGE_INDEX.md` — recent changes and status
3. `selective_updates/ARTIFACT_IMPACT_MAP.md` — change-to-artifact lookup

---

## Required Workflow

### Step 1: Determine Changed Requirement
Identify the exact requirement change (defect fix, feature addition, config change, data update).

### Step 2: Identify Affected Canonical Artifacts
Map the requirement to canonical artifacts using CANONICAL_ARTIFACT_INVENTORY.md.

**Examples:**
- Bug in `runner.py` → AID-SRC-002 (`src/benchmark/execution/runner.py`)
- Config profile change → AID-SRC-003 (`project/configs/smoke.yaml`)
- Scenario addition → AID-SCI-005 (`benchmark_data/scenarios/*.yaml`)

### Step 3: Identify Generated Derivatives
Determine which generated artifacts contain copies of the changed canonical artifact:

| Canonical Change | Affected Derivatives |
|-----------------|---------------------|
| `seven_arm_benchmark.py` | `kaggle_upload/code/seven_arm_benchmark.py` |
| `src/benchmark/*.py` | `kaggle_upload/code/src/benchmark/` |
| `configs/*.yaml` | `kaggle_upload/code/configs/` |
| `benchmark_data/*.yaml` | `kaggle_upload/data/` |

### Step 4: Regenerate Only Affected Derivatives
Copy only the changed files to bundle locations. Do not rebuild entire bundle.

### Step 5: Preserve Unaffected Artifacts
Do not touch bundle files whose canonical source has not changed.

### Step 6: Verify Source-to-Derivative Checksums
For each regenerated derivative, verify SHA-256 matches the canonical source.

```bash
# Example verification
$canonical = (Get-FileHash "seven_arm_benchmark.py" -Algorithm SHA256).Hash
$bundle = (Get-FileHash "kaggle_upload/code/seven_arm_benchmark.py" -Algorithm SHA256).Hash
if ($canonical -ne $bundle) { throw "Checksum mismatch" }
```

### Step 7: Run Targeted Tests
Run only tests related to the changed component:
```bash
python -m pytest tests/unit/execution/ -v --tb=short
```

### Step 8: Run Full Gates Before Merge
```bash
ruff check src/ tests/
mypy src/
python -m pytest tests/ -v --tb=short
pip check
```

### Step 9: Create Selective-Update Record
Every merged production or deployment change must create or update exactly one record under `selective_updates/records/`. Trivial typo-only edits may skip this unless they affect operational instructions.

### Step 10: Measure Impact

| Metric | Record |
|--------|--------|
| Files changed | Count |
| Lines changed | Count |
| Tests executed | Count / total |
| Execution time | Time |
| Agent token usage | Tokens (when available) |
| Defects introduced | Count |
| Defects detected | Count |

### Step 10: Compare Selective vs Full Regeneration (When Possible)
If both selective and full regeneration were performed, compare:
- Time saved
- Token usage saved
- Defect detection rate
- Whether selective update missed any needed changes

---

## Goals

1. **Reduce engineering time** — avoid regenerating 66 source files when only 1 changed
2. **Reduce agent token usage** — fewer copy operations
3. **Verify quality preservation** — selective updates must not introduce defects that full regeneration would catch

## Caveats

- Selective regeneration does not claim quality improvement without measured evidence.
- First-time bundle creation (from scratch) is always full regeneration.
- If bundle structure changes, always do full regeneration.
