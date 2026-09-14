# Pytest Runtime Profile (final stable closure)

**Generated:** 2026-09-14
**Method:** full corpus run once in deterministic shards (Rule 2 of
`OPENCODE_P1_LAUNCH_FAST_TEST_POLICY_2026-09-14.md`); `--durations=25` retained.

## Summary

- Full suite total: **3133 tests / 3100 passed / 33 skipped / 0 failed**
  (5 shards: shard-1, shard-2, shard-3, shard-4a, shard-4b).
- Shard 4 was split into two (4a/4b) because a single run exceeded the shell's
  30-minute command timeout (Rule 2: split only that shard; passing shards not
  restarted).
- Two pre-existing environment-gated tests in
  `tests/integration/test_stagec_djangocms_runtime_wiring.py`
  (`test_all_six_gates_pass`, `test_pinned_source_available`) require the real
  provisioned `benchmark_data/repositories/djangocms` checkout, which is
  gitignored/untracked and absent on this machine; they also conflict with the
  `test_pilot_deployment_bundle.py` hermetic suite (which requires that repo
  ABSENT). This is a pre-existing environment conflict, not a code regression:
  the D13R2 2671-test baseline was run on the pilot branch with a different
  test inventory. After restoring the baseline environment
  (`benchmark_data/repositories` = `{todo}` only), both shards pass.
- Shard logs/XML: `reports/pytest-full-shard-{1,2,3,4a,4b}.{log,xml}`.

## Slowest tests (call/setup duration)

| Time (s) | Test | Shard |
|---|---|---|
| 163.98 | `test_scientific_smoke_v2_production_path.py::test_r5_nine_record_matrix` | 2 |
| 163.73 | `test_scientific_smoke_v2_production_path.py::test_r5_sequential_workspace_isolation_001_002_003[monolithic]` | 2 |
| 80.83 | `test_pilot_deployment_bundle.py::TestPilotKaggleExpandedMount::test_real_kaggle_artifact_expanded_simulation` | 4a |
| 23.77 | `test_kaggle_bundle_smoke_v2_preflight.py::TestKaggleBundleSmokeV2Preflight::test_bundle_baseline_47_tests_and_evaluator_pass[todo-smoke-001]` | 2 |
| 20.31 | `test_scientific_smoke_v2_production_path.py::test_r5_representative_selective_cell_todo_smoke_001` | 2 |
| 18.12 | `test_kaggle_bundle_smoke_v2_preflight.py::TestKaggleBundleSmokeV2Preflight::test_bundle_baseline_47_tests_and_evaluator_pass[todo-smoke-003]` | 2 |
| 17.98 | `test_todo_smoke_evaluator_assets.py::TestCorrectFixtureBaselineCompatibility::test_correct_fixture_passes_baseline_and_evaluator[todo-smoke-003-...]` | 2 |
| 17.69 | `test_scientific_smoke_v2_production_path.py::test_r5_representative_agent_cell_todo_smoke_001` | 2 |
| 17.67 | `test_scientific_smoke_v2_production_path.py::test_r5_leakage_agent_tools_reject_evaluator_paths` | 2 |
| 17.65 | `test_scientific_smoke_v2_production_path.py::test_r5_shared_snapshot_root_arm_child_topology_succeeds` | 2 |
| 17.59 | `test_scientific_smoke_v2_production_path.py::test_r5_representative_monolithic_cell_todo_smoke_001` | 2 |
| 17.47 | `test_scientific_smoke_v2_production_path.py::test_r5_negative_zeroed_persisted_metrics` | 2 |
| 17.46 | `test_kaggle_bundle_smoke_v2_preflight.py::TestKaggleBundleSmokeV2Preflight::test_bundle_baseline_47_tests_and_evaluator_pass[todo-smoke-002]` | 2 |
| 17.38 | `test_todo_smoke_evaluator_assets.py::TestCorrectFixtureBaselineCompatibility::test_correct_fixture_passes_baseline_and_evaluator[todo-smoke-001-...]` | 2 |
| 17.32 | `test_todo_smoke_evaluator_assets.py::TestCorrectFixtureBaselineCompatibility::test_correct_fixture_passes_baseline_and_evaluator[todo-smoke-002-...]` | 2 |
| 15.85 | `test_scientific_smoke_v2_production_path.py::test_r5_negative_evaluator_execution_skipped` | 2 |
| 15.75 | `test_pilot_release_provenance.py::TestGate3CodeManifestSourceParity::test_all_matching_entries_pass` | 4a |
| 15.12 | `test_pilot_release_provenance.py::TestGate3CodeManifestSourceParity::test_lock_files_must_be_lf_faithful` | 4a |
| 14.44 | `test_pilot_real_launch_preflight.py::TestPreflightRunnerPath::test_real_todo_preflight_passes_end_to_end` | 3 |
| 10.08 | `test_pilot_release_provenance.py::TestGate3CodeManifestSourceParity::test_modified_source_blob_fails_naming_the_path` | 4a |
| 9.98 | `test_pilot_release_provenance.py::TestGate3CodeManifestSourceParity::test_missing_tracked_source_fails_naming_the_path` | 4a |
| 9.75 | `test_pilot_release_provenance.py::TestReleaseBuildProvenanceWiring::test_validated_build_rejects_refrozen_notebook_at_head` | 4a |
| 8.86 | `test_pilot_deployment_bundle.py::TestPilotReleaseTrustGate::test_gate3_finalizer_repairs_stale_anchor_and_verifies_without_injection` | 4a |
| 8.63 | `test_pilot_deployment_bundle.py::TestPilotKaggleExpandedMount::test_expanded_mode_dry_run_48_cells` | 4a |

## Slowest files (aggregate)

`tests/integration/test_scientific_smoke_v2_production_path.py` dominates
(several 15–164 s tests, including the 164 s `test_r5_nine_record_matrix`
matrix). `tests/integration/test_pilot_deployment_bundle.py` is next (bundle
builds, ~4–81 s per test). These are pre-existing integration tests; per Rule 3
they are NOT refactored before the paper deadline (nothing blocks
correctness).