# D7_R3_HARNESS_CONTRACT

**Mission:** `M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE`
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY — no scientific
result, no RQ evidence)
**Branch:** `parallel/env-canon-2026-10-09` · **HEAD:**
`1661ec215ede6ae96e82735148db4febffb21580`
**Canonical store:** `D:\wp2_env_store` · **Harness dir:** `harness\d7_r3\`

This document is the frozen contract of the D7_R3 validation harness.  R3 is an
ADDITIVE engineering correction of the frozen R2 harness
(`harness\d7_r2`), which remains immutable failed-calibration evidence and is
NEVER repaired in place.

R3 corrects only harness engineering probe-spec metadata whose falsity was
proven by the real `D7_R2_CALIBRATION_12` mission (BLOCKED_STOP on the first
unit: NATIVE_FAIL) and independently reproduced here under `--network=none`
against the exact frozen images (evidence: `tmp/d7_r3_out/probes/D7_R3_NATIVE_SPEC_AUDIT.json`).

---

## 0. Scope gate

This mission:

- corrects and freezes the D7 validation harness ONLY (additive R3);
- never executes any of the frozen 12 real calibration units;
- never runs Full D7, D8, D9, D10, MAIN Oracle, READY, or OPWS;
- never performs a new source build, Docker pull, or network acquisition;
- makes no scientific change (`SCIENTIFIC_CHANGES = NONE`).

The real 12 remain untouched until a separate owner-authorized
`D7_R3_CALIBRATION_12` mission.

---

## A. Input authority

D7_R3 consumes only frozen, hash-verifiable inputs (identical to R2):

1. **Frozen validation-unit matrix** — `manifests/VALIDATION_UNIT_MATRIX.csv`
   (144 units) and `manifests/D7_CALIBRATION_12_PLAN.json` (12-unit subset,
   `FIRST_12_FROZEN_ORDER`, no cherry-picking).
2. **Frozen locks** — `artifacts/locks/<task>_poetry.toml` (SHA-256 pinned in
   the plan).
3. **Final-R4B canonical wheels** — `built_wheelhouse/canon_r4b/<era>/**`
   (215/215 accounting: 214 canonical + 1 approved compatibility backport).
4. **Approved wheelhouse artifacts** — `wheelhouse/<era>/` per
   `manifests/WHEELHOUSE_HASHES_*.json`.
5. **Approved Docker images** — `manifests/DOCKER_PROFILE_MANIFEST.json`
   (`envcanon/saleor-env-native-nat-*` images).
6. **Native-profile manifests** — `manifests/DOCKER_PROFILE_MANIFEST.json`
   (`native_profiles` per profile), `manifests/NATIVE_DEPENDENCY_MATRIX.csv`,
   `manifests/MARKER_FILTER_AUDIT.json`.

The build-toolhouse (`manifests/R4B_FINAL_BUILD_TOOLHOUSE.json`) is an
authoritative *build-stage* manifest only; it is NEVER an input to the D7
runtime install.

---

## B. Network

Every D7 execution container:

```
--network=none
```

- No PyPI, no GitHub, no apt, no resolver download, no Docker pull, no
  package download.
- The V2 network probe inside the container MUST report
  `NETWORK_UNAVAILABLE`.
- Any network-reachable / fetch-capable outcome is `NETWORK_FAIL_CLOSED`.

---

## C. Runtime environment

The final runtime environment contains ONLY:

- the unit's frozen runtime closure packages, and
- legitimate transitive runtime dependencies of that closure.

**Build-toolhouse-only distributions MUST NOT contaminate the runtime
environment** (vcs-versioning, poetry-core, setuptools-scm, wheel). The harness
audits the runtime environment against the frozen build-toolhouse-only dist
name set and fails closed if any is present (`RUNTIME_TOOLHOUSE_CONTAMINATION`).

```text
SOURCE-BUILD CANON
    -> frozen canonical wheels
    -> D7 runtime wheel input
    -> clean runtime install        (wheel-only, --only-binary=:all:)
    -> pip check / smoke / native probes
```

If a runtime install unexpectedly requires a source build, that is a
`RUNTIME_ARTIFACT_CLOSURE_DEFECT` (FAIL CLOSED).

---

## D. Pip check

`pip check` runs against the FINAL runtime environment on every unit.

- No filtering, no suppression, no exclude-based post-hoc tuning based on
  observed output.
- Any nonzero rc is a genuine `PIP_CHECK_FAIL` (FAIL CLOSED).

---

## E. Native probes (R3-corrected engineering spec)

- Native checks are derived from the unit's exact frozen `native_profile_id`
  (`DOCKER_PROFILE_MANIFEST.json`). Probes of another profile are NEVER run.
- **Soname matching** uses strict EQUALITY against loader-visible names
  (`ldconfig -p` tokens). There is no substring-based optimistic matching.
- **Executable/path probes** use fetch-truth: either an exact frozen absolute
  filesystem path, or (for PATH-resolved executables) a strict EXEC probe that
  requires the executable to resolve on PATH inside the container
  (`command -v <exe>` -> real file). This is the R2_DEFECT_B correction.

R2 -> R3 corrections (each evidence-backed by `D7_R3_NATIVE_SPEC_AUDIT.json`):

| defect | package | R2 spec (wrong) | R3 spec (loader/path truth) |
|---|---|---|---|
| R2_DEFECT_A | `libopenjp2-7` | SONAME `libopenjp2-7.so.7` | SONAME `libopenjp2.so.7` |
| R2_DEFECT_B | `pipx` | PATH `/usr/local/bin/pipx` | EXEC probe (`command -v pipx` -> `/usr/bin/pipx`) |
| R2_DEFECT_C | `libxslt1-dev` | SONAME `libxslt.so.1.1` | SONAME `libxslt.so.1` |

R2_DEFECT_A: the Debian package is `libopenjp2-7`, but its loader-visible SONAME
(and the real ELF DT_SONAME of `libopenjp2.so.2.5.0`) is `libopenjp2.so.7`.  R2
mistook the Debian package-name morphology for a SONAME.

R2_DEFECT_B: pipx is installed by the Debian package `pipx 1.1.0-1` to
`/usr/bin/pipx` and resolves via `command -v pipx`; `/usr/local/bin/pipx` does
not exist in any affected image.  The requirement is "pipx exists on PATH", not
a frozen `/usr/local/bin` absolute path.

R2_DEFECT_C: `libxslt.so.1.1.35` is the versioned FILENAME; the loader-visible
SONAME is `libxslt.so.1`.  R2 encoded part of the filename as if it were a
SONAME.

A profile package without a frozen probe spec is a FAIL CLOSED probe-spec gap
(never silently skipped).

---

## F. Smoke

Preserved D7 smoke semantics per member task, unchanged:

- application import (`import saleor`);
- `manage.py check --settings=saleor.tests.settings` where applicable;
- `pytest --collect-only -q` where applicable.

Classification is not weakened: rc `0` = pass, `SKIP` = skipped, anything else
= `SMOKE_FAIL`.

---

## G. Failure (FAIL CLOSED)

The harness fails closed on ANY of:

1. missing artifact;
2. incompatible wheel;
3. runtime source-build request (runtime-artifact-closure defect);
4. pip-check failure;
5. required native probe failure;
6. network availability / fetch capability;
7. smoke failure.

There is no "proceed with warning" path for a unit.

---

## H. Deterministic synthetic validation (harness freeze)

Before freeze, the harness proves itself with a synthetic P2P/F2P suite
(`d7_r3_validation_driver.py --synthetic`) — deterministic, docker-free,
network-free, NO real calibration unit.

Positive (must PASS): clean wheel-only install; clean pip check; exact native
probes; pipx PATH-resolution exact; no-native profile runs no unrelated probes;
network unavailable under `--network=none`; libxslt corrected-SONAME exact.

Negative (must FAIL CLOSED): build-toolhouse contamination; missing runtime
wheel → source-build request; wrong native-profile probe; incorrect/absent
required SONAME (including the wrong R2-era `libopenjp2-7.so.7` token);
pipx not resolvable on PATH; libxslt absent SONAME; network-visible execution;
deliberate pip-check inconsistency; deliberate smoke failure.

Wheel-tag controls: abi3 wheels (cp37/cp38/cp39) and py3-none-any accepted for
the CPython 3.12 linux x86_64 bookworm target; win_amd64 / macOS / non-abi3
cp311 / future-cp313 wheels rejected.

---

## I. Freeze artifacts

Written at freeze time:

- `manifests/D7_R3_HARNESS_FREEZE.json`
- `receipts/D7_R3_HARNESS_P2P_F2P.json`
- `reports/D7_R3_HARNESS_FREEZE_REPORT.md`
- `harness\d7_r3\D7_R3_HARNESS_MANIFEST.json` (SHA-256 of every harness file,
  self-inclusive after emission)
- `receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json`
- `project-light-year-2026-10-12-r3-<HHmm>.zip` (additive LIGHT <= 50 MiB)

---

## J. R2 immutability / R3 additive boundary

- `harness\d7_r2` is immutable historical evidence. Every R2 manifest-listed
  artifact was SHA-256-recorded at mission start and re-verified unchanged at
  mission end.
- R3 is a separate harness directory (`harness\d7_r3`) with its own manifest,
  hashes, receipts, and reports.
- R3 never imports or depends on R2 modules.
- `D7_R3_CALIBRATION_12` is NOT started by this mission and requires a separate
  owner authorization.

---

## K. Dry closure verification (this mission)

- Exactly 12 units in `D7_CALIBRATION_12_PLAN.json`, `FIRST_12_FROZEN_ORDER`;
- every member of the frozen 144-unit D7 population;
- no substitution / no cherry-picking;
- all 12 runtime closures resolve under R3 (wheel-only);
- all required frozen image identities exist locally;
- all required native profiles have audited R3 specifications.
