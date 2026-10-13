# R4 Native-Image Composition Repair — Mission Report

- Mission: `M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR`
- Branch: `parallel/d7-r4-native-image-composition-repair-2026-10-13`
- Starting HEAD: `f3f6c5cb03fc41fedc317742099a1cb51f11e146`
- Pre-build freeze HEAD: `e7856c99c2a9414841e8eebd47b00d75c396d188`
- Census semantic hash: `8478d05ac2aa75be995a25b62a06effffc6d61563f206f74474cbb9b891fe633`

## Verdict

**PASS_READY_FOR_BEHAVIORAL_CALIBRATION_N12**

Next gate: **M17_D7_R4_BEHAVIORAL_CALIBRATION_N12** (NOT started by this mission).

## Repair target (exactly one frozen missing composite)

| dimension | value |
|---|---|
| docker_profile_id | `dk-py312-bookworm` |
| python_version | `3.12` |
| wheelhouse_era | `py312` |
| native_profile_id | `nat-f65b9bf250fd` |
| required parent base | `envcanon/saleor-env-base-py312-bookworm:latest` |
| affected unit | `vu-692af9112c6d` |
| affected task | `saleor-rc-19bb9b070965` |

## Build method authority

- Frozen qualified recipe: `D:\wp2_env_store\dockerfiles\saleor-env-native-nat-f65b9bf250fd.Dockerfile`
  (native package layer) and `D:\wp2_env_store\dockerfiles\saleor-env-base-py312-bookworm.Dockerfile` (base).
- The repair delta is ONLY the base swap `py39 -> py312`; the native apt layer is
  byte-identical to the frozen recipe.
- Package-version policy: **package identities + frozen behavioral probes**
  (name-only apt install, no Debian version pins).

## New composite image

- Ref: `envcanon/saleor-env-native-nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013`
- Immutable ID: `sha256:1be41dd22a934cc56ed10fa1046234a450f6d2946f8099d7bcb501f696f1d759`
- Python: `3.12.15` · OS: Debian bookworm (linux/amd64)
- Parent base: `envcanon/saleor-env-base-py312-bookworm:latest` (`b9e35d98a9b1...`)

## Network

- Owner network authorization present (limited to `deb.debian.org/debian` +
  `deb.debian.org/debian-security`).
- External acquisition: `gettext 0.21-12`, `libgdk-pixbuf2.0-0 2.40.2-2`,
  `mime-support 3.66` + transitive (`gettext-base`, `mailcap`,
  `libgdk-pixbuf-xlib-2.0-0`).
- No Docker pull. All qualification/probe containers used `--network=none`
  (probe result: `NETWORK_UNAVAILABLE`).

## Qualification

- Native probes: 14/14 PASS (frozen R3 harness implementation reused unchanged).
- Required SONAMEs present (libcairo.so.2, libgdk_pixbuf-2.0.so.0, liblcms2.so.2,
  libopenjp2.so.7, libpango-1.0.so.0, libpangocairo-1.0.so.0, libpq.so.5,
  libssl.so.3, libtiff.so.6, libwebp.so.7, libxml2.so.2, libmagic.so.1).
- gettext resolves at `/usr/bin/gettext`; mime paths present.
- No apt lists / no apt archives retained in the image.

## Differential safety

- Existing py39 nat-f65 image unchanged (`baea6c4b01e1...`).
- All 13 other qualified image IDs unchanged (14 total checked, 0 failures).
- Native package sets byte-identical between py39 nat-f65 and py312 composite
  (14/14, same resolved versions).
- Frozen store and frozen repository evidence unchanged.

## General execution-image binding

- Identity model: `(docker_profile_id, native_profile_id)`.
- Unique pairs derived from frozen 144-unit population: **11** (not hardcoded).
- 10 existing pairs -> EXISTING_QUALIFIED_NATIVE_IMAGE; 1 repaired pair ->
  R4_COMPOSITE_REPAIR.
- `(dk-py39-bookworm, nat-f65b9bf250fd)` stays bound to the original py39 image.
- `(dk-py312-bookworm, nat-f65b9bf250fd)` bound to the new composite.
- Deterministic binding hash: `3878e75a7f5f4b676af3633cad5cd64eeab05d4b9155ef9b61b2b8c1dd9607b3`.
- No per-task / per-unit selection exceptions.

## Post-repair composition accounting

- COMPOSITION_MATCH: **144**
- COMPOSITE_IMAGE_REQUIRED: **0**
- AUTHORITY_AMBIGUOUS / INVALID_FROZEN_MAPPING / UNKNOWN: **0**
- missing composite count: **0**
- The original frozen census is immutable; the additive post-repair result is
  `R4_POST_REPAIR_COMPOSITION_CENSUS.json`.

## P2P / F2P

- 32/32 offline tests PASS (`tests/unit/wp2/env_r4/test_r4_native_image_composition_repair.py`).
- All P1..P22 and F1..F20 requirements satisfied.

## Evidence artifacts

- `research/env-canon-r4/docker/nat-f65b9bf250fd-py312-bookworm/Dockerfile`
- `research/env-canon-r4/docker/nat-f65b9bf250fd-py312-bookworm/BUILD_INPUTS.json`
- `scripts/r4_execution_image_composite_binding.py`
- `tests/unit/wp2/env_r4/test_r4_native_image_composition_repair.py`
- `research/env-canon-r4/R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json`
- `research/env-canon-r4/R4_POST_REPAIR_COMPOSITION_CENSUS.json`
- `research/env-canon-r4/R4_NATIVE_IMAGE_COMPOSITION_REPAIR_RECEIPT.json`

External evidence root: `D:\WP2\runs\r4-native-image-composition-repair-2026-10-13`
(freeze/, build/, logs/, probes/, receipts/).

## Prohibited-work accounting

No Behavioral Calibration, no Full D7, no OPWS, no population change, no
dependency-version substitution, no Python-version reinterpretation, no py39
wheelhouse use, no existing image mutation/retag, no frozen evidence mutation.