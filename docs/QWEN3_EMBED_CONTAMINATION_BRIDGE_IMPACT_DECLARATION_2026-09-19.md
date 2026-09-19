# Impact Declaration — Qwen3-Embedding Contamination-Robustness Bridge (T3)

**Date:** 2026-09-19
**Mission:** DEVELOPMENT-only contamination-robustness bridge (scope change to
the paused Stage-5 confirmatory preparation).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** **T3** — a new evaluation-strategy family (independent dense-retrieval
control) under a frozen protocol.
**Status:** **BLOCKED BEFORE SCIENTIFIC CALL 1** — the requested model
`qwen/qwen3-embedding-8b` does NOT exist on OpenRouter (verified against the
full 447-model catalog: 0 embedding-capable models; 404 on all three
Qwen3-Embedding identifiers). Per the mission's frozen stop conditions, **NO
paid scientific call is made**. This declaration covers the preparation and
documentation work that remains valid.

---

## 1. Scientific question (unchanged by the stop)

"Is the SweRankEmbed DEVELOPMENT improvement caused by dense semantic retrieval
as a general mechanism, or is it unusually dependent on SweRank/SweLoc
specialization, training distribution, or possible target-repository overlap?"

Answering it requires an INDEPENDENT pretrained dense-retrieval control under
the EXACT same parent-only file-localization protocol. Because the designated
control model is unavailable through the required interface, the bridge is
frozen as **technically inconclusive** (`QWEN3_EMBED_BRIDGE_TECHNICALLY_
INCONCLUSIVE`); the availability result is documented, an alternative is
recommended but NOT executed, and the paused Stage-5 confirmatory remains
sealed.

## 2. Affected scientific artifacts (created)

| Artifact | Kind | Role |
|---|---|---|
| `docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md` | NEW doc | frozen protocol (gate A–J, metrics, leak rules, interpretation cases A–E) — marked NOT EXECUTED (model unavailable) |
| `reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md` + `.json` | NEW report | frozen budget (expected/ceiling cost, calls, tokens, wall) — marked NOT EXECUTED; includes measured DEVELOPMENT token estimates |
| `reports/SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md` | NEW report | deepened SweLoc provenance investigation (verdict A/B/C) |
| `reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md` | NEW report | documents the availability finding and why no results exist |
| `reports/QWEN3_EMBED_INDEPENDENT_AUDIT.md` + `.json` | NEW report | independent audit of the availability finding, budget artifact, sealed-data guard, protocol hygiene (no analyzer imports) |
| `reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md` | NEW report | closure: STOP-before-call-1, preserved work, Stage-5 decision |
| `src/benchmark/signal/or_embeddings.py` | NEW module | OpenRouter embeddings client (frozen model id, no fallback, transport retry policy, cost accounting) — prepared, mock-tested only |
| `tests/unit/test_or_embeddings.py` | NEW tests | request formatting, no fallback, batching determinism, hashing, cost accounting, failure policy, sealed-data guard |
| `research/contamination-bridge/*.json` | NEW evidence | token estimates, availability record, budget JSON |

## 3. Affected implementation components

| Component | Change |
|---|---|
| `src/benchmark/signal/metrics.py`, `code_units.py`, `swrank_adapter.py`, `swerank_model.py` | READ-ONLY reuse (frozen DEV pipeline) — no scientific change |
| `research/strong-localization-signal/swerank/{metrics,gate,efficiency}.json` | READ-ONLY (frozen DEV results) — no modification |
| SweRank venv (temp) + HF cache (temp) | used for token counting only (Qwen3 tokenizer), no inference |
| OpenRouter client | NEW, mock-tested only; NO network call made |

## 4. Dependencies

- `benchmark.signal.*` (frozen DEV pipeline modules) for reuse.
- Local caches for token estimates: `swerank-cache/blob_text.json`,
  `swerank-cache/emb/embed_index.json` (49,705 units), 14,807 blob texts.
- Qwen3 tokenizer from HF (free metadata download) for token counting ONLY.
- OpenRouter catalog endpoints (free metadata) for the availability audit.

## 5. Edge cases / boundaries

- NO paid OpenRouter call; NO fallback model; NO silent substitution.
- Sealed sets (djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE, spent
  djangoCMS INTERNAL_TEST) untouched — no outcome read.
- If a Qwen3-Embedding model becomes available on OpenRouter later, the frozen
  protocol + budget + client are ready; a NEW explicit authorization is still
  required before call 1.
- The client is tested against a fake transport only (no endpoint exists).

## 6. Verification plan

1. ruff; 2. py_compile; 3. git diff --check; 4. affected pytest suites
(signal modules + new or_embeddings tests); 5. independent audit (no analyzer
imports) recomputing the availability finding and budget JSON from recorded
artifacts.

## 7. Planned decisions (append-only)

- `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE` (model unavailable on the
  required interface) — the ONLY scientifically correct label; no positive
  bridge label is invented.
- `STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION` — Stage 5 stays
  sealed/paused (bridge did not run; provenance verdict C unchanged).