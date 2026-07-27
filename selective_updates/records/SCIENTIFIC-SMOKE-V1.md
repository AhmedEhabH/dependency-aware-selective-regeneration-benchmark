# SCIENTIFIC-SMOKE-V1 — Minimal Real Kaggle Scientific Smoke

**Date:** 2026-07-27
**Status:** FAILED — fixes applied, retry1 deployment pinned (not yet launched)
**Branch:** experiment/scientific-smoke-v1
**Base Commit (original):** 414173a
**First real execution:** exp-20260726-231536
**First real result:** FAILED
**Fixes committed at:** 76ef349bf9cef14ebae378d8d51757bfa5cc78ad
**Retry commit:** 76ef349bf9cef14ebae378d8d51757bfa5cc78ad
**Retry deployed build ID:** 76ef349
**Retry output path:** /kaggle/working/runs/scientific_smoke_v1_retry1

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

## 1a. First Execution Result (exp-20260726-231536) — FAILED

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| A. Report finalization crash | `seven_arm_benchmark.py:45` imports `datetime, timezone` but line 1906 uses `datetime.now(UTC)` without importing `UTC` | Added `UTC` to import line |
| B. Checkpoint scenario_ids mismatch | Line 1528 builds `selected_scenario_ids` from `all_scenarios` (unfiltered) instead of `selected_scenarios` | Changed to use filtered `selected_scenarios` |
| C. Monolithic/selective no-op success | `pipeline.py:_make_runner()` never sets `enable_regeneration=True` — runner takes impact-only path, succeeds with `model_calls=0, regenerated=0, validation=None` | Added `enable_regeneration` to `PipelineConfig`, propagated to `RunnerConfig`, enabled for approved strategies |
| D. Truncated iterative JSON | `kaggle_qwen_backend.py:169` hardcodes `finish_reason="stop"` regardless of actual EOS. 196-completion-token output ends mid-decision | Dynamic EOS detection; compact JSON prompt instruction |
| E. Failed-run metrics discarded | `runner.py:_run_iterative_flow()` accumulated tokens AFTER error check — failed parse discarded usage | Moved accumulation before error check |
| F. Progress stuck at "running" | `rebuild_experiment_reports()` runs BEFORE checkpoint update to "completed" | Updated checkpoint before report rebuild |

### Observed evidence
- **exp-20260726-231536**
- 3 runs attempted
- 2 reported success but **scientifically invalid** (zero model calls, zero regenerated artifacts, no validation)
- Iterative agent failed from truncated JSON
- Report finalization raised `NameError: name 'UTC' is not defined`
- Checkpoint stored `scenario_ids=["djangocms-cross-007"]` instead of `["todo-loc-001"]`
- Failed iterative run recorded `selection_model_calls=0, total_workflow_tokens=0` despite 695 actual tokens
- Progress ended with `completion_status="running"` despite all runs complete

### Retry policy
- New experiment ID required
- New output directory: `/kaggle/working/runs/scientific_smoke_v1_retry1`
- Must not resume or overwrite exp-20260726-231536
- Same repository, scenario, model, 3 arms, max_attempts=2, timeout=180, token budget 4096

### Audit 2: Retry-path propagation (2026-07-27)

A second audit before committing the first-round fixes discovered 2 additional
propagation gaps that would cause the retry to fail:

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| G. No validation command propagated | `PipelineConfig` had no `validation_command` field. `_make_runner()` never passed it to `RunnerConfig`. The canonical test command `test_discovery: "python -m pytest"` existed in `benchmark_data/manifests/repositories.yaml` for `todo` but was never loaded or forwarded. | Added `validation_command` + `validation_timeout` to `PipelineConfig`. `_make_runner()` passes both to `RunnerConfig`. `main()` loads manifests via `RepositoryLoader`, extracts `test_discovery` for each repo, and passes through. Pre-flight check fails closed if `enable_regeneration=True` with no `validation_command`. |
| H. No workflow token budget | `PipelineConfig.max_tokens_per_run` was never set. No CLI `--max-tokens` argument existed. The runner's `BudgetManager` received `max_tokens=0` (unlimited). | Added `--max-tokens` CLI arg (default 0 = unlimited, backward compat). Added `max_tokens` parameter to `_run_single_scenario_strategy()` and `run_arm()`. Notebook cells pin `--max-tokens 4096`. |

### Changes made (round 2)

| File | Change |
|------|--------|
| `src/benchmark/execution/pipeline.py` | Added `validation_command`, `validation_timeout` to `PipelineConfig`; `_make_runner()` passes both |
| `seven_arm_benchmark.py` | Added `--max-tokens`, `--validation-command` CLI args; manifest loading via `RepositoryLoader`; pre-flight check for missing validation_command; added `shlex` import |
| `notebooks/seven_arm_benchmark.ipynb` | Pinned `--max-tokens 4096` in exec-cell and continuous-smoke-cell |
| `kaggle_upload/notebooks/seven_arm_benchmark.ipynb` | Synced |
| `tests/integration/test_scientific_smoke_v1_fixes.py` | 21 tests: positive monolithic end-to-end, missing-validation negative, selective positive, finish_reason dynamic detection, EOS detection, max_tokens propagation, retry readiness (3 arms), pipeline preflight |

### Validation (round 2)
- 21/21 targeted tests passed
- 1048/1048 full-suite passed (5 skipped, same as baseline)
- Ruff: 0 errors in changed files (line-length warnings pre-existing)
- Mypy strict: 0 new errors (8 pre-existing in `seven_arm_benchmark.py`)
- Bundle: 107 files, 606,629 bytes, verified OK
- Git diff --check: no whitespace errors

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
- **Directory (Retry1):** `/kaggle/working/runs/scientific_smoke_v1_retry1/`
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

### Original deployment (exp-20260726-231536, failed)

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

### Retry1 deployment (commit 76ef349)

- [x] All 6 root-cause failures fixed in production code
- [x] Token budget and validation command propagation gaps closed
- [x] Prompt-aware workflow token budget enforced
- [x] Unlimited max_tokens=0 sends 4096 to backend (not 0)
- [x] Full test suite: 1058 passed, 5 skipped
- [x] Notebooks updated with Retry1 identity (source commit, build ID, output dir)
- [x] Both notebooks (canonical + kaggle_upload) are structurally identical
- [x] Retry1 output directory: `/kaggle/working/runs/scientific_smoke_v1_retry1` (fresh, empty)
- [x] HF auto-resume will not collide: different source commit + different output directory
- [x] no `--new-experiment` required (isolation guaranteed by new output dir and different source commit)
- [x] No OpenRouter arguments in any notebook cell
- [x] No Pilot or Research profile referenced
- [x] Partial cell contains `--max-runs 1`
- [x] Continuous cell contains no `--max-runs`
- [x] Documentation updated truthfully
- [x] Retry1 has not been launched
- [x] Pilot remains unauthorized
- [x] No stable tag exists

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

**RETRY1 DEPLOYMENT PINNED** — commit 76ef349, build ID 76ef349, output `/kaggle/working/runs/scientific_smoke_v1_retry1`. Retry1 is not yet launched.

**KAGGLE_SCIENTIFIC_SMOKE_RETRY1_DEPLOYMENT_PINNED**