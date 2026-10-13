# R4-I6 Corrected Zero-Container Census — Summary

- Mission: `M17_D7_R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144`
- Branch: `parallel/d7-r4-i6-corrected-census144-2026-10-13`
- Starting HEAD: `e62675d6dcbec327f393ca42cd924258dbe9402a`
- Population identity SHA-256: `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac`

## Population processing

- Units processed: **144/144**
- Mapped tasks processed: **219/219**
- Strata: {'3.12_poetry': 25, '3.12_uv': 21, '3.8_poetry': 15, '3.9_poetry': 83}

## Dependency terminal classification

| classification | count |
|---|---|
| AVAILABLE_COMPATIBLE_WHEEL | 49299 |
| EDITABLE_SELF_NOT_THIRD_PARTY | 35 |
| EXCLUDED_BY_TARGET | 1011 |
| SOURCE_FIDELITY_OVERLAY_RESOLVED | 4 |
| TRUE_MISSING_ARTIFACT | 89 |

## TRUE_MISSING_ARTIFACT

- Occurrence count: **89**
- Unique package/version/source count: **28**
- Affected units: **65**

### Exact true-missing identities

- `pylint==2.10.2`
- `pylint==2.11.1`
- `pylint==2.12.2`
- `pylint==2.13.4`
- `pylint==2.13.5`
- `pylint==2.13.8`
- `pylint==2.13.9`
- `pylint==2.14.3`
- `pylint==2.14.5`
- `pylint==2.15.10`
- `pylint==2.15.2`
- `pylint==2.15.3`
- `pylint==2.15.4`
- `pylint==2.15.5`
- `pylint==2.15.8`
- `pylint==2.16.1`
- `pylint==2.17.1`
- `pylint==2.17.2`
- `pylint==2.17.3`
- `pylint==2.17.4`
- `pylint==2.17.5`
- `pylint==2.17.7`
- `pylint==2.7.2`
- `pylint==2.7.4`
- `pylint==2.8.1`
- `pylint==2.8.2`
- `pylint==2.9.5`
- `pylint==2.9.6`

## Summary answers

- Processed 144/144 units: **True**
- Processed 219/219 tasks: **True**
- TRUE_MISSING_ARTIFACT occurrence count: **89**
- TRUE_MISSING_ARTIFACT unique identities: **28**
- Affected units: **65**
- Resolved as EXCLUDED_BY_TARGET: **1011**
- Resolved through approved source/sdist: **0**
- Resolved through source-fidelity overlay: **4**
- Semantic ambiguity count: **0**
- Tooling/instrumentation failure count: **0**
- Silent skip count: **0**

## Final readiness decision

**PASS_REQUIRES_R4E_ARTIFACT_RECOVERY**

Next gate: **M17_D7_R4_E_BOUNDED_ARTIFACT_RECOVERY**

## Provenance & constraints

- I5 resolver reused unchanged (parser, RuntimeTarget, wheel compatibility, source-fidelity, canonical identity, local-store resolution).
- Phase I6-0 authority adjudication printed before the census; R4-B lock closure unmodified.
- ZERO Docker CLI, ZERO network, ZERO install/build/behavioral execution.
- Registry digests remain unfrozen (`registry_digests_unfrozen = true`).

Census canonical SHA-256: `8e378c496940119f2e280971e772c0ae4174264ae2bd626a19c16ed06075966a`
