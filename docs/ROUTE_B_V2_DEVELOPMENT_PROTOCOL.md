# Route B V2 — Development Protocol (robustness closure)

**Date:** 2026-09-17
**Tier:** T3 scientific development (ZERO new model calls for the ranker study)
**Precedence:** supersedes Route B V1's B=5-only framing; the primary scientific
object is the **budget curve** B ∈ {0,1,3,5,10}.
**Status:** FROZEN (pre-result, 2026-09-17) on DEVELOPMENT only.

---

## 1. Purpose

V1 showed a promising candidate-level signal (Classical CIA beats single-draw
Random at B=5) but the DEV_VALIDATION CI included zero. V2 does NOT attempt to
"make significance happen". It tests robustness with a better predeclared
analysis:
- an **analytic Random control** (hypergeometric expectation) instead of one
  lucky random draw;
- a full **budget curve** instead of a single B=5;
- **fold/stratum stability** instead of one split comparison.

## 2. Experimental object (frozen)

- **Candidate pool (per task):** files decoded/treated as Sparse PRESERVE /
  omitted candidates (i.e., candidate universe minus the Sparse write set).
- **Evaluation-only positive:** file is in the observed historical changed-file
  proxy AND Sparse omitted it (a Sparse-observed FN at file level).
- **Gold/proxy NEVER enters candidate features.** Candidate features use only
  parent-visible public inputs (BM25 / path-token / graph / intent overlap).
- **Task is the independent unit.** Candidate rows are nested within task; they
  are never treated as independent tasks.

## 3. Primary scientific object = budget curve

- B ∈ {0, 1, 3, 5, 10}; B=0 = Sparse alone (no reconsideration).
- Report **normalized sensitivity** B / |omitted_set| as a secondary view; do
  NOT replace raw B with normalized B.
- **Primary endpoint:** False-Negative Recovery Rate / Omission Recovery Rate
  @ B (per task, recovered Sparse-observed FNs within B / all Sparse-observed
  FNs for that task), presented as recovery effectiveness as a function of
  added inspection budget.
- **Secondary:** absolute recall gain; FNR reduction; fraction of Oracle@B gap
  closed; candidates inspected per recovered FN; final precision/F1 (safety
  metrics); runtime; index/build cost.

## 4. Random control — analytic expectation (frozen)

For ranking-only experiments the Random control is the **analytic
hypergeometric expectation**:

- Task t: N_t omitted candidates, M_t observed Sparse FNs among them, budget B.
- E[X_t] = B * M_t / N_t, with B clipped to N_t (expected recovered FNs).
- Omission recovery rate expectation = E[X_t] / M_t = min(B, N_t) / N_t.
- The comparison is the ranker's observed recovery vs this analytic expectation
  (per task), aggregated across tasks (task-level macro mean), with task-level
  bootstrap CI for the difference.
- Probability distributions / CI may be computed where useful (hypergeometric).
- Random repetitions are NEVER counted as independent tasks.

## 5. Primary anchors (per B)

- Sparse / B=0
- Analytic Random@B (hypergeometric expectation)
- BM25@B
- Path-token@B
- Graph/static@B
- Classical-CIA@B
- history/co-change@B IF parent-visible history is available
- ONE fixed simple hybrid (0.5 BM25 + 0.5 graph neighbor) — predeclared before
  V2 outcome inspection
- Oracle@B (best possible candidate selection given evaluation labels; ranking
  headroom only)
- InspectAll (actual/exhaustive reconsideration reference)

**Oracle@B != InspectAll.** Oracle@B = ranking headroom; InspectAll =
exhaustive reconsideration.

## 6. Robustness analysis (no new held-out data)

The old DEV_VALIDATION has already been inspected; it is NOT a new confirmatory
set. Use all current DEVELOPMENT as DEVELOPMENT and evaluate stability via
**predeclared grouped/task-level K-fold CV** (K=5, seeded) plus strata:
- effect direction across folds;
- bootstrap task-level CI;
- year/time strata;
- omitted-set-size strata;
- candidate-universe-size strata;
- proxy-size strata.

No learned model is required. No feature-weight tuning per fold.

## 7. Progression gate for an actual verifier (frozen)

A ranker family qualifies only if:
- positive direction across the majority of predeclared development folds;
- materially above analytic Random over a nontrivial portion of the B curve;
- not driven solely by omitted-set size / universe size / time cohort;
- leakage-free;
- practically meaningful recovery;
- exact rule frozen before verifier calls.

Do NOT demand p<0.05 in every fold; do demand stable effect + uncertainty
reporting. If the gate fails: freeze the negative result and stop verifier work.

## 8. Gates / audit

Six gates (Dataset / Input / Smoke / Dry Run / Integration / Metric) +
independent audit. Permanent checks: no gold feature; no future state/history;
task is the statistical unit; no candidate-row pseudo-replication; exposed old
cases not mislabeled confirmatory; INTERNAL_TEST/RESERVE untouched; exact
configs/hashes persisted; API ceilings fail-closed; no result-dependent reruns;
capability unavailable != numeric zero.

## 9. Outputs

- `reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md`
- `research/transparency/route_b_v2_results.json`
- gate + audit artifacts