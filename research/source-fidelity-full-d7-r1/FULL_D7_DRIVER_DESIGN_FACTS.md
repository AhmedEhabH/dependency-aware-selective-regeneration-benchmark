# M17 Full-D7 driver design facts (recorded before F4 driver freeze)

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7

This file records the frozen-authority design facts the Full-D7 driver MUST
follow. It is a mission-owned record, not a scientific result.

## 1. FULL_D7_FAILURE_POLICY

Authority: D7_R3_HARNESS_CONTRACT.md section G ("The harness fails closed on
ANY of ... There is no 'proceed with warning' path for a unit") is the PER-UNIT
gate contract. The Full-D7 mission (owner authorization, mission brief) is an
environment-QUALIFICATION CENSUS: every frozen unit is executed and classified;
per-unit scientific failures are recorded and execution continues, because the
objective is to establish which units/tasks have a faithful, reproducible,
executable environment (READY / NOT_READY census). There is no frozen Full-D7
fail-fast contract: the D7_R3_HARNESS_CONTRACT section 0 explicitly defers
"Full D7" to a separate owner-authorized mission, and this mission brief IS
that authorization, defining Full D7 as a census (F9 classification taxonomy,
F10 task projection, F11 READY/NOT_READY counts).

FULL_D7_FAILURE_POLICY = CENSUS_CONTINUE

A genuine DRIVER/INFRASTRUCTURE defect (not a unit's scientific gate outcome)
still STOPs the mission per the mission brief F4/F8 STOP conditions.

## 2. Runtime mapping preserved (frozen)

- Per unit: python_version from VALIDATION_UNIT_MATRIX.csv (3.8 / 3.9 / 3.12).
- Per unit: docker image = envcanon/saleor-env-native-<native_profile_id>:latest
  (all 10 native profiles; image id from D6_NATIVE_RESULTS.json image_ids).
- Per unit: era wheelhouse = wheelhouse/<py38|py39|py312>, canon wheels =
  built_wheelhouse/canon_r4b/<era>, merged per era (canon wins).
- Per unit: native profile packages from DOCKER_PROFILE_MANIFEST.json
  native_profiles[<native_profile_id>].
- Per unit: install route / lock type / lock sha256 unchanged.
- Every execution container: --network=none; frozen gates (network probe,
  wheel-only install, toolhouse audit, pip check, native probes, smoke).

## 3. Closure derivation (frozen semantics)

- RUNTIME closure: frozen d7_r3_closure.derive_runtime_closure(lock, pyproject
  paths, MARKER_FILTER_AUDIT.json, pyver=<unit python_version>). The pyver
  parameter is the frozen function's documented parameter; it is REQUIRED to
  keep each era's historical closure (a py39 unit must not be filtered with a
  3.12 python-versions marker set). This is use of the frozen function, not a
  reimplementation.
- SOURCE-AWARE identity: benchmark.wp2.source_fidelity_r1.
  derive_source_aware_closure(lock_text, target_commit, SALEOR_REPO,
  python_version=<unit python_version>, sys_platform="linux",
  lock_format=<unit lock_type>). For uv locks the root editable self is
  classified PATH + excluded from pins (uv_editable_self), matching the frozen
  source-fidelity schema.
- Wheel-tag gate: frozen d7_r3_closure.resolve_runtime_artifacts(pins,
  wheel_file_list=<era merged wheels>). The frozen py312-targeted
  wheel-compatibility gate is the ONLY wheel authority (mission P11). Units
  whose era wheels are rejected by the frozen gate classify
  ARTIFACT_RESOLUTION_FAILURE -> NOT_READY. This is a faithful frozen-authority
  census outcome.

## 4. Source-fidelity overlay (generic, source-type driven)

- apply_source_fidelity_overlay(runtime_pins, source_aware_records): for each
  runtime pin whose lock records a DIRECTORY/PATH source, overlay the merged
  wheel input with the frozen source-fidelity wheel (exact bytes verified
  against SOURCE_FIDELITY_PROVENANCE_MANIFEST.json). REGISTRY pins keep exact
  frozen R3 resolution. DIRECTORY/PATH pin without a frozen artifact, or any
  other non-registry source without exact identity -> FAIL CLOSED.
- Exactly 2 units are affected (vu-692af9112c6d, vu-b9808f19ace4).

## 5. Worktrees

- Full D7 needs all 219 member-task worktrees (byte-exact task checkouts at
  target commits; they provide pyproject.toml for the win32 python-magic-bin
  exclusion and the mounted source for the smoke gates). The read-only store
  contains only the 18 calibration worktrees, so the Full-D7 mission
  materializes all 219 worktrees byte-exact (raw git blob extraction, no CRLF
  conversion) into the FRESH output root (D:\wp2_sf_full_d7_r1_store\worktrees).
  Verified byte-identical to the git tree (the 18 existing store worktrees
  reproduce byte-identically with the same method).

## 6. Host driver interpreter

- Accepted calibration driver ran under C:\Python313\python.exe (Python 3.13),
  verified from the calibration session record. HOST_DRIVER_PYTHON_EXE and
  HOST_DRIVER_PYTHON_VERSION are frozen in the F4 driver-freeze receipt and
  checked by a preflight compatibility test before any real unit.

## 7. Resume / immutability

- One unit per driver invocation (--unit <ordered_full_d7_index>), matching the
  accepted calibration pattern. progress.json records completed units;
  completed units are NEVER re-run; first-attempt evidence is immutable.

## 8. Classification taxonomy (F9)

PASS/READY, ARTIFACT_RESOLUTION_FAILURE, INSTALL_FAILURE, PIP_CHECK_FAILURE,
NATIVE_FAILURE, IMPORT_FAILURE, MANAGE_CHECK_FAILURE, PYTEST_COLLECT_FAILURE/
SMOKE_FAIL, INFRASTRUCTURE_DRIVER_FAILURE, UNKNOWN_FAIL_CLOSED. The driver maps
frozen gate outcomes onto this taxonomy (calibration classify_unit order
preserved, labels renamed to the mission taxonomy).