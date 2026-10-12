# D7_R3_HARNESS_FREEZE_REPORT

- **Mission:** `M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE`
- **Harness:** `D:\wp2_env_store\harness\d7_r3`
- **Deterministic synthetic suite:** P2P 7/7 | F2P 9/9 | wheel-tag controls 9/9
- **Real 12-unit calibration executed:** NO
- **Scientific changes:** NONE

## Corrected engineering probe-spec defects (evidence-mapped)

| defect | package | R2 spec | R3 spec (loader-truth) |
|---|---|---|---|
| R2_DEFECT_A | `libopenjp2-7` | `libopenjp2-7.so.7` | `libopenjp2.so.7` |
| R2_DEFECT_B | `pipx` | PATH `/usr/local/bin/pipx` | EXEC probe (command -v pipx -> `/usr/bin/pipx`) |
| R2_DEFECT_C | `libxslt1-dev` | `libxslt.so.1.1` | `libxslt.so.1` |

## Harness SHA256 (per file)

| file | sha256 | bytes |
|---|---|---|
| `D7_R3_HARNESS_CONTRACT.md` | `fd06ebb2fcc29f128c15af0a1986f90684ba4d4c62dbfcb6493ed863fb98dfa5` | 8823 |
| `D7_R3_HARNESS_MANIFEST.json` | `4724f3dc5e222ed6dcab4d230661da898a8a3fb71922225b7dd614b0bf9aa97d` | 1515 |
| `d7_r3_closure.py` | `88eec826d6c099831c9116e8269d402053624e8d4049ab6337c42daab3b54f58` | 8979 |
| `d7_r3_light_pack.py` | `c14e9d2e7b56f02774b96449ba6755a083cd7f819c62e683b070579c7655620e` | 4821 |
| `d7_r3_native_specs.py` | `051608c37840a8a4d5b01c6bf5fb0d653624227ca723bef656af64846508b44c` | 6026 |
| `d7_r3_probes.py` | `04a395ce0069321f11b5b419d48569d94a1e81891ab767b564fd0c89aa35bad9` | 6406 |
| `d7_r3_validation_driver.py` | `658f316961948041f908a6447736cd3169dedd26123d70c7942bdf4dea8aea40` | 43741 |
| `d7_r3_wheeltags.py` | `e5e7d83846c90d61988190a6c0115565fb762fdebfed757fa1012356fe03312e` | 5858 |
| `tests/pytest.ini` | `aff86c25b341f851c7689e0e81c92b5a57d3ee3825de58e03a1a5568fccdcc77` | 35 |
| `tests/test_d7_r3_harness.py` | `5a138cf112fcfdd17c144e804d89babb058b64f665e8b54be1802a61f60fdfdb` | 13151 |

## Synthetic suite items

### Positive (P2P)

- P1_clean_runtime_wheel_only_install_path: `PASS` (PASS)
- P2_runtime_pip_check_clean: `PASS` (PASS)
- P3_native_profile_exact_required_probes: `PASS` (PASS)
- P3b_pipx_path_resolution_exact: `PASS` (PASS)
- P4_no_native_profile_does_not_probe_unrelated: `PASS` (PASS)
- P5_network_unavailable_under_network_none: `PASS` (PASS)
- P6_libxslt_soname_exact_loader: `PASS` (PASS)

### Negative (F2P), each must FAIL CLOSED

- F1_build_toolhouse_contamination_fail_closed: detected as `RUNTIME_TOOLHOUSE_CONTAMINATION` (OK)
- F2_missing_runtime_wheel_source_build_request_fail_closed: detected as `RUNTIME_ARTIFACT_CLOSURE_DEFECT` (OK)
- F3_wrong_native_profile_probe_fail_closed: detected as `NATIVE_FAIL` (OK)
- F4_incorrect_absent_required_soname_fail_closed: detected as `NATIVE_FAIL` (OK)
- F4b_pipx_not_resolvable_fail_closed: detected as `NATIVE_FAIL` (OK)
- F4c_libxslt_absent_soname_fail_closed: detected as `NATIVE_FAIL` (OK)
- F5_network_visible_fetchcapable_fail_closed: detected as `NETWORK_FAIL_CLOSED` (OK)
- F6_deliberate_pip_check_inconsistency_fail_closed: detected as `PIP_CHECK_FAIL` (OK)
- F7_deliberate_smoke_failure_fail_closed: detected as `SMOKE_FAIL` (OK)

## Frozen closure (read-only, 12 units, no execution)

- `12` units checked | all_resolve=`True`
- Runtime path is wheel-only; a missing/incompatible wheel is a runtime-artifact-closure defect (FAIL CLOSED); no source build is ever attempted.

## Build/runtime separation mechanism

- SOURCE-BUILD CANON -> frozen canonical wheels -> D7 runtime wheel input -> clean runtime install -> pip check / smoke / native probes.
- The build toolhouse is NEVER installed into the runtime environment. `audit_toolhouse_contamination` fails closed if any build-toolhouse-only distribution (vcs-versioning, poetry-core, setuptools-scm, wheel) is present.

## Native-profile derivation & matching

- Probes are derived from the unit's exact frozen `native_profile_id`; no global probe map.
- SONAME matching validates loader-visible names with strict equality against frozen allowed sonames - no substring-based optimistic matching.
- PATH/executable requirements use fetch-truth: absolute paths where the frozen images genuinely place them, and EXEC-on-PATH resolution (command -v) for PATH-resolved executables (pipx).

## Network enforcement

- Every execution path requires the network gate: containers run with `--network=none` and the V2 probe must report `NETWORK_UNAVAILABLE`; a reachable/fetch-capable outcome is FAIL CLOSED.

## R2 immutability

- R2 harness (`harness/d7_r2`) is immutable historical evidence; all its manifest-listed files were SHA-256-verified before and after this mission (unchanged).  R3 is a separate additive harness (harness/d7_r3).

