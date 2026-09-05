# SCIENTIFIC MICRO-STUDY 01 — PRE-BENCHMARK VALIDATION

## G1 Dataset Validation: PASS
- PASS todo-smoke-001 parses; id matches
- PASS todo-smoke-002 parses; id matches
- PASS todo-smoke-003 parses; id matches
- PASS todo-smoke-001 blast_radius == localized
- PASS todo-smoke-002 blast_radius == moderate
- PASS todo-smoke-003 blast_radius == cross_cutting
- PASS todo-smoke-001 evaluator sidecar exists
- PASS todo-smoke-001 evaluator SHA matches sidecar
- PASS todo-smoke-002 evaluator sidecar exists
- PASS todo-smoke-002 evaluator SHA matches sidecar
- PASS todo-smoke-003 evaluator sidecar exists
- PASS todo-smoke-003 evaluator SHA matches sidecar
- PASS test_todo_smoke_evaluator_assets.py passes (exit 0)
- PASS todo-smoke-001: 10 evaluator check names present; 0 names without a direct visible keyword (traced via requirement/constraint/gold)
- PASS todo-smoke-002: 9 evaluator check names present; 0 names without a direct visible keyword (traced via requirement/constraint/gold)
- PASS todo-smoke-003: 10 evaluator check names present; 0 names without a direct visible keyword (traced via requirement/constraint/gold)
- PASS no hidden feature contradiction identified in static evaluator scan
- PASS no strategy-visible prompt leaks evaluator_asset marker
- PASS no strategy-visible prompt leaks expected_actions marker
- PASS no strategy-visible prompt leaks scoring_script marker
- PASS no strategy-visible prompt leaks frozen_results marker
- PASS todo llm_editable == frozen five-file universe (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py', 'todo/urls.py', 'todo/views.py'])
- PASS todo dependency graph = 5-node/6-edge production graph ([('todo/permissions.py', 'todo/models.py'), ('todo/serializers.py', 'todo/models.py'), ('todo/urls.py', 'todo/views.py'), ('todo/views.py', 'todo/models.py'), ('todo/views.py', 'todo/permissions.py'), ('todo/views.py', 'todo/serializers.py')])
- PASS all scenarios repository == todo (['todo'])

## G2 Prompt Validation: PASS
- PASS prompt contains visible acceptance criterion
- PASS prompt lacks gold sentinel label
- PASS prompt lacks evaluator name
- PASS plan-derived expected action appears

## G3 Pipeline Smoke Test: PASS
- PASS throwaway synthetic pipeline smoke: backend->provider pin->exact patch->write->usage OK

## G4 Dry Run: PASS
- PASS 30/30 records persisted (30)
- PASS 30 unique run IDs
- PASS 30 records all todo-smoke scenarios
- PASS 15 iterative_repository_agent
- PASS 15 selective
- PASS scenario counts == 10 each ({'todo-smoke-001': 10, 'todo-smoke-002': 10, 'todo-smoke-003': 10})
- PASS reps 1..5 each 6 times ({1: 6, 2: 6, 3: 6, 4: 6, 5: 6})
- PASS 0 real tokens / 0 model calls
- PASS config identity frozen (config_hash present)
- PASS deterministic execution-plan hash computed

## G5 Integration Test: PASS
- PASS tests/unit/llm/test_llm_openrouter_provider_pin.py passes (exit 0)
- PASS tests/unit/test_scientific_identity.py passes (exit 0)
- PASS tests/unit/execution/test_scientific_gold_leakage.py passes (exit 0)
- PASS tests/unit/test_scientific_evidence_persistence.py passes (exit 0)
- PASS tests/unit/test_acceptance_gate_script.py passes (exit 0)
- PASS tests/unit/test_scientific_microstudy_plan.py passes (exit 0)
- PASS tests/integration/test_todo_smoke_evaluator_assets.py passes (exit 0)

## G6 Metric Verification: PASS
- PASS metric/go-no-go logic tests pass (exit 0)

## Gate summary
- G1 Dataset Validation: PASS
- G2 Prompt Validation: PASS
- G3 Pipeline Smoke Test: PASS
- G4 Dry Run: PASS
- G5 Integration Test: PASS
- G6 Metric Verification: PASS

## Microstudy real-run authorization
MICROSTUDY_REAL_RUN_AUTHORIZED=YES