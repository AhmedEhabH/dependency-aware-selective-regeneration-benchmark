# RESEARCH STATUS — 2026-10-02

**Role:** Research-status snapshot at the closure of the 2026-10-02 phase
(M16-v1 closed; documentation and evidence consolidation). This is a
point-in-time status, not a replacement for the live
`docs/LIVE_STATUS.json`-rendered block.

## Where the research stands

- **Primary scientific object:** repository-level affected-file / editable
  change-scope correctness.
- **Primary metric:** file-level impact correctness (file-level F1).
- **WP1 — primary evidence is complete:**
  - Sparse impact-plan representation solves the output-feasibility /
    truncation problem (djangoCMS 30-task study).
  - Saleor RESERVE-300: RM-CSS F1 .3569 vs SIP .2647, Δ +.0921, CI
    [.0691, .1156] — primary.
  - MAIN_297 selection-only: Agent .3631 / RM-CSS .3568 / SIP .2652; NI at the
    preregistered 0.05 margin supported; RM-CSS ≈0.2746× calls and ≈0.2134×
    generation tokens vs Agent — primary.
- **WP2 — supporting evidence is closed/consolidated:**
  - Smoke v2.2 (supporting; engineering pipeline works).
  - Pilot-A, M14R (supporting negatives; generator floor not removed).
  - M15-R OPWS Pilot-B (supporting descriptive; n=10).
  - M16-v1 (CLOSED pre-experiment adapter failure; **no** MAIN OPWS outcome).

## M16-v1 status (this phase's headline)

M16-v1 attempted to qualify the OPWS-MAIN instrument but stopped before any
experiment at R02_ADAPTER_VERIFY (`M16_ADAPTER_FAIL`, resumable=False) with 4
fail-closed violations (3 ENG install-mode mismatches; 1 MAIN task with a
declared dev group but closure mechanism `none`). R00 (102 tests) and R01
(guard) passed; R03/R04/R05 and MAIN never ran; no result-driven redesign
exists. Full record: [`docs/M16_V1_CLOSURE_2026-10-02.md`](M16_V1_CLOSURE_2026-10-02.md).

## Open / not started

- AG16 budget sensitivity (preregistered; runner not built).
- WP2 E2E generation-based selector comparison (blocked by generator floor;
  M15-R S2 gate failed; S3 correctly skipped).
- WP3 cross-language/polyglot study (optional; only after a feasibility gate
  and a brain decision that it materially strengthens the thesis without
  delaying it).

## Source of truth

Numbers and allowed interpretation are bound by
[`EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md),
[`RESULTS_SUMMARY.md`](RESULTS_SUMMARY.md) and
[`CLAIM_REGISTRY.md`](CLAIM_REGISTRY.md); claim wording is frozen there.