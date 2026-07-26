# SCIENTIFIC-SMOKE-V1 — Minimal Real Kaggle Scientific Smoke

**Date:** 2026-07-27
**Status:** PREPARATION COMMITTED — Audit corrections applied, Kaggle execution pending
**Branch:** experiment/scientific-smoke-v1
**Base Commit:** 414173a

---

## 1. Objective

Prepare and execute the smallest real Kaggle Scientific Smoke using:
- **Backend:** KaggleQwenBackend (Qwen2.5-Coder on Kaggle GPU)
- **Arms:** full_scope_reference (monolithic), hybrid_selective (selective), iterative_repository_agent
- **Scope:** 1 repository × 1 scenario × 3 arms × 1 execution per arm = 3 total runs
- **Budgets:** max_attempts=2, max_tokens=4096 per call, timeout=180s (bounded)
- **Evidence Tier:** scientific_smoke_v1 (non-publication engineering/scientific harness smoke)

**This is an engineering/scientific harness smoke, not a statistical experiment.**

---

## 2. Configuration

### Backend
- **Model:** Qwen2.5-Coder-7B-Instruct (qwen-lm/qwen2.5-coder/transformers/7b-instruct/1)
- **Path:** `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/7b-instruct/1` (auto-discovered)
- **GPU:** Kaggle T4/V100/A100 (sm_70+ required)

### Repository
- **ID:** `todo` (Controlled Django Todo Application)
- **Size:** Small (purpose-built synthetic)
- **URL:** https://github.com/ahmed-ehab/controlled-django-todo
- **Ref:** main
- **Snapshot:** Staged at runtime via `stage_repository_snapshot()`

### Scenario
- **ID:** `todo-loc-001`
- **Type:** Schema and field changes (add priority field to Task model)
- **Blast Radius:** Localized
- **Requirement:** Add `priority` CharField with choices HIGH/MEDIUM/LOW, default MEDIUM to Task model and TaskSerializer

### Arms (3)
| Arm ID | Strategy | Role |
|--------|----------|------|
| 1 | `monolithic` | Full-scope reference (regenerates all artifacts) |
| 2 | `selective` | Hybrid selective regeneration (dependency graph + semantic) |
| 3 | `iterative_repository_agent` | Iterative agent (plan → regen → validate → revise) |

### Budgets
- **max_attempts:** 2 (1 initial + up to 1 repair/revision)
- **max_tokens:** 4096 per model call
- **timeout_seconds:** 180 (bounded)
- **random_seed:** 42

### Output
- **Directory:** `/kaggle/working/runs/scientific_smoke_v1/`
- **Format:** JSONL + checkpoint + progress + ZIP bundle
- **Provenance:** Full write_provenance=true

---

## 3. Changes from Baseline

### Production Code Changes (minimal)

1. **seven_arm_benchmark.py** — Added `scientific-smoke-v1` profile and scenario filtering
   - Added `repository_names` and `blast_radii` fields to `ExecutionProfile` dataclass
   - Added `scientific-smoke-v1` to `PROFILES` dict with 3 strategies and filtering
   - Modified `_build_execution_plan()` to accept pre-filtered scenarios
   - Added scenario filtering logic in `main()` before execution plan

2. **configs/smoke.yaml** — Updated to scientific-smoke-v1 specification
   - profile_label: `scientific-smoke-v1`
   - strategies: monolithic, selective, iterative_repository_agent
   - repositories: todo (real URL)
   - scenario_selection: todo + localized + count: 1
   - execution: max_iterations: 2, evidence_tier: scientific_smoke_v1
   - output: output_dir: runs/scientific_smoke_v1

3. **kaggle_upload/code/configs/smoke.yaml** — Synced with configs/smoke.yaml

4. **kaggle_upload/code/seven_arm_benchmark.py** — Copied from project root

5. **kaggle_upload/notebooks/seven_arm_benchmark.ipynb** — Updated to use scientific-smoke-v1 profile
   - Markdown description updated
   - Execution cells use `--profile scientific-smoke-v1`
   - Notes updated

### No Production Logic Changes
- Strategy implementations unchanged
- Pipeline, budgets, repair, validation unchanged
- Backends unchanged
- Evaluation/metrics unchanged
- Ground truth boundary preserved

---

## 4. Ground Truth Boundary Verification

✅ **ArtifactUniverse** comes from active repository snapshot (`discover_eligible_artifacts()` on staged snapshot)
✅ **DependencyGraph** built from repository profile architecture data only (no `expected_affected_artifacts`)
✅ **Ground Truth paths** NOT sent to Qwen — only acceptance criteria and artifact list
✅ **Ground Truth** used ONLY during evaluation after prediction (`GroundTruthComparator`)

---

## 5. Required Smoke Evidence (per arm)

For each of the 3 arms, the following must be saved:

| Evidence | Description |
|----------|-------------|
| RunRecord | Final RunRecord with all fields |
| Status | succeeded / failed / timed_out |
| Validation Result | functional_validation_passed (true/false/null) |
| Attempt Count | 1 or 2 (max_attempts=2) |
| Selection Calls & Tokens | selection_model_calls, selection_total_tokens |
| Regeneration Calls & Tokens | regeneration_model_calls, regeneration_total_tokens |
| Total Workflow Calls & Tokens | total_workflow_model_calls, total_workflow_tokens |
| Workflow Duration | total_workflow_duration_seconds |
| Selected/Regenerated/Preserved Counts | selected_artifact_count, regenerated_artifact_count, preserved_artifact_count |
| Failure History | All failure records with kind, message, stage |

### Also Saved (once per experiment)
- Commit hash (set after preparation commit)
- Kaggle notebook/kernel identifier
- Qwen model identifier/path (qwen2.5-coder)
- Repository ID (todo)
- Scenario ID (todo-loc-001)
- Exact conditions (profile, budgets, seed)
- Exact budgets (max_attempts=2, max_tokens=4096)
- Generated report (benchmark_summary.json + report.json + progress.json)
- Machine-readable manifest (checkpoint.json, source_identity.json)

---

## 6. Artifacts Location

**Dedicated Path:** `/kaggle/working/runs/scientific_smoke_v1/`

Will contain (after Kaggle run):
- `run_records.jsonl` — All 3 RunRecords
- `checkpoint.json` — Final checkpoint state
- `progress.json` — Progress tracking
- `report.json` — Rebuilt experiment report
- `benchmark_summary.json` — Per-arm summary
- `source_identity.json` — Provenance
- `benchmark-results.zip` — Complete bundle

---

## 7. Kaggle Datasets Required

| Dataset | Purpose |
|---------|---------|
| `ahmedehabh/dependency-aware-selective-regeneration-code` | Source code (src/, seven_arm_benchmark.py, configs/, pyproject.toml, requirements-kaggle.txt) |
| `ahmedehabh/dependency-aware-selective-regeneration-data` | Scenarios, manifests, repository profiles |
| `qwen-lm/qwen2.5-coder/transformers/7b-instruct/1` | Qwen2.5-Coder-7B-Instruct model weights |

---

## 8. Launch Readiness Checklist

- [x] Scientific-smoke-v1 profile defined in code
- [x] Scenario filtering implemented (todo + localized)
- [x] 3 target arms configured (monolithic, selective, iterative_repository_agent)
- [x] max_attempts=2, max_tokens=4096
- [x] Kaggle notebook updated to use scientific-smoke-v1
- [x] Configs synced to kaggle_upload/
- [x] kaggle_upload/code/seven_arm_benchmark.py synced
- [x] All local tests pass (1018 passed, 5 skipped)
- [x] Dry-run verified locally with scientific-smoke-v1 profile
- [x] Ground truth boundary verified
- [x] Documentation updated

---

## 9. Execution on Kaggle

```bash
# In Kaggle notebook, run setup cell, then exec-cell (3x for 3 arms)
# Or run continuous-smoke-cell once for all 3 arms
```

Each exec-cell runs `--max-runs 1 --auto-resume-hf`, advancing by 1 arm per session.

---

## 10. Pilot Authorization Status

**PILOT REMAINS UNAUTHORIZED** — Only after successful Scientific Smoke audit and stable tag.

---

## 11. Related Records

- SU-0011-iterative-repository-agent.md (8th arm implementation)
- SU-0010A-minimal-shared-regeneration.md (shared regeneration path)
- SU-0010B1B-ground-truth-free-dependency-graph.md (GT-free graph)
- OPENROUTER-BACKEND.md (optional local backend, NOT used for this smoke)

---

**PREPARATION COMMITTED** — Audit corrections applied, Kaggle execution pending.

**KAGGLE_SCIENTIFIC_SMOKE_V1_AUDIT_CORRECTED**