# M4A-3 / P1 — Serialized-Record Metric Correction

**Date:** 2026-09-14
**Study:** `real-commit-p1-full-v2-vs-sparse-v2-01`
**Type:** derived-metric recomputation from persisted raw responses (ZERO API calls).

## 1. Defect

The original metrics (`final_metrics.json`) computed `serialized_records` and
task-level `*_records_mean` from `len(decoded_write_set_ids)`. That field holds
ONLY decoded `REGENERATE` candidate ids — the **predicted write-set size** — and
is NOT the number of decision rows the model serialized. Evidence of the
mislabel: Full-v2 must serialize exactly one decision per candidate (the frozen
manifest candidate counts are 140–152, mean 144), yet the original report showed
`Records mean = 4.03`, which equals the mean REGENERATE write-set size.

## 2. Method

For each of the 60 frozen P1 cells, the persisted raw provider response
(`research/real-commit-p1-01/runs/raw/<run_id>.txt`) is parsed:

    parsed = json.loads(raw)
    payload = json.loads(parsed["choices"][0]["message"]["content"])
    serialized_decision_count = len(payload["decisions"])

`serialized_decision_count` is persisted per cell; `predicted_write_set_size`
is retained separately as `len(decoded_write_set_ids)`. Raw response bytes are
never modified. P/R/F1/FNR, TP/FP/FN, validity, truncation, token usage, cost,
and latency are read unchanged from the persisted run records.

## 3. Independent assertions (every valid cell)

- Full-v2: `serialized_decision_count == candidate_count` — asserted for
  all valid cells; **failures:
  0**.
- Sparse-v2: no explicit `PRESERVE` rows AND `serialized_decision_count`
  == explicit non-PRESERVE decision count — **failures:
  0**.
- Total cells parsed: 60; total assertion failures: 0.

## 4. Corrected serialized-record metrics

| Arm | Serialized records mean | Predicted write-set mean |
|---|---:|---:|
| Full-v2 | **144.000** | 4.033 |
| Sparse-v2 | **4.067** | 2.500 |

Paired task-level delta (Sparse − Full) in serialized records + bootstrap CI:

- mean delta: **-139.910**
- 95% bootstrap CI: **[-143.300, -137.000]** (10,000 resamples over 10 tasks, seed 20260914)

## 5. Former (mislabeled) values for comparison

| Quantity | Former (write-set size) | Corrected (serialized decisions) |
|---|---:|---:|
| Full-v2 mean | 4.033333 | **144.000** |
| Sparse-v2 mean | 2.5 | **4.067** |
| Delta mean | -1.540287 | **-139.910** |
| Delta CI | [-2.833334, -0.366667] | **[-143.300, -137.000]** |

## 6. Interpretation impact

- The serialized-record reduction of Sparse-v2 is **larger** than the former
  write-set-only value indicated (Sparse now correctly includes explicit
  VALIDATE / HUMAN_REVIEW rows; Full-v2 is the full candidate serialization).
- Semantic metrics (P/R/F1/FNR), validity, truncation, tokens, cost, and
  latency are **unchanged** — this correction affects only the serialized
  decision-record derived metric.
- The historical diff remains an **OBSERVED CHANGE-SET PROXY**, never semantic
  ground truth.

## 7. Artifacts

- `research/real-commit-p1-01/final_metrics_serialization_corrected.json`
- `research/real-commit-p1-01/serialization_metric_corrected.json` (per-cell)
- `research/real-commit-p1-01/final_metrics.json` (original, UNCHANGED)
- This report.

## 8. Regression coverage

`tests/unit/test_real_commit_p1_serialization_metric.py` proves Full-v2
record count equals candidate count and Sparse-v2 record count derives from
raw `decisions` (not write-set size). `tests/integration/` re-runs this
recomputation against the persisted evidence.

## 9. Related findings from the same audit (NOT re-run here)

The same defect pattern (reporting `len(decoded_write_set_ids)` as
"serialized records") exists in the runners for the **M1B controlled 16K
study** (`scripts/controlled_encoding_ablation_execute.py`, sparse arm) and
the **M3 graph ablation** (`scripts/graph_ablation_execute.py`). The frozen
M1B/M3 final-metrics JSONs and result reports are NOT rewritten in this
milestone (historical evidence preserved). Both runners are fixed
prospectively so any future re-execution persists `serialized_decision_count`
alongside `predicted_write_set_size`. Audit-quantified magnitude for M1B
sparse-v2 from the persisted raw responses: serialized decision mean **5.9**
vs the reported write-set mean **4.9**. Registered as technical-debt items
TD-011/TD-012 for a separate decision.
