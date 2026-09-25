# WP-2 Linux Oracle V2 + DEV Pool — Impact Declaration (2026-09-23)

Status: **IMPACT DECLARATION.** Declared before substantive edits, per Mission
07 §2 and amendment O. Authority chain: Mission 07
(`07_OPENCODE_WP2_LINUX_ORACLE_AND_DEV_POOL_MISSION_2026-09-23.md`) amended by
the Claude Opus 5.5 review (A–N amendments, frozen below in
`docs/WP2_DESIGN_V2_AMENDMENT_FREEZE_2026-09-23.md`).

## 1. Execution identity

- Branch: `main`
- HEAD at start: `493924efd7d3f95bbf9f734bc51c15a48b79c1b9` == `origin/main`
  (mission's expected main; live origin wins; no reset performed; tree clean).
- Mission model/API budget: $0.00. Zero LLM/OpenRouter/embedding/AG16 calls.

## 2. Files and outputs this mission WILL create or change

### 2.1 Linux execution adapter / container files (new)
- `src/benchmark/wp2/linux_adapter.py` — Linux filesystem/worktree adapter:
  historical `?` filenames, container/WSL command execution, safe path handling.
- `src/benchmark/wp2/era_resolver.py` — era environment resolver: one controlled
  base image per Python/environment era, immutable digests, pinned installer
  versions, lockfile SHA, offline test execution, no silent fallback.
- `scripts/wp2_linux_preflight.py` — substrate preflight (Docker Desktop/WSL).
- `scripts/wp2_linux_dryrun.py` — bounded real-task Linux dry run.

### 2.2 Node-level classification change (new semantics module + tests)
- `src/benchmark/wp2/oracle_semantics_v2.py` — mechanical V2 node-level
  classification: `PARENT_COLLECTION_ERROR`, `SYMBOL_ABSENCE_F2P`,
  `BEHAVIORAL_F2P`; task-level primary eligibility; test-patch regex freeze;
  environment canary semantics; P2P V1 candidate rule.
- `tests/unit/wp2/test_oracle_semantics_v2.py` — RED/GREEN classification tests.
- Windows v1 evidence is preserved; v1 taxonomy is not rewritten in place.

### 2.3 Provenance schema (new)
- `src/benchmark/wp2/provenance_schema_v2.py` — `oracle_harness_schema_v2` with
  mandatory non-`None` provenance fields (harness SHA, classifier bundle SHA256,
  OS/distro, image digest, Python version, lockfile SHA, dependency hash,
  parent/target SHA, DB/service versions, commands, JUnit/output hashes,
  timestamp).
- `tests/unit/wp2/test_provenance_schema_v2.py`.

### 2.4 DEV census / oracle outputs (new, under `research/wp2/oracle_confirmation_linux_v2_2026-09-23/`)
- DEV 150 zero-model census (added/modified/no-evidence, migration/config,
  commit year / environment family).
- DEV split freeze: `DEV_TRAIN_ENG` ≈ 40 / `DEV_TRAIN_ASSAY_HOLDOUT` ≈ 80
  (deterministic salted split of frozen `DEV_TRAIN=120`), `DEV_VALIDATION=30`
  separate.
- DEV changed-test Linux oracle confirmation (C4).
- Temporal-strata report (D1).
- MAIN 220 Linux V2 oracle rerun (C2).
- P2P unchanged-test candidate inventory v1 (D2).
- Developer-change-description deterministic feature audit (D3).
- Metadata reconciliation artifact (D4).
- MAIN generation quarantine manifest (E1).

### 2.5 Documentation touched
- `docs/WP2_LINUX_ORACLE_V2_DEV_POOL_IMPACT_DECLARATION_2026-09-23.md` (this file).
- `docs/WP2_DESIGN_V2_AMENDMENT_FREEZE_2026-09-23.md` (A–N freeze + mapping).
- `docs/reviews/CLAUDE_OPUS_5_5_WP2_SCIENTIFIC_REVIEW_2026-09-23.md`.
- `docs/WP2_WINDOWS_V1_TO_LINUX_V2_RECONCILIATION_2026-09-23.md`.
- `docs/WP2_METADATA_RECONCILIATION_2026-09-23.md`.
- `docs/WP2_PRESERVATION_ORACLE_PREP_2026-09-23.md`.
- `docs/WP2_LINUX_ORACLE_V2_DEV_POOL_STOP_REPORT_2026-09-23.md`.
- `README.md` / `START_HERE_CURRENT_*` / `PROGRESS.md` /
  `00_CURRENT_RESEARCH_STATE.md` / `docs/LIVE_STATUS.json` (live-status block)
  via `scripts/render_live_status.py --write` at E1.
- `DECISIONS.md` (append-only new decisions at the end).

## 3. Explicit non-changes (WP-1 / RM-CSS / Agent)
- No change to any frozen WP-1 artifact: `wp1b_agent_predictions.json`,
  `sip_rmcss_per_task_predictions.json`, decision rules, margins, protocols.
- No modification of RM-CSS or Agent predictions or prediction files.
- No regeneration, repair tuning, prompt tuning, Smoke, assay Pilot, or
  selector E2E on MAIN or DEV in this mission (amendments G, K, L, N).
- The 786 sealed Saleor RESERVE outcomes remain sealed and are never
  listed/read/opened/scored beyond already-authorized aggregate metadata.
- `INTERNAL_TEST=80` remains untouched (amendment G).
- Windows v1 evidence under `research/wp2/oracle_confirmation_2026-09-22/` is
  never overwritten.

## 4. Verification plan
- RED/GREEN classification tests before any large rerun (amendment A/E/O).
- Linux preflight + bounded real-task dry run (incl. one 2025–2026/Python 3.12
  task) before the full 220 MAIN + DEV confirmation (amendment E).
- Harness SHA and image digests frozen before the large rerun (Mission 07 §4).
- Targeted tests, ruff, py_compile, mypy on changed production files; full
  pytest suite once at the final validation gate (T3).
- `git diff --check` before commits; exact staging; conventional commits.

## 5. Scientific guardrails honored
- Ground Truth remains evaluation-only; no selector/outcome-based scientific
  inclusion decisions (Mission 07 §8).
- No RM-CSS-vs-Agent selector comparison on DEV as thesis evidence
  (Mission 07 §9; amendment F).
- No full-suite repeated runs during development; exactly one final run.
- Hard stops of Mission 07 §19 remain active, extended by amendment M.