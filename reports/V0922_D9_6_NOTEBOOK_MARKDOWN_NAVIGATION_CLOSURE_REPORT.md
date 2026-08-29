# V0922_D9_6_NOTEBOOK_MARKDOWN_NAVIGATION_CLOSURE_REPORT

**Task:** PILOT-EXEC-01 — v0.9.22 D9.6 Notebook-Markdown Cell-Labels Closure (notebook-navigation refinement on top of the D9.6 Kaggle/GitHub boundary correction)

**Date:** 2026-08-29

**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`

**Status:** LOCAL CLOSURE COMPLETE — REAL 2x T4 PROOF PENDING, NO STABLE TAG.

## 1. Objective

Add 11 exact Markdown navigation cells (`pilot-step-00..10-*md`) plus a visible pre-launch STOP boundary to
`notebooks/pilot_exec_01.ipynb` between the 16 (byte-identical, unchanged) executable code cells, so Kaggle's Table of
Contents names every operational stage and a STOP boundary guards `pilot-launch`. Deliver with strong regression tests,
re-freeze, verify, and document — WITHOUT touching any code-cell source, production code, frozen config, command flags,
or the accepted Kaggle/GitHub boundary; without creating the stable tag or launching the Pilot.

## 2. What changed

- **11 Markdown navigation cells inserted** between the 16 executable code cells in
  `notebooks/pilot_exec_01.ipynb`: `pilot-step-00-*md` … `pilot-step-10-*md` (e.g. Step 04 model-preflight, Step 08 STOP
  boundary, Step 09 launch, Step 10 resume). The Step 05 (4-stage) checklist and the Step 08 explicit STOP boundary are
  asserted exactly by the tests.
- **Nothing scientific, nothing in production/runtime code, NOT the Kaggle/GitHub boundary** changed. The 16 code cells
  are byte-identical (notebook diff = **126 insertions / 0 deletions**); all 16 code cells compile; `nbformat` minor 5.
- **New regression tests (RED on the D9.6 baseline, then GREEN):**
  - `tests/integration/test_pilot_notebook_contract.py` — `TestNotebookStructure` (full 29-cell order + code-only
    order), `TestMarkdownNavigation` (IDs/order/placement, exact headings + order, Step 05 4-stage checklist, Step 08
    STOP boundary, `HF_TOKEN`/no-`GITHUB_TOKEN`, launch/resume local-only, no forbidden fragments),
    `TestCodeCellsUnchangedFromBaseline` (git-show-blob baseline at `d0f8269…`, encoding-correct), and
    `TestBundledNotebookParity`.
  - `tests/integration/test_pilot_deployment_bundle.py` — `TestPilotBundleKeepsMarkdownNavigation` (frozen bundle
    retains 11 md cells with exact headings/order, no duplicates, code-order preserved, setup-cell frozen tag).
- Focused notebook-contract / D9.6-boundary / bundle / release-provenance suites all GREEN; full acceptance unchanged
  **2538 passed / 33 skipped / 0 failed**. `git diff --check`/ruff/compile clean.

## 3. Freeze (two-pass finalizer, `--verify-source-provenance`)

- Commit (markdown + tests): `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`
  (`feat(pilot): add Step 00-10 Markdown navigation cells to the pilot notebook`) = **source_commit / future tag
  target**, build id `478261f`.
- The notebook's frozen anchors were already correct (the stable code/data/repository-snapshot/transport manifest
  hashes do not depend on the notebook markdown, so they are UNCHANGED from D9.6); the finalizer discovery+validation
  and the provenance-enabled rebuild both confirm the artifact at `478261f…`.
- Finalizer at `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` with `--verify-source-provenance`: **FROZEN, 0 provenance
  mismatches**, idempotent (same-input rerun: archive SHA unchanged, stable manifest hashes unchanged).
- Exact artifact: `dist/pilot-kaggle-upload.zip` SHA-256
  `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`; sidecar matches; freeze evidence
  `reports/pilot_notebook_trust_freeze.json`.
- Stable manifest hashes (unchanged from D9.6): code `37e79950…`, data `8b859ecc…`, repository snapshot `49d91d39…`,
  transport path map `07036a36…`. `notebook_manifest_sha256` is NEW `9d3edac4c20c00ab73a1ecda10d52322a5c57756820ed03f3a6162615e19adb6`;
  deployed bundle notebook SHA `6720293b922e06a80ecdc44a6d16e5eb12cc777d23c24a7076d005872d7aba68` == the canonical
  source blob at `478261f…` (canonical ↔ bundled byte-equal).

## 4. Exact fresh-extraction bundled dry-run

Fresh extraction of the frozen artifact + transport restore, then the bundled CLI dry-run with explicit
`--source-commit 478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (48 expected cells, mock backend, `--deployed-build-id 478261f`):

```
Terminal: 48/48
Succeeded: 48
Failed: 0
Pending: 0
```

Canonical `validate_pilot_dryrun_evidence` PASS: 48 records, 48 unique run IDs, repos 16/16/16, strategies 24/24,
reps 24/24, 0 model calls, 0 prompt/completion / total workflow tokens; every record + `source_identity.json` ==
`478261f…` and its build id `478261f`.

## 5. Current-truth documentation + decision log

- AGENTS.md, README.md, SYSTEM_STATE.md, TODO.md, docs/PILOT_KAGGLE_RUNBOOK.md, docs/START_HERE.md,
  docs/MASTER_IMPLEMENTATION_PLAN.md, docs/PROJECT_HANDOFF.md, docs/AI_ACCOUNT_TRANSFER_HANDOFF.md,
  reports/latest_phase_report.md — current-truth block rewritten to the D9.6 notebook-markdown cell-labels closure with
  the new source commit `478261f…`/artifact `edae1b7e…`; the D9.6 boundary-correction truth demoted to PRIOR TRUTH;
  required boundary markers preserved (never contact GitHub, owner-controlled, locally verified against, after real
  preflight, `v0.9.22-pilot-exec-ready`); forbidden fragments not reintroduced.
- DECISION_LOG.md — Decision D032 added.

## 6. Required truthful status

- The prior D9.6 artifact `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4` (source
  `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`) is **SUPERSEDED** by this notebook-nav artifact; do not upload the old
  artifact.
- D8 (`02d16ca2…`) is REJECTED for Pilot launch and remains superseded; `exp-20260828-151335` has 0 accepted RunRecords
  and must never be resumed.
- No stable tag during this local closure: the next external step is ONE exact-new-artifact real 2x T4 GQA microprobe +
  generation-deadline canary + short + 12k preflight ONLY; annotate `v0.9.22-pilot-exec-ready` at `478261f…` ONLY after
  PASS; on FAIL return to the SAME v0.9.22 task (never v0.9.23).
- Scientific contract unchanged. This remains v0.9.22 (never v0.9.23).
