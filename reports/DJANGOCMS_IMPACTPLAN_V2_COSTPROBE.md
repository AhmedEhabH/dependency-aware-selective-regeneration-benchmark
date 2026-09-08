# DJANGOCMS IMPACTPLAN-V2 COST/SMOKE PROBE

**PROBE_ID:** `scientific-stagec-djangocms-impactplan-v2-costprobe-01`
**Date (UTC):** 2026-09-08
**Type:** POST-HOC / EXPLORATORY / ONE-SCENARIO cost/smoke probe — **exactly ONE scientific v2 run.**
**Arm:** `impact_plan_v2`

---

## 1. Probe configuration (frozen)

| Parameter | Value |
|---|---|
| Scenario | `djangocms-external-validity-004` |
| Arm | `impact_plan_v2` |
| Scientific model | `qwen/qwen3-coder` |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`) |
| Fallback | OFF |
| Temperature | 0 |
| Completion cap | **4096** (original frozen ImpactPlan-v1 primary cap; NOT 2048/8192/16384) |
| Scope | SELECTION ONLY |
| Candidate universe | frozen 144 paths (hash `43f4279b...`) |
| Graph assistance | NOT injected |

Frozen inputs reused EXACTLY (identical to the primary study / D057 / D058):
same scenario 004 (visible SHA `0b25d274...`), same hidden gold
(evaluation-only), same 144-path universe, same scientific model/provider.

## 2. Deterministic validation (zero scientific calls)

- Probe pre-run validation PASS (universe == frozen 144; candidate ID mapping
  144 entries deterministic + artifact SHA-256 `9d33e163...` verified; scenario
  004 model-facing; v2 cap == 4096 == v1 primary cap; v1 planner source
  unchanged vs HEAD; v1/v2 prompt+schema hashes computed and reproducible;
  primary evidence immutable 71/71; 8192 + 16K evidence unchanged; graph
  absent; exactly-one-probe).
- EXACT six deterministic gates + independent audit PASS
  (`reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/probe_gates.json`).

## 3. Probe result (ONE scientific v2 call)

Full evidence: `reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/costprobe.json`,
`raw_response.txt`, `raw_response.sha256`, `v2_prompt.txt`, `v2_schema.json`,
`v1_prompt.txt`, `v1_schema.json`, `candidate_id_map.json`, `sparse_analysis.json`.

### 3.1 Technical validity + serialization (PRIMARY probe purpose)

- terminal_status: **succeeded**
- finish_reason: **stop**; truncation_status: **false**
- schema_valid: **true**
- prompt_tokens 3447 / completion_tokens **1107** / total_tokens 4554; model_calls 1
- latency 17.532 s; api_cost **$0.002141**
- raw response persisted: 4,783 bytes / 127 lines, SHA-256 `7efc1e1a...`
- explicitly emitted decision count: **7** (sparse)
- decoded PRESERVE count: **137** -> decoded policy = **144** candidate
  decisions exactly
- invalid_ids: **[]** ; duplicate_ids: **[]** ; conflicts: **[]**
- predicted write set: 6 paths

### 3.2 Correctness metrics (hidden gold applied ONLY after inference)

- Selected = 6 ; TP = 4 ; FP = 2 ; FN = 0
- Precision = 0.666667 ; Recall = 1.0 ; F1 = 0.8 ; FNR = 0.0 ; full_recall = true

### 3.3 Explicitly emitted non-PRESERVE decisions (rationale/confidence/codes/evidence retained)

| id | path | action | confidence |
|---|---|---|---|
| 4 | cms/admin/forms.py | REGENERATE | 0.85 |
| 6 | cms/admin/pageadmin.py | REGENERATE | 0.90 |
| 10 | cms/api.py | REGENERATE | 0.90 |
| 79 | cms/models/contentmodels.py | REGENERATE | 0.95 |
| 81 | cms/models/managers.py | REGENERATE | 0.80 |
| 111 | cms/templatetags/cms_static.py | VALIDATE | 0.70 |
| 134 | cms/views.py | REGENERATE | 0.85 |

Every emitted decision carries rationale, confidence, reason_codes and
evidence (persisted in `costprobe.json`). All other 137 candidates decode
deterministically to PRESERVE.

## 4. V1 vs V2 comparison

| Treatment | Cap | Completion Tokens | Valid | Explicit Decisions | Decoded Preserve | Selected | Precision | Recall | F1 | Time | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 PRIMARY @ 4096 | 4096 | truncation (19/30 cells truncated) | 6/30 valid | full 144-path serialization | — | — | 0.6765 (micro, 6 survivors) | 0.9200 | 0.7797 | — | — |
| v1 @ 16384 diagnostic | 16384 | 10650 | YES | 143 | 1 (omitted path defaulted to P) | 9 | 0.444444 | 1.0 | 0.615385 | 179.172 s | $0.01148 |
| **v2 @ 4096 probe** | **4096** | **1107** | **YES** | **7** | **137 (deterministic decode)** | **6** | **0.666667** | **1.0** | **0.8** | **17.532 s** | **$0.002141** |

Separate report:

- v1 PRIMARY @ 4096: **19 / 30** ImpactPlan cells truncated (recorded in
  `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md`).

Interpretation rule (frozen): this is a **TECHNICAL VALIDITY + COST +
SERIALIZATION** probe. It is NOT an accuracy gate chosen after seeing the
result. One-run accuracy differences are NOT statistically meaningful. Do NOT
tune v2 to repair the observed result before the future study. Poor correctness
in the probe would be a scientific observation, not a tuning trigger.

## 5. Future 30-run v2 cost lock

6 scenarios x 5 repetitions = 30 v2 cells; 25% conservative cost margin.

| Item | Value |
|---|---|
| Single probe cost | $0.002141 |
| Raw 30-cell estimate | $0.064230 |
| 25% margin | $0.016058 |
| Locked 30-cell estimate | **$0.080288** |
| Hard separate v2 scientific ceiling | $0.20 |
| Result | **COST_LOCK=PASS_FOR_FUTURE_V2_30** |

The 30 v2 cells are NOT executed in this task.

## 6. Pre-experiment token-savings estimate

Any projected v2 token savings derived from the persisted 16K raw response
remain **PRE-EXPERIMENT ESTIMATE** until measured by v2. Derived
token-per-entry figures are NOT universal constants. (The single 16K
omitted=>P success is illustrative only, not universal proof of omitted=>P
safety.)

## 7. Closure

- Six closure gates + audit PASS (zero scientific calls).
- Primary evidence immutable: **71/71** unchanged.
- 8192 probe evidence unchanged; 16K diagnostic evidence unchanged.
- v1 unchanged (planner source identical to HEAD; v1 prompt/schema hashes
  reproducible).
- No second v2 probe; no Agent; no repetitions; no second scenario.
- Future 30 v2 cells NOT run. Graph NOT injected. Saleor NOT started.

Evidence: `reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/`,
`reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md`.