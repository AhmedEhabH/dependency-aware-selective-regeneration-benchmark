# R4-E1 Pylint Recovery Plan — Owner Review Summary

- Mission: `M17_D7_R4_E1_PYLINT_RECOVERY_PLAN`
- Branch: `parallel/d7-r4-e-bounded-artifact-recovery-2026-10-13`
- Starting HEAD: `b4667fd56738b4d7d069ba88c73a290c201d1628`
- Upstream I6 census SHA-256: `f60668f88b42d8f7aebb6671dba97d705dc8d2bfbed4046ff7e4332361ec9240`
- Population identity SHA-256: `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac`

## Recovery scope (exact, frozen)

- **Exactly 28 versions** of exactly **one package** (`pylint`), no substitution.
- Exactly one target era: **CPython 3.9 / Linux / x86_64**.
- Install route: `REQ_MAIN_PLUS_LOCK_DEV`.
- TRUE_MISSING occurrences: **89**
- Unique identities: **28**
- Affected units: **65**

### Exact ordered recovery identities

- `pylint==2.7.2`
- `pylint==2.7.4`
- `pylint==2.8.1`
- `pylint==2.8.2`
- `pylint==2.9.5`
- `pylint==2.9.6`
- `pylint==2.10.2`
- `pylint==2.11.1`
- `pylint==2.12.2`
- `pylint==2.13.4`
- `pylint==2.13.5`
- `pylint==2.13.8`
- `pylint==2.13.9`
- `pylint==2.14.3`
- `pylint==2.14.5`
- `pylint==2.15.2`
- `pylint==2.15.3`
- `pylint==2.15.4`
- `pylint==2.15.5`
- `pylint==2.15.8`
- `pylint==2.15.10`
- `pylint==2.16.1`
- `pylint==2.17.1`
- `pylint==2.17.2`
- `pylint==2.17.3`
- `pylint==2.17.4`
- `pylint==2.17.5`
- `pylint==2.17.7`

## External authority (future acquisition ONLY)

- Metadata origin: `https://pypi.org/`
- Artifact origin: `https://files.pythonhosted.org/`
- Metadata endpoint template: `https://pypi.org/pypi/pylint/<EXACT_VERSION>/json`
- Wheel compatibility authority: `R4-A`
- No dependency downloads. No version substitution. No "latest".
- No sdist auto-build: sdist fallback is `OWNER_REVIEW_REQUIRED`.

## Store design (additive overlay only)

- Recovery root: `D:\wp2_env_store\recovery\r4e_pylint_py39`
- Staging (network downloads land here): `D:\wp2_env_store\recovery\r4e_pylint_py39\staging`
- Final overlay (wheels after full verification): `D:\wp2_env_store\recovery\r4e_pylint_py39\wheels`
- Recovery manifest path: `D:\wp2_env_store\recovery\r4e_pylint_py39\manifests`
- Frozen wheelhouse: `D:\wp2_env_store\wheelhouse\py39`
- Frozen manifest: `D:\wp2_env_store\manifests\WHEELHOUSE_HASHES_py39.json`
- Frozen wheelhouse/manifest are read-only and NEVER a recovery destination.
- No overwrite of an existing artifact unless byte-identical and recorded by the same recovery manifest.

## E1 status (this planning phase)

- `network_used`: false — **no network performed in E1**.
- `artifacts_downloaded`: 0.
- `Docker_used`: false; `Full_D7_executed`: false; `behavioral_calibration_executed`: false.
- Frozen I6 evidence and frozen store are unmutated.
- Acquisition status: **`PLANNED_AWAITING_OWNER_NETWORK_APPROVAL`**

## Next action

Requires **explicit owner authorization** before any external acquisition (E2) may start.

Plan SHA-256: `731d71817051a1f5154b1853c7cc74ba95dc2e309b31e5b464c26dbbdf283baa`
