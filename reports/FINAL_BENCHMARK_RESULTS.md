# FINAL BENCHMARK RESULTS — djangoCMS External-Validity Stage-C Selection Study

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Generated (UTC):** 2026-09-08T01:49:59.327506+00:00
**Wiring tag:** `stagec-djangocms-study-wiring-verified-01`
**Scientific model/provider:** `qwen/qwen3-coder` @ `deepinfra/turbo` (DeepInfra pinned through OpenRouter; fallback OFF; temperature 0)
**Caps:** `iterative_repository_agent` = 1024 / `impact_plan` = 4096 completion tokens
**Scope:** SELECTION ONLY (no regeneration / repair / migration / functional execution)
**Design:** 6 scenarios × 2 arms × 5 repetitions = exactly 60 manifest cells
**Recorded:** 60/60 cells — 31 succeeded (valid) / 29 failed (recorded)
**Universe:** 144 paths, canonical SHA-256 `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`
**Total recorded cost:** $0.264148 (ceiling $0.50) — **COST_LOCK=PASS**

## 1. OVERALL HEADLINE TABLE (MICRO-AGGREGATED, pooled over VALID runs)

Micro-aggregation pools TP/FP/FN across each arm's valid (succeeded) study runs. **Percentages are NOT averaged.**

**WARNING (missing-data asymmetry):** Agent has 25 valid runs; ImpactPlan has 6 valid runs (24 of its 30 cells failed operationally — 4096-cap truncation / unknown-path hallucination / 429 / harness defect). ImpactPlan micro-metrics therefore describe only the small survivor subset and are NOT comparable to Agent micro-metrics as equal-evidence estimates.

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 147 | 95 | 52 | 18 | 0.6463 | 0.8407 | 0.7308 | 0.1593 | 432057 | 198 | 2216.0 | 0.135316 |
| impact_plan | 34 | 23 | 11 | 2 | 0.6765 | 0.9200 | 0.7797 | 0.0800 | 32560 | 6 | 382.4 | 0.018714 |

> Selected = total selected paths across the arm's valid runs; Tokens = total scientific tokens; Model Calls = total model calls; Time = total measured latency (s); Cost = total recorded API cost (USD).

## 2. MACRO PER-RUN STATISTICS (valid runs; reported separately from MICRO)

### iterative_repository_agent (valid runs = 25)

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| precision | 0.6747 | 0.8333 |  |  |
| recall | 0.8095 | 1.0000 |  |  |
| f1 | 0.7121 | 0.7692 |  |  |
| selected_set_size | 5.88 | 5.0 | 2.0 | 10.0 |
| tokens | 17282.28 | 17675.0 | 12723.0 | 21204.0 |
| model_calls | 7.92 | 8.0 | 7.0 | 8.0 |
| latency_seconds | 88.64 | 47.27 | 11.09 | 252.00 |
| api_cost_usd | 0.005413 | 0.005476 | 0.004060 | 0.006673 |
- **Full-recall rate** (proportion of valid runs with recall == 1.0): **0.6000**

### impact_plan (valid runs = 6)

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| precision | 0.6591 | 0.6667 |  |  |
| recall | 0.9429 | 1.0000 |  |  |
| f1 | 0.7657 | 0.8000 |  |  |
| selected_set_size | 5.666667 | 6.0 | 2.0 | 8.0 |
| tokens | 5426.666667 | 5436.0 | 4049.0 | 7068.0 |
| model_calls | 1.0 | 1.0 | 1.0 | 1.0 |
| latency_seconds | 63.73 | 51.48 | 16.58 | 165.70 |
| api_cost_usd | 0.003119 | 0.003003 | 0.001859 | 0.004745 |
- **Full-recall rate** (proportion of valid runs with recall == 1.0): **0.6667**

## 3. PER-SCENARIO TABLES (pooled across the 5 repetitions; same micro schema)

### djangocms-external-validity-002

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 2 | 0 | 2 | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 21141 | 8 | 31.2 | 0.006569 |
| impact_plan | 2 | 1 | 1 | 0 | 0.5000 | 1.0000 | 0.6667 | 0.0000 | 4049 | 1 | 38.4 | 0.001859 |
Values are pooled across valid repetitions only (micro).

### djangocms-external-validity-004

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 22 | 20 | 2 | 0 | 0.9091 | 1.0000 | 0.9524 | 0.0000 | 81801 | 40 | 119.1 | 0.025595 |
| impact_plan (no valid runs — all 5 repetitions failed) | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.000000 |
Values are pooled across valid repetitions only (micro).

### djangocms-external-validity-005

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 25 | 25 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 89028 | 40 | 369.5 | 0.027653 |
| impact_plan | 5 | 4 | 1 | 1 | 0.8000 | 0.8000 | 0.8000 | 0.2000 | 7068 | 1 | 165.7 | 0.004745 |
Values are pooled across valid repetitions only (micro).

### djangocms-external-validity-006

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 18 | 5 | 13 | 7 | 0.2778 | 0.4167 | 0.3333 | 0.5833 | 65767 | 31 | 515.6 | 0.020501 |
| impact_plan (no valid runs — all 5 repetitions failed) | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.000000 |
Values are pooled across valid repetitions only (micro).

### djangocms-external-validity-007

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 30 | 25 | 5 | 10 | 0.8333 | 0.7143 | 0.7692 | 0.2857 | 85940 | 40 | 681.6 | 0.026955 |
| impact_plan | 8 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 | 0.1429 | 4752 | 1 | 57.5 | 0.002718 |
Values are pooled across valid repetitions only (micro).

### djangocms-external-validity-008

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|
| iterative_repository_agent | 50 | 20 | 30 | 0 | 0.4000 | 1.0000 | 0.5714 | 0.0000 | 88380 | 39 | 499.0 | 0.028043 |
| impact_plan | 19 | 12 | 7 | 0 | 0.6316 | 1.0000 | 0.7742 | 0.0000 | 16691 | 3 | 120.8 | 0.009392 |
Values are pooled across valid repetitions only (micro).

## 4. FAILED-RUN ACCOUNTING (29 failed cells, none rerun, none replaced)

| run_id | arm | failure_category | tokens | calls | latency |
|---|---:|---:|---:|---:|---|
| stgc-djangocms-external-validity-002-iterative_repository_agent-r1 | iterative_repository_agent | OpenRouter HTTP 429: Provider returned error | 0 | 0 | 6.64 |
| stgc-djangocms-external-validity-002-iterative_repository_agent-r2 | iterative_repository_agent | OpenRouter HTTP 429: Provider returned error | 0 | 0 | 14.531 |
| stgc-djangocms-external-validity-002-iterative_repository_agent-r3 | iterative_repository_agent | OpenRouter HTTP 429: Provider returned error | 0 | 0 | 1.594 |
| stgc-djangocms-external-validity-002-iterative_repository_agent-r4 | iterative_repository_agent | OpenRouter HTTP 429: Provider returned error | 0 | 0 | 1.688 |
| stgc-djangocms-external-validity-002-impact_plan-r1 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7225 | 1 | 271.406 |
| stgc-djangocms-external-validity-002-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7225 | 1 | 134.563 |
| stgc-djangocms-external-validity-002-impact_plan-r4 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7225 | 1 | 130.125 |
| stgc-djangocms-external-validity-002-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7225 | 1 | 60.296 |
| stgc-djangocms-external-validity-004-impact_plan-r1 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 6864 | 1 | 37.672 |
| stgc-djangocms-external-validity-004-impact_plan-r2 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 6864 | 1 | 49.938 |
| stgc-djangocms-external-validity-004-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 6864 | 1 | 38.828 |
| stgc-djangocms-external-validity-004-impact_plan-r4 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 6864 | 1 | 52.468 |
| stgc-djangocms-external-validity-004-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 6864 | 1 | 66.719 |
| stgc-djangocms-external-validity-005-impact_plan-r2 | impact_plan | OpenRouter HTTP 429: Provider returned error | 0 | 0 | 2.313 |
| stgc-djangocms-external-validity-005-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7414 | 1 | 207.312 |
| stgc-djangocms-external-validity-005-impact_plan-r4 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7414 | 1 | 146.797 |
| stgc-djangocms-external-validity-005-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7414 | 1 | 274.984 |
| stgc-djangocms-external-validity-006-iterative_repository_agent-r4 | iterative_repository_agent | iterative_agent: no paths selected after exploration | 17735 | 8 | 25.062 |
| stgc-djangocms-external-validity-006-impact_plan-r1 | impact_plan | impact_plan_planner_error: planner produced unknown paths: ['cms/migra | 4705 | 1 | 36.047 |
| stgc-djangocms-external-validity-006-impact_plan-r2 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7202 | 1 | 219.625 |
| stgc-djangocms-external-validity-006-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7202 | 1 | 85.563 |
| stgc-djangocms-external-validity-006-impact_plan-r4 | impact_plan | impact_plan_planner_error: planner produced unknown paths: ['cms/migra | 5399 | 1 | 27.89 |
| stgc-djangocms-external-validity-006-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner produced unknown paths: ['cms/migra | 5724 | 1 | 48.047 |
| stgc-djangocms-external-validity-007-impact_plan-r1 | impact_plan | harness_exception: ValueError | 0 | 0 | 30.547 |
| stgc-djangocms-external-validity-007-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7001 | 1 | 65.125 |
| stgc-djangocms-external-validity-007-impact_plan-r4 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7001 | 1 | 81.375 |
| stgc-djangocms-external-validity-007-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7001 | 1 | 99.421 |
| stgc-djangocms-external-validity-008-impact_plan-r3 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7572 | 1 | 68.516 |
| stgc-djangocms-external-validity-008-impact_plan-r5 | impact_plan | impact_plan_planner_error: planner response not JSON (finish_reason=le | 7572 | 1 | 40.75 |

Failure classes:
1. **Model-output `finish_reason=length` at the frozen 4096 cap (ImpactPlan):** the full 144-path plan JSON did not fit in 4096 completion tokens and truncated mid-JSON → `impact_plan_planner_error: planner response not JSON (finish_reason=length)`. This is a recorded scientific/model-output failure under the frozen cap.
2. **Planner hallucinated unknown paths (ImpactPlan):** the model emitted paths outside the 144-path universe (e.g. `cms/migrations/0001_initial.py`, `cms/tests/*`) → fail-closed `planner produced unknown paths`. Recorded failure.
3. **Provider 429 (infrastructure):** DeepInfra shared-pool rate limit (`engine_overloaded`) exhausted the frozen 1-transient-retry policy in 5 cells (4 agent + 1 impact). Recorded infrastructure failure.
4. **Agent `no paths selected after exploration`:** 1 agent cell (006-r4) explored 8 calls then submitted an empty set → recorded model-output failure.
5. **Harness defect (ImpactPlan 007-r1):** the model returned `validation_obligations[].kind='ui_state_reflection'` outside the enum → `ValueError` during record construction. One model call was consumed but its token usage/cost could not be recorded (documented accounting gap, ~$0.003).

**No scientific cell was rerun for any reason; no replacement runs; run 61 does not exist.**

## 5. LATENCY OUTLIERS (valid runs > mean + 2σ)

| run_id | latency_seconds |
|---|---:|
| stgc-djangocms-external-validity-006-iterative_repository_agent-r2 | 252.0 |

## 6. TOTALS

| Metric | Value |
|---|---:|
| Recorded cells | 60 |
| Successful (valid) cells | 31 |
| Failed cells | 29 |
| Total scientific tokens | 634193 |
| Total model calls | 234 |
| Total measured latency (s) | 4924.2 |
| Total recorded API cost (USD) | 0.264148 |
| Cost ceiling (USD) | 0.5 |
| COST_LOCK | PASS |

## 7. Provenance

- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF
- Implementation/OpenCode model: authorization header declares `openrouter/deepseek/deepseek-v3.2` (DEFAULT); the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731` (openrouter/deepseek/deepseek-v4-flash-0731). The two are inconsistent; both are recorded truthfully and neither is asserted as authoritative for scientific inference.
- Wiring tag: `stagec-djangocms-study-wiring-verified-01` (ancestor of HEAD)
- Frozen runtime universe hash: `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`
- Raw evidence: `reports/scientific-stagec-djangocms-01/run_records.jsonl` + `reports/scientific-stagec-djangocms-01/runs/*.json`
- Frozen manifest: `reports/scientific-stagec-djangocms-01/manifest_60.json`
- Gate evidence: `reports/scientific-stagec-djangocms-01/runtwiring_gates.json` (pre) / `closure_gates.json` (post)

## 8. Scientific Interpretation (Stage-C selection behavior only)

- This study measures **Stage-C selection only**. It does NOT measure end-to-end selective-regeneration correctness.
- Correctness first: ImpactPlan's headline F1 (0.7797) exceeds Agent's (0.7308) ONLY on the small 6-run valid subset; with 24/30 ImpactPlan cells failing operationally, the evidence is insufficient to claim ImpactPlan is more accurate. No such claim is made.
- No claim of general large-repository superiority is made from djangoCMS alone.
- No claim of end-to-end selective-regeneration correctness is made.
- Lower precision/recall, failed cells, large selected sets, and latency outliers are all reported without hiding.
