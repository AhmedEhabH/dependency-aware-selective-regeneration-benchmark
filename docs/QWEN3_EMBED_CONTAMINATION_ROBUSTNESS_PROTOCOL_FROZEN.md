# Qwen3-Embedding Contamination-Robustness Protocol — FROZEN (2026-09-19)

**Tier:** T3 (new evaluation-strategy family: INDEPENDENT DENSE-RETRIEVAL
CONTROL).
**Status:** **FROZEN BUT NOT FULLY EXECUTED — STOPPED at the determinism
probe.** P71 recorded the original (defective) probe; P72 confirmed the
availability-probe defect (the model IS in the dedicated embeddings catalog,
pinned DeepInfra $0.01/M). The determinism probe (§12.8) was then executed:
cosine drift ~1.0e-4 with a file-level B=5 set flip on 1/5 sampled DEVELOPMENT
tasks → per the frozen criterion this is material enough to destabilize the
operating-point ranking → **STOP BEFORE THE FULL SCIENTIFIC RUN** (P73). The
bridge remains `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE` (root cause:
material embedding nondeterminism at the file-level margin). Technical probes
only (~$0.023 spend); no full scientific Qwen result was produced.
**Mission:** contamination-robustness bridge (scope change; Stage-5
confirmatory PAUSED).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Scientific spend to date:** ~$0.023 (technical probes only), 0 full-run
calls.

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
**SUPERSEDED by P72 (the availability probe was defective; the model IS
available in the dedicated embeddings catalog).**

## 12. EXECUTION CLARIFICATIONS (2026-09-19, frozen BEFORE call 1)

The user authorized resumption after the availability-probe defect was
confirmed (P72; the model IS in the dedicated embeddings catalog). The
following API-specific details were genuinely unspecified and are now frozen
ONCE, before any target-aware call:

1. **Availability (corrected):** `GET https://openrouter.ai/api/v1/embeddings/models`
   lists 33 embedding models; **`qwen/qwen3-embedding-8b` is present**
   (context 32,768; HF `Qwen/Qwen3-Embedding-8B`). Scientific calls use
   `POST https://openrouter.ai/api/v1/embeddings`.
2. **Provider pin:** **DeepInfra** (documented $0.01/M prompt; context 32,768;
   100% 5-min uptime; consistent with the project's prior frozen DeepInfra
   route). Request carries
   `"provider": {"order": ["DeepInfra"], "allow_fallbacks": false}` — routing
   pinned, fallback disabled. Nebius ($0.01/M) is the recorded alternative;
   no provider switch based on scientific output.
3. **Price (documented):** $0.01 per 1M tokens (prompt). Expected full-run
   cost = 21,882,529 / 1,000,000 × $0.01 = **$0.2188**. Hard ceiling $0.50.
   If the exact full-run projected charge exceeds $0.50 → STOP before call 1.
4. **Input semantics:** `input` = array of plain strings (code-unit texts for
   the corpus; parent-visible intent texts for queries). NO instruction prefix
   is added by us (the generic OpenRouter embeddings endpoint takes raw text;
   the frozen benchmark query text is used verbatim). Batch size 64 (frozen;
   ~28k tokens/request < DeepInfra 32,768 context).
5. **Embedding dimension / normalization:** vectors are L2-normalized on both
   sides and scored by dot product (= cosine), identical to the SweRank
   adapter. This rule is frozen regardless of whether the provider returns
   pre-normalized vectors.
6. **Numeric gate clarification (primary replication requirement on BOTH
   repos at B=5, vs Frozen Route-B):**
   - A. `Delta F1 > 0` AND paired-bootstrap `95% CI lower bound for Delta F1 > 0`;
   - B. `Delta Recall >= -0.02`;
   - C. `Delta FNR <= +0.02`;
   - D. `Delta Precision >= -0.02`;
   - E. >= 3/5 seeded grouped folds with `Delta F1 >= 0`;
   - F. zero target leakage;
   - G. technically valid deterministic execution (>=95% valid requests after
     permitted transport retries; determinism probe drift below a
     rank-stable threshold);
   - H. total cost <= frozen $0.50 ceiling.
   Sparse is reported separately; a Qwen result that beats Route-B but stays
   below Sparse is described as a `dense-ranking/recovery improvement`, NOT
   `complete final-set superiority`.
7. **Wall-time ceiling:** frozen 180 minutes (extended from 120 min, documented
   before call 1: ~783 batched embedding requests × provider latency; cost
   ceiling remains the hard stop).
8. **Determinism probe:** ~200 already-exposed code units embedded twice with
   identical input/provider/model/settings; report max cosine drift; if drift
   could plausibly change ranking ties, STOP and report (technical freeze, not
   scientific negative).
9. **Input-preparation clarification (frozen after the first transport
   validation error, BEFORE any target-aware call):** whitespace-only code
   units are excluded (the endpoint rejects empty strings with HTTP 400). This
   is a deterministic text-preparation rule with no target influence; the
   affected units would contribute no discriminative signal (empty text).