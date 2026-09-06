# STAGE-C-HELDOUT-CHALLENGE-01 (D053) - PRE-BENCHMARK VALIDATION

## G1 Dataset Validation (scientific-stagec-heldout-01): PASS
- PASS todo-heldout-001 parses
- PASS todo-heldout-002 parses
- PASS todo-heldout-003 parses
- PASS todo-heldout-004 parses
- PASS todo-heldout-005 parses
- PASS todo-heldout-006 parses
- PASS todo-heldout-001 blast_radius localized
- PASS todo-heldout-002 blast_radius localized
- PASS todo-heldout-003 blast_radius moderate
- PASS todo-heldout-004 blast_radius localized
- PASS todo-heldout-005 blast_radius moderate
- PASS todo-heldout-006 blast_radius moderate
- PASS five-file universe exact (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py', 'todo/urls.py', 'todo/views.py'])
- PASS todo-heldout-001 architecture_constraints empty list ([])
- PASS todo-heldout-002 architecture_constraints empty list ([])
- PASS todo-heldout-003 architecture_constraints empty list ([])
- PASS todo-heldout-004 architecture_constraints empty list ([])
- PASS todo-heldout-005 architecture_constraints empty list ([])
- PASS todo-heldout-006 architecture_constraints empty list ([])
- PASS todo-heldout-001 visible text free of source-file names ([])
- PASS todo-heldout-002 visible text free of source-file names ([])
- PASS todo-heldout-003 visible text free of source-file names ([])
- PASS todo-heldout-004 visible text free of source-file names ([])
- PASS todo-heldout-005 visible text free of source-file names ([])
- PASS todo-heldout-006 visible text free of source-file names ([])
- PASS todo-heldout-001 gold non-empty
- PASS todo-heldout-001 gold subset of source universe
- PASS todo-heldout-001 normalized gold exact (['todo/models.py', 'todo/serializers.py'])
- PASS todo-heldout-002 gold non-empty
- PASS todo-heldout-002 gold subset of source universe
- PASS todo-heldout-002 normalized gold exact (['todo/views.py'])
- PASS todo-heldout-003 gold non-empty
- PASS todo-heldout-003 gold subset of source universe
- PASS todo-heldout-003 normalized gold exact (['todo/models.py', 'todo/serializers.py', 'todo/views.py'])
- PASS todo-heldout-004 gold non-empty
- PASS todo-heldout-004 gold subset of source universe
- PASS todo-heldout-004 normalized gold exact (['todo/models.py'])
- PASS todo-heldout-005 gold non-empty
- PASS todo-heldout-005 gold subset of source universe
- PASS todo-heldout-005 normalized gold exact (['todo/permissions.py', 'todo/views.py'])
- PASS todo-heldout-006 gold non-empty
- PASS todo-heldout-006 gold subset of source universe
- PASS todo-heldout-006 normalized gold exact (['todo/models.py', 'todo/permissions.py', 'todo/serializers.py'])

## G2 Prompt Validation (scientific-stagec-heldout-01): PASS
- PASS agent prompt has requirement before
- PASS agent prompt has requirement after
- PASS agent prompt has visible criteria
- PASS agent prompt has editable universe
- PASS agent prompt has no expected_actions
- PASS agent prompt has no gold sentinel
- PASS agent prompt has no evaluator name
- PASS agent prompt has no expected_actions
- PASS planner prompt has no expected_actions
- PASS agent prompt has no GOLD_SENTINEL
- PASS planner prompt has no GOLD_SENTINEL
- PASS agent prompt has no todo-heldout
- PASS planner prompt has no todo-heldout
- PASS agent prompt has no heldout
- PASS planner prompt has no heldout
- PASS planner prompt exercises candidate/evidence surface

## G3 Pipeline Smoke Test (scientific-stagec-heldout-01): PASS
- PASS selection-only AnalyzeImpact -> RunRecord(selection_study) -> RunRecordData persisted -> metrics computed (mock, 0 model calls)

## G4 Dry Run (scientific-stagec-heldout-01): PASS
- PASS 60/60 records (60)
- PASS 60 unique run IDs
- PASS 30 iterative_repository_agent (30)
- PASS 30 impact_plan (30)
- PASS 10/scenario ({'todo-heldout-001': 10, 'todo-heldout-002': 10, 'todo-heldout-003': 10, 'todo-heldout-004': 10, 'todo-heldout-005': 10, 'todo-heldout-006': 10})
- PASS reps 1..5 x 12 ({1: 12, 2: 12, 3: 12, 4: 12, 5: 12})
- PASS 0 model calls / 0 tokens
- PASS config profile frozen
- PASS protocol identity frozen
- PASS config_hash frozen
- PASS agent control cap frozen 1024

## G5 Integration Test (scientific-stagec-heldout-01): PASS
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

## G6 Metric Verification (scientific-stagec-heldout-01): PASS
- PASS synthetic precision/recall/F1/FNR/full-recall/write-set exact across 5 cases

## Gate summary
- G1 Dataset Validation (scientific-stagec-heldout-01): PASS
- G2 Prompt Validation (scientific-stagec-heldout-01): PASS
- G3 Pipeline Smoke Test (scientific-stagec-heldout-01): PASS
- G4 Dry Run (scientific-stagec-heldout-01): PASS
- G5 Integration Test (scientific-stagec-heldout-01): PASS
- G6 Metric Verification (scientific-stagec-heldout-01): PASS

STAGEC_HELDOUT_01_REAL_RUN_AUTHORIZED=
YES