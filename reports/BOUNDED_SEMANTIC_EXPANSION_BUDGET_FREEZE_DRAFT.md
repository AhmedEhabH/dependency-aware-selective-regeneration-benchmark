# Bounded Semantic Expansion — API Budget Freeze DRAFT (NO CALLS)

**Date:** 2026-09-18
**Tier:** T3 — projection ONLY; **ZERO new model/API calls made**.
**Status:** DRAFT budget for the next authorized DEVELOPMENT pilot. This document
does not authorize any call.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 0. Basis (frozen records only; no new inference)

- Route-B verifier pilot (`reports/ROUTE_B_VERIFIER_PILOT_REPORT.md`): 30 calls,
  6,748 tokens, $0.0023 (≈225 tokens/call, ≈$0.000077/call; qwen3-coder @
  deepinfra/turbo, temp 0, cap 512).
- Measured verifier cost model (`src/benchmark/p2/cost_model.py`):
  `prompt_tokens(B) ≈ 204.51 + 7.40·B`; `api_cost(B) ≈ 0.000065 + 0.000005·B`
  (least-squares fit over the 320 frozen confirmatory verifier calls).
- djangoCMS confirmatory budget freeze (`reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md`):
  per-call reservation rule (p99-based), fail-closed cumulative ledger.
- Frozen pricing (DeepInfra-through-OpenRouter): **$0.30 / $1.00 per 1M
  prompt/completion tokens**.

## 1. Frozen pilot scope (DEVELOPMENT only)

- Pool construction per `docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md`
  §3: Route-B top-10 ∪ reverse-1hop consumers, deduped, deterministic pre-order,
  hard pool cap **C = 40**.
- Sampling (seeded 20260918): **≤30 tasks per repo (djangoCMS DEV 174 + Saleor
  DEV 149) with ≥1 Sparse FN and omitted ≥ 5 → ≤60 tasks**.
- Arm A (Route-B verifier): 4 calls/task (B∈{1,3,5,10}) → **≤240 calls**.
- Arm B (expanded-pool bounded rerank/verify): **1 call/task → ≤60 calls**.

## 2. Per-call token/cost projection (cap-40 pool)

| Quantity | Formula | At |p|=40 |
|---|---:|---:|
| prompt tokens | 204.51 + 7.40·\|pool\| | **~500.5** |
| completion tokens | cap 512 (worst case) | **~512** |
| total tokens / call | ~1,012 | **~1,012** |
| api cost / call | 0.000065 + 0.000005·\|pool\| (~$0.00025) or tokens-based | **~$0.00025–0.00030** |

## 3. Projected totals (Arm B — the candidate arm)

| Quantity | Expected (60 tasks × 1 call) | Conservative ceiling |
|---|---:|---:|
| Calls | **60** | 60 (no retries) |
| Tokens | 60 × 1,012 ≈ **60,720** | 60 × 1,500 = **90,000** |
| USD | 60 × 0.00028 ≈ **$0.017** | 60 × 0.00040 = **$0.024** |
| Latency | 60 × ~2–5 s ≈ 2–5 min | ≤ 15 min |

## 4. Projected totals (Arm A — frozen Route-B verifier reference)

| Quantity | Expected (60 tasks × 4 calls) | Conservative ceiling |
|---|---:|---:|
| Calls | **240** | 240 |
| Tokens | 240 × ~225 ≈ **54,000** | 240 × 400 = **96,000** |
| USD | 240 × 0.000077 ≈ **$0.018** | 240 × 0.00015 = **$0.036** |

Note: Arm B and Arm A are within the same order of magnitude on tokens/cost at
this pilot scale; the scientific comparison is on recovery/F1 quality, and cost
is a secondary reported axis.

## 5. Proposed conservative hard stop (frozen)

| Quantity | Hard ceiling |
|---|---:|
| Calls | **300** (60 Arm B + 240 Arm A) |
| Tokens | **300,000** |
| USD | **$0.30** |
| Latency | **60 min** wall-clock |
| Failure rate | stop/report if >10% of Arm B calls fail closed |

Fail-closed per-call reservation ledger (reserve before dispatch: Arm B
reservation 1,500 tokens / $0.00040; Arm A reservation 400 tokens / $0.00015);
the run stops BEFORE dispatching any call that would breach a ceiling.

## 6. Constraints

- DEVELOPMENT only; djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE sealed;
  spent djangoCMS INTERNAL_TEST never reused as a fresh test.
- No result-dependent reruns; no prompt/schema tuning after outcomes.
- No claim of success if ORR rises but final F1 falls materially.

## 7. EXACT USER AUTHORIZATION REQUIRED to execute the DEVELOPMENT pilot

The pilot described in `docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md`
is **NOT executed** by this mission. To run it, the user must explicitly
authorize ALL of the following:

1. **Budget ceiling:** ≤300 total model calls, ≤300,000 total tokens, ≤$0.30
   USD, ≤60 min wall-clock, fail-closed reservation ledger (Section 5 above).
2. **Model/route:** qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) via OpenRouter
   (deepinfra/turbo preferred, fallback OFF), temperature 0, completion cap 512.
3. **Data boundary:** DEVELOPMENT only (djangoCMS DEV 174 + Saleor DEV 149),
   sampled ≤30 tasks/repo with ≥1 Sparse FN and omitted ≥5, seeded 20260918;
   INTERNAL_TEST/RESERVE sealed.
4. **Protocol/schema:** the frozen protocol and strict JSON schema from
   `docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md` (pool cap 40,
   fail-closed semantics, no result-based retries).
5. **Arms:** Arm A (Route-B verifier, 4 calls/task) + Arm B (expanded-pool
   bounded rerank/verify, 1 call/task) + analytic references; matched-budget
   comparison; pre-registered stop rule.

**Authorization sentence (if the user agrees):**
> "Authorize the bounded semantic rerank/verify DEVELOPMENT pilot under the
> frozen protocol + budget draft (≤300 calls / ≤300,000 tokens / ≤$0.30 / ≤60
> min, qwen3-coder, DEV only, sealed sets sealed)."

Without that explicit authorization, NO call is made.