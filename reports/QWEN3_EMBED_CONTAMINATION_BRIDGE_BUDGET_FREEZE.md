# Qwen3-Embedding Contamination Bridge — Budget Freeze (v2, live pricing)

**Date:** 2026-09-19  **Tier:** T3  **Status:** FROZEN BEFORE CALL 1 with corrected availability probe + live provider pricing. Technical probes EXECUTED; the FULL scientific run was STOPPED on material embedding nondeterminism (see `reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md`).

**Hard safety ceilings (frozen):** total OpenRouter scientific cost **<= $0.50**; wall <= 180 min (documented before call 1: ~783 batched requests x provider latency); max transport retries 3 (timeout/network/transient 5xx only); no fallback; no result-based retry; no batch-size change based on results; sealed-data guard ON.

**Provider pin (frozen before call 1):** **DeepInfra** for `qwen/qwen3-embedding-8b` at the documented **$0.01 / 1M tokens** (context 32,768; 100% 5-min uptime); routing pinned and fallbacks disabled per request. Nebius also serves $0.01/M (recorded alternative).

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

## 3. Expected cost (explicit arithmetic, live pinned-provider price)

`expected_cost = total_estimated_tokens / 1_000_000 * price_per_1m`

`= 21882529 / 1_000_000 * $0.01 = $0.2188`

**Expected full-run input cost: $0.2188** (hard ceiling $0.50). The earlier $1.09-$5.47 projection used stale assumed prices and is superseded by the live $0.01/M provider price.

## 4. Max input length

- Longest unit: 23954 tokens; DeepInfra context 32,768 → no truncation required at the documented max.

## 5. Retry / failure policy (frozen)

- Permitted: deterministic transport retry for timeout / network / transient 429/5xx, max 3 retries.
- Forbidden: result-based retry, provider/model fallback, batch-size change based on results, dropping unfavorable tasks.

## 6. Availability correction (2026-09-19)

The dedicated embeddings catalog `GET /api/v1/embeddings/models` lists 33 embedding models including `qwen/qwen3-embedding-8b` (context 32,768). The prior probe used the GENERATION catalog (0 embedding models) and was defective (P72: QWEN3_EMBED_AVAILABILITY_PROBE_DEFECT_CONFIRMED). The bridge therefore RESUMES under the frozen protocol.

Machine-readable: `reports/qwen3_embed_bridge_budget_freeze.json`.