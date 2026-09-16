# Independent Audit — Omission-Risk Development Inference (Sparse-v2)

**Generated:** 2026-09-16T06:08:35.567166+00:00
**Study:** omission-risk-development-inference-v1

**OVERALL:** PASS
**Checks:** 31/31

- [PASS] cells_exactly_90 — 90
- [PASS] run_ids_unique — 90
- [PASS] manifest_matches_records — "exact run_id set equality"
- [PASS] valid_90_of_90 — 90
- [PASS] schema_valid_all — 90
- [PASS] no_truncations — 0
- [PASS] raw_sha256_all_match — "mismatches=0"
- [PASS] token_budget_respected — {"tokens": 490747, "ceiling": 600000}
- [PASS] cost_budget_respected — {"cost": 0.184088, "ceiling": 0.3}
- [PASS] records_only_train_validation — {"n_cases": 30}
- [PASS] records_exclude_heldout — "no HELD_OUT_TEST case in records"
- [PASS] manifest_excludes_heldout — "no HELD_OUT_TEST case in manifest"
- [PASS] analysis_outputs_exclude_heldout — "files_with_heldout=0"
- [PASS] provider_deepinfra_all — 1
- [PASS] model_frozen — "qwen/qwen3-coder"
- [PASS] provider_tag_frozen — "deepinfra/turbo"
- [PASS] graph_off_all — "OFF"
- [PASS] temperature_zero_all — "0.0"
- [PASS] cap_16384_all — "16384"
- [PASS] fallback_off_all — "off"
- [PASS] single_record_per_run_id — "one record per cell"
- [PASS] closure_no_replacement_reruns — true
- [PASS] closure_no_result_reruns — true
- [PASS] closure_run_complete — 90
- [PASS] labels_n_30_tasks — 30
- [PASS] reps_nested_not_independent — "has_fn(t) = 1 iff the Sparse-v2 prediction omits >=1 proxy-positive file; pre-registered aggregation = any-FN-over-reps "
- [PASS] class_balance_gate_failed_no_scorer — {"n_pos": 26, "n_neg": 4, "reason": "multivariable RiskScorer NOT fitted: class-balance gate requires >=10 independent tasks per class; analysis is descripti"}
- [PASS] no_scorer_artifact — "no risk_scorer.json produced"
- [PASS] spot_serialized_count_reproducible — {"run_id": "omission-djangocms-rc-0fec81224889-sparse_v2-r1", "from_raw": 3, "recorded": 3}
- [PASS] gates_all_passed — true
- [PASS] gates_audit_passed — true

## Discipline

- Reads persisted artifacts only; no recomputation of model outputs; no new API calls.
- Historical diff = OBSERVED CHANGE-SET PROXY, never semantic ground truth.
- Independent task = historical change; repetitions are nested observations.
- HELD_OUT_TEST never used for any decision in this run.