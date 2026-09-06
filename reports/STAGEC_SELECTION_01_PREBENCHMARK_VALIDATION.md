# STAGE-C-SELECTION-01 (D052) - PRE-BENCHMARK VALIDATION

## G1 Dataset Validation (scientific-stagec-selection-01): PASS
- PASS todo-smoke-001 parses
- PASS todo-smoke-002 parses
- PASS todo-smoke-003 parses
- PASS todo-smoke-001 blast_radius localized
- PASS todo-smoke-002 blast_radius moderate
- PASS todo-smoke-003 blast_radius cross_cutting
- PASS five-file universe exact (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py', 'todo/urls.py', 'todo/views.py'])
- PASS todo-smoke-001 gold subset of source universe
- PASS todo-smoke-001 normalized gold exact (['todo/models.py', 'todo/serializers.py', 'todo/views.py'])
- PASS todo-smoke-002 gold subset of source universe
- PASS todo-smoke-002 normalized gold exact (['todo/models.py', 'todo/views.py'])
- PASS todo-smoke-003 gold subset of source universe
- PASS todo-smoke-003 normalized gold exact (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py', 'todo/views.py'])
- PASS todo-smoke-001 evaluator asset exists
- PASS todo-smoke-002 evaluator asset exists
- PASS todo-smoke-003 evaluator asset exists

## G2 Prompt Validation (scientific-stagec-selection-01): PASS
- PASS agent prompt has requirement before
- PASS agent prompt has requirement after
- PASS agent prompt has visible criteria
- PASS agent prompt has editable universe
- PASS agent prompt has no expected_actions
- PASS agent prompt has no gold sentinel
- PASS agent prompt has no evaluator name
- PASS planner prompt has no expected_actions
- PASS planner prompt has no gold sentinel
- PASS planner prompt has no evaluator name
- PASS planner prompt exercises candidate/evidence surface

## G3 Pipeline Smoke Test (scientific-stagec-selection-01): PASS
- PASS selection-only AnalyzeImpact -> RunRecord(selection_study) -> RunRecordData persisted -> metrics computed (mock, 0 model calls)

## G4 Dry Run (scientific-stagec-selection-01): PASS
- PASS 30/30 records (30)
- PASS 30 unique run IDs
- PASS 15 iterative_repository_agent (15)
- PASS 15 impact_plan (15)
- PASS 10/scenario ({'todo-smoke-001': 10, 'todo-smoke-002': 10, 'todo-smoke-003': 10})
- PASS reps 1..5 x 6 ({1: 6, 2: 6, 3: 6, 4: 6, 5: 6})
- PASS 0 model calls / 0 tokens
- PASS config profile frozen
- PASS protocol identity frozen
- PASS config_hash frozen
- PASS agent control cap frozen 1024

## G5 Integration Test (scientific-stagec-selection-01): PASS
- PASS iterative_repository_agent real NON-STUDY probe exit 0
- PASS iterative_repository_agent produced exactly 1 probe record
- PASS iterative_repository_agent probe terminal valid selection
- PASS iterative_repository_agent INITIAL prediction captured
- PASS iterative_repository_agent regenerate-source set captured
- PASS iterative_repository_agent probe consumed tokens
- PASS impact_plan real NON-STUDY probe exit 0
- PASS impact_plan produced exactly 1 probe record
- PASS impact_plan probe terminal valid selection
- PASS impact_plan INITIAL prediction captured
- PASS impact_plan regenerate-source set captured
- PASS impact_plan probe consumed tokens

## G6 Metric Verification (scientific-stagec-selection-01): PASS
- PASS synthetic precision/recall/F1/FNR/full-recall/write-set exact across 5 cases

## Gate summary
- G1 Dataset Validation (scientific-stagec-selection-01): PASS
- G2 Prompt Validation (scientific-stagec-selection-01): PASS
- G3 Pipeline Smoke Test (scientific-stagec-selection-01): PASS
- G4 Dry Run (scientific-stagec-selection-01): PASS
- G5 Integration Test (scientific-stagec-selection-01): PASS
- G6 Metric Verification (scientific-stagec-selection-01): PASS

STAGEC_SELECTION_01_REAL_RUN_AUTHORIZED=
YES