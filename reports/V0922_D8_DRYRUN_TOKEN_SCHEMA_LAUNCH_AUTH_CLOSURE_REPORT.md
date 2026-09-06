# v0.9.22 D8 Dry-Run Token-Schema + Launch-Auth Evidence Closure

**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Date:** 2026-08-28
**Status:** CLOSED — REAL T4 PROOF PENDING (no stable tag created)

## Closure

D8 closes a proven `RunRecordData` token-schema drift that made the old bundled
48-cell dry-run gate a **false green**:

- A real 48-record CLI dry-run writes nested `token_usage`
  (`prompt` / `completion` / `total`) plus `total_workflow_model_calls`,
  `total_workflow_tokens`, phase `selection|regeneration|repair` `_model_calls` /
  `_total_tokens`, and status `succeeded` — it NEVER writes a top-level
  `total_tokens`.
- The pre-D8 bundled `dryrun-cell` read the fabricated top-level
  `total_tokens`; the old 48-cell gate therefore **PASSes real records** via the
  fail-open `or 0` check. This false-green behavior is proven by a dedicated
  regression test.

Deliverables:

- **D8.1** Canonical `validate_pilot_dryrun_evidence` + private
  `_collect_dryrun_evidence_errors` in `src/benchmark/execution/preflight.py`
  with strict `_expect_zero_int` (None/bool/str/float/non-zero all fail closed),
  returning a truthful summary, and `validate_pilot_launch_authorization`
  refactored to reuse the same collector (single source of truth).
- **D8.2** The bundled `dryrun-cell` calls the canonical validator with
  `expected_model_identity="dry-run:mock"` and prints only summary-backed totals
  (`dryrun_summary['total_tokens']`), never fabricating a top-level field.
- **D8.3** The GQA per-device display (notebook cell 8) reads all real evidence
  fields (`device_index`, `device`, `passed`, `gpu_name`, `compute_capability`,
  `before_heads`, `after_heads`, `q_device`, `k_device`, `v_device`,
  `output_device`, `output_shape`, `error`) on `dryrun_summary['gqa_probe']` —
  no `available` fallback/guess.
- Incidental mypy fixes in `preflight.py` (line-362 `no-any-return` on the
  long-context probe result; `rep_counts` retyped) — all four were pre-existing
  at HEAD, verified via a temporary worktree.

## RED / GREEN evidence

- **RED (genuine):** 39 new unit tests plus 1 false-green proof failed before
  D8.1 (fabricated-schema acceptance, missing-validator failures,
  `validate_pilot_launch_authorization` mismatch each recorded as failure).
- **GREEN (focused):** `TestPilotDryrunEvidenceValidatorIntegration` 2 passed;
  contract schemas (`TestPilotDryrunCellSchema`,
  `TestGqaPerDeviceEvidenceDisplay`) 8 passed; full notebook-contract +
  deployment-bundle suites **136 passed** in 228s.
- **GREEN (acceptance):** full suite **2492 passed / 33 skipped / 0 failed**
  in 1099.73 s (18:19) — D7 baseline was 2442, +50 tests.
- Diagnostics: `git diff --check` clean (only expected LF→CRLF notices),
  Ruff clean on all changed Python files, mypy clean on `preflight.py`
  (`Success: no issues found in 1 source file`), `compile()` OK on the notebook
  cells and changed sources.

## Exact artifact acceptance

- Two-pass finalizer (`scripts/finalize_pilot_notebook_trust.py`):
  - PASS 1 (discovery, WS anchor write) then PASS 2 (validation build,
    idempotent) with `--verify-source-provenance`;
  - `git show <source>:<path>` blob equality for the notebook and every
    `code_manifest.json` entry — **0 provenance mismatches**;
  - `reports/pilot_notebook_trust_freeze.json` **FROZEN**.
- Identity: task `PILOT-EXEC-01`, source commit
  `8f0b11953a4fe2990b7e6c680288be282b8a6b67`, source tag
  `v0.9.22-pilot-exec-ready` (planned), code manifest
  `54e112130b01fddaa95e35dc4b73d45e1c76977c380036accb044a8ae5c00af4`.
- Artifact: `dist/pilot-kaggle-upload.zip`
  SHA-256 `02d16ca2c3a35969b32ac438e577f41198e376ba0ce9ee88757a07bd46f268ee`;
  sidecar (`dist/pilot-kaggle-upload.zip.sha256`) matches.
- Exact final-artifact dry-run (fresh extraction, bundled CLI, explicit
  `--source-commit 8f0b11953a4fe2990b7e6c680288be282b8a6b67`):
  **48/48 succeeded, 48 unique run IDs, repos 16/16/16, strategies 24/24,
  reps 24/24, 0 model calls, 0 tokens**, and the canonical
  `validate_pilot_dryrun_evidence` **PASS** over that dry-run directory
  (every record source commit == `8f0b119…`).

## Scientific and release truth

- Frozen scientific contract **UNCHANGED** (model Qwen2.5-Coder-14B-Instruct,
  BNB-NF4, sdpa, kernel policy `flash_or_efficient_no_math`, GQA compat
  `repeat_kv_sm75`, 12 scenarios, 3 pins, 2 strategies, 2 reps = 48 cells,
  prompts, Ground Truth, metrics, `--timeout 600`, `--validation-timeout 1800`,
  max attempts 3, completion cap 4096, the 12000/64 long-context gate).
- No stable tag created. **NO 48-cell launch.**
- Next action (single exact step): upload ONLY this artifact and run the fresh
  real 2x T4 Kaggle model preflight (repo preflight + heartbeat, Qwen 14B
  BNB-NF4 load, GQA microprobe, short probe, 12k/64 probe with
  attention-policy evidence); only on PASS annotate
  `v0.9.22-pilot-exec-ready` at `8f0b11953a4fe2990b7e6c680288be282b8a6b67`;
  on FAIL return to the SAME v0.9.22 task (never v0.9.23).
- Commits in this closure: code+tests `969eca10…` (C0), frozen notebook
  `8f0b11953a4fe2990b7e6c680288be282b8a6b67` (C1, artifact source / future
  tag target), freeze report `6cb5466…` (C2), then the docs commits.
- Superseded artifacts (do not upload): D7 `e0a64937…` from `3ebc75d…`;
  D1–D6 `ce40b330…` from `f72ecda…`; candidate-consistency `3fd98626…`;
  first-freeze `9182ea2b…`; long-context `bfbc935f…`; pre-D8 bundled
  dryrun-cell fabricated-token gate.