# RealCommitImpactDataset-v1 (M4A-1) — Six Pre-Benchmark Validation Gates

**Generated:** 2026-09-13T16:17:12.821096+00:00
**Minery version:** real-commit-miner-v1.0.0

| # | Gate | Result | Checks |
|---|---|---|---|
| 1 | Dataset Validation | PASS | 46 |
| 2 | Prompt Validation | PASS | 15 |
| 3 | Pipeline Smoke Test | PASS | 3 |
| 4 | Dry Run | PASS | 14 |
| 5 | Integration Test | PASS | 10 |
| 6 | Metric Verification | PASS | 5 |

## Gate 1 — Dataset Validation: PASS

- [PASS] dataset_manifest_exists — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev_manifest.json`
- [PASS] dev_case_count_between_4_and_6 — `6`
- [PASS] anchor_sha_matches_manifest — `{'manifest': '0f633fc9fa213357f4202482aab2b0edad680f95', 'expected': '0f633fc9fa213357f4202482aab2b0edad680f95'}`
- [PASS] repository_url_matches_manifest — `https://github.com/django-cms/django-cms`
- [PASS] target_commit_verified_djangocms-rc-47040a2887ca — `47040a2887ca3cab21a21f3e0fab758221be3d7c`
- [PASS] parent_relation_verified_djangocms-rc-47040a2887ca — `{'parents': ('8f9ed64184d2303cc9f8c252a53d7e3675d14814',), 'expected': ('8f9ed64184d2303cc9f8c252a53d7e3675d14814',)}`
- [PASS] universe_hash_verified_djangocms-rc-47040a2887ca — `{'recomputed': '6dcadd21b2e5dc514eb19e691a868e690c6e749085f914cd11dcfe098906ae7d', 'recorded': '6dcadd21b2e5dc514eb19e691a868e690c6e749085f914cd11dcfe098906ae7d'}`
- [PASS] graph_hash_verified_djangocms-rc-47040a2887ca — `{'recomputed': 'e02be95043eda334ad269f9dbd4819af61d050444e2b0fb7320e3352d1cea6c4', 'recorded': 'e02be95043eda334ad269f9dbd4819af61d050444e2b0fb7320e3352d1cea6c4'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-47040a2887ca — `['cms/models/placeholdermodel.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-47040a2887ca — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-47040a2887ca — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`
- [PASS] target_commit_verified_djangocms-rc-e008ff4b5c21 — `e008ff4b5c21f376e42896692a78a84e3d6c023c`
- [PASS] parent_relation_verified_djangocms-rc-e008ff4b5c21 — `{'parents': ('8d50660e7bcf8e480b32f36b4fb409c09f8b3fcd',), 'expected': ('8d50660e7bcf8e480b32f36b4fb409c09f8b3fcd',)}`
- [PASS] universe_hash_verified_djangocms-rc-e008ff4b5c21 — `{'recomputed': '2bed02d3eb0d6cbbffa0890fbda34e48f9437073f3da9d5e46e2ab7819f90cf3', 'recorded': '2bed02d3eb0d6cbbffa0890fbda34e48f9437073f3da9d5e46e2ab7819f90cf3'}`
- [PASS] graph_hash_verified_djangocms-rc-e008ff4b5c21 — `{'recomputed': '8ef4456257464c47e08340b222875828cbd28097d4b41f5b1f6d641acc726d8f', 'recorded': '8ef4456257464c47e08340b222875828cbd28097d4b41f5b1f6d641acc726d8f'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-e008ff4b5c21 — `['cms/plugin_base.py', 'cms/plugin_pool.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-e008ff4b5c21 — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-e008ff4b5c21 — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`
- [PASS] target_commit_verified_djangocms-rc-c30efd44e92e — `c30efd44e92eb24141bf5aa5f4c8e0a3fb590870`
- [PASS] parent_relation_verified_djangocms-rc-c30efd44e92e — `{'parents': ('888ee6eeef91ba094e5dfd6cf4a04332969d9952',), 'expected': ('888ee6eeef91ba094e5dfd6cf4a04332969d9952',)}`
- [PASS] universe_hash_verified_djangocms-rc-c30efd44e92e — `{'recomputed': 'b649efd8b692a45193395fa8b0b09958ea0bcd136a75aebf34db82637d74da4a', 'recorded': 'b649efd8b692a45193395fa8b0b09958ea0bcd136a75aebf34db82637d74da4a'}`
- [PASS] graph_hash_verified_djangocms-rc-c30efd44e92e — `{'recomputed': '193941c43e4f142d7b16c9e50fbb8706056847d73dfae21aaa75c4a654f96c84', 'recorded': '193941c43e4f142d7b16c9e50fbb8706056847d73dfae21aaa75c4a654f96c84'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-c30efd44e92e — `['cms/utils/decorators.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-c30efd44e92e — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-c30efd44e92e — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`
- [PASS] target_commit_verified_djangocms-rc-fd608e896daf — `fd608e896daf9c56a3f2202133c823efbace4603`
- [PASS] parent_relation_verified_djangocms-rc-fd608e896daf — `{'parents': ('23824547e0641b7bb03b334a8d825252c937758c',), 'expected': ('23824547e0641b7bb03b334a8d825252c937758c',)}`
- [PASS] universe_hash_verified_djangocms-rc-fd608e896daf — `{'recomputed': '0818094619172e62e0af9b23e25ed547bd898d4cfb7184cd79a2e3eb2b4fab5f', 'recorded': '0818094619172e62e0af9b23e25ed547bd898d4cfb7184cd79a2e3eb2b4fab5f'}`
- [PASS] graph_hash_verified_djangocms-rc-fd608e896daf — `{'recomputed': '9c1f10996c6c203d359df0485a860b72cbdc1c0cac6a35dc17b7f3dbca51161a', 'recorded': '9c1f10996c6c203d359df0485a860b72cbdc1c0cac6a35dc17b7f3dbca51161a'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-fd608e896daf — `['cms/views.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-fd608e896daf — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-fd608e896daf — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`
- [PASS] target_commit_verified_djangocms-rc-110d4c740927 — `110d4c74092768ee3e58f44b5a44f767b4c15fe5`
- [PASS] parent_relation_verified_djangocms-rc-110d4c740927 — `{'parents': ('50c3576080be08a4b7672bbd7bdfea4f97cc1621',), 'expected': ('50c3576080be08a4b7672bbd7bdfea4f97cc1621',)}`
- [PASS] universe_hash_verified_djangocms-rc-110d4c740927 — `{'recomputed': 'e0ca73df948151e3121e98870c481809c4677591f0fbc808fad0e9fd414cffd7', 'recorded': 'e0ca73df948151e3121e98870c481809c4677591f0fbc808fad0e9fd414cffd7'}`
- [PASS] graph_hash_verified_djangocms-rc-110d4c740927 — `{'recomputed': 'f6b381ea2bc9a6723543e8a4e2909c147571f35252e88bc662d7a3eaaa709cde', 'recorded': 'f6b381ea2bc9a6723543e8a4e2909c147571f35252e88bc662d7a3eaaa709cde'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-110d4c740927 — `['cms/admin/placeholderadmin.py', 'cms/toolbar/utils.py', 'cms/views.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-110d4c740927 — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-110d4c740927 — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`
- [PASS] target_commit_verified_djangocms-rc-888ee6eeef91 — `888ee6eeef91ba094e5dfd6cf4a04332969d9952`
- [PASS] parent_relation_verified_djangocms-rc-888ee6eeef91 — `{'parents': ('ada585d3f3580691f7c14c7bf0115f55cdca87f2',), 'expected': ('ada585d3f3580691f7c14c7bf0115f55cdca87f2',)}`
- [PASS] universe_hash_verified_djangocms-rc-888ee6eeef91 — `{'recomputed': '59ff57dea7017f1ac67fb8eec7924f5fc85ee9f0e7d816a011fbb27eeea28760', 'recorded': '59ff57dea7017f1ac67fb8eec7924f5fc85ee9f0e7d816a011fbb27eeea28760'}`
- [PASS] graph_hash_verified_djangocms-rc-888ee6eeef91 — `{'recomputed': 'c250396911e8aaf4a965b130a2e4e0cdbc9609f2383a243ce70eb192895f2fc1', 'recorded': 'c250396911e8aaf4a965b130a2e4e0cdbc9609f2383a243ce70eb192895f2fc1'}`
- [PASS] proxy_paths_valid_repo_relative_djangocms-rc-888ee6eeef91 — `['cms/models/pluginmodel.py', 'cms/plugin_base.py', 'cms/toolbar/utils.py', 'cms/utils/plugins.py']`
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-888ee6eeef91 — `[]`
- [PASS] split_is_miner_dev_djangocms-rc-888ee6eeef91 — `{'split': 'MINER_DEV', 'role': 'MINER_DEVELOPMENT'}`

## Gate 2 — Prompt Validation: PASS

- [PASS] public_bundle_hidden_free_djangocms-rc-47040a2887ca — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=385'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-47040a2887ca — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-47040a2887ca\public\intent.json`
- [PASS] public_bundle_hidden_free_djangocms-rc-e008ff4b5c21 — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=407'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-e008ff4b5c21 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-e008ff4b5c21\public\intent.json`
- [PASS] public_bundle_hidden_free_djangocms-rc-c30efd44e92e — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=371'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-c30efd44e92e — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-c30efd44e92e\public\intent.json`
- [PASS] public_bundle_hidden_free_djangocms-rc-fd608e896daf — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=349'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-fd608e896daf — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-fd608e896daf\public\intent.json`
- [PASS] public_bundle_hidden_free_djangocms-rc-110d4c740927 — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=467'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-110d4c740927 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-110d4c740927\public\intent.json`
- [PASS] public_bundle_hidden_free_djangocms-rc-888ee6eeef91 — `[{'check': 'no_proxy_filename_in_public', 'ok': True, 'detail': 'observed_change_set_proxy.json'}, {'check': 'no_hidden_field_names_in_public', 'ok': True, 'detail': []}, {'check': 'no_proxy_status_marker_rows_in_public', 'ok': True, 'detail': []}, {'check': 'no_target_diff_text_in_public', 'ok': True, 'detail': []}, {'check': 'no_hidden_proxy_payload_embedded_in_public', 'ok': True, 'detail': 'proxy_json_bytes=521'}, {'check': 'no_semantic_gold_tokens_in_public', 'ok': True, 'detail': []}]`
- [PASS] static_intent_artifact_exists_djangocms-rc-888ee6eeef91 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-888ee6eeef91\public\intent.json`
- [PASS] m1_m3_prompt_module_unmodified_encoding_ablation.py — `src/benchmark/selection/encoding_ablation.py`
- [PASS] m1_m3_prompt_module_unmodified_impact_planner_v2.py — `src/benchmark/selection/impact_planner_v2.py`
- [PASS] m1_m3_prompt_module_unmodified_study_runtime.py — `src/benchmark/external_validity/study_runtime.py`

## Gate 3 — Pipeline Smoke Test: PASS

- [PASS] synthetic_pipeline_produced_valid_cases — `['d846c5094714b4fbdddf47ebde053740ecb7a7c2']`
- [PASS] synthetic_pipeline_recorded_exclusions — `{'duplicate_or_related_change': 1, 'intent_path_leakage': 1, 'merge_commit': 1, 'migrations_only': 1, 'production_add_delete_rename_copy_v1_unsupported': 3, 'tests_only': 1, 'whitespace_only': 1}`
- [PASS] synthetic_pipeline_zero_api — `synthetic pipeline is deterministic local git only`

## Gate 4 — Dry Run: PASS

- [PASS] four_to_six_miner_dev_cases_materialized — `6`
- [PASS] case_manifest_reloads_djangocms-rc-47040a2887ca — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-47040a2887ca`
- [PASS] case_artifacts_present_djangocms-rc-47040a2887ca — `{'case_id': 'djangocms-rc-47040a2887ca', 'parent': '8f9ed64184d2303cc9f8c252a53d7e3675d14814', 'target': '47040a2887ca3cab21a21f3e0fab758221be3d7c', 'proxy_size': 1, 'universe_size': 144}`
- [PASS] case_manifest_reloads_djangocms-rc-e008ff4b5c21 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-e008ff4b5c21`
- [PASS] case_artifacts_present_djangocms-rc-e008ff4b5c21 — `{'case_id': 'djangocms-rc-e008ff4b5c21', 'parent': '8d50660e7bcf8e480b32f36b4fb409c09f8b3fcd', 'target': 'e008ff4b5c21f376e42896692a78a84e3d6c023c', 'proxy_size': 2, 'universe_size': 144}`
- [PASS] case_manifest_reloads_djangocms-rc-c30efd44e92e — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-c30efd44e92e`
- [PASS] case_artifacts_present_djangocms-rc-c30efd44e92e — `{'case_id': 'djangocms-rc-c30efd44e92e', 'parent': '888ee6eeef91ba094e5dfd6cf4a04332969d9952', 'target': 'c30efd44e92eb24141bf5aa5f4c8e0a3fb590870', 'proxy_size': 1, 'universe_size': 144}`
- [PASS] case_manifest_reloads_djangocms-rc-fd608e896daf — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-fd608e896daf`
- [PASS] case_artifacts_present_djangocms-rc-fd608e896daf — `{'case_id': 'djangocms-rc-fd608e896daf', 'parent': '23824547e0641b7bb03b334a8d825252c937758c', 'target': 'fd608e896daf9c56a3f2202133c823efbace4603', 'proxy_size': 1, 'universe_size': 144}`
- [PASS] case_manifest_reloads_djangocms-rc-110d4c740927 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-110d4c740927`
- [PASS] case_artifacts_present_djangocms-rc-110d4c740927 — `{'case_id': 'djangocms-rc-110d4c740927', 'parent': '50c3576080be08a4b7672bbd7bdfea4f97cc1621', 'target': '110d4c74092768ee3e58f44b5a44f767b4c15fe5', 'proxy_size': 3, 'universe_size': 144}`
- [PASS] case_manifest_reloads_djangocms-rc-888ee6eeef91 — `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\benchmark_data\real_commit_impact_v1\miner_dev\djangocms-rc-888ee6eeef91`
- [PASS] case_artifacts_present_djangocms-rc-888ee6eeef91 — `{'case_id': 'djangocms-rc-888ee6eeef91', 'parent': 'ada585d3f3580691f7c14c7bf0115f55cdca87f2', 'target': '888ee6eeef91ba094e5dfd6cf4a04332969d9952', 'proxy_size': 4, 'universe_size': 144}`
- [PASS] zero_scientific_api_calls — `M4A-1 miner issues zero LLM/API calls (deterministic git + AST only)`

## Gate 5 — Integration Test: PASS

- [PASS] manifest_reloads_through_validator_djangocms-rc-47040a2887ca — `djangocms-rc-47040a2887ca`
- [PASS] manifest_reloads_through_validator_djangocms-rc-e008ff4b5c21 — `djangocms-rc-e008ff4b5c21`
- [PASS] manifest_reloads_through_validator_djangocms-rc-c30efd44e92e — `djangocms-rc-c30efd44e92e`
- [PASS] manifest_reloads_through_validator_djangocms-rc-fd608e896daf — `djangocms-rc-fd608e896daf`
- [PASS] manifest_reloads_through_validator_djangocms-rc-110d4c740927 — `djangocms-rc-110d4c740927`
- [PASS] manifest_reloads_through_validator_djangocms-rc-888ee6eeef91 — `djangocms-rc-888ee6eeef91`
- [PASS] frozen_universe_count_144 — `{'count': 144, 'count_ok': True, 'hash': '43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410', 'hash_ok': True}`
- [PASS] frozen_universe_hash_unchanged — `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`
- [PASS] frozen_graph_edge_count_562 — `{'edge_count': 562, 'edge_count_ok': True, 'hash': '0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58', 'hash_ok': True, 'node_count': 144}`
- [PASS] frozen_graph_hash_unchanged — `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58`

## Gate 6 — Metric Verification: PASS

- [PASS] synthetic_metrics_tp_fp_fn — `{'tp': 2, 'fp': 1, 'fn': 1}`
- [PASS] synthetic_metrics_precision — `0.6666666666666666`
- [PASS] synthetic_metrics_recall — `0.6666666666666666`
- [PASS] synthetic_metrics_f1_fnr — `{'f1': 0.6666666666666666, 'fnr': 0.3333333333333333}`
- [PASS] miner_dev_excluded_from_aggregate_metrics — `MINER_DEV split is permanently excluded from final metrics (frozen policy)`
