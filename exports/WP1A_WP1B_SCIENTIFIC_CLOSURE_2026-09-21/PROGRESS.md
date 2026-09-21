# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main` (WP-1a closure work INTEGRATED 2026-09-21 via --no-ff merge
`18652d6` "chore(wp1a): close integration and preregister WP1b blockers")
**Scientific closure commit:** `8b2d1b6` (merge of
`research/oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific
fact)
**Scientific closure tag peel:** `8b2d1b6` (tag
`oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific fact)
**Live HEAD / origin/main:** runtime git facts — a tracked file cannot embed
its own final live HEAD SHA (committing metadata changes HEAD again). Query
at read time: `git rev-parse HEAD`, `git rev-parse origin/main`,
`git status --porcelain`.
**Model:** openrouter/deepseek/deepseek-v4-flash-0731 (OpenCode coding model;
NOT the WP-1 scientific arm model — the frozen SIP scientific model is
qwen/qwen3-coder @ deepinfra/turbo, see research/wp1a/)
**Task:** WP-1a INTEGRATION CLOSURE → WP-1b READINESS (2026-09-21; T3; ZERO
API; $0.00 scientific spend) - **COMPLETE: DECISION = BLOCKED (WP-1b not
ready for authorization).** Independent raw-evidence recomputation PASS (sample
hash, main/cal disjointness, pooled SIP/RM-CSS F1, per-task hashes, v1.1
truncation evidence); G1 NI margin = DECISION REQUIRED (no margin frozen; no
margin invented; decision-required doc
`docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md`); G2 completion cap =
DECISION REQUIRED (512 pilot-derived vs 1024 v1.1; provenance + proposed
amendment documented); G3 loop-termination semantics instrumented (telemetry +
tests, behavior-preserving); G4 audit terminology corrected (same-session
cross-check, NOT independent audit) + blind independent-audit packet prepared;
G5 variance substudy preregistered (15 of main-50, salt frozen); G6 pricing
preflight PASS (live OpenRouter metadata, no drift); Calibration-3 gate frozen
before inference; WP-1a integration closure table recorded; merged to `main`
(`18652d6`); post-merge re-audit from main PASS (146 targeted passed + 1
skipped; full suite 3700/35/5 where the 5 failures are PRE-EXISTING baseline
failures also present at `f25950f`); FULL + TRUE LIGHT exports produced. WP-1a
preparation AC-1A.1..AC-1A.12 ALL PASS. WP-1b
NOT started. Previous task - SALEOR_RESERVE_300_RMCSS
(2026-09-20; PRIMARY `SALEOR_RESERVE_300_RMCSS_PASS` + SECONDARY
`SECONDARY_CROSS_REPO_TRANSFER_PASS`; RM-CSS F1 0.3569 vs SIP 0.2647, Delta F1
+0.0921 CI [+0.0691,+0.1156]).

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

## Current active state (2026-09-21, normalized)

- **Phase:** 5 — End-to-End Selective Regeneration.
- **WP-0 (G7) ground-truth leakage fix:** COMPLETE and merged into `main`
  (fast-forward integration). `ArtifactUniverse` is now derived from the
  parent-commit repository state; legacy fixture behavior is behind an
  explicit `allow_ground_truth_universe` flag (default False), auditable on
  `RunRecord`. AC-0.1..AC-0.5 PASS; independent audit 6/6 PASS.
- **WP-1a (2026-09-21):** Repository-Agent Selection Baseline PREPARATION
  COMPLETE + INTEGRATION CLOSURE merged to `main` (`18652d6`). AC-1A.1..
  AC-1A.12 ALL PASS; same-session cross-check 19/19 (NOT an independent audit);
  50 new unit tests + WP-1b closure tests; ruff/mypy
  strict/py_compile/git diff --check PASS. Scientific API spend $0.00.
- **WP-1b readiness (2026-09-21):** DECISION = **BLOCKED**. G1 NI margin and
  G2 completion cap require prospective decisions; paid WP-1b is FAIL-CLOSED
  until both are frozen. G3 loop semantics instrumented; G4 audit terminology
  corrected + independent-audit packet prepared; G5 variance substudy
  preregistered; G6 pricing preflight PASS; Calibration-3 gate frozen before
  inference. Full closure deliverables under `docs/WP1B_*`,
  `artifacts/wp1b_*`, `exports/`.
- **Localization method selection:** CLOSED — `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
  permanent. No V3.
- **Frozen scientific result (unchanged):** SALEOR_RESERVE_300_RMCSS — RM-CSS
  F1 0.3569 vs SIP 0.2647, Delta F1 +0.0921 CI [+0.0691,+0.1156]; secondary
  cross-repo transfer PASS.
- **WP-1 frozen artifacts:** `research/wp1a/` (model provenance, label-free
  schema, per-task predictions + SHA-256, re-derivation verification, main-50
  + calibration-3 manifests, intent parity, frozen agent protocol, failure
  semantics, shared scorer schema, accounting schema, budget model,
  cost-quality categories, same-session cross-check, acceptance report).
- **Remaining untouched Saleor RESERVE:** 786 tasks (outcomes unread).
- **Next candidate scientific work package:** WP-1b Repository-Agent
  Calibration + Main n=50 Selection Run — BLOCKED until (1) an F1
  non-inferiority margin is prospectively frozen (G1) and (2) the agent-control
  completion cap is decided (G2). After that, a fresh Ahmed spend authorization
  is required.
- **Pending:** WP-2 E2E Phase-0 instrument (DEFERRED); G6 F2P/P2P oracle
  (DEFERRED/unresolved).
- **No E2E scientific claim exists yet.** No Smoke / Pilot / Research Run.
- **Blockers:** G1 (NI margin decision required) and G2 (completion-cap
  decision required) block paid WP-1b. No spend authorization exists.

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

**Next step (NOT started):** WP-1b Calibration + Main n=50 Selection Run —
AWAITING AHMED AUTHORIZATION (WP-1a preparation COMPLETE; see
`research/wp1a/`). WP-2 E2E Phase-0 instrument DEFERRED. G6 oracle
unresolved. No Smoke / Pilot / Research Run. No E2E scientific claim allowed.
