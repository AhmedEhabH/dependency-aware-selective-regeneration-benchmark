# M17 source-fidelity fresh calibration-12 report

- **Mission:** `M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12`
- **Status:** `N_EXECUTED=12 N_PASS=12 N_FAIL=0`
- **Result:** `PASS_READY_FOR_FULL_D7_OWNER_DECISION`
- **Freeze commit:** `f5f4c1d0ecae135f3b687bf8b9d27ffd150b6338`
- **Freeze tag:** `m17-env-source-fidelity-r1-frozen-2026-10-12` (peels to `f5f4c1d0ecae135f3b687bf8b9d27ffd150b6338`)
- **Plan SHA256:** `a7617c287a77546ea3a085f4d1fa7115f85fa5988de669419d80677e4ee546bd`
- **Harness freeze SHA256:** `ad8130941391aad2a0575221373651fbfb138f694122f3cd901c59639f68ab35`
- **Selection rule:** `FIRST_12_FROZEN_ORDER`

## Ordered 12-member identity

1. `vu-e4998719ee01`
2. `vu-b68ee1b3ad18`
3. `vu-262f45bffe92`
4. `vu-db74b3640c98`
5. `vu-e878163db06a`
6. `vu-422bca69f329`
7. `vu-117d7bd068d5`
8. `vu-5321e03160a1`
9. `vu-0d8ddec94417`
10. `vu-561a1a172143`
11. `vu-e40f7e955c05`
12. `vu-b9808f19ace4`

## Per-unit summary

| # | unit | class | sf_change | elapsed_s | network | install | pipcheck | native | smoke |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `vu-e4998719ee01` | PASS | False | 397.0 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 2 | `vu-b68ee1b3ad18` | PASS | False | 240.3 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 3 | `vu-262f45bffe92` | PASS | False | 248.4 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 4 | `vu-db74b3640c98` | PASS | False | 307.99 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 5 | `vu-e878163db06a` | PASS | False | 837.17 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 6 | `vu-422bca69f329` | PASS | False | 246.71 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 7 | `vu-117d7bd068d5` | PASS | False | 475.8 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 8 | `vu-5321e03160a1` | PASS | False | 264.3 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 9 | `vu-0d8ddec94417` | PASS | False | 242.15 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 10 | `vu-561a1a172143` | PASS | False | 453.04 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 11 | `vu-e40f7e955c05` | PASS | False | 420.83 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |
| 12 | `vu-b9808f19ace4` | PASS | True | 236.61 | NETWORK_UNAVAILABLE | PASS | PASS | PASS | PASS |

## Unit 12 (affected, previously failed) evidence

- old R3 closure identity: `52a2ef9e817a0790b2d58e8aa018dc34aa98d9b921730167b8edc6838d4e91a4`
- new source-aware closure identity: `7bf871f278d8c5008682a8203be8835fcb643f9e471c5c43700cd914fa2cb1bd`
- SOURCE_FIDELITY_CHANGE_APPLIED: `True`
- selected artifacts: `{"PyXB==1.2.5": "ee196b69018cf9833f0210d050d8ae544070353a92d490a713be4e8347965aee", "authorizenet==1.1.4": "ba04a34ddba7496d778a458f8023ef597918b301b0824ad0517feed35c727ca9"}`
- pytest --collect-only rc: `0`
- smoke status: `PASS`

## Scientific invariants

- CALIBRATION_MEMBERSHIP_CHANGED = FALSE
- CALIBRATION_ORDER_CHANGED = FALSE
- PYTHON_VERSION_CHANGED = FALSE (all 3.12)
- TASK_ELIGIBILITY_CHANGED = FALSE
- SCIENTIFIC_POPULATION_CHANGED = FALSE
- SMOKE_GATE_CHANGED = FALSE (frozen R3 harness byte-exact)
- R3_HARNESS_MUTATED = FALSE
- PYXBX_USED = FALSE
- NETWORK_USED = FALSE (--network=none, NETWORK_UNAVAILABLE)
- PREVIOUS_FAILED_EVIDENCE_MODIFIED = FALSE
- SOURCE_FIDELITY_RULE_GENERIC = TRUE (source-type-driven, no task-ID branch)

## Material cost

- benchmark/model API calls: 0
- external model calls: 0
- downloads: 0
- package-index access: 0
- docker pulls: 0
- network acquisition: 0

