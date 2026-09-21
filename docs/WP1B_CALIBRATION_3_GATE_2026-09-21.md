# WP-1b Calibration-3 Gate (frozen before inference)

**Date:** 2026-09-21
**Status:** FROZEN BEFORE INFERENCE (mission section 23). No calibration
inference has run; the gate definition is committed before any calibration
outcome exists.

## Purpose

Calibration is an instrumentation/protocol sanity gate, NOT an opportunity to
tune the method against performance. The gate checks execution validity and
instrumentation correctness. It does NOT gate the main run on F1.

## Frozen checks (machine-checkable)

Machine-readable: `artifacts/wp1b_calibration_gate.json`.

| ID | Requirement |
|----|-------------|
| CG-1 | 3/3 requested calibration tasks executed under the intended protocol |
| CG-2 | 3/3 protocol metadata records complete |
| CG-3 | 3/3 valid final outputs OR failure explicitly classified |
| CG-4 | 0 silent parser failures |
| CG-5 | 0 unclassified EMPTY predictions |
| CG-6 | 0 route/model drift |
| CG-7 | 0 unexpected scientific-knob drift |
| CG-8 | 0 corrupted accounting records |
| CG-9 | 0 unexplained budget overrun |

Evaluator: `scripts/wp1b_calibration_gate.py <calibration_results_dir>`.
Result: `artifacts/wp1b_calibration_gate_result.json`.

## Truncation / cap handling

- Report exact cap-hit and truncation counts from the first-class telemetry
  (`src/benchmark/wp1b/telemetry.py`).
- Use the already frozen G2 cap rule; do NOT invent a post-calibration cap
  change.
- The frozen pre-run protocol does NOT declare any cap hit/truncation as a
  stop trigger, so cap hits during calibration are reported, not a stop
  trigger.

## Performance-based calibration rules (mission section 24)

- NO F1-based calibration continuation rule is frozen.
- Calibration F1 alone MUST NOT tune or cancel the main experiment, except for
  obvious protocol/instrumentation failure already defined in advance (e.g.,
  CG-4/CG-5 fail-closed instrumentation defects).

## Falsifiers

- This gate is wrong if a future WP-1b run evaluates checks that were not in
  the frozen set above, or if calibration F1 is used to tune the main run.