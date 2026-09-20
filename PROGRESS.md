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
**Task:** SALEOR_RESERVE_300_RMCSS - FINAL CLEAN RM-CSS REPLICATION +
PRE-REGISTERED CROSS-REPOSITORY TRANSFER TEST (2026-09-20; T3; ONE clean
untouched evaluation of 300 Saleor RESERVE tasks; APPROVED BY AHMED) -
**COMPLETE: PRIMARY `SALEOR_RESERVE_300_RMCSS_PASS` + SECONDARY
`SECONDARY_CROSS_REPO_TRANSFER_PASS`.** Actual cost $1.619525 < $1.75 amended
ceiling (P89). SIP 300/300 (228 succeeded / 70 completed-empty / 2
transport-failed -> fail-closed EMPTY; $1.59349); embeddings 2,076 units + 299
queries ($0.026035); parity gate 10/10 + independent parity audit 11/11 PASS;
PRIMARY RM-CSS F1 0.3569 vs SIP 0.2647, Delta F1 +0.0921 CI [+0.0691,+0.1156];
SECONDARY django-only F1 0.3389 vs SIP 0.2647, Delta F1 +0.0742 CI
[+0.0535,+0.0957]; result audit 15/15; outcomes opened once; 786 Saleor RESERVE
tasks remain untouched; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` permanent;
no post-unseal tuning; no V3. Previous task - STAGE5_CORRECTED_REEXECUTION
(2026-09-20; P86/P87; corrected 139-task result on EXPOSED population:
`STAGE5_CORRECTED_REEXECUTION_POSITIVE`, pooled SIP 0.2857 / RM-CSS 0.3419 /
Delta +0.0562 CI [+0.0185,+0.0945]).

---

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

## WP-0 (2026-09-20) — G7 Ground-Truth Leakage Fix (ArtifactUniverse de-repo)

**Task:** WP-0 — G7 Ground-Truth Leakage Fix. **Branch:**
`fix/wp0-artifact-universe-no-ground-truth`. **Tier:** T3. **Scientific API
spend:** $0.00. **Measurement-infrastructure repair; no scientific claim.**

- **Completed (AC-0.1..AC-0.5 + independent audit):** `_build_artifact_universe`
  now derives the eligible artifact universe from the parent-commit repository
  state for every non-fixture execution; legacy fixture behavior moved behind
  explicit `allow_ground_truth_universe` (default False) and auditable on
  `RunRecord`; fail-closed config (fixture incompatible with regeneration and
  with selection-only); pass-through in `PipelineConfig`.
- **RED->GREEN:** regression test
  `test_production_universe_never_consults_expected_affected` failed pre-fix
  (universe was `{'hidden/secret.py'}` — ground truth) and passed post-fix
  (repository-derived). New suite
  `tests/unit/test_artifact_universe_no_ground_truth.py` 14/14.
- **AC-0.1 hidden-truth independence:** PASS (140-file repo universe built
  with hidden proxy unreadable, ground-truth path absent, flag False).
- **AC-0.2 static search:** PASS (only guarded fixture occurrence of
  `expected_affected_artifacts` in execution code; no proxy/hidden reads).
- **AC-0.3 3-task sanity:** PASS — repo-derived vs public candidate-universe
  counts: 140/140, 152/152, 140/140 (djangocms-rc-06ecf3a8e8de,
  -0daae01f2f65, -0fec81224889).
- **AC-0.4:** new + affected regression suites pass; ruff PASS; mypy strict
  PASS; py_compile PASS; git diff --check PASS.
- **AC-0.5:** `selective_updates/records/SU-0012-artifact-universe-derepo.md`.
- **Independent audit:** 6/6 PASS (computed without importing audited helpers).
- **Governance:** DECISIONS.md — Decision WP0 + full event/deferral ledger
  (LED-A..S) appended; `WP0_SCOPE_AMENDMENT_RUNRECORD_AUDITABILITY` ACCEPTED.
- **Status:** WP-0 acceptance criteria all PASS; commit + push of feature
  branch only; NOT merged to main; no scientific tag.

**Next step (NOT started):** WP-1 Repository-Agent Selection-Only Baseline —
AWAITING AHMED AUTHORIZATION. WP-2 E2E Phase-0 instrument DEFERRED. G6 oracle
unresolved. No Smoke / Pilot / Research Run. No E2E scientific claim allowed.
