# Qwen3-Embedding Contamination-Robustness Protocol — FROZEN (2026-09-19)

**Tier:** T3 (new evaluation-strategy family: INDEPENDENT DENSE-RETRIEVAL
CONTROL).
**Status:** **FROZEN BUT NOT EXECUTED.** As of 2026-09-19 the designated model
`qwen/qwen3-embedding-8b` is **not available on OpenRouter** (verified: full
447-model catalog, zero embedding-capable models; 404 on all three
Qwen3-Embedding identifiers). Per the mission's stop conditions, **no
scientific call was made** and the bridge is frozen as
`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`. This document is the frozen
design that WOULD govern an authorized run (with the same model if it becomes
available, or with an explicitly authorized substitute under a new freeze).
**Mission:** contamination-robustness bridge (scope change; Stage-5
confirmatory PAUSED).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Scientific spend to date:** 0 paid calls, $0.00.

---

## 1. Scientific question

Does an independently pretrained, code-capable dense embedding model reproduce
the direction and magnitude of SweRankEmbed-Small's DEVELOPMENT gains under the
EXACT same parent-only file-localization protocol? This is a
CONTAMINATION-ROBUSTNESS CONTROL, not a competition to find a new winner.

## 2. Frozen context (immutable)

- `SWERANK_EMBED_PASS` (DEV; frozen method, revision
  `745d2a06103a66d3cfa600aa52fc0d3523010daa`; comparator Frozen Route-B @ B=5).
- SweRank DEV populations: djangoCMS 174, Saleor 149 (FULL legal DEV).
- Provenance verdict (unchanged): `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`.
- Sealed populations: djangoCMS RESERVE (59), Saleor INTERNAL_TEST (80),
  Saleor RESERVE (1086), spent djangoCMS INTERNAL_TEST (80) — NEVER opened.

## 3. Independent control model (designated)

| Item | Value |
|---|---|
| Model id | `qwen/qwen3-embedding-8b` (OpenRouter) |
| Endpoint | `POST https://openrouter.ai/api/v1/embeddings` |
| Frozen constant | `src/benchmark/signal/or_embeddings.py::OPENROUTER_EMBED_MODEL` |
| No fallback | ANY model/provider substitution requires a new freeze + authorization |
| Availability (2026-09-19) | **NOT AVAILABLE** — bridge STOPPED before call 1 |

## 4. Protocol reuse (identical to the frozen SweRank DEV study)

Same for the control run wherever the model interface permits:
- DEVELOPMENT populations: djangoCMS 174 + Saleor 149 (no subsampling without
  a documented technical/cost limitation and new authorization);
- parent revision indexing; production-file universe; frozen code-unit
  extraction (top-level sync functions + classes + sync methods; whole-file
  fallback); test/vendor/generated exclusions; query = parent-visible issue
  intent ONLY (hashed per task); target-leakage guard (no changed paths,
  target diff, child revision, proxy, future issue/commit info);
- file aggregation: `score(F) = MAX over units of similarity(q, unit)`;
- tie-break: normalized repository path ascending;
- primary B=5 (curve B ∈ {1,3,5,10} only from the same ranking, no extra
  calls); Route-B comparator; metrics + paired task bootstrap (>=10,000
  resamples, fixed seed frozen before target analysis, CI95 = [Q2.5, Q97.5]).

## 5. Similarity normalization rule (frozen)

If the control model's API returns raw (non-normalized) embeddings, the frozen
rule is L2-normalize both query and unit embeddings and score = dot product
(cosine), identical to the SweRank adapter. If the API normalizes server-side,
use the returned vectors directly. Freeze the rule per the interface BEFORE
inspecting target results.

## 6. Frozen gate (before target results; does NOT modify SweRank/Stage-4/4b gates)

Required on BOTH djangoCMS and Saleor at B=5:
- A. final F1 (control) > final F1 (Frozen Route-B);
- B. Recall >= Route-B − margin (conservative non-inferiority margin frozen
  before outcomes; default 0.05 pooled points);
- C. FNR <= Route-B + margin;
- D. Precision >= Route-B OR bounded loss compensated by preregistered
  F1/Recall improvement;
- E. >= 3/5 seeded grouped folds non-negative on final F1;
- F. paired-bootstrap 95% CIs reported;
- G. zero leakage (audited);
- H. >= 95% technically valid embedding requests after permitted transport
  retries (no result-dependent retry);
- I. deterministic/reproducible ranking under frozen inputs;
- J. total cost within the frozen ceiling.

ORR is a mechanism diagnostic, not the sole primary criterion.

## 7. Interpretation rules (frozen BEFORE results)

- CASE A — control materially improves over Route-B on both repos, same broad
  direction as SweRank: strong evidence dense retrieval as a mechanism
  contributes value; weakens but does NOT eliminate the memorization
  hypothesis; Stage 5 may become justifiable after a provenance review.
- CASE B — SweRank succeeds, control fails to improve robustly on one or both
  repos: SweRank advantage appears specialization/training-dependent; increase
  contamination concern; do NOT open Stage 5.
- CASE C — control approx. matches/exceeds SweRank on both repos: an
  independent multilingual dense signal may be preferable for generalization;
  do NOT auto-replace the frozen method; new comparison protocol required.
- CASE D — control improves one repo only: dense retrieval not robustly
  replicated; do NOT open Stage 5 on that evidence.
- CASE E — technical/API reproducibility unacceptable: freeze the bridge as
  technically inconclusive (`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`);
  do NOT convert technical failure into scientific failure.

## 8. Important limitation (stated explicitly)

A successful Qwen control does NOT prove "neither model has seen djangoCMS or
Saleor". Its scientific value is narrower: it tests whether an independently
trained dense embedding architecture reproduces the observed localization gain.

## 9. Failure policy

- Permitted: deterministic transport retry for timeout/network/transient 5xx
  (429/5xx), max retries frozen (default 3).
- Forbidden: result-based retry, provider/model fallback, batch-size change
  based on results, dropping unfavorable tasks, silent exclusion.
- A permanent failure is recorded per the frozen ledger; the task is NOT
  silently excluded.

## 10. Required budgets/ledgers (frozen)

- Reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md + .json.
- Development token estimate (informational): 49,705 distinct units =
  21,870,401 unit tokens; 323 queries = 12,128 query tokens; combined
  21,882,529 tokens (Qwen3-Embedding-8B tokenizer, measured).
- Hard ceiling: total OpenRouter scientific cost <= $0.50; expected cost
  frozen before call 1; wall ceiling <= 120 min unless a longer ceiling is
  documented before call 1.

## 11. NOT EXECUTED — model unavailable

Bridge STOPPED BEFORE CALL 1 because the exact model could not be verified on
OpenRouter and no substitute is authorized. No Qwen3 embedding call was made.
Stage-5 confirmatory execution remains PAUSED and SEALED.