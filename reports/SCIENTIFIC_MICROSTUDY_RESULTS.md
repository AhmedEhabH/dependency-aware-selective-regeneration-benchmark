# SCIENTIFIC-MICROSTUDY-01 Results (FAST-RESULTS-02 FINAL RUN)

- Experiment ID: exp-20260905-225518
- Source commit (pushed): `d6e27d7`  | config hash `828191860bff37c0`
- Model identity: `openrouter:qwen/qwen3-coder@DeepInfra` (frozen D050/PA-004, DeepInfra, no fallback)
- Profile: `scientific-wip-impactplan-v1` (Scenario-ImpactPlan protocol v1, `protocol_version` 1.0)
- Runs: 30/30 terminal (`exp-20260905-225518`); statuses Counter({'failed': 30})
- Failure classification: {'model_output': 30} (all `model_output`; 0 retryable)
- Functional validation reached: 0/30 (all runs failed pre-validation)
- Total real API tokens: prompt 371,825 + completion 186,301 = 558,126; model calls 337
- **TOTAL_SCIENTIFIC_API_COST_USD = 0.2978** (prompt $0.3/1M + completion $1.0/1M, DeepInfra list prices, no cache/fallback discount; acceptance gate 3/3 adds ~$0.0004)

## GO/NO-GO (frozen D043 / preregistration section 4: all 3 clear G1 AND G2 AND ≥2/3 clear G3)
- **todo-smoke-001**: G1=False G2=True G3=True
- **todo-smoke-002**: G1=False G2=True G3=True
- **todo-smoke-003**: G1=False G2=True G3=True

**DECISION = NO-GO** — G1 correctness not cleared in all 3 scenarios; study NO-GO

G1 = Selective ≥4/5 changed-requirement passes and Agent not worse by >1 rep; G2 = Selective ≥4/5 preservation; G3 = Selective impact recall 1.0 in ≥4/5.
Selective arm = `impact_plan` (ImpactPlanSelectiveStrategy); Agent arm = `iterative_repository_agent`; 5 reps per scenario×strategy.

**Interpretation caveat:** G2/G3 are *vacuously* satisfied. `changed_requirement_pass` (scenario_evaluator_passed) is 0/5 for both arms in every scenario, so G1 is NOT cleared anywhere. Zero runs reached functional validation (0/30), hence no edits were ever applied: preservation counts as clear because nothing was preserved-wrong, and impact recall on the *planned* (not executed) actions happened to be perfect for all 5 selective reps (predicted_any_action 15/15) even though the regenerated output never applied. The study is therefore NO-GO on the primary correctness gate alone.

Scenario-result machine output: {"todo-smoke-001": {"scenario_id": "todo-smoke-001", "G1": {"selective": false, "selective_ge_4_5": false, "agent_not_worse_by_more_than_1": true, "agent": false, "agent_passes": 0, "selective_passes": 0}, "G2": {"selective": true, "preservation_4_5": true, "preservation_pass_count": 5}, "G3": {"selective": true, "recall_4_5": true, "recall_full_count": 5}}, "todo-smoke-002": {"scenario_id": "todo-smoke-002", "G1": {"selective": false, "selective_ge_4_5": false, "agent_not_worse_by_more_than_1": true, "agent": false, "agent_passes": 0, "selective_passes": 0}, "G2": {"selective": true, "preservation_4_5": true, "preservation_pass_count": 5}, "G3": {"selective": true, "recall_4_5": true, "recall_full_count": 5}}, "todo-smoke-003": {"scenario_id": "todo-smoke-003", "G1": {"selective": false, "selective_ge_4_5": false, "agent_not_worse_by_more_than_1": true, "agent": false, "agent_passes": 0, "selective_passes": 0}, "G2": {"selective": true, "preservation_4_5": true, "preservation_pass_count": 5}, "G3": {"selective": true, "recall_4_5": true, "recall_full_count": 5}}}

## Per-arm aggregates

| arm | runs | succeeded | failed | predicted_any_action | mean_tokens | mean_calls | mean_duration_s (workflow) | sum_tokens | human_review | prohibited_writes |
|---|---|---|---|---|---|---|---|---|---|---|
| Agent | 15 | 0 | 15 | 15 | 10391.3 | 8.6 | 29.5 | 155869 | 0 esc / 0 unres | 0 |
| Selective | 15 | 0 | 15 | 15 | 26817.1 | 13.87 | 247.3 | 402257 | 0 esc / 0 unres | 0 |

## Dominant failure signatures (by strategy)

| strategy | failure message | count |
|---|---|---|
| impact_plan | Generation guard: no model calls or no generated source | 42 |
| impact_plan | Output rejected for todo/models.py: unbalanced_fence | 32 |
| impact_plan | Output rejected for todo/views.py: unbalanced_fence | 24 |
| impact_plan | ImpactPlan bounded expansion (v2) exhausted; escalating to HUMAN_REVIEW | 15 |
| iterative_repository_agent | iterative_agent: no remaining agent calls | 12 |
| impact_plan | Output rejected for todo/permissions.py: unbalanced_fence | 11 |
| impact_plan | Output rejected for todo/serializers.py: unbalanced_fence | 5 |
| impact_plan | repair_no_progress: repair reproduced the prior attempt output; stopping repair rounds | 5 |
| impact_plan | repair_no_progress: todo/serializers.py identical to previous attempt (response_sha256=0185dbb23518d | 4 |
| impact_plan | exact_patch_failed: todo/views.py: REPLACE block not terminated by a '>>>>>>> REPLACE' marker | 3 |
| impact_plan | exact_patch_failed: todo/models.py: SEARCH block is empty | 3 |
| iterative_repository_agent | Generation guard: no model calls or no generated source | 3 |
| iterative_repository_agent | iterative_agent: revision failed to select paths | 3 |
| impact_plan | exact_patch_failed: todo/models.py: trailing content after duplicate closing markers; expected only  | 2 |
| iterative_repository_agent | Output rejected for todo/models.py: unbalanced_fence | 2 |
| iterative_repository_agent | Output rejected for todo/views.py: unbalanced_fence | 2 |
| impact_plan | repair_no_progress: todo/serializers.py identical to previous attempt (response_sha256=aabfebf379ecb | 1 |
| impact_plan | exact_patch_failed: todo/views.py: SEARCH block is empty | 1 |
| impact_plan | exact_patch_failed: todo/serializers.py: REPLACE block not terminated by a '>>>>>>> REPLACE' marker | 1 |
| impact_plan | artifact_contract_violation: todo/views.py: undeclared_dependency: django_filters; response_sha256=a | 1 |
| impact_plan | exact_patch_failed: todo/models.py: expected '<<<<<<< SEARCH' block start, found: 'Please note that  | 1 |
| impact_plan | exact_patch_failed: todo/models.py: expected '<<<<<<< SEARCH' block start, found: '### todo/models.p | 1 |
| impact_plan | exact_patch_failed: todo/views.py: trailing content after duplicate closing markers; expected only ' | 1 |
| impact_plan | exact_patch_failed: todo/serializers.py: trailing content after duplicate closing markers; expected  | 1 |
| iterative_repository_agent | artifact_contract_violation: todo/views.py: undeclared_dependency: django_filters; response_sha256=e | 1 |
| iterative_repository_agent | exact_patch_failed: todo/models.py: SEARCH block not terminated by a '=======' divider | 1 |
| iterative_repository_agent | Output rejected for todo/permissions.py: unbalanced_fence | 1 |

## Per-run detail
`reports/SCIENTIFIC_MICROSTUDY_RESULTS.csv` (all 30 rows) and raw evidence under `reports/scientific_microstudy/` (run_records.jsonl, failure_records.json, benchmark_summary.json, source_identity.json).
