# Qwen3-32B Cross-Model Study — Operational Accounting Correction Note

**Date:** 2026-09-11
**Type:** derived-metrics / classification correction only — **raw evidence,
predictions, and RunRecords are unchanged.**
**Scope:** `scientific-stagec-djangocms-qwen3-32b-crossmodel-01` (POST-HOC
CROSS-MODEL ROBUSTNESS REPLICATION).

---

## 1. What was wrong

Two derived-operational accounting defects were found by an independent
inspection of the frozen RunRecords and raw evidence.

### Defect A — Sparse-v2 truncations were under-counted (0 → 6)

The `truncation_status` field was set **only on the success-path evidence
builder** (`_build_cell_evidence`). Failed cells went through
`_build_failed_cell_evidence`, which always wrote `truncation_status: False`.
Six Sparse-v2 failed cells were in fact **completion-cap truncations at the
frozen 4096 budget** — the provider returned `finish_reason=length` (visible in
the persisted failure message) and the persisted raw response is unterminated
JSON (~16 KB ≈ 4096 completion tokens). These were counted as ordinary
"failed" cells, so the published "v2 truncations = 0" was wrong.

### Defect B — call accounting under-counted requests (52 → 60)

`model_calls` was recorded as 0 for 8 failed cells. 7 of them (002-v2-r2,
002-v2-r3, 004-v2-r1..r5) ran under the driver **before the usage-capture
recorder was wired in** (mid-run fix): each issued an API request and received
a provider response (raw persisted) but the provider `usage` object was not
captured, so the record carries `prompt_tokens=0`, `completion_tokens=0`,
`model_calls=0`. The 8th (006-impact_plan-r3) is a genuine transport failure
(`IncompleteRead`) — a request was issued but no usable response was returned.
All 60 manifest cells therefore issued exactly **one API request each**;
recording 52 as "total calls" understated the true request count.

## 2. Exact affected records (raw evidence UNCHANGED)

### Defect A — the six corrected Sparse-v2 truncations

| run_id | scenario | evidence |
|---|---|---|
| stgc32b-...-004-impact_plan_v2-r1 | 004 | failure `finish_reason=length`; raw unterminated (~16,170 B) |
| stgc32b-...-004-impact_plan_v2-r2 | 004 | failure `finish_reason=length`; raw unterminated (~16,492 B) |
| stgc32b-...-004-impact_plan_v2-r3 | 004 | failure `finish_reason=length`; raw unterminated (~16,462 B) |
| stgc32b-...-004-impact_plan_v2-r4 | 004 | failure `finish_reason=length`; raw unterminated (~15,884 B) |
| stgc32b-...-004-impact_plan_v2-r5 | 004 | failure `finish_reason=length`; raw unterminated (~16,126 B) |
| stgc32b-...-008-impact_plan_v2-r2 | 008 | failure `finish_reason=length`; raw unterminated (~16,719 B); **completion_tokens=4096 captured** |

### Defect B — the eight `model_calls=0` records

| run_id | raw persisted? | issue |
|---|---|---|
| ...-002-impact_plan_v2-r2 | yes (valid JSON, conflicting decisions) | usage not captured (pre-fix driver) |
| ...-002-impact_plan_v2-r3 | yes (valid JSON, conflicting decisions) | usage not captured (pre-fix driver) |
| ...-004-impact_plan_v2-r1..r5 | yes (truncated JSON) | usage not captured (pre-fix driver) |
| ...-006-impact_plan-r3 | **no** | transport failure (`IncompleteRead`); request issued, no response |

## 3. Corrected operational counts

| Metric | Old (published) | Corrected | Basis |
|---|---|---|---|
| v1 truncations | 24 | **24** (unchanged) | success-path flag (correct) |
| v2 truncations | 0 | **6** | `finish_reason=length` + unterminated raw |
| Total truncations | 24 | **30** | 24 + 6 |
| v1 valid / failed | 2 / 28 | 2 / 28 (unchanged) | — |
| v2 valid / failed | 21 / 9 | 21 / 9 (unchanged) | — |
| Total valid / failed | 23 / 37 | 23 / 37 (unchanged) | — |
| Recorded `model_calls` (usage-bearing) | 52 | 52 (unchanged field) | recorded |
| **API requests issued** | 52 (mislabeled) | **60** | 1 per manifest cell |
| Usage-bearing responses | 52 | 52 | recorded |
| Responses received (raw persisted) | — | **59** | 7 lost-usage + 52 |
| No-response transport failures | — | 1 | 006-impact_plan-r3 |

**Selection metrics (P / R / F1 / FNR / full-recall) are UNCHANGED** — the six
corrected truncations were already `failed` cells, hence excluded from the
valid-run micro/macro pools.

## 4. Recoverable vs unrecoverable usage

Recoverable (persisted in RunRecords):
- 008-v2-r2: prompt 4159, completion **4096**, calls 1.
- 007-v2-r3: prompt 3588, completion 1676, calls 1.
- All 52 usage-bearing cells (the valid cells + these).

Unrecoverable (exact provider usage not persisted; only raw text remains):
- 5× 004-v2 truncated: completion **exactly 4096 each** (known lower bound,
  `finish_reason=length` = cap reached); prompt usage unknown.
- 2× 002-v2 conflicting: exact usage unknown (raw valid JSON 1,743 / 1,953 B).
- 006-impact_plan-r3: fully unrecoverable (no response).

> These unrecoverable amounts are reported separately and are NOT added to the
> recorded totals. The recorded totals (321,252 tokens; $0.054028 live cost)
> remain the lower-bound scientific accounting.

## 5. Fix applied (derived layer only)

- `scripts/stagec_djangocms_qwen3_32b_crossmodel_execute.py`:
  - new `_is_truncation(record)` classifier (truncation_status OR
    finish_reason=="length" OR `finish_reason=length` in failure message OR
    unterminated persisted raw);
  - `_arm_metrics`, `_write_checkpoint`, `compute_metrics` now use it;
  - totals/arm add `requests_issued` (== recorded cells) and
    `usage_unrecoverable_cells`; a `truncation_classifier` and
    `calls_semantics` field document the semantics.
- `scripts/verify_qwen3_32b_crossmodel_claims.py`: mirrors the classifier and
  asserts the corrected counts (v1 24 / v2 6 / total 30; requests_issued 60;
  usage_unrecoverable 8).
- `tests/unit/test_qwen3_32b_crossmodel_accounting.py`: regression tests
  (7 tests, all pass).
- Regenerated `final_metrics.json`, `closure_gates.json` (six gates + audit
  PASS), README cross-model section, `reports/QWEN3_32B_PAPER_INTEGRATION_NOTE.md`.
- `cross_model_agreement.json` / `QWEN3_32B_CROSSMODEL_AGREEMENT.{md,csv}`
  are **unchanged** (they use valid runs only).

## 6. Old vs corrected headline values

| Headline | Old | Corrected |
|---|---|---|
| v2 truncations | 0 | 6 |
| Total truncations | 24 | 30 |
| v2 truncation rate | 0/30 = 0.000 | 6/30 = 0.200 |
| v1 truncation rate | 24/30 = 0.800 | 24/30 = 0.800 |
| v2 validity rate | 21/30 = 0.700 | 21/30 = 0.700 |
| v1 validity rate | 2/30 = 0.067 | 2/30 = 0.067 |
| "Total calls" | 52 | 60 requests issued (52 usage-bearing) |
| v2 P / R / F1 | 0.360 / 0.621 / 0.456 | 0.360 / 0.621 / 0.456 (unchanged) |
| Live cost | $0.054028 | $0.054028 (unchanged) |
| DIRECTIONALLY REPLICATED | YES | **YES (still holds)** |

Directional criterion check (both must hold): v2 validity > v1 (0.700 > 0.067)
✓; v2 truncation rate < v1 (0.200 < 0.800) ✓.

## 7. Tag / release status

No tags were created or moved for this correction. Tag strategy is deferred
pending review of this note.