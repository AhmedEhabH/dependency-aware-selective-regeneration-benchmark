# D7 R3 runtime failure — owner review

**Primary classification: C_LOCK_RECONSTRUCTION_DEFECT. Full D7: NO.**

The frozen failure is real, but Python 3.12 is historically justified. The historical lock names **vendored directory sources** for both PyXB 1.2.5 and authorizenet 1.1.4. Reconstruction preserved the numeric pins while substituting non-equivalent wheel sources. The historical PyXB already uses `collections.abc.MutableSequence`; the installed frozen wheel uses `collections.MutableSequence`.

## Authority and failure reconstruction

The source store is read-only: `D:\wp2_env_store`. Its receipt `receipts/D7_R3_CALIBRATION_12_RECEIPT.json` and report `reports/D7_R3_CALIBRATION_12_REPORT.md` record BLOCKED_STOP, 12 executed, 11 PASS, 1 failure: `vu-b9808f19ace4`, task `saleor-rc-e6198146186d`. The selection plan is FIRST_12_FROZEN_ORDER. All 10 files named by `manifests/D7_R3_HARNESS_FREEZE.json` match their frozen hashes (manifest itself checked using the receipt's actual-file hash, distinct from its skeleton self-hash).

Existing `tmp/d7_r3_cal_out/vu-b9808f19ace4/pytest_wt0.log` proves:

```
saleor/payment/gateways/authorize_net/__init__.py:4
 -> authorizenet/apicontractsv1.py:9
 -> pyxb.binding -> datatypes.py:1243 -> content.py:807
 -> class _PluralBinding(collections.MutableSequence)
 -> AttributeError; pytest rc=2; 13245 tests collected, 1 collection error
```

`install.log` says Python 3.12.15; `pipfreeze.txt` records authorizenet==1.1.4 and PyXB==1.2.5. `native.json` has no failures; `netprobe.json` reports NETWORK_UNAVAILABLE. The receipt records import/manage rc=0, pip-check rc=0, collection rc=2. These are historical observed outcomes, not a fresh reproduction. Pip metadata validity and successful native gates do not establish source fidelity or whole-instrument validity.

## Runtime provenance (R2)

Local repository: `C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor`.
Target commit: `e6198146186d1c782bf46f6c9439fa05b1049b2f`, author/committer date **2024-09-16T10:23:42+02:00**.

`TARGET_COMMIT_EVIDENCE.json` records line-numbered excerpts and exact Git blob SHA-256 values. At that commit:

- `pyproject.toml`: `tool.poetry.dependencies.python = "~3.12"`.
- `Dockerfile`: `FROM python:3.12 AS build-python`, later `python:3.12-slim`; vendored directory copied before dependency installation.
- `.github/workflows/pytest.yml`: container `python:3.12` and Poetry installation.
- `poetry.lock`: metadata Python range `~3.12`, lock format 2.0. Package-level `python-versions = "*"` for the two vendored packages does not override project-level requirements.
- No root `setup.py`, `tox.ini`, or `runtime.txt` recovered at the target; vendored setup files are separately recorded.

Assignment chain: target declaration -> frozen `m17-posteligibility-dev/research/wp2/m17_v1/r2b/environment/ENVIRONMENT_MATRIX_248.json` (`per_task[task_id]`: era py312, matching Python/CI evidence, no role conflict) -> `D:\wp2_env_canon\scripts\env_canon_phase_a_generate.py` (reads per-task era; ERA_TO_PY maps py312 to 3.12) -> store `TASK_ENV_MATRIX.csv` -> `VALIDATION_UNIT_MATRIX.csv` -> `D7_CALIBRATION_12_PLAN.json` -> receipt. The repository's `src/benchmark/wp2/era_resolver.py` also explicitly maps ~3.12 / >=3.12,<3.13 and rejects unknown requirements; it corroborates the rule, rather than being assumed to be the Phase-A executable.

Classification **HISTORICAL_RUNTIME**, at Python minor-version level. Bookworm/base-image and patch-version normalization remain distinct. No evidence supports downgrading this task to 3.9.

| Population denominator | Explicitly supports 3.12 | Explicitly excludes 3.12 | Unknown |
|---|---:|---:|---:|
| 144 validation units (all members agree) | 46 | 98 | 0 |
| 219 member task commits | 77 | 142 | 0 |

All 46 assigned-3.12 units are in the support group. Other units use their declared 3.8/3.9 era. Counts are declarations, not proof of runtime success. `HISTORICAL_RUNTIME_BY_TASK.json` cites each exact commit/pyproject hash; `D7_RUNTIME_BLAST_RADIUS.csv` maps every member back to its unit.

## Dependency provenance (R3)

Both dependencies are **direct project path dependencies**; authorizenet additionally depends transitively on `pyxb==1.2.5`. The historical Poetry lock retains `develop=true`, `source.type=directory`, and URLs `vendored/authorizenet` / `vendored/pyxb`. Neither is merely a generic registry pin.

The frozen lock equals original Git blob bytes exactly. Raw SHA-256 is `95884b5108283b7929da9adf82afde2532d5de6eb7ef58287cac067154298137`. The plan's `5ac46a7ec1a90deb4fb152a7a10bb3e115c6ddc126aaa6c75b2a138f075822bf` is SHA-256(raw + LF), a documented E1/Phase-A convention. This is not lock tampering.

The provenance loss occurs downstream: Phase-A `parse_poetry_lock` emits name/version/python marker with generic source_type `poetry.lock`; `harness/d7_r3/d7_r3_closure.py::poetry_pins` emits `name==version`, and `resolve_runtime_artifacts` matches wheels by those fields. `tmp/d7_r3_calibration_driver.py` writes runtime pins (line 139) and installs them with offline `uv pip install ... -r requirements-lock.txt` (line 248). A route label does not restore omitted source provenance.

The py312 canon PyXB wheel SHA is `52a256ce138aa2a4031a86789ba8edbe5379eb4ca96391eb4c572092894092d9`, independently matching `receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json`. Its source is the registry sdist plus the approved find_spec backport, per `manifests/R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json`. The py312 authorizenet wheel SHA is `d5e8d38de4c7ac6c4e8d2cbe190fcbb5427995c9da760ba3eba60e0faaa94e36`.

`SOURCE_FIDELITY_COMPARISON.json` proves the historical PyXB content.py hash is `2a4b80093dcddb99a5a5db201143b130d69a332b69bf7ee596e633f051aea7ff`, versus frozen wheel `b873d3dc679b30fbb6696ad9e77325823912f19ca7e91f8958632a7e571c8025`. Its two changed common Python files are content.py and six.py; file-set differences also exist. Five of six common authorizenet Python files differ from the historical vendor tree. Byte differences establish non-identity, not necessarily a distinct failure for every changed file.

## Local wheels and prior amendment (R4)

`LOCAL_WHEEL_AUDIT.json` records filenames, raw hashes, metadata, top-level imports and inspected expressions for all six relevant wheels, including the older py39 canon. Both PyXB-X 1.2.6.2 and 1.2.6.3 export `pyxb` and use `collections.abc.MutableSequence`; their content.py equals the historical file. Full distribution equivalence is not established: distribution names/versions and Python file inventories differ. PyXB-X does not satisfy a `PyXB==1.2.5` distribution requirement merely by exporting the same import name. Co-installation would also risk overlapping modules.

All inspected PyXB/PyXB-X and authorizenet wheels omit Requires-Python. This supplies no safety restriction and is too weak to prevent the observed install/runtime mismatch; a `py3-none-any` tag is not proof of compatibility with every Python 3 release.

PyXB-X hashes match `WHEELHOUSE_HASHES_py312.json`: 1.2.6.2 = `7d130e824c9e08acc3d43a0b454a48613588b27cee09d9f34d947081a92691e2`; 1.2.6.3 = `4c4a55d6b8c61c2d84ab4c2cb49ee74185599242bbfd1cf0bdd6be4a8a874006`. Presence in that manifest authorizes no substitution. The prior approved exception was **PyXB 1.2.5 find_spec only**, with no unrelated edits, not PyXB-X and not the MutableSequence change. No wider approval was found in the reviewed frozen authorities.

## Blast radius and conservative limits (R5–R6)

| Static property | Units / 144 |
|---|---:|
| PyXB==1.2.5 present | 84 |
| authorizenet==1.1.4 present | 75 |
| Same lock as failing unit | 1 |
| V2_EDITABLE_PLUS_LOCK_DEV | 19 |
| Assigned Python 3.12 | 46 |
| Python 3.12 + PyXB 1.2.5 + directory-source mismatch | 2 |

The two directly exposed units are `vu-b9808f19ace4` / `saleor-rc-e6198146186d` and `vu-692af9112c6d` / `saleor-rc-19bb9b070965`. Both historical content.py blobs contain the compatible expression. The second unit is **potentially affected**, not newly executed or proven failed. Exactly these two Poetry locks contain directory-source packages. Authorizenet is an additional proven source-fidelity concern within the same pair. No additional package/runtime failure is asserted solely from age, universal wheel tags, or missing metadata. This audit is not an exhaustive compatibility proof for the remaining packages or units.

A is rejected because the expected historical artifact was not reconstructed. B is rejected because declared runtime evidence supports the assignments. C fits source-identity loss despite unchanged numeric pins. D is rejected because legitimate test collection encounters a real import error. E is unnecessary because local evidence suffices.

## Required answers and next action

**1 why unit12 failed** — The frozen wheel contains collections.MutableSequence and fails during authorize_net pytest collection under CPython 3.12.15. The target commit instead vendors PyXB code using collections.abc.MutableSequence. Name/version-only reconstruction discarded that source identity.

**2 was r3 harness correct** — G7 correctly failed closed on pytest rc=2; all 10 frozen harness-file hashes match. However, the shared closure representation and calibration install route do not preserve directory-source identity. Correct failure detection does not establish historically faithful environment reconstruction or global harness validity.

**3 was python312 justified** — YES at the minor-version level: target commit dated 2024-09-16 declares ~3.12, Dockerfile and pytest CI use Python 3.12, lock metadata requires ~3.12. HISTORICAL_RUNTIME. D7 uses normalized bookworm image/3.12.15 patch; this is not a claim of bit-identical historical OS or patch version.

**4 narrow or systemic** — Primary C_LOCK_RECONSTRUCTION_DEFECT, specifically loss of dependency source identity rather than a changed numeric pin. Mechanism is systematic name/version flattening; the statically proven directory-source exposure is bounded to two D7 units. Not evidence of a population-wide Python-era assignment defect.

**5 population affected** — 2/144 units (2/219 tasks) share Python 3.12 plus vendored PyXB 1.2.5 source-loss exposure. Only Unit 12 has the observed failure here. 84 units contain PyXB 1.2.5 overall; 75 contain authorizenet 1.1.4; 1 shares the failing lock; 19 use V2_EDITABLE_PLUS_LOCK_DEV; 46 use 3.12.

**6 pyxbx valid replacement** — NOT established or authorized. Both local PyXB-X versions fix the observed expression and provide pyxb, but have different distribution identity/version and package file sets. authorizenet requires pyxb==1.2.5. Shared import name and one identical source file do not establish distribution or scientific equivalence.

**7 exclusion defensible** — NO ad hoc exclusion. Prior PYXB_DISPOSITION_R4X_DELTA finds no unambiguous existing eligibility rule for this defect. Any new population-wide rule needs prospective owner approval, disclosure of observed failure, population accounting and recalibration; it cannot retroactively become predeclared.

**8 recalibration required** — YES before release qualification of any corrected canon: rerun all frozen 12 from zero after a separately approved additive correction/refreeze. Full D7 must begin from zero for the new canon; do not reuse results across identities. This is a recommendation for owner approval, not execution authority.

**9 full d7 authorized** — NO

Review `RUNTIME_REMEDIATION_DECISION_MATRIX.md`. The preferred owner decision is an additive **source-faithful reconstruction amendment**, keeping Python 3.12 and restoring both exact commit-local vendor identities, followed by source-provenance validation and full 12-unit recalibration. This is an additional evidence-led option; none of the five generic options alone addresses the defect. No remediation is implemented or authorized by this packet.

## Reproduction and validation boundary

Run `python -B research/env-runtime-audit-r1/audit_static.py`, then `python -B research/env-runtime-audit-r1/audit_source_fidelity.py` in this checkout to regenerate static evidence. These commands read local Git objects and store files, and write audit artifacts only. Do not invoke the calibration driver. `P2P_F2P_RECEIPT.json` and `VALIDATION_RECEIPT.json` record the final review checks; input rehashing is in `INPUT_IMMUTABILITY_RECEIPT.json`.

The mission-specific LIGHT package excludes repositories, wheel payloads and large raw logs, superseding the generic full-project export content rule. The existing store and all frozen harness files remain untouched. The final stop report is `STOP_REPORT.md`.
