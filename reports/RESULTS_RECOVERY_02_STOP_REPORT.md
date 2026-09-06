# RESULTS-RECOVERY-02 — REQUIRED STOP REPORT

## 1. Execution identity
- OpenCode implementation model: `openrouter/deepseek/deepseek-v4-flash-0731`
- branch: `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
- HEAD: `31acfee91c2fa696baa0922a08c073e988a51c60`
- origin HEAD: `31acfee91c2fa696baa0922a08c073e988a51c60` (HEAD == upstream)
- tree state: tracked tree clean; only user-owned untracked files preserved
  (`GIT_STATE.txt`, `reports/dryrun_scientific_microstudy/`,
  `reports/dryrun_wip_impactplan/`, `uv.lock`) — untouched.

## 2. Documentation freeze
- decision ID: D051 (pre-existing, frozen before model calls)
- assumption ID: A032 (frozen before model calls)
- protocol version: `scientific-wip-impactplan-v1.1`
- output-budget doc: `docs/LLM_OUTPUT_BUDGET_AND_PRODUCTION_SIZING.md`
- freeze commits already pushed before the first real model call:
  `565d11c` (v1.1 interface freeze), `fa16410`, `da09cf5`, `5acf0e3`
- this execution pushed: `5d2accd`, `4c9c410`, `6deece8`, `c0bf91b`,
  `28a00e9`, `75364ee`, `5aab1fa`, `c0b56eb`, `31acfee`

## 3. Exact production-code changes
- `scripts/run_model_acceptance_gate.py`
  - `run_schema_capability_probe`: awaited the async `generate_structured`
    via `asyncio.run` (was returning a coroutine -> AttributeError). Added
    `LLMResponse` import; nested `token_usage` fields. Reason: real runtime
    defect blocking the capability probe. Deps: OpenRouter backend.
- `src/benchmark/strategies/iterative_agent.py`
  - `AGENT_FINAL_SCHEMA`: removed `uniqueItems` keyword. Reason: DeepInfra's
    strict JSON-schema grammar rejects it (`Unimplemented keys:
    ["uniqueItems"]`), failing every `agent_final` call. Uniqueness of
    `selected_paths` is already enforced deterministically in the control
    loop (`_is_repeated_tool_request` / duplicate check); no semantic
    guarantee lost. Deps: agent control, acceptance gate, results builder.
- `scripts/build_todo_microstudy_results.py`
  - `functional_validation_reached` / `functional_validation_passed` /
    `agent_finalized_within_8` / summary counts / qualified-run filter now
    derive from `scenario_evaluator_passed` (the deterministic functional
    check of the change) instead of the legacy baseline-mirror
    `functional_validation_passed`. Reason: the summary claimed 5/30
    "functional validation passed" while the scenario evaluator passed
    0/30; the report must be truthful. Deps: run records, results CSV/MD.

## 4. Output budgets
- AGENT_CONTROL_MAX=1024
- IMPACT_PLAN_MAX=4096
- PATCH_MAX=8192
- REPAIR_MAX=8192
- `finish_reason=length` observed: **0** (across 335 model calls)

## 5. Provider/model freeze
- model: `qwen/qwen3-coder`
- provider: `DeepInfra` (via existing OpenRouter account)
- fallback: OFF (`allow_fallbacks=false`, `require_parameters=true`)
- structured-output capability result: PASS (native JSON-schema `{ok:true}`
  probe passed; NovitaAI never needed)
- exact settings: temperature 0.0, mode direct/non-thinking, call timeout
  120 s, workflow timeout 900 s, max attempts 3, transient retry max=1
  (429/5xx/transport only; 4xx never retried)
- freeze file: `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json` (pricing
  prompt $0.30/M, completion $1/M, fp4 turbo)

## 6. Focused tests
- Focused implementation set (handoff): 197 passed, 4 skipped
- Checkpoint/result focused set (handoff): 138 passed
- Additional focused regression (handoff): 109 passed
- Re-run during execution: `test_agent_control_cap.py` +
  `test_acceptance_gate_script.py` = 30 passed; `test_scientific_microstudy_metrics.py`
  + `test_acceptance_gate_script.py` = 38 passed; ruff/mypy/py_compile clean
  on changed files.

## 7. Two-arm real acceptance
Agent:
- calls: 3 (2 tool + 1 final); finalized within 8: YES
- patch valid: YES (structured PatchEnvelope parsed + applied)
- functional validation reached: YES; passed: YES
- 0 truncations

ImpactPlan:
- plan valid: YES (native JSON-schema ImpactPlan)
- provenance persisted: YES (impact_plan_hash/version, planner calls/tokens)
- patch valid: YES
- functional validation reached: YES; passed: YES
- 0 truncations
- gate `eligible=True`; freeze written

## 8. Pre-Benchmark Validation (exactly six gates)
- G1 Dataset Validation: PASS
- G2 Prompt Validation: PASS
- G3 Pipeline Smoke Test: PASS
- G4 Dry Run: PASS (30/30 records, 0 calls/tokens, profile/protocol frozen)
- G5 Integration Test: PASS (11 suites)
- G6 Metric Verification: PASS
- Evidence: `reports/SCIENTIFIC_WIP_PREBENCHMARK_VALIDATION.md`
  `MICROSTUDY_REAL_RUN_AUTHORIZED=YES`

## 9. Independent Audit
- gold leakage: PASS
- context/action separation: PASS
- write guard: PASS (0 prohibited writes in study)
- bounded expansion: PASS (exactly one v1->v2 per impact-plan run then H)
- repair provenance: PASS
- cap freeze: PASS (0 truncations; no cap raised)
- provider pin: PASS
- historical-run preservation: PASS (hash matched at handoff and at stop)
- over-engineering check: PASS
- Audit file: `reports/SCIENTIFIC_WIP_V11_AUDIT.md`

## 10. Full suite
- Run exactly once on corrected code: **2825 passed / 33 skipped / 0 failed**

## 11. v1.1 scientific results
- experiment ID: `exp-20260906-v11`
- 30 attempted: YES (30/30, 15 agent + 15 impact_plan, 10/scenario, reps 1-5)
- functional validation reached: 5/30
- Agent finalization within 8 calls: 1/15
- action metrics: impact_recall_full 14/30; action_f1 > 0 in 14/30;
  class support reported per row
- functional correctness (scenario evaluator passed): 0/30
- preservation: preservation_pass 30/30; unintended preserve changes 0
- truncations: 0
- expansion/H: 14/15 impact-plan runs expanded once then escalated to
  HUMAN_REVIEW
- planner usage: 64225 planner tokens (included in Selective totals)
- prohibited writes: 0
- API cost: $0.1789 (350125 prompt + 73846 completion tokens, 335 calls)
- qualified efficiency: agent 1 qualified run 14865 tokens/14 calls/53.5 s;
  impact_plan 4 qualified runs mean 12122.5 tokens/7 calls/101.3 s
- GO/NO-GO: **NO-GO** (G1 correctness not cleared in any scenario;
  G2/G3 clear per scenario)

## 12. GitHub / tag / export
- commits: `5d2accd`, `4c9c410`, `6deece8`, `c0bf91b`, `28a00e9`,
  `75364ee`, `5aab1fa`, `c0b56eb`, `31acfee`
- push verification: HEAD == upstream == `31acfee...` at every checkpoint
  and at stop
- tag: `wip-impactplan-v1.1-evidence` (annotated, created at HEAD,
  pushed; local peel == remote peel `31acfee...` == HEAD; NOT a release tag)
- light ZIP: `project-2026-09-06-1911.zip`
  - path: `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project-2026-09-06-1911.zip`
  - size: 2086358 bytes
  - SHA-256: `ea31ae5701a2d270d91f475cf5499e0104bf1ef55eb546f335b17a2e592dec81`
  - verified: contains GIT_STATE.txt; no `.git/`, no `dist/`, no dry-run bulk

## Mandatory final lines
PROTOCOL=scientific-wip-impactplan-v1.1
SCIENTIFIC_MODEL=qwen/qwen3-coder
SCIENTIFIC_PROVIDER=DeepInfra
AGENT_CONTROL_MAX=1024
IMPACT_PLAN_MAX=4096
PATCH_MAX=8192
REPAIR_MAX=8192
HISTORICAL_0_30_PRESERVED=YES
STRUCTURED_PATCH=PASS
AGENT_FORCED_FINAL=PASS
IMPACTPLAN_PROVENANCE_PERSISTED=PASS
TWO_ARM_REAL_ACCEPTANCE=PASS
DATASET_VALIDATION=PASS
PROMPT_VALIDATION=PASS
PIPELINE_SMOKE=PASS
DRY_RUN=PASS
INTEGRATION_TEST=PASS
METRIC_VERIFICATION=PASS
AUDIT=PASS
V11_RUNS_ATTEMPTED=30/30
V11_FUNCTIONAL_VALIDATION_REACHED=5/30
V11_TOTAL_API_COST_USD=0.1789
GO_NO_GO=NO-GO
RESULTS_PUSHED_TO_GITHUB=YES
EVIDENCE_TAG=wip-impactplan-v1.1-evidence
NEXT_ACTION=STOP after results