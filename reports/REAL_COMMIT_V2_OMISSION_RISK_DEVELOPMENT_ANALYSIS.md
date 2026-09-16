# RealCommitImpactDataset-v2 — Omission-Risk Development Analysis (C4/C5)

**Date:** 2026-09-16
**Tier:** T3 (live Sparse development inference within authorized ceilings)
**Run evidence:** `research/omission-risk-feature-study-v1/v2_trainval/`
**Analysis:** `research/transparency/v2_omission_risk_analysis.json`

---

## 1. Run execution record

- **450-cell ceiling; 431 cells executed, 19 cells NOT run** (fail-closed
  budget stop at the 2.5M token ceiling; cost $0.87 < $1.00).
- 144 independent V2 development tasks (120 DEV_TRAIN requested, 117 actually
  reached + 27 DEV_VALIDATION reached); 143 tasks with 3 nested reps, 1 task
  with 2 reps.
- **430 / 431 valid; 1 failure** (a JSON-parse cell, recorded fail-closed;
  no replacement rerun).
- Provider/model: DeepInfra through OpenRouter, qwen/qwen3-coder, temp 0,
  cap 16384, Graph OFF, Sparse-v2 contract. Raw responses + sha256 persisted.
- Budget: **2,501,964 tokens (0.08% over the 2.5M ceiling from the final
  cell's post-check), $0.8728 cost** — the run stopped immediately after the
  check, before any further call.

## 2. Merged labels (v1 30 + v2 144 = 174 independent tasks)

- has_fn positive **155** / negative **19**; prevalence **89.1%**.
- Class-balance gate (>=10 each): **PASS** for a descriptive model.
- v1-only: 26/30 (86.7%); v2-only: 129/144 (89.6%).

## 3. C4 gate assessment

| Gate | Requirement | Result |
|---|---|---|
| 1 | >=10 pos / >=10 neg independent tasks | PASS (155/19) |
| 2 | predeclared feature/family above chance | **FAIL on replication** — see below |
| 3 | directionally stable DEV_TRAIN vs DEV_VALIDATION | FAIL (v1→v2 flip for bm25_zero_count) |
| 4 | not merely repository identity / proxy size / leakage artifact | **FAIL — universe-size confound** |
| 5 | — | — |

**Gate 2 / 3 / 4 (the decisive evidence):**

- The only v1 candidate signal was the retrieval-peakiness cluster
  (`bm25_zero_count` v1 AUROC 0.837, direction-consistent).
- **Within the new V2 cohort this does NOT replicate:** `bm25_zero_count`
  v2 AUROC **0.592** (inside the v2 random band [0.346, 0.649]).
- The pooled-174 analysis looked strong (33 features "above" the pooled band)
  but that is a **cohort/universe-size artifact**: V2 parent universes are
  systematically larger (up to 234 vs v1's 140–152), and graph-structure
  features (`graph_isolated_count`, `graph_conn_components`) correlate ≈0.99
  with candidate-universe size. Pooling v1+v2 conflates cohort membership with
  omission risk.
- Within-cohort replication (v1-only vs v2-only AUROC) for the predeclared
  candidates:

| feature | v1 AUROC | v2 AUROC | replicates? |
|---|---|---:|---:|---|
| bm25_zero_count | 0.837 | 0.592 | NO |
| bm25_nonzero_frac | 0.168 | 0.333 | (anti, stable direction) |
| bm25_relthresh_count | 0.173 | 0.302 | (anti, stable direction) |
| bm25_top1_top2_margin | 0.317 | 0.478 | NO |
| graph_p1_mean_dist_seeds | 0.615 | 0.679 | weak, universe-confounded |

## 4. Conclusion (C5 contingency pivot)

**Task-level risk modeling remains unseparable.** The V2 development enlargement
(n=144 new tasks) does NOT establish a reliable, replicable task-level risk
signal: the one v1 candidate does not replicate in V2, and the pooled signal is
a universe-size/cohort artifact. Per the frozen C4 rules:

- **NO multivariable RiskScorer is fitted.**
- The negative result is frozen as development evidence.
- The planned mechanism pivots to **Route B — candidate-level bounded omission
  verification** (see `docs/REAL_COMMIT_DATASET_V2_PROTOCOL.md` §Route B and the
  roadmap): use cheap first-pass candidate evidence + independent
  structural/history evidence to identify suspicious omitted candidates and
  verify only those under a hard budget, compared with always-verify and random
  matched-budget verification.

This is NOT a thesis failure; it is the pre-registered contingency.

## 5. Interpretation / honest bounds

- The run is a LIVE API result (431 calls), not a dry run.
- The class-balance gate passing at merged scale is necessary but not
  sufficient; the signal-quality and artifact gates fail.
- V2 universes are larger than v1; any future V2 modeling must stratify or
  covariate-adjust for candidate-universe size, and must use a balanced or
  negative-enriched development sample.
- The exposed v1 40 remain LEGACY_EXPOSED_V1; INTERNAL_TEST (80) and RESERVE
  (59) are untouched and never inferred.

## 6. Next action

- Continue with Route B design (candidate-level bounded verification), the
  print-ready proposal, the seminar outline, the living-review novelty audit,
  and the consolidated git/export.