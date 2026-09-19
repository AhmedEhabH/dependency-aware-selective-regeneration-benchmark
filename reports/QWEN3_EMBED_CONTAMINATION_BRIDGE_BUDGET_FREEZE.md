# Qwen3-Embedding Contamination Bridge — Budget Freeze (FROZEN, NOT EXECUTED)

**Date:** 2026-09-19  **Tier:** T3  **Status:** FROZEN BEFORE CALL 1 — **NOT EXECUTED** (model unavailable on OpenRouter; cost ceiling infeasible for the required full population).

**Hard safety ceilings (frozen):** total OpenRouter scientific cost **<= $0.50**; wall <= 120 min; max transport retries 3 (timeout/network/transient 5xx only); no fallback; no result-based retry; no batch-size change based on results; sealed-data guard ON.

## 1. DEVELOPMENT inputs (measured with the Qwen3-Embedding-8B tokenizer)

| Quantity | Value |
|---|---:|
| Unique DEVELOPMENT code units | 49705 |
| Query texts (174 djangoCMS + 149 Saleor) | 323 |
| Unit input tokens (total) | 21,870,401 |
| Unit tokens p50 / p90 / p99 / max | 155 / 766 / 5591 / 23954 |
| Query input tokens (total; mean 37.5/query) | 12,128 |
| Combined input tokens | 21,882,529 |

## 2. Requests under legal batching (batch = 64)

- Unit requests: ceil(49705/64) = **777**
- Query requests: ceil(323/64) = **6**
- Total embedding requests: **783**

## 3. USD cost assessment (informational)

The model is NOT offered by OpenRouter (verified 2026-09-19), so no real price exists. A sensitivity analysis over hypothetical per-1M-token prices shows the REQUIRED full-corpus run cannot fit the $0.50 ceiling:

| Price per 1M tokens | Projected full-run cost | Within $0.50? |
|---:|---:|:---:|
| $0.05 | $1.09 | no |
| $0.10 | $2.19 | no |
| $0.15 | $3.28 | no |
| $0.20 | $4.38 | no |
| $0.25 | $5.47 | no |

**Conclusion:** even at an optimistic $0.05/1M tokens the full-corpus run would cost ~$1.09, above the frozen $0.50 ceiling. Subsampling the DEVELOPMENT population is forbidden without a documented technical/cost limitation AND new authorization. The $0.50 ceiling therefore cannot be satisfied for the REQUIRED full population, independently of the model-availability blocker.

## 4. Max input length

- Longest unit: 23954 tokens; model documented max: 32,768 (re-verify at run time if the model becomes available) → no truncation required at the documented max.

## 5. Retry / failure policy (frozen)

- Permitted: deterministic transport retry for timeout / network / transient 429/5xx, max 3 retries.
- Forbidden: result-based retry, provider/model fallback, batch-size change based on results, dropping unfavorable tasks.

## 6. STOP conditions actually triggered (2026-09-19)

1. **Model unavailable**: `qwen/qwen3-embedding-8b` is not in the OpenRouter catalog (0 embedding models).
2. **Cost ceiling infeasible**: the required full-corpus run is projected above $0.50 even at optimistic prices; no real price exists to freeze.

Per the frozen stop policy, **NO scientific call was made** (0 calls, $0.00). Machine-readable: `reports/qwen3_embed_bridge_budget_freeze.json`.