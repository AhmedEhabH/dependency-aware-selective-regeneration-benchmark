# Precision-Safe Acceptance Pilot — API Budget Freeze DRAFT (2026-09-18)

**Status:** FROZEN DRAFT — **NO API call is authorized by this document.**
**Tier:** T3 (DEVELOPMENT pilot; cost minimization is a first-class objective;
ceilings are safety limits, NOT spending targets).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Protocol:** `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md`

---

## 1. Purpose

Estimate the **smallest justified future API budget** for the single frozen
RANK → VERIFY → VARIABLE-ACCEPT DEVELOPMENT pilot, from the MEASURED Stage-4
cost distributions (300 real calls). This draft is a cost freeze, not an
execution order.

## 2. Measured Stage-4 cost basis (from the frozen 300-call ledger)

| Component | calls | mean total tok | p95 tok | mean cost | max cost |
|---|---:|---:|---:|---:|---:|
| Arm A verifier (djangoCMS) | 120 | 248.3 | 352 | $0.000086 | — |
| Arm A verifier (Saleor) | 120 | 252.1 | 356 | $0.000088 | — |
| Arm B semantic rank @cap40 (djangoCMS) | 30 | 658.4 | 906 | $0.000334 | $0.000939 |
| Arm B semantic rank @cap40 (Saleor) | 30 | 884.1 | 1,094 | $0.000448 | $0.001098 |

Budget basis: total 300 calls / 106,325 tokens / $0.0444 / 553.6 s.

## 3. Future-pilot call structure (frozen protocol)

Per task (60 tasks = 30 djangoCMS + 30 Saleor, fresh seed 20260919):

- **Arm A baseline** (frozen Route-B verifier): 1 call per (task, B), B ∈
  {1,3,5,10} → 4 calls/task → **240 calls**.
- **Arm B candidate**: 1 semantic-ranking call over the pool (cap 80) + 1
  strict-verification call over the top-K inspection set (K=10) → 2 calls/task
  → **120 calls**.
- **Arm C**: analytic references, 0 calls.

## 4. Expected cost (using Stage-4 measured rates)

| Component | calls | per-call reserve | expected tokens | expected cost |
|---|---:|---:|---:|---:|
| Arm A baseline | 240 | 300 tok / $0.00010 | ~60,000 | ~$0.021 |
| Arm B rank @cap80 | 60 | 1,500 tok / $0.00060 | ~60,000–72,000 | ~$0.024–0.031 |
| Arm B verify @K=10 | 60 | 400 tok / $0.00015 | ~18,000 | ~$0.007 |
| **Total** | **360** | — | **~138,000–150,000** | **~$0.052–0.059** |

Rank-stage reserve (1,500 tok / $0.00060) is sized at ~1.5–1.7× the measured
cap-40 p95 (906–1,094 tok) to cover the cap-40→80 prompt growth
(~7.4 · 40 ≈ +296 prompt tokens) and completion headroom. Expected wall time
< 30 min (Stage-4 was 553.6 s for 300 calls with comparable per-call latency).

## 5. Hard ceilings (frozen safety limits, NOT targets)

| Ceiling | Value | Rationale |
|---|---:|---|
| Calls | **400** | 360 expected + 11% margin |
| Tokens | **300,000** | 2.1× expected; identical ceiling to Stage-4 |
| Cost | **$0.15** | ~2.7× expected; far below Stage-4's $0.30 ceiling |
| Wall time | **60 min** | same as Stage-4 |

Cumulative per-call reservation ledger (fail-closed): a call is dispatched ONLY
if the reservation fits every ceiling; any ceiling breach stops BEFORE dispatch
and the pilot halts resumable.

## 6. Why this is the smallest justified budget

- The comparison baseline must run on the SAME fresh sample (cross-sample
  comparison is prohibited), so Arm A needs its full B-curve (240 calls) to
  provide the matched ORR/F1/precision curves and fold evidence the gate uses.
- The candidate requires exactly 2 calls/task (rank + verify); a single
  combined call would collapse the two-stage design the gate is testing.
- 60 fresh tasks (30/repo) is the minimum for the fold-stability and
  per-repo gate evidence at the same scale as Stage-4; a smaller sample cannot
  support 5-fold stability claims.
- No fallback provider, no result-based retries, no reruns — every call is
  budgeted once.

## 7. Exact user authorization sentence required before ANY call

> I authorize the precision-safe acceptance DEVELOPMENT pilot exactly as frozen
> in `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` under the budget in
> `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` — ≤400 calls /
> ≤300,000 tokens / ≤$0.15 / ≤60 min, qwen3-coder @ OpenRouter deepinfra/turbo,
> DEVELOPMENT only, sealed sets sealed, no result-based retries, no prompt
> tuning, no fallback provider, STOP at the preregistered gate.

No other wording authorizes a call. This mission made **zero** API calls.