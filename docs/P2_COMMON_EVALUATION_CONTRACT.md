# P2 Common Evaluation Contract

**Date:** 2026-09-17
**Tier:** T3 scientific documentation — frozen evaluation contract for the P2
adaptive-budget program (DEVELOPMENT only; ZERO API here)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** CONTRACT FROZEN. Applies to every P2 method from Nov 2026.

**Status statement (2026-09-17):** P2 is **NOT complete**; it is a development
research program, not a proven contribution. Fixed Route B is CONFIRMED
(djangoCMS INTERNAL_TEST) and is NOT retuned. Every P2 method is evaluated
under this contract on DEVELOPMENT data only (djangoCMS DEV + Saleor DEV);
the opened djangoCMS INTERNAL_TEST is permanently spent, and Saleor
INTERNAL_TEST stays sealed.

---

## 1. Purpose

Every P2 adaptive-budget method must be evaluated under ONE common contract so
cross-method comparison is fair and matched-budget. No method is selected by
F1 alone.

## 2. Data

- **Development:** djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks) — the
  SAME frozen run records + bundles used for Route-B V2 / transfer.
- **Forbidden:** the opened djangoCMS INTERNAL_TEST (permanently spent); Saleor
  INTERNAL_TEST (sealed; reserved for a possible future P2 confirmation).
- Method code receives ONLY parent-visible public inputs; the hidden proxy
  enters evaluation only.

## 3. Anchors (every P2 method compared against)

| Anchor | Definition |
|---|---|
| Fixed B={1,3,5,10} | frozen composite ranker, fixed budget per task |
| Analytic Random | hypergeometric E[X]=B·M/N (B clipped to N) |
| BM25-only ranking | normalized BM25 ranking, fixed B |
| Frozen BM25+Graph-Neighbor Composite | the CONFIRMED primary ranker, fixed B |
| Oracle | ranking headroom (proxy-aware, evaluation only) |
| InspectAll | exhaustive reconsideration |

## 4. Primary P2 question

> Can an adaptive policy achieve comparable or better omission recovery than the
> best fixed-B operating point with lower expected verification cost?

## 5. Candidate P2 endpoints (all reported; no F1-only selection)

- ORR / FNRR @ realized budget (per task and pooled macro)
- verifier calls / task
- tokens / task
- cost / task
- fraction of Oracle gap closed
- Pareto dominance (recovery vs cost) over the fixed-B curve
- over-allocation error (budget spent beyond the point of no added recovery)
- under-allocation error (recovery lost by stopping too early)
- robustness across repository and task-size strata (omitted-size /
  universe-size / proxy-size buckets)

## 6. Evaluation mechanics

- **Matched budget:** each P2 policy reports recovery at its REALIZED budget
  (which may differ per task); compare against the fixed-B anchor at the same
  realized-cost point and against the fixed-B curve.
- **Task-level aggregation:** task is the independent unit; nested candidate
  rows are not pseudo-replicates; task-level bootstrap CIs for differences vs
  anchors (seeded, fixed seed).
- **No tuning on outcomes:** τ constants and rule structure are pre-registered
  before evaluating any P2 method on DEV; the common harness computes features
  and endpoints deterministically.
- **Leakage rule:** features use parent-visible inputs only; hidden proxy is
  evaluation-only; no gold enters any policy.

## 7. Output format (per P2 method)

1. Exact rule/pseudocode + pre-registered constants.
2. Task/input/output definition.
3. Adaptation variable + objective/cost function.
4. Fixed vs adaptive budget; learned vs deterministic stopping.
5. Realized-budget curve (recovery vs cost) vs anchors.
6. Pareto position + over/under-allocation errors.
7. Robustness by repo + strata.
8. Implementation effort + scientific value + decision (implement/keep/
   reject/defer) with reason.

## 8. Decision rule (frozen)

- A P2 candidate is **scientifically justified** only if it Pareto-dominates
  (or matches recovery at lower cost than) the best fixed-B operating point on
  BOTH repositories (DEV), with task-level uncertainty accounting, and the
  advantage is not a size/confound artifact.
- At most 1–2 candidates may proceed to pre-registration; their final
  evaluation uses the still-sealed Saleor INTERNAL_TEST **only if justified**
  and pre-registered; otherwise P2 closes NEGATIVE.

## 9. Relationship to the harness

The P2 evaluation uses the same public-case + hidden-proxy separation as the
frozen `benchmark.harness` seams (DatasetAdapter / Ranker / BudgetPolicy /
Evaluator). P2 policies are `BudgetPolicy` implementations that consume the
frozen candidate features (normalized BM25, binary graph-neighbor, rank
percentiles, dispersion, task-size proxies) and emit a per-task verification
budget + stop decision. No new leakage surface.

## 10. Status

**CONTRACT FROZEN** — ready for the Nov 2026 start. ZERO API in this document.