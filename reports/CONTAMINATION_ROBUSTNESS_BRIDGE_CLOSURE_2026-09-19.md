# Contamination-Robustness Bridge — Closure Report (2026-09-19)

**Date:** 2026-09-19
**Mission:** Scope change — PAUSE Stage 5 confirmatory execution; run a
DEVELOPMENT-only contamination-robustness bridge (`qwen/qwen3-embedding-8b`
through the OpenRouter embeddings interface).
**Tier:** T3.
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Verdict:** **`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`** — the bridge
**STOPPED BEFORE SCIENTIFIC CALL 1** (model unavailable; cost ceiling
infeasible for the required full population). **0 paid calls, $0.00.**

---

## 1. Checkpoint (safe state preserved)

- Stage-5 confirmatory preparation from the previous session produced NO
  committed changes (the branch was created but the Impact Declaration write
  was superseded by this scope change). `main` was clean.
- All prior frozen scientific facts preserved exactly (see §6).
- `PROGRESS.md` updated to state:
  **`STAGE 5 CONFIRMATORY EXECUTION PAUSED — pending DEVELOPMENT-only
  contamination-robustness bridge.`**

## 2. Why the bridge did not run (documented, not a scientific failure)

1. **Model unavailable:** `qwen/qwen3-embedding-8b` is NOT in the OpenRouter
   catalog (447 models; **0 embedding-capable models**; HTTP 404 on all three
   Qwen3-Embedding identifiers). Recorded in
   `research/contamination-bridge/model_availability.json`.
2. **Cost ceiling infeasible (independent blocker):** measured DEVELOPMENT
   inputs = 49,705 units / 21,870,401 unit tokens + 12,128 query tokens
   (Qwen3-Embedding-8B tokenizer). Even at $0.05/1M tokens the required full
   run projects ~$1.09, above the frozen **$0.50** ceiling; subsampling is
   forbidden without a documented limitation + new authorization.

Per the frozen stop policy, **no scientific call was made** and no substitute
model was executed.

## 3. Delivered artifacts

- `docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md` (frozen, NOT EXECUTED)
- `reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md` + `.json` (frozen, NOT EXECUTED)
- `reports/SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md` (verdict C unchanged, strengthened)
- `reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md` (availability stop; no results)
- `reports/QWEN3_EMBED_INDEPENDENT_AUDIT.md` + `.json` (**9/9 PASS**)
- `src/benchmark/signal/or_embeddings.py` (mock-tested client; 13 tests)
- `scripts/contamination_bridge_token_estimate.py`, `scripts/contamination_bridge_budget_freeze.py`,
  `scripts/qwen3_bridge_independent_audit.py`
- `research/contamination-bridge/{model_availability,token_estimate}.json`
- `docs/QWEN3_EMBED_CONTAMINATION_BRIDGE_IMPACT_DECLARATION_2026-09-19.md`

## 4. Provenance audit V2 — outcome

Deepened investigation (2026-09-01 top-PyPI dump, full SweRank repo history,
paper text, HF datasets, GitHub code search attempt):
- `django-cms` rank **11,118** (just outside the top-11k SweLoc cutoff; 2025
  rank unverifiable → cannot rule out membership);
- `saleor` absent from the current top-15k (very unlikely, not impossible);
- no released SweLoc corpus/manifest exists anywhere we could find.
**Verdict C (`TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`)
UNCHANGED.** SweRank results are NOT clean unseen generalization.

## 5. Stage-5 decision

**`STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION`** — the bridge did
not run (technically inconclusive), so no new evidence weakens the provenance
concern. Stage-5 confirmatory execution stays PAUSED and SEALED
(djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent
djangoCMS INTERNAL_TEST 80). No sealed outcome was read.

## 6. Preserved frozen decisions

`CHEAP_RANKING_CLOSED_FOR_NOW`, `BOUNDED_SEMANTIC_NEGATIVE_FROZEN`,
`PRECISION_SAFE_ACCEPTANCE_FAIL`, `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`,
`SWERANK_EMBED_PASS`, SweRank revision `745d2a06103a66d3cfa600aa52fc0d3523010daa`,
comparator Frozen Route-B @ B=5, DEV populations 174/149 — all unchanged.

## 7. New decision (append-only)

**`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`** (2026-09-19) — model
unavailable on the required interface; budget ceiling infeasible for the
required full population. This is a technical freeze, NOT a scientific verdict
on dense retrieval, Qwen3-Embedding, or SweRank.

## 8. Recommended alternative (NOT executed)

`BAAI/bge-m3` (local, MIT, 568M, multilingual, CPU-feasible) as an independent
dense-retrieval control under a NEW frozen protocol + explicit authorization;
re-check the $0.50 ceiling (or authorize a revised ceiling) before any run.

## 9. Tests / audit

- `tests/unit/test_or_embeddings.py` **13/13 PASS** (request format, no
  fallback, batching determinism, hashing, cost accounting, retry policy,
  sealed-data guard).
- Independent preflight audit **9/9 PASS**
  (`reports/qwen3_embed_bridge_independent_audit.json`).
- Ruff / py_compile / git diff --check clean; affected signal suites PASS.

## 10. ONE next scientific action

With explicit authorization, run the contamination bridge with an available
independent dense-embedding control (recommended `BAAI/bge-m3`, local) under
the frozen file-level protocol, then decide Stage-5 justification. Until a
bridge outcome exists, Stage 5 remains paused/sealed.