# PROGRESS.md — Execution Source of Truth

<!-- LIVE_STATUS:BEGIN -->

## LIVE STATUS — single current-state source of truth

**Position:** Mission-10A environment test-dependency audit COMPLETE (zero-API). PROVEN declared-but-not-installed: pytest-django-queries + pytest-mock omitted from frozen V2; explains 41/41 P2P-U cap200 COLLECTION_ERROR and 98.7% of py312 C4 error-TOI records. Scratch probe task 1 recovered 18/18 SET A nodes to P2P_ONLY, but SET B non-regression FAILED (1 V2 BEHAVIORAL_F2P node flipped to P2P_ONLY, V2 JWT iat clock-skew flake). DECISION TOKEN = ENV_AUDIT_INCONCLUSIVE; probe stopped per preregistered S2. No generation/Smoke/DEV-47/HOLDOUT/VALIDATION/MAIN execution. MAIN quarantined; INTERNAL_TEST untouched; 786 RESERVE sealed.

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
| WP-1b Calibration-3c | PASS | gate v3 CG-1..CG-12 PASS · $0.063205 · 4 reads · 1/18 rejected (5.6%) · longest run 1 · 0 blocking review-card flags · NOT scored |
| WP-1b MAIN_297 + variance 15x3 | DONE | RMCSS_NONINFERIOR_AT_LOWER_COST (NI_SUPPORTED); main $7.15 + variance $1.19; scored with decision rules v2; X1-X11 exploratory |
| WP-1b post-MAIN_297 docs closure + claim sheet | DONE | claim sheet, robustness/limitations, README/FAQ updated; zero API |
| AG16 budget sensitivity (MAIN_50) | PREREGISTERED, NOT RUNNABLE | brain-built/tested bundle required first (iterative_agent_budget.py + golden parity + dry-run); ceilings $0.80 cal / $12.20 MAIN_50 |
| WP-2 zero-API MAIN_297 census | DONE | 297/297 materializable; 20 STRONG / 200 MODIFIED / 77 no-test-evidence F2P candidates; proposal-only Smoke candidates 8; zero API |
| WP-2 Oracle Confirmation + Design v1 | DONE (zero-API) | harness validated; 220/220 changed-test candidates attempted; 8 primary behavioral F2P + 1 symbol-absence eligible; causal Design v1, power planning, Smoke v2 emitted; environment-dominant blocker on this host |
| WP-2 shared E2E instrument | NOT STARTED | same generator/validator/repair for every arm |
| E2E Smoke → Pilot → Research Run | NOT STARTED | staged; each stage can stop the run |
| WP-2 preservation oracle (P2P-S + P2P-U V2) | FROZEN (Mission-09) | P2P-S 46/47 defined; P2P-U V2 rule+membership frozen; ENG cap200+cap400 executed, repeatability 1.0 |
| Mission-10A environment test-dependency audit | DONE (ENV_AUDIT_INCONCLUSIVE) | proven pytest-django-queries/pytest-mock declared-but-not-installed in V2; 41/41 P2P-U cap200 COLLECTION_ERROR explained; probe recovered 18/18 SET A but SET B non-regression failed (1 V2 node flip, JWT iat clock-skew); STOP probe; no V3 |
| Full DEV-47 P2P-U cap200 execution | NOT STARTED (awaits approval) | est ~4.9-8.1 h serial central 6.7 h; overnight-feasible with resume; zero-node tasks UNDEFINED |

**LLM-call accounting:**

| Workflow | Calls | Note |
| :---|:---|:---|
| SIP on Saleor-300 | 300 coder calls (1/task) | 315 HTTP attempts incl. retries · 5.09 M tokens · $1.593 |
| RM-CSS on top of SIP | 0 extra coder calls | local logistic regression + repository memory |
| Qwen embeddings (RM-CSS) | 33 batched calls | 2,076 file units + 299 queries · $0.026 |
| WP-1b Calibration-3 agent | 24 calls (8/task) | $0.081 · 7 of 24 were rejected repeats · 0 successful reads (INSTRUMENT_INVALID) |
| WP-1b Calibration-3b agent | 21 calls (5/8/8) | $0.070028 · 3 successful reads · 0 instrument errors · gate v2 PASS · loop: 11/21 rejected repeats |
| WP-1b G12 (zero API) | 0 | agent context hygiene amendment D1 APPROVED: echo, call counter, named rejection, truncation note; gate v3 CG-12 FAILS 3b |
| WP-1b Calibration-3c agent | 18 calls (4/8/6) | $0.063205 · 4 successful reads · 1/18 rejected repeats (5.6%) · longest run 1 · gate v3 CG-1..CG-12 PASS · NOT scored |
| MAIN_297 agent | 2,164 logical / 2,178 HTTP attempts | ledger $7.147 · 23.55M prompt / 81.7K completion tokens · 147 forced finals · 2 EMPTY (parser_failure) · 8 transport retries |
| Variance substudy 15x3 | 331 logical / 341 HTTP attempts | ledger $1.194 · pooled F1 0.389/0.438/0.479 · pairwise exact match 0.444 · 0 EMPTY |
| WP-2 zero-API MAIN_297 census | 0 | deterministic read-only git diff over already-opened case metadata; $0.00 |
| E2E generation + repair | not frozen yet | defined by WP-2 |

**Authorized / not authorized:**

| Item | Status | Note |
| :---|:---|:---|
| Calibration-3c | DONE (CLEAN) | gate v3 CG-1..CG-12 PASS; $0.063205; NOT scored |
| MAIN_297 + variance 15×3 + scoring | DONE (D3 = YES) | RMCSS_NONINFERIOR_AT_LOWER_COST (NI_SUPPORTED); main $7.15 + variance $1.19; predictions frozen/tagged before any label load |
| Agent budget-sensitivity arm (AG16, MAIN_50) | PREREGISTERED, NOT AUTHORIZED; runner NOT built | design frozen before MAIN_297 outputs; needs brain-built/tested bundle + decision D6 |
| WP-2 zero-API MAIN_297 census | DONE | deterministic planning evidence only; no E2E execution; no F2P/P2P oracle |
| WP-2 Oracle Confirmation (zero-API) + Design v1 | DONE | 8 primary behavioral F2P + 1 symbol-absence eligible confirmed; causal Design v1 + power planning + Smoke v2 proposal; NO E2E execution |
| 786 Saleor RESERVE outcomes | SEALED | never opened/read/scored/sampled; guarded by the label-access audit hook |
| Calibration-3 / 3b / 3c F1 claims | NOT PERMITTED | instrument checks only; no labels loaded or scored |
| Mission-09 P2P-S + P2P-U V2 freeze | DONE | zero-API; P2P-S (46/47) + P2P-U V2 rule/membership frozen before any V2 outcome execution |
| Mission-09 ENG P2P-U V2 execution (cap200 + cap400) | DONE | 8 executable ENG tasks x 2 caps, workers=1, 3+3 reps, integrity PASS; no Smoke/full-DEV/MAIN execution |
| Mission-10A environment test-dependency audit (zero-API, Tier T3) | DONE (ENV_AUDIT_INCONCLUSIVE) | proven declared-but-not-installed dev/test group in frozen V2; ENG-only scratch probe (task 1) recovered 18/18 SET A; SET B non-regression FAILED (1 V2 BEHAVIORAL_F2P node flip) -> STOP per preregistered S2; no V3 build, no generation, no Smoke |
| Full DEV-47 P2P-U cap200 + Smoke freeze | NOT AUTHORIZED | requires Ahmed decision; estimates ready (DEV ~6.7 h central) |

**Next action:** Ahmed decision (ENV_AUDIT_INCONCLUSIVE): approve targeted follow-up = (1) V2 BEHAVIORAL_F2P node flakiness audit (JWT iat clock-skew class), (2) complete probe task 2 + SET B under clock-skew-robust harness, (3) re-decide V3/V2/INCONCLUSIVE. No generation, Smoke, DEV-47, HOLDOUT, VALIDATION, or MAIN execution.

**End-to-end status:** WP-2 has **not started**; E2E-G6 F2P/P2P oracle has **not started**; **no** E2E Smoke, Pilot or Research Run exists yet.

*Source: `docs/LIVE_STATUS.json` (schema `live_status_v1`), rendered by `scripts/render_live_status.py`. As of 2026-09-26 (Africa/Cairo).*
<!-- LIVE_STATUS:END -->

## MISSION-10A — GOAL -> OUTCOMES -> DRIVERS -> ACTIONS -> SCHEDULE -> TRACKING -> REFLECTION

**GOAL:** Reach the first generated-patch experiment with a scientifically
valid, historically reproducible, frozen environment/evaluator.

**OUTCOMES:**
- environment completeness decision closed (decision token **ENV_AUDIT_INCONCLUSIVE**)
- error-TOI causes explained quantitatively (41/41 P2P-U cap200; 98.7% of py312 C4 error records)
- V2 kept or V3 recommended based on preregistered evidence (probe recovered 18/18 SET A, but S2 non-regression failed)
- no generation before freeze
- all five evaluation dimensions retain a valid measurement substrate

**DRIVERS:** historical lockfile fidelity · declared test dependency
completeness · plugin load correctness · node-level non-regression ·
deterministic evidence · leakage firewall.

**ACTIONS:** Mission-10A audit -> decision (ENV_AUDIT_INCONCLUSIVE) -> STOP.

**SCHEDULE:** current mission only; no V3/Smoke execution scheduled
automatically.

**TRACKING:**
- error taxonomy coverage: C4 3,682 error-TOI / P2P-U 41 / C2 rescue 3,304
- declared-but-not-installed %: 37/37 cause rows; 41/41 P2P-U nodes
- probe recovered nodes: 18/18 (task 1 SET A)
- non-regression count: 55/56 unchanged; 1 transition
- audit decision token: **ENV_AUDIT_INCONCLUSIVE**
- commit/tag/export: see STOP report

**REFLECTION:**
1. Evidence that changed our understanding: the V2 parent failure for
   `test_update_voucher` was a JWT `iat` clock-skew flake that resolved to
   P2P_ONLY on re-execution — V2 oracle classification instability, not a
   dependency defect.
2. Earlier assumption wrong: "pytest 'error' == collection error" — the 41
   P2P-U nodes are SETUP (missing fixture), and the C4 error majority is
   DB/migration environment, not missing test plugins.
3. What saved time: reusing frozen V2 exec/runner patterns for the scratch
   probe and the deterministic taxonomy in the shared audit module.
4. Single next change with highest validity/productivity payoff: a
   clock-skew-robust oracle + V2 BEHAVIORAL_F2P flakiness audit before any
   Env V3 freeze.

**NORTH STAR:** Number of tasks eventually evaluated E2E across ALL five
dimensions under a frozen, valid environment/evaluator (localization-only tasks
do not count).

## MISSION-10B — GOAL -> OUTCOMES -> DRIVERS -> ACTIONS -> SCHEDULE -> TRACKING -> REFLECTION

**GOAL:** Produce a valid frozen evaluator/harness and reach ENG Smoke
readiness without spending API/model budget prematurely. Harness V3 is an
infrastructure-only correction (nofile / DB lifecycle / lock-exact
dependencies / clock preflight); oracle scientific semantics stay unchanged.

**OUTCOMES (so far):**
- corrected root-cause attribution: node-level, not task-level
- V3 decision (pending Phase-4 mechanical gate)
- recovered valid oracle coverage if warranted
- zero clean-node regressions (S2' target)
- ENG Smoke-ready evaluator (gate-gated)
- full C4 corrected if gate passes

**DRIVERS:** node-level causal attribution · FD headroom · DB isolation ·
historical lock fidelity · clock stability · deterministic concurrency ·
evidence integrity.

**ACTIONS:** RCA -> freeze -> 4-task w1 probe -> gate -> w2 equivalence ->
ENG C4 -> P2P-S/P2P-U ENG -> ENG_SMOKE_READY -> remaining C4.

**SCHEDULE:** Phase-1 RCA COMPLETE (2026-09-26). Phases 2-4 next (freeze,
probe, gate). Phase 5 auto-continues iff Phase-4 gate passes.

**TRACKING (Phase-1 durable results):**
- C4 reconciliation exact: 3,727 = 2,592 STABLE + 1,055 MIXED + 35 MISSING +
  45 FAILED_ONLY (mismatch 0)
- materiality: 2,592 stable-family nodes (INFRA 2,511 + MISSING_FIXTURE 81) /
  3,682 = 70.4% (node-level; >> 20% gate)
- EMFILE: 29 C4 tasks (py38/py39), 9,676 target rep-records, 2,511 stable
  nodes (68.2% of error-TOI); C2 rescue 58/159; ENG 10 EMFILE tasks all
  NOT_PRIMARY
- EMFILE FIX EFFICACY: TRUE (A reproduces at nofile=1024 max 714 FDs; B at
  nofile=65536 max 2,287 FDs, 261 passed / 1 genuine behavioral fail)
- DB reuse: WRONG_CONSTRAINTS 1,095/1,098 WC-r2 nodes follow EMFILE-r0 in the
  same (task,state) DB -> partial-DB reuse SUPPORTED
- install failures: C4 24/24 + C2 60/60 = LOCKFILE_INCOMPATIBILITY (V2 never
  used historical lockfiles; dev/test group omitted)
- clock: host<->WSL skew -1.85s (WARN); container +0.9-1.1s ahead of WSL;
  AT_RISK_F2P C4=2 C2=1 (JWT iat ImmatureSignatureError)
- probe tasks lockfile: all poetry.lock; exact dev versions extracted
- Phase-3 4-task ENG probe (workers=1): ALL COMPLETE. c3b9e396b07d 416 TOI->1,
  e25cf9b4a837 252 TOI->0, 74538ea00ce9 0 TOI (1 V2_DEFECT_CORRECTION:
  test_update_voucher JWT clock-skew), 8f76ddc6267f V3==V2. 667 V2-invalid
  nodes recovered to valid oracle classes. 0 EMFILE across all 66 V3 junit.
  integrity PASS on all 4.
- Phase-4 mechanical gate: **ALL PASS** -> TOKEN=HARNESS_V3_RECOMMENDED,
  AUTO-CONTINUE Phase 5 (gate.json/gate.md). MATERIALITY 2592/3647=71.1%,
  RECOVERY 667, FIX_EFFICACY PASS, SAFETY PASS, REGRESSIONS=0,
  V2_DEFECT_CORRECTIONS=1.
- decision token: **HARNESS_V3_RECOMMENDED (Phase-4 gate passed)**
- commit/tag/export: see STOP report at mission end

**REFLECTION (Phase 1):**
1. Evidence that changed understanding: node-level STABLE_CAUSE shows EMFILE
   is the dominant C4 TOI cause (68%), and WRONG_CONSTRAINTS is NOT an
   independent cause — it is the reuse of an EMFILE-partial DB (1,095/1,098
   nodes). Mission-10A's truncated parser missed this because it never
   read full error text.
2. Earlier assumption wrong: the C4 error majority is not "DB/other" but
   specifically INFRA:EMFILE during test-DB creation/migrations, hidden by
   V2's default nofile=1024 container limit.
3. What saved time: reusing frozen V2 runner/exec patterns, the Mission-09
   resource sampler concept, and the frozen era images as the V3 base runtime
   (no new image build).
4. Single highest-payoff next step: freeze Harness V3 + run the 4-task ENG
   probe under workers=1, then evaluate the Phase-4 mechanical gate.
5. Phase-3/4 result: the Phase-4 gate passed (HARNESS_V3_RECOMMENDED) with
   667 V2-invalid nodes recovered under V3, 0 EMFILE residue, 0 regressions.
   The single V2_DEFECT_CORRECTION (test_update_voucher) confirms the
   clock-skew mechanism Mission-10A suspected.

**NORTH STAR:** Tasks eventually evaluated E2E across all five dimensions
under a frozen, valid, reproducible environment/evaluator.

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `wp1b/main-297-2026-09-22` (overnight mission
`OPENCODE_OVERNIGHT_WP1B_MAIN297_FULL_2026-09-22`; MAIN_297 + variance 15×3 +
scoring + X1–X11; result `RMCSS_NONINFERIOR_AT_LOWER_COST`, NI_SUPPORTED).
Main merged; result tag `wp1b-main297-result-2026-09-22`.
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

## Current active state (2026-09-22, normalized)

- **Phase:** 5 — End-to-End Selective Regeneration.
- **Localization method selection:** CLOSED — `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
  permanent; RM-CSS is the frozen method.
- **Frozen scientific result (unchanged):** SALEOR_RESERVE_300_RMCSS — RM-CSS
  F1 0.3569 vs SIP 0.2647, Delta F1 +0.0921 CI [+0.0691,+0.1156]; secondary
  cross-repo transfer PASS.
- **WP-1b MAIN_297 (2026-09-22):** COMPLETE and FROZEN. Primary result =
  `RMCSS_NONINFERIOR_AT_LOWER_COST` (decision rules v2, `NI_SUPPORTED`).
  P n=297: D −0.0062 [−0.0449,+0.0308], Q5 −0.0383. S n=295 (2 parser-failure
  EMPTY dropped): D −0.0115 [−0.0502,+0.0255], Q5 −0.0434. Agent F1 0.363 vs
  RM-CSS 0.357 vs SIP 0.265 (pooled micro-F1). RM-CSS cheaper (View A: 0.27×
  calls, 0.21× generative tokens/task). Variance 15×3 pooled F1
  0.389/0.438/0.479, pairwise exact match 0.444. X1-X11 exploratory labelled.
  Selection-stage result, NOT E2E. Run spend $7.15 (main) + $1.19 (variance);
  billed OpenRouter deltas are descriptive ($3.43 main, $0.62 variance) and are
  never the normalized cost verdict.
- **WP-1b post-MAIN_297 closure (2026-09-22, ZERO API):** claim sheet
  (`docs/WP1B_CLAIM_SHEET_2026-09-22.md`), robustness/limitations
  (`docs/WP1B_POSTHOC_ROBUSTNESS_AND_LIMITATIONS_2026-09-22.md`), README/FAQ
  correction, impact declaration committed before substantive edits, decision
  block appended to `DECISIONS.md`.
- **AG16 (budget sensitivity, MAIN_50):** PREREGISTERED, NOT RUNNABLE. Design
  frozen before MAIN_297 outputs (8 → 16 calls; 2000 → 8000 chars; ceilings
  $0.80 cal / $12.20 MAIN_50). A separate brain-built/tested bundle is
  required (`iterative_agent_budget.py` + golden parity `(8,2000)` + dry-run
  + AG16 calibration gating + parameterized paid runner + AG16 scoring).
  Readiness audit + brain handoff package:
  `docs/WP1B_AG16_READINESS_2026-09-22.md`,
  `research/wp1b/wp1b_ag16_harness_requirements_2026-09-22.json`,
  `exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/`. Zero paid calls this mission.
- **WP-2 zero-API MAIN_297 census (2026-09-22):** DONE, deterministic planning
  evidence only. 297/297 materializable in the local Saleor cache (0 metadata/
  materialization problems); read-only git diff parent..target; 20
  STRONG_F2P_CANDIDATE, 200 MODIFIED_TEST_CANDIDATE, 77 NO_CHANGED_TEST_EVIDENCE;
  never F2P_CONFIRMED. Environment feasibility recorded; proposal-only Smoke
  candidates (8) selected outcome-blind:
  `docs/WP2_MAIN297_ZERO_API_CENSUS_2026-09-22.md`, `research/wp2/`.
- **WP-2 Oracle Confirmation + Design v1 (2026-09-22, ZERO API):** deterministic
  harness built and validated (isolated worktrees, per-(task,state) test DB,
  per-file evaluator, frozen failure taxonomy). All 220 changed-test candidates
  attempted: **8 primary behavioral F2P + 1 symbol-absence F2P confirmed**;
  207 ENV_BROKEN (Windows host: native libs, `?` in filenames, Unix-only
  `resource` module); 2 FLAKY; 2 TARGET_ORACLE_INVALID. Environment-validity
  audit separated harness defects (fixed) from genuine blockers. WP-2 causal
  Design v1, power/assay-sensitivity planning, and Smoke proposal v2 emitted.
  See `docs/WP2_E2E_CAUSAL_DESIGN_V1_2026-09-22.md`,
  `docs/WP2_ORACLE_CONFIRMATION_REPORT_2026-09-22.md`,
  `research/wp2/wp2_oracle_environment_validity_audit_2026-09-22.json`.
- **Remaining untouched Saleor RESERVE:** 786 tasks (outcomes unread, never
  accessed).
- **Pending:** version-aware Saleor environment bundle (dominant blocker);
  WP-2 shared E2E instrument (NOT STARTED); E2E-G6 F2P/P2P oracle (NOT STARTED);
  Smoke / Pilot / Research Run (NOT STARTED). AG16 runner implementation (needs
  brain-built/tested bundle + D6 authorization).
- **No E2E scientific claim exists yet.** No Smoke / Pilot / Research Run.
- **Next:** Brain/Ahmed review WP-2 Design v1 + Smoke v2 (8 confirmed oracle
  tasks); build a version-aware Saleor environment bundle to lift the
  environment blocker; in parallel build/review the AG16 executable bundle. Then
  AG16 sensitivity and WP-2 Smoke can be authorized.

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
