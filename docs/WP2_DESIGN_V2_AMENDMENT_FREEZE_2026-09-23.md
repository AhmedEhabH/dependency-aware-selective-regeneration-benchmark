# WP-2 Design V2 — Amendment Freeze (2026-09-23)

Status: **FROZEN.** This artifact is the Design-v2 amendment/freeze layer for
Mission 07 (`WP2_LINUX_ORACLE_V2_DEV_POOL`), integrating the Claude Opus 5.5
review (A–N amendments) with Mission 07. It maps every amendment to concrete
implementation, tests, and outputs. It is the operative specification for this
mission.

Authority rule:
- Where Claude (A–N) explicitly amends Mission 07, Claude's amendment wins.
- Where Claude is silent, Mission 07 remains authoritative.
- Current live `origin/main` wins over the SHA recorded when the mission was
  authored; never reset newer valid work.

All decisions below that concern future E2E execution are **recorded, NOT
executed** (amendment K). This mission performs no generation, no Smoke/Pilot,
no selector E2E comparison.

---

## A–N amendments: verbatim freeze + implementation mapping

### A. ORACLE CLASSIFICATION — MAKE IT MECHANICAL

Verbatim rule:

1. `PARENT_COLLECTION_ERROR` (PCE):
   - the target node does not exist/collect at parent; OR
   - its module, conftest, fixture, cassette, or other required test-support
     import fails during collection.
   - If a shared test-support file fails during collection, dependent nodes
     are PCE.
   - PCE is NOT primary behavioral F2P.
2. `SYMBOL_ABSENCE_F2P` (SA):
   - the node itself is successfully collected;
   - failure occurs in call/execution phase;
   - the stable parent failure is specifically ImportError / AttributeError /
     NameError caused by a target-introduced symbol/component absent at parent.
   - It is NOT primary behavioral F2P.
3. `BEHAVIORAL_F2P`:
   - node passes target 3/3;
   - node is collected on parent+testpatch;
   - node fails parent 3/3 during call/execution phase with an assertion or
     another behavioral exception not covered by symbol absence.

Task-level primary eligibility:
- a task is primary-eligible if it contains >=1 stable BEHAVIORAL_F2P node.
- flaky or target-invalid nodes are excluded node-wise; they do NOT invalidate
  an otherwise eligible task.
- only systemic environment/collection failure may invalidate the whole task.
- Preserve PCE and SYMBOL_ABSENCE counts separately.

Implementation:
- New module `src/benchmark/wp2/oracle_semantics_v2.py` with
  `classify_node_v2(...)` returning exactly `PARENT_COLLECTION_ERROR` |
  `SYMBOL_ABSENCE_F2P` | `BEHAVIORAL_F2P` | `FLAKY` | `TARGET_ORACLE_INVALID`
  | `P2P_ONLY` | `OTHER_REVIEW_REQUIRED`, with an explicit
  `collection_phase_failure` input so the caller (harness) supplies whether the
  node was collected on parent+testpatch (PCE gate) and whether the failure was
  in call/execution.
- The PCE decision consumes evidence:
  - `parent_collects_node: bool` (node present and its module/conftest/fixture/
    cassette/test-support imports collected at parent+testpatch),
  - `parent_outcomes` (3),
  - `parent_failure_text`,
  - `target_outcomes` (3).
- Order of evaluation (frozen):
  1. target stability flaky -> FLAKY; parent flaky -> FLAKY.
  2. target not STABLE_PASS -> TARGET_ORACLE_INVALID.
  3. parent STABLE_PASS -> P2P_ONLY.
  4. NOT `parent_collects_node` -> PARENT_COLLECTION_ERROR.
  5. parent failure text matches symbol-absence signature
     (ImportError/AttributeError/NameError/ModuleNotFoundError) -> SA.
  6. behavioral exception (assertion or other non-symbol failure) -> BEHAVIORAL_F2P.
  7. else OTHER_REVIEW_REQUIRED.
- Task eligibility: `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE = (n_behavioral >= 1) and
  environment_valid and not task_collection_failure`. Counts for PCE and SA are
  preserved separately in every task record.
- Tests (RED/GREEN): `tests/unit/wp2/test_oracle_semantics_v2.py` covering each
  branch, including: mixed task (stable behavioral + flaky node remains
  eligible), mixed task (stable behavioral + target-invalid node remains
  eligible), shared test-support file collection failure -> PCE for dependent
  nodes, cassette/`?`-filename node -> PCE, node missing at parent -> PCE,
  05bd-style parent-missing/collection nodes NOT primary behavioral.
- Output: `research/wp2/oracle_confirmation_linux_v2_2026-09-23/` per-task and
  per-test records carry `pce_count` / `symbol_absence_count` /
  `behavioral_count` separately.

### B. FREEZE THE TEST-PATCH DEFINITION

Verbatim rule: define and freeze one deterministic test-path regex before
examining V2 results. The test patch contains ONLY target changes under that
regex covering: test files; conftest; fixtures; cassettes / equivalent
test-support artifacts. It contains nothing outside the frozen test-path rule.
Record the exact rule and hash/version it as part of V2 provenance.

Implementation:
- `TEST_PATH_REGEX_V2` (frozen string, exported from `oracle_semantics_v2.py`):
  a single compiled regex used by the V2 harness to derive the test-only patch.
  Covering rule: path matches if it is under a `tests` directory, OR basename
  starts with `test_`, OR basename ends with `_test.py`, OR basename is
  `conftest.py` / `fixtures.py`, OR the path is a cassette/test-support
  artifact (under `cassettes/`, or matching `.yaml`/.json recorded test-support
  under a `tests` tree), per amendment B's coverage list.
- The regex is hashed: `TEST_PATH_REGEX_V2_SHA256`; both recorded in every V2
  provenance record (`test_patch_rule_sha256`).
- Tests: regex accepts the listed categories and rejects production paths,
  migration paths, and config/infra paths; patch derivation produces identical
  bytes across runs (determinism test).

### C. ENVIRONMENT CANARY

Verbatim rule: for every task, identify one unchanged pre-existing test in the
touched Saleor app/module where feasible. Run it: parent 3/3; target 3/3. Use
as per-task environment canary so environment validity is not confused with
oracle behavior. Record explicit outcomes when no defensible canary can be
constructed.

Implementation:
- `select_canary_node(test_nodes, changed_test_files, changed_production_dirs)`
  picks, deterministically, the first stable pre-existing test node (not in the
  changed-test set) in the same top-level Saleor app as the touched production
  files; preference order frozen: same module as a touched production file,
  then same app dir, then first available; fixed-salt tie-break.
- The V2 runner executes the canary node on parent (3x) and target (3x) for
  every task where a canary exists.
- Task record fields: `canary_node_id`, `canary_parent_outcomes`,
  `canary_target_outcomes`, `canary_verdict`
  (`CANARY_VALID` both 3/3 pass | `CANARY_ENV_INVALID` | `CANARY_NONE`).
- When no defensible canary exists, the explicit outcome `CANARY_NONE` with
  reason is recorded.
- Tests: canary selection determinism + exclusion of changed-test nodes.

### D. LINUX ENVIRONMENT STRATEGY

Verbatim rule: one controlled base image per Python/environment era; immutable
image digest; fixed system-library superset per era; commit's own lockfile/
dependency metadata; pip/Poetry/installer version pinned per era; test
execution offline after environment construction; no silent dependency
fallback; do NOT build arbitrary per-commit production Dockerfiles as the
experimental platform; commit Dockerfiles may be inspected as evidence for
required apt/system packages only. Record: base image digest; Python version;
installer version; lockfile SHA; resolved dependency / `pip freeze` hash;
Postgres version + image digest; Redis version + image digest where relevant;
harness SHA; classifier bundle SHA256; parent/target SHA; commands;
JUnit/output hashes; timestamp. No required provenance field may be `None`.

Implementation:
- `src/benchmark/wp2/era_resolver.py`:
  - `ERA_TABLE` maps Python requirement -> (base image tag, immutable digest,
    system-package superset, installer pin, pip pin).
  - Resolves a task's era from its commit's Python requirement + lockfile SHA.
  - `resolve_era(commit_metadata) -> EraSpec`; fails closed (never falls back
    to a newer/global environment).
  - Offline test execution: image construction installs deps; test invocation
    runs with `--disable-socket` and no network.
  - Commit Dockerfiles are read only to extract required apt/system packages
    (never executed as the experimental platform).
- Tests: era determinism; unknown era -> hard error (no fallback); offline flag
  enforced; provenance completeness (no field `None`).

### E. DRY RUN COVERAGE

Verbatim rule: the bounded Linux dry run must include all categories already
required by Mission 07 (§17: one old-era task; one newer-era task; one prior
Windows path failure; one prior Unix-resource failure; one prior native-lib
failure if feasible), PLUS at least one 2025–2026 / Python 3.12 task. Do not
begin the full sweep until the dry run and RED/GREEN classification tests pass.

Implementation:
- `scripts/wp2_linux_dryrun.py` selects 5–6 tasks by the frozen categories and
  runs them on the Linux substrate; success gate = all dry-run tasks reach a
  terminal classification with complete provenance and the RED/GREEN unit tests
  pass.
- The 2025–2026/Python 3.12 task is selected from the DEV or MAIN candidates
  with target year >= 2025 and python `>=3.12,<3.13` (verified present: 35
  tasks with that requirement).

### F. DEV SPLIT — FREEZE BEFORE CANDIDATE GENERATION

Verbatim rule: before producing any DEV candidate list, deterministically
split the frozen `DEV_TRAIN=120` into `DEV_TRAIN_ENG` ≈ 40 and
`DEV_TRAIN_ASSAY_HOLDOUT` ≈ 80. Use a deterministic salted procedure. Freeze
and record: algorithm; salt/seed; membership; hashes. `DEV_VALIDATION=30`
remains separate. DEV_TRAIN_ENG may later support harness/generator/repair
engineering. DEV_TRAIN_ASSAY_HOLDOUT + DEV_VALIDATION are protected from
engineering contamination and are intended for later Smoke/assay work according
to the frozen research design. NO generation or Smoke/Pilot is authorized now.
Do NOT perform RM-CSS-vs-Agent selector comparison on DEV as thesis evidence.

Implementation:
- `src/benchmark/wp2/dev_split_v2.py`: salted deterministic split
  (SHA-256(salt|task_id) rank, first 40 -> ENG, remaining 80 -> ASSAY_HOLDOUT;
  salt frozen: `wp2-dev-train-eng-v1-2026-09-23`). Outputs membership + role
  SHA-256.
- Frozen output artifact: `research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_split_v2.json`
  (algorithm, salt, seed, membership, per-role hashes, DEV_VALIDATION
  unchanged).
- Tests: deterministic membership; 40/80 counts; `DEV_VALIDATION` untouched;
  INTERNAL_TEST and RESERVE not referenced.

### G. INTERNAL_TEST AND RESERVE

Verbatim rule: `INTERNAL_TEST=80` is UNTOUCHABLE in this mission. Do not: open
it; oracle-run it; generate on it; make new Agent predictions for it; use it
for sample-size expansion. It is only a possible future expansion pool if a
separately frozen statistical trigger authorizes it. The 786 RESERVE outcomes
remain sealed exactly as specified in Mission 07. Do not list/read/open/score
them beyond already-authorized aggregate metadata.

Implementation:
- All V2 census/oracle/preflight scripts take an explicit allow-list and refuse
  (raise) on any `INTERNAL_TEST` or sealed-RESERVE task id.
- Test: `tests/unit/wp2/test_protected_pools_v2.py` asserts the allow-list
  guard rejects INTERNAL_TEST ids and sealed-reserve paths
  (`is_sealed_outcome_source`).

### H. CENSUS / EVALUATOR-SIDE METADATA ADDITIONS

Verbatim rule: for MAIN and relevant DEV census artifacts, add deterministic
evaluator-side fields for: (1) production files added in target but absent at
parent; (2) number/list or hashed representation of Gold production files that
already exist at parent; (3) RM-CSS empty-scope flag; (4) Agent empty-scope
flag; (5) RM-CSS-vs-Agent scope-identical flag. Metadata only. Do NOT alter
frozen RM-CSS or Agent predictions.

Verified machine-readable facts (recomputed, see
`docs/WP2_METADATA_RECONCILIATION_2026-09-23.md`):
- claim sheet `EMPTY 2/297` refers to the Agent only
  (`wp1b_main297_result.json.agent_empty_by_reason.parser_failure = 2`);
- RM-CSS has 29/297 empty MAIN scopes
  (`research/wp1a/sip_rmcss_per_task_predictions.json`, empty
  `rmcss_predicted_set`), matching the Claude audit;
- RM-CSS-vs-Agent scope-identical: 31/297.

Implementation:
- `src/benchmark/wp2/census_metadata_v2.py`:
  - `added_in_target_absent_at_parent(cache, parent, target)` -> production
    files added in target but absent at parent;
  - `gold_files_exist_at_parent(...)` -> hashed representation (sha256 of
    sorted list) of Gold (target-changed production) files already present at
    parent;
  - per-task flags: `rmcss_empty_scope`, `agent_empty_scope`,
    `scope_identical` computed ONLY from the frozen prediction artifacts, never
    modifying them.
- Output: extended census artifacts (new files; v1 census JSON untouched).

### I. FIX CURRENT METADATA CONTRADICTIONS BEFORE NEW RESULTS

Verbatim rule: mechanically resolve and document:
1. Power-analysis CI-width mismatch: one document reports n=8 CI width ≈0.63;
   JSON reports ≈0.52. Determine the authoritative computation from source
   code/JSON and correct current-facing documentation without deleting
   historical artifacts.
2. Empty-set claim: clearly distinguish Agent empty count from RM-CSS empty
   count.
Also: 147 vs 140 environment-family counts; migration/config-heavy summary
contradiction. Never overwrite old evidence; create reconciliation artifacts.

Verified facts (see `docs/WP2_METADATA_RECONCILIATION_2026-09-23.md`):
- CI width: authoritative computation is `scripts/wp2_power_scenarios.py`
  (Exact Clopper-Pearson / binom interval widths). JSON records n=8 widths
  0.5193–0.5696; the doc's "≈0.6" was rounded text. Current-facing docs
  corrected to JSON-exact widths.
- Agent empty 2/297 (parser_failure) vs RM-CSS empty 29/297.
- 147 vs 140 env families: 147 = unique target-state fingerprint families
  (environment_fingerprints.json); 140 = `env_families_count` from
  `scripts/wp2_oracle_summary.py` over the selection manifest (139 real + 1
  UNKNOWN bucket, because 20 Wave-A tasks have `env_family: None`). Canonical
  V2 rule defined in reconciliation.
- migration/config-heavy: `summary.json` reports 0 because per_task.jsonl rows
  lack `n_migration`/`n_config_or_infra`; the census shows 40/297 tasks with
  migration/config. Recompute from census source.

Implementation:
- `scripts/wp2_metadata_reconciliation.py` + `docs/WP2_METADATA_RECONCILIATION_2026-09-23.md`
  (reconciliation artifact; old evidence untouched).
- Tests: `tests/unit/wp2/test_metadata_reconciliation.py` verifies recomputed
  numbers equal machine-readable authoritative sources.

### J. P2P PRESERVATION RULE V1 — FREEZE NOW

Verbatim rule: for the deterministic unchanged-test candidate inventory:
consider unchanged test files in the same top-level Saleor app as touched
production files; test file itself must be unchanged by the target commit; keep
nodes that pass stably 3/3 on BOTH parent and target; if >400 eligible nodes
exist for one task, select a deterministic fixed-seed sample of 400;
coverage-based association is NOT primary V1 (later sensitivity). P2P
oracle/candidate set is evaluator-only and MUST remain invisible to future
generation and repair. Do not claim final preservation validation is complete
merely because the inventory exists.

Implementation:
- `src/benchmark/wp2/p2p_inventory_v1.py` + script
  `scripts/wp2_p2p_inventory_v1.py` producing
  `research/wp2/wp2_unchanged_p2p_candidate_inventory_v1_2026-09-23.json`.
- Association rule V1: same top-level Saleor app (first path segment after
  `saleor/`) as any touched production file; unchanged test file (not in the
  target diff); nodes stable 3/3 pass on BOTH parent and target; cap 400 per
  task via deterministic fixed-seed sampling.
- Tests: inventory determinism, unchanged-file requirement, 400-cap behavior.
- Guard: the candidate set lives under evaluator-only paths and is never
  referenced by future generator/repair inputs.

### K. FUTURE E2E DECISIONS — RECORD, DO NOT EXECUTE

Verbatim rule (recorded, not executed in this mission):
- FULL developer change description is the primary specification.
- target-derived signatures/docstrings are forbidden as primary inputs.
- TITLE_ONLY is a later sensitivity analysis.
- new production files may eventually be created under equal arm rules, but
  target-only new file paths must not be handed to Gold.
- edits to test paths are forbidden in all future generation arms.
- empty RM-CSS scopes are intention-to-treat and must not receive an automatic
  fallback.
- future Placebo size is based on Gold files that exist at parent, not RM-CSS
  scope size.
- future Gold-minus-one belongs on DEV after the instrument is frozen.
- future statistical margin, replicate count, INTERNAL_TEST expansion and
  reserve decisions are NOT to be executed now; they depend on later DEV assay
  evidence.
- Do not start implementing the downstream generator because these decisions
  are recorded.

Implementation: recorded verbatim in this artifact (above) and in
`DECISIONS.md` append-only. No generator code is written.

### L. MAIN GENERATION QUARANTINE

Verbatim rule: MAIN may be used now only for evaluator/oracle construction.
Absolutely no code generation, prompt tuning, repair tuning, Smoke, assay
Pilot, or generator debugging on MAIN before the later research freeze.

Implementation:
- `research/wp2/main_generation_quarantine_2026-09-23.json`: all MAIN task IDs
  with state `NO_GENERATION_BEFORE_RESEARCH_FREEZE`.
- Script `scripts/wp2_main_quarantine.py`; test asserts the quarantine file
  covers all 220 changed-test MAIN candidates (and the full 297).

### M. ADDITIONAL HARD STOP

Verbatim rule: all Mission 07 §19 hard stops remain active. Add: STOP if Linux
oracle yield differs sharply across eras and the harness/provenance evidence
cannot demonstrate that the difference is unlikely to be a harness artifact. Do
not explain away the difference and continue.

Implementation: checked in `scripts/wp2_temporal_attrition.py` (D1); STOP token
`WP2_LINUX_V2_ERA_YIELD_HARNESS_AMBIGUOUS` if triggered. This is a STOP, not an
explanatory note.

### N. SCOPE OF THIS RUN

Authorized now: authority/git inspection; impact declaration; Design V2
freeze/amendment; deterministic tests; Linux/Docker/WSL preflight; Linux
filesystem adapter; era environment resolver; dry run; freeze harness SHA; MAIN
220 Linux oracle rerun; DEV 150 zero-model census; DEV changed-test Linux
oracle confirmation; temporal/attrition analysis; unchanged-test P2P candidate
inventory; developer-change-description deterministic feature audit; metadata
reconciliation; provenance hardening; docs/status/progress updates; validation;
git/tag/push; FULL + TRUE LIGHT exports.

NOT authorized now: any LLM/model/API call; OpenRouter; embeddings; AG16;
generation; repair experiments; Gold-vs-Placebo execution; RM-CSS-hard/soft
E2E; Agent-hard E2E; Gold-minus-one execution; MAIN Smoke; MAIN prompt tuning;
INTERNAL_TEST access; RESERVE access; new localization-method development.

---

## O. EXECUTION DISCIPLINE (recorded)

Exactly one TODO in progress. RED/GREEN tests before large rerun; Linux
preflight and bounded dry run before the full sweep; harness SHA/image digests
frozen before the large oracle work. Long runs: live progress, tee logs,
checkpoint every task, resumable state, no `Select-Object -Last`, no rerunning
completed tasks after interruption, full suite once at final T3 validation.
No background execution as an excuse to continue scientific work before a
required gate passes.

---

## Implemented-output registry (what each amendment produces)

| Amendment | Implementation module | Tests | Output artifact |
|---|---|---|---|
| A | `oracle_semantics_v2.py` | `test_oracle_semantics_v2.py` | V2 per-task/per-test records |
| B | `oracle_semantics_v2.py` (regex) | regex tests | provenance `test_patch_rule_sha256` |
| C | canary selection in `oracle_semantics_v2.py` | canary tests | per-task `canary_*` fields |
| D | `era_resolver.py` | `test_era_resolver.py` | era provenance records |
| E | `scripts/wp2_linux_dryrun.py` | dry-run gate | dry-run JSON |
| F | `dev_split_v2.py` | `test_dev_split_v2.py` | `dev_split_v2.json` |
| G | protected-pool guard | `test_protected_pools_v2.py` | guard assertions |
| H | `census_metadata_v2.py` | `test_census_metadata_v2.py` | extended census artifacts |
| I | `scripts/wp2_metadata_reconciliation.py` | `test_metadata_reconciliation.py` | reconciliation JSON/MD |
| J | `p2p_inventory_v1.py` | `test_p2p_inventory_v1.py` | P2P candidate inventory v1 |
| K | (recorded only) | — | this artifact + DECISIONS.md |
| L | `scripts/wp2_main_quarantine.py` | quarantine test | `main_generation_quarantine_2026-09-23.json` |
| M | `scripts/wp2_temporal_attrition.py` | hard-stop gate | temporal-strata report |
| N | (scope gate) | — | this artifact + STOP report |

## Hard-stop confirmation
- No model/API call will occur ($0.00 budget).
- The 786 sealed RESERVE outcomes are never opened.
- INTERNAL_TEST=80 is never accessed.
- MAIN generation/quarantine enforced.
- Historical checkouts live on a Linux filesystem (no NTFS `?` restriction).
- No V1 evidence is overwritten; V2 is a new root
  (`research/wp2/oracle_confirmation_linux_v2_2026-09-23/`).