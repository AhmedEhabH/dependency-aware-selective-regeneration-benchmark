# WP-2 Oracle Confirmation + Causal Design V1 — STOP REPORT (2026-09-22)

## 1. Executive decision

`WP2_ORACLE_PARTIAL_TIMEBOX_COMPLETE`

The WP-2 Oracle Confirmation substrate is validated (8 primary behavioral F2P +
1 symbol-absence F2P confirmed from 220 attempted changed-test candidates), WP-2
causal Design v1 / power planning / Smoke v2 are emitted, but the environment is
the dominant blocker on this Windows host (207/220 ENV_BROKEN) and the confirmed
pool (n=8) is far below the n=60 planning target. No E2E result is claimed.

## 2. Git / origin / public-repo identity

- Branch: `wp2/oracle-confirmation-design-v1-2026-09-22`
- origin: `https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git` — identity matches expected repo; verified before any push.
- HEAD/origin/main at mission start: `2a24621ed7adccacca56abb8ec8bd1d80ae39256` (no reset performed).

## 3. Census terminology: what it means

`Census` = exhaustive structural inspection of the entire 297-task MAIN_297
opened population (not a sample). `Task` = one real Saleor change instance.
`Candidate` has three distinct meanings (impact candidate / F2P candidate /
Smoke candidate) never collapsed. Full definitions in
`docs/WP2_CENSUS_TASK_CANDIDATE_SELECTION_RATIONALE_2026-09-22.md`.

## 4. Why 20/200/77 happened

- **20 STRONG**: target diff ADDS ≥1 test file (clearest F2P-oracle signal; not confirmed until executed).
- **200 MODIFIED**: target modifies ≥1 test file, adds none (weaker but valid evidence).
- **77 NO_CHANGED_TEST_EVIDENCE**: no test path changed in target diff; deferred from the automatic changed-test Oracle Confirmation path, NOT discarded.

## 5. What was excluded vs merely deferred

- **Excluded by frozen design:** the 3 Calibration-3 tasks (instrument overlap).
- **Sealed/UNOPENED:** the 786 Saleor RESERVE outcomes (never accessed).
- **Deferred (not excluded):** the 77 no-changed-test-evidence tasks (manual/external oracles later); migration/config-heavy tasks (a complexity stratum, not excluded).

## 6. Literature-supported rationale

Verified references recorded in
`research/wp2/wp2_design_reference_manifest_2026-09-22.json` and
`research/literature/wp2_verified_references_2026-09-22.bib`. FastContext
(arXiv:2606.14066) is recorded as WITHDRAWN and not used as positive evidence.

## 7. Oracle Confirmation methodology

Deterministic zero-API harness: isolated git worktrees (never mutating the
Saleor cache), test-only patch derivation (source-free), per-(task,state)
PostgreSQL test database, target-state pytest collection for node IDs, 3x
target + 3x parent+testpatch runs with JUnit, frozen failure taxonomy
(BEHAVIORAL_F2P / SYMBOL_ABSENCE_F2P / P2P_ONLY / ENV_BROKEN /
TEST_PATCH_APPLY_FAIL / FLAKY / TARGET_ORACLE_INVALID / OTHER_REVIEW_REQUIRED).

## 8. Environment families

147 environment families from 220 changed-test fingerprints; interpreter
resolved from each commit's Python requirement (`~3.8`, `~3.9`, `~3.12`, etc.)
via `uv`/`py`/`WP2_PYTHON`.

## 9. Wave A results (20 strong)

1 `BEHAVIORAL_F2P`, 19 `ENV_BROKEN`.

## 10. Wave B results (60 modified)

4 `BEHAVIORAL_F2P`, 55 `ENV_BROKEN`, 1 `TARGET_ORACLE_INVALID`.

## 11. Expansion results (140)

3 `BEHAVIORAL_F2P`, 1 `SYMBOL_ABSENCE_F2P`, 133 `ENV_BROKEN`, 2 `FLAKY`,
1 `TARGET_ORACLE_INVALID`.

## 12. Attrition flow

```
Census 297 -> changed-test candidates 220 -> attempted 220
-> environment valid 13 -> target stable 9
-> parent discriminative (behavioral) 8 -> (symbol) 1 -> P2P-only 13 tasks/1505 nodes
```

## 13. Behavioral F2P pool

8 tasks: `saleor-rc-05bdc7feb9ac`, `-30fe250747ae`, `-9057e82cea23`,
`-2a59d31fc839`, `-c6220233ccb1`, `-305415e0f8b7`, `-367b8038f6b9`,
`-a7a2bf4146ba`.

## 14. Symbol-absence F2P pool

1 task: `saleor-rc-c7207e71e0d3`.

## 15. P2P-only pool

13 tasks / 1,505 nodes inventoried in
`research/wp2/wp2_p2p_candidate_inventory_2026-09-22.json`.

## 16. Flaky / env-broken / invalid breakdown

2 FLAKY; 207 ENV_BROKEN (native libs e.g. gobject-2.0, `?` in cassette
filenames — invalid Windows path, Unix-only `resource` module, Poetry-era
build failures); 2 TARGET_ORACLE_INVALID.

## 17. Power and assay-sensitivity planning

`WP2_F2P_POOL_SMALL` (n=8 < 60). Paired power at n=8: 8% (5pp) to 20% (20pp).
Single-arm CI width at n=8 ≈ 0.6 (uninformative); n≥60 ≈ 0.25. Estimation-first
design recommended; Pilot Gold-vs-Placebo calibration required before any
selector comparison. `research/wp2/wp2_power_scenarios_2026-09-22.json`.

## 18. Smoke proposal v2

8 proposal-only tasks from the confirmed pool (SMALL/MEDIUM/larger coverage,
migration-heavy stress, 1 symbol-absence stress). `SMOKE_V2_PROPOSAL_ONLY`;
requires brain/Ahmed review. `research/wp2/wp2_smoke_candidate_proposal_v2_2026-09-22.json`.

## 19. WP-2 causal arms and estimands

GOLD_HARD / RMCSS_HARD / AGENT_HARD / PLACEBO_HARD (core), RMCSS_SOFT
(secondary), GOLD_MINUS_ONE (mechanistic subset). Estimands: F2P resolved rate,
P2P/preservation violations, over-edit rate, total pipeline cost. Design only;
no paid execution.

## 20. Novelty boundaries

Not novel: graph impact analysis, intent-aware change impact, repo memory,
localize-then-repair, restrictive file gate, gold/oracle files, F2P/P2P.
Candidate differentiators (hypotheses, not asserted): hard-vs-soft scope under
same selector, interventional placebo analysis, Gold-minus-one, real
requirement-driven tasks, full pipeline cost, preservation compliance.
`docs/WP2_NOVELTY_AND_RELATED_WORK_BOUNDARY_2026-09-22.md`.

## 21. What is verified / inferred / unknown

- **Verified:** oracle harness works end-to-end (4/5 previously-TARGET_ORACLE_INVALID now confirmed behavioral F2P after harness fixes); 8 confirmed oracles; taxonomy implemented; 786 sealed outcomes untouched; $0.00 spend.
- **Inferred:** the environment is the dominant blocker on this Windows host; a version-aware Saleor environment bundle is needed.
- **Unknown:** actual F2P yield of the remaining env-blocked tasks on a compatible host; E2E correctness (not measured); final P2P oracle (E2E-G6).

## 22. Validation

- `git diff --check`: PASS.
- Ruff: PASS (all changed scripts + wp2 src + tests).
- py_compile: PASS.
- Targeted pytest: 51/51 wp2 tests + 26 census/live-status/README/model/thesis tests PASS.
- Full suite: **4 failed / 3883 passed / 34 skipped**. 3 failures match the
  known-failures artifact (`artifacts/known_test_failures_2026-09-21.json`).
  The 4th (`tests/unit/test_wp1b_main_runner.py::test_lock_blocks_live_process_and_recovers_stale`)
  is a pre-existing flaky lock-timing test: passes in isolation, and neither it
  nor `wp1b/main_runner.py` was modified by this mission (git diff empty).
- No unintended tracked evidence-file mutations committed (full-suite side
  effects restored).

## 23. API spend = $0.00

Zero model/API/embedding calls. Postgres/Redis used locally (already available);
only a private isolated WP-2 Postgres cluster was created on port 5433 for
tests (never touched the user's 5432 cluster or global config).

## 24. Git commits / tag

Commits on `wp2/oracle-confirmation-design-v1-2026-09-22` (latest first):
`691d775 docs(governance)`, `cc819de docs(wp2): oracle confirmation report`,
`59fe5ba docs(wp2): oracle summary, power planning, smoke v2, novelty`,
`4e935ac chore(wp2): all 220 candidates`, `4f01fe8 definitive Wave A+B`,
`f1e9e5c environment validity audit`, `772b01c recovery evidence`, `ca01524`,
`c8f16f0`, `d1bee38`, `e09ba07` etc. Tag `wp2-oracle-confirmation-design-v1-2026-09-22` pending E3.

## 25. Exact next action

Per §24 decision rule (primary behavioral F2P pool < 60 after exhausting all
220 changed-test candidates):

> **Brain chooses estimation-first vs new prospective mining/cross-repository
> expansion; do not open the 786 sealed reserve. In parallel, build a
> version-aware Saleor environment bundle to lift the dominant environment
> blocker, and build/review the AG16 executable bundle.** Then AG16 sensitivity
> and WP-2 Smoke (from the 8 confirmed oracles, proposal v2) can proceed.