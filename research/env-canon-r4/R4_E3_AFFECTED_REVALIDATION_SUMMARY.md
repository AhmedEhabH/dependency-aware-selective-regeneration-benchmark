# R4-E3 Affected Revalidation — Summary

- Mission: `M17_D7_R4_E_AFFECTED_REVALIDATION`
- Branch: `parallel/d7-r4-e-affected-revalidation-2026-10-13`
- Starting HEAD: `00a35c80b4705cb35d0fa763f1724e4fffaacb15`
- Population identity SHA-256: `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac`
- I6 census SHA-256: `f60668f88b42d8f7aebb6671dba97d705dc8d2bfbed4046ff7e4332361ec9240`
- Affected-set SHA-256: `d5ed821a95ce7d8a6adf5655dfd2b62216e4979b30023f225ba8a9a8f27678ea`

## Affected set (frozen I6 derivation)

- Affected units: **65**
- Affected mapped tasks: **89**
- Original TRUE_MISSING occurrences: **89**
- Original TRUE_MISSING unique identities: **28**

## Recovery overlay integrity

- E2 manifest SHA-256: `0ac1fa2bd7b078d99c05a92f90d2dba886454377f7c1d392065e6db4ec8ea902`
- Recovery artifacts verified: **28/28**
- Recovery artifact hash failures: **0**

## Revalidation result

- Affected units processed: **65/65**
- Affected tasks processed: **89/89**
- Exact transitions: **89**
  `TRUE_MISSING_ARTIFACT(pylint) -> RECOVERY_OVERLAY_RESOLVED`
- Non-pylint transitions: **0**
- Remaining TRUE_MISSING occurrences: **0**
- Remaining TRUE_MISSING unique identities: **0**
- Semantic ambiguity: **0**
- Tooling/instrumentation failures: **0**
- Silent skips: **0**

## Invariance & synthesis

- Dependency-classification invariance: **PASS**
- Unaffected units adopted from frozen I6: **79**
- Unaffected tasks adopted from frozen I6: **130**
- Population synthesized: **144/144 units, 219/219 tasks**

## Verdict

**PASS_READY_FOR_BEHAVIORAL_CALIBRATION**

Next gate: **M17_D7_R4_BEHAVIORAL_CALIBRATION_N12**

Deterministic semantic hash: `1eb1d0ae1e8205f034002358fefabb32b61127f9d5f7b1963e55b77cda7ca8dc`
