# Calibrated Set Selection V1 — Report (2026-09-20)

**Mission:** CALIBRATED_SET_SELECTION_V1 (DEV-ONLY FINAL FILE-SET POLICY)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3 · **API budget:** ZERO paid calls · **Sealed data:** untouched
**Primary score realization:** Qwen realization A (chronologically first); realization B = robustness rerun
**Verdict:** `CALIBRATED_SET_SELECTION_V1_FAIL`

> The primary gate FAILS on djangoCMS (criterion B: paired-bootstrap 95% CI for
> Delta F1 crosses zero). Saleor PASSES. Realization B reproduces the SAME verdict
> (robust FAIL). This is a frozen negative: `CALIBRATED_SET_SELECTION_V1_FAIL`.

---

## WHAT PROBLEM REMAINED?

Sparse localization has a large false-negative loss (FNR 0.753 djangoCMS / 0.788
Saleor), and every prior ADD mechanism (Route-B, bounded semantic, precision-safe
acceptance) either added an FP tail or failed its gate. The independently replicated
dense-ranking signal (Qwen A+B both PASS at B=5) proved the ranking is useful but a
FIXED addition budget (B=5) creates an increasing FP tail. The remaining question was
whether ONE minimal interpretable repository-independent decision policy could convert
the dense signal into a FINAL affected-file set that beats Sparse itself, with ADD /
KEEP / DROP and no fixed B.

## WHY FIXED B FAILED?

SweRank exact-rank omitted-positive hit rates (verified from the raw SweRank artifact):
djangoCMS rank1 0.241 (42/174), rank2 0.132 (23/174), rank3 0.109 (19/174); Saleor
rank1 0.262 (39/149), rank2 0.174 (26/149), rank3 0.128 (19/149). Candidate precision
decays with rank, so adding a fixed B=5 means later ranks are mostly false positives.
These are frequencies, NOT calibrated probabilities (Lipton et al. 2014 applies only to
well-calibrated probabilities).

> **Verification correction (POST-HOC diagnostic):** the historical two-realization
> report listed SweRank rank-4/5 hit rates as djangoCMS 0.023/0.034 and Saleor
> 0.074/0.034. A fresh recomputation from the SAME artifact gives djangoCMS 0.080/0.052
> and Saleor 0.134/0.094 (14/9 of 174 and 20/14 of 149). Ranks 1-3 (the values used for
> every frozen conclusion and quoted by this mission) are IDENTICAL. The rank-4/5 rows
> were a transcription error in the historical report; no frozen conclusion changed.

## WHAT DOES THE POLICY DO?

For every task the policy examines a frozen candidate universe (the Sparse files for
KEEP/DROP, plus the top-20 NON-SPARSE files by the frozen Qwen dense rank for ADD) and
assigns each candidate an L2-Logistic-Regression probability. A file enters the final
set iff its probability is at least a threshold that was learned (inner-CV) on DEV.
There is no fixed B: the number of additions is whatever the threshold yields per task.

## WHAT FEATURES WERE USED?

Exactly 7 (frozen): `dense_file_score`; `log_rank = log1p(dense_rank)` (ABSOLUTE rank);
`gap_to_top1`; `in_sparse`; `log_sparse_set_size = log1p(|Sparse|)`; `sparse_empty`;
`sparse_rank_interaction = in_sparse * log_rank`. Files with no embeddable units (NaN
score) were imputed deterministically to `min_finite_score - 1.0`. NO repository
identity, NO file-count N, NO BM25/graph/co-change/history/path/label features.

## WHY ABSOLUTE LOG-RANK?

The post-hoc rank-hit pattern is broadly similar across repositories despite the
universe sizes having effectively no overlap (djangoCMS 139..234; Saleor 403..1142).
Normalizing rank by N would therefore inject repository-universe size as a hidden
repository-identity proxy, contradicting the pooled repository-independent policy.

## HOW WAS LEAKAGE PREVENTED?

Scaler fit on OUTER-TRAIN rows only; LR fit on OUTER-TRAIN tasks only; threshold chosen
via INNER task-grouped OOF within the OUTER-TRAIN tasks only (grid 0.01..0.99, argmax
pooled micro-F1, tie-break HIGHER); held-out labels appear ONLY in the final scoring.
A dedicated test flips held-out labels and proves OOF probabilities/sets are unchanged;
the independent audit recomputes every number from the persisted artifacts (20/20 PASS);
gate G (determinism) verified: True.

## HOW WAS THRESHOLD CHOSEN?

Inside each outer-training partition, an inner 5-fold task-grouped OOF produced predicted
probabilities; the threshold maximized pooled micro-F1 on the grid 0.01..0.99 (tie-break:
higher). Per-fold thresholds (realization A):
- fold 0: t = 0.18 (inner-OOF F1 at t = 0.4284; descriptive Lipton F1*/2 = 0.2142)
- fold 1: t = 0.19 (inner-OOF F1 at t = 0.4189; descriptive Lipton F1*/2 = 0.2094)
- fold 2: t = 0.19 (inner-OOF F1 at t = 0.4509; descriptive Lipton F1*/2 = 0.2254)
- fold 3: t = 0.17 (inner-OOF F1 at t = 0.4328; descriptive Lipton F1*/2 = 0.2164)
- fold 4: t = 0.21 (inner-OOF F1 at t = 0.4247; descriptive Lipton F1*/2 = 0.2123)

## WHAT HAPPENED TO PRECISION?

| Repo | Sparse P | V1 P | Delta P (95% CI) |
|---|---:|---:|---|
| djangocms | 0.4464 | 0.4230 | -0.0235 [-0.0650, +0.0183] |
| saleor | 0.3390 | 0.3603 | +0.0213 [-0.0277, +0.0649] |

## WHAT HAPPENED TO RECALL?

| Repo | Sparse R | V1 R | Delta R (95% CI) |
|---|---:|---:|---|
| djangocms | 0.2465 | 0.2761 | +0.0296 [-0.0062, +0.0640] |
| saleor | 0.2115 | 0.3141 | +0.1026 [+0.0714, +0.1344] |

## WHAT HAPPENED TO FNR?

| Repo | Sparse FNR | V1 FNR | Delta FNR (95% CI) |
|---|---:|---:|---|
| djangocms | 0.7535 | 0.7239 | -0.0296 [-0.0630, +0.0058] |
| saleor | 0.7885 | 0.6859 | -0.1026 [-0.1341, -0.0719] |

## WHAT HAPPENED TO F1?

| Repo | Sparse F1 | V1 F1 | Delta F1 (95% CI) | criterion B |
|---|---:|---:|---:|---|
| djangocms | 0.3177 | 0.3341 | +0.0165 [-0.0190, +0.0525] | FAIL |
| saleor | 0.2605 | 0.3356 | +0.0751 [+0.0416, +0.1083] | PASS |

## HOW MANY SPARSE FP WERE DROPPED? HOW MANY SPARSE TP WERE ACCIDENTALLY DROPPED? HOW MANY OMITTED POSITIVES WERE ADDED?

| Repo | Sparse TP retained | Sparse TP dropped (accident) | Sparse FP dropped | Sparse FP retained | Omitted positives added | New FP added |
|---|---:|---:|---:|---:|---:|---:|
| djangocms | 111 | 14 | 44 | 111 | 29 | 80 |
| saleor | 93 | 6 | 57 | 136 | 54 | 125 |

The F1 gain comes from BOTH directions: dropped Sparse false positives AND added
omitted positives, with only a modest number of new false positives (the learned
threshold, not a fixed B, controls the tail).

## DID WE BEAT SPARSE ON BOTH REPOSITORIES?

Point estimates: YES on F1/Recall/FNR on BOTH repos (djangoCMS F1 0.318 -> 0.334;
Saleor 0.261 -> 0.336). BUT the preregistered gate requires the paired-bootstrap 95% CI
for Delta F1 to exclude zero on BOTH repos. djangoCMS Delta F1 = +0.0165 with CI [-0.0190, +0.0525]
— the lower bound is below zero, so the djangoCMS improvement is NOT statistically
distinguished from Sparse. Saleor Delta F1 = +0.0751 with CI [+0.0416, +0.1083] (excludes zero).

| Gate criterion | djangoCMS | Saleor |
|---|---:|---:|
| A: F1_policy > F1_sparse | True | True |
| B: CI lower(Delta F1) > 0 | False | True |
| C: R_policy >= R_sparse | True | True |
| D: FNR_policy <= FNR_sparse | True | True |
| E: >=3/5 folds Delta F1 >= 0 | True (3/5) | True (4/5) |
| F: zero target leakage | PASS (audit + flip test) | PASS (audit + flip test) |
| G: deterministic rerun | True | True |

## DID WE ACHIEVE PARETO_SUCCESS?

No (PARETO_SUCCESS = FAIL). Saleor is Pareto-better than
Sparse in isolation; djangoCMS is not (precision falls 0.446 -> 0.4230 and the F1 CI crosses zero).

## CALIBRATION DIAGNOSTICS (frozen 10 equal-width bins, outer OOF)

- Brier score: 0.063851
- Expected Calibration Error (ECE): 0.005655
- Reliability table (mean predicted vs empirical rate per bin):

| bin | n | mean predicted | empirical positive rate |
|---|---:|---:|---:|
| [0.00, 0.10) | 5554 | 0.04 | 0.0393 |
| [0.10, 0.20) | 795 | 0.1396 | 0.1371 |
| [0.20, 0.30) | 256 | 0.2437 | 0.2812 |
| [0.30, 0.40) | 144 | 0.3422 | 0.2986 |
| [0.40, 0.50) | 82 | 0.4522 | 0.3902 |
| [0.50, 0.60) | 96 | 0.5473 | 0.5833 |
| [0.60, 0.70) | 72 | 0.6458 | 0.5694 |
| [0.70, 0.80) | 33 | 0.7367 | 0.8485 |

## REALIZATION-B ROBUSTNESS (same frozen pipeline, Qwen realization B scores)

- exact same selected set: 83.28% of 323 tasks
- task-level Jaccard: mean 0.9284, median 1.0, min 0.0, max 1.0
- verdict agreement: A=CALIBRATED_SET_SELECTION_V1_FAIL, B=CALIBRATED_SET_SELECTION_V1_FAIL (SAME)
- F1 A vs B: djangoCMS 0.3341 vs 0.3409; Saleor 0.3356 vs 0.3322

The A/B set agreement (83.28%) is lower than the fixed-B=5 replication (97.21%) because
files near the learned probability threshold flip more easily under hosted float noise;
the SCIENTIFIC verdict is stable (both FAIL on the same criterion).

## HOW MUCH ORACLE HEADROOM REMAINS?

Oracle-Add ALL (perfect recall of omitted positives) caps file-level F1 at 0.867/0.829;
the V1 policy reaches 0.334/0.336. The remaining gap decomposes into: (1) ranking /
candidate-coverage error (positives outside Sparse union top-20), (2) ADD decision
error (top-20 candidates that are positives but below the threshold), (3) DROP decision
error (Sparse positives accidentally dropped: 14 djangoCMS / 6 Saleor), and (4) the
historical changed-file proxy's own ambiguity. See the Oracle-gap dated successor
`reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md`.

## WHAT DOES THIS MEAN FOR STAGE 5?

The final file-set decision policy is NOT frozen as a success: the preregistered primary
gate FAILS (djangoCMS Delta-F1 CI crosses zero), and the frozen verdict is
`CALIBRATED_SET_SELECTION_V1_FAIL`. Stage 5 remains PAUSED and SEALED
(`FINAL_POLICY_NOT_FROZEN`). The dense-ranking mechanism is independently replicated, so
lack of independent replication is no longer a Stage-5 blocker — but the policy problem
is not solved.

## WHAT DOES THIS NOT PROVE?

- It does NOT prove the calibrated policy is useless: the point estimates improve on
  both repos and Saleor's CI excludes zero. It proves the CURRENT frozen minimal policy
  is not statistically distinguishable from Sparse on djangoCMS under the frozen gate.
- It does NOT prove any V2 feature set (graph, co-change, BM25, history, model family
  changes) — those require a NEW mission and a NEW frozen hypothesis.
- It does NOT prove Qwen/SweRank training-provenance status (verdict C unchanged).
- It does NOT unlock Stage 5 and does NOT claim the method beats LocAgent or any
  external baseline (LocAgent F1~0.333 is from a different exposed 10-task population).

## Evidence

Machine-readable outputs under `research/calibrated-set-selection-v1/`; frozen config in
`reports/calibrated_set_selection_v1_freeze.json`; independent audit 20/20 PASS (`reports/calibrated_set_selection_v1_audit.json`).
