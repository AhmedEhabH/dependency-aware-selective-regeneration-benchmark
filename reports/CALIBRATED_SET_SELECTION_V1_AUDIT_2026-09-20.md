# CALIBRATED_SET_SELECTION_V1 — Independent Audit (2026-09-20)

**Verdict: PASS 20/20.** The independent audit recomputes every key claim from
the PERSISTED artifacts (under `research/calibrated-set-selection-v1/`) plus
`load_dev_tasks()` (the data layer) and does NOT import the primary analyzer
(`benchmark.calibrated.*` or the run script). Machine-readable result:
`reports/calibrated_set_selection_v1_audit.json`.

| # | Check | Pass |
|---|---:|---|
| 1 | candidate universe == 323 DEV tasks | PASS |
| 2 | DEV repos only | PASS |
| 3 | Sparse baseline djangoCMS TP/FP/FN == 125/155/382 | PASS |
| 4 | Sparse baseline Saleor TP/FP/FN == 99/193/369 | PASS |
| 5 | OOF covers every task exactly once | PASS |
| 6 | fold assignment covers all 323 tasks | PASS |
| 7 | final sets recomputed from OOF probs + thresholds == persisted | PASS (323/323) |
| 8 | repo_metrics recomputed == persisted (both repos) | PASS |
| 9 | independent paired task bootstrap F1 CI matches (both repos) | PASS |
| 10 | folds repository-stratified (<=1 task imbalance per repo) | PASS |
| 11 | no repository-identity / file-count-N feature in candidate schema | PASS |
| 12 | all frozen feature definitions recompute exactly | PASS |
| 13 | gate G: deterministic rerun identical | PASS |
| 14 | calibration (Brier/ECE) recomputed | PASS |
| 15 | A/B robustness recomputed == persisted | PASS |
| 16 | A/B gate verdict agreement stable | PASS |
| 17 | gate logic recomputed matches persisted pass flags | PASS |
| 18 | LR coefficients + scaler parameters finite | PASS |

(Check numbering follows the audit script; 18 rows cover the 20 assertions
because several rows carry two assertions.)

## Independent recomputation highlights

- **Final sets**: all 323 tasks' final selected sets were re-derived from the
  persisted OOF probabilities and the per-fold frozen thresholds; all 323 match
  the persisted `final_oof_predictions_A.json`.
- **Pooled metrics**: pooling the recomputed selected sets against the DEV
  proxy reproduces the persisted `repo_metrics_A.json` (TP/FP/FN/P/R/F1/FNR)
  exactly.
- **Bootstrap**: an independently implemented task-paired bootstrap (10,000
  resamples, seed 20260920) reproduces the persisted Delta-F1 95% CIs within
  2e-3 on both repositories.
- **Features**: `log_rank = log1p(dense_rank)`, `sparse_rank_interaction =
  in_sparse * log_rank`, `gap_to_top1 = max_score(task) - score`, and the NaN
  floor (`min_finite - 1.0`) all recompute exactly from the persisted
  candidate universe.
- **Leakage**: the candidate-universe schema contains NO repository-identity or
  repository-file-count feature; the dedicated flip-test (unit suite) proves
  held-out labels cannot change OOF probabilities or final sets; gate G
  (deterministic rerun) holds.
- **Sealed guard**: exactly the 323 DEV case IDs (174 djangoCMS + 149 Saleor)
  are present; no INTERNAL_TEST / RESERVE case appears anywhere.

## Sealed data / boundary

No sealed scientific dataset was opened. Stage 5 was not executed. ZERO paid
API calls.