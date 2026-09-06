# STAGE-C LATENCY DECOMPOSITION

Per study/arm selection-stage latency metrics. `call_equivalent_duration` is `total_selection_duration / total_model_calls` and is a per-run WORKLOAD label, NOT provider per-call latency.

## smoke / iterative_repository_agent
- n: 15
- total_selection_duration: 147.644000
- mean_run_duration: 9.842933
- median_run_duration: 10.281000
- p90_run_duration: 12.672000
- max_run_duration: 14.172000
- total_model_calls: 89
- total_tool_calls: 74
- total_tool_duration: 0.467000
- total_prompt_tokens: 95343
- total_completion_tokens: 3169
- total_tokens: 98512
- call_equivalent_duration: 1.658921
- top3_outlier_run_ids: todo-smoke-003_iterative_repository_agent_rep2_f13e6f59=14.172s; todo-smoke-003_iterative_repository_agent_rep4_b9cc5737=12.672s; todo-smoke-002_iterative_repository_agent_rep4_7a7fd294=12.469s

## smoke / impact_plan
- n: 15
- total_selection_duration: 252.094000
- mean_run_duration: 16.806267
- median_run_duration: 13.531000
- p90_run_duration: 24.438000
- max_run_duration: 43.750000
- total_model_calls: 15
- total_tool_calls: 0
- total_tool_duration: 0.000000
- total_prompt_tokens: 18800
- total_completion_tokens: 15284
- total_tokens: 34084
- call_equivalent_duration: 16.806267
- top3_outlier_run_ids: todo-smoke-003_impact_plan_rep5_c45d5c18=43.750s; todo-smoke-002_impact_plan_rep5_81ed8d80=24.438s; todo-smoke-003_impact_plan_rep3_14ebae7d=22.047s

## heldout / iterative_repository_agent
- n: 30
- total_selection_duration: 490.108000
- mean_run_duration: 16.336933
- median_run_duration: 8.211000
- p90_run_duration: 9.953000
- max_run_duration: 149.468000
- total_model_calls: 220
- total_tool_calls: 159
- total_tool_duration: 1.318000
- total_prompt_tokens: 203121
- total_completion_tokens: 7762
- total_tokens: 210883
- call_equivalent_duration: 2.227764
- top3_outlier_run_ids: todo-heldout-002_iterative_repository_agent_rep1_1e586b58=149.468s; todo-heldout-002_iterative_repository_agent_rep2_9dc9d2f6=111.406s; todo-heldout-001_iterative_repository_agent_rep1_9a26ad9b=10.406s

## heldout / impact_plan
- n: 30
- total_selection_duration: 236.162000
- mean_run_duration: 7.872067
- median_run_duration: 6.891000
- p90_run_duration: 8.906000
- max_run_duration: 26.235000
- total_model_calls: 30
- total_tool_calls: 0
- total_tool_duration: 0.000000
- total_prompt_tokens: 29870
- total_completion_tokens: 27101
- total_tokens: 56971
- call_equivalent_duration: 7.872067
- top3_outlier_run_ids: todo-heldout-001_impact_plan_rep4_4ed35922=26.235s; todo-heldout-001_impact_plan_rep5_79722919=25.765s; todo-heldout-002_impact_plan_rep3_28454ae0=10.359s

## Reporting rule

Always report BOTH the total-latency delta AND the median-run latency.
The held-out `-51.81%` total-latency delta is NOT a stable algorithmic 
speedup: two Agent held-out outliers materially affect the total.