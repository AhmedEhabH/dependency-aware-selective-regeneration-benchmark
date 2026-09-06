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
- **commit hash:** `a89f13e`
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
- **commit hash:** `a89f13e`
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
- **commit hash:** `a89f13e`
- **exact paths to raw evidence/reports:** `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json`.
- **pre-data or post-data status:** PRE-DATA
---

## Entry 4: six Pre-Benchmark gate outcome

- **timestamp:** 2026-09-06 (post-gates, pre-30-run)
- **decision ID/title:** Six Pre-Benchmark gates G1-G6
- **what was decided:** All six gates required before the 30-run study.
- **why:** Frozen protocol (file `03_TESTS_AND_SIX_GATES.md`) requires exactly six gates, then Audit, then full suite once.
- **exact evidence supporting it:**
  - Gate report: `reports/STAGEC_SELECTION_01_PREBENCHMARK_VALIDATION.md`
  - G1 dataset (3 smoke IDs, exact 5-file universe, normalized gold audited): PASS
  - G2 prompt (no expected_actions/evaluator/gold in Agent or planner prompt): PASS
  - G3 pipeline smoke (selection -> prediction -> persistence -> metrics): PASS
  - G4 dry run (30 unique records, 15/15 arms, 10/scenario, reps 1..5 x6, 0 calls / 0 tokens): PASS
  - G5 integration (real NON-STUDY probe per arm -> valid terminal selection, INITIAL prediction captured, tokens > 0): PASS
  - G6 metric verification (synthetic precision/recall/F1/FNR/full-recall/write-set exact): PASS
- **alternative(s) rejected + why:** A seventh gate REJECTED (file 03: "No seventh gate"). Skipping G5's real probe REJECTED (integration requires a genuine non-study initial-selection call).
- **affected protocol/config/artifacts:** validator script `scripts/validate_stagec_selection_prebenchmark.py`; probe outputs under `reports/stagec_selection_01_probes/`.
- **commit hash:** (recorded with the finalization commit)
- **exact paths to raw evidence/reports:** gate report + probe `run_records.jsonl` under `reports/stagec_selection_01_probes/`.
- **pre-data or post-data status:** POST-GATES / PRE-30-RUN

---

## Entry 5: independent Audit outcome

- **timestamp:** 2026-09-06 (post-gates, pre-30-run)
- **decision ID/title:** Independent Audit
- **what was decided:** Independent audit of design adherence, gold isolation, immutability of INITIAL predictions, frozen caps, topology, and scope control.
- **why:** Frozen protocol requires an independent audit after the six gates and before the 30-run study.
- **exact evidence supporting it:** `reports/STAGEC_SELECTION_01_AUDIT.md` (16-item checklist, all PASS).
- **alternative(s) rejected + why:** None - audit is a mandated gate.
- **affected protocol/config/artifacts:** audit report only (no code change).
- **commit hash:** (recorded with the finalization commit)
- **exact paths to raw evidence/reports:** `reports/STAGEC_SELECTION_01_AUDIT.md`.
- **pre-data or post-data status:** POST-AUDIT / PRE-30-RUN

---

## Entry 6: 30-run selection-study result summary

- **timestamp:** 2026-09-06 (post-30-run)
- **decision ID/title:** 30-run selection-only result (EXPLORATORY COMPONENT STUDY)
- **what was decided:** Ran all 30 selection cells (3 scenarios x 2 arms x 5 reps) on qwen/qwen3-coder @ DeepInfra; measured initial-selection precision/recall/F1/FNR/full-recall against hidden normalized gold.
- **why:** The study is the frozen exploratory measurement of the Stage-C impact-selection boundary motivated by the v1.1 executor NO-GO.
- **exact evidence supporting it:**
  - Raw records (30): `reports/scientific_stagec_selection_01/run_records.jsonl` (SHA-256 `da815cd5bbca21ac6b189b5395c28beb403625bd6d30c72e1598ef6575ee96ff`), experiment `exp-20260906-225222`
  - Result CSV: `reports/STAGEC_SELECTION_01_RESULTS.csv` (SHA-256 `f95c1badb3b7590a8d2afd75fc7498b52c33114b68707f05157d159695692956`)
  - Result tables/decision: `reports/STAGEC_SELECTION_01_RESULTS.md`, `reports/STAGEC_SELECTION_01_DECISION.md`
  - Frozen gold: `scripts/build_stagec_selection_results.py` (normalized), verified by gate G1
  - Result: 30/30 attempted, 30/30 valid finals, **full recall 15/15 per arm**, precision/recall/F1 1.000, FNR 0.000 per arm; exact API cost `$0.052696`
- **alternative(s) rejected + why:** Rerunning any valid unfavorable result REJECTED (frozen protocol); union-gold aggregation REJECTED (per-run metrics use each run's own scenario gold).
- **affected protocol/config/artifacts:** none (study is terminal).
- **commit hash:** (recorded with the finalization commit)
- **exact paths to raw evidence/reports:** as listed above.
- **pre-data or post-data status:** POST-DATA

---

## Entry 7: final interpretation + next-action decision

- **timestamp:** 2026-09-06 (post-data)
- **decision ID/title:** Final interpretation of the selection-only study
- **what was decided:** Interpret the result as EXPLORATORY COMPONENT EVIDENCE: both arms' INITIAL selection perfectly identifies the hidden gold source set (15/15 full recall each) on the same three Todo smoke scenarios that produced the v1.1 end-to-end NO-GO (0/30 functional passes). Therefore the v1.1 end-to-end failures are not attributable to initial impact selection; they sit downstream in code-generation/exact-patch/revision/validation.
- **why:** The selection-only component evidence isolates the Stage-C boundary that the end-to-end result confounds; it refines where executor engineering should focus next.
- **exact evidence supporting it:** Entry 6 evidence + v1.1 raw records (`reports/scientific_microstudy_v11/run_records.jsonl`) + `reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md` (NO-GO).
- **alternative(s) rejected + why:** Claiming end-to-end correctness/efficiency from selection recall REJECTED (no functional validation ran in this study); claiming selection superiority REJECTED (both arms equal on these smoke scenarios; exploratory only, no confirmatory threshold).
- **affected protocol/config/artifacts:** none.
- **commit hash:** (recorded with the finalization commit)
- **exact paths to raw evidence/reports:** as listed in Entry 6.
- **pre-data or post-data status:** POST-DATA
- **NEXT_ACTION:** archive + evidence tag `stagec-selection-exploratory-01` + LIGHT zip; no executor change in this study; a future held-out/multi-repo preregistered study may examine selection confidence/precision beyond these three smoke scenarios.

---

## Entry 8: held-out challenge-01 freeze + authorization (D053)

- **timestamp:** 2026-09-07 (before any `scientific-stagec-heldout-01` model call)
- **decision ID/title:** D053 - STAGE-C-HELDOUT-CHALLENGE-01 frozen held-out selection challenge authorized
- **what was decided:** The 3-smoke selection study hit a 100% ceiling in both arms (15/15 full recall each, P/R/F1 1.0). This is a frozen follow-up held-out challenge: 6 new user-level Todo scenarios x 2 arms x 5 reps = 60 selection cells, selection-only, same qwen/qwen3-coder @ pinned DeepInfra, fallback OFF, temperature 0, Agent cap 1024 / ImpactPlan cap 4096, no executor work. Visible requirements contain no explicit source-file names.
- **why (1-3 concise lines):** The prior ceiling proves capability but does not discriminate selection quality; held-out user-level requirements without visible file names are harder and remove the visible-requirement leakage that made the smoke scenarios trivial.
- **exact evidence supporting it:**
  - Pack design/freeze: `_workspace/active/STAGE_C_HELDOUT_CHALLENGE_01_PACK/00_DECISION_LOCK.md` + `05_EXECUTE_END_TO_END.md` + `07_MANIFEST_SHA256.json` (all 13 file hashes verified against the pack before copy)
  - Frozen scenarios: `benchmark_data/scenarios/todo-heldout-001..006.yaml` (SHA-256 byte-identical to pack hash list: `5f8a1953…`, `794c93fa…`, `5ea3d587…`, `68f9ca80…`, `a2913614…`, `d210a1d4…`)
  - Prior ceiling: `reports/STAGEC_SELECTION_01_RESULTS.md` (Agent 15/15 + ImpactPlan 15/15 full recall)
- **alternative(s) rejected + why:** Executor/regeneration work REJECTED (out of scope; v1.1 NO-GO preserved); scenario/prompt/cap tuning REJECTED (no post-hoc tuning); rerunning valid unfavorable outcomes REJECTED (frozen protocol).
- **affected protocol/config/artifacts:** New profile `scientific-stagec-heldout-01`; `scripts/build_stagec_heldout_results.py`; `scripts/validate_stagec_heldout_prebenchmark.py`; six scenario YAMLs copied frozen.
- **commit hash:** (recorded with the Phase-0 freeze commit)
- **exact paths to raw evidence/reports:** future `reports/scientific_stagec_heldout_01/run_records.jsonl` (this study); prior D052 records at `reports/scientific_stagec_selection_01/` preserved.
- **pre-data or post-data status:** PRE-DATA
