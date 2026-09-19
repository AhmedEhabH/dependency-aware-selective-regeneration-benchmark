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

---

## 11. UPDATE — probe-defect correction mission (2026-09-19)

The user-authorized correction mission (QWEN3_EMBEDDING_BRIDGE_PROBE_DEFECT_
CORRECTION) re-probed with the CORRECT dedicated embeddings catalog:

- **P72 — availability probe defect confirmed.** `GET
  https://openrouter.ai/api/v1/embeddings/models` lists 33 embedding models
  including `qwen/qwen3-embedding-8b` (context 32,768; HF
  Qwen/Qwen3-Embedding-8B). Providers: Nebius $0.01/M, **DeepInfra $0.01/M
  (pinned)**, SiliconFlow $0.04/M. Expected full-run cost
  `21,882,529 / 1e6 × $0.01 = $0.2188` (< $0.50 ceiling). P71 remains the true
  historical record of the defective probe.
- **P73 — STOPPED on material embedding nondeterminism (BEFORE the full
  scientific run).** The frozen determinism probe (§12.8) found cosine drift
  ~1.0e-4 (float-level) with unit top-10 overlap 1.0, BUT the file-level
  stability check (5 complete djangoCMS DEV tasks × two independent
  realizations) showed a **B=5 file-set flip on 1/5 tasks** (0.8 overlap).
  Per the frozen criterion this is material enough to destabilize the
  operating-point ranking → **STOP**. Technical probes only (~$0.023 spend,
  0 full-run calls); the bridge remains
  `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE` (determinism root cause).
- No scientific Qwen result was produced; no substitute model was executed;
  sealed sets remain untouched; Stage-5 confirmatory remains PAUSED and SEALED
  (`STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION`).
- Evidence: `research/contamination-bridge/model_availability_v2.json`,
  `research/contamination-bridge/qwen_embed/{probe,stability}.json`,
  `reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md` (technical-stop
  update), `docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md`.
- Recommended next step (NOT executed, needs new authorization): a
  determinism-controllable LOCAL open-weight control (e.g., `BAAI/bge-m3`
  local inference where numerical determinism can be pinned) under a new
  freeze.
## 12. UPDATE — two-realization replication (2026-09-19, T3)

The bridge line is now CLOSED WITH A RESULT, NOT technically inconclusive for
the conclusion-reproducibility question:

- **P74 amendment (append-only, before any target-aware Qwen inspection):** two
  complete independent realizations (A and B) of the hosted Qwen embeddings
  replace the strict bitwise-determinism requirement. P73's determinism finding
  remains a valid historical record; this mission evaluates CONCLUSION
  REPRODUCIBILITY.
- **Execution:** qwen/qwen3-embedding-8b @ DeepInfra (.01/M live-verified,
  fallback disabled) over the FULL legal DEV population twice (49,703 units +
  323 queries per realization; whitespace-only excluded per frozen 12.9).
  Actual cost A .1971 / B .2188; cumulative incl. probes ~.439 < .50.
  0 permanent failures.
- **Result:** **INDEPENDENT_DENSE_RETRIEVAL_REPLICATED** — A and B BOTH pass
  the frozen gate on djangoCMS AND Saleor @B=5 (Qwen F1 0.262/0.270 vs
  Route-B 0.226/0.237; all file-level CIs exclude zero). A-vs-B: 97.21% exact
  same selected set, mean Jaccard 0.9907, 9 one-file flips all FP-for-FP.
- **NO OVERCLAIM:** Qwen does NOT beat Sparse final-set F1 (0.318/0.261) and
  does NOT replace SweRankEmbed-Small (0.280/0.288).
- **Engineering artifact:** label-free full-file-score Parquet tables
  (143,852 rows/realization) for the future calibrated ADD+DROP study.
- **Stage 5 remains PAUSED and SEALED**
  (STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION): the dense
  replication strengthens the mechanism hypothesis but does NOT prove unseen
  generalization (provenance verdict C unchanged).
- Evidence: reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md,
  research/contamination-bridge/qwen_embed/{realization_A,realization_B,two_realization_metrics}.json,
  reports/qwen3_two_realization_{gate,reproducibility,audit}.json,
  docs/CALIBRATED_SET_SELECTION_V1_DRAFT.md, DECISIONS.md P74/P75/P76.
