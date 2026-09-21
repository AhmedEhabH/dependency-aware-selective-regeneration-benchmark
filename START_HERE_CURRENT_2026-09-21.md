# START HERE - Current Research (2026-09-21)

This file is the entry map. Read it first, then open the referenced documents.
**Terminology:** SIP = Sparse Impact Plan (baseline); RM-CSS =
Repository-Memory Calibrated Set Selection (= SIP + Qwen dense ranking +
parent-only Repository Memory + calibrated ADD/KEEP/DROP). See
`docs/GLOSSARY.md`.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection` - **method
selection CLOSED** (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`).

## Current position (one paragraph)

WP-1a selection-baseline preparation is complete and merged. The two remaining
WP-1b scientific blockers (G1: F1 non-inferiority margin; G2: agent-control
completion cap) are now resolved prospectively by the **WP-1b preflight
freeze** (2026-09-21): G1 = Δ0.05 (Q5 one-sided rule), G2 = 1024 (amendment
EFFECTIVE). Budget model v2, the sample-size amendment (MAIN_297), decision
rules v2, and agent telemetry are all frozen pre-result. **Calibration-3 (3
tasks, cap 1024, ceiling $0.25) is authorized (D6 YES).** The Main run and the
variance substudy are **NOT** authorized (D7 NO) until Ahmed reviews the
Calibration-3 STOP report.

## Key facts

- **Frozen margin (G1):** `research/wp1b/wp1b_ni_margin_frozen.json`,
  `docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md`.
- **Completion cap 1024 (G2):** `research/wp1b/wp1b_frozen_agent_protocol_v2.json`;
  amendment EFFECTIVE in `DECISIONS.md`.
- **Budget v2:** `research/wp1b/wp1b_budget_model_v2.json` (no ceiling below
  worst case ×1.5; underestimate factor ~3.40×).
- **Sample-size amendment:** `research/wp1b/wp1b_main_297_manifest.json` (n=297),
  `wp1b_main_150_manifest.json` (n=149), `wp1b_main_50_manifest.json`; power doc
  `docs/WP1B_POWER_AND_SAMPLE_SIZE_2026-09-21.md`.
- **Decision rules v2:** `research/wp1b/wp1b_decision_rules_v2.json`.
- **Agent telemetry:** `src/benchmark/wp1b/telemetry.py`,
  `docs/WP1B_AGENT_BASELINE_DISCLOSURE_2026-09-21.md`.
- **Exploratory prereg:** `research/wp1b/wp1b_exploratory_prereg.json` (X1–X5).
- **Appendix R re-derivation:** 125 comparisons, 0 disagreements, ALL_AGREE
  (`research/wp1b/wp1b_appendix_r_agreement.json`).
- **Calibration gate (frozen):** `artifacts/wp1b_calibration_gate.json`
  (CG-1..CG-9), evaluator `scripts/wp1b_calibration_gate.py`.
- **Calibration-3 manifest:** `research/wp1a/wp1_calibration_3_manifest.json`.

## Authorized / not authorized

- **AUTHORIZED now (D6 YES):** Calibration-3 (3 tasks, protocol v2 cap 1024,
  provider/pricing frozen, USD guard ≤ $0.25).
- **NOT authorized (D7 NO):** MAIN_297, MAIN_50, MAIN_150, the variance
  substudy, and any other paid main experiment. MAIN_297 requires a new
  explicit Ahmed authorization after he reviews the Calibration-3 STOP report.
- **Never:** read/open/score/sample the 786 unread Saleor RESERVE outcomes.

## Where to go next

1. `docs/WP1B_PREFLIGHT_FREEZE_STOP_REPORT_2026-09-21.md` (mission STOP report).
2. `DECISIONS.md` (G1/G2, budget, sample-size, decision rules, telemetry,
   Appendix R).
3. `PROGRESS.md` (execution source of truth).
