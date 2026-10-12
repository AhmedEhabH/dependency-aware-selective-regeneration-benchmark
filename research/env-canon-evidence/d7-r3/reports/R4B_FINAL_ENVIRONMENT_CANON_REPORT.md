# R4B_FINAL_ENVIRONMENT_CANON_REPORT

**Mission:** `M17_ENV_CANON_R4B_FINAL_EXECUTE_APPROVED_ENVIRONMENT_CANON`
**Branch:** `parallel/env-canon-2026-10-09` · **HEAD:** `1661ec215ede6ae96e82735148db4febffb21580`
**Mode:** Engineering only. scientific_changes = NONE. D7 NOT started.

---

## 1. Summary

Final R4B execution completed cleanly:

- 5 amendment classes probed: **C015, C016, C022, C023, C030** — all FULL_PASS
- google-crc32c: **FULL_NATIVE_BUILD_PASS** (8/8 checks, native `.abi3.so`)
- cairocffi py39 runtime gate: **PASS** (cairo_version_string = 1.16.0, libcairo.so.2 resolved)
- PyXB 1.2.5 py312: **OWNER-APPROVED compatibility backport applied + accepted** (9/9 checks)
- Clean canonical 215 rebuild: **214 CANONICAL_FULL_PASS + 1 CANONICAL_APPROVED_COMPATIBILITY_BACKPORT_PASS = 215, 0 FAIL**
- **ENV_SOURCE_BUILD_CANON_READY = TRUE** (source-build stage only; NOT ENV_CANON_READY)
- P2P **12/12 PASS**, F2P **13/13 FAIL-CLOSED**

## 2. Preconditions

- R0 frozen outputs read and internally consistent (manifests/receipts/reports).
- LIGHT `project-light-year-2026-10-11-0122.zip` SHA256 verified =
  `8BADC25BFCA20F5724596960BA3394D45A1CE647B237D4DFE714D7AC824E4252`.
- Frozen scout state confirmed: 215/215 (213 exploratory full, 1 degraded, 1 historical);
  5 amendment classes exactly C015 C016 C022 C023 C030.
- R2 toolhouse: 20/20 files hash-valid (BUILD_TOOLHOUSE_HASHES_R2.json unchanged).
- 7 staged direct artifacts: 7/7 hash-valid (R4B_S0_STAGED_ARTIFACTS).

## 3. R4B.0 — Final input packet revalidated

| Assertion | Result |
|---|---|
| A. R2 toolhouse hash-valid | PASS (20/20) |
| B. canonical staged direct artifacts hash-valid | PASS (7/7; cffi 1.14.0/1.14.4, pycparser 2.20, pytest-runner 5.2, Sphinx 2.2.2) |
| C. Sphinx 2.2.2 effective closure frozen | PASS (23 base wheels + Sphinx; requires_dist identical to 2.2.1 closure) |
| D. libcairo2 Bookworm runtime plan frozen | PASS (libcairo2 1.16.0-7 amd64) |
| E. google/crc32c exact historical source frozen | PASS (tag 1.0.6, commit 75e82b8bc35fd013a6220427e7f61f8adeebf9b7) |
| F. PyXB Option A now OWNER_APPROVED | PASS (PYXB_OPTION_A, this mission) |

## 4. R4B.1 — Controlled acquisition

- Sphinx 2.2.2 closure: **23/23 base wheels** downloaded from exact frozen
  files.pythonhosted.org URLs, SHA256 verified (11,761,794 B).
- libcairo2 `.deb`: `libcairo2_1.16.0-7_amd64.deb` (574,676 B), SHA256
  `927fa059...6a69` = frozen value.
- google/crc32c source: `crc32c-1.0.6.tar.gz` (29,596 B), SHA256
  `6b3b1d86...788e9`, provenance verified — shallow clone HEAD == commit
  `75e82b8...` and **38/38 extracted files byte-match git blob content**.
- Total new network payload: **11.79 MiB** (well under 256 MiB cap).

## 5. R4B.2 — Final build toolhouse (additive)

- 7 staged direct artifacts promoted (copies) into the amended toolhouse.
- 23 Sphinx closure wheels added to py38/py39 (per-era MarkupSafe cp38/cp39 placed in matching era).
- R2 files **byte-identical** (re-verified 20/20 vs BUILD_TOOLHOUSE_HASHES_R2.json).
- Final toolhouse: py38=33, py39=33, py312=8 (total 74 wheels).
- Verify: 74 wheels checked — 0 metadata problems, 0 closure transitive missing.
  `R4B2_TOOLHOUSE_VERIFY_PASS`.
- Freeze: `manifests/R4B_FINAL_BUILD_TOOLHOUSE.json`.

## 6. R4B.3 — py39 native capability image

- Built `envcanon/saleor-env-r4b-py39-native:latest`
  (digest `3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89`).
- libcairo2 runtime: **PRESENT** (`/lib/x86_64-linux-gnu/libcairo.so.2`).
- google/crc32c native installed to `/opt/envcanon/crc32c`:
  - `include/crc32c/crc32c.h` (sha256 `2ad42dff...`)
  - `lib/libcrc32c.so` (sha256 `b611bc93...`)
- CMake config: `CRC32C_BUILD_TESTS=OFF CRC32C_BUILD_BENCHMARKS=OFF CRC32C_USE_GLOG=OFF BUILD_SHARED_LIBS=ON`.
- cmake 3.31.10 pip-installed (Google documented method); gcc/g++/make already present.
- Freeze: `manifests/R4B_FINAL_NATIVE_ENVIRONMENT.json`.

## 7. R4B.4 — Five-class probe

| Class | Member | Result |
|---|---|---|
| C015 | cairocffi==1.1.0::py38 | FULL_PASS |
| C015 | cairocffi==1.2.0::py38 | FULL_PASS |
| C016 | measurement==3.2.0::py38 | FULL_PASS |
| C022 | cairocffi==1.2.0::py39 | FULL_PASS |
| C023 | measurement==3.2.0::py39 | FULL_PASS |
| C030 | google-crc32c==1.0.0::py39 | FULL_PASS + **FULL_NATIVE_BUILD_PASS** |

Flags: `--network=none --no-build-isolation`, max workers 2.
Freeze: `receipts/R4B_FINAL_CLASS_PROBES.json`.

## 8. R4B.5 — cairocffi py39 runtime gate (C022)

- Wheel build: PASS. Offline install: PASS.
- `python -c "import cairocffi; print(cairocffi.cairo_version_string())"` → **1.16.0**.
- Resolves `/lib/x86_64-linux-gnu/libcairo.so.2` (libcairo2 1.16.0-7 bookworm).
- Freeze: `receipts/R4B_FINAL_CAIRO_RUNTIME.json`.

## 9. R4B.6 — google-crc32c fidelity gate (C030)

- **FULL_NATIVE_BUILD_PASS**, 8/8 checks:
  1. build exit 0 ✓ 2. wheel NOT py3-none-any ✓ 3. exact Name/Version ✓
  4. offline install ✓ 5. import ✓ 6. implementation='cffi' ✓
  7. `google_crc32c._crc32c_cffi` importable ✓ 8. known CRC32C smoke ✓
    (`value(b"123456789") == 0xe3069283`).
- Native module: `google_crc32c/_crc32c_cffi.abi3.so` present in wheel.
- Build consumed `/opt/envcanon/crc32c/include/crc32c/crc32c.h` + `libcrc32c.so`
  (CRC32C_INSTALL_PREFIX). Source commit `75e82b8...` confirmed.
- Freeze: `receipts/R4B_FINAL_GOOGLE_CRC32C_FIDELITY.json`.

## 10. R4B.7 — PyXB 1.2.5 compatibility backport (OWNER-APPROVED)

- Source input: exact frozen `PyXB-1.2.5.tar.gz`
  (sdist sha256 `4e8f62ee...`), independently verified.
- Root cause: vendored `pyxb/utils/six.py` `_SixMetaPathImporter` lacks `find_spec`
  (PEP 302 only); Python 3.12 removed `find_module`.
- Patch: minimal `find_spec()` via `importlib.util.spec_from_loader` (Track-B equivalent).
- **before six.py sha256 = `c759ab5c...`** (independently verified from canonical sdist;
  the R4B_R0 JSON receipt value `c7811dd2...` was contradicted by canonical input —
  mission's warning validated).
- **after six.py sha256 = `04bf14b9...`** (matches Track-B proven value exactly).
- Diff: `B_patch_canonical.diff` sha256 `325908f7...` (only find_spec, 0 unrelated edits).
- Label: `DEPENDENCY_COMPATIBILITY_BACKPORT`, authority
  `OWNER_APPROVED_ENGINEERING_EXCEPTION`; scientific_evidence NONE, rq_evidence NONE.
- Freeze: `manifests/R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json`.

## 11. R4B.8 — PyXB acceptance gate

- 9/9 checks PASS on py312: package PyXB, version 1.2.5, target py312,
  only approved diff, wheel builds (`pyxb-1.2.5-py3-none-any.whl`), valid filename,
  offline install, `import pyxb`, `import pyxb.utils.six.moves.urllib`,
  representative smoke (`urlparse`, `pyxb.utils.utility`).
- Differential smoke: unmodified PyXB 1.2.5 on py39 **PASS**.
- Informational: deeper modules (`pyxb.binding`, `pyxb.xmlschema`) hit a SEPARATE
  py312 incompatibility (`collections.MutableSequence` removed in 3.10) — outside the
  approved backport scope; recorded distinctly, NOT silently ideal.
- Freeze: `receipts/R4B_FINAL_PYXB_ACCEPTANCE.json`.

## 12. R4B.9 — Clean canonical 215 rebuild

- Fresh canonical source-build validation (NOT Track-B outputs).
- Inputs: frozen canonical source set (215/215 hash-verified), amended toolhouse,
  final native profiles, approved PyXB backport for pyxb==1.2.5::py312 only.
- Flags: `--network=none --no-build-isolation`, max workers 2.
- Accounting: **214 CANONICAL_FULL_PASS + 1 CANONICAL_APPROVED_COMPATIBILITY_BACKPORT_PASS = 215; 0 FAIL.**
- Wheel hashes independently re-verified 215/215 against receipts.
- Offline-install spot checks (pyxb py312, google-crc32c py39, cairocffi py39): PASS.
- Freeze: `receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json`.

## 13. R4B.10 — Source build canon freeze

`ENV_SOURCE_BUILD_CANON_READY = TRUE` for the source-build-environment stage only.

Freeze: `manifests/R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json`.

NOT claimed: `ENV_CANON_READY` (D7 authority boundary; D7 not started in this mission).

## 14. R4B.11 — P2P / F2P

- **P2P 12/12 PASS** (hash-valid artifacts, Sphinx closure complete, cffi pins preserved,
  libcairo gate PASS, google FULL_NATIVE_BUILD_PASS, exact historical commit, PyXB 1.2.5
  preserved, only approved patch, clean 215 accounting, network disabled, no patch promotion,
  no app/lock/population/scientific change).
- **F2P 13/13 FAIL-CLOSED** (no 2.2.2→2.2.1, no 1.14.0→1.14.2, no incomplete closure,
  no pure-Python fallback as full native, no random crc32c source, no libcairo runtime failure,
  no PyXB-X, no Python downgrade, no invented NOT_READY, no extra PyXB edits,
  no network during builds, no patch-lane promotion, no D7 start).
- Freeze: `receipts/R4B_FINAL_P2P_F2P.json`.

## 15. Invariants

```
application_dependency_versions_changed = NONE
application_locks_changed = NONE
population_changed = NONE
readiness_semantics_changed = NONE
scientific_protocol_changed = NONE
frozen_build_toolhouse_changed = FALSE (R2 unchanged; additive only)
canonical_wheels_changed = FALSE
D7_started = FALSE
```

## 16. Outputs (under D:\wp2_env_store)

Manifests:
- `manifests/R4B_FINAL_ACQUISITION.json`
- `manifests/R4B_FINAL_BUILD_TOOLHOUSE.json`
- `manifests/R4B_FINAL_NATIVE_ENVIRONMENT.json`
- `manifests/R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json`
- `manifests/R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json`

Receipts:
- `receipts/R4B_FINAL_CLASS_PROBES.json`
- `receipts/R4B_FINAL_GOOGLE_CRC32C_FIDELITY.json`
- `receipts/R4B_FINAL_CAIRO_RUNTIME.json`
- `receipts/R4B_FINAL_PYXB_ACCEPTANCE.json`
- `receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json`
- `receipts/R4B_FINAL_P2P_F2P.json`

Report:
- `reports/R4B_FINAL_ENVIRONMENT_CANON_REPORT.md`

---

**STOP token (success):**
`M17_ENV_CANON_R4B_FINAL_COMPLETE_READY_FOR_D7_CALIBRATION`

D7 is NOT started. This is engineering-only evidence; scientific evidence = NONE.