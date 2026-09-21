# Independent Audit Packet — WP-1a / WP-1b Readiness

**Prepared:** 2026-09-21
**Mission:** WP-1a Integration Closure → WP-1b Execution Readiness
**Repository commit at preparation:** (see `git provenance` section in the
closure package)

## Purpose

This packet lets a genuinely independent auditor verify the WP-1a acceptance
criteria WITHOUT trusting:
- the WP-1a STOP report prose,
- the WP-1a implementation helpers (`benchmark.wp1a.*`), or
- this mission's own cross-check.

The WP-1a 19-check pass is a **same-session alternate-implementation
cross-check**, not an independent audit. This packet is the handoff for the
real independent audit.

## Critical instruction for the auditor

- Do NOT assume the expected result is PASS. Compute every value yourself and
  compare.
- Do NOT adjust your conclusion to support any thesis.
- Do NOT import `benchmark.wp1a.*`, `scripts/wp1a_*.py`, or
  `src/benchmark/wp1a/*` when the goal is an implementation-independent check.
  Re-implement the formulas from the definitions in `recompute_instructions.md`.
- Do NOT run any paid API call. Everything here is recomputed from frozen
  artifacts already in the repository.
- Any discrepancy between your recomputed value and the stored value is a
  finding. Distinguish:
  - **DISCREPANCY** — your value differs; report both values and the likely
    cause.
  - **REPRODUCED** — your value matches the stored value exactly (or within
    the stated tolerance).

## Contents

- `README_AUDITOR.md` — this file.
- `acceptance_criteria.json` — the AC-1A.1..12 acceptance criteria as
  machine-readable checks.
- `artifact_manifest.json` — the artifact universe + expected stored values.
- `sha256sums.txt` — SHA-256 of every referenced artifact.
- `recompute_instructions.md` — step-by-step independent recomputation.

## Ground rule on labels

The `candidate_rows_saleor300.parquet` `label` column is an all-zero
placeholder. Verify it is not exposed to prediction-side code. This proves the
tested leakage vector was non-informative; it does NOT prove that informative
labels had previously leaked. Do not overstate.

## Reporting

Report your findings as a table (check id, recomputed value, stored value,
status REPRODUCED/DISCREPANCY, note). Return this to Ahmed.