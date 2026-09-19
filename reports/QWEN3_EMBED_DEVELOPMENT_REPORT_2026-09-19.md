# Qwen3-Embedding Development Report (2026-09-19) — NOT EXECUTED

**Date:** 2026-09-19
**Tier:** T3 (INDEPENDENT DENSE-RETRIEVAL CONTROL)
**Status:** **NOT EXECUTED — model unavailable on the required interface.**
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Scientific spend:** **0 paid calls / $0.00** (no OpenRouter call was made).

## 1. Why there are no results

The mission designated `qwen/qwen3-embedding-8b` through the **OpenRouter
`/api/v1/embeddings`** interface as the independent dense-retrieval control.
Preflight verification (2026-09-19) found:

- The full OpenRouter model catalog (`/api/v1/models`, 447 models) contains
  **zero embedding-capable models** (no model with an embedding
  architecture/tag).
- The model-detail endpoint returns **HTTP 404** for
  `qwen/qwen3-embedding-8b`, `qwen/qwen3-embedding-4b` and
  `qwen/qwen3-embedding-0.6b`.

Per the frozen stop conditions (mission §6/§27 and the frozen protocol), the
bridge is **STOPPED BEFORE CALL 1**. No substitute model was executed (a
silent substitution is forbidden). This report records the availability
finding and the frozen preparation; it intentionally contains **no scientific
result table**.

## 2. What was prepared (and remains valid for a future authorized run)

| Artifact | Status |
|---|---|
| `docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md` | FROZEN (gate A–J, metrics, leak rules, interpretation cases A–E); NOT EXECUTED |
| `reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md` + `.json` | FROZEN budget with measured DEVELOPMENT token counts; NOT EXECUTED |
| `src/benchmark/signal/or_embeddings.py` | OpenRouter embeddings client (frozen model id, no fallback, transport retry policy, cost ledger, sealed-data guard); mock-tested only (13 tests) |
| `research/contamination-bridge/model_availability.json` | recorded availability verdict |
| `research/contamination-bridge/token_estimate.json` | measured Qwen3-Embedding-8B token counts for the DEVELOPMENT inputs |
| `reports/SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md` | deepened provenance audit (verdict C unchanged) |
| `reports/QWEN3_EMBED_INDEPENDENT_AUDIT.md` + `.json` | independent preflight audit 9/9 PASS |

## 3. Development inputs (measured, informational)

| Quantity | Value |
|---|---:|
| Unique DEVELOPMENT code units | 49,705 |
| Query texts (174 djangoCMS + 149 Saleor) | 323 |
| Unit input tokens (Qwen3-Embedding-8B tokenizer) | 21,870,401 |
| Query input tokens | 12,128 |
| Combined | 21,882,529 |
| Embedding requests @ batch 64 | 777 (units) + 6 (queries) = 783 |

## 4. Cost assessment (informational)

The model has no OpenRouter price (not offered). A sensitivity analysis
($0.05–$0.25 per 1M tokens) projects **$1.09–$5.47** for the REQUIRED full
population — **above the frozen $0.50 ceiling** at every rate. Because
subsampling is forbidden without a documented limitation and new
authorization, the $0.50 ceiling cannot be satisfied for the required full
run. This is a SECOND independent blocker alongside model availability.

## 5. What this does NOT mean

- It is NOT a scientific result about dense retrieval (no run occurred).
- It is NOT a positive or negative verdict on Qwen3-Embedding or on
  SweRank — the SweRank DEV result (`SWERANK_EMBED_PASS`) is untouched.
- It is NOT a claim that the contamination question is answered.

## 6. Recommended alternative (NOT executed, requires new authorization)

**`BAAI/bge-m3`** (local open-weight, MIT license, 568M params, multilingual,
strong retrieval benchmarks, CPU-feasible on this machine for ~22M tokens) as
an **independent dense-retrieval control** under the same frozen file-level
protocol. Running the same Qwen3-Embedding-8B locally is not feasible on this
CPU-only machine. Any substitute requires an explicit new authorization and a
new freeze (budget, truncation rule, and a re-check of the $0.50 ceiling or an
authorized revised ceiling).