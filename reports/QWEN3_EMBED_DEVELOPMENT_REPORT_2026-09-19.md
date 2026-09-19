# Qwen3-Embedding Development Report (2026-09-19) — TECHNICAL STOP (no full run)

**Date:** 2026-09-19 (updated by the probe-defect correction mission)
**Tier:** T3 (INDEPENDENT DENSE-RETRIEVAL CONTROL)
**Status:** **NO FULL SCIENTIFIC RESULT — technical probes only.**
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Scientific spend:** **~$0.023** (technical probes; 0 full-run calls).

## 1. Availability (CORRECTED — the original probe was defective)

- P71's "model unavailable" verdict was caused by probing the GENERATION
  catalog. The **dedicated embeddings catalog**
  (`GET https://openrouter.ai/api/v1/embeddings/models`) lists **33 embedding
  models**, including **`qwen/qwen3-embedding-8b`** (context 32,768; HF
  `Qwen/Qwen3-Embedding-8B`).
- **Pinned provider: DeepInfra** (documented **$0.01 / 1M tokens**; context
  32,768; 100% 5-min uptime; fallback disabled). Nebius also serves $0.01/M.
- Expected full-run cost `21,882,529 / 1e6 × $0.01 = $0.2188` (< $0.50
  ceiling) — the earlier $1.09–$5.47 projection used stale assumed prices.

## 2. Determinism probe (frozen protocol §12.8) — RESULT: STOP

| Check | Result |
|---|---|
| 201-unit probe, identical input embedded twice | max cosine drift **~1.0e-4** (float-level), mean 4e-5; min cosine sim 0.9999 |
| Anchor text in batch vs fresh single call | cosine 0.99994–1.0 (batch-position stable) |
| Unit top-10 overlap (call1 vs call2) for a DEV query | **1.0** |
| FILE-level stability (5 complete djangoCMS DEV tasks, two independent realizations) | B=5 file sets **identical 4/5**, **1/5 flipped a B=5 file** (overlap 0.8) |
| Frozen criterion (§12.8) | drift CAN destabilize the file-level B=5 selection → **STOP** |

The endpoint is deterministic to ~1e-4 cosine (normal hosted-service float
noise), and that noise CAN flip a near-tie at the file-level B=5 operating
point (~1/5 tasks in the sample). Per the pre-committed criterion, the full
scientific run was **NOT** performed.

## 3. Why there are no results

The bridge was stopped BEFORE the full scientific run (P73). Two realizations
of a task's corpus can select a different B=5 file set when a near-tie exists;
the protocol's determinism gate ("technically valid deterministic execution",
gate G) is therefore not satisfiable with this endpoint at the operating point.
This is a **technical freeze**, not a scientific verdict on Qwen3-Embedding or
on dense retrieval.

## 4. What was prepared (valid for a future authorized run)

- `docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md` (frozen;
  numeric gate A–H; API-semantics; determinism criterion).
- `reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md` + `.json` (live
  $0.01/M pricing; expected $0.2188; ceiling $0.50).
- `src/benchmark/signal/or_embeddings.py` (pinned model/provider, no fallback,
  transport retry policy, cost ledger, sealed guard; 16 unit tests).
- `research/contamination-bridge/model_availability_v2.json`,
  `qwen_embed/probe.json`, `qwen_embed/stability.json` (measured evidence).
- Regression test forcing future availability checks to the embeddings
  catalog.

## 5. Recommended alternative (NOT executed, requires new authorization)

A **determinism-controllable LOCAL open-weight** dense-embedding control (e.g.,
`BAAI/bge-m3` local inference, where numerical determinism can be pinned)
under a new frozen protocol. Local inference is the only way to guarantee the
bit-level reproducibility the file-level operating point needs. Any substitute
requires an explicit new authorization.

## 6. What this does NOT mean

- NOT a scientific result about Qwen3-Embedding or dense retrieval (no full
  run occurred).
- NOT a claim that the contamination question is answered.
- NOT a change to the SweRank DEV result (`SWERANK_EMBED_PASS` is untouched).