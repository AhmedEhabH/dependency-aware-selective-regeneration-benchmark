# R4 Native-Image Composition Census

- Mission: `M17_D7_R4_NATIVE_IMAGE_COMPOSITION_CENSUS`
- Branch: `parallel/d7-r4-native-image-composition-2026-10-13`
- Starting HEAD: `4c1ec32cdff48afecd77970c32e210d756f979a6`
- Population identity SHA-256: `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac`
- Units: **144** / tasks: **219**
- Strata: {"3.12_poetry": 25, "3.12_uv": 21, "3.8_poetry": 15, "3.9_poetry": 83}

## Docker profiles

| docker_profile_id | base image | era | python |
|---|---|---|---|
| dk-py312-bookworm | envcanon/saleor-env-base-py312-bookworm:latest | py312 | 3.12 |
| dk-py38-bullseye | envcanon/saleor-env-base-py38-bullseye:latest | py38 | 3.8 |
| dk-py39-bookworm | envcanon/saleor-env-base-py39-bookworm:latest | py39 | 3.9 |
| dk-py39-bullseye | envcanon/saleor-env-base-py39-bullseye:latest | py39 | 3.9 |

## Native profiles

| native_profile_id | current native image | era | python | packages |
|---|---|---|---|---|
| nat-02b9bb45ba01 | envcanon/saleor-env-native-nat-02b9bb45ba01:latest | py312 | 3.12.15 | 12 |
| nat-0728db662cde | envcanon/saleor-env-native-nat-0728db662cde:latest | py312 | 3.12.15 | 13 |
| nat-34c1a3756742 | envcanon/saleor-env-native-nat-34c1a3756742:latest | py312 | 3.12.15 | 11 |
| nat-591718dce38a | envcanon/saleor-env-native-nat-591718dce38a:latest | py312 | 3.12.15 | 11 |
| nat-62bc3631c27d | envcanon/saleor-env-native-nat-62bc3631c27d:latest | py38 | 3.8.20 | 9 |
| nat-a39687f3d19c | envcanon/saleor-env-native-nat-a39687f3d19c:latest | py312 | 3.12.15 | 12 |
| nat-cc2f641e9e04 | envcanon/saleor-env-native-nat-cc2f641e9e04:latest | py312 | 3.12.15 | 14 |
| nat-d35546f097f4 | envcanon/saleor-env-native-nat-d35546f097f4:latest | py39 | 3.9.23 | 14 |
| nat-d7d5ae76a87f | envcanon/saleor-env-native-nat-d7d5ae76a87f:latest | py39 | 3.9.23 | 13 |
| nat-f65b9bf250fd | envcanon/saleor-env-native-nat-f65b9bf250fd:latest | py39 | 3.9.25 | 14 |

## Composition classification

- COMPOSITION_MATCH: **143**
- COMPOSITE_IMAGE_REQUIRED: **1**
- AUTHORITY_AMBIGUOUS: **0**
- INVALID_FROZEN_MAPPING: **0**
- UNKNOWN: **0**

## Cross-era native profiles

- Cross-era native-profile count: **1**
- Exact cross-era native profiles: ["nat-f65b9bf250fd"]

## Missing composite images

- Missing composite-image count: **1**

- `(dk-py312-bookworm, 3.12, py312, nat-f65b9bf250fd)`
  - required parent base: `envcanon/saleor-env-base-py312-bookworm:latest`
  - affected units: `vu-692af9112c6d`
  - reuse blocked: current native image envcanon/saleor-env-native-nat-f65b9bf250fd:latest is py39 (python 3.9.25); cannot satisfy py312/3.12 semantics

## Known blocker diagnosis

- vu-692af9112c6d blocker confirmed: **True**

## Repair recommendation (not implemented)

- Execution image identity: `(docker_profile_id, native_profile_id)`

## Deterministic semantic hash

`8478d05ac2aa75be995a25b62a06effffc6d61563f206f74474cbb9b891fe633`

## Verdict

**PASS_COMPOSITE_REPAIR_SCOPE_FROZEN**

Next gate: **M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR**
