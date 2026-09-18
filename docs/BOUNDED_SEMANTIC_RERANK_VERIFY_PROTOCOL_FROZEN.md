# Bounded Semantic Rerank/Verify Protocol — FROZEN (PREPARED, NOT EXECUTED)

**Date:** 2026-09-18
**Tier:** T3 — prepared but **NOT executed** in this mission (ZERO new model/API calls).
**Status:** FROZEN protocol DRAFT for the next authorized DEVELOPMENT pilot. No call is
made from this document. Execution requires explicit user authorization (see the
companion `reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 0. Position in the research ladder

The quantitative-structural ranking bridge (this mission, Section 2) closed with
**CHEAP_RANKING_CLOSED_FOR_NOW**: no transparent count/normalized formula
materially beats frozen Route-B at matched budget on BOTH repos (best: R1
BM25+RevSupport, djangoCMS +0.034 / Saleor −0.020 at B=5). The dominant remaining
loss is therefore still **ordering/acceptance inside an already useful candidate
pool**. This protocol defines the middle layer: a **bounded semantic
decision layer over a small deterministic pool**, deliberately NOT a full
repository agent, using the **existing frozen verifier protocol
(`docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md`)** as the starting point.

## 1. Primary scientific question

Does bounded semantic reasoning improve **ordering/acceptance within a
deterministically high-coverage pool** enough to convert the measured
availability headroom (reverse-1hop 0.558/0.724; UNION_ALL 0.725/0.870 @K=5)
into realized FN recovery and better final F1 — without full repository
agentic search?

## 2. Arm design (compared at MATCHED inspection + API budget)

- **Arm A — Frozen Route-B verifier (baseline):** existing frozen protocol
  (`docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md`): per task, the frozen composite
  (BM25 + graph-neighbor) ranks omitted candidates; the verifier inspects top-B
  with **1 call per (task, B)**, B∈{1,3,5,10} → **4 calls/task**.
- **Arm B — Expanded-pool bounded semantic rerank/verify (candidate):** per
  task, a **single bounded call over the deterministic expanded pool**; the
  verifier returns a **reranked/approved subset**; top-B of that output is the
  addition at each B. → **1 call/task**.
- **Arm C — references:** Analytic Random (hypergeometric expectation) and
  Oracle ranking (perfect order) computed deterministically; no calls.

Matched-budget rule: a reported comparison at budget B uses the **same B as the
number of accepted additions**; API cost is accounted per arm (Arm A 4 calls
per task vs Arm B 1 call per task at the same B curve) and reported as a
secondary axis — superiority claims require no material F1 regression under
the stricter cost accounting.

## 3. Candidate-pool construction (frozen)

Per task t (DEVELOPMENT only):

1. **Base pool** = frozen Route-B composite top-B_max ranked omitted candidates,
   B_max = 10.
2. **Add** the **high-coverage reverse-1hop downstream-consumer pool**
   (candidates c with a directed edge c→s for some seed s; parent-visible).
3. **Forward provider pool is NOT included by default**: DEV evidence
   (`reports/FN_SOURCE_SPECIFIC_RECALL_CEILINGS.md`) shows forward-1hop adds
   only +12/+20 FNs over reverse at K=5 while roughly doubling the pool; a
   frozen optional sub-arm may enable it ONLY after a separate DEV
   non-redundancy check. This sub-arm is NOT part of the default frozen pilot.
4. **Deterministic dedupe + tie rules:** union dedupe by path; the pool is
   pre-ordered by **frozen deterministic pre-score** (desc `bm25`, then asc
   path) before semantic ranking, so the pool order is reproducible even before
   any model call.
5. **Hard pool cap per task:** `min(len(pool), C)` with **C = 40** (frozen).
   Tasks whose pool exceeds the cap are truncated to the first 40 candidates in
   the deterministic pre-order. Rationale: saleor DEV reverse-1hop pools are
   large (mean queue ~4–9 within budget, total pool up to several hundred);
   C=40 keeps the semantic call bounded and the per-call token ceiling
   conservative while covering the high-value candidates (Route-B top-10 ∪
   top-consumers by BM25).

## 4. Semantic layer (frozen; reuses the existing verifier)

- **Model/provider/route:** qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) via
  OpenRouter, deepinfra/turbo preferred, fallback OFF (same route discipline as
  the frozen Route-B verifier pilot).
- **Temperature:** 0. **Completion cap:** 512.
- **Context payload (per call):** task intent text; the Sparse write set; the
  expanded pool candidates (path + one-line module/class hint, in the frozen
  pre-order); the candidate universe size; explicit instruction that the pool
  is a bounded pre-filtered set and the model should reorder/accept the most
  plausible change-relevant files. NO hidden proxy, NO gold, NO target/future
  info, NO repository-identity hint.
- **Output schema:** strict JSON — either (a) an ordered reranked list of
  `{path, reason}` of length ≤ pool size, or (b) `{reconsider: bool}` per
  candidate. The exact single schema is frozen at pilot registration; strict
  JSON-array/object decode; non-parseable → **fail-closed failure** (recorded,
  never retried, no partial credit).
- **Admission rule (frozen, both schema variants):** the final addition at
  budget B = the first B pool candidates the model ranks/approves (respecting
  the pool cap), deduped against the Sparse write set.

## 5. Fail-closed semantics and no-result-based-retry

- Non-parseable output, schema-invalid JSON, transport failure, or
  finish_reason=length → **FAILED cell** (fn contributed, no partial credit).
- **No retries based on result; no reruns; no result-dependent resampling.**
- A task with no succeeded Sparse repetition is EXCLUDED (frozen Route-B rule).

## 6. Token / cost / latency ceilings

Projected in `reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`:
- per-call prompt ≈ `204.5 + 7.4·|pool|` (measured verifier cost model) ≤
  ~500 prompt tokens at cap 40; completion cap 512 → ≤ ~1,100 total
  tokens/call;
- per-call reservation rule (fail-closed) with a cumulative ledger;
- hard ceilings: calls / tokens / USD / latency are frozen there.

## 7. DEVELOPMENT task sampling (pilot)

- Stratified, seeded (20260918): from djangoCMS DEV (174) + Saleor DEV (149),
  sample tasks with ≥1 Sparse FN and omitted set ≥ 5, stratified by repo and by
  year/universe-size strata; **≤30 tasks per repo (≤60 total)**.
- INTERNAL_TEST and RESERVE are never touched; djangoCMS INTERNAL_TEST (spent)
  is never reused as a fresh test.

## 8. Primary + safety metrics

Primary:
- Omission Recovery Rate (ORR) @ B∈{1,3,5,10} (macro over tasks).
- Final P / R / F1 / FNR of the accepted set (file-level).
- Fraction of Oracle-Add gap closed.
- calls / tokens / cost / latency / failure rate.

Safety:
- naive-union F1 must not materially regress vs Route-B at matched budget
  (`>0.05` F1 drop = material);
- candidate precision (fraction of accepted that are FN) reported;
- per-repo primary; no cross-repo pooling headline.

## 9. Stop rule

- Run stops fail-closed at any ceiling breach (calls/tokens/cost) BEFORE
  dispatch.
- Analysis stops at a **pre-registered gate**: Arm B must (1) materially
  improve matched-budget ORR over Arm A on both repos, (2) positive direction
  in a majority of frozen folds, (3) not materially worsen final F1, (4) be
  leak-free, (5) justify its marginal API cost. If the gate fails → freeze the
  negative; do NOT tune the prompt/schema to chase F1.

## 10. What this is NOT

- NOT a full repository agent; NOT an open-ended semantic search; NOT a
  learned reranker; NOT a method-selection exercise on any confirmatory set.
- No claim of success if ORR rises but final F1 falls materially.

## 11. Authorized-only execution

This document **prepares** the protocol only. The exact user authorization
needed to execute the DEVELOPMENT pilot is stated at the end of
`reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md` (Section 7).