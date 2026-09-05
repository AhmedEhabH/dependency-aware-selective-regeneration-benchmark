# SCIENTIFIC-WIP-IMPACTPLAN-V1 — INDEPENDENT AUDIT (internal, before external GPT-5.6 Sol audit)

## Audit print (D047 / 06_OPENCODE_NEXT_TASK_SINGLE_PASS Step 10)

```
SCIENTIFIC_GOAL_CHANGED=NO
QWEN14_T4_REOPENED=NO
OLD_48_LAUNCHED=NO
DJANGOCMS_WORK=NO
SALEOR_WORK=NO
GOLD_EXPECTED_ACTIONS_VISIBLE_TO_EXECUTOR=NO
EVALUATOR_VISIBLE_TO_STRATEGIES=NO
MODEL_PROVIDER_FROZEN=NO            (acceptance gate FAILED on both providers; no freeze)
PROVIDER_FALLBACKS=NO               (contract enforces no-fallback; gate evidence recorded)
THRESHOLDS_CHANGED_AFTER_CALLS=NO
SCENARIOS_CHANGED_AFTER_CALLS=NO
PREDICTED_ACTIONS_PERSISTED=YES
ACTUAL_CHANGED_PATHS_PERSISTED=YES
MIGRATIONS_SCORED_SEPARATELY=YES
```

## Construct audit (Stage-C contract)

- ImpactPlan persisted BEFORE first write: YES (sidecar `impact_plans/<run>_<vN>.json` before executor).
- Every candidate artifact classified exactly once R/P/V/H: YES (gate invariant #1 + tests).
- `write_set == {R}`: YES (plan_from_impact_plan builds executable plan from write_set only).
- P/V/H writes blocked + logged: YES (WRITE_GUARD_BLOCKED + prohibited_write_attempts).
- context_set independent of action sets: YES (orthogonality tested).
- validation/test obligations separate (ValidationObligation): YES.
- every R cites strategy-visible evidence: YES (gate invariant #6).
- low-confidence/conflict -> H under frozen rule (conf<0.60): YES (apply_uncertainty_rule).
- at most one bounded expansion v1->v2 then HUMAN_REVIEW: YES (integration tests).
- planner cost counted: YES (planner tokens/calls/latency in RunRecord fields).

## Fairness / leakage audit

- Same NL requirement/repo/model/provider for both arms: YES (matched profile arms).
- No gold expected_actions or hidden evaluator in planner/executor inputs: YES (sentinel tests + planner template scan).
- Baseline (iterative agent) does not receive ImpactPlan: YES (only impact_plan arm emits it).
- Unknown paths rejected: YES (gate invariant #8).

## Measurement audit

- initial-plan impact metrics computable (R/P/V/H action counts, write/validate/context sizes): YES.
- preservation/correctness/architecture evidence computable: YES (changed_artifact_paths, evaluator, obligations).
- planner + executor + repair/expansion cost counted: YES.

## Validation gates

All six Pre-Benchmark gates for scientific-wip-impactplan-v1 PASS:
G1 Dataset Validation PASS, G2 Prompt Validation PASS, G3 Pipeline Smoke PASS,
G4 Dry Run PASS (30 cells, 15 agent + 15 impact_plan, 0 calls/tokens),
G5 Integration PASS, G6 Metric Verification PASS.
Full suite once PASS: 2805 passed / 33 skipped / 0 failed.

## Model/provider acceptance gate — FAIL (preregistered STOP)

Primary model `qwen/qwen3-coder` on BOTH predeclared providers FAILED the frozen
A2 exact-patch task (deterministic byte-exact SEARCH) — 3/3 deterministic-task
success not met on either provider:

- DeepInfra: A2 SEARCH block contained an extra trailing newline vs the frozen
  current file, so the byte-exact apply rejected it (A1 PASS, A3 PASS).
- Novita: A2 output degenerated into many repeated `>>>>>>> REPLACE` markers
  (A1 PASS, A3 PASS).

Per D047 / 04_MODEL_PROVIDER_DECISION.md: "If the primary model itself cannot
satisfy this contract on both predeclared providers: STOP. Do not silently
model-shop." Evidence files:
- reports/model_acceptance_gate_deepinfra_2026-09-05.json (eligible=False)
- reports/model_acceptance_gate_novita_2026-09-05.json (eligible=False)

No model/provider freeze was written. No 30-run scientific execution.

## Conclusion

Internal independent audit result: treatment construct + gates are ready for
external review, but MODEL/PROVIDER FREEZE FAILED — the acceptance gate
truthfully did not pass the primary model on either predeclared provider. The
30 scientific runs stay blocked.
```