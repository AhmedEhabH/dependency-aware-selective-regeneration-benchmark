# Impact Declaration — WP-1a Integration Closure → WP-1b Execution Readiness

**Date:** 2026-09-21
**Branch:** `feat/wp1a-selection-baseline-preparation`
**Tier:** T3 (scientific protocol closure, audit hardening, and WP-1b preregistration)
**Scientific API spend:** $0.00. Paid WP-1b inference is STRICTLY FORBIDDEN in this mission.
**Status:** Declared BEFORE any substantive edit, per mission contract section 5 / A3.

This declaration records the exact intended scope of the WP-1a integration
closure and WP-1b readiness mission. It is committed before any substantive
code/protocol edit.

---

## 1. Purpose

Independently inspect and recompute the WP-1a evidence (NOT trusting the prior
WP-1a STOP report), resolve the four scientific blockers (G1 NI margin, G2
completion cap, G3 forced-final semantics, G4 audit terminology), prepare the
two forward prerequisites (G5 variance substudy, G6 pricing preflight), freeze
the Calibration-3 gate, close the WP-1a integration, and produce the required
STOP/export deliverables. The mission decides ONE question: is the repository
ready to ask Ahmed for WP-1b spend authorization?

## 2. Affected artifacts / features

- WP-1a frozen artifacts under `research/wp1a/` are inputs; they are NOT
  rewritten. Amendments to their wording are transparent (append/version),
  never silent replacement.
- Repository-agent strategy (`src/benchmark/strategies/iterative_agent.py`)
  gains additive truncation/EMPTY-classification telemetry and an explicit
  loop-termination state description. NO change to selection behavior.
- WP-1b readiness artifacts (new): NI-margin decision-required doc, completion-
  cap provenance + proposed amendment, loop-termination semantics, knob
  registry, pricing preflight, calibration gate, variance-substudy
  preregistration, integration closure doc, STOP report, machine-readable
  closure JSON, independent-audit packet, export package.
- Governance: `PROGRESS.md`, `DECISIONS.md` (append-only).

## 3. Affected dependencies

- Read-only frozen Saleor-300 inputs: `research/saleor-reserve-300-rmcss/*`
  (sample, run records, candidate rows, proxies, deployment artifact).
- `research/wp1a/*` frozen artifacts (read-only except transparent wording
  amendments for audit terminology).
- `src/benchmark/wp1a/*`, `scripts/wp1a_*.py`, `tests/unit/test_wp1a_*.py`.
- No dependency on the 786 unread Saleor RESERVE outcomes. They remain closed.

## 4. Exact files expected to be modified / created

New files (this mission):

- `docs/WP1A_WP1B_SCIENTIFIC_CLOSURE_IMPACT_DECLARATION_2026-09-21.md` (this file)
- `docs/WP1B_KNOB_REGISTRY_2026-09-21.md` — scientific vs operational knob registry
- `docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md` — G1 decision-required artifact
- `docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md` — G2 provenance timeline
- `docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md` — G2 proposed prospective amendment
- `docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md` — G3 state machine
- `docs/WP1B_VARIANCE_SUBSTUDY_PREREGISTRATION_2026-09-21.md` — G5
- `docs/WP1B_PROVIDER_PRICING_PREFLIGHT_2026-09-21.md` — G6
- `docs/WP1B_CALIBRATION_3_GATE_2026-09-21.md` — Calibration-3 gate
- `docs/WP1A_INTEGRATION_CLOSURE_2026-09-21.md` — integration closure table
- `docs/WP1A_WP1B_SCIENTIFIC_CLOSURE_STOP_REPORT_2026-09-21.md` — final STOP report
- `artifacts/wp1b_provider_pricing_preflight_2026-09-21.json` — G6 machine-readable
- `artifacts/wp1b_calibration_gate.json` — Calibration-3 gate machine-readable
- `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json` — G5 manifest
- `artifacts/wp1a_wp1b_scientific_closure_2026-09-21.json` — mission machine-readable output
- `artifacts/wp1a_wp1b_closure_recomputation.json` — PHASE 2 recomputed evidence
- `artifacts/wp1b_completion_cap_truncation_evidence.json` — G2 truncation recomputation
- `scripts/wp1b_closure_recompute.py` — independent recomputation script
- `scripts/wp1b_variance_substudy_selection.py` — deterministic 15-task subset
- `src/benchmark/wp1b/__init__.py`, `src/benchmark/wp1b/telemetry.py` — truncation/EMPTY metric schema
- `tests/unit/test_wp1b_loop_termination.py` — G3 state-machine + telemetry tests
- `tests/unit/test_wp1b_truncation_telemetry.py` — G3/G2 telemetry tests
- `tests/unit/test_wp1b_closure_recompute.py` — PHASE 2 recomputation tests
- `tests/unit/test_wp1b_variance_substudy.py` — G5 subset determinism tests
- `exports/wp1a_independent_audit_packet_2026-09-21/` — blind audit handoff
  (README_AUDITOR.md, acceptance_criteria.json, artifact_manifest.json,
  sha256sums.txt, recompute_instructions.md)
- `exports/WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21/` — closure evidence package
  (MANIFEST.json, SHA256SUMS.txt, git provenance)

Modified files (transparent, minimal):

- `src/benchmark/strategies/iterative_agent.py` — additive truncation /
  EMPTY-classification telemetry (no behavior change)
- `research/wp1a/wp1a_independent_audit.json` — relabel "independent audit" to
  "same-session cross-check" (G4 terminology correction)
- `research/wp1a/wp1a_acceptance_report.json` — relabel AC-1A.10 wording
- `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` — terminology
  note if required
- `PROGRESS.md` — durable status
- `DECISIONS.md` — append-only decision entries

## 5. Documentation / governance files

- All docs listed in section 4.
- `PROGRESS.md` and `DECISIONS.md` updated per protocol v2.
- `00_CURRENT_RESEARCH_STATE.md` — NOT modified (no new scientific result; the
  frozen WP-1a/Saleor-300 evidence is unchanged).

## 6. Tests / scripts to add

- `scripts/wp1b_closure_recompute.py` + `tests/unit/test_wp1b_closure_recompute.py`
- `scripts/wp1b_variance_substudy_selection.py` + `tests/unit/test_wp1b_variance_substudy.py`
- G3 tests: forced-final succeeds / truncates / malformed / no-final-before-cap /
  valid-final-before-cap / EMPTY classification / finish-reason telemetry
  (`tests/unit/test_wp1b_loop_termination.py`)
- Truncation/cap telemetry schema tests
  (`tests/unit/test_wp1b_truncation_telemetry.py`)
- Existing affected tests re-run: `tests/unit/test_wp1a_*`, iterative-agent
  integration tests (`tests/integration/test_su0011_iterative_agent.py`).

## 7. Expected edge cases

- G1: no frozen WP-1b F1 NI margin exists in the WP-1a authoritative artifacts;
  the Statistical Analysis Plan's Δ=0.05 applies to regression pass rate (H2),
  and `EXPERIMENTAL_DESIGN_V2.md` defines an F1 NI margin (Δ=0.05, sensitivity
  0.03/0.10) for `hybrid_selective` vs `repository_agent` — its authority for
  the WP-1b selection-only RM-CSS comparison is documented, not assumed.
  RESULT: G1 requires an explicit prospective margin decision; paid WP-1b is
  blocked until frozen.
- G2: 512 (current default, pilot-derived) vs 1024 (v1.1 scientific run value)
  both have provenance; no WP-1b-specific prospective scientific justification
  exists for 512. RESULT: a proposed prospective amendment is prepared; final
  selection requires authorization; paid WP-1b is blocked until resolved.
- G3: malformed JSON on the forced-final call currently collapses into the
  generic "no paths selected after exploration" EMPTY error — classification
  telemetry is added without changing selection behavior.
- SIP 2/300 transport-failed records are EMPTY (fail-closed) in re-derivation.
- `candidate_rows_saleor300.parquet` label column is all-zero placeholder;
  the tested leakage vector is non-informative (no claim of past informative
  leakage).
- Pricing preflight must not invoke paid inference; if live provider metadata
  is unavailable at execution time, record the frozen verified pricing with an
  explicit timestamp limitation instead of inventing values.

## 8. Tier / risk

**Tier T3.** Failure to resolve G1/G2 blocks WP-1b authorization. This mission
adds no paid inference and makes no scientific claim about method quality.

## 9. Explicitly out of scope (unless separately authorized)

- Changing model family or provider for convenience.
- Changing temperature / prompts / sample membership / scorer / threshold.
- Selecting a NI margin after observing WP-1b; tuning against main-50.
- Running paid WP-1b inference.
- Opening the 786 unread Saleor RESERVE outcomes.
- Rewriting thesis claims unrelated to this closure.
- Refactoring production code beyond the additive telemetry above.

## 10. Reversibility

- Every new file is additive; revert by deleting it.
- `iterative_agent.py` telemetry is additive (new counters/properties); revert
  by reverting the single commit that touches it. No behavioral path changes.
- Wording amendments to the two WP-1a JSON artifacts are value-only relabels
  (old values retained in DECISIONS.md); revert by restoring the old values.
- `PROGRESS.md`/`DECISIONS.md` changes are standard append/replace reversions.
- Merge to `main` is a normal `--no-ff` merge; revert via `git revert <merge>`.