# Mission-10B — Harness V3 Gold Mission — Impact Declaration (2026-09-26)

Status: **IMPACT DECLARATION.** Declared before any substantive edit, per the
single authoritative OpenCode Execution & Validation Protocol v2 (Tier T3) and
Mission-10B sections 1-2.

Authority chain: Mission-10B
(`_workspace/active/MISSION_10B_HARNESS_V3_GOLD_2026-09-26.md`) issued from the
completed Mission-10A checkpoint (decision token `ENV_AUDIT_INCONCLUSIVE`).
This mission is a ZERO-LLM scientific validity/audit mission; it performs no
model/API generation, no Smoke execution, no C2/MAIN V3 rerun, and no full
DEV-47 P2P-U V3 execution.

### Impact Declaration — mission-10b-harness-v3

## 1. Execution identity

- Branch: `main`
- HEAD at start: `9ce11c73530c6a7121680d4800f94804af430b4b` == `origin/main`
  (verified reconciled before new work).
- Mission-10A scientific commit `25dfa7c6bc9fe63b59c12743b69d82e2b4d2f3c5` is an
  ancestor of HEAD (verified). Later main commits `9633ff17`, `9ce11c73`
  (export/report tooling) are descendants.
- Frozen tag present: `wp2-env-audit-2026-09-26` (annotated tag object
  `2cb34756…`), peel `25dfa7c6bc9fe63b59c12743b69d82e2b4d2f3c5` == Mission-10A
  scientific commit (verified via `git for-each-ref`).
- Working tree: pre-existing untracked `logs/` and
  `scripts/watch_c4_reliable.ps1` (Mission-07/08/10 operational helpers); known
  untracked operational logs/scripts, not part of the scientific repo.
- Mission model/API budget: **$0.00. ZERO LLM/OpenRouter/embedding calls.**
- Tier: **T3** (validity audit + evaluator reconstruction on a new
  infrastructure candidate — Harness V3).

## 2. Scientific question (GOAL A)

Does the frozen V2 oracle/evaluator invalidate a material number of
TARGET_ORACLE_INVALID nodes through infrastructure defects — specifically
OSError [Errno 24] Too many open files (EMFILE) during Django test-DB
creation/migrations, DB reuse/WRONG_CONSTRAINTS, missing declared dev/test
dependencies, and clock-skew time exceptions — and does a minimal Harness V3
(infrastructure-only, no oracle-semantic change) correct them? The primary
validity question is NODE-LEVEL, never task-level co-occurrence.

## 3. Frozen evidence read (read-only; immutable)

- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/` — C4 DEV Linux V2
  evidence: `per_test_dev_v2.jsonl`, `per_task_dev_v2.jsonl`, `summary_dev_v2.json`
  (authoritative C4 TARGET_ORACLE_INVALID = 3,727; error-bearing 3,682;
  failed-only 45), `c4_progress.json`, `summary_v2.json` (C2 MAIN),
  `c2_junit_rescue_2026-09-23.tar.gz`, `junit/` (1,559 files, full-text),
  `junit_manifest_2026-09-23.tsv`, `c2_artifact_manifest_2026-09-23.tsv`,
  `dev_census_2026-09-23.json`, `dev_split_v2_2026-09-23.json`,
  `harness_v2_freeze_2026-09-23_REVISED.json`, `linux_substrate_preflight_2026-09-23.json`.
- `research/wp2/oracle_confirmation_2026-09-22/` — C2/Main older oracle evidence
  where available.
- `research/wp2/p2p_u_v2_eng_2026-09-25/` — Mission-09 P2P-U ENG evidence
  (per-task cap200/cap400 `manifest.json`, `node_classes.json`,
  `node_outcomes.json`, `junit/`), `consolidated_results_2026-09-25.json`
  (authoritative 41 cap200 COLLECTION_ERROR nodes).
- `research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json`,
  `research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json`,
  `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json`,
  `research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json`.
- Mission-10A audit outputs: `research/wp2/mission10a_env_audit_2026-09-26/`
  (taxonomy, dependency matrix, plugin state, probe results).
- Environment logic: `scripts/wp2_linux_dryrun.py`, `scripts/wp2_linux_dev_sweep.py`,
  `scripts/wp2_linux_main_sweep.py`, `scripts/wp2_linux_main_orchestrator.py`,
  `scripts/wp2_p2p_u_v2_exec.py`, `scripts/wp2_m10a_*.py`,
  `src/benchmark/wp2/` (era_resolver, environment_manager, linux_adapter,
  oracle_runner, oracle_semantics_v2, provenance_schema_v2, m10a_audit,
  dev_split_v2, p2p_inventory_*, p2p_s_freeze_v1, p2p_u_v2, resource_sampler).
- Frozen era images verified present in WSL Docker: `wp2-era-py38`,
  `wp2-era-py39`, `wp2-era-py312`, `postgres:15-alpine`
  (digests match `harness_v2_freeze_2026-09-23_REVISED.json`).
- Saleor cache substrate healthy at `/opt/wp2_v2/saleor-cache` (git worktree
  list OK). PostgreSQL container `wp2-pg` healthy (pg_isready accepting).
- C: free = 49.8 GiB at mission start (above WARNING 40 GiB / HARD STOP 32 GiB).

## 4. New scientific outputs (under `research/wp2/harness_v3_2026-09-26/`)

Per Mission-10B §4 (immutable-output rule) all new scientific outputs go under:

`research/wp2/harness_v3_2026-09-26/`

Planned machine-readable artifacts (each with schema/version, created date,
source artifact identities/hashes, deterministic ordering):

1. Full-text error extraction records (C4 + C2 rescue + P2P-U ENG) — full
   `<error>`/`<failure>` text, final normalized exception, taxonomy.
2. Node-level causal attribution tables (STABLE_CAUSE / MIXED_CAUSE /
   MISSING_EVIDENCE per authoritative C4 TARGET_ORACLE_INVALID node, 3 target
   reps each; equivalent for C2 rescue TOI coverage).
3. Reconciliation tables (C4 3,727 = 3,682 error + 45 failed-only; P2P-U 41).
4. EMFILE RCA evidence (container limits, reproduction, uplifted-nofile test).
5. DB reuse / WRONG_CONSTRAINTS RCA evidence.
6. Historical lockfile/dependency audit + INSTALL_MODE decisions.
7. Clock-skew audit + AT_RISK_F2P list.
8. Harness V3 freeze (human doc `docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md` +
   machine-readable V3 spec + hashes).
9. Preregistered V3 decision rules (before Phase 3).
10. Four-task ENG probe evidence + transition matrix.
11. Phase-4 gate (`gate.json`, `gate.md`).
12. ENG_V3_ORACLE_READY checkpoint, P2P-S V3 ENG, P2P-U V3 ENG cap200/cap400
    (only if gate passes).
13. ENG_SMOKE_READY checkpoint (only if gate passes).
14. Full C4 V3 closure/reconciliation (only if gate passes and continued).
15. Resource/performance/quality metric summaries.
16. STOP report + FULL + TRUE LIGHT exports.

## 5. Existing docs/progress files to update

- `PROGRESS.md` — Mission-10B progress frame updates at durable checkpoints
  (execution source of truth).
- `DECISIONS.md` — append audit decisions (append-only).
- `docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md` — new freeze doc (Phase 2).
- `docs/MISSION_10B_HARNESS_V3_STOP_REPORT_2026-09-26.md` — new STOP report
  (at closure/STOP).
- `docs/LIVE_STATUS.json` + 4 current-facing files via
  `scripts/render_live_status.py --write` (end-of-mission outcome block).
- Smoke DRAFT population update only (no final Smoke protocol freeze).

## 6. Code/scripts to add or modify

New zero-LLM deterministic code (prefix `wp2_m10b_` / `wp2_v3_`):

- Full-text JUnit error extraction (fixes Mission-10A truncated
  `raw_error_text[:1200]` limitation): full `<error>`/`<failure>` element text
  with the extraction precedence from Mission-10B §7.1.
- New taxonomy (Mission-10B §7.2): INFRA:EMFILE, DB:WRONG_CONSTRAINTS,
  DB:SET_SESSION_IN_TXN, DB:OTHER, MISSING_FIXTURE, MODULE_NOT_FOUND,
  IMPORT_ERROR, TIME:* (IMMATURE_SIGNATURE/EXPIRED_SIGNATURE/NBF/FREEZEGUN/
  TIMEZONE/OTHER), INSTALL, COLLECTION, OTHER.
- Node-level attribution engine (STABLE_CAUSE/MIXED_CAUSE/MISSING_EVIDENCE).
- EMFILE RCA probe runner (scratch container, ulimit measurement,
  uplifted-nofile comparison, FD/process/memory sampling).
- DB reuse / WRONG_CONSTRAINTS scratch probe.
- Lockfile/dependency audit (LOCKFILE-FIRST rule, INSTALL_MODE).
- Clock-skew measurement + V3 clock preflight.
- Harness V3 runner/orchestrator changes (nofile, per-(task,state) unique fresh
  DB lifecycle, lock-exact install, clock preflight, manifest v3).
- Resource sampler reuse (Mission-09) + extension for V3 needs.
- P2P-S V3 ENG extraction, P2P-U V3 ENG rediscovery/execution (only if gate
  passes).
- Summary/reconciliation/gate/report tooling.
- Tests under `tests/unit/wp2/` covering: full-text parser (EMFILE,
  WRONG_CONSTRAINTS, SET_SESSION, missing fixture, module missing, import
  error, time exceptions, exception tail selection, truncated-text regression,
  node/rep reconciliation, mixed-cause), V3 install, clock, DB, orchestrator,
  P2P, resource.

Modification of frozen harness files is limited to the V3 runner/orchestrator
and the taxonomy parser; frozen era images are NOT rebuilt or retagged (no new
Docker image build authorized — V3 changes are container-runtime only).

## 7. Runtime/container changes proposed

- Harness V3 test containers add `--ulimit nofile=65536:65536` (V3 freeze
  item A).
- Containers remain based on the frozen era images (`wp2-era-py38/39/312`) —
  no new image build/tag.
- Unique container names `wp2-t3-<task12>-<state>-<worker>` under workers=2
  (Phase 5, gate-dependent).

## 8. DB lifecycle changes proposed

- Per (task,state): unique DB name; create fresh at state start; never reuse a
  partially created DB; DROP at task completion; within repetitions of one
  successfully-initialized state `--reuse-db` only if it matches C4 semantics
  and never crosses parent/target state boundaries.
- If Phase 1D disproves reuse amplification: document fresh per-state DB as
  isolation, not proven causal repair.
- Never reuse a DB whose creation failed.

## 9. Dependency-install changes proposed

- LOCKFILE-FIRST: exact historical lock/pin; then historical constraint; range
  only when no lock exists. Never install today's latest unconstrained package.
- Preferred V3 INSTALL_MODE: LOCK_EXACT_MAIN_PLUS_DEV
  (uv: `uv sync --frozen --group dev` / `uv export --frozen --group dev`;
  Poetry: exact historical poetry.lock main+dev set).
- Fallback (only if full project lock install impossible):
  V2_MAIN_PLUS_EXACT_LOCKED_DEV.
- Harness-only tooling retained at frozen V2 versions; no re-resolution of the
  project graph.
- Every task records INSTALL_MODE; if no historically faithful mode exists:
  ENV_INSTALL_BLOCKED (rule not weakened).

## 10. Clock-preflight changes proposed

- Measure median host↔WSL skew (midpoint method, >=3 samples) before every V3
  task.
- <=0.5 s PASS; >0.5 s: ONE safe WSL clock resync; after resync <=1.0 s
  continue, >1.0 s CLOCK_BLOCKED (no task).
- Never silently change Windows host time; `wsl --shutdown` only when no
  scientific task is running, with persist/checkpoint first and frozen image
  verification after restart.

## 11. Resource/concurrency changes proposed

- Phase 3 probes: workers=1 only.
- Phase 5 (gate-dependent): workers=2 TASK-LEVEL parallelism, unique worktree/
  container/DB/JUnit/logs/temp per worker; shared read-only caches.
- Mission-09 resource sampler reused; sample every 5 s (host/WSL/docker/
  harness).
- Guards: C free >=32 GiB, host available >=2.5 GiB, WSL MemAvailable >=2 GiB
  before worker 1; >=5 GiB / >=3 GiB prefer before worker 2; 2→1 adaptive
  fallback allowed (no semantic change); graceful hard stop at C free <32 GiB.
- W2 equivalence gate before continuing to non-ENG C4.

## 12. Testing / validation plan

- py_compile on all changed files.
- ruff on changed files.
- mypy strict on changed production Python files.
- Targeted unit/integration tests: full-text parser suite, V3 install modes,
  clock preflight, DB lifecycle, orchestrator (one-writer, resume, DONE
  validation, STOP flag, transaction cleanup, ENG barrier, workers isolation,
  w2-equivalence stop), P2P-S/P2P-U extraction + salt unchanged + first200⊆
  first400 + membership diff.
- Existing WP2 unit tests run where shared WP2 code changed.
- No unrelated full suite merely for ceremony.
- `git diff --check` before each durable commit.

## 13. Explicit forbidden scope (non-negotiables)

- No LLM/model/API generation anywhere in this mission ($0.00).
- No Smoke generated-patch execution; no repair generation; no assay
  generated-patch execution.
- No HOLDOUT/VALIDATION model-arm tuning; no using corrected holdout/validation
  outcomes to change V3 rules.
- No C2/MAIN V3 rerun; no full DEV-47 P2P-U V3 execution; no INTERNAL_TEST;
  no RESERVE.
- No changing frozen splits; no changing F2P/P2P semantic definitions; no
  changing P2P-U V2 sampling rule/salt; no changing V2 history.
- No building/retagging replacement frozen Docker images.
- No weakening of any gate after seeing outcomes (incl. Phase-4 mechanical
  gate).
- No submission of routine questions to Ahmed (autonomy per Mission-10B §38);
  Phase-4 gate authorizes unattended Phase-5 continuation if all conditions
  pass.

## 14. Output roots

- All new scientific outputs: `research/wp2/harness_v3_2026-09-26/`.
- Human-readable docs: `docs/` using existing naming conventions.
- Logs: `logs/` (operational; untracked).

Declared 2026-09-26 by OpenCode executing Mission-10B.