# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main`
**Scientific closure commit:** `8b2d1b6` (merge of
`research/oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific
fact)
**Scientific closure tag peel:** `8b2d1b6` (tag
`oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific fact)
**Live HEAD / origin/main:** runtime git facts — a tracked file cannot embed
its own final live HEAD SHA (committing metadata changes HEAD again). Query
at read time: `git rev-parse HEAD`, `git rev-parse origin/main`,
`git status --porcelain`.
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** CALIBRATED SET SELECTION V1 — DEV-ONLY FINAL FILE-SET POLICY
(2026-09-20; T3 DEVELOPMENT; ZERO API) — **COMPLETE:
`CALIBRATED_SET_SELECTION_V1_FAIL`** (frozen negative; primary gate fails on
djangoCMS criterion B — Delta-F1 CI crosses zero — in BOTH realizations A and
B; Saleor passes; final-set decision policy NOT frozen; Stage 5 stays
PAUSED/SEALED).

---

## Now executing

- **MILESTONE COMPLETE (T3, ZERO paid API).** A single minimal interpretable
  repository-independent decision policy (L2-LR, 7 frozen features, nested
  5×5 task-grouped CV, inner-OOF F1 threshold, ADD/KEEP/DROP, no fixed B) was
  evaluated on DEVELOPMENT using the persisted Qwen full-file scores
  (realization A primary; B robustness). **Verdict =
  `CALIBRATED_SET_SELECTION_V1_FAIL`** (frozen negative; no V2): djangoCMS F1
  0.318 → 0.334 (point) but paired-bootstrap 95% CI for Delta F1 =
  [+0.017, CI −0.019..+0.053] crosses zero → gate criterion B fails; Saleor
  F1 0.261 → 0.336 (CI +0.042..+0.108, PASS). Realization B reproduces the
  same verdict (A=B; 83.28% exact same set; mean Jaccard 0.9284). Independent
  audit 20/20 PASS. Calibration excellent (Brier 0.064, ECE 0.0057). Oracle
  gap after V1 decomposed (coverage 199/177, ADD decision 154/138, DROP
  decision 14/6).
- **Remaining:** closure (governance docs already updated; commit/merge/push/
  tag/export/STOP report).

## Last completed task

- CALIBRATED_SET_SELECTION_V1 (2026-09-20, T3, ZERO API): frozen config +
  governance amendment (P78) recorded BEFORE implementation; candidate
  universe (Sparse ∪ top-20 non-sparse by Qwen dense rank); 7 frozen features;
  L2-LR C=1.0 liblinear; nested 5×5 task-grouped repo-stratified CV; inner-OOF
  F1 threshold (grid 0.01..0.99, tie-break higher); final sets by threshold;
  per-repo metrics + paired task bootstrap CIs + calibration (10 equal-width
  bins) + error decomposition + set-size analysis + A/B robustness; primary
  gate A–G (FAIL: djangoCMS criterion B); deterministic rerun identical;
  independent audit 20/20 PASS. Scripts
  `scripts/calibrated_set_selection_v1_{run,audit,report}.py`;
  evidence under `research/calibrated-set-selection-v1/`;
  reports `reports/CALIBRATED_SET_SELECTION_V1_REPORT_2026-09-20.md`,
  `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md`,
  `reports/LOCAGENT_MATCHED_COMPARISON_PROTOCOL_DRAFT_2026-09-20.md`.

## Immediate next step

- Closure: full validation, commit/merge/push/tag, verify HEAD ==
  origin/main, clean tree, TRUE LIGHT export, STOP report.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Stage 5 confirmatory stays PAUSED/SEALED: **`FINAL_POLICY_NOT_FROZEN`**
  (the V1 final-set policy FAILED its frozen gate; the dense-mechanism
  replication removed the non-replication blocker, but a frozen successful
  policy does not exist yet).

## Full-suite state (CALIBRATED_SET_SELECTION_V1, 2026-09-20)

- New unit tests `tests/unit/test_calibrated_set_selection.py` **18/18 PASS**
  (task grouping; repo-stratified folds; train-only scaling/fitting; inner-OOF
  threshold + tie-break; no outer-label leakage flip-test; candidate
  universe; absolute log-rank; N-not-a-feature; interaction; ADD/KEEP/DROP
  accounting; metric formulas; bootstrap determinism; robustness; sealed
  guard; gate/PARETO evaluation).
- Independent audit **20/20 PASS**
  (`reports/calibrated_set_selection_v1_audit.json`): recomputes every claim
  from persisted artifacts WITHOUT importing the analyzer.
- Ruff clean; py_compile clean; `git diff --check` clean.
- Affected suites: `tests/unit/test_calibrated_set_selection.py` 18/18.

## Closure block (CALIBRATED_SET_SELECTION_V1, 2026-09-20)

- T3 ZERO-API DEVELOPMENT closure; frozen negative
  `CALIBRATED_SET_SELECTION_V1_FAIL` recorded.
- DEV-evidence tag (peel == merge == main-at-tag-time; audited DEVELOPMENT
  evidence; NOT a stable-tag move). Pushed to origin; origin/main == HEAD ==
  tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific action (NOT started): a V2 calibrated set-selection policy
  would require a NEW mission and NEW frozen hypothesis (mission §32 forbids
  automatic V2); Stage 5 remains gated on a frozen successful final policy.