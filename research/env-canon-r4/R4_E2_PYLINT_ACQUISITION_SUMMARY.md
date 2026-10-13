# R4-E2 Pylint Official PyPI Acquisition — Summary

- Mission: `M17_D7_R4_E2_PYLINT_OFFICIAL_PYPI_ACQUISITION`
- Branch: `parallel/d7-r4-e-bounded-artifact-recovery-2026-10-13`
- Starting HEAD: `d56f125f88806cb051d431108c4a99766af0ff59`
- Upstream E1 plan SHA-256: `731d71817051a1f5154b1853c7cc74ba95dc2e309b31e5b464c26dbbdf283baa`
- Target: CPython 3.9 / linux / x86_64 (R4-A compatible)

## Result

**PASS 28/28** — all 28 exact owner-authorized pylint wheels acquired, verified
and promoted to the additive R4-E overlay.

## Counts

| gate | result |
|---|---|
| Metadata resolved (pypi.org) | 28/28 |
| Compatible wheel selected (R4-A) | 28/28 |
| Downloaded (files.pythonhosted.org) | 28/28 |
| SHA-256 verified | 28/28 |
| Structural + identity verified | 28/28 |
| R4-A compatibility | 28/28 |
| ZIP integrity + path safety | 28/28 |
| METADATA name/version | 28/28 |
| Promoted to overlay wheels | 28/28 |

## Network budget

- Metadata requests: **28**
- Artifact requests: **28**
- Downloaded bytes: **12,880,982**
- Downloaded MiB: **12.284262**
- Downloaded GiB: **0.011996349**
- Dependency downloads: **0**
- Retries: **0**
- STOP_OWNER_REVIEW gates hit: **0** (no yanked release, no missing wheel)

## Selected wheels

All 28 selected artifacts are the official pure-Python
`pylint-<VERSION>-py3-none-any.whl` wheels (R4-A compatible).

## Overlay (additive, frozen stores untouched)

- Staging: `D:\wp2_env_store\recovery\r4e_pylint_py39\staging`
- Final overlay: `D:\wp2_env_store\recovery\r4e_pylint_py39\wheels`
- External manifest: `D:\wp2_env_store\recovery\r4e_pylint_py39\manifests\R4_E2_PYLINT_ACQUISITION_MANIFEST.json`
- Frozen wheelhouse/manifest: **unchanged**

## Next gate

`M17_D7_R4_E_AFFECTED_REVALIDATION` (revalidate the 65 affected units with the
recovered exact artifacts).