# T12 M02-D2 — Input Contract Closure (materializer-ready scope, RD-8 classification provenance, exact F2P call plan)

Mission `T12_M02_D2_INPUT_CONTRACT_20261027` (Track 1.2). Offline engineering ONLY:
no Docker/WSL/reconstructed-tree pytest, no benchmark-API calls (USD 0.00), no
experiment execution, no outcomes read. See the mission deliverable package in
`D:\WP2\audit_results\T12_M02_D2_INPUT_CONTRACT_RESULT_<timestamp>\`.

## What this branch adds

| File | Purpose |
| --- | --- |
| `scripts/t12_m02_materializer_schema.py` | Single offline source of truth for the frozen `opws_phase3b_patch_materialize.py` input schema (scope paths, canonical hash, classification statuses, git name-status parser, census→authority mapping) — transcribed verbatim from the pinned materializer, stdlib-only. |
| `scripts/t12_m02_scope_normalizer.py` | ZERO-OUTCOME-READ per-task/per-arm extraction of the frozen multi-task prediction sources into real materializer-ready `{"scope": [...]}` JSON + audit receipts (allowlisted extraction; oracle fields recorded, never consumed). |
| `scripts/t12_m02_classification_provenance.py` | RD-8: deterministic derivation of `--classification-json` + `--test-authority-json` from the frozen parent→target reference diff (git name-status M/D/A, no-renames) cross-checked against the frozen census; artifacts labelled `PROPOSED_NEW_DERIVATION_PENDING_RESEARCHER_RD8_APPROVAL`. |
| `scripts/t12_m02_f2p_contract.py` | Exact prospective per-arm `harness_v3.run_state_v3` invocation plan (3 frozen F2P nodes × 3 reps = 9 JUnit/arm; fresh per-arm DB/out_dir/execution_id; m3b smoke single-node limitation documented). NO run mode. |
| `scripts/t12_m02_driver.py` / `scripts/t12_m02_arm_adapter.py` | Preflight + dry-run now consume the D2-normalized scope JSON, derived classification and test-authority; the red-flag selector-domain lumping is corrected; status `INPUT_CONTRACT_READY_FOR_RESEARCHER_REVIEW`, execution STOPs on `RD8_DERIVATION_PENDING_RESEARCHER_APPROVAL` + `EXECUTION_NOT_AUTHORIZED`. |

## Proof (2026-10-27, real frozen engine)

`python scripts/opws_phase3b_patch_materialize.py … --dry-run` (read-only hash/print
engine) run for all 13 arms with ONLY the D2-derived inputs reproduces the frozen plan's
per-arm `selected_scope_hash` AND `reference_patch_sha256` byte-for-byte (13/13 MATCH),
with `scientific_outcome=UNOBSERVED` — i.e. the derived inputs are provably equivalent to
the original frozen engineering pipeline. Split invariants
(`test_equals_census_authoritative`, `union_all_classification`, `union_all_git_changed`,
`changed_test_paths_equal_authority`) all PASS.

## Status

- ENGINEERING: **PASS / INPUT_CONTRACT_READY_FOR_RESEARCHER_REVIEW** (all three gaps closed).
- SCIENCE: **NOT_RUN** — all 13 arms `NOT_RUN`, USD 0.00, no experiment authorized.
- Gate: RD-8 researcher approval decides the derived classification artifact's admission;
  a separate execution authorization + exclusive resource window is required before any run.