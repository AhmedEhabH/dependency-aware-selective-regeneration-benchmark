# WP2 M14A Pilot-A V1: execution blueprint v2 (corrected)

Scientific role: Pilot-A calibrates GOLD_HARD against PLACEBO_HARD on 12 protected ASSAY_HOLDOUT tasks, with 2 replicates each. It is not a selector comparison.

## Phases, with executor and exit mapping

| Phase | Does | Output (under research/wp2/pilot_a_v1/) | On failure |
|---|---|---|---|
| P00 | kit self-tests (zero network) | — | KIT_SELFTEST_FAIL (stop) |
| P01 | M13B guard: design, selection, verify and freeze hashes; pool = A+B+reserve | m14a_guard.json | M14A_GUARD_FAIL |
| P02 (loop) | readiness of the 26 tasks, one task per iteration (C4 V3.1; P2P-U V3 cap200; gold/empty check) | readiness/<task>/{record,detail}.json | 33 → READINESS_ENV_FAIL (resumable, same task) |
| P03 | frozen `finalize_after_readiness`, then the evaluator sets | pilot_final_membership.json, evaluator_only/ | 31 → POOL_INSUFFICIENT (human hold, no paid run) |
| — | **human**: `scripts/wp2_m14a_authorize.py` (template-bound, ≤ $1.00, committed) | human_authorization.json | — |
| P04 | authorization check | auth_check.json | 32 → NOT_AUTHORIZED (resumable) |
| P05 / P06 | doctor offline / read-only paid doctor | doctor/ | 33 → PAID_PREFLIGHT_FAIL (resumable) |
| P07 | ENG canary `saleor-rc-2d45b76a52f2` (never a Pilot task) | canary.json, junit/ | 33 → CANARY_FAIL; 79 → EVAL_ERROR |
| P08 | paid-run freeze + exact tag | pilot_a_freeze.json, frozen_scopes.json, generation_plan.json | FREEZE_FAIL / FREEZE_DRIFT |
| P09 (loop) | **only paid step**: 48 episodes | episodes/, cache_namespaces/, ledger/, transport/ | 75 outage (resumable), 76, 77, 78 |
| P10 | generation freeze + exact tag (before any evaluation) | generation_freeze.json | GENERATION_FREEZE_FAIL |
| P11 | plan keyed by (task_id, full diff sha) | evaluations/plan.json | M14A_INVARIANT |
| P12 (loop) | evaluation with evaluator-core guards | evaluations/, junit/ | 79 → EVAL_ERROR (resumable); corrupt record → 78 |
| P13 | A0–A5 gates via `gates_for(n)`; token; no auto M14R/M15 | pilot_a_summary.json, docs/WP2_PILOT_A_V1_RESULT.md | — |
| final | state `complete=true` → commit → push → exact result tag → LIGHT | — | FINAL_ACTION_FAILED (resumable) |

**Result tokens:**

- `PILOT_A_PASS` → the brain builds M15.
- `PILOT_A_GENERATOR_FLOOR_HOLD`, `PILOT_A_PLACEBO_LEAK_REVIEW`, `PILOT_A_INSTRUMENT_FIX` → human decision.
