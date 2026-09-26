# MISSION-10A — ENVIRONMENT TEST-DEPENDENCY AUDIT — STOP REPORT (2026-09-26)

Decision token: **`ENV_AUDIT_INCONCLUSIVE`**

Mission-10A performed a scientific validity audit of the frozen V2 test
environment: do project-declared historical test/dev dependencies that V2 did
not install or load systematically exclude valid Saleor tests? ZERO LLM / API
calls. No generation, no Smoke, no HOLDOUT/VALIDATION/MAIN execution. One
ENG-only scratch probe ran; probe continuation was STOPPED after task 1 per the
preregistered S2 rule.

---

## 1. Executive decision

**ENV_AUDIT_INCONCLUSIVE.**

The audit PROVED the dependency mechanism: `pytest-django-queries` (provides
`count_queries`) and `pytest-mock` (provides `mocker`) are **project-declared**
in the `dev` / `[dependency-groups]` group at the affected historical target
commits, and are **NOT installed in the frozen V2 environment** (verified at the
package, entry-point, plugin-load, and fixture-visibility layers in scratch
introspection). This DECLARED_BUT_NOT_INSTALLED cause explains the 41 P2P-U
cap200 COLLECTION_ERROR nodes (39 count_queries + 2 mocker) at 100%, and is the
only explanation for 98.7% of py312-era C4 error-TOI records. The scratch probe
recovered **18/18** count_queries error nodes in the top-ranked ENG task to
P2P_ONLY (SET A recovery), and the mechanical category definition shows 100%
systematic exclusion of the count_queries and mocker categories under V2 (M3
satisfied).

However, the probe's SET B (non-regression) produced **one classification
change** in a previously-valid V2 node (`test_update_voucher`,
BEHAVIORAL_F2P → P2P_ONLY), caused by a JWT `iat` clock-skew flake in the V2
parent run that resolved to P2P_ONLY under re-execution. Under the preregistered
S2 rule ("every V2 BEHAVIORAL_F2P and P2P_ONLY node keeps the SAME
classification"), any classification change forces **ENV_AUDIT_INCONCLUSIVE**
and STOP of probe continuation. The token criteria are not weakened after
seeing results.

---

## 2. Error taxonomy

Machine-readable: `error_taxonomy_summary.json` (20,362 node-records across
C2/C4/P2P-U, deduplicated by node identity in `error_records.jsonl`).

| dataset | error records | unique nodes | unique tasks | dominant taxonomy |
|---|---|---|---|---|
| C4 (DEV) | 11,046 | 2,064 | 40 | OTHER (5,877), EXECUTION_OTHER (4,911), MISSING_FIXTURE:count_queries (237) |
| C2 (MAIN rescue) | 8,530 | 3,304 | 90 | EXECUTION_OTHER (3,929), OTHER (3,556), DB_ERROR (855) |
| P2P-U ENG cap200 | 786 (incl. 3 reps × 2 sides) | 54 | 7 | MISSING_FIXTURE:count_queries (762), MISSING_FIXTURE:mocker (24) |

P2P-U ENG cap200 unique error nodes: **41** = 39 `MISSING_FIXTURE:count_queries`
+ 2 `MISSING_FIXTURE:mocker`. Parametrized-ID share among the 41: **0%**
(confirms the hypothesis; no node-ID quoting problem).

## 3. C4 error-TOI explanation

- Authoritative C4 TARGET_ORACLE_INVALID = **3,727**; error-bearing = **3,682**;
  failed-only = **45** (reconciled exactly, mismatch 0).
- **2.3%** of C4 error records (258/11,046) are explained by the
  DECLARED_BUT_NOT_INSTALLED causes (count_queries / mocker / before_after /
  mock / openpyxl).
- Per-era: py312 98.7% of records (234/237) are count_queries-missing; py39
  0.3%; py38 0%.
- The dominant C4 error population (OTHER / EXECUTION_OTHER ≈ 9,800 records) is
  **NOT** explained by missing test-dependency plugins: manual inspection shows
  Django migration-execution / DB-setup errors and generic fixture setup text
  (`django.db.migrations.state.ProjectState`, `@pytest.fixture(scope=...)`),
  i.e. DB/environment-other, not dependency-missing.

## 4. C2 evidence

C2 per-node error text is available only through the rescue archive
(159/220 tasks). Rescue archive error-bearing nodes = 3,304 unique across 90
tasks; count_queries-file category errors = 125 (node-level, static evidence),
mocker-file = 12. C2 task-level counts (per_task_v2.jsonl) are the
authoritative denominators; no overclaim beyond rescue-archive coverage.

## 5. Mission-09 P2P-U error explanation

- Authoritative cap200 COLLECTION_ERROR = **41** (machine-readable
  `consolidated_results_2026-09-25.json`); reconciled exactly, mismatch 0.
- **39 count_queries** (38 under `*/tests/benchmark/*`; 1 under
  `order/tests/test_fetch.py`) and **2 mocker** (both in
  `payment/tests/queries/test_payment_sources.py`).
- All 41 are `SETUP_ERROR:MISSING_FIXTURE:<name>` (setup phase, not true
  collection). All 41 attributable to DECLARED_BUT_NOT_INSTALLED packages.

## 6. Declared vs installed dependencies

Machine-readable: `dependency_declaration_matrix.json` (35 affected tasks, 37
cause-rows).

- **37/37 B_DECLARED_BUT_NOT_INSTALLED** (zero A/C/D/E/F).
- 33/37 in the `dev` group (pyproject poetry group / legacy dev-dependencies /
  PEP 735 `[dependency-groups]`); 4/37 declared via requirements_dev.txt /
  poetry.lock (`mock` backport, `before_after`, `openpyxl` transitive pins).
- Locked versions proven from poetry.lock / uv.lock / requirements_dev.txt
  (e.g. pytest-django-queries==1.2.0 at both probe target commits;
  pytest-mock==3.10.0 at py39 commits).

## 7. Lockfile / group analysis

- Affected tasks are poetry (py38/py39 era, `[tool.poetry.dependencies]` +
  `[tool.poetry.dev-dependencies]`) or modern py312 (PEP 735
  `[dependency-groups] dev`).
- V2 installer installs production deps only: py38/py39 `-r requirements.txt`;
  py312 `-e . freezegun fakeredis` (no dev group); TOOLING_INSTALL = pytest,
  pytest-django, pytest-socket, pytest-xdist, billiard<4.3, setuptools<81, wheel.
- The project-declared test/dev group is **omitted** in V2; lockfile-first
  requirement is respected for the probe (exact locked 1.2.0 used).

## 8. Package → entry point → plugin load → fixture visibility

Machine-readable: `frozen_v2_installed_state.json`, `pytest_plugin_state.json`
(eras py312 + py39, scratch containers replicating the exact frozen V2 install).

| package | PACKAGE_INSTALLED | ENTRY_POINT_REGISTERED | PLUGIN_LOADED | FIXTURE_VISIBLE |
|---|---|---|---|---|
| pytest-django-queries | NO | NO | NO | count_queries: NO |
| pytest-mock | NO | NO | NO | mocker: NO |

Counterfactual proven in a controlled scratch container: installing
pytest-django-queries==1.2.0 + pytest-mock==3.14.1 registers pytest11 entry
points (`django_queries`, `pytest_mock`) and exposes `count_queries` + `mocker`
fixtures. This closes the "package exists therefore correct" false-conclusion
gap at all four layers.

## 9. Systematically excluded categories

Machine-readable: `category_exclusion_analysis.json`.

- **benchmark-count-queries**: node-level static signature evidence — 38/38
  ENG cap200 nodes that request `count_queries` are COLLECTION_ERROR under V2;
  **excluded_share = 1.0**. The single STABLE_P2P node in a benchmark file does
  NOT request the fixture (no false positive).
- **mocker-fixture**: 2/2 ENG cap200 nodes requesting `mocker` are
  COLLECTION_ERROR; excluded_share = **1.0**.
- C4: 72 error-TOI benchmark-count-queries nodes + 4 mocker nodes; C2 rescue:
  125 + 12.
- **M3 systematic whole-category exclusion: SATISFIED** (mechanically defined
  category, every requesting node errors for the SAME missing declared
  dependency, no valid execution observed in V2 for the category).

## 10. Probe selection

Machine-readable: `probe_selection.json` (frozen before probe execution).

1. `saleor-rc-74538ea00ce9` (py312) — 18 attributable count_queries nodes.
2. `saleor-rc-8f76ddc6267f` (py39) — 6 attributable count_queries nodes.

Distinct-dependency coverage would have required violating the primary rank
rule; reported as `distinct_dependency_cover=false` (both tasks share
pytest-django-queries; the mocker-carrying ENG task ranked 3rd).

## 11. Probe results

Machine-readable: `probe/probe_results.json` (labeled
`NON_FROZEN_EXPLORATORY_ENV_PROBE`).

Task 1 (`saleor-rc-74538ea00ce9`, scratch = V2 install + `pytest-django-queries==1.2.0`):
- SET A recovery (18 count_queries error nodes): **18/18 → P2P_ONLY**
  (0 still TARGET_ORACLE_INVALID, 0 FLAKY, 0 other). Zero missing/duplicate/
  orphan records; JUnit persisted; parent/target state correct.
- SET B non-regression (56 V2 BEHAVIORAL_F2P/P2P_ONLY nodes): 52 P2P_ONLY +
  4 BEHAVIORAL_F2P; **1 classification change**:
  `test_voucher_update.py::test_update_voucher` V2 BEHAVIORAL_F2P → probe
  P2P_ONLY (V2 parent failed 3/3 with `ImmatureSignatureError` JWT `iat`
  clock-skew; probe parent passed 3/3).

Probe continuation STOPPED after task 1 per §18. Task 2 NOT run.

## 12. Non-regression result

**FAILED (S2 not satisfied).** One previously-valid V2 BEHAVIORAL_F2P node
changed classification under scratch re-execution. The change is a V2 parent
JWT-`iat` clock-skew flake, not a dependency-install defect; nonetheless the
preregistered S2 rule (Mission-10A §14) counts ANY classification change as a
non-regression failure → probe class change → **ENV_AUDIT_INCONCLUSIVE**.

## 13. V2 oracle undercount impact

Machine-readable: `v3_impact_estimate.json`.

- MEASURED in probe: 18/18 recovered in one ENG task (P2P_ONLY; no
  BEHAVIORAL_F2P recovery, so M1/M2 measured = 0).
- PROJECTED across population (never labeled as observed):
  - C4: 72 benchmark-count-queries + 4 mocker error-TOI nodes recoverable in
    principle; 35 affected tasks in the declaration matrix; eras py39/py312.
  - C2 rescue: 125 + 12 category errors.
  - P2P-U cap200 ENG: 41 nodes, 7 tasks.
  - Some currently-TARGET_ORACLE_INVALID tasks could gain valid P2P_ONLY /
    BEHAVIORAL_F2P membership; count is task-dependent and NOT pre-determined.

## 14. V3 cost / impact estimate

- V3 concept (NOT built/run in Mission-10A): same frozen era strategy + same
  historical lock + the omitted project-declared test/dev group.
- Reusable unchanged: task commits, split membership, oracle semantics, test
  patch semantics, P2P-S/P2P-U V2 rules, membership for unaffected tasks.
- New versions needed: era image(s), environment manifest, C4 DEV oracle
  evidence, C2/MAIN evidence where affected, F2P sets, P2P-S re-verify,
  P2P-U membership + ENG + full DEV execution, Smoke draft population, runtime
  estimates, V2→V3 reconciliation.
- Runtime: DEV-47 cap200 central ≈ 6.7 h re-run unchanged; only
  category-excluded tasks strictly need re-execution in the cleanest path.

## 15. Recommendation

Do NOT proceed to Env V3 automatically. The dependency mechanism is PROVEN
(declared-but-not-installed, M3 systematic category exclusion, 18/18 probe
recovery), but a clean V3 recommendation is blocked by the S2 non-regression
failure: the probe exposed a V2 oracle classification instability (one
BEHAVIORAL_F2P node was a JWT-clock flake). A targeted follow-up must (a)
decide how V2 oracle instability is handled (per-node flakiness audit of the
BEHAVIORAL_F2P set), and (b) re-run the second probe task and the affected SET B
under a clock-skew-robust harness before any V3 freeze. V2 remains immutable
historical evidence.

## 16. Project orientation

- WHERE ARE WE NOW: last pre-generation environment-validity gate, decision
  point open.
- WHERE DID WE COME FROM: localization → F2P → P2P-S → P2P-U V1 scaling failure
  → P2P-U V2 → environment completeness question.
- WHERE DO WE GO NEXT (branch only after Ahmed review):
  C. ENV_AUDIT_INCONCLUSIVE → targeted follow-up only.
- NEAR GOAL: close environment validity.
- MEDIUM GOAL: first ENG generated-patch Smoke across all five dimensions.
- FAR GOAL: E2E evidence on selective regeneration cost/scope vs
  correctness/preservation.
- MINIATURE VIEW: V2 omitted declared test/dev group (count_queries/mocker);
  probe recovered 18/18 but one V2 valid node flipped → audit inconclusive.
- DETAILED VIEW: environment/evaluator validity audit complete; decision token
  ENV_AUDIT_INCONCLUSIVE.
- ZOOMED-OUT VIEW: MSc question — does selective regeneration reduce
  cost/scope without sacrificing correctness/preservation, measured on a valid
  frozen environment/evaluator.

## 17. Exact next action requiring Ahmed approval

Approve the targeted follow-up (Mission-10B-bis): (1) flakiness audit of the V2
BEHAVIORAL_F2P node set (JWT `iat` clock-skew class), (2) complete probe task 2
and SET B under a clock-skew-robust harness, (3) then re-decide
ENV_V3_RECOMMENDED / ENV_V2_ADEQUATE / ENV_AUDIT_INCONCLUSIVE. No generation,
Smoke, DEV-47, HOLDOUT, VALIDATION, or MAIN execution without explicit approval.

---

# APPENDIX — VALIDATION

- py_compile: PASS (all audit modules + tests).
- ruff: PASS (all changed files).
- mypy strict: PASS (`src/benchmark/wp2/m10a_audit.py`).
- pytest: 28 new Mission-10A tests PASS; existing WP2 suite 194 PASS.
- Evidence integrity: C4 mismatch 0; P2P-U 41 mismatch 0; probe 0 missing /
  0 duplicate / 0 orphan.
- Docs: Impact Declaration (new), STOP report (new), DECISIONS.md (appended),
  PROGRESS.md (updated), LIVE_STATUS + 4 render targets (updated).
- No frozen image mutation; no oracle rewrite; no generation; no Smoke; no
  HOLDOUT/VALIDATION/MAIN.

---

# EXPORTS

## FULL AUDIT EXPORT

\PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=project-2026-09-26-0632.zip
PROJECT_EXPORT_PATH=C:\\Users\\Ahmed\\Desktop\\OpenCode\\master-2026-07-21-2355\\project-2026-09-26-0632.zip
PROJECT_EXPORT_SIZE_BYTES=249654286
PROJECT_EXPORT_SHA256=6f928c776f033e5b6850bc65c0aafc5a7cf19d96ab7d6367f61ba16816d7e1b4
UPLOAD_THIS_FILE=project-2026-09-26-0632.zip
\
Verified: \.git/HEAD\ present; \dist/pilot-kaggle-upload.zip\ + \.sha256\ present;
ZIP opens; testzip PASS; 12,760 entries.

## TRUE LIGHT EXPORT

\LIGHT_EXPORT_READY
LIGHT_EXPORT_NAME=project-LIGHT-2026-09-26-0629.zip
LIGHT_EXPORT_PATH=C:\\Users\\Ahmed\\Desktop\\OpenCode\\master-2026-07-21-2355\\project-LIGHT-2026-09-26-0629.zip
LIGHT_EXPORT_SIZE_BYTES=902355
LIGHT_EXPORT_SHA256=acca1793e140599b868a65165f07a81865b126c0648c53da808d5cd1930df982
WITHIN_50MB=True
\
## Tag

- Tag: \wp2-env-audit-2026-09-26\ (annotated), created on commit
  dfa7c6bc9fe63b59c12743b69d82e2b4d2f3c5\ (the Mission-10A audit commit;
  == tag peel). Pushed to origin. Export scripts committed post-tag
  (\9633ff17\) as workflow tooling only — never a tag target.
