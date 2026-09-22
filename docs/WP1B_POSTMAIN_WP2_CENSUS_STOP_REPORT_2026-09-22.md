# WP-1b Post-MAIN_297 WP-2 Census — STOP REPORT (2026-09-22)

## 1. Executive decision

`DECISION: POSTMAIN_ZERO_API_COMPLETE_AG16_NEEDS_BRAIN_BUNDLE`

## 2. Git / repository state

- Branch: `wp1b/postmain-wp2-census-2026-09-22`
- HEAD: `main` base = `cf84fd061ac534b0c4200650e5f3d01c4857ae28` (== origin/main
  at mission start); working branch carries the mission commits.
- origin/main: `cf84fd0` (unchanged by this mission until the merge in P10).
- Tree: clean at STOP (after P10 commit; exports are untracked workflow
  artifacts in the parent directory).
- MAIN_297 tags verified locally + on origin and are ancestors of `main`:
  `wp1b-main297-harness-prereg-2026-09-22`,
  `wp1b-main297-predictions-frozen-2026-09-22`,
  `wp1b-variance-predictions-frozen-2026-09-22`,
  `wp1b-main297-result-2026-09-22`. None was moved or recreated.

## 3. What changed

| File | Change | Why |
|---|---|---|
| `docs/WP1B_POSTMAIN_WP2_CENSUS_IMPACT_DECLARATION_2026-09-22.md` | NEW | P1 mandatory impact declaration, committed before substantive edits |
| `DECISIONS.md` | APPENDED | D1–D8 decision block (2026-09-22) |
| `README.md` | EDITED | static drift removed; MAIN_297 COMPLETE; lessons 1f–1j; FAQ expanded; section 5/6 updated |
| `docs/WP1B_CLAIM_SHEET_2026-09-22.md` | NEW | P3 one-page claim sheet |
| `docs/WP1B_POSTHOC_ROBUSTNESS_AND_LIMITATIONS_2026-09-22.md` | NEW | P4 labelled robustness/limitations |
| `research/wp1b/wp1b_posthoc_robustness_input_manifest_2026-09-22.json` | NEW | P4 machine-readable input manifest (SHA-256, labels, `analysis_code_supplied=false`) |
| `docs/WP1B_AG16_READINESS_2026-09-22.md` | NEW | P5 AG16 readiness audit |
| `research/wp1b/wp1b_ag16_harness_requirements_2026-09-22.json` | NEW | P5 harness requirements |
| `exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/` | NEW | P5 brain handoff (23 files; README_BRAIN.md, MANIFEST.json, SHA256SUMS.txt verified) |
| `scripts/wp2_saleor_e2e_census.py` | NEW | P6 deterministic census script |
| `research/wp2/wp2_saleor_main297_census_2026-09-22.json/.csv` | NEW | P6 census outputs (297 tasks) |
| `research/wp2/wp2_saleor_environment_feasibility_2026-09-22.json` | NEW | P6.2 environment feasibility |
| `docs/WP2_SALEOR_ENVIRONMENT_FEASIBILITY_2026-09-22.md` | NEW | P6.2 environment feasibility doc |
| `scripts/wp2_smoke_candidate_proposal.py` | NEW | P6.3 deterministic proposal generator |
| `research/wp2/wp2_smoke_candidate_proposal_2026-09-22.json` | NEW | P6.3 proposal (8 candidates, proposal-only) |
| `docs/WP2_MAIN297_ZERO_API_CENSUS_2026-09-22.md` | NEW | P6.4 census summary |
| `tests/unit/test_wp2_saleor_census.py` | NEW | P8 census tests (8 tests) |
| `docs/LIVE_STATUS.json` | EDITED | P9 current-state update (all keys preserved) |
| `PROGRESS.md`, `TODO.md`, `START_HERE_CURRENT_2026-09-21b.md`, `00_CURRENT_RESEARCH_STATE.md` | EDITED | P9 current-state sections + rendered LIVE blocks |

## 4. WP-1b documentation closure

Stale static README content was corrected: WP-1b is no longer "LIVE" and
MAIN_297 is no longer "not scored yet". README now states plainly that
localization method selection is CLOSED, MAIN_297 is COMPLETE, the primary
result is `RMCSS_NONINFERIOR_AT_LOWER_COST`, RM-CSS satisfies the preregistered
NI criterion at Δ=0.05 (Agent point estimate slightly higher), this is a
selection-stage result NOT E2E, and WP-2 / F2P / P2P / Smoke / Pilot / Research
Run have NOT started.

## 5. Claim sheet

`docs/WP1B_CLAIM_SHEET_2026-09-22.md` — contains exact frozen numbers,
6 allowed sentences, 13 forbidden sentences (including "RM-CSS beats the
Agent", "equivalence", "MAIN_297 proves E2E", "4.5× cheaper" without
list-price qualifier), 9 required caveats, and a supervisor-safe 30-second
explanation. No new statistics.

## 6. Robustness / limitations

`docs/WP1B_POSTHOC_ROBUSTNESS_AND_LIMITATIONS_2026-09-22.md` classifies every
item: PRIMARY PREREGISTERED (P/S NI), SECONDARY PREREGISTERED (Δ=0.03/0.10
sensitivity), EXPLORATORY PREREGISTERED (macro-F1, X3/X6/X10/X11),
POST-HOC DESCRIPTIVE (variance 15×3, billed vs list cost),
`PENDING_BRAIN_SCRIPT — not recomputed by OpenCode in this mission` (run-noise
Q5 robustness: no brain-reviewed script supplied; exact frozen inputs listed).

## 7. AG16 readiness

- Current runner status: **NOT runnable.** `iterative_agent.py` hard-codes
  `MAX_AGENT_CALLS=8` and `OBSERVATION_WINDOW_CHARS=2000`;
  `src/benchmark/wp1b/main_runner.py` freezes protocol v3 knobs. No
  `iterative_agent_budget.py` exists; no AG16 runner/scorer/tests exist.
- Missing implementation pieces: parameterized agent module, golden parity test
  `(8,2000)`, AG16 dry-run, AG16 calibration gating (ceil $0.80, not scored),
  parameterized paid runner (MAIN_50, ceil $12.20), AG16 scoring (sensitivity
  only).
- Handoff package: `exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/` (23 files,
  MANIFEST.json + SHA256SUMS.txt verified).
- Zero paid calls this mission. Frozen `iterative_agent.py` /
  `repository_tools.py` are byte-unchanged.

## 8. WP-2 census

- n = **297** (exactly the MAIN_297 manifest IDs; 0 errors; 0 materialization
  problems).
- STRONG F2P candidates (target adds ≥1 test file): **20**.
- MODIFIED-test candidates: **200**.
- No changed-test evidence: **77**.
- Migration/config complexity: 78 migration files + 21 config/infra files across
  **40** tasks.
- Environment availability: Postgres 17 AVAILABLE (running), Redis AVAILABLE
  (running), pytest/offline posture AVAILABLE (`--disable-socket`), Saleor HEAD
  Python `>=3.12,<3.13` vs local 3.11.5 → UNKNOWN until a compatible venv is
  provisioned; no-network local test structurally feasible but NOT measured.

## 9. Smoke candidate proposal

8 proposal-only candidates selected deterministically (Group A favored,
changed-file-count diversity, never outcome-based, SHA-256 salt tie-break):
`saleor-rc-b8786c1bf4d3`, `saleor-rc-11756ee6b65a`, `saleor-rc-14f2176b5d8c`,
`saleor-rc-bd0c56fc787e`, `saleor-rc-10889526d151`, `saleor-rc-cae629dc4166`
(STRONG), `saleor-rc-a9e79dac40a2` (Group B), `saleor-rc-b84bf6595f49`
(Group C). `SMOKE_CANDIDATE_PROPOSAL_ONLY`; final sample requires brain/Ahmed
review.

## 10. E2E status

- WP-2 execution: **NOT started** (census is planning evidence only).
- F2P/P2P oracle: **NOT built**.
- Smoke / Pilot / Research Run: **NOT run**.

## 11. External validity

Future ordering only: JabRef/Java or NestJS/TypeScript first cross-language
replication → a second if useful → Grafana true-polyglot (Go + TypeScript)
after core E2E evidence. No repositories were cloned in this mission.

## 12. Validation

- `git diff --check`: PASS.
- Ruff: PASS on new scripts (`scripts/wp2_saleor_e2e_census.py`,
  `scripts/wp2_smoke_candidate_proposal.py`, `tests/unit/test_wp2_saleor_census.py`).
- `python -m py_compile`: PASS.
- Mypy: NOT REQUIRED (new scripts are standalone `scripts/*`, excluded by
  pyproject override; no typed production package changed).
- Pytest targeted (26 passed): census (8), live-status blocks (3), README
  markdown tables (7), model identity policy (5), thesis doc hygiene (3).
- Census self-checks: exactly 297 unique IDs; no calibration IDs; no task
  outside MAIN_297; no sealed-outcome path accessed; every output maps to a
  MAIN_297 ID; counts reconcile.
- Full suite: NOT run (T2; no shared production Agent/scorer change; mission
  allows targeted only).
- No unintended tracked evidence-file mutations introduced by tests.

## 13. Spend

**$0.00** scientific/API inference this mission. Zero paid/API/model calls.

## 14. Scientific unknowns

- AG16 (budget sensitivity) outcome: unknown until the brain builds/tests the
  harness and Ahmed authorizes D6.
- Δ=0.03 sensitivity: remains INCONCLUSIVE.
- Run-noise / Q5 robustness analysis: not computed (no brain-reviewed script
  supplied); exact frozen inputs listed in P4 artifact.
- F2P/P2P true behaviour: unknown; census candidacy is structural only.
- Real E2E runtime (setup, per-test wall time, migration cost): unmeasured.
- Whether changed tests actually fail at parent / pass at target: unverified.

## 15. Falsifiers / interpretation limits

- A future finding that the agent's tools were still disabled would weaken the
  agent baseline claim; the instrument was validated only at Calibration-3c
  gate v3 and MAIN-mode Review Card M1–M5.
- Billed vs list USD divergence is provider-caching-dependent and descriptive.
- Variance 15×3 is execution variability on 15 tasks, not three full MAIN_50
  replications; the replicate F1 values are not a trend.
- NI at Δ=0.05 does not imply superiority or equivalence; macro-F1 favors the
  Agent and is not hidden.

## 16. Exact next action

Brain builds/reviews the AG16 executable bundle from the frozen readiness
requirements; then Ahmed may authorize AG16 calibration + MAIN_50 sensitivity.
In parallel, the WP-2 census is ready for the brain to design the shared E2E
executor and F2P/P2P oracle.