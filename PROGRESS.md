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

## Current active state (2026-09-20, normalized)

- **Phase:** 5 — End-to-End Selective Regeneration.
- **WP-0 (G7) ground-truth leakage fix:** COMPLETE and merged into `main`
  (fast-forward integration). `ArtifactUniverse` is now derived from the
  parent-commit repository state; legacy fixture behavior is behind an
  explicit `allow_ground_truth_universe` flag (default False), auditable on
  `RunRecord`. AC-0.1..AC-0.5 PASS; independent audit 6/6 PASS.
- **Localization method selection:** CLOSED — `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
  permanent. No V3.
- **Frozen scientific result (unchanged):** SALEOR_RESERVE_300_RMCSS — RM-CSS
  F1 0.3569 vs SIP 0.2647, Delta F1 +0.0921 CI [+0.0691,+0.1156]; secondary
  cross-repo transfer PASS.
- **Remaining untouched Saleor RESERVE:** 786 tasks (outcomes unread).
- **Next candidate scientific work package:** WP-1 Repository-Agent
  Selection-Only Baseline — AWAITING AHMED AUTHORIZATION. NOT started.
- **Pending:** WP-2 E2E Phase-0 instrument (DEFERRED); G6 F2P/P2P oracle
  (DEFERRED/unresolved).
- **No E2E scientific claim exists yet.** No Smoke / Pilot / Research Run.
- **Blockers:** none for the current integration closure. Historical
  human-audit and Stage-5 final-policy blockers are superseded (method-search
  phase CLOSED).

## Historical per-experiment records

The full-suite state and closure blocks below are retained as historical
records of prior, already-closed experiments (PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2,
ISSUE_GROUNDED_INTENT_HEADROOM, STAGE5_V2_FINAL). They are NOT active
execution state.

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
- **Status:** WP-0 acceptance criteria all PASS; integrated into `main` via
  fast-forward (commit `6eb0b2c`); no scientific tag; no E2E scientific claim.
  Legacy fixture behavior is explicit-opt-in only via
  `allow_ground_truth_universe` (default False), auditable on `RunRecord`.

**Next step (NOT started):** WP-1 Repository-Agent Selection-Only Baseline —
AWAITING AHMED AUTHORIZATION. WP-2 E2E Phase-0 instrument DEFERRED. G6 oracle
unresolved. No Smoke / Pilot / Research Run. No E2E scientific claim allowed.
