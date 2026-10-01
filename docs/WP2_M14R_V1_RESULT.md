# WP2 M14R V1 result (DEV_TRAIN_ENG only)

Token: **M14R_FLOOR_NOT_MET**. Winner: **G0**. Next: **HUMAN_DECISION_WP2_RESHAPE**.
Strict-endpoint sensitivity: {'token': 'M14R_FLOOR_NOT_MET', 'winner': 'G0'}.

Member tasks: 13. Provider-reported spend: $0.572623.

| Variant | GOLD n | APPLIED | INVALID | F2P | RESOLVED strict | RESOLVED robust | tasks>=1 | mean tokens | PLACEBO robust |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| G0 | 39 | 35 | 4 | 10 | 8 | 8 | 4 | 14350.0 | 0 |
| G1 | 39 | 35 | 4 | 11 | 9 | 9 | 4 | 16843.3 | 0 |
| G2 | 39 | 38 | 1 | 10 | 8 | 8 | 4 | 21174.4 | 0 |
| G3 | 39 | 38 | 1 | 10 | 8 | 8 | 4 | 24162.3 | 0 |

Decision: {"checks": {"G1": {"better_tasks": 1, "direction": true, "gain": false, "invalid": true, "worse_tasks": 0}, "G2": {"better_tasks": 1, "direction": true, "gain": false, "invalid": true, "worse_tasks": 1}, "G3": {"better_tasks": 1, "direction": true, "gain": false, "invalid": true, "worse_tasks": 1}}, "eligible": [], "thresholds": {"floor_resolved_min": 8, "floor_tasks_min": 5, "max_extra_invalid_vs_g0": 3, "min_gain_vs_g0": 3, "n_gold_episodes_per_variant": 39, "placebo_robust_max": 1}}

M14R is a development probe on DEV_TRAIN_ENG only. It selects a generator variant for a future, separately frozen M15; it is not an RM-CSS-vs-Agent comparison and supports no selector claim. Pilot-A remains PILOT_A_GENERATOR_FLOOR_HOLD.
