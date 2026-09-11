# Qwen3-Coder-30B-A3B-Instruct Cross-Model Study — Accounting Correction Note

**Date:** 2026-09-11
**Type:** derived-accounting field correction only — **raw provider responses,
scientific predictions, validity classifications, truncation classifications,
and selection metrics are UNCHANGED.**
**Scope:** `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01`
(POST-HOC CROSS-MODEL / CROSS-PROVIDER ROBUSTNESS REPLICATION).

---

## 1. What was found by the independent audit of the recorded accounting fields

After the 60 scientific cells completed, an independent audit of the recorded
per-cell accounting fields found a **wiring artifact in the recording layer**
(a snapshot ordering defect in the executor), which affected four derived
*accounting* fields. No scientific input, raw response, prediction, or
validity/truncation classification was affected.

### Defect — recorded field values (as written by the executor)

| Field | Recorded value | Truth (from immutable raw evidence) |
|---|---|---|
| `request_dispatched` | `False` on ALL 60 records | **True** on all 60 (each manifest cell dispatched exactly one provider request) |
| `usage_received` / `usage_known` on the single transport-failure cell (`stgc30b-djangocms-external-validity-007-impact_plan_v2-r3`) | `True` | **False** — no provider response and no usable usage was returned |
| `transport_failure` on `...-007-impact_plan_v2-r3` | `False` | **True** — failure category `OpenRouter request failed: Remote end closed connection without response` proves a request was dispatched with no usable response |

Root cause: in the executor's `run_cell`, the `accounting` dict (including
`request_dispatched` and `usage_received`) was snapshotted **before**
`runner.run(...)` executed, so the recorder's post-run dispatch/usage state was
never reflected. The executor wiring was fixed for any future recomputation.
The 60 recorded RunRecords themselves are **preserved byte-identical** (they
are the immutable record of what ran); the authoritative accounting is derived
from the immutable raw evidence exactly as the Qwen3-32B accounting correction
(2026-09-11) was handled.

## 2. Authoritative accounting derived from immutable raw evidence

- Raw responses: 59/60 persisted in `runs/raw/{run_id}.txt` (SHA-256 sidecars
  verified). The only cell without a raw response is
  `...-007-impact_plan_v2-r3` (transport failure).
- **Requests issued: 60** (59 raw responses + 1 transport failure that reached
  the provider; all 60 manifest cells dispatched exactly one request).
- **Responses received: 59.**
- **Usage-known cells: 59. Usage-unknown cells: 1** (`...-007-impact_plan_v2-r3`;
  its billed usage/cost are genuinely unavailable and are NOT silently zeroed).
- **Transport failures: 1.**
- Recorded tokens 203,806 prompt + 97,340 completion = **301,146 total** are a
  **LOWER-BOUND** (the transport-failure cell consumed an unknown provider
  usage that is not recorded).
- Recorded live cost **$0.041518** (SiliconFlow $0.07/$0.28 per 1M) is a
  **LOWER-BOUND** for the same reason.

## 3. What is unchanged

- All 60 raw provider responses and their SHA-256 sidecars.
- `run_records.jsonl` (byte-identical; includes the recorded accounting fields
  as-written, which are superseded for *accounting* purposes by the derived
  values in this note and in `final_metrics.json`).
- Validity counts (45 valid / 15 failed), truncation counts (11: all v1),
  TP/FP/FN, Precision/Recall/F1/FNR, full-recall, S006 analysis, agreement.
- The `truncation_status` / `completion_cap_hit` fields and the truncation
  classifier (which already used raw-evidence fallback) were correct.

## 4. Where the derived accounting lives

- `final_metrics.json` — `totals`/arm blocks use the raw-evidence-derived
  accounting (`requests_issued`, `responses_received`, `usage_known_cells`,
  `usage_unknown_cells`, `transport_failure_cells`, `lower_bound_qualified`).
- `scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py` — recomputes all
  accounting from the records + raw evidence and asserts the corrected values
  (exit 0 = PASS).
- This note is the human-readable explanation.

## 5. Corrected headline accounting

| Metric | Corrected |
|---|---|
| Requests issued | **60** (1 per manifest cell) |
| Responses received | **59** |
| Usage-known cells | **59** |
| Usage-unknown cells | **1** (`...-007-impact_plan_v2-r3`, transport failure) |
| Transport failures | **1** |
| Recorded total tokens | **301,146** (LOWER-BOUND) |
| Recorded live cost | **$0.041518** (LOWER-BOUND) |
| Directional label | `DIRECTIONALLY REPLICATED` (see results) |