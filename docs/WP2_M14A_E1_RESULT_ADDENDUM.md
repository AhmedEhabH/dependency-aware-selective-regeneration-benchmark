# WP2 Pilot-A V1: M14A-E1 evaluator amendment addendum

Rule: `M14A_E1_PATCH_STARTUP_FAILURE_V1`. Unique evaluations: 29. Scored under E1 as PATCH_STARTUP_FAILURE: 2.

A patch whose tree cannot start pytest (all runs without JUnit, a Python traceback naming an edited file, parent/gold trees verified to start in readiness) is scored with every node `missing` (not passed), the frozen Smoke v2.2 semantics. Every other missing JUnit remained an infrastructure STOP.

| Task | Arm | Diff | Decision | Edited file(s) in traceback | F2P | P2P-S | P2P-U200 |
|---|---|---|---|---|---|---|---|
| saleor-rc-b14def73518c | GOLD_HARD (GOLD_HARD__r2) | 073711c62862 | PATCH_STARTUP_FAILURE | saleor/product/models.py | FAIL | FAIL | FAIL |
| saleor-rc-b14def73518c | GOLD_HARD (GOLD_HARD__r1) | f1aeafb9e0ee | PATCH_STARTUP_FAILURE | saleor/product/models.py | FAIL | FAIL | FAIL |

Descriptive addendum. It changes no gate, threshold or endpoint.
