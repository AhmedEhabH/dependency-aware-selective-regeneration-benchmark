# M17 source-fidelity amendment R1 — freeze report

**Root cause addressed:** `C_LOCK_RECONSTRUCTION_DEFECT` — the D7 R3 environment canon and its closure derivation flatten every dependency to `name==version` and resolve the artifact by normalized distribution name/version, discarding the historical Poetry lock's directory-source identity.  The substituted registry PyXB 1.2.5 wheel uses `collections.MutableSequence` and fails on Python 3.12; the historical vendored PyXB uses `collections.abc.MutableSequence`.

## Authority

- Owner decision: design + freeze an additive source-faithful dependency reconstruction amendment (no calibration, no Full D7).
- Mission class: T3 — environment canon source-fidelity amendment design + freeze.
- Frozen input: `ROOT_CAUSE_CLASSIFICATION = C_LOCK_RECONSTRUCTION_DEFECT`.

## Schema

- `SOURCE_IDENTITY_SCHEMA_VERSION = source_fidelity_r1` (additive; no existing canon schema overwritten).
- Source types: REGISTRY, DIRECTORY, PATH, GIT, URL, FILE, UNKNOWN.
- Dependency identity distinguishes `distribution_name`, `version`, `source_type`, `source_reference`, `source_tree_sha256` (DIRECTORY/PATH), `target_commit`, and environment markers.

## Extraction

- Anchored to `target_commit + historical path`; reads committed Git objects only (`ls-tree -r -z` + raw `cat-file --batch`), never the mutable working tree.
- Canonical tree hash = SHA-256 over the sorted `"<mode> <relpath>\0<content-sha256>\n"` serialization (P2P/F2P, cross-platform deterministic).
- Both exposed tasks vend the identical source bytes, so one source-aware identity covers both directory packages under the same generic rule (confirmed by the defect receipt's P2P note).

## Population audit (S2/S9)

- 50,438 dependency rows across 219 tasks; 50,399 REGISTRY, 4 DIRECTORY, 35 PATH (uv root-project editable-self, not a dependency source loss).
- Source-identity loss: exactly 2 units / 2 tasks (['saleor-rc-19bb9b070965', 'saleor-rc-e6198146186d']).
- Closure impact: 142 units unchanged, 2 changed.

| unit | task | old closure identity | new source-aware identity |
|---|---|---|---|
| vu-692af9112c6d | saleor-rc-19bb9b070965 | `8c86e692f8d23ca4...` | `8c638686445b8895...` |
| vu-b9808f19ace4 | saleor-rc-e6198146186d | `da2fd74b0afb4e99...` | `7bf871f278d8c500...` |

## Built artifacts (S8, engineering P2P only)

| package | wheel | sha256 | probe |
|---|---|---|---|
| PyXB | `pyxb-1.2.5-py3-none-any.whl` | `ee196b69018cf9833f0210d050d8ae544070353a92d490a713be4e8347965aee` | PASS |
| authorizenet | `authorizenet-1.1.4-py3-none-any.whl` | `ba04a34ddba7496d778a458f8023ef597918b301b0824ad0517feed35c727ca9` | PASS |

The built PyXB wheel ships `pyxb/binding/content.py` = `2a4b80093dcddb99a5a5db201143b130d69a332b69bf7ee596e633f051aea7ff` (the exact historical vendored file) using `collections.abc.MutableSequence`, and imports under CPython 3.12. These are ENGINEERING_P2P_ONLY checks, NOT calibration evidence.

## Test results

- 20 source-fidelity tests, all PASS (P1–P9 P2P + F1–F10 F2P).
- Regression: `tests/unit/wp2/test_dep_compiler.py` still passes (registry-only closure unchanged, P7).

## Invariants

- `PYTHON_VERSION_CHANGED = FALSE`
- `TASK_ELIGIBILITY_CHANGED = FALSE`
- `SMOKE_GATE_CHANGED = FALSE`
- `SCIENTIFIC_POPULATION_CHANGED = FALSE`
- `PYXBX_USED = FALSE`
- `R3_HISTORICAL_EVIDENCE_MODIFIED = FALSE`
- `NETWORK_USED = FALSE`
- `TASK_ID_SPECIAL_CASE_USED = FALSE`

## Decision gates

- `CALIBRATION_RERUN_REQUIRED = TRUE` (fresh calibration-12 under the new canon, from zero).
- `FULL_D7_AUTHORIZED = FALSE` (STOP for owner decision before real calibration).

**Status:** `M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_FROZEN_READY_FOR_FRESH_CALIBRATION_OWNER_DECISION`
