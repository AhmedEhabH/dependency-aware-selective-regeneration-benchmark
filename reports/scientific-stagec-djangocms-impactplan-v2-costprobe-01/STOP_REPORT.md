# STOP REPORT — djangoCMS ImpactPlan-v2 SPARSE COST/SMOKE PROBE

**PROBE_ID:** `scientific-stagec-djangocms-impactplan-v2-costprobe-01`
**Date (UTC):** 2026-09-08
**Type:** POST-HOC / EXPLORATORY / ONE-SCENARIO cost/smoke probe — **exactly ONE scientific v2 run.**
**Closure type:** REPORTING / EVIDENCE / DOCUMENTATION closure. ONE scientific v2 call; ZERO study cells; primary and 8192/16K evidence unchanged.

---

## 1. Execution Identity

- Implementation/OpenCode model: `openrouter/deepseek/deepseek-v4-flash-0731` (DEFAULT variant).
- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0, selection-only.
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD at closure start: `07c975e6a9b58725b18042bb5b0d3102c2c1b104`
- Remote HEAD: `07c975e6a9b58725b18042bb5b0d3102c2c1b104` (parity YES at closure start)

## 2. Why I Am Stopping

**STOP FOR GPT-5.6 SOL REVIEW.** The single v2 cost/smoke probe on
`djangocms-external-validity-004` at the ORIGINAL 4096 completion cap
completed **technically valid**: `finish_reason=stop`, `completion_tokens=1107`,
schema-valid, no truncation, no invalid/duplicate/conflicting ids, exactly 144
decoded candidate decisions (7 explicit + 137 deterministic PRESERVE).
`COST_LOCK=PASS_FOR_FUTURE_V2_30` for the future 30-run v2 study
(`$0.080288 <= $0.20`). Per the frozen interpretation policy, the ONE v2 probe
is a technical-validity + cost + serialization probe, NOT an accuracy gate.
STOP FOR GPT-5.6 SOL. Do NOT run the 30 v2 cells. Do NOT add graph assistance.
Do NOT start Saleor. Do NOT merge main yet.

## 3. What was delivered

- **v2 design:** `reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md`
- **v2 costprobe report:** `reports/DJANGOCMS_IMPACTPLAN_V2_COSTPROBE.md`
- **v2 module:** `src/benchmark/selection/impact_planner_v2.py`
- **v2 deterministic tests:** `tests/unit/selection/test_impact_plan_v2.py` (37 passed)
- **candidate ID mapping artifact:** `benchmark_data/external_validity/impactplan_v2_candidate_id_map.json`
- **v2 probe runner:** `scripts/stagec_djangocms_impactplan_v2_costprobe_execute.py`
- **evidence dir:** `reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/`

## 4. Deterministic validation (zero scientific calls)

- Probe pre-run validation PASS: universe == frozen 144 (hash `43f4279b...`);
  candidate ID mapping 144 entries, deterministic, artifact SHA-256
  `9d33e163...` verified; scenario 004 model-facing from `visible_drafts/`;
  v2 cap == 4096 == v1 primary cap (not 2048/8192/16384); v1 planner source
  unchanged vs HEAD; v1/v2 prompt + schema hashes computed/reproducible; hidden
  gold evaluation-only; primary evidence immutable (71/71); 8192 + 16K evidence
  unchanged; graph absent; exactly-one-probe.
- EXACT six deterministic gates + independent audit PASS
  (`probe_gates.json`).

## 5. Probe result (ONE scientific v2 call)

Full evidence: `costprobe.json`, `raw_response.txt`, `raw_response.sha256`,
`v2_prompt.txt`, `v2_schema.json`, `v1_prompt.txt`, `v1_schema.json`,
`candidate_id_map.json`, `sparse_analysis.json`.

- Scenario: `djangocms-external-validity-004`, arm `impact_plan_v2`, cap 4096
- **completion_tokens: 1107** (TERMINATED BEFORE 4096); finish_reason: `stop`;
  terminal_status: `succeeded`; schema_valid: true; truncation: false
- prompt_tokens 3447 / completion 1107 / total 4554; model_calls 1;
  latency 17.532 s; api_cost **$0.002141**
- invalid_ids: []; duplicate_ids: []; conflicts: []
- explicitly emitted decisions: **7** (6 REGENERATE + 1 VALIDATE)
- decoded PRESERVE count: **137** -> decoded policy = **144** exactly
- predicted write set: 6 paths
- Selection metrics (hidden gold applied AFTER inference): TP 4 / FP 2 / FN 0,
  precision 0.666667, recall 1.0, F1 0.8, FNR 0.0, full_recall true
- Full raw response persisted: 4,783 bytes / 127 lines, SHA-256
  `7efc1e1a637c3b5af1866b75f00a2f7741fa00396de4e040de1759cc4bb3ef8c`
- v1/v2 prompt + schema hashes persisted (see `costprobe.json` "identity").

## 6. Interpretation (frozen policy)

- This is a **TECHNICAL VALIDITY + COST + SERIALIZATION** probe.
- It is NOT an accuracy gate chosen after seeing the result.
- One-run accuracy differences between v1 and v2 are NOT statistically
  meaningful. The probe had lower FP than the v1 16K diagnostic (FP 2 vs 5) on
  this single scenario; this is a scientific observation, NOT a tuning trigger.
- v1 -> v2 changes schema and planner instruction together (ONE representation
  redesign); prompt/schema effects are NOT independently isolated.
- The one 16K omitted=>P success is illustrative only, not universal proof of
  omitted=>P safety.
- Projected token savings remain PRE-EXPERIMENT ESTIMATES until measured by v2.

## 7. Cost lock (future 30-run v2 study)

- 6 scenarios x 5 reps = 30 v2 cells; 25% conservative margin.
- Single probe $0.002141 -> raw 30-cell $0.064230 + margin $0.016058 =
  locked **$0.080288** <= hard ceiling $0.20.
- **COST_LOCK=PASS_FOR_FUTURE_V2_30**.
- The 30 v2 cells were NOT run in this task.

## 8. Closure

- Six closure gates + audit PASS (zero scientific calls).
- Primary evidence immutable: **71/71** unchanged.
- 8192 probe evidence unchanged; 16K diagnostic evidence unchanged.
- v1 unchanged (planner source identical to HEAD; v1 prompt/schema hashes
  reproducible; v1 default cap 4096).
- Graph NOT injected into v2; primary djangoCMS ImpactPlan was instantiated
  WITHOUT the frozen dependency graph (documented in
  `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md` and
  `reports/RESEARCH_TRUTH_MATRIX.md`).

## 9. Git state

- Committed + pushed to `research/djangocms-external-validity-prep-01`.
- No main merge. No `v0.11.0-benchmark-complete`.
- Evidence tag `stagec-djangocms-impactplan-v2-costprobe-verified-01` created
  (verification of ONE probe closure; does NOT imply completion of the future
  30-run v2 evaluation).

**STOP FOR GPT-5.6 SOL REVIEW. DO NOT RUN THE 30 V2 CELLS. DO NOT ADD GRAPH ASSISTANCE. DO NOT START SALEOR. DO NOT MERGE MAIN YET.**