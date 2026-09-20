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
**Task:** STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT - REPAIR THE
EXECUTION DEFECT IN THE FROZEN STAGE-5 V2 PIPELINE (2026-09-20; T3;
governance-first P86): the first Stage-5 run was EXECUTION-INVALID (finite
-1e9 sentinel instead of NaN/new embeddings for Stage-5 blobs missing from the
DEV cache; superseded `STAGE5_V2_FINAL_CONFIRMATION_FAIL`); fix embedding
coverage ONLY, add hard pipeline guards, run the label-free parity gate +
independent parity audit, corrected re-execution on the SAME 139 exposed tasks
reusing persisted Sparse write sets, corrected metrics/bootstrap (seed
20260920), defect impact analysis, Acc@K descriptive, independent result audit,
governance after corrected run, new tag `stage5-corrected-reexecution-2026-09-20`;
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` holds; Saleor RESERVE sealed;
draft clean-replication preregistration prepared for Ahmed review ONLY.

---

**Previous task (2026-09-20, one-shot untouched confirmatory; SUPERSEDED by the
execution-defect correction):** STAGE5_V2_FINAL -
FINAL THESIS IMPACT-LOCALIZATION FREEZE + ONE-SHOT STAGE-5 CONFIRMATORY
EVALUATION (T3; $0.544067) - **COMPLETE:
`STAGE5_V2_FINAL_CONFIRMATION_FAIL`** (frozen negative; pooled Delta F1 −0.0588,
CI [−0.1119, −0.0084]; A and B FAIL; both repos negative; V2 did not survive
untouched confirmation; method-search phase CLOSED). **The first Stage-5 run is
now EXECUTION-INVALID (P86: finite -1e9 sentinel embedding-coverage defect);
its FAIL label is superseded by
`STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`.** Previous task -
ISSUE-GROUNDED INTENT HEADROOM -
DOES A REAL PRE-CHANGE PROBLEM DESCRIPTION FIX THE INFORMATION BOTTLENECK?
(2026-09-20; T3 DEVELOPMENT; minimal-cost) - **COMPLETE:
`ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`** (frozen negative; strict
temporal rule leaves 12 djangocms + 0 saleor clean paired tasks; djangoCMS
Recall@20 point-rises 0.6875->0.7188 but paired CI crosses zero and median
rank worsens; Saleor unevaluable; no full issue-grounded pipeline justified;
Stage 5 stays PAUSED/SEALED). Previous task - PARENT-ONLY REPOSITORY MEMORY
RESCUE V2 - HISTORY-AUGMENTED DEEP FALSE-NEGATIVE RECOVERY
(2026-09-20; T3 DEVELOPMENT; ZERO API) — **COMPLETE:
`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`** (frozen negative; parent-only
repository-history memory recovers deep dense misses at the candidate level
but the unchanged final-set gate fails on djangoCMS — Delta-F1 CI crosses zero
in BOTH realizations A and B; Saleor passes; Stage 5 stays PAUSED/SEALED).

---

## Now executing

- **MILESTONE COMPLETE (T3, ZERO paid API).** A deterministic parent-only
  repository-memory generator (Channel A structural co-change Jaccard with
  support>=2 + Channel B episodic BM25 over historical commit text) was frozen
  (P80) and evaluated: memory candidate set (top-10 structural ∪ top-10
  episodic NON-SPARSE) recovered 43/199 (0.216) djangoCMS and 48/177 (0.271)
  Saleor of the DEEP_DENSE_MISS files (median dense rank 62/70) — vs
  popularity 41/18 and random 11.1/2.45. V2 (EXACTLY V1 model/CV/threshold, 11
  features) point F1 improves over Sparse AND V1 on both repos (djangoCMS
  0.318→0.334→0.345; Saleor 0.261→0.336→0.348) but **verdict =
  `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`**: djangoCMS Delta-F1 CI
  [+0.027, CI −0.010..+0.064] crosses zero in A and B; Saleor PASS. All added
  djangoCMS positives came from history-involved candidates. Realization-B
  robustness: 99.07% exact same set, mean Jaccard 0.9964, verdict SAME.
  Independent audit 23/23 PASS; new unit tests 36/36 PASS.
- **Remaining:** closure (governance docs updated; commit/merge/push/tag/
  export/STOP report).

## Last completed task

- PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 (2026-09-20, T3, ZERO API): P80
  frozen config + governance + Full-Universe cancellation recorded BEFORE
  implementation; verified V1 rank-selection diagnostic (172/93/20/3/0) and
  deep dense misses (199/177, median ranks 62/70); dependency-cluster
  diagnostic (109/25/56; 130/49/76, oracle-style only); parent-only history
  build (fail-closed ancestry, production-file filter, ALL parent-visible
  history, caches on D:); structural co-change + episodic BM25 memory
  channels; deep-FN coverage report + popularity/random baselines; V2
  pipeline (11 features, exact V1 folds/model/threshold); per-repo metrics +
  paired bootstrap CIs + error decomposition with channel attribution +
  intent stratification + sparse-empty; primary gate A-G (FAIL djangoCMS
  criterion B, robust A/B); channel ablations (descriptive); determinism
  identical; independent audit 23/23 PASS; 36 new unit tests PASS. Scripts
  `scripts/memory_rescue_v2_{history,run,diagnostics,ablation,audit}.py`;
  evidence `research/memory-rescue-v2/`;
  reports `reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_REPORT_2026-09-20.md`,
  `reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_DIAGNOSTICS_2026-09-20.md`,
  `reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE_2026-09-20.md`.

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
  (V2 final-set policy FAILED its frozen gate on djangoCMS in both
  realizations; repository history recovers candidates but does not solve the
  final-set decision).

## Full-suite state (PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2, 2026-09-20)

- New unit tests `tests/unit/test_memory_rescue_{history,cochange,v2}.py`
  **36/36 PASS** (parent-only visibility; no future/target leakage; temporal
  ancestry fail-closed; production-file filtering; parse determinism;
  co-change counts; Jaccard; support>=2; Sparse-empty; dense-rank1 seed;
  commit-text indexing; BM25 determinism; structural/episodic top10;
  candidate-union; V1 fold/LR/threshold reuse; metrics; bootstrap determinism;
  intent bucket assignment (NOT a feature); realization-B robustness; sealed
  guard).
- V1 calibrated suite `tests/unit/test_calibrated_set_selection.py` still
  **18/18 PASS** (policy.py change is backward-compatible).
- Independent audit **23/23 PASS** (`reports/memory_rescue_v2_audit.json`):
  recomputes every claim from persisted artifacts WITHOUT importing the
  analyzer.
- Ruff clean (new files); py_compile clean; `git diff --check` clean.

## Closure block (PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2, 2026-09-20)

- T3 ZERO-API DEVELOPMENT closure; frozen negative
  `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` recorded.
- DEV-evidence tag (peel == merge == main-at-tag-time; audited DEVELOPMENT
  evidence; NOT a stable-tag move). Pushed to origin; origin/main == HEAD ==
  tag peel.
- TRUE LIGHT export at scientific closure: project-LIGHT-2026-09-20-0746.zip (40.22 MB <= 50 MB; SHA-256 d6a3af836dd127ec539a602120a4c854ce31664af231d7a90d09099f93b292c7; HEAD 939e5a2; origin/main == HEAD == tag peel).
- Next scientific action (NOT started): a V3 would require a NEW mission and
  NEW frozen hypothesis (no automatic V3); Stage 5 remains gated on a frozen
  successful final policy.
## Full-suite state (ISSUE_GROUNDED_INTENT_HEADROOM, 2026-09-20)

- New unit tests `tests/unit/test_issue_grounded.py` **27/27 PASS**
  (reference parsing; repo-local resolution; issue-vs-PR distinction; no-PR
  text; temporal-clean rule; updated_at guard; corpus hashing; ranking
  aggregation unchanged; Recall@K formulas; task-paired bootstrap; path-mention
  detection; sealed-data guard; 404 -> unresolved; ARM I query construction).
- Independent audit **12/12 PASS** (`reports/issue_grounded_audit.json`):
  recomputes reference counts, provenance, temporal flags, clean population,
  ARM M/I Recall@20, bootstrap CI, corpus SHA256, A/B agreement WITHOUT
  importing the analyzer.
- Ruff clean; py_compile clean; `git diff --check` clean.
- Cost: GitHub metadata free (cached); Qwen issue-query embeddings only
  5,662 prompt tokens / $0.000057 (live $0.01/M verified); no corpus re-embed.

## Closure block (ISSUE_GROUNDED_INTENT_HEADROOM, 2026-09-20)

- T3 minimal-cost DEVELOPMENT closure; frozen negative
  `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` recorded.
- Reference counts verified: djangocms 99/174, saleor 112/149 (recomputed,
  matches prior descriptive claim). Strict temporal rule -> clean population =
  djangocms 12 / saleor 0. Primary gate fails on djangoCMS (paired CI for
  Delta Recall@20 crosses zero; median rank worsens); Saleor unevaluable.
  Realization A == B. DeepFNRescue@20 = 0.143 (1/7). History BM25 arm NOT
  improved by issue query (candidate precision 0.0885 -> 0.0431).
- No full issue-grounded pipeline justified by this evidence; commit-message
  proxy not demonstrated to suppress useful localization information.
- Next scientific action (NOT started): a future issue-grounded mission must
  deliberately decide the temporal rule (the strict `updated_at` rule produces
  a near-empty Saleor population) and pre-register a larger clean corpus;
  Stage 5 remains gated on a frozen successful final policy.
- TRUE LIGHT export at scientific closure: project-LIGHT-2026-09-20-0746.zip (40.22 MB <= 50 MB; SHA-256 d6a3af836dd127ec539a602120a4c854ce31664af231d7a90d09099f93b292c7; HEAD 939e5a2; origin/main == HEAD == tag peel).

## Full-suite state (STAGE5_V2_FINAL, 2026-09-20)

- Pre-unsealing tests `tests/unit/test_stage5_v2_final.py` **10/10 PASS**
  (feature schema exact-11; threshold reproducibility; serialization/reload;
  candidate determinism; Sparse determinism; Qwen config; parent-only guard;
  preregistration hash).
- Independent audit `reports/stage5_independent_audit.json` **10/10 PASS**
  (recomputes task counts, Sparse/V2 confusion, per-repo P/R/F1/FNR, pooled
  stratified Delta-F1 bootstrap, direction consistency, Acc@K/Hit@K/Recall@K,
  final label WITHOUT importing the primary analyzer).
- Metric-compatibility audit `reports/stage5_native_compat_audit.json` 7/7 PASS.
- Ruff clean; py_compile clean; git diff --check clean.

## Closure block (STAGE5_V2_FINAL, 2026-09-20)

- ONE-SHOT untouched confirmatory evaluation of the best frozen DEV candidate
  (`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2`); frozen negative
  `STAGE5_V2_FINAL_CONFIRMATION_FAIL` + `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
- Population: dc RESERVE 59 + Saleor INTERNAL_TEST 80 = 139 (Saleor RESERVE
  untouched). Paid $0.544067 (Sparse 139 tasks + query embeddings) << $1.00.
- Primary: pooled V2 F1 0.2269 vs Sparse 0.2857; Delta F1 −0.0588
  CI [−0.1119, −0.0084]; A and B FAIL; both repos negative.
- Method-search phase CLOSED; next phase external-validity-and-end-to-end
  regeneration (separate mission); Stage 5 never re-run.
- TRUE LIGHT export at scientific closure: filename/hash in the final stop
  report.
