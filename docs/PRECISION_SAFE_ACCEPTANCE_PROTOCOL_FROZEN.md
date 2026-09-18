# Precision-Safe Acceptance Protocol — FROZEN (DEVELOPMENT PILOT, 2026-09-18)

**Date:** 2026-09-18
**Tier:** T3 — prepared and **FROZEN but NOT executed**. ZERO new model/API calls
are made from this document. Execution requires the explicit user authorization
sentence in `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` (§7).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 0. Position in the research ladder

- Stage 1 (Sparse + Route-B): DONE. Stage 2 (FN anatomy): DONE — ranking
  bottleneck. Stage 3 (cheap quant ranking bridge): DONE, NEGATIVE
  (`CHEAP_RANKING_CLOSED_FOR_NOW`). Stage 4 (bounded semantic rerank/verify):
  DONE, NEGATIVE (`BOUNDED_SEMANTIC_NEGATIVE_FROZEN`, authorized 300-call
  pilot). Stage 5 (confirmatory): NOT reached.
- The Stage-4 failure anatomy (`reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md`)
  found: the semantic ranking carries real FN-recovery signal; the FP tail is
  an acceptance-layer failure, split across BOTH pool sources; the frozen
  verifier is uncalibrated for acceptance (8.6–14% approval precision) and was
  never assessed on reverse-1hop-only candidates; the pool cap C=40 loses
  10+29 FNs; 6/60 schema-invalid Arm-B calls received partial credit.
- This protocol is the **single, exactly-one next DEVELOPMENT pilot**: a
  precision-safe acceptance layer (RANK → VERIFY → VARIABLE ACCEPT) tested
  prospectively under a preregistered gate.

## 1. Scientific question (preregistered)

> Can a bounded precision-safe acceptance layer — semantic ranking of a
> deterministic expanded pool followed by a strict, machine-constrained
> second-stage verifier over a bounded inspection set, with a VARIABLE number
> of accepted additions (0..K) — retain useful semantic FN recovery while
> rejecting enough false-positive additions to preserve final file-level F1 on
> BOTH repositories (djangoCMS and Saleor), without a full repository agent?

## 2. Architecture (frozen)

```
Sparse first pass (frozen DEV predictions; ZERO new calls)
→ deterministic expanded candidate pool (Route-B top-10 ∪ reverse-1hop
  consumers; dedupe; pre-order desc bm25 then asc path; hard cap C=80)
→ bounded semantic ranking (1 call/task) over the pool
→ top-K inspection set (K=10) = first K of the semantic ranking
→ strict second-stage verifier (1 call/task) over the top-K inspection set
  (fixed-length boolean vector, candidate-ID constrained)
→ accepted additions = verifier-approved subset, ordered by semantic rank
→ final file set = Sparse write set ∪ accepted additions
```

Conceptual invariant (from the feasibility anatomy): **K (inspection budget) is
separate from the number of accepted additions (0..K).** The method is allowed
to inspect K candidates and add 0..K; exactly-K acceptance is rejected by
design.

## 3. Arms (compared on the SAME fresh task sample, matched semantics)

- **Arm A — frozen Route-B verifier (baseline).** The existing frozen protocol
  (`docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md`): per task, the frozen composite
  (BM25 + graph-neighbor) ranks omitted candidates; the verifier inspects top-B
  with **1 call per (task, B)**, B ∈ {1,3,5,10} → **4 calls/task**.
- **Arm B — RANK → VERIFY → VARIABLE ACCEPT (candidate).** Per task: 1 semantic
  ranking call over the pool (cap 80) + 1 strict verification call over the
  top-K inspection set → **2 calls/task**. The candidate's accepted additions
  are the verifier-approved subset, ordered by semantic rank; the reported
  ORR/F1 curve at B ∈ {1,3,5,10} uses the first B of that approved-and-ranked
  list (fewer than B additions are allowed when fewer are approved).
- **Arm C — references (no calls).** Analytic Random (hypergeometric
  expectation) and Oracle ranking.

Matched-budget rule: superiority claims require no material F1 regression under
the stricter cost accounting (Arm B: 2 calls/task vs Arm A: 4 calls/task).

## 4. Candidate pool construction (frozen)

Per task t (DEVELOPMENT only):

1. **Base** = Route-B composite top-10 (frozen `rank_composite(t)[:10]`).
2. **Add** the reverse-1hop downstream-consumer pool (candidates c with a
   directed edge c→s for some seed s; parent-visible).
3. **Deterministic dedupe + pre-order:** union deduped by path, ordered desc
   `bm25`, then asc `path` (identical to Stage-4).
4. **Hard pool cap C = 80** — **DEVELOPMENT-derived method design** (labeled as
   such): cap-40 excluded 10 (djangoCMS) + 29 (Saleor) FNs; cap-80 covers
   65.6% / 60.0% of sampled FNs at ~2× the ranking cost; cap-120 adds only
   +3% / +9% coverage. C=80 is the smallest cap with materially better coverage
   than Stage-4's C=40.
5. Forward-provider pool is NOT included (Stage-4 rationale preserved: low
   marginal FN gain at ~2× pool size).

## 5. Inspection set and acceptance semantics (frozen)

- **K = 10** — **DEVELOPMENT-derived method design**: recovery keeps growing
  through rank 10 (Saleor cumulative FNs 9→31; 5/5 positive folds at B=10)
  while cumulative candidate precision is already poor by rank 5; K=10 matches
  the Route-B B_max used in pool construction. K is the maximum number of
  semantically-ranked candidates the verifier may consider.
- **Acceptance:** the strict verifier returns one boolean per inspected
  candidate; **accepted additions = the approved candidates**, ordered by their
  semantic rank. The accepted count is variable in [0, K] per task; nothing
  forces exactly B accepted additions.

## 6. Model / provider / decoding (frozen)

- **Model:** qwen3-coder (Qwen3-Coder-480B-A35B-Instruct).
- **Provider/route:** OpenRouter, `deepinfra/turbo`, fallback OFF, same route
  discipline as the frozen Route-B verifier and Stage-4.
- **Temperature:** 0. **Completion cap:** 512.
- **Context payload (rank stage):** task intent text; the Sparse write set; the
  pool candidates as `C<nn>: <path> | <module/class hint>` in the frozen
  pre-order; the candidate universe size; instruction to rank the most
  plausibly affected first and to include only candidates it genuinely
  considers plausibly affected. **NO hidden proxy, NO gold, NO target/future
  info, NO repository-identity hint.**
- **Context payload (verify stage):** task intent text; the Sparse write set;
  the top-K inspection set as `C<nn>: <path> | <module/class hint>`; explicit
  instruction that approval means "the file is directly implicated by the
  change and should be added to the change set", and that the model MUST be
  conservative (approve only when genuinely warranted).

## 7. Schema (frozen; machine-constrained; engineering validity, not tuning)

**Rank stage** — `{"ranked": [{"candidate_id": "C03", "reason": "<short>"}, ...]}`:
- `candidate_id` constrained to the pool's ID **enum** in the JSON Schema
  (`response_format.json_schema`, `strict: true`) AND validated by the
  fail-closed parser against the pool (two independent layers).
- Uniqueness: an ID may appear at most once; duplicate → whole call invalid.
- `maxItems` = pool size.

**Verify stage** — `{"approve": [true, false, ...]}`:
- **Fixed-length boolean vector**, `minItems == maxItems == K` (10 booleans),
  in the presented candidate-ID order.
- Any length mismatch, non-boolean item, or parse failure → whole call invalid.

**Fail-closed, NO partial credit:** any schema-invalid call contributes **zero**
accepted additions for its task (fixes the Stage-4 partial-credit defect);
recorded, never retried. No result-based retries; no reruns; no fallback
provider; no prompt tuning after outcomes.

## 8. Leak guard (frozen)

- Prompts contain only parent-visible inputs: public intent, Sparse write set,
  candidate pool / inspection set (paths + module hints), universe size.
- No proxy path, no gold set, no future/target information, no repo identity,
  no rank position labels, no aggregate outcomes.
- Registered as `prompt_sha256` per call; audit A10 recomputes prompt hashes
  from a deterministic sample.

## 9. Task sampling — DEVELOPMENT, fresh and disjoint (frozen before calls)

- Seed **20260919** (new; distinct from Stage-4 seed 20260918).
- Eligibility predicate: `n_missed ≥ 1 AND omitted_size ≥ 5` (same as Stage-4).
- **Hard exclusion of all 60 Stage-4 sampled case_ids.**
- Stratified by repo, then by year/universe-size exactly as Stage-4
  (`stratified_sample`); **≤30 tasks per repo (≤60 total)**.
- Verified availability from frozen DEV records: 123 djangoCMS + 97 Saleor
  fresh eligible tasks (≥30 per repo). INTERNAL_TEST/RESERVE never touched; the
  spent djangoCMS INTERNAL_TEST is never reused as a fresh test.

## 10. Metrics (frozen)

Primary: macro ORR @ B ∈ {1,3,5,10}; candidate precision (accepted additions
that are FN); final file-level P / R / F1 / FNR of the accepted set; fraction
of Oracle-Add gap closed; calls / tokens / cost / latency / failure rate.
Safety: naive-union F1 must not materially regress vs Arm A at matched budget;
per-repo primary, NO cross-repo pooling as headline.

## 11. Preregistered stop gate (frozen BEFORE any call; reference B=5; BOTH repos)

| # | Condition | Threshold | Rationale |
|---|---|---:|---|
| c1 | candidate macro ORR > Arm A ORR + 0.05 | material recovery | same materiality as Stage-4; blocks marginal +0.02 claims |
| c2 | ≥ 3/5 seeded folds positive direction | fold majority | stability, not single-fold luck |
| c3 | candidate naive F1 ≥ Arm A F1 − 0.05 | no material F1 regression | forbids "ORR up, F1 down" |
| c4 | candidate acceptance precision ≥ Arm A candidate precision | measured precision | the precision-safe claim is measured, not asserted |
| c5 | leak-free (audited) | pass | no hidden target/gold |
| c6 | ≥ 90% schema-valid calls, zero partial credit | engineering validity | fail-closed semantics |
| c7 | within frozen ceilings; marginal cost justified | cost | cost minimization first-class |
| c8 | per-task delta distribution reported (descriptive) | transparency | heterogeneity |

Gate decision: PASS only if c1–c7 hold on BOTH repos (c8 descriptive). If the
gate fails → freeze the negative; do NOT tune prompt/schema/thresholds to chase
F1. A result where ORR rises but final F1 falls materially is a FAILURE by
definition.

## 12. Cost accounting and ceilings

Frozen in `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md`:
expected ≈ 360 calls / 130–170k tokens / ~$0.05–0.06 / <30 min; hard ceilings
400 calls / 300,000 tokens / $0.15 / 60 min; per-call reservation ledger
(fail-closed) sized from measured Stage-4 distributions.

## 13. What this protocol is NOT

- NOT a full repository agent; NOT unbounded semantic search; NOT a learned
  reranker; NOT a method-selection exercise on any confirmatory set.
- NOT a re-run of Stage-4 (different pool cap, different schema, different
  acceptance semantics, NEW verifier stage, fresh disjoint sample).
- The new strict verifier's performance is **UNTESTED by frozen records** (the
  frozen verifier never saw reverse-1hop-only candidates — explicit
  insufficiency). This pilot is a prospective test, not a confirmation.

## 14. Execution gate

Execution of this protocol requires the exact user authorization sentence in
`reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` §7. Until then this
document is frozen and ZERO calls are authorized.