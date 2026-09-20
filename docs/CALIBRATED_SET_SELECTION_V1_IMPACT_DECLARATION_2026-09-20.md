# CALIBRATED_SET_SELECTION_V1 — T3 Impact Declaration + Frozen Configuration (2026-09-20)

**Status:** FROZEN BEFORE IMPLEMENTATION. This document records the exact
decision policy, feature set, model configuration, cross-validation procedure,
threshold procedure, success gate, and expected file list for the
CALIBRATED_SET_SELECTION_V1 mission BEFORE any outer-OOF outcome is inspected.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** CALIBRATED_SET_SELECTION_V1 (DEV-ONLY FINAL FILE-SET POLICY)
**Tier:** T3 (new evaluation strategy / baseline family)
**Branch:** `research/calibrated-set-selection-v1-2026-09-20`
**API budget:** ZERO paid API calls (all features come from the persisted
label-free Qwen full-file-score artifacts + parent-visible DEV data).
**Sealed data:** NOT opened. Development populations only (djangoCMS DEV 174,
Saleor DEV 149).

---

## 1. Impact Declaration (separated per the mission §5)

### A. Calibrated-policy implementation

New package `src/benchmark/calibrated/` with deterministic, pure modules:

| File | Purpose |
|---|---|
| `src/benchmark/calibrated/__init__.py` | package marker |
| `src/benchmark/calibrated/features.py` | candidate-universe construction + frozen 7-feature row builder |
| `src/benchmark/calibrated/folds.py` | deterministic task-grouped, repository-stratified fold assignment |
| `src/benchmark/calibrated/policy.py` | L2-LR policy: scaler + model fit, inner-OOF threshold selection, final set construction, pooled metrics |
| `src/benchmark/calibrated/analysis.py` | nested 5x5 task-grouped CV driver, bootstrap CIs, calibration diagnostics, error decomposition, A/B robustness |

### B. Nested-CV / evaluation artifacts

| File | Purpose |
|---|---|
| `scripts/calibrated_set_selection_v1_run.py` | the ONE primary analyzer (realization A primary; `--realization B` for robustness) |
| `scripts/calibrated_set_selection_v1_report.py` | human-readable report generator |
| `scripts/calibrated_set_selection_v1_audit.py` | INDEPENDENT audit (does NOT import the primary analyzer) |
| `research/calibrated-set-selection-v1/` | machine-readable outputs (fold assignments, candidate rows, features, scaler params, LR coefficients, inner thresholds, OOF probabilities, final OOF predictions, task-level selected sets, repo metrics, bootstrap CIs, calibration, error decomposition, A/B robustness, audit JSON) |

### C. Governance / documentation updates

| File | Purpose |
|---|---|
| `DECISIONS.md` | append P78 (governance amendment + this frozen config) |
| `00_CURRENT_RESEARCH_STATE.md` | scientific truth update |
| `PROGRESS.md` | execution truth update |
| `docs/RESEARCH_JOURNEY.md` | chronological row |
| `docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md` | this file |
| `reports/CALIBRATED_SET_SELECTION_V1_REPORT_2026-09-20.md` | human-readable report |
| `reports/CALIBRATED_SET_SELECTION_V1_AUDIT_2026-09-20.md` + `.json` | audit report |
| `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md` | dated successor of the Oracle-gap explanation with the V1 update |
| `reports/LOCAGENT_MATCHED_COMPARISON_PROTOCOL_DRAFT_2026-09-20.md` | future matched-comparison protocol draft (NOT executed) |

### D. Audit / testing artifacts

| File | Purpose |
|---|---|
| `tests/unit/test_calibrated_set_selection.py` | unit tests for every frozen component |
| `reports/calibrated_set_selection_v1_freeze.json` | machine-readable frozen config + governance amendment (frozen BEFORE OOF) |
| `reports/calibrated_set_selection_v1_gate.json` | success-gate verdict |
| `reports/calibrated_set_selection_v1_audit.json` | independent-audit verdict |

---

## 2. Governance amendment (mission §3) — recorded BEFORE implementation

Append a new decision (P78) to `DECISIONS.md`:

- **`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`** means lack of independent
  replication is **NO LONGER a Stage-5 blocker**.
- **Stage 5 remains paused** because the final set-selection policy is NOT
  frozen: **`FINAL_POLICY_NOT_FROZEN`**.
- **Pretrained-model provenance claim boundary (preserved):** independent
  replication (Qwen3-Embedding-8B A+B both PASS djangoCMS and Saleor @B=5)
  **weakens** the hypothesis that SweRankEmbed-Small's gain is solely due to
  SweLoc-specific supervision or memorization, but it does **NOT** prove that
  either pretrained model never saw public target-repository code. Verdict C
  (`TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`) is unchanged.

---

## 3. Frozen scientific position (mission §1 — preserved, not rewritten)

- A. Sparse suffers substantial false-negative loss (frozen).
- B. Cheap structural ranking did not robustly solve the problem (frozen).
- C. Generic bounded semantic / verifier families were frozen negative (frozen).
- D. SweRankEmbed-Small showed a successful specialized dense-ranking and
  omission-recovery signal (frozen; external pretrained diagnostic, verdict C).
- E. Qwen3-Embedding-8B independently reproduced the SAME broad dense-ranking
  mechanism on BOTH repositories (`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`;
  A/B both PASS both repos @B=5; 97.21% exact same set; mean Jaccard 0.9907).

The current bottleneck is the **FINAL FILE-SET DECISION** (adaptive ADD, KEEP
of correct Sparse files, DROP of incorrect Sparse files). This mission
implements a single minimal interpretable repository-independent decision
policy for that decision.

---

## 4. Frozen data scope (mission §7)

- djangoCMS DEV: 174 tasks.
- Saleor DEV: 149 tasks.
- NOT used: djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE, spent
  djangoCMS INTERNAL_TEST. No sealed outcome is read. No Stage-5 execution.

---

## 5. Frozen primary score realization (mission §8)

- **Qwen realization A** is the PRIMARY dense-score realization (generated
  chronologically first; choice made independent of downstream policy
  performance).
- Realization B is used ONLY after all V1 elements (features, candidate
  universe, model, folds, threshold procedure, success gate) are frozen —
  for the realization-B robustness rerun (mission §27).
- No averaging of A/B scores. No choosing the better realization.

---

## 6. Frozen decision policy (mission §10, §11, §13)

### 6.1 Candidate universe (frozen; `TOP_ADD_UNIVERSE = 20`)

For every task:

- **KEEP/DROP candidates:** ALL files currently selected by Sparse
  (`in_sparse == True` in the frozen full-file-score artifact).
- **ADD candidates:** the top 20 NON-SPARSE legal production files according
  to the frozen Qwen dense ranking (`dense_rank` ascending among files with
  `in_sparse == False`; ties already resolved deterministically by the frozen
  rank artifact).
- Files outside `Sparse ∪ top-20 omitted` remain unselected in V1.
- NO hard cap on how many of the top-20 candidates may be added; the learned
  threshold determines the final number. NO "max additions = 5" cap. NO
  minimum-one-file constraint.

### 6.2 Feature set (frozen EXACTLY; no feature shopping)

For each candidate file, EXACTLY these seven features:

| # | Feature | Definition |
|---|---|---|
| 1 | `dense_file_score` | frozen Qwen dense file score (NaN imputed deterministically — see 6.4) |
| 2 | `log_rank` | `log1p(dense_rank)`; **ABSOLUTE** rank 1..N; NOT normalized by N |
| 3 | `gap_to_top1` | `max_score(task) - dense_file_score` (deterministic from frozen scores) |
| 4 | `in_sparse` | boolean: 1 if the file is in the Sparse write set |
| 5 | `log_sparse_set_size` | `log1p(sparse_set_size)` |
| 6 | `sparse_empty` | boolean: 1 if `sparse_set_size == 0` |
| 7 | `sparse_rank_interaction` | `in_sparse * log_rank` |

FORBIDDEN (never added): repository identity, repository file-count N,
normalized rank by N, BM25, graph distance/degree, co-change, historical
frequency, path tokens, file extension, architecture layer, LLM semantic
labels, generated reviewer features, target-aware information.

### 6.3 Why absolute log-rank is frozen (mission §12 — documented BEFORE execution)

The post-hoc DEVELOPMENT rank-hit pattern is broadly similar across
repositories despite large repository-size differences. Verified from the raw
SweRank artifact (`research/strong-localization-signal/swerank/task_rankings.json`):

| rank | djangoCMS hit rate (174) | Saleor hit rate (149) |
|---|---:|---:|
| 1 | 0.241 (42/174) | 0.262 (39/149) |
| 2 | 0.132 (23/174) | 0.174 (26/149) |
| 3 | 0.109 (19/174) | 0.128 (19/149) |

These are aggregate **frequencies**, NOT calibrated probabilities. Absolute
early rank is treated as an interpretable cross-repository signal. Because the
legal-file universe sizes separate the repositories with effectively no
overlap (djangoCMS 139..234; Saleor 403..1142), a normalized feature
`log1p(rank)/log1p(N)` would inject repository-universe size and act as a
hidden repository-identity proxy, contradicting the pooled repository-
independent policy — hence absolute rank is frozen.

### 6.4 Deterministic handling of files with no embeddable units

`dense_file_score` is NaN for ~7.7% of universe rows (files with no embeddable
code units). Frozen deterministic imputation (parent-visible, label-free,
computed once per realization from the frozen score artifact):
`imputed = min_finite_dense_score - 1.0` where `min_finite_dense_score` is the
minimum FINITE dense file score in the frozen realization (~0.072). This keeps
the value below every observed score while remaining numerically well-behaved
under StandardScaler (unlike `-1e9`). `gap_to_top1` is then computed from the
imputed score. `dense_rank` is complete (no NaN) and unchanged.

### 6.5 Model (mission §13) — one family only

- L2-regularized Logistic Regression (`sklearn.linear_model.LogisticRegression`).
- `penalty="l2"`, `C=1.0`, `solver="liblinear"` (deterministic), `max_iter=1000`,
  `random_state=0`.
- `StandardScaler` for the continuous features
  (`dense_file_score`, `log_rank`, `gap_to_top1`, `log_sparse_set_size`,
  `sparse_rank_interaction`); the two boolean features (`in_sparse`,
  `sparse_empty`) are NOT scaled.
- Scaler fit ONLY on training rows (never on held-out rows).
- NO class-weight search, NO C search, NO solver search, NO hyperparameter
  optimization. NO comparison against other model families.

---

## 7. Frozen nested task-grouped OOF evaluation (mission §14)

- Deterministic **5-fold OUTER task-grouped CV**, all candidate files of the
  same task kept together.
- Outer folds approximately stratified by repository (within each repository
  the tasks are deterministically shuffled with a fixed seed and assigned
  `fold = index % 5`, so each fold contains ~1/5 of each repository's tasks).
- Fold seeds: outer and inner both `20260920` (deterministic; realization-
  independent because assignment depends only on case IDs).

For every outer fold:

1. designate held-out tasks;
2. use ONLY remaining outer-training tasks;
3. fit preprocessing (scaler) using only outer-training evidence;
4. fit Logistic Regression using only outer-training tasks;
5. derive the final decision threshold using INNER task-grouped OOF only
   within the outer-training tasks;
6. freeze that threshold;
7. predict probabilities for the outer held-out tasks;
8. construct final affected-file sets (`prob >= threshold`);
9. score against the historical changed-file evaluation proxy.

NO file-level random train/test split.

---

## 8. Frozen inner threshold procedure (mission §15, §16, §17)

- Inside each OUTER training partition: deterministic **5-fold INNER
  task-grouped OOF** (same task-grouped, repo-stratified procedure).
- Generate inner-OOF predicted probabilities; then choose ONE threshold
  `t = argmax pooled micro-F1` using ONLY inner-training OOF predictions.
- Threshold grid: `0.01, 0.02, ..., 0.99` inclusive, step `0.01`.
- Tie-break: the HIGHER threshold (conservative; limits unnecessary FP
  expansion).
- The threshold is chosen to maximize pooled micro-F1 (the primary final-set
  metric) on INNER OOF training evidence — NOT the Lipton F1*/2 rule applied
  to raw scores/ranks.
- **Lipton, Elkan, Narayanaswamy, "Thresholding Classifiers to Maximize F1
  Score," ECML-PKDD 2014** is used as THEORETICAL MOTIVATION only: for
  well-calibrated conditional probabilities `t = F1*/2`. It is NOT applied
  directly to raw cosine scores, dense ranks, or aggregate rank-hit
  frequencies. The paper's batch-dependence caveat is documented. The
  empirical relationship between the chosen training-only threshold and the
  training-fold F1*/2 is reported as a DESCRIPTIVE check only.

---

## 9. Frozen final-set construction (mission §19)

For each candidate file: include the file iff
`predicted_probability >= outer_training_threshold`.

This permits ADD (previously omitted file enters), KEEP (correct Sparse file
remains), DROP (Sparse-selected file falls below threshold). Files outside the
frozen candidate universe remain unselected. No minimum-one-file constraint.
No fixed B. No max-additions cap.

---

## 10. Frozen baselines / comparators (mission §20)

- PRIMARY baseline: **Sparse final affected-file set** (the research question
  is whether the COMPLETE policy improves the Sparse final-set prediction).
- Descriptive (NOT retuned): Route-B B=5, Qwen B=5, Qwen diagnostic B=1,
  SweRank B=5, SweRank diagnostic B=1.
- Historical frozen numbers (verified from artifacts): Sparse F1 0.318/0.261;
  Route-B B=5 0.226/0.237; Qwen B=5 0.262/0.270; Qwen B=1 0.329/0.308;
  SweRank B=5 0.280/0.288; SweRank B=1 0.348/0.304.

---

## 11. Frozen metrics + confidence intervals (mission §21, §22)

- Always report TP/FP/FN, P, R, FNR, F1 (definitions as in the protocol).
- `Delta_metric = Metric_policy - Metric_sparse` for policy-vs-Sparse.
- Task-paired bootstrap: >= 10,000 resamples, fixed seed `20260920`, resample
  TASKS (not files). `Delta_b = Metric_policy_b - Metric_sparse_b`;
  CI95 = [Q2.5, Q97.5]. CIs reported for Precision, Recall, F1, FNR.

---

## 12. Frozen primary success gate (mission §23)

Required on BOTH repositories:

| Criterion | Condition |
|---|---|
| A | Final micro-F1 > Sparse micro-F1 |
| B | paired-bootstrap 95% CI lower bound for Delta F1 > 0 |
| C | Recall_policy >= Recall_sparse |
| D | FNR_policy <= FNR_sparse (D is mathematically equivalent to C; reported for interpretability, NOT an independent criterion) |
| E | at least 3/5 outer folds satisfy Delta F1 >= 0 |
| F | zero target leakage |
| G | deterministic local rerun produces identical OOF predictions and final selected sets |

**Precision handling (mission §24):** NO arbitrary non-inferiority margin. F1
is the preregistered primary precision/recall trade-off criterion. Report
Precision point estimate, absolute Delta Precision, paired 95% CI. Also report
the descriptive flag `PARETO_SUCCESS` (TRUE only if on BOTH repositories
P_policy > P_sparse AND R_policy > R_sparse AND F1_policy > F1_sparse AND
FNR_policy < FNR_sparse). PARETO_SUCCESS is descriptive, NOT required for the
primary gate.

---

## 13. Frozen error decomposition + set-size + calibration (mission §25, §26, §18)

- **Error decomposition (per repo):** A. Sparse TP RETAINED; B. Sparse TP
  incorrectly DROPPED; C. Sparse FP correctly DROPPED; D. Sparse FP RETAINED;
  E. Sparse FN correctly ADDED; F. new FP ADDED.
- **Set-size analysis (per repo):** mean/median |Sparse|, |Policy|, |proxy
  changed-file set|; number of empty Sparse and empty Policy predictions;
  distribution of number of additions per task.
- **Calibration diagnostics (frozen 10 equal-width probability bins):** Brier
  score, Expected Calibration Error (ECE), reliability table, using the outer
  OOF probabilities. NO second calibration algorithm, NO alternative bin
  counts, NO isotonic/Platt/temperature comparison after outcomes.

---

## 14. Frozen realization-B robustness (mission §27)

ONLY after the complete V1 design is frozen and the realization-A OOF
procedure is specified: rerun the EXACT same pipeline with Qwen realization B
scores (allowed: refit scaler + LR inside the SAME frozen fold/training
procedure). Forbidden: changing features, log-rank transform, interaction,
candidate universe, C, solver, folds, threshold grid, tie-break, primary gate.
Report: A vs B repository metrics, exact selected-set agreement, task-level
Jaccard mean/median/min, PASS/FAIL agreement. If A and B produce different
scientific PASS/FAIL verdicts: `CALIBRATED_SET_SELECTION_V1_ROBUSTNESS_INCONCLUSIVE`.

---

## 15. Frozen decision rule (mission §32, §37)

- Once outer-OOF outcomes are visible: NO changes to the top-20 candidate
  universe, log-rank transform, feature set, interaction feature, LR family,
  C, solver, fold count, fold assignments, inner threshold grid, tie-break,
  primary comparator, or success gate.
- If the primary gate passes on BOTH repositories AND realization-B robustness
  preserves the PASS verdict: record `CALIBRATED_SET_SELECTION_V1_PASS` and
  recommend ONE exact frozen final policy for Stage-5 preregistration
  (DO NOT execute Stage 5).
- If the primary gate fails: record `CALIBRATED_SET_SELECTION_V1_FAIL` and STOP.
- If A/B verdict differs: record
  `CALIBRATED_SET_SELECTION_V1_ROBUSTNESS_INCONCLUSIVE` and STOP.
- No automatic V2.

---

## 16. Storage discipline (mission §35)

- No large caches on C:. No new caches created (features come from persisted
  artifacts). No raw embeddings committed to Git.
- Machine-readable outputs are compact JSON (fold assignments, candidate rows,
  features, scaler params, LR coefficients, inner thresholds, OOF
  probabilities, final OOF predictions, task-level sets, repo metrics,
  bootstrap CIs, calibration, error decomposition, A/B robustness, audit).
- TRUE LIGHT export kept <= 50 MB.

---

## 17. Frozen sealed-data guard (mission §36)

- The primary analyzer reads ONLY: (1) the label-free Qwen full-file-score
  Parquet artifacts; (2) `load_dev_tasks()` (DEV 174 + 149 only). A runtime
  guard asserts the case set is exactly the 323 DEV case IDs and that no
  sealed split (INTERNAL_TEST / RESERVE) case is present. The independent
  audit re-asserts the same guard.

---

## 18. Frozen competitor boundary (mission §30, §31)

- LocAgent / Agentless / Loc-Bench are NOT executed. The old LocAgent F1≈0.333
  came from a DIFFERENT exposed 10-task population and is NOT directly
  comparable with the current 323-task DEVELOPMENT numbers. A future
  matched-comparison protocol draft is prepared (same tasks, same evaluator,
  same production-file universe, same target proxy, same file-level metrics,
  fail-closed result, usable-only result separately, tokens, calls, cost,
  latency). NO claim that the current method beats LocAgent.
- Roadmap order preserved: (1) final calibrated policy on Python DEVELOPMENT;
  (2) freeze ONE final policy; (3) Stage-5 untouched Python confirmation;
  (4) TypeScript NestJS; (5) Java JabRef; (6) Go Prometheus;
  (7) true polyglot Grafana; (8) matched competitor / Loc-Bench studies;
  (9) downstream regeneration correctness.

---

## 19. Verification plan (mission §36)

- Independent audit does NOT import the primary analyzer.
- Unit tests required: correct task grouping; repository-stratified grouped
  folds; train-only scaling; train-only model fitting; inner-OOF threshold
  selection; no outer-label threshold leakage; candidate-universe
  construction; absolute log-rank transform; explicit test that repository
  file-count N is NOT a feature; sparse-rank interaction; ADD accounting;
  KEEP accounting; DROP accounting; metric formulas; paired bootstrap
  determinism; realization-B robustness; sealed-data guard.
- Run: targeted pytest; ruff; py_compile; git diff --check; affected suites.