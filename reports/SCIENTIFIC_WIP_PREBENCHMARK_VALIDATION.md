# SCIENTIFIC-WIP-IMPACTPLAN-V1 — PRE-BENCHMARK VALIDATION

## G1 Dataset Validation (scientific-wip-impactplan-v1): PASS
- PASS todo-smoke-001 parses
- PASS todo-smoke-002 parses
- PASS todo-smoke-003 parses
- PASS todo-smoke-001 blast_radius localized
- PASS todo-smoke-002 blast_radius moderate
- PASS todo-smoke-003 blast_radius cross_cutting
- PASS five-file universe exact (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py', 'todo/urls.py', 'todo/views.py'])
- PASS todo-smoke-001 evaluator sidecar exists
- PASS todo-smoke-001 evaluator SHA matches sidecar
- PASS todo-smoke-002 evaluator sidecar exists
- PASS todo-smoke-002 evaluator SHA matches sidecar
- PASS todo-smoke-003 evaluator sidecar exists
- PASS todo-smoke-003 evaluator SHA matches sidecar
- PASS planner prompt/source has no todo_smoke_001_checks
- PASS executor prompt/source has no todo_smoke_001_checks
- PASS planner prompt/source has no todo_smoke_002_checks
- PASS executor prompt/source has no todo_smoke_002_checks
- PASS planner prompt/source has no todo_smoke_003_checks
- PASS executor prompt/source has no todo_smoke_003_checks
- PASS test_todo_smoke_evaluator_assets.py (exit 0)

## G2 Prompt Validation (scientific-wip-impactplan-v1): PASS
- PASS prompt has visible acceptance
- PASS prompt has no gold sentinel
- PASS prompt has no evaluator name
- PASS planner prompt has no expected_actions
- PASS planner prompt has no gold sentinel

## G3 Pipeline Smoke Test (scientific-wip-impactplan-v1): PASS
- PASS ImpactPlan -> gate -> write_set plan -> executor -> write -> usage OK (stub, 0 model calls)

## G4 Dry Run (scientific-wip-impactplan-v1): PASS
- PASS 30/30 records (30)
- PASS 30 unique run IDs
- PASS 15 agent (15)
- PASS 15 impact_plan (15)
- PASS 10/scenario ({'todo-smoke-001': 10, 'todo-smoke-002': 10, 'todo-smoke-003': 10})
- PASS reps 1..5 x 6 ({1: 6, 2: 6, 3: 6, 4: 6, 5: 6})
- PASS 0 model calls / 0 tokens
- PASS config profile frozen
- PASS config_hash frozen

## G5 Integration Test (scientific-wip-impactplan-v1): PASS
- PASS tests/unit/selection/test_impact_plan_contract.py (exit 0)
- PASS tests/unit/selection/test_impact_evidence_and_planner.py (exit 0)
- PASS tests/unit/execution/test_impact_plan_runner.py (exit 0)
- PASS tests/unit/llm/test_llm_openrouter_provider_pin.py (exit 0)
- PASS tests/unit/test_scientific_identity.py (exit 0)
- PASS tests/unit/test_scientific_evidence_persistence.py (exit 0)
- PASS tests/unit/test_acceptance_gate_script.py (exit 0)
- PASS tests/integration/test_todo_smoke_evaluator_assets.py (exit 0)

## G6 Metric Verification (scientific-wip-impactplan-v1): PASS
- PASS regenerate count == 1
- PASS validate_only count == 1
- PASS preserve count == 3
- PASS all candidates counted exactly once (5)

## Gate summary
- G1 Dataset Validation (scientific-wip-impactplan-v1): PASS
- G2 Prompt Validation (scientific-wip-impactplan-v1): PASS
- G3 Pipeline Smoke Test (scientific-wip-impactplan-v1): PASS
- G4 Dry Run (scientific-wip-impactplan-v1): PASS
- G5 Integration Test (scientific-wip-impactplan-v1): PASS
- G6 Metric Verification (scientific-wip-impactplan-v1): PASS

## Microstudy real-run authorization
MICROSTUDY_REAL_RUN_AUTHORIZED=YES