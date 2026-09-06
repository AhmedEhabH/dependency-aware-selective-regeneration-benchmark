# V1.1 ROOT-CAUSE TAXONOMY

Deterministic classification of the historical v1.1 evidence (`reports/scientific_microstudy_v11/run_records.jsonl`, immutable).
Each run receives exactly ONE `first_failure_class` (earliest causal failure).

## Overall first-failure distribution

| Class | Label | Count |
|---|---|---|
| A | selection_control | 1 |
| B | generation_structured_output | 0 |
| C | exact_patch_application | 10 |
| D | syntax_static_validation | 8 |
| E | migration_runtime | 4 |
| F | functional_evaluator | 7 |
| G | repair_expansion_exhaustion | 0 |
| H | timeout_provider_transport | 0 |
| I | other | 0 |
| **TOTAL** | | **30** |

## By arm

| Arm | A | B | C | D | E | F | G | H | I | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| impact_plan | 1 | 0 | 5 | 4 | 1 | 4 | 0 | 0 | 0 | 15 |
| iterative_repository_agent | 0 | 0 | 5 | 4 | 3 | 3 | 0 | 0 | 0 | 15 |

## By scenario

| Scenario | A | B | C | D | E | F | G | H | I | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| todo-smoke-001 | 0 | 0 | 3 | 7 | 0 | 0 | 0 | 0 | 0 | 10 |
| todo-smoke-002 | 1 | 0 | 2 | 0 | 0 | 7 | 0 | 0 | 0 | 10 |
| todo-smoke-003 | 0 | 0 | 5 | 1 | 4 | 0 | 0 | 0 | 0 | 10 |

## Representative evidence examples

- **D** `iterative_repository_agent` `todo-smoke-001` `ep1_d9fb5715` (stage=regeneration): artifact_contract_violation: todo/models.py: python_syntax_error: line=34 offset=5 msg=expected an indented block after class definition on line 33; response_sha256=c314ec89b7007dd14e1e0a7649d600b2...
- **C** `iterative_repository_agent` `todo-smoke-001` `ep2_a72ee0cf` (stage=regeneration): exact_patch_failed: todo/serializers.py: block 2: SEARCH content is ambiguous, matched 3 times; search='fields = ['
- **D** `iterative_repository_agent` `todo-smoke-001` `ep3_cda87f13` (stage=regeneration): artifact_contract_violation: todo/models.py: python_syntax_error: line=34 offset=5 msg=expected an indented block after class definition on line 33; response_sha256=097d339d4726e93fc57e53f9e6f6ebb4...
- **D** `iterative_repository_agent` `todo-smoke-001` `ep4_7b67bd25` (stage=regeneration): artifact_contract_violation: todo/models.py: python_syntax_error: line=34 offset=5 msg=expected an indented block after class definition on line 33; response_sha256=097d339d4726e93fc57e53f9e6f6ebb4...
- **D** `iterative_repository_agent` `todo-smoke-001` `ep5_d53177c5` (stage=regeneration): artifact_contract_violation: todo/models.py: python_syntax_error: line=34 offset=5 msg=expected an indented block after class definition on line 33; response_sha256=124aa52c85e78e40dc05765f90cce14b...
- **C** `impact_plan` `todo-smoke-001` `ep1_0b0c1df0` (stage=regeneration): exact_patch_failed: todo/models.py: block 2: SEARCH content not found in current file (count=0); search='status = models.CharField(max_length=20, choices=Status.choices, default=Status.'
- **C** `impact_plan` `todo-smoke-001` `ep2_470072be` (stage=regeneration): exact_patch_failed: todo/models.py: block 2: SEARCH content not found in current file (count=0); search='status = models.CharField(max_length=20, choices=Status.choices, default=Status.'
- **F** `iterative_repository_agent` `todo-smoke-002` `ep1_c608e09e` (stage=scenario_evaluator): Scenario evaluator failed; checks: soft_delete_retains_row, soft_delete_sets_timestamp, default_manager_excludes_deleted, normal_list_excludes_deleted, deleted_detail_is_404; error: deleted_action_...
- **C** `iterative_repository_agent` `todo-smoke-002` `ep2_6f1678fe` (stage=regeneration): exact_patch_failed: todo/models.py: block 2: SEARCH content is ambiguous, matched 3 times; search='    def __str__(self):'
- **F** `iterative_repository_agent` `todo-smoke-002` `ep3_3700cc24` (stage=scenario_evaluator): Scenario evaluator failed; checks: soft_delete_retains_row, soft_delete_sets_timestamp, default_manager_excludes_deleted, normal_list_excludes_deleted, deleted_detail_is_404; error: deleted_action_...
- **F** `iterative_repository_agent` `todo-smoke-002` `ep5_61e674ac` (stage=scenario_evaluator): Scenario evaluator failed; checks: soft_delete_retains_row, soft_delete_sets_timestamp, default_manager_excludes_deleted, normal_list_excludes_deleted, deleted_detail_is_404; error: deleted_action_...
- **F** `impact_plan` `todo-smoke-002` `ep1_81420272` (stage=scenario_evaluator): Scenario evaluator failed before escalation
- **A** `impact_plan` `todo-smoke-002` `ep5_7d4747ea` (stage=analyze_impact): impact_plan_planner_error: planner response not JSON (finish_reason=error): Unterminated string starting at: line 106 column 25 (char 3721)
- **E** `iterative_repository_agent` `todo-smoke-003` `ep1_9aed4cbd` (stage=migration_generation): Migration failed: exit=3; stdout: Field 'owner' on model 'project' not migrated: it is impossible to add a non-nullable field without specifying a default. ; stderr:  [post-generation validation] e...
- **E** `iterative_repository_agent` `todo-smoke-003` `ep2_a98d1b90` (stage=migration_generation): Migration failed: exit=3; stdout: Field 'owner' on model 'project' not migrated: it is impossible to add a non-nullable field without specifying a default. ; stderr:  [post-generation validation] e...
- **E** `iterative_repository_agent` `todo-smoke-003` `ep4_94912c4b` (stage=migration_generation): Migration failed: exit=3; stdout: Field 'owner' on model 'project' not migrated: it is impossible to add a non-nullable field without specifying a default. ; stderr:  [post-generation validation] e...
- **E** `impact_plan` `todo-smoke-003` `ep5_36e3f3e8` (stage=migration_generation): Migration failed before escalation

## Interpretation

The v1.1 NO-GO was dominated by downstream exact-patch and 
source-validity failures (C+D), with additional migration/evaluator 
failures (E+F). This does NOT attribute the 0/30 outcome to the 
impact selector (A).