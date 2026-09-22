# WP-2 MAIN_297 Zero-API Census — 2026-09-22

Status: **ZERO-API DETERMINISTIC PLANNING EVIDENCE ONLY**. Not an E2E result.
No Saleor test was executed; no F2P/P2P oracle was built; nothing was
installed, started, or downloaded.

## 1. Executive summary

The 297 already-opened MAIN_297 Saleor tasks were inspected deterministically
(read-only `git diff parent..target` in the local cache) to prepare the E2E
phase. **20** tasks add at least one test file (`STRONG_F2P_CANDIDATE`), **200**
modify but do not add a test file (`MODIFIED_TEST_CANDIDATE`), and **77** have no
changed-test evidence. There are **0** metadata/materialization problems (all
297 parent/target commit pairs verified in the local cache). 78 migration files
and 21 config/infra files appear across 40 tasks. The local environment is
structurally feasible for offline test runs (Postgres 17 and Redis are running,
pytest is designed offline via `--disable-socket`), but real runtime is not
measured.

## 2. Exact 297-task scope

`research/wp1b/wp1b_main_297_manifest.json` (297 unique IDs; first 50 = nested
MAIN_50). Verified: all 297 have `case_manifest.json` in
`benchmark_data/real_commit_impact_saleor/scientific/`; all parent/target
commits exist in `dist/pilot-repo-cache/saleor`. The 3 calibration tasks are
excluded by the manifest and do not enter the census. The 786 sealed RESERVE
outcomes were never accessed.

## 3. Counts by F2P candidacy

| F2P candidacy (planning label only) | Tasks |
|---|---:|
| STRONG_F2P_CANDIDATE (target ADDS ≥1 test file) | 20 |
| MODIFIED_TEST_CANDIDATE (modifies but does not add a test file) | 200 |
| NO_CHANGED_TEST_EVIDENCE | 77 |
| F2P_CONFIRMED | 0 (never assigned) |
| **Total** | **297** |

> F2P/P2P requires executable before/after test behaviour and belongs to E2E-G6.
> A changed test file is NOT proof that a test fails at parent and passes at
> target.

## 4. Counts of changed / added / modified test files

Across all 297 tasks (sum of per-task diffs):
- changed files: **1,906**
- production files (not test/migration/config): **1,079**
- test files: **728** (added **47**, modified **680**, deleted **0**)
- tasks with ≥1 added test file: **20**

Static test-command inference was possible for **220** tasks (added/modified
Python test path → `pytest <path>`, Saleor `setup.cfg` `testpaths=saleor`);
the remaining 77 record `UNKNOWN`/none — no commands were invented.

## 5. Migration / config complexity

- migration files: **78** across **40** tasks; config/infra files: **21**.
- Tasks with migration-or-config-heavy markers: **40** of 297 → these are
  Group-B candidates in the Smoke proposal (higher environment setup cost).

## 6. Environment feasibility

See `docs/WP2_SALEOR_ENVIRONMENT_FEASIBILITY_2026-09-22.md` and
`research/wp2/wp2_saleor_environment_feasibility_2026-09-22.json`. Highlights:
- Test runner: pytest + Django TestCase (`setup.cfg`, `--ds=saleor.tests.settings`, offline by default).
- Postgres 17: AVAILABLE locally (running). Redis: AVAILABLE locally (running).
- Python: Saleor HEAD requires ≥3.12,<3.13; local interpreter is 3.11.5 → a
  compatible interpreter/venv is required at execution time (UNKNOWN until then).
- Celery: tests run eager (`CELERY_TASK_ALWAYS_EAGER=True`), so no worker needed.
- A no-network local test execution is structurally feasible but NOT measured.

## 7. Proposed Smoke candidates (proposal-only)

`research/wp2/wp2_smoke_candidate_proposal_2026-09-22.json` — 8 candidates
selected by transparent deterministic rules (Group A favored; changed-file
count diversity; never by RM-CSS/Agent success; tie-break SHA-256(salt+task_id)):

| Task | Group | F2P candidacy | n_changed |
|---|---|---|---|
| saleor-rc-b8786c1bf4d3 | A | MODIFIED_TEST_CANDIDATE | 3 |
| saleor-rc-11756ee6b65a | A | MODIFIED_TEST_CANDIDATE | 3 |
| saleor-rc-14f2176b5d8c | A | MODIFIED_TEST_CANDIDATE | 5 |
| saleor-rc-bd0c56fc787e | A | MODIFIED_TEST_CANDIDATE | 3 |
| saleor-rc-10889526d151 | A | MODIFIED_TEST_CANDIDATE | 2 |
| saleor-rc-cae629dc4166 | A | STRONG_F2P_CANDIDATE | 6 |
| saleor-rc-a9e79dac40a2 | B | MODIFIED_TEST_CANDIDATE | 7 |
| saleor-rc-b84bf6595f49 | C | NO_CHANGED_TEST_EVIDENCE | 4 |

`SMOKE_CANDIDATE_PROPOSAL_ONLY` — the final Smoke sample requires brain/Ahmed
review.

## 8. What this DOES show

- Concrete F2P/P2P feasibility evidence for the E2E phase: 20 tasks with
  added-target tests (fail-to-pass oracle candidates), 200 with modified tests,
  77 without test evidence.
- All 297 tasks are materializable in the local cache (0 metadata problems).
- Test commands are statically inferable for most test-bearing tasks.
- The environment is structurally ready for offline loopback test runs.

## 9. What this DOES NOT show

- No E2E correctness, no F2P/P2P verdicts, no Smoke/Pilot/Research Run.
- No runtime measurement (setup time, per-test wall time, migration cost).
- No claim that a changed test actually fails at parent and passes at target.
- No scientific inference; this is deterministic repository inspection.

## 10. Missing pieces before WP-2 execution

- WP-2 shared E2E executor (generation/validation/repair for every arm) —
  brain/Ahmed design required.
- E2E-G6 F2P/P2P oracle semantics and implementation.
- Compatible Saleor Python interpreter/venv + dependency install + test
  database provisioning (runtime then measurable).
- Brain/Ahmed review of the Smoke candidate proposal.

## 11. Recommended next sequence

1. AG16 sensitivity closeout (brain-built harness, then D6).
2. WP-2 shared executor design.
3. E2E-G6 F2P/P2P oracle.
4. E2E Smoke (on the reviewed candidate sample).
5. Pilot.
6. Research Run.

## 12. External validity stays later

- NestJS/TypeScript; JabRef/Java; Grafana true-polyglot (Go + TypeScript);
  optional Prometheus/Go. No external-repository cloning in this mission; these
  are roadmap candidates, not validated datasets.