# Qwen3-Coder-30B-A3B-Instruct Cross-Model / Cross-Provider Robustness Replication — Results

**Study ID:** `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01`
**Date:** 2026-09-11
**Classification:** POST-HOC CROSS-MODEL / CROSS-PROVIDER ROBUSTNESS REPLICATION

Model: **Qwen3-Coder-30B-A3B-Instruct** (OpenRouter slug
`qwen/qwen3-coder-30b-a3b-instruct`) @ OpenRouter / **SiliconFlow**
(`siliconflow/fp8`), model-native non-thinking, temperature 0, cap 4096,
graph OFF. Historical reference (descriptive): Qwen3-Coder-480B-A35B-Instruct
(OpenRouter slug `qwen/qwen3-coder`) @ OpenRouter / DeepInfra. The completed
Qwen3-32B robustness study is shown beside these values DESCRIPTIVELY. The
three studies are never pooled.

> **Provider difference (disclosed limitation):** historical = DeepInfra;
> new coder model = SiliconFlow. Model and provider are confounded in any
> comparison.

---

## 1. Operational results

| Metric | v1 (ImpactPlan-v1) | v2 (ImpactPlan-v2 / Preserve-by-Omission) | Overall |
|---|---|---|---|
| Recorded | 30 | 30 | 60 |
| Valid | 17 | 28 | 45 |
| Failed | 13 | 2 | 15 |
| Truncations | **11** | **0** | **11** |
| Requests issued | 30 | 30 | **60** |
| Responses received | 30 | 29 | **59** |
| Usage-known cells | 30 | 29 | **59** |
| Usage-unknown cells | 0 | 1 | **1** |
| Transport failures | 0 | 1 | **1** |
| Prompt tokens (known) | 93,510 | 110,296 | 203,806 |
| Completion tokens (known) | 68,766 | 28,574 | 97,340 |
| Total tokens (known) | 162,276 | 138,870 | **301,146** |
| Calls (usage-bearing) | 30 | 29 | 59 |
| Latency (s) | 2,318.6 | 1,141.3 | 3,459.9 |
| Live cost (USD, lower bound) | $0.025800 | $0.015718 | **$0.041518** |

Token and cost totals are **LOWER-BOUND recorded values**: the single
transport-failure cell (`stgc30b-djangocms-external-validity-007-impact_plan_v2-r3`)
issued a request but its exact provider usage/cost is unknown and is NOT
silently zeroed (see `ACCOUNTING_CORRECTION_NOTE.md`).

**Failure taxonomy (v1, 13 failed):** 11 truncations at the frozen 4096 cap
(`finish_reason=length`), 2 planner errors (unknown paths). **v2 (2 failed):**
1 duplicate-candidate-id error, 1 transport failure (no response).

## 2. Selection fidelity (valid cells only, micro-aggregated)

| Arm | TP | FP | FN | Precision | Recall | F1 | FNR | Full-recall rate |
|---|---|---|---|---|---|---|---|---|
| ImpactPlan-v1 | 44 | 23 | 11 | 0.6567 | 0.8000 | 0.7213 | 0.2000 | 0.588 (10/17) |
| ImpactPlan-v2 | 75 | 60 | 34 | 0.5556 | 0.6881 | 0.6148 | 0.3119 | 0.357 (10/28) |

## 3. Directional representation label (NEW study ONLY, descriptive)

Criterion: v2 validity rate > v1 validity rate AND v2 truncation rate < v1
truncation rate.

- v2 validity 28/30 = 0.933 > v1 17/30 = 0.567 ✓
- v2 truncation 0/30 = 0.000 < v1 11/30 = 0.367 ✓

**DIRECTIONALLY REPLICATED (descriptive only).** Selection fidelity is a
separate outcome.

## 4. Per-scenario results (v2 arm)

| Scenario | Valid | Failed | Trunc | TP | FP | FN | P | R | F1 |
|---|---|---|---|---|---|---|---|---|
| djangocms-external-validity-002 | 5 | 0 | 0 | 5 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| djangocms-external-validity-004 | 4 | 1 | 0 | 12 | 9 | 4 | 0.571 | 0.750 | 0.649 |
| djangocms-external-validity-005 | 5 | 0 | 0 | 24 | 2 | 1 | 0.923 | 0.960 | 0.941 |
| djangocms-external-validity-006 | 5 | 0 | 0 | 1 | 18 | 14 | 0.053 | 0.067 | 0.059 |
| djangocms-external-validity-007 | 4 | 1 | 0 | 17 | 7 | 11 | 0.708 | 0.607 | 0.654 |
| djangocms-external-validity-008 | 5 | 0 | 0 | 16 | 24 | 4 | 0.400 | 0.800 | 0.533 |

## 5. Scenario 006 analysis (v2)

S006 (djangocms-external-validity-006) is the known weak case. All 5 new v2
runs were valid (0 truncations) but selection fidelity was poor:

| Selected file | Frequency (of 5) | Gold? |
|---|---|---|
| `cms/admin/forms.py` | 5 | no |
| `cms/models/placeholderpluginmodel.py` | 4 | no |
| `cms/admin/utils.py` | 4 | no |
| `cms/plugin_rendering.py` | 3 | no |
| `cms/models/permissionmodels.py` | 2 | no |
| `cms/models/pluginmodel.py` | 1 | **yes** |

TP=1, FP=18, FN=14, P=0.053, R=0.067, F1=0.059. The model **over-selected**
non-gold files and persistently missed gold files — the same qualitative S006
weakness observed for the historical Qwen3-Coder-480B-A35B-Instruct
(over-selection + persistent misses). **Descriptive only; no causal claim.**
Completion-token stats (valid cells): v1 min/median/mean/max =
705 / 2269 / 2292 / 4096; v2 = 346 / 954 / 952 / 2178.

## 6. Cross-model Sparse-v2 agreement (DESCRIPTIVE)

**Qwen3-Coder-30B-A3B-Instruct vs historical Qwen3-Coder-480B-A35B-Instruct:**
135 cross-product pairs; mean Jaccard 0.491, median 0.429, min 0.091,
max 1.000 (per-file frequencies in
`reports/QWEN3_CODER_30B_A3B_CROSSMODEL_AGREEMENT.{md,csv}`). Runs are NOT
paired by repetition. The completed Qwen3-32B agreement (102 pairs; mean
0.284, median 0.231) is shown beside these values DESCRIPTIVELY — the three
studies are never pooled.

## 7. Cost and runtime

- Live SiliconFlow rates $0.07/1M input, $0.28/1M output.
- Recorded live cost **$0.041518** (LOWER-BOUND) < $0.20 hard ceiling.
- Serial runtime 3,459.9 s (~57.7 min) < 3 h ceiling.

## 8. Validation

Six pre-benchmark gates + independent audit PASS (before cell 1); manifest
frozen (60 cells); two capability probes PASS; six closure gates + independent
audit PASS; `scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py` (zero
API) PASS; `scripts/verify_qwen3_32b_crossmodel_claims.py` PASS;
`scripts/verify_paper_claims.py` PASS. Historical evidence unchanged.