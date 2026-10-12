# D7 R3 Evidence — Remote Preservation Index

Mission: `M17_ENV_CANON_D7_R3_REMOTE_EVIDENCE_PRESERVATION`
Date: 2026-10-12
Mission class: T2 — EVIDENCE PRESERVATION / REMOTE BACKUP ONLY
Scientific changes: NONE
Calibration touched: FALSE
Source store (read-only): `D:\wp2_env_store`
This Git snapshot root: `research/env-canon-evidence/d7-r3/`
Verifier: `scripts/env_canon_preserve_verify.py`
Per-file SHA-256 + provenance: `EVIDENCE_MANIFEST.json`

## What this snapshot is

1. R2 was immutable failed calibration evidence. `harness/d7_r2` froze before
   the calibration-12 run, and R2 calibration failed at the first real unit
   (`N_EXECUTED=1, N_PASS=0, N_FAIL=1`) on a native-profile SONAME mismatch.
   R2 is unchanged and remains immutable failed evidence
   (`receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json`).
2. R3 is additive corrected harness evidence. A new harness tree
   (`harness/d7_r3/`) was created alongside R2; R2 was never modified. The
   correction is engineering metadata only, aligning harness probe truth with
   the already-frozen environment artifacts.
3. Known R3 engineering corrections (defect-mapped):
   - libopenjp2 loader-visible SONAME: `libopenjp2-7.so.7` -> `libopenjp2.so.7`
   - pipx executable-on-PATH semantics: absolute `/usr/local/bin/pipx` ->
     `command -v pipx` -> `/usr/bin/pipx`
   - libxslt loader-visible SONAME: `libxslt.so.1.1` -> `libxslt.so.1`
4. Frozen R3 verification already established before this preservation mission:
   - 43/43 unit tests PASS (frozen R3 harness test suite)
   - P2P 7/7
   - F2P 9/9
   - WT (wheel-tag controls) 9/9
   - dry closure 12/12
5. No real Calibration-12 result is claimed by THIS preservation mission. The
   R3 freeze explicitly records `real_12_unit_execution_started=false` and
   `calibration_12_not_run=true`. This snapshot preserves evidence; it does not
   add, run, or re-interpret calibration.
6. Source-of-truth remains the original store evidence at `D:\wp2_env_store`;
   this Git copy is a byte-identical remote-preservation snapshot
   (source SHA-256 == destination SHA-256 for every preserved artifact).

## Preserved artifact index

| classification | destination path | sha256 (destination) |
|---|---|---|
| HARNESS | `harness/D7_R3_HARNESS_CONTRACT.md` | `fd06ebb2fcc29f128c15af0a1986f90684ba4d4c62dbfcb6493ed863fb98dfa5` |
| HARNESS | `harness/D7_R3_HARNESS_MANIFEST.json` | `f9f1018bb7d7cc7c78127dcd439303fff4c9bd391d65f9fe2d8e2ac3016c7363` |
| HARNESS | `harness/d7_r3_closure.py` | `88eec826d6c099831c9116e8269d402053624e8d4049ab6337c42daab3b54f58` |
| HARNESS | `harness/d7_r3_light_pack.py` | `c14e9d2e7b56f02774b96449ba6755a083cd7f819c62e683b070579c7655620e` |
| HARNESS | `harness/d7_r3_native_specs.py` | `051608c37840a8a4d5b01c6bf5fb0d653624227ca723bef656af64846508b44c` |
| HARNESS | `harness/d7_r3_probes.py` | `04a395ce0069321f11b5b419d48569d94a1e81891ab767b564fd0c89aa35bad9` |
| HARNESS | `harness/d7_r3_validation_driver.py` | `658f316961948041f908a6447736cd3169dedd26123d70c7942bdf4dea8aea40` |
| HARNESS | `harness/d7_r3_wheeltags.py` | `e5e7d83846c90d61988190a6c0115565fb762fdebfed757fa1012356fe03312e` |
| HARNESS | `harness/tests/pytest.ini` | `aff86c25b341f851c7689e0e81c92b5a57d3ee3825de58e03a1a5568fccdcc77` |
| HARNESS | `harness/tests/test_d7_r3_harness.py` | `5a138cf112fcfdd17c144e804d89babb058b64f665e8b54be1802a61f60fdfdb` |
| SUPPORTING_AUTHORITY | `manifests/D7_CALIBRATION_12_PLAN.json` | `a7617c287a77546ea3a085f4d1fa7115f85fa5988de669419d80677e4ee546bd` |
| MANIFEST | `manifests/D7_R3_HARNESS_FREEZE.json` | `ad8130941391aad2a0575221373651fbfb138f694122f3cd901c59639f68ab35` |
| SUPPORTING_AUTHORITY | `manifests/DOCKER_PROFILE_MANIFEST.json` | `e9ad154f58eca68f5a62cc8041343dc38fddf8cc9ab9910f8ab01ceccc482c4c` |
| SUPPORTING_AUTHORITY | `manifests/R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json` | `131ad7f25c5a32442321b59afa6dd7a7d5d0b09c2145076e15e0de46d6691a52` |
| RECEIPT | `receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json` | `3ad9995bc6bccb411c8c75b846ab8a645bd653f645631b5e2b38d9d4ef39168c` |
| RECEIPT | `receipts/D7_R3_HARNESS_P2P_F2P.json` | `657733893db6989fee0a9e3bece7300c511665727eaa34b94a6ba06295f69672` |
| SUPPORTING_AUTHORITY | `receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json` | `1028bb98798b2ee47a76fec8e82a96172c5564dbc3c6b8a3ce7e922bcad3a67e` |
| REPORT | `reports/D7_R3_HARNESS_FREEZE_REPORT.md` | `287fb4fd332f84e2abec4e7d22621d7a577a9cf856a33a6194220330355e6d77` |
| SUPPORTING_AUTHORITY | `reports/R4B_FINAL_ENVIRONMENT_CANON_REPORT.md` | `8755a686c0e556274313fc2aba66a99db177a8a1f37fabe93d24d231b83b50ca` |
