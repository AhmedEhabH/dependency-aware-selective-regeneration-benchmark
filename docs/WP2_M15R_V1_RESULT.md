# WP2 M15-R V1 result (Pilot-B, descriptive)

Tokens: **M15R_OPWS_COMPLETE + M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM**. S3 executed: **False**.
S2 gate: {"gold_robust_episodes": 3, "gold_solvable_tasks": ["saleor-rc-436f52ee3d0c"], "thresholds": {"min_robust_episodes": 6, "min_solvable_tasks": 4, "n_episodes": 30, "n_tasks": 10}, "token": "M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM", "verdict": "FAIL"}.

| Arm:rep | n | APPLIED | NO_SCOPE | INVALID | robust (all) | strict (all) | robust (analysis set) | F2P | tokens | cost $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GOLD_HARD:r1 | 10 | 9 | 0 | 1 | 1 | 1 | 0 | 1 | 220894 | 0.0703667 |
| GOLD_HARD:r2 | 10 | 7 | 0 | 3 | 1 | 1 | 0 | 1 | 252567 | 0.0969071 |
| GOLD_HARD:r3 | 10 | 8 | 0 | 2 | 1 | 1 | 0 | 1 | 241977 | 0.0805299 |

Paired S3 (analysis set): {}.
Cost: {"agent_localization": {"completion_tokens": 8721, "empty_predictions": 2, "model_calls": 228, "prompt_tokens": 2120312, "runs": 30}, "agent_localization_usd_frozen_list_price": 0.6448146, "generation_provider_reported_tokens": 715438, "generation_provider_reported_usd": 0.2478037, "rmcss_selector": "frozen out-of-fold predictions; no M15-R model call"}.

M15-R is descriptive (n <= 10 Pilot-B tasks). OPWS (S1) is the primary, generator-independent selector endpoint. Generation results (S3) are interpreted only on GOLD-solvable tasks and only if the S2 gate passed. No superiority claim.
