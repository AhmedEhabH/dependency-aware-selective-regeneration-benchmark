# Track 1.2 — R7 scoped F2P control evidence (2026-10-27)

**Gate verdict: R7_SCOPED_F2P_CONTROL_PASS.** This is *not* a full M02-Q environment qualification, an M02-E competitor result, or generated-code end-to-end validation.

## Verified run identity

- Task: `saleor-rc-7e42fc67ce72` (one Saleor task; three frozen F2P pytest nodes).
- Runner: original frozen R7 F2P pilot; `R7_FIRST_RM_CSS_F2P_BEHAVIORAL_RESULT_RECORDED_NOT_E2E`.
- UTC window: `2026-10-27T08:26:05.801327Z` through `2026-10-27T08:43:59.558317Z` (~17 min 54 sec).
- Frozen plan SHA-256: `62ef73588d302553596b9eb6161f03df5a4fe0df4c131390a9b61138754ac401`.
- Stage Git HEAD: `22d569464fdbf9d0ebda842497cc23a7a10e2237` (the stage runner has separately pinned stage-file hashes).
- Original local archive name: `M19B_R7_F2P_PILOT_20261027T082605801327Z_f32b72b6.zip`; SHA-256 of uploaded archive: `6018e0e62c20ed352143ccfb218e9d37f9a5a72ca87cedeb507631ba854969bf`.
- `R7_PILOT_REPORT.json` SHA-256: `c5a87141e200dc4dee07126a0fc793dfbc36c064b0d6d848f5e5cd0304c43641`.
- `SHA256SUMS.txt` SHA-256: `9334c9ea449e14bb0ff190ef11f17575f00b7a2b7a95c11b316e90b3422b5715`.

## Actual fresh outcomes (raw JUnit XML verified)

| State | Expected classification | Observed XML files | Actual result | Physical pytest invocations |
|---|---|---:|---|---:|
| NEG | `FAIL_ASSERTION` | 9 | 9/9 pytest failures as expected; 0 infrastructure/collection errors | 9 |
| FULL_REFERENCE | `PASS` | 9 | 9/9 PASS | 9 |
| RM_CSS | `PASS` under frozen selected-file transfer | 9 | 9/9 PASS | 9 |
| **Total** | — | **27** | **27/27 classifications agree** | **27** |

Manifest verification: **71/71 listed archive-file SHA-256 values match**. Each of the 27 JUnit file digests also matches its corresponding report entry. Each JUnit file contains one test case. Negative-run pytest failures are the intended regression-control behavior, not a qualification failure.

## Environment evidence and limitations

- Frozen tree materialization passed for NEG, FULL_REFERENCE, and RM_CSS at recorded OIDs; each state used its own PostgreSQL database and logs report `db_absent=true` after teardown.
- Container logs show the two specified external-egress probes were blocked, and isolated PostgreSQL TCP probe succeeded; this is bounded probe evidence, **not proof that all possible egress paths were measured**.
- Test container used Python 3.12.15 and pytest 8.4.2; the earlier Windows process-local import-path preflight used Python 3.11.9. Do not conflate these environments.
- Source-run report declares `scientific_independent_repetitions=false`. These are **three nodes repeated three times within one task**, not 27 independent tasks or replications, and not a population-wide outcome.
- P2P preservation controls (103 nodes in the scoped prior protocol) **were not run in this execution**.
- RM_CSS arm transferred reference code only to the frozen selected-file scope. **No LLM-generated code or full E2E regeneration was evaluated**. No independent estimate of model success, fair-arm superiority, or end-to-end cost follows.
- Logs show `NO_LOCKED_DEV_GROUP` while the structured report records an exact frozen+dev installation mode; resolve this provenance detail in environment audit before broad M02-E claims. It does not change the 27 observed JUnit classifications.
- Benchmark/model-generation API calls: zero; benchmark API cost: USD 0.00. Peak RAM and complete network byte accounting: NOT_MEASURED.

## Next gated work (not authorized by this document)

1. Decide whether M02-Q requires the frozen P2P preservation set and further qualified isolated environment receipts beyond the scoped R7 F2P result. Preserve R7 as a valid **scoped** behavioral control milestone.
2. Validate arm identity, matching information rights and budgets, paired task cohorts and test-oracle coverage before each prospective comparator arm.
3. Obtain an explicitly bounded, separate M02-E researcher authorization, specifying arm batch, tasks, provider route, maximum USD/token budget, stop rules and exclusive resource window. Option B `REUSE_NOT_PERMITTED` requires independent physical execution for each arm.
4. Keep this file in `docs/track12/` on branch `docs/track12-m01d-m02q-evidence-20261027` under draft PR #1. No automatic merge and no raw evidence publication to the public repository.

**Claims boundary:** `R7_SCOPED_F2P_CONTROL_PASS` only; **M02-E comparator outcomes NOT_RUN** and **full E2E unproven**.
