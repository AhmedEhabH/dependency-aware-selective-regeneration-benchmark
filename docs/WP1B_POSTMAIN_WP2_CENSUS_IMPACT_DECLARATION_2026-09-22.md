# Impact Declaration — wp1b-postmain-wp2-census

> Tier **T2** · Scientific/API spend **$0.00** · ZERO API · Deterministic census
> over already-opened MAIN_297 scientific case metadata and frozen result
> artifacts only.

## Artifacts / features affected

- Current-facing documentation (README, `00_CURRENT_RESEARCH_STATE.md`,
  `PROGRESS.md`, `TODO.md`, `START_HERE_CURRENT_2026-09-21b.md`,
  `docs/LIVE_STATUS.json` + rendered LIVE block) — **static/current-state
  refresh only**.
- WP-1b claim boundaries (one-page claim sheet) — **narrative closure**, no new
  statistics.
- AG16 readiness handoff — **requirements/evidence bundle only**, no execution.
- WP-2 zero-API census over MAIN_297 — **new deterministic census artifacts**.

## Dependencies

- Frozen MAIN_297 result JSON (`reports/wp1b_main297_result.json`).
- Frozen variance 15x3 result JSON (`reports/wp1b_variance_15x3_result.json`).
- Frozen exploratory JSON (`reports/wp1b_main297_exploratory.json`).
- Frozen AG16 preregistration
  (`research/wp1b/wp1b_agent_budget_sensitivity_prereg.json`).
- MAIN_297 manifest (`research/wp1b/wp1b_main_297_manifest.json`).
- Already-opened Saleor MAIN_297 case metadata (local
  `dist/pilot-repo-cache/saleor` + `real_commit_impact_saleor/scientific`
  manifests). No new API, no new Saleor commits fetched.

## Exact files to be edited / created

**Edited (docs/current-facing only):** `README.md`, `PROGRESS.md`, `TODO.md`,
`00_CURRENT_RESEARCH_STATE.md`, `START_HERE_CURRENT_2026-09-21b.md`,
`docs/LIVE_STATUS.json`, `docs/DECISIONS.md` (append-only), `AGENTS.md`
(only if mandated), `research/wp1b/wp1b_decision_rules_v2.json` (only if a
frozen-facts display fix is needed — otherwise untouched).
**Created:** `docs/WP1B_POSTMAIN_WP2_CENSUS_IMPACT_DECLARATION_2026-09-22.md`
(☑ this file), `docs/WP1B_CLAIM_SHEET_2026-09-22.md`,
`docs/WP1B_POSTHOC_ROBUSTNESS_AND_LIMITATIONS_2026-09-22.md`,
`research/wp1b/wp1b_posthoc_robustness_input_manifest_2026-09-22.json`,
`docs/WP1B_AG16_READINESS_2026-09-22.md`,
`research/wp1b/wp1b_ag16_harness_requirements_2026-09-22.json`,
`exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/`,
`scripts/wp2_saleor_e2e_census.py`, `research/wp2/wp2_saleor_main297_census_2026-09-22.json/.csv`,
`research/wp2/wp2_saleor_environment_feasibility_2026-09-22.json`, `docs/WP2_SALEOR_ENVIRONMENT_FEASIBILITY_2026-09-22.md`,
`research/wp2/wp2_smoke_candidate_proposal_2026-09-22.json`,
`docs/WP2_MAIN297_ZERO_API_CENSUS_2026-09-22.md`,
`docs/WP1B_POSTMAIN_WP2_CENSUS_STOP_REPORT_2026-09-22.md`.
**Test edits:** tests added for new deterministic census/readiness logic +
new tests for any new utility scripts (e.g. render_live_status-driven
sync test, census tests).

## Edge cases

- Static README prose may disagree with the generated LIVE block → rely on the
  generated render after `render_live_status.py --write`; never hand-edit the
  block.
- List-price USD vs actually-billed USD must never be conflated — label every
  cost figure with view/accounting basis.
- Pooled micro-F1 vs macro-F1 must remain distinct — pooled is primary.
- NI at Δ=0.05 does NOT imply superiority or equivalence.
- Δ=0.03 sensitivity is inconclusive — must be stated.
- Variance 15x3 replicates are NOT full MAIN_50 replications.
- X3/X6 preregistered negative readings remain negative.
- F2P/P2P candidate ≠ validated F2P oracle; census never labels
  `F2P_CONFIRMED`.
- Changed test file is NOT proof a test fails at parent and passes at target.
- 786 sealed Saleor RESERVE outcomes stay sealed — never accessed.

## Decision block (append to DECISIONS.md)

| ID | Decision | Value |
|---|---|---|
| D1 | Post-MAIN_297 zero-API closure | **APPROVED** |
| D2 | README/current-doc refresh + FAQ + develop `What we have learned` | **APPROVED** |
| D3 | WP-1b claim sheet | **APPROVED** |
| D4 | New post-hoc statistics | **NOT AUTHORIZED** unless an externally supplied brain-reviewed script already exists; OpenCode must not invent the analysis |
| D5 | WP-2 MAIN_297 static/deterministic census | **APPROVED — ZERO API ONLY** |
| D6 | AG16 paid execution | **NOT IN THIS MISSION** — readiness/preparation only; runner/config must be brain-built and independently supplied/tested first |
| D6b | AG16 factorial extension `(16,2000)` / `(8,8000)` | **NO** |
| D6c | AG16 MAIN_150 extension | **NO** |
| D7 | Access to the 786 sealed Saleor RESERVE outcomes | **FORBIDDEN** |
| D8 | Polyglot / JabRef / NestJS / Grafana execution now | **NO** — future external-validity work after core E2E evidence |

Decided by **Ahmed Ehab**, 2026-09-22. Supervisor informed: **no**.
