# RESEARCH DECISION ARCHIVE

Append-only research decision ledger for the Stage-C selection study (D052).
This index/ledger NEVER replaces raw evidence; every claim points to exact
evidence paths/hashes. Facts, decisions, rationale, metrics, and evidence
references only - no submission-ready paper prose.

---

## Entry 1: selection-only exploratory study authorization (D052)

- **timestamp:** 2026-09-06 (before any `scientific-stagec-selection-01` model call)
- **decision ID/title:** D052 - STAGE-C-SELECTION-01 selection-only exploratory component study authorized
- **what was decided:** Run a selection-only component study isolating the Stage-C impact-selection boundary: 3 Todo smoke scenarios x 2 arms (iterative_repository_agent, impact_plan) x 5 reps = 30 cells. Each run calls `analyze_impact` exactly once; never `revise_plan`; never regeneration/repair/migration/evaluator.
- **why (1-3 concise lines):** v1.1 end-to-end result is NO-GO (30/30 attempted, 5/30 evaluator reached, 0/30 passed) but is confounded by code-generation/exact-patch/revision failures; the Agent's post-revision `predicted_actions` is not a fair initial-selection measurement. The selection-only study measures the novel Stage-C boundary cheaply (est. <= $0.25) before further executor engineering.
- **exact evidence supporting it:**
  - Pack design: `_workspace/active/STAGE_C_SELECTION_RESULTS_NOW_PACK/00_DECISION_LOCK.md`
  - Audit basis: `_workspace/active/STAGE_C_SELECTION_RESULTS_NOW_PACK/06_AUDIT_NOTE_GPT56_SOL.md`
  - v1.1 NO-GO: `reports/scientific_microstudy_v11/` (raw records), `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.md`, `reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md`
- **alternative(s) rejected + why:** Executor/regeneration rewrite REJECTED (out of scope, preserves v1.1); measuring post-revision `predicted_actions` REJECTED (can be overwritten by revision failure); end-to-end rewrite of the study REJECTED (exploratory component evidence only).
- **affected protocol/config/artifacts:** New profile `scientific-stagec-selection-01`; dedicated `BenchmarkRunner._run_selection_only`; additive `RunRecordData.selection_study`; `scripts/build_stagec_selection_results.py`; `scripts/validate_stagec_selection_prebenchmark.py`.
- **commit hash:** (filled at Phase 0 commit)
- **exact paths to raw evidence/reports:** `reports/scientific_microstudy_v11/run_records.jsonl` (v1.1 preserved); future `reports/scientific_stagec_selection_01/run_records.jsonl` (this study).
- **pre-data or post-data status:** PRE-DATA

---

## Entry 2: frozen source-universe / gold-normalization rule

- **timestamp:** 2026-09-06 (pre-data)
- **decision ID/title:** Selection source universe and gold normalization
- **what was decided:** Candidate source universe is exactly the Todo five-file set (`todo/models.py`, `todo/serializers.py`, `todo/views.py`, `todo/permissions.py`, `todo/urls.py`). Gold for evaluation is the scenario `expected_actions` normalized to source-file paths ONLY: symbol markers (`path#symbol`) stripped, migration/`tests` paths excluded, directories excluded.
- **why:** Migration directories and evaluator/test files are not part of source-selection recall (measurement contract).
- **exact evidence supporting it:** `_workspace/active/STAGE_C_SELECTION_RESULTS_NOW_PACK/01_MEASUREMENT_CONTRACT.md`; frozen Todo profile `benchmark_data/repository_profiles/todo.yaml` (`artifact_universe.llm_editable`); gold fixture `scripts/build_stagec_selection_results.py` + G1 gate.
- **alternative(s) rejected + why:** Including migrations in recall REJECTED (scored separately); including evaluator/test assets REJECTED (not candidate source).
- **affected protocol/config/artifacts:** gold-map in `scripts/build_stagec_selection_results.py`; G1 gate checks exact normalized gold.
- **commit hash:** (filled at Phase 0 commit)
- **exact paths to raw evidence/reports:** `benchmark_data/scenarios/todo-smoke-00{1,2,3}.yaml` (expected_actions); `_workspace/active/STAGE_C_SELECTION_RESULTS_NOW_PACK/07_MANIFEST_SHA256.json`.
- **pre-data or post-data status:** PRE-DATA

---

## Entry 3: frozen model/provider/output caps

- **timestamp:** 2026-09-06 (pre-data)
- **decision ID/title:** Frozen model, provider, temperature, and output caps
- **what was decided:** Model `qwen/qwen3-coder`; provider `DeepInfra` pinned through the existing OpenRouter account; fallback OFF; temperature 0.0. Agent control cap 1024; ImpactPlan planner cap 4096 (module constant). No source-edit/repair caps exist in the selection-only path.
- **why:** Same frozen model/provider as v1.1 for an apples-to-apples Stage-C comparison; role-sized caps bound cost/latency/truncation.
- **exact evidence supporting it:** `_workspace/active/STAGE_C_SELECTION_RESULTS_NOW_PACK/00_DECISION_LOCK.md`; freeze `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json` (model/provider/pricing); `src/benchmark/selection/impact_planner.py::IMPACT_PLAN_MAX_COMPLETION_TOKENS=4096`; main() role-cap forcing for the profile.
- **alternative(s) rejected + why:** Provider fallback ON REJECTED (scientific pin); cap increase REJECTED (frozen pre-data).
- **affected protocol/config/artifacts:** `seven_arm_benchmark.py` profile + role-cap block; `source_identity.json` model_identity.
- **commit hash:** (filled at Phase 0 commit)
- **exact paths to raw evidence/reports:** `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json`.
- **pre-data or post-data status:** PRE-DATA