# Model Identities

**Purpose:** unambiguous identity reference for every model used in this
repository's scientific studies. Current-facing reviewer documentation must
use the exact human-readable names below — never an ambiguous abbreviation
that drops the full model identity (e.g., the bare family label alone, without
the parameter specification).

**Policy:** when a raw API identifier (OpenRouter slug) matters in current
documentation, write **both** the full human-readable name and the slug, e.g.:

> **Qwen3-Coder-480B-A35B-Instruct** (OpenRouter slug `qwen/qwen3-coder`)

Raw scientific evidence (provider responses, historical manifests, historical
RunRecords, API evidence) keeps the exact identifier used at execution time;
this document does **not** rewrite that evidence.

---

## 1. Historical Primary Scientific Model

| Attribute | Value |
|---|---|
| Full human-readable name | **Qwen3-Coder-480B-A35B-Instruct** |
| OpenRouter slug | `qwen/qwen3-coder` |
| Role | historical **primary** scientific model + historical Sparse-v2 exploratory study model |
| Gateway | OpenRouter |
| Provider | **DeepInfra** (through OpenRouter) |
| Historical endpoint tag | `deepinfra/turbo` |
| Reasoning | model-native direct / non-thinking |
| Used by | the primary djangoCMS selection study (Agent + ImpactPlan-v1), the post-hoc/exploratory ImpactPlan-v2 study, and the microstudies |

This model is the reference treatment that every robustness replication is
compared against. Its evidence is frozen and unchanged.

---

## 2. Completed General-Model Robustness Replication

| Attribute | Value |
|---|---|
| Full human-readable name | **Qwen3-32B** |
| OpenRouter slug | `qwen/qwen3-32b` |
| Role | completed post-hoc **cross-model** robustness replication |
| Gateway | OpenRouter |
| Provider | **DeepInfra** (through OpenRouter) |
| Endpoint tag | `deepinfra/fp8` (fp8) |
| Reasoning | hybrid model — **explicitly disabled** (`reasoning.enabled=false`) to match the historical non-thinking contract |
| Study | `scientific-stagec-djangocms-qwen3-32b-crossmodel-01` (60 cells: 6 scenarios × 2 arms × 5 repetitions) |
| Accounting status | derived-accounting correction applied (2026-09-11); raw evidence immutable |

---

## 3. New Coder-Model Robustness Replication

| Attribute | Value |
|---|---|
| Full human-readable name | **Qwen3-Coder-30B-A3B-Instruct** |
| OpenRouter slug | `qwen/qwen3-coder-30b-a3b-instruct` |
| Role | new post-hoc **cross-model / cross-provider** coder-model robustness replication |
| Gateway | OpenRouter |
| Provider | frozen from live OpenRouter metadata (see study report) |
| Reasoning | model-native non-thinking (no reasoning control parameter) |
| Study | `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01` (60 cells planned) |

---

## Quick-Reference Table

| Model | Slug | Study role | Provider |
|---|---|---|---|
| Qwen3-Coder-480B-A35B-Instruct | `qwen/qwen3-coder` | historical primary scientific model + historical Sparse-v2 study model | DeepInfra via OpenRouter |
| Qwen3-32B | `qwen/qwen3-32b` | completed post-hoc cross-model robustness replication | DeepInfra via OpenRouter |
| Qwen3-Coder-30B-A3B-Instruct | `qwen/qwen3-coder-30b-a3b-instruct` | new post-hoc cross-model / cross-provider robustness replication | frozen provider via OpenRouter |

---

## Study / Evidence Classification

- **Primary** studies: the djangoCMS selection study (Agent, ImpactPlan-v1) and
  the microstudies, run on **Qwen3-Coder-480B-A35B-Instruct**.
- **Post-hoc / exploratory**: the ImpactPlan-v2 / Preserve-by-Omission study on
  **Qwen3-Coder-480B-A35B-Instruct**.
- **Post-hoc cross-model robustness replication**: **Qwen3-32B**.
- **Post-hoc cross-model / cross-provider robustness replication**:
  **Qwen3-Coder-30B-A3B-Instruct**.

Rows come from **separate studies**. Denominators are never pooled across
rows. Unknown usage is represented as a lower bound, never silently converted
to zero.