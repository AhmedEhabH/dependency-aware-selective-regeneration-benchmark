# MISSION-11 E2E Smoke — Impact Declaration (2026-09-27)

Authority: MISSION-11 (`_workspace/active/MISSION_11_ONE_SHOT_ENG_TO_FIRST_E2E_2026-09-26.md`)
decision register §3 D30–D64, incorporated here by reference. This Smoke runs
after the WP-2 Environment Closure V3.1 (ENG_SMOKE_READY = YES).

## What changes
- Builds the shared WP-2 E2E instrument (generator + validator + repair +
  evaluator) in `src/benchmark/wp2/e2e/` (zero API during build).
- Runs the first E2E Smoke on the 14 ENG behavioral tasks × 4 arms
  (GOLD_HARD / RMCSS_HARD / AGENT_HARD / PLACEBO_HARD) × 1 replicate.

## What does NOT change
- Oracle semantics, Harness V3, P2P-U rule/salt/caps, populations/splits,
  workers=1, 3-repetition policy, leakage firewall, frozen agent protocol v3.

## Population
- Smoke population = 14 behavioral ENG tasks (§3 D40). Symbol-only tasks
  (`22ec4dab0154`, `9258154b8a0b`) are listed only, never generated.
- Evaluator sets (protected): `evaluator_only/eng_evaluator_sets_v3.json`.

## Arms (all HARD)
- `GOLD_HARD` = target-changed non-test paths (D42).
- `RMCSS_HARD` = RM-CSS out-of-fold realization-A DEV predictions (D43).
- `AGENT_HARD` = frozen protocol-v3 Agent selected_paths (D44, from AU6).
- `PLACEBO_HARD` = deterministic sha256-ranked placebo of size |GOLD| (D45).

## Budget
- AU6 Agent scopes ≤ $1.00; AU7 Smoke generation ≤ $4.50; hard total ≤ $5.50.
- No paid call before C1 preflight + freeze tag + ledger check.

## Leakage boundary
- Generators never read `evaluator_only/`. No F2P/P2P ids, test patch, target
  diff, target contents, or oracle outcomes in any prompt (I6).

## Stop tokens
STATE_MISMATCH · UNLISTED_SCIENTIFIC_DECISION · BLOCKED_ENGINEERING ·
USER_STOP_FLAG · INFRA_DB_DOWN · INFRA_DOCKER_DOWN · CLOCK_BLOCKED ·
P2PU_INTEGRITY_STOP · RESOURCE_GUARD · E2E_INSTRUMENT_INVALID ·
E2E_BUDGET_PROJECTION_EXCEEDED · INTENT_SOURCE_UNRESOLVED ·
PRICING_DRIFT_STOP · E2E_PROVIDER_OUTAGE · E2E_BLOCKED_NO_CREDIT ·
E2E_BUDGET_STOP · E2E_SMOKE_PIPELINE_VALID · E2E_SMOKE_FLOOR_EFFECT ·
E2E_SMOKE_INSTRUMENT_INVALID.