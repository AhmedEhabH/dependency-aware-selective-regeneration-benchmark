# R4 Framework-Gate Phase-3 Repair

- **Mission:** `M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR`
- **Mission type:** narrow implementation + targeted qualification + corrected Full144 pre-execution refreeze
- **Terminal verdict:** `PASS_FRAMEWORK_GATE_REPAIR_READY_FOR_CORRECTED_FULL144_EXECUTION`

---

## 1. Phase-2 authority

The Phase-2 frozen ruling (Candidate C) is the sole design authority:

> The manage gate MUST use the exact historical revision's repository-authored
> pytest/test Django settings module:
> `python manage.py check --settings=<repo-authored pytest settings module>`.

- Decision artifact: `research/env-canon-r4/R4_FRAMEWORK_GATE_PHASE2_DECISION.json`
- Phase-2 tag: `m17-d7-r4-framework-gate-phase2-decision-r1-2026-10-15` (peel `06610ef1…`)
- Starting HEAD verified: `06610ef13fcf635aafdfe5cf94128e160d2e799c`

## 2. Exact code change

**File:** `scripts/r4_behavioral_calibration_n12_r2.py`

The manage-gate command in the container script changed from:

```
python manage.py check --settings=saleor.tests.settings
```

to a per-worktree resolution of the repository-authored pytest Django settings
module from the EXACT materialized worktree:

```
python manage.py check --settings=<resolved repo-authored pytest settings module>
```

The resolver is a narrow port of the Phase-1 `pytest_ds_modules` extraction
(`--ds=<module>` over `setup.cfg`, `pytest.ini`, `pyproject.toml` in that order)
plus fail-closed resolution.  The same logic ships both as host-side pure
functions (tested directly) and as a self-contained program executed inside the
container (`REPO_SETTINGS_RESOLVER_PROGRAM`).

### Resolver semantics

1. Inspect only repository-authored pytest config sources (`setup.cfg`,
   `pytest.ini`, `pyproject.toml`).
2. Resolve exactly one module.
3. Modern signature → `saleor.tests.settings`; legacy signature → `tests.settings`.
4. Verify the dotted module maps to a file/package present in the exact worktree
   before running the manage gate.
5. FAIL CLOSED on: zero modules, multiple conflicting modules, malformed module,
   or referenced module absent from the exact worktree.
6. Never fall back silently to `saleor.tests.settings` or `saleor.settings`.
7. No task/unit/commit identity is used for selection.

Manage-gate strength is unchanged: rc==0 PASS, nonzero framework smoke failure;
`SKIP` only where `manage.py` is absent; import/pytest smoke, gate ordering, rc
classification, timeout/network/install semantics unchanged.

## 3. Static replay (frozen Phase-1 evidence, no git rescan)

`scripts/r4_framework_gate_phase3_static_replay.py` replays the resolver rule
against the frozen probe/audit artifacts:

| Metric | Value |
|---|---|
| total commits | 219 |
| resolvable | 219 |
| → `saleor.tests.settings` | 218 |
| → `tests.settings` | 1 |
| unresolved | 0 |
| conflicting | 0 |
| frozen repo-module mismatches | 0 |

## 4. Targeted tests

`tests/unit/wp2/env_r4/test_r4_framework_gate_phase3_repair.py` — **16 passed**:

1. modern config resolves `saleor.tests.settings`
2. legacy config resolves `tests.settings`
3. missing settings declaration fails closed
4. conflicting settings declarations fail closed
5. referenced settings module absent from worktree fails closed
6. no task/unit/commit-specific selection exists
7. manage command uses the resolved module
8. pytest/import smoke unchanged
9. frozen 219/219 static replay consistent

## 5. Real offline qualification

Dedicated root `D:\WP2\runs\r4-framework-gate-phase3-qualification-2026-10-15`,
`--network=none`, existing local images only.

### A. Legacy target (Unit 56)

- `vu-cdcf3222cbb5`, commit `8220a534…`, image
  `envcanon/saleor-env-native-nat-62bc3631c27d-runtimeclean:r4-toolhouse-clean-20261014`
- **Resolved manage module: `tests.settings`**
- install rc 0, pip check rc 0, native failures [], import rc 0, manage rc 0, pytest rc 0
- **Result: PASS**

### B. Modern-layout control (Unit 47)

- `vu-eda4e9f82401` (modern signature, same py38/poetry profile/era as Unit 56)
- **Resolved manage module: `saleor.tests.settings`** (both member worktrees)
- manage rc 0 (both), import rc 0, pytest rc 0
- **Result: PASS**

## 6. Invariance statement

Only the manage-gate settings-module resolution changed.  Import smoke, pytest
smoke, gate ordering, rc classification, timeout/network/install semantics,
population/order, providers, lock closure, images, artifact store, source
materializer, and dependency rules are unchanged.

## 7. Corrected Full144 run

- Run root: `D:\WP2\runs\r4-full-d7-144-framework-corrected-2026-10-15`
- Fresh freeze: `<run_root>\freeze\PRE_EXECUTION_FREEZE.json`
- Launcher: `scripts/r4_full144_corrected_launcher.ps1`
- Preflight: `scripts/r4_full144_corrected_preflight.py`
- Effective execution code set:
  `research/env-canon-r4/R4_FRAMEWORK_GATE_CORRECTED_EFFECTIVE_EXECUTION_CODE_SET.json`
  (aggregate `a74f718d…`; corrected runner sha256 `f906539f…`)
- Restart from Unit 1; zero imported scientific evidence; concurrency 1;
  fail-fast/checkpoint semantics preserved; `--network=none`.
- **Full144 scientific units executed in this mission: 0** (preflight only).

## 8. Canonical failed run immutability

- Freeze record SHA-256 still `5c3ec3bde…` (matches frozen receipt)
- Progress: 55 PASS + Unit 56 `ENV_FRAMEWORK_GATE_FAILURE`, stopped_early false,
  56 unit dirs present
- Launcher stop line unchanged
- Predecessor worktree `D:\WP2\active\r4-full144-successor-refreeze` clean at
  `def15aef…`

## 9. Next gate

`M17_D7_R4_FRAMEWORK_GATE_CORRECTED_FULL144_EXECUTION` — start the corrected
Full144 run with the corrected launcher.
