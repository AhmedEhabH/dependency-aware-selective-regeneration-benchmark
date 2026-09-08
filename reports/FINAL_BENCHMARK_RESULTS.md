# FINAL BENCHMARK RESULTS — djangoCMS External-Validity Stage-C Selection Study

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Report corrected (UTC):** 2026-09-08T03:12:51.914421+00:00
**Wiring tag:** `stagec-djangocms-study-wiring-verified-01`
**Scientific model/provider:** `qwen/qwen3-coder` @ `deepinfra/turbo` (DeepInfra pinned through OpenRouter; fallback OFF; temperature 0)
**Caps:** `iterative_repository_agent` = 1024 / `impact_plan` = 4096 completion tokens (frozen)
**Scope:** SELECTION ONLY (no regeneration / repair / migration / functional execution)
**Design:** 6 scenarios × 2 arms × 5 repetitions = exactly 60 frozen manifest cells
**Recorded:** 60/60 — 31 valid (succeeded) / 29 failed (recorded)
**Universe:** 144 paths, canonical SHA-256 `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`
**Recorded API cost:** $0.264148 (ceiling $0.50) — **COST_LOCK=PASS** (see Cost section for missing-cost caveat)

---

## 0. Definitions: VALID vs FAILED

**VALID / SUCCEEDED** means the inference reached a terminal selection result that is parseable / schema-valid, and whose selected paths pass runtime-universe validation, so that TP/FP/FN and correctness metrics can be computed.

**VALID DOES NOT MEAN CORRECT.** A valid run may have precision = 0, recall = 0, or F1 = 0 and still be a valid scientific observation.

**FAILED** means a normal scorable terminal selection was not produced due to an operational failure: completion truncation, provider failure, invalid/non-universe paths, terminal empty selection treated fail-closed by the frozen harness, or a harness defect. Failed cells are NOT converted into synthetic correctness scores.

---

## 1. OVERALL HEADLINE TABLE — VALID-RUN MICRO-AGGREGATION

Micro-aggregation pools TP/FP/FN across each arm's **valid** study runs. **Percentages are NOT averaged.**

### ⚠ WARNING — SEVERE MISSING-DATA ASYMMETRY

**Agent valid cells = 25**  
**ImpactPlan valid cells = 6**

Therefore these correctness values are based on **severely asymmetric survivor subsets** (ImpactPlan had 24/30 cells fail operationally). **DO NOT claim ImpactPlan has higher overall accuracy based on this table.**

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 147 | 95 | 52 | 18 | 0.6463 | 0.8407 | 0.7308 | 0.1593 | 432057 | 198 | 2216.0 | 0.135316 |
| impact_plan | 34 | 23 | 11 | 2 | 0.6765 | 0.9200 | 0.7797 | 0.0800 | 32560 | 6 | 382.4 | 0.018714 |

> Selected = pooled selected paths across valid runs only; TP/FP/FN = pooled across valid runs; Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2PR/(P+R); FNR = FN/(TP+FN); Tokens/Model Calls/Time/Cost = the valid-run subset for that row.

- Agent: tokens 432057, calls 198, tool calls 79, explicit read_file 26, inspected files 25.
- ImpactPlan: tokens 32560, calls 6, tool calls 0, explicit read_file 0.

---

## 2. ALL-CELL OPERATIONAL TABLE (valid + failed resource consumption)

This table includes resources consumed by BOTH valid and failed cells. It is an operational/efficiency table, NOT a correctness comparison.

| Arm | Valid / 30 | Failed / 30 | Valid Rate | Tokens | Model Calls | Measured Time | Recorded Cost |
|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 25 | 5 | 0.8333 | 449792 | 206 | 2265.517 | 0.140850 |
| impact_plan | 6 | 24 | 0.2000 | 184401 | 28 | 2658.733 | 0.123298 |

**ImpactPlan relative to Agent (all-cell):** tokens -59.00% · model calls -86.41% · recorded cost -12.46% · measured total latency +17.36%.

**Do not confuse this all-cell resource table with valid-only correctness.**

---

## 3. FAILURE TABLE (recomputed from raw evidence)

Recomputed from the 60 raw run records. Total failed cells: **29**.

| Arm | Failure Type | Count | Scientific Interpretation |
|---|---|---|---|
| impact_plan=19 | completion truncation 4096 cap | 19 | The current full structured ImpactPlan representation is operationally vulnerable to output truncation on the 144-file djangoCMS universe under the preregistered 4096 completion-token cap. NOT a judgment of reasoning quality. |
| iterative_repository_agent=1 | empty selection fail closed | 1 | The agent exhausted its 8 exploration calls and submitted an empty selection; the frozen harness treats empty final selection as a failed cell. |
| impact_plan=1 | harness defect | 1 | The model returned a validation_obligation kind outside the frozen enum, raising a ValueError during record construction (harness gap; one model call's cost was not recorded). |
| impact_plan=1, iterative_repository_agent=4 | provider http 429 | 5 | DeepInfra shared-pool upstream rate limit (engine_overloaded) exhausted the frozen 1-transient-retry policy (infrastructure). |
| impact_plan=3 | unknown path non universe | 3 | The model emitted paths outside the frozen 144-path universe; the fail-closed gate rejected the plan (a model-output/schema failure). |

**Truncation raw-evidence verification:** every truncation record has `finish_reason = length` and `completion_tokens = 4096` (the frozen cap). Counts below are per-arm.

---

## 4. OUTPUT-BUDGET ASYMMETRY (important validity issue)

The study arms did NOT have an equal completion-token allowance structure:

- **iterative_repository_agent:** up to **8 model calls**, each with **max completion tokens = 1024** → cumulative per-run completion-token allowance exposure up to **8 × 1024 = 8192 tokens across sequential calls**.
- **impact_plan:** **1 model call**, **max completion tokens = 4096** → up to **4096 tokens in one structured response**.

These budgets are **NOT directly interchangeable**; the arms have different interaction structures:
- Agent can distribute output over several sequential exploratory/action calls (up to 8).
- ImpactPlan must serialize a large structured plan in a single response.

**The frozen 4096 cap may therefore confound representational scalability with completion-budget sufficiency.** This is a genuine validity concern and is reported as a limitation, not as a measured property of either approach.

---

## 5. SERIALIZATION-SIZE ANALYSIS (ZERO API — deterministic)

A minimal schema-valid ImpactPlan JSON over the exact frozen 144-path candidate universe (shortest action label `PRESERVE`, empty rationales/evidence, compact JSON) measures:

- **Bytes (UTF-8):** 17364
- **Characters:** 17364
- **Rough token estimate (project heuristic `chars // 4`, ESTIMATE ONLY):** ~4341 tokens

**The exact `qwen/qwen3-coder` tokenizer is NOT available locally and was NOT downloaded; no API call was made.** The token figure is a heuristic estimate and must not be reported as a measured fact.

**Measured comparison with raw study responses:**

- **19 truncated ImpactPlan cells:** all `finish_reason = length`, all `completion_tokens = 4096` (the cap) — the model's emitted JSON (with rationales/evidence) reached the cap in every one of these cells.
- **6 successful ImpactPlan cells:** completion tokens min 920 / median 2165 / max 3750 — compact plan serializations did fit within the cap.

**Interpretation:** the minimal serialization alone is already on the order of the 4096-token cap (~4.3k heuristic-estimated tokens for 144 paths with no rationales), and the model's real outputs include rationales/evidence that pushed every truncated response to exactly 4096 completion tokens. The cap plausibly constrained serialization, but the primary study cannot separate representation scalability from the cap; the two are confounded (see Ablation Proposal).

---

## 6. MACRO PER-RUN STATISTICS (VALID runs only; reported separately from MICRO)

### VALID-RUN MACRO STATISTICS

### iterative_repository_agent (valid runs = 25)

| Metric | Mean | Median | Min | Max |
|---|---|---|---|---|
| precision | 0.6747 | 0.8333 |  |  |
| recall | 0.8095 | 1.0000 |  |  |
| f1 | 0.7121 | 0.7692 |  |  |
| selected set size | 5.88 | 5.0 | 2.0 | 10.0 |
| tokens | 17282.28 | 17675.0 | 12723.0 | 21204.0 |
| model calls | 7.92 | 8.0 | 7.0 | 8.0 |
| latency (s) | 88.64 | 47.27 | 11.09 | 252.00 |
| cost (USD) | 0.005413 | 0.005476 | 0.004060 | 0.006673 |
- **Full-recall rate** (valid runs with recall == 1.0): **0.6000**
- Valid-run tokens total: 432057; model calls total: 198; latency total: 2216.002 s; cost total: $0.135316.

### impact_plan (valid runs = 6)

| Metric | Mean | Median | Min | Max |
|---|---|---|---|---|
| precision | 0.6591 | 0.6667 |  |  |
| recall | 0.9429 | 1.0000 |  |  |
| f1 | 0.7657 | 0.8000 |  |  |
| selected set size | 5.666667 | 6.0 | 2.0 | 8.0 |
| tokens | 5426.666667 | 5436.0 | 4049.0 | 7068.0 |
| model calls | 1.0 | 1.0 | 1.0 | 1.0 |
| latency (s) | 63.73 | 51.48 | 16.58 | 165.70 |
| cost (USD) | 0.003119 | 0.003003 | 0.001859 | 0.004745 |
- **Full-recall rate** (valid runs with recall == 1.0): **0.6667**
- Valid-run tokens total: 32560; model calls total: 6; latency total: 382.406 s; cost total: $0.018714.

**Latency outliers (valid runs, > mean + 2σ):** ['stgc-djangocms-external-validity-006-iterative_repository_agent-r2']

Never mix these valid-run macro statistics with all-cell operational totals.

---

## 7. PER-SCENARIO TABLES (pooled across valid repetitions; same micro schema)

Schema: | Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |

### djangocms-external-validity-002

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 1 | 2 | 0 | 2 | 1 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 21141 | 8 | 31.2 | 0.006569 |
| impact_plan | 1 | 2 | 1 | 1 | 0 | 0.5000 | 1.0000 | 0.6667 | 0.0000 | 4049 | 1 | 38.4 | 0.001859 |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

### djangocms-external-validity-004

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 5 | 22 | 20 | 2 | 0 | 0.9091 | 1.0000 | 0.9524 | 0.0000 | 81801 | 40 | 119.1 | 0.025595 |
| impact_plan | 0/5 valid runs (N/A) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

### djangocms-external-validity-005

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 5 | 25 | 25 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 89028 | 40 | 369.5 | 0.027653 |
| impact_plan | 1 | 5 | 4 | 1 | 1 | 0.8000 | 0.8000 | 0.8000 | 0.2000 | 7068 | 1 | 165.7 | 0.004745 |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

### djangocms-external-validity-006

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 4 | 18 | 5 | 13 | 7 | 0.2778 | 0.4167 | 0.3333 | 0.5833 | 65767 | 31 | 515.6 | 0.020501 |
| impact_plan | 0/5 valid runs (N/A) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

### djangocms-external-validity-007

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 5 | 30 | 25 | 5 | 10 | 0.8333 | 0.7143 | 0.7692 | 0.2857 | 85940 | 40 | 681.6 | 0.026955 |
| impact_plan | 1 | 8 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 | 0.1429 | 4752 | 1 | 57.5 | 0.002718 |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

### djangocms-external-validity-008

| Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 5 | 50 | 20 | 30 | 0 | 0.4000 | 1.0000 | 0.5714 | 0.0000 | 88380 | 39 | 499.0 | 0.028043 |
| impact_plan | 3 | 19 | 12 | 7 | 0 | 0.6316 | 1.0000 | 0.7742 | 0.0000 | 16691 | 3 | 120.8 | 0.009392 |
Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).

---

## 8. COST ACCOUNTING

- **Recorded API cost across persisted study records was $0.264148.**
- **Actual spend is slightly higher** because one harness-defect scientific model call (impact_plan scenario 007 repetition 1) lacks complete cost provenance (the run raised a `ValueError` before token-usage/cost could be recorded; ≈ $0.003 by per-token rate). No estimate is presented as a measured fact.
- Hard scientific-study ceiling: **$0.50**. Evidence still supports remaining below the ceiling (recorded $0.264148 + estimated missing ≈ $0.003 << $0.50). **COST_LOCK=PASS.**

---

## 9. SCIENTIFIC INTERPRETATION (conservative)

**Supported:**
- The explicit ImpactPlan approach shows a strong reduction in selection-stage inference work, especially model-call count (206 → 28 all-cell) and token usage (449,792 → 184,401 all-cell; −59.0%).
- The current full structured-plan representation exhibited **poor operational completion** on the 144-file djangoCMS study under the preregistered 4096-token single-response cap: **19/30 ImpactPlan cells truncated** (raw-evidence confirmed), giving an **ImpactPlan operational valid rate of 20%** vs **Agent operational valid rate of 83.33%**.
- When ImpactPlan completed successfully, valid-run write-set recall was high (micro recall 0.92, macro median recall 1.0), but the severe valid-run imbalance (6 vs 25) prevents a clean between-arm accuracy-superiority claim.
- All-cell ImpactPlan token/model-call savings coexist with **worse total measured latency (+17.4%)**, driven by failed/truncated runs.
- The primary study **cannot disentangle representation scalability from the single-response output-cap constraint**.
- A separate post-hoc 8192-cap ablation would be appropriate to investigate this, but it is **NOT part of the primary result** (see `reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md`).

**NOT supported / NOT claimed:**
- ImpactPlan is universally more accurate.
- ImpactPlan is universally faster.
- End-to-end selective regeneration is proven.
- djangoCMS proves arbitrary large-repository generalization.
- The preregistered study proves truncation is inherent to ImpactPlan rather than partly cap-induced.

---

## 10. BASELINE DESCRIPTION

`iterative_repository_agent` is **our implemented iterative repository-agent baseline**, not a canonical or standardized representation of all agentic coding systems. Frozen behavior: up to 8 model calls with a 1024-token control-plane completion cap per call; calls 1–7 may issue `list_files` / `read_file` / `search_text` tool actions against a clean per-run workspace copy of the pinned repository; call 8 is reserved and forced to `final`, which must submit a non-empty subset of the 144-path editable universe. It does not regenerate, repair, or run migrations in this study (selection-only).

## 11. PROVENANCE

- Scientific model: `qwen/qwen3-coder`; provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF.
- Implementation/OpenCode model: the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731`; the task authorization header declared `openrouter/deepseek/deepseek-v3.2`. Both are recorded truthfully; neither is asserted as authoritative for scientific inference.
- Wiring tag: `stagec-djangocms-study-wiring-verified-01` (ancestor of HEAD).
- Frozen runtime universe hash: `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`.
- Raw evidence: `reports/scientific-stagec-djangocms-01/run_records.jsonl` + `reports/scientific-stagec-djangocms-01/runs/*.json` (hashes persisted in `raw_evidence_hashes.json`; verified unchanged).
