# Independent Audit Packet — WP-1a / WP-1b Readiness (v2)

**Prepared:** 2026-09-21
**Mission:** WP1B_PREFLIGHT_FREEZE_2026-09-21 (pre-result freeze)
**Repository commit at preparation:** branch
`wp1b/preflight-freeze-2026-09-21` (see `git provenance` in the closure
package)
**Version:** v2 — SUPERSEDES v1 (`exports/wp1a_independent_audit_packet_2026-09-21/`),
which stays untouched as history. v2 adds two reproduction traps the external
review found: **coefficient order** and **FULL-only inputs**.

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

- `README_AUDITOR.md` — this file (v2: coefficient order + FULL-only inputs).
- `acceptance_criteria.json` — the AC-1A.1..12 acceptance criteria as
  machine-readable checks.
- `artifact_manifest.json` — the artifact universe + expected stored values.
- `sha256sums.txt` — SHA-256 of every referenced artifact.
- `recompute_instructions.md` — step-by-step independent recomputation.

## REPRODUCTION TRAP 1 — RM-CSS coefficient order (MANDATORY)

In `research/stage5-v2-final/deployment_artifact.json` the `lr_coef` vector is
ordered **`continuous_features` + `boolean_features`**, NOT in the order of the
`feature_names` field. The `feature_names` field lists a DIFFERENT order.

- Using the `feature_names` order to multiply the feature matrix: **174/300
  tasks fail to reproduce the stored RM-CSS predicted sets.**
- Using the documented order `continuous_features + boolean_features`:
  **0/300 mismatches.**

Reproduce RM-CSS probabilities as:

```
X = column_stack([ (f - scaler_mean[f]) / scaler_scale[f]  for f in continuous_features ] +
                 [ candidate_rows[f].astype(float)          for f in boolean_features ])
p = 1 / (1 + exp(-(X @ lr_coef + lr_intercept)))
predicted = file_path where p >= threshold
```

If you reproduce with `feature_names` order and get 174 mismatching tasks, you
have hit this trap — switch to the documented order. This is the single most
common reason an external auditor fails to reproduce RM-CSS.

## REPRODUCTION TRAP 2 — FULL-only inputs (MANDATORY)

`scripts/wp1a_independent_audit.py` (and the RM-CSS reproduction above) read
inputs that the **LIGHT export does NOT contain** because they are derivable
per-case artifacts. To audit you MUST use a FULL checkout/export containing:

- `benchmark_data/real_commit_impact_saleor/scientific/<case_id>/public/candidate_universe.json`
  (530 cases; the WP-1a audit reads this per task for the parent-state universe
  check).
- `benchmark_data/real_commit_impact_saleor/scientific/<case_id>/public/dependency_graph.json`
  (530 cases; deterministic per-case derived graph).
- `benchmark_data/real_commit_impact_saleor/saleor_development_manifest.json`.

These paths are excluded by `scripts/export_light_project_v2.py`
(`/real_commit_impact_saleor/scientific/` → `candidate_universe.json` /
`dependency_graph.json` are dropped). If the packet you receive is a LIGHT
export, the RM-CSS reproduction (Trap 1) and the WP-1a A7 universe check CANNOT
be executed — request the FULL export or re-derive the per-case universe from
the pinned Saleor repository snapshot.

## Ground rule on labels

The `candidate_rows_saleor300.parquet` `label` column is an all-zero
placeholder. Verify it is not exposed to prediction-side code. This proves the
tested leakage vector was non-informative; it does NOT prove that informative
labels had previously leaked. Do not overstate.

## Reporting

Report your findings as a table (check id, recomputed value, stored value,
status REPRODUCED/DISCREPANCY, note). Return this to Ahmed.