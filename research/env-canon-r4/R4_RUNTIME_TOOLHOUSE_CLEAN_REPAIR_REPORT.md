# R4 Runtime-Toolhouse Clean Image Successor — Repair Report

**Mission:** `M17_D7_R4_RUNTIME_TOOLHOUSE_CLEAN`
**Date:** 2026-10-14
**Class:** bounded environment repair (instrumentation/environment only — no scientific-method change)
**Verdict:** `PASS_RUNTIME_TOOLHOUSE_CLEAN_IMAGES_READY_FOR_CALIBRATION_ATTEMPT6`
**Exact next gate:** `M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_ATTEMPT6`

## Proven defect

Attempt-5 Unit 9 (`vu-eda4e9f82401`, py38) failed the frozen mandatory
`RUNTIME_TOOLHOUSE_CONTAMINATION` gate with `toolhouse_present = ["wheel"]`.
The calibration install did **not** install `wheel` (`wheel` absent from
`requirements-lock.txt`, absent from `install.log`, `install_rc=0`,
`pipcheck_rc=0`, native probes PASS, smoke PASS): `wheel` is **pre-existing** in
the qualified py38/py39 execution images.

Frozen `BUILD_TOOLHOUSE_ONLY_DISTS = {vcs-versioning, poetry-core, setuptools-scm, wheel}`.
The frozen contract forbids these distributions from the final runtime
environment, so the gate fired correctly. The py312 images are toolhouse-clean;
the py38/py39 images are not.

## REPAIR-1 — bounded full binding audit

11 unique execution images across the frozen 144-unit population (metadata only,
`--network=none`):

| decision | count | images |
|---|---|---|
| CLEAN | 7 | all py312 (incl. the py312 composite) |
| NEEDS_TOOLHOUSE_CLEAN_SUCCESSOR | 4 | `nat-62bc3631c27d` (py38), `nat-d35546f097f4` (py39), `nat-d7d5ae76a87f` (py39), `nat-f65b9bf250fd` (py39) |
| STOP_OWNER_REVIEW | 0 | — |

Only `wheel` is present; no contamination beyond the frozen set.

## REPAIR-2 — closure safety audit

All 219 frozen mapped-task locks scanned: **0** occurrences of any
`BUILD_TOOLHOUSE_ONLY_DISTS` distribution (raw regex also 0). `wheel` is
pre-existing image contamination, **not** a frozen runtime requirement.

## REPAIR-3/4 — qualified repair semantics + build

Additive transformation, local parent only, no network/pull/apt/dependency change:

```
FROM <exact existing qualified image>
RUN python -m pip uninstall -y wheel
```

New deterministic tags (not `:latest`):

| pair | parent image ID | successor ref | successor image ID |
|---|---|---|---|
| dk-py38-bullseye / nat-62bc3631c27d | `sha256:a8b198cf…d9caff` | `…nat-62bc3631c27d-runtimeclean:r4-toolhouse-clean-20261014` | `sha256:b3e7e890…6122403` |
| dk-py39-bullseye / nat-d35546f097f4 | `sha256:d6f91088…5f2796` | `…nat-d35546f097f4-runtimeclean:r4-toolhouse-clean-20261014` | `sha256:94246e6b…067ac28` |
| dk-py39-bullseye / nat-d7d5ae76a87f | `sha256:dc6a421b…773233` | `…nat-d7d5ae76a87f-runtimeclean:r4-toolhouse-clean-20261014` | `sha256:8c90d36a…aaec3ae` |
| dk-py39-bookworm / nat-f65b9bf250fd | `sha256:baea6c4b…d86f24` | `…nat-f65b9bf250fd-runtimeclean:r4-toolhouse-clean-20261014` | `sha256:4332cce5…7776523` |

## REPAIR-5 — successor qualification (all PASS)

Per successor: parent ID recorded; Python major/minor unchanged; OS/suite
unchanged; architecture unchanged; native package/probe contract unchanged;
native probes PASS; network unavailable (`--network=none`); `wheel` absent; all
`BUILD_TOOLHOUSE_ONLY_DISTS` absent; `pip check` PASS; installed distribution
set == parent set **minus exactly `wheel`** (no additions, no version changes);
parent image ID invariant; all unrelated qualified image IDs invariant.

## REPAIR-6 — successor binding

`research/env-canon-r4/R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json`
(key `(docker_profile_id, native_profile_id)`; clean bindings retain existing
IDs; only the 4 contaminated pairs map to successors; no unit/task special
cases). Successor semantic hash: `5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2`.
Accounting: 11/11 pairs, 144/144 units, no missing/duplicate/ambiguity/fallback.

## REPAIR-7 — bounded N12 readiness

Units 1–8 → existing unchanged py312 images; Unit 2 → py312 composite; Unit 9 →
py38 runtime-clean successor; Units 10–12 → py39 runtime-clean successors.
PASS. No behavioral calibration executed.

## Frozen invariance

R4-D plan, exact N12, source-fidelity, E2/E3, recovery overlay, R4-C symlink
successor, wheelhouses, R3 gate semantics, `BUILD_TOOLHOUSE_ONLY_DISTS`, Python
versions, dependency closures, native-profile contracts, and all original
qualified Docker image IDs — **UNCHANGED**. No network, no pull, no apt, no
dependency change, no image mutation/retag/delete.

## Evidence

- `research/env-canon-r4/R4_RUNTIME_TOOLHOUSE_IMAGE_AUDIT.json`
- `research/env-canon-r4/R4_RUNTIME_TOOLHOUSE_CLEAN_REPAIR_RECEIPT.json`
- `research/env-canon-r4/R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json`
- `research/env-canon-r4/R4_RUNTIME_TOOLHOUSE_CLEAN_REPAIR_REPORT.md` (this file)