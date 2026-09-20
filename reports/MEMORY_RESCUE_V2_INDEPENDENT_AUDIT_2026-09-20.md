# Parent-Only Repository Memory Rescue V2 — Independent Audit (2026-09-20)

**Checks:** 23/23 PASS

- [x] sealed_guard_323_dev_only — n=323
- [x] v1_fold_reuse_exact — 
- [x] deep_fn_counts — dc=199 saleor=177
- [x] deep_fn_median_rank — {'djangocms': 62.0, 'saleor': 70.0}
- [x] deep_fn_coverage_union_positive — {'djangocms': {'n': 199, 'union_recovered': 43, 'rate': 0.2161}, 'saleor': {'n': 177, 'union_recovered': 48, 'rate': 0.2712}}
- [x] dependency_cluster_diagnostic — {'djangocms': {'n': 199, 'A': 109, 'B': 25, 'C': 56}, 'saleor': {'n': 177, 'A': 130, 'B': 49, 'C': 76}}
- [x] v2_A_djangocms_metrics_recompute — persisted={'tp': 152, 'fp': 222, 'fn': 355, 'precision': 0.40641711229946526, 'recall': 0.29980276134122286, 'f1': 0.34506242905788875, 'fnr': 0.7001972386587771} audited={'tp': 152, 'fp': 222, 'fn': 355, 'precision': 0.40641711229946526, 'recall': 0.29980276134122286, 'f1': 0.34506242905788875, 'fnr': 0.7001972386587771}
- [x] v2_A_saleor_metrics_recompute — persisted={'tp': 158, 'fp': 283, 'fn': 310, 'precision': 0.35827664399092973, 'recall': 0.33760683760683763, 'f1': 0.34763476347634764, 'fnr': 0.6623931623931624} audited={'tp': 158, 'fp': 283, 'fn': 310, 'precision': 0.35827664399092973, 'recall': 0.33760683760683763, 'f1': 0.34763476347634764, 'fnr': 0.6623931623931624}
- [x] v2_B_djangocms_metrics_recompute — persisted={'tp': 152, 'fp': 222, 'fn': 355, 'precision': 0.40641711229946526, 'recall': 0.29980276134122286, 'f1': 0.34506242905788875, 'fnr': 0.7001972386587771} audited={'tp': 152, 'fp': 222, 'fn': 355, 'precision': 0.40641711229946526, 'recall': 0.29980276134122286, 'f1': 0.34506242905788875, 'fnr': 0.7001972386587771}
- [x] v2_B_saleor_metrics_recompute — persisted={'tp': 159, 'fp': 283, 'fn': 309, 'precision': 0.3597285067873303, 'recall': 0.33974358974358976, 'f1': 0.34945054945054943, 'fnr': 0.6602564102564102} audited={'tp': 159, 'fp': 283, 'fn': 309, 'precision': 0.3597285067873303, 'recall': 0.33974358974358976, 'f1': 0.34945054945054943, 'fnr': 0.6602564102564102}
- [x] v2_A_djangocms_ci_crosses_zero — {'metric': 'f1', 'n_tasks': 174, 'n_resamples': 10000, 'seed': 20260920, 'point_policy': 0.34506242905788875, 'point_sparse': 0.3176620076238882, 'point_delta': 0.027400421434000566, 'ci95_lower': -0.01024363001316319, 'ci95_upper': 0.06363646578140962, 'ci95_excludes_zero': False}
- [x] v2_A_saleor_ci_excludes_zero — {'metric': 'f1', 'n_tasks': 149, 'n_resamples': 10000, 'seed': 20260920, 'point_policy': 0.34763476347634764, 'point_sparse': 0.26052631578947366, 'point_delta': 0.08710844768687398, 'ci95_lower': 0.05151940532931262, 'ci95_upper': 0.12288854177685306, 'ci95_excludes_zero': True}
- [x] v2_B_djangocms_ci_crosses_zero — {'metric': 'f1', 'n_tasks': 174, 'n_resamples': 10000, 'seed': 20260920, 'point_policy': 0.34506242905788875, 'point_sparse': 0.3176620076238882, 'point_delta': 0.027400421434000566, 'ci95_lower': -0.01034497895377164, 'ci95_upper': 0.06381894734701936, 'ci95_excludes_zero': False}
- [x] v2_B_saleor_ci_excludes_zero — {'metric': 'f1', 'n_tasks': 149, 'n_resamples': 10000, 'seed': 20260920, 'point_policy': 0.34945054945054943, 'point_sparse': 0.26052631578947366, 'point_delta': 0.08892423366107577, 'ci95_lower': 0.052890236168822935, 'ci95_upper': 0.12548254414049784, 'ci95_excludes_zero': True}
- [x] robustness_exact_same_set_high — 
- [x] robustness_jaccard_mean_high — 
- [x] robustness_verdict_same — 
- [x] gate_A_djangocms_fail — 
- [x] gate_A_saleor_pass — 
- [x] gate_B_djangocms_fail — 
- [x] gate_B_saleor_pass — 
- [x] final_verdict_fail — 
- [x] zero_api_by_construction — no network/model code path in this mission
