# PROGRESS.md — Execution Source of Truth

<!-- LIVE_STATUS:BEGIN -->

## LIVE STATUS — single current-state source of truth

**Position:** G12 (agent context hygiene, D1 APPROVED) is applied zero-API: the selection loop now echoes each action with its arguments, shows a call counter before every non-final call, names the exact repeated request in the rejection warning, and marks truncated reads. Gate v3 (CG-12: no task with >= 3 consecutive rejected repeats) FAILS Calibration-3b prospectively (runs 1/6/4; 52% of spend on repeats) — the RED proof. Calibration-3c (same 3 tasks, protocol v3, gate v3, NOT scored, <= $0.25) is next. MAIN_297 + variance + scoring remain NOT authorized (D3 = MANUAL = stop after Calibration-3c).

**Research pipeline:**

| Step | Status | Note |
| :---|:---|:---|
| Localization method selection | CLOSED | RM-CSS frozen; Saleor-300 PASS (+0.0921 F1) |
| WP-0 leakage fix (G7) | DONE | ArtifactUniverse built from the parent repository |
| WP-1a preparation | DONE | zero API; frozen predictions, manifests, agent protocol |
| WP-1b preflight freeze | DONE | G1 delta=0.05 · G2 cap 1024 · n=297 · budget v2 · rules v2 |
| WP-1b Calibration-3 | DEFECT | v1 gate PASS, $0.081, 24 calls — 0 successful reads; INSTRUMENT_INVALID |
| Tool-budget fix + gate v2 | DONE | D2: search_text does not consume the 30-file budget; CG-10/CG-11 written; RED on Calibration-3 |
| WP-1b Calibration-3b | PASS | gate v2 PASS · $0.070 · 3 reads · 0 instrument errors · 11/21 calls rejected repeats (loop) |
| G12 agent context hygiene | DONE | D1 APPROVED, zero API: echo, call counter, named rejection, truncation note; gate v3 CG-12 FAILS 3b (runs 1/6/4); protocol v3 |
| WP-1b Calibration-3c | NOT STARTED | same 3 tasks, protocol v3, gate v3, NOT scored, ceiling $0.25; then STOP (D3 MANUAL) |
| WP-1b MAIN_297 + variance 15x3 | BLOCKED | forbidden this mission (D3 MANUAL); requires a separate decision after 3c |
| WP-2 shared E2E instrument | NOT STARTED | same generator/validator/repair for every arm |
| E2E-G6 F2P/P2P oracle | NOT STARTED | fail-to-pass + pass-to-pass tests per task |
| E2E Smoke → Pilot → Research Run | NOT STARTED | staged; each stage can stop the run |

**LLM-call accounting:**

| Workflow | Calls | Note |
| :---|:---|:---|
| SIP on Saleor-300 | 300 coder calls (1/task) | 315 HTTP attempts incl. retries · 5.09 M tokens · $1.593 |
| RM-CSS on top of SIP | 0 extra coder calls | local logistic regression + repository memory |
| Qwen embeddings (RM-CSS) | 33 batched calls | 2,076 file units + 299 queries · $0.026 |
| WP-1b Calibration-3 agent | 24 calls (8/task) | $0.081 · 7 of 24 were rejected repeats · 0 successful reads (INSTRUMENT_INVALID) |
| WP-1b Calibration-3b agent | 21 calls (5/8/8) | $0.070028 · 3 successful reads · 0 instrument errors · gate v2 CG-1..CG-11 PASS · loop: 11/21 rejected repeats |
| WP-1b G12 (zero API) | 0 | agent context hygiene amendment D1 APPROVED: echo, call counter, named rejection, truncation note; gate v3 CG-12 FAILS 3b |
| WP-1b Calibration-3c agent (ceiling) | <= 24 calls | same 3 tasks, protocol v3, gate v3, not scored; ceiling $0.25; authorized |
| MAIN_297 agent (ceiling) | ≤ 2,376 calls | 297 × 8; not authorized |
| Variance substudy (ceiling) | ≤ 360 calls | 15 tasks × 3 runs × 8 |
| E2E generation + repair | not frozen yet | defined by WP-2 |

**Authorized / not authorized:**

| Item | Status | Note |
| :---|:---|:---|
| Calibration-3b (Phase C) | AUTHORIZED | D4 = YES, ceiling $0.25, paired revalidation of the D2 tool fix |
| MAIN_297 + variance 15×3 | NOT AUTHORIZED | requires D7 = YES after Ahmed reviews Calibration-3b |
| 786 Saleor RESERVE outcomes | SEALED | never opened/read/scored/sampled |
| Calibration-3 / Calibration-3b F1 claims | NOT PERMITTED | instrument checks only; no labels loaded or scored |

**Next action:** Run Calibration-3c on the same 3 calibration tasks (protocol v3, gate v3, not scored, ceiling $0.25). Per D3 = MANUAL the mission STOPS after Calibration-3c regardless of outcome; MAIN_297 + variance + scoring require a separate explicit decision. No label loading; no F1.

**End-to-end status:** WP-2 has **not started**; E2E-G6 F2P/P2P oracle has **not started**; **no** E2E Smoke, Pilot or Research Run exists yet.

*Source: `docs/LIVE_STATUS.json` (schema `live_status_v1`), rendered by `scripts/render_live_status.py`. As of 2026-09-22 05:09 (Africa/Cairo).*
<!-- LIVE_STATUS:END -->

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `wp1b/calibration-3b-2026-09-21` (T3 mission
`WP1B_TOOLFIX_LIVESTATUS_2026-09-21`; Phase C = Calibration-3b, D4 YES, ceiling
$0.25; Phases A/B merged to `main` `f6c858b` with tag
`wp1b-toolfix-2026-09-21`)
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
**Task:** WP1B_TOOLFIX_LIVESTATUS_2026-09-21 (T3) - **COMPLETE: DECISION =
CALIBRATION_3B_DONE(CG-1..CG-11 PASS).** Calibration-3 reclassified
**`GATE_V1_PASS / INSTRUMENT_INVALID`** (D1). D2 fix
(`WP1B_G11_TOOL_BUDGET_2026_09_21`): `search_text` no longer consumes
`MAX_DISTINCT_FILES`; `read_file` keeps 30. Gate v2 (CG-10/CG-11) FAILS on old
Calibration-3 (RED) and **PASSES on Calibration-3b (GREEN)** — 21 calls, 3
successful reads, 0 instrument errors, $0.070028 ≤ $0.25, cost ratios ≤ 1.2.
A4 telemetry (tool_ok/tool_error + search telemetry). LIVE_STATUS single source
of truth rendered into FOUR current-facing files. README/GLOSSARY/AGENTS.md
updated. **STOP after Phase C (contract §6 step 7).** MAIN_297/variance NOT
authorized (D5/D7 NO) — requires a separate explicit Ahmed decision after he
reviews Calibration-3b. 786 sealed RESERVE outcomes untouched.
**Previous task - WP-1b Calibration-3 (2026-09-21; D6 YES, ceiling $0.25):**
**COMPLETE: DECISION = CALIBRATION_DONE(CG-1..CG-9 PASS)** ($0.081142; 24
calls; 0 cap hits; 0 EMPTY; 0 observation truncation) — **subsequently
reclassified `GATE_V1_PASS / INSTRUMENT_INVALID`** by the tool-budget defect
mission (D1).
Previous task - SALEOR_RESERVE_300_RMCSS
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
- **WP-1b Calibration-3 (2026-09-21):** EXECUTED (D6 YES, $0.081142, 24 calls,
  v1 gate CG-1..CG-9 PASS) — **reclassified `GATE_V1_PASS / INSTRUMENT_INVALID`**
  (D1) by the tool-fix mission: the agent's tools were blind (0 successful
  reads).
- **WP-1b tool-fix + gate v2 + LIVE_STATUS (2026-09-21, ZERO API):**
  D2 fix `WP1B_G11_TOOL_BUDGET_2026_09_21` (`search_text` no longer
  consumes `MAX_DISTINCT_FILES`; `read_file` keeps 30); gate v2 (CG-10/CG-11)
  FAILS on old Calibration-3 (RED); A4 telemetry; `docs/LIVE_STATUS.json` +
  renderer + 4 rendered blocks.
- **WP-1b Calibration-3b (2026-09-21, Phase C, D4 YES):** **COMPLETE —
  DECISION = `CALIBRATION_3B_DONE(CG-1..CG-11 PASS)`.** 21 calls, 3 successful
  reads, 0 instrument errors, $0.070028 ≤ $0.25, cost ratios 0.405/0.626/0.547
  (≤ 1.2). Agent instrument-valid. STOP after Phase C. MAIN_297/variance NOT
  authorized (D5/D7 NO).
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
- **Next candidate scientific work package:** MAIN_297 — requires a separate
  explicit Ahmed authorization (D7) after he reviews the Calibration-3b
  evidence.
- **Pending:** WP-2 E2E Phase-0 instrument (DEFERRED); E2E-G6 F2P/P2P oracle
  (DEFERRED/unresolved).
- **No E2E scientific claim exists yet.** No Smoke / Pilot / Research Run.
- **Blockers:** MAIN_297 is BLOCKED on D7 = YES. The agent is instrument-valid
  (gate v2 PASS on Calibration-3b); no further paid run is permitted in this
  mission.

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

## WP-1b Preflight Freeze (2026-09-21) - Phase 0/A/B COMPLETE (T3; zero API)

**Task:** WP1B_PREFLIGHT_FREEZE_2026-09-21. **Branch:**
wp1b/preflight-freeze-2026-09-21. **Tier:** T3. **Scientific API spend:**
\.00 through Phases 0/A/B. Pre-result freeze; no paid inference yet.

- **Phase 0 (git sync):** origin/main was at 87c86f5; pushed local main 1ae7058
  (push succeeded on the 60s retry after an initial network failure); verified
  local main == origin/main == 1ae7058 via ls-remote; branch created.
- **Phase A1 (test mutation):** the four WP-1 generator entry points
  (wp1a_independent_audit, wp1a_acceptance_report, wp1b_closure_recompute,
  wp1b_variance_substudy_selection) now accept --out <dir> so tests redirect
  outputs to a pytest tmp_path; default human-run behaviour byte-identical.
  NEW artifacts store repository-relative POSIX paths. Added
  tests/unit/test_no_tracked_artifact_mutation.py (6 tests) proving the four
  generators do not mutate tracked artifacts/ and research/wp1a/ files.
  Absolute-path leak recorded as a cosmetic defect in DECISIONS.md (frozen
  artifacts not rewritten). A1 acceptance: targeted WP-0/WP-1 suite green,
  git status --porcelain empty (AC-P1/AC-P2).
- **Phase A2 (name the 5 pre-existing failures):** full suite on clean checkout
  = 5 failed / 3700 passed / 35 skipped. Recorded node IDs + classes in
  docs/KNOWN_TEST_FAILURES_2026-09-21.md and
  artifacts/known_test_failures_2026-09-21.json (REAL_DEFECT x3,
  ENV_OR_DATA_MISSING x2). New full-suite acceptance rule: failing node-ID set
  == known list (AC-P3). TODO.md REAL_DEFECT entries added.
- **Phase A3 (audit packet v2):** exports/wp1a_independent_audit_packet_2026-09-21_v2/
  (v1 untouched) adds the coefficient-order trap (lr_coef = continuous +
  boolean, NOT feature_names; 0/300 vs 174/300) and the FULL-only inputs list
  (public candidate_universe.json / dependency_graph.json / saleor manifest).
- **Phase A4 (export member):** restored the provenance-verified D13R2
  pilot-kaggle-upload.zip (SHA 65269528...) from _historical_archive into dist/
  so the FULL export includes it; DECISIONS.md line.
- **Appendix R re-derivation:** every R number independently re-derived with
  scripts/wp1b_appendix_r_rederivation.py; 125 comparisons, 0 disagreements,
  status ALL_AGREE (research/wp1b/wp1b_appendix_r_agreement.json).
- **Phase B1 (budget v2, G8):** research/wp1b/wp1b_budget_model_v2.json. Real
  ArtifactUniverse per task (production path, allow_ground_truth_universe=False)
  + exact initial prompt rendered; worst case (8 calls, cap 1024); totals for
  Calibration-3/Main-50/150/297/variance(15x3) x1.5; NO ceiling below worst case
  x1.5 (cal 0.202<=0.25; main-297 18.640<=21.50; variance 3.025<=3.50);
  underestimate factor ~3.40x vs v1. Abort rule v2 preregistered (AC-P6).
- **Phase B2 (sample-size, G9):** wp1b_main_297_manifest.json (n=297, first 50
  == WP-1a MAIN_50 exact, calibration absent, hashes recorded),
  wp1b_main_150_manifest.json (n=149; one calibration task removed),
  wp1b_main_50_manifest.json (unchanged). Power doc
  docs/WP1B_POWER_AND_SAMPLE_SIZE_2026-09-21.md re-derives R-C (AGREE) (AC-P7).
- **Phase B3 (freeze G1):** research/wp1b/wp1b_ni_margin_frozen.json +
  docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md (Delta=0.05, Q5 rule, inheritance,
  coherence anchor, relative size) (AC-P8).
- **Phase B4 (decision rules v2):** research/wp1b/wp1b_decision_rules_v2.json
  (P/S dual analysis, seven ordered quality verdicts, cost CHEAPER rule, five
  final categories; 'dominance' retired) (AC-P9).
- **Phase B5 (freeze G2):** DECISIONS.md WP1B_G2_COMPLETION_CAP_2026_09_21
  EFFECTIVE (D3); research/wp1b/wp1b_frozen_agent_protocol_v2.json (cap 1024);
  tests/unit/test_wp1b_g2_cap_freeze.py asserts 1024 + frozen SIP/RM-CSS
  artifacts unchanged (AC-P10).
- **Phase B6 (agent telemetry, G10):** additive per-call sidecar JSONL +
  per-task observation metrics in iterative_agent.py + telemetry.py; behavior
  preservation proven by stub-backend golden test
  (tests/unit/test_wp1b_agent_telemetry_golden.py); disclosure
  docs/WP1B_AGENT_BASELINE_DISCLOSURE_2026-09-21.md (AC-P11).
- **Phase B7 (exploratory prereg):** research/wp1b/wp1b_exploratory_prereg.json
  X1-X5, status EXPLORATORY_PREREGISTERED, only after primary frozen/tagged
  (AC-P12).
- **Validation:** ruff PASS, mypy strict PASS (production files), git diff
  --check PASS; targeted WP-0/WP-1 suite 47 passed; no new artifact contains an
  absolute machine path (AC-P13); API spend \.00 (AC-P14).

**Next step:** B8 integration (merge --no-ff to main, annotated tag
wp1b-preflight-freeze-2026-09-21, push main + tag, PROGRESS/00_CURRENT/
START_HERE updates, TRUE LIGHT export), then Phase C Calibration-3 (D6 YES,
cap 1024, ceiling 0.25). MAIN_297/variance NOT authorized (D7 NO) until Ahmed
reviews the Calibration-3 STOP report.

## WP-1b Calibration-3 (2026-09-21) - EXECUTED; STOP after Phase C (D7 = NO)

**Phase C run (D6 YES, ceiling \.25):** exactly the 3 tasks in
research/wp1a/wp1_calibration_3_manifest.json with protocol v2 (cap 1024),
frozen qwen/qwen3-coder @ deepinfra/turbo, temp 0.0. Ran via
scripts/wp1b_calibration_run.py into research/wp1b/calibration-3-2026-09-21/.

- **Cost:** cumulative \.081142 <= \.25 (per task 0.033858 / 0.031420 /
  0.015865). Per-task / B1 worst-case ratios 0.636 / 0.617 / 0.523 - all
  within 1.2x (BUDGET_MODEL_V2_OK).
- **Gate:** CG-1..CG-9 all PASS.
- **Instrument:** 0 cap hits, 0 observation truncations, 0 EMPTY (all valid
  finals), finish-reason distribution 24x stop; 24 per-call sidecar records.
- **Not scored against labels** (instrument check only).
- **STOP after Phase C:** the main run (MAIN_297) and the variance substudy
  are NOT authorized (D7 = NO). MAIN_297 requires a new explicit Ahmed
  authorization after he reviews the Calibration-3 STOP report.
- Branch: wp1b/calibration-3-2026-09-21 (calibration records + gate result).

**Next step:** Ahmed reviews the Calibration-3 STOP report; then a new
authorization (D7 = YES) is required before MAIN_297 / variance. The 786 sealed
Saleor RESERVE outcomes remain untouched.
