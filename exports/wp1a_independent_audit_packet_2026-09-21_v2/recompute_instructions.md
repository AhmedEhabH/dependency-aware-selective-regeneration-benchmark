# Independent Audit — Recompute Instructions

These instructions let an auditor recompute the WP-1a values WITHOUT importing
the WP-1a implementation helpers. Follow the numbered steps. Record your value,
the stored value, and REPRODUCED / DISCREPANCY.

## Step 0 — Setup

- Use a Python 3.11 environment with `numpy`, `pandas`, `sklearn` available
  (the repository environment). Do NOT import `benchmark.wp1a.*` or run
  `scripts/wp1a_*.py` for implementation-independent steps.
- Repository root = the top of the checked-out repository.

## Step 1 — Sample ordering hash (AC-1A.4 input)

1. Load `research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json`.
2. Take `selected_ids` (300 strings, already sorted lexicographically).
3. Compute `sha256( ("\n".join(ids) + "\n").encode("utf-8") )`.
4. Compare to `445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447`.

## Step 2 — Main-50 and Calibration-3 (AC-1A.4)

1. `main_50 = selected_ids[:50]`.
2. `complement = sorted(set(selected_ids) - set(main_50))`.
3. `rng = numpy.random.default_rng(20260921)`; `cal = rng.choice(
   numpy.asarray(complement, dtype=object), size=3, replace=False)`; sort
   ascending.
4. `task_ids_sha256 = sha256(("\n".join(ids) + "\n").encode())` for both sets.
5. `intersection_size = len(set(main_50) & set(cal))` (must be 0).
6. Compare to the stored manifests `research/wp1a/wp1_main_50_manifest.json`
   and `research/wp1a/wp1_calibration_3_manifest.json`.

## Step 3 — Pooled SIP / RM-CSS metrics (AC-1A.3)

Use `research/wp1a/sip_rmcss_per_task_predictions.json` (per task:
`sip_predicted_set`, `rmcss_predicted_set`) and
`research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json`
(`proxies`).

1. For each task: `proxy = set(proxies[cid])`.
2. SIP confusion: `tp = |sip_set & proxy|`, `fp = |sip_set - proxy|`,
   `fn = |proxy - sip_set|`. Sum across all 300 tasks.
3. RM-CSS confusion: same with `rmcss_set`.
4. `precision = tp/(tp+fp)`, `recall = tp/(tp+fn)`,
   `f1 = 2*tp/(2*tp+fp+fn)`.
5. `delta_f1 = f1_rmcss - f1_sip`.
6. Compare to stored `wp1_rederivation_verification.json` and to
   `reports/saleor_reserve_300_rmcss_result.json`.

## Step 4 — Per-task prediction hashes (integrity)

1. For each task, recompute
   `sha256("\n".join(sorted(sip_predicted_set)).encode("utf-8"))` and
   compare to the stored `sip_prediction_hash` (same for RM-CSS with
   `rmcss_prediction_hash`).
2. Note: the hash is computed WITHOUT a trailing newline.

## Step 5 — Label isolation (AC-1A.2)

1. `pandas.read_parquet("research/saleor-reserve-300-rmcss/candidate_rows_saleor300.parquet")`.
2. Confirm the raw artifact has a `label` column; check it is all-zero.
3. Confirm `research/wp1a/sip_rmcss_per_task_predictions.json` contains no
   label/outcome column.
4. State exactly what this proves (non-informative tested vector; NOT past
   informative leakage).

## Step 6 — Model provenance (AC-1A.1)

1. Read `research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl` (300
   lines).
2. For each record, extract the scientific model + provider/temperature/cap.
3. Count how many match `qwen/qwen3-coder` @ `deepinfra/turbo` (temperature
   0.0). Report (n_matching, n_total).

## Step 6B — RM-CSS reproduction from the deployment artifact (REPRODUCTION TRAP 1)

**Do NOT use the `feature_names` order.** In
`research/stage5-v2-final/deployment_artifact.json` the `lr_coef` vector is
ordered `continuous_features` + `boolean_features`.

1. Load `candidate_rows_saleor300.parquet` and the deployment artifact.
2. Build X in the order `continuous_features` (standardized with
   `scaler_mean`/`scaler_scale`) then `boolean_features` (as float, not
   standardized).
3. `p = 1/(1+exp(-(X @ lr_coef + lr_intercept)))`; predicted set = file paths
   where `p >= threshold` (per case_id).
4. Compare to each task's `rmcss_predicted_set` in
   `research/wp1a/sip_rmcss_per_task_predictions.json`. Expect **0/300**
   mismatching tasks.
5. Sanity check of the trap: if you instead use the `feature_names` order you
   should observe **174/300** mismatching tasks. If you see 174, you hit the
   trap; redo with the documented order.

## Step 6C — FULL-only inputs (REPRODUCTION TRAP 2)

The RM-CSS reproduction above and the WP-1a A7 universe check read per-case
public artifacts under `benchmark_data/real_commit_impact_saleor/scientific/
<case_id>/public/candidate_universe.json` and `dependency_graph.json`. These
are excluded from the LIGHT export (`scripts/export_light_project_v2.py`). If
the packet you received is a LIGHT export, these steps cannot run — request a
FULL checkout/export (or re-derive the universes from the pinned Saleor
snapshot) before executing Steps 6B and the A7 universe check.

## Step 7 — Cross-check reproducibility (AC-1A.10)

1. OPTIONAL, and only as a cross-check: run
   `python scripts/wp1a_independent_audit.py` in the repository root
   (zero API). Record the exit code and 19-check result.
2. Remember: this script was authored in the same session as the WP-1a
   implementation. Treat its result as a cross-check, NOT as an independent
   audit.

## Step 8 — Final report

Produce a table:

```
check | recomputed value | stored value | REPRODUCED/DISCREPANCY | note
```

Do not change any repository file. Do not run paid inference. Do not open the
786 unread Saleor RESERVE outcomes.