# WP-1b Calibration-3 — STOP Report (2026-09-21)

**Mission:** `WP1B_PREFLIGHT_FREEZE_2026-09-21`, Phase C (Calibration-3).
**Authorized:** D6 = YES (Phase C, ceiling $0.25). **Not authorized:** D7 = NO
(main run + variance substudy).
**Branch:** `wp1b/calibration-3-2026-09-21`.

## 1. Executive decision

```
DECISION: CALIBRATION_DONE(CG-1..CG-9 PASS)
```

Calibration-3 executed with protocol v2 (cap 1024), frozen
`qwen/qwen3-coder @ deepinfra/turbo` (temp 0.0). The frozen gate
CG-1..CG-9 all **PASS**. Cumulative cost **$0.081142 ≤ $0.25**. Per-task cost /
B1 worst-case ratios 0.636 / 0.617 / 0.523 — all within 1.2×
(BUDGET_MODEL_V2_OK; no BUDGET_MODEL_V2_WRONG stop). **STOP after Phase C.** The
main run (MAIN_297) and the variance substudy are NOT authorized (D7 = NO).

## 2. Run summary

| Task | Calls | Prompt | Completion | USD | B1 worst | ratio | EMPTY |
|------|-------|--------|-----------|-----|----------|-------|-------|
| saleor-rc-349d46d906ad | 8 | 112,009 | 255 | 0.033858 | 0.053253 | 0.636 | none |
| saleor-rc-b05633dae118 | 8 | 103,876 | 257 | 0.031420 | 0.050923 | 0.617 | none |
| saleor-rc-d52a55471bfc | 8 | 51,883 | 300 | 0.015865 | 0.030339 | 0.523 | none |
| **Total** | 24 | 267,768 | 812 | **0.081142** | — | — | 0 |

Ceiling $0.25. **BUDGET_MODEL_V2_OK** (no task exceeded 1.2× its B1 worst case).

## 3. Gate evaluation (frozen CG-1..CG-9)

| Check | Result |
|-------|--------|
| CG-1 | PASS — 3/3 records, complete protocol metadata |
| CG-2 | PASS — all protocol fields match frozen values |
| CG-3 | PASS — 3/3 telemetry classified (all valid finals) |
| CG-4 | PASS — 0 silent parser failures |
| CG-5 | PASS — 0 unclassified EMPTY |
| CG-6 | PASS — no route/model drift |
| CG-7 | PASS — 0 scientific-knob drift |
| CG-8 | PASS — token accounting identity |
| CG-9 | PASS — $0.081142 ≤ $0.25 |

Full result: `research/wp1b/calibration-3-2026-09-21/wp1b_calibration_gate_result.json`.

## 4. Instrument findings (Phase C report item 3)

- **Cap hits:** 0 (finish_reason == "length" on 0 of 24 calls; all 24 are
  `stop`).
- **Observation truncation rate:** 0.0 across all 3 tasks (no tool output
  exceeded the 2000-char window).
- **EMPTY reasons:** none — all 3 tasks produced a valid final prediction.
- **Per-call finish-reason distribution:** `{stop: 24}`.
- **Per-call sidecar:** 24 records (actions: search_text 9, final 3, list_files
  3, read_file 2, plus 7 empty-action control records); 0 truncated
  observations.
- **Paths surfaced vs read:** task 1: 7 surfaced / 1 read; task 2: 7 surfaced /
  1 read; task 3: 20 surfaced / 0 read.

## 5. Budget model v2 validation

The B1 budget model v2 worst-case estimates comfortably bounded actual cost:
observed / worst-case ratios 0.52–0.64. The model is confirmed fit for purpose
for Calibration-3; no `BUDGET_MODEL_V2_WRONG` stop fired.

## 6. Not scored against labels

Calibration-3 is an instrumentation / protocol sanity check. The 3 calibration
tasks were **NOT** scored against labels, and nothing produced here changes any
Phase-B artifact.

## 7. Independent self-audit

- **Scope:** Calibration-3 only (D6 YES). No main/variance run (D7 NO).
- **Ceiling respected:** $0.081142 ≤ $0.25.
- **786 sealed RESERVE outcomes:** untouched.
- **Phase-B artifacts:** unchanged by Phase C.
- **Freshness:** branch `wp1b/calibration-3-2026-09-21` pushed; `main` remains
  at `f3cbe03` (preflight-freeze integrated).

## 8. Next permitted action

```
MAIN_297 requires a NEW explicit Ahmed authorization (D7 = YES) after he
reviews this Calibration-3 STOP report.
```

Until then, no main run and no variance substudy. The preflight-freeze tag
`wp1b-preflight-freeze-2026-09-21` and all frozen Phase-B artifacts stand.
