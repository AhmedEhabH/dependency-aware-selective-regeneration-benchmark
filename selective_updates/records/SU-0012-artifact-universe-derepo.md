# SU-0012 — ArtifactUniverse derived from repository state (no ground truth)

**Change ID:** SU-0012
**Title:** Artifact Universe derived from repository state (no ground truth)
**Date:** 2026-09-20
**Requirement / defect:** The execution Runner could derive `ArtifactUniverse`
from `scenario.expected_affected_artifacts`, exposing ground truth (G7). A
valid E2E execution must derive the eligible artifact universe from the
repository state at the task's PARENT commit.
**Reason for change:** Remove the ground-truth leakage blocker before any
scientific E2E execution. WP-0 (G7) of the End-to-End Selective Regeneration
phase.
**Research/protocol impact:** None — measurement-infrastructure repair. No
scientific claim is created; no localization method or RM-CSS is changed.

## Scope

WP-0 with authorized scope amendment `WP0_SCOPE_AMENDMENT_RUNRECORD_AUDITABILITY`
(ACCEPTED; scientific scope NO; frozen evidence NO). Files touched are
restricted to: `src/benchmark/execution/runner.py`,
`src/benchmark/core/models.py` (RunRecord auditable field),
`src/benchmark/execution/pipeline.py` (flag pass-through), targeted/new tests,
`scripts/ac01_*`, `scripts/ac03_*`, this record, `DECISIONS.md`, `PROGRESS.md`.

## PRE-CHANGE EVIDENCE

### Leaking code path

`BenchmarkRunner._build_artifact_universe` (runner.py) had a legacy impact-only
fixture branch:

```python
# Legacy impact-only fixture compatibility only.
return ArtifactUniverse(artifacts=scenario.expected_affected_artifacts)
```

For any execution where `enable_regeneration=False` and `selection_only=False`,
the eligible artifact universe was derived directly from
`scenario.expected_affected_artifacts` — the ground-truth change set. That is
the documented G7 leakage (recorded in SU-0010A "Ground-Truth Universe
Boundary"). It invalidates scientific E2E execution because the method under
test would see which files the reference says were changed.

### RED regression test

`tests/unit/test_artifact_universe_no_ground_truth.py`
`TestProductionUniverseRepositoryDerived::test_production_universe_never_consults_expected_affected`

Command:
```
python -m pytest "tests/unit/test_artifact_universe_no_ground_truth.py::TestProductionUniverseRepositoryDerived::test_production_universe_never_consults_expected_affected" -q
```
Exit code: 1

Failing output (pre-fix):
```
tests\unit\test_artifact_universe_no_ground_truth.py:171: in test_production_universe_never_consults_expected_affected
    assert "src/main.py" in paths
E   AssertionError: assert 'src/main.py' in {'hidden/secret.py'}
```
The universe was `{'hidden/secret.py'}` — i.e. derived from
`scenario.expected_affected_artifacts` (ground truth) rather than from the
parent repository state.

### Why it invalidates scientific E2E execution

A non-fixture execution that feeds ground-truth paths into `ArtifactUniverse`
leaks the answer into the strategy/regeneration input, so impact prediction
and regeneration are no longer independent of the reference. No valid
scientific E2E correctness/efficiency comparison can be run while this path is
reachable.

## IMPLEMENTATION

### Exact repair

`_build_artifact_universe` now derives the universe from the parent repository
state (the active snapshot) for every non-fixture execution, and only uses
`scenario.expected_affected_artifacts` behind an explicit fixture-only opt-in:

```python
def _build_artifact_universe(self, scenario: Scenario) -> ArtifactUniverse:
    if self._config.allow_ground_truth_universe:
        # Explicit fixture-only opt-in (WP-0 / G7): the universe MAY be
        # derived from scenario.expected_affected_artifacts. This is auditable
        # via RunRecord.allow_ground_truth_universe and is never reachable
        # from a scientific path (fail-closed config).
        return ArtifactUniverse(artifacts=scenario.expected_affected_artifacts)

    # Production path: derive the eligible artifact universe from the
    # repository state at the task's PARENT commit (the active snapshot).
    # Ground truth is NEVER consulted here.
    return ArtifactUniverse(
        artifacts=resolve_allowed_artifacts(
            self._active_snapshot(),
            self._config.editable_artifact_paths,
        )
    )
```

### Source of production ArtifactUniverse

Parent repository state = the runner's active snapshot
(`self._active_snapshot()`), resolved through the existing
`resolve_allowed_artifacts` (the same repository-derived resolver used by the
public real-commit candidate universe and by the regeneration/selection-only
production paths). `resolve_allowed_artifacts` fails closed on missing
snapshot, missing files, traversal, absolute paths, backslashes, and empty
allowed paths.

### Fixture compatibility

Legacy fixture behavior is preserved but moved behind an explicit
`allow_ground_truth_universe` boolean:
- default = `False`;
- a non-fixture/scientific execution cannot silently enable it;
- fixture mode requires explicit opt-in;
- when `True`, the resulting `RunRecord.allow_ground_truth_universe` is `True`
  (auditable);
- invalid configuration fails closed at construction:
  `allow_ground_truth_universe=True` is incompatible with
  `enable_regeneration=True` and with `selection_only=True` (both scientific
  paths); a non-bool value is rejected.

### Why localization science is unchanged

No localization method, RM-CSS policy, prompt, ground truth, dataset, or
scientific protocol was modified. The change is confined to how the *eligible
artifact universe* input is constructed (repository-derived by default) and
how fixture usage is gated + audited. `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
is preserved.

## POST-CORRECTION EVIDENCE

### GREEN regression test

Same command as RED. Exit code: 0. Output:
```
tests\unit\test_artifact_universe_no_ground_truth.py .
============================== 1 passed
```
New suite: `tests/unit/test_artifact_universe_no_ground_truth.py` — 14/14 PASS
(production universe repository-derived; hidden truth absent; flag default
False; fixture opt-in; auditable in RunRecord; serialized; fail-closed on
missing snapshot / empty allowed paths / missing file / traversal; invalid
fixture+regeneration and fixture+selection-only configs rejected; non-bool
flag rejected).

### AC-0.1 transcript (hidden/ground-truth independence)

Command:
```
python scripts/ac01_hidden_truth_independence.py
```
Exit code: 0. Result: PASS. A non-fixture selection-only execution on an
already-exposed djangoCMS scientific case
(`djangocms-rc-06ecf3a8e8de`, parent `369f776…`) constructed a 140-file
repository-derived universe while the hidden proxy
(`hidden/observed_change_set_proxy.json`) was made unreadable and the
ground-truth path was absent. `hidden_in_universe=False`,
`record.allow_ground_truth_universe=False`.

### Static leakage search (AC-0.2)

`grep -rn "expected_affected_artifacts" src/benchmark/execution/` (Windows
`Select-String`):
- `runner.py:2817` — the ONLY production-path access to
  `scenario.expected_affected_artifacts`; guarded by
  `allow_ground_truth_universe` (fixture-only opt-in).
- remaining matches are comments only.

`observed_change_set_proxy`: zero occurrences in `src/benchmark/execution/`.
`hidden` in execution code: `isolation.py:109` (private-path indicator set,
not a read) and two comments. `expected_actions`/`hidden_tests` accesses are
in the regeneration-prompt context builder (`_build_scenario_context`), which
is a separate concern already fail-closed by `scientific_gold_isolation`; they
do not feed `ArtifactUniverse`. No unexplained production-path occurrence.

### 3-task universe sanity table (AC-0.3)

Command: `python scripts/ac03_universe_sanity.py` — exit 0, PASS.

| case_id | parent SHA | repo-derived universe | public candidate-universe | diff | reason |
|---|---|---|---|---|---|
| djangocms-rc-06ecf3a8e8de | 369f7768934 | 140 | 140 | 0 | identical eligibility |
| djangocms-rc-0daae01f2f65 | d7ee89da24e | 152 | 152 | 0 | identical eligibility |
| djangocms-rc-0fec81224889 | 68947484a87 | 140 | 140 | 0 | identical eligibility |

Repository-derived counts equal the public candidate-universe counts exactly
(no Saleor RESERVE outcome was touched).

### Tests

Targeted new suite: `tests/unit/test_artifact_universe_no_ground_truth.py`
14/14 PASS. Affected regression suites pass:
`test_runner.py` 57, `test_regression_fixes.py` 36 (1 skip),
`test_r3d_wiring.py`, `test_pipeline.py`, `test_stagec_selection_study.py`,
`test_stagec_heldout_study.py`, `test_models.py`, `test_checkpoint.py`,
`test_scientific_evidence_persistence.py`, `test_stagec_consolidation.py`,
`test_su0005/0006`, `test_scientific_gold_leakage.py`,
`test_impact_plan_runner.py`, `test_r4_token_and_metrics.py`,
`test_r4_metric_contract.py`, `test_three_arm_core.py`,
`test_su0010a_regeneration.py`, `test_su0011_iterative_agent.py`,
`test_real_smoke.py`, `test_scientific_smoke_v1_fixes.py`,
`test_scientific_smoke_v2_production_path.py`,
`test_v0921_per_cell_validation_runtime.py`,
`test_pilot_multi_repo_production_path.py`, plus scenarios/input-contract/
snapshot suites — all PASS.

### Static checks

- ruff: PASS (changed files)
- mypy --strict on affected packages (`runner.py`, `models.py`, `pipeline.py`):
  PASS
- py_compile on changed files: PASS
- `git diff --check`: PASS

## LIMITATIONS

- G6 FAIL_TO_PASS / PASS_TO_PASS oracle is still unresolved.
- E2E scientific claims (correctness, preservation, architecture, efficiency)
  are still forbidden; no Smoke / Pilot / Research Run is authorized.
- Legacy fixture behavior is now explicit-opt-in only; callers relying on the
  old implicit ground-truth universe must set `allow_ground_truth_universe=True`
  (auditable) or provide parent-state + editable paths.

## Code/Data/Notebook status

- Code Dataset: `src/benchmark/**` changed (runner, core/models, execution/pipeline).
- Data Dataset: unchanged (no benchmark data touched).
- Notebook: unchanged.

## Next step

WP-1 Repository-Agent Selection-Only Baseline — AWAITING AHMED AUTHORIZATION.
Do not run it in this work package.
