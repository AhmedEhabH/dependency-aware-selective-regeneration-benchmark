# Phase 2B — Protocol Freeze Report

**Date:** 2026-07-22
**Protocol Version:** 1.0
**Status:** FROZEN
**Approved for Phase 3:** true

## Summary

Research Protocol v1.0 is frozen from researcher-approved decisions. The Phase 2A draft (`reports/PHASE2_PROTOCOL_DRAFT.md`) is superseded. All 14 DA decisions and 11 AC mandatory corrections from `docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md` have been applied. Nine contradictions between the draft and the approved decisions were identified and corrected. Phase 3 is authorized but has not started.

## Tasks Completed

| ID | Description | Status |
|----|-------------|--------|
| T301 | Apply Researcher Decisions DA-01 through DA-14 | FROZEN |
| T302 | Apply Mandatory Corrections AC-01 through AC-11 | FROZEN |
| T303 | Create Frozen Protocol Documents | FROZEN |
| T304 | Update State Files for Phase 2B | FROZEN |
| T305 | Validation of Frozen Protocol | FROZEN |

## 9 Contradictions Corrected

| # | Draft Wording | Corrected To | Trigger |
|---|--------------|-------------|---------|
| 1 | §9.3: "regression pass rate: regressed_tests / total_regression_tests (inverted)" | Regression pass rate = passed / total; failure rate = newly failing / total | AC-02 |
| 2 | §15.2: "Maximum repair iterations: 3 per scenario" | Maximum two LLM repair attempts | AC-05 |
| 3 | §15.4: "marked as excluded from that repository's aggregate" | Failures remain in aggregates; conditional metrics labelled | AC-04 |
| 4 | §16.2: "cross-validation across scenarios" alternative for hidden split | Cross-validation is not a substitute; hidden tests mandatory | AC-03 |
| 5 | §13.4: "temperature=0" produces identical outputs | Best-effort reproducibility; GPU does not guarantee identical outputs | AC-07 |
| 6 | §9.5: "Estimated monetary cost: USD" | Report tokens, GPU time, wall time; do not invent monetary cost | AC-08 |
| 7 | §20.5: "monotonically decreases" | Perfect monotonicity not required; evaluate trend + CI | AC-10 |
| 8 | §3.5: "repos older than N months" | Tagged stable release ≥ 90 days old | DA-03 |
| 9 | §14.4: "~8.6M tokens estimated" as budget | Three-stage approach (smoke, pilot, main); not a hard budget | DA-09 |

## Frozen Documents Created

| Document | SHA-256 Checksum |
|----------|-----------------|
| `docs/FINAL_RESEARCH_PROTOCOL.md` | `9D4A140C1CBA19C3076AF8C71AD859F243C31836FECD6026C2CD86CFC271B148` |
| `docs/GROUND_TRUTH_PROTOCOL.md` | `83F1ADB28CD99B6859BD7BE8189B22C2D272538CBB19B386D921F9DC728DD9E5` |
| `docs/SCENARIO_TAXONOMY.md` | `5FA4D7114E1993E2D8FB570EC9BAC4129F3956B09E7555C200C118E206D9BB62` |
| `docs/STATISTICAL_ANALYSIS_PLAN.md` | `FA8B76C41FF05462E80675B297917A904ECD4605CA5AD54C84740A38B6AB1D4C` |
| `docs/EXECUTION_AND_FAILURE_POLICY.md` | `FB3072880A6EBDD259707F9F64F50D56DF6DD4B04DBDE80E1E2867C80295F49E` |
| `docs/LEAKAGE_PREVENTION_PROTOCOL.md` | `F78AF1F57C8A59EA324E1996B4B172F7A02EF9D0D8EB66DD1D02F9EFD2B53910` |
| `docs/REPRODUCIBILITY_PROTOCOL.md` | `A59A666CC740BF2F9F9D9D193422892C1E064D99F6D264250C5625CFB35DB02E` |
| `docs/RESEARCHER_DECISIONS_DA_AC.md` | `1884352AF8813E794A25A1BAE947269BB343C788A22A933F59754B7DEE607BD3` |

## Validation Checks

| Check | Result |
|-------|--------|
| No unresolved REQUIRES_RESEARCHER_APPROVAL items remain | PASSED |
| Regression pass-rate formula corrected (AC-02) | PASSED |
| Hidden tests separated from held-out scenarios (AC-03) | PASSED |
| Failed strategies remain in analysis (AC-04) | PASSED |
| Repair budgets uniform, max 2 (AC-05) | PASSED |
| Candidate artifact universes frozen before execution (AC-01) | PASSED |
| Kaggle monetary cost not fabricated (AC-08) | PASSED |
| Protocol amendment rules explicit (AC-11) | PASSED |
| Authoritative proposal unchanged (inputs/paper/) | PASSED |
| SHA-256 checksums generated and recorded | PASSED |

## Files Created
- `docs/FINAL_RESEARCH_PROTOCOL.md`
- `docs/GROUND_TRUTH_PROTOCOL.md`
- `docs/SCENARIO_TAXONOMY.md`
- `docs/STATISTICAL_ANALYSIS_PLAN.md`
- `docs/EXECUTION_AND_FAILURE_POLICY.md`
- `docs/LEAKAGE_PREVENTION_PROTOCOL.md`
- `docs/REPRODUCIBILITY_PROTOCOL.md`
- `docs/RESEARCHER_DECISIONS_DA_AC.md`
- `reports/PHASE2B_PROTOCOL_FREEZE_REPORT.md`

## Files Modified
- `PROTOCOL_VERSION.md` (v1.0 FROZEN)
- `DECISION_LOG.md` (D007)
- `SYSTEM_STATE.md` (Phase 2B)
- `TODO.md` (T301–T305)
- `reports/latest_phase_report.md`

## Exact Next Task
**Phase 3 — Repository and Scenario Preparation**: Prepare Controlled Django Todo; assess django CMS; assess Saleor Core; prepare manifests; prepare scenario definitions; prepare acquisition or snapshot strategy; document licences. Do not run real repository evolution using an LLM.
