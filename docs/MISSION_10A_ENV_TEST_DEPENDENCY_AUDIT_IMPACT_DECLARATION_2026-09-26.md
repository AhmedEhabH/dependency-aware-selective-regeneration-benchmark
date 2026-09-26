# Mission-10A — Environment Test-Dependency Audit — Impact Declaration (2026-09-26)

Status: **IMPACT DECLARATION.** Declared before any substantive edit, per the
single authoritative OpenCode Execution & Validation Protocol v2 (Tier T3) and
Mission-10A sections 1-2.

Authority chain: Mission-10A
(`_workspace/active/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_2026-09-26.md`) issued
from the completed Mission-09 checkpoint (decision token `P2P_V2_ENG_READY`).
This mission is a ZERO-LLM scientific validity audit; it is NOT a performance
mission and does NOT generate/execute Smoke/HOLDOUT/VALIDATION/MAIN.

## 1. Execution identity

- Branch: `main`
- HEAD at start: `a9e5ac576e100c11b2d4480cdeaab12dfcef3a6f` == `origin/main`.
- Working tree: pre-existing untracked `logs/` and
  `scripts/watch_c4_reliable.ps1` (Mission-07/08 operational helpers); not part
  of Mission-10A.
- Frozen tag present: `wp2-p2p-v2-eng-freeze-2026-09-25` (annotated), peel
  `f2416d83…` == Mission-09 commit.
- Mission model/API budget: **$0.00. ZERO LLM/OpenRouter/embedding calls.**
- Tier: **T3** (validity audit on a new evaluation-strategy baseline family).
  No generation, no repair, no Smoke, no assay, no E2E, no HOLDOUT/VALIDATION/
  MAIN outcome execution, no INTERNAL_TEST, no RESERVE, no split membership
  change, no P2P-S/P2P-U rule change.

## 2. Scientific question

"Does the frozen V2 environment systematically exclude valid Saleor tests
because project-declared historical test/dev dependencies were not installed or
loaded into pytest?" — answered with the A/B/C/D/E classification and a
preregistered materiality rule (Mission-10A section 14).

## 3. Frozen artifacts read (read-only; immutable)

- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/` — C4 DEV Linux V2
  evidence: `per_test_dev_v2.jsonl`, `summary_dev_v2.json`, `c4_progress.json`,
  `per_task_v2.jsonl`, `c2_junit_rescue_2026-09-23.tar.gz`, `junit/`,
  `junit_manifest_2026-09-23.tsv`, `c2_artifact_manifest_2026-09-23.tsv`,
  `dev_census_2026-09-23.json`, `harness_v2_freeze_2026-09-23_REVISED.json`,
  `linux_substrate_preflight_2026-09-23.json`.
- `research/wp2/oracle_confirmation_2026-09-22/` — C2/Main older oracle
  evidence (`per_task.jsonl`, `per_test.jsonl`, `summary.json`) where
  available.
- `research/wp2/p2p_u_v2_eng_2026-09-25/` — Mission-09 P2P-U ENG evidence
  (per-task cap200/cap400 `manifest.json`, `node_classes.json`,
  `node_outcomes.json`, `junit/`, `logs/`), `consolidated_results_2026-09-25.json`.
- `research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json`,
  `research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json`,
  `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json`,
  `research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json`,
  `research/wp2/mission07_result_summary_2026-09-25.json`.
- Environment logic: `scripts/wp2_linux_dryrun.py` (`deps_install_cmd`,
  `TOOLING_INSTALL`), `scripts/wp2_p2p_u_v2_exec.py`,
  `src/benchmark/wp2/era_resolver.py`, `src/benchmark/wp2/environment_manager.py`,
  `scripts/wp2_oracle_confirm.py` (C2/C4 installer), `harness_v2_freeze_*`,
  frozen era image digests.
- Target-commit dependency manifests from the Saleor cache repo
  (`dist/pilot-repo-cache/saleor`, mirrored at `/opt/wp2_v2/saleor-cache` in
  WSL): pyproject.toml / poetry.lock / requirements*.txt / setup.cfg at the
  exact target commits of the affected tasks.
- `dist/pilot-repo-cache/saleor` git object store for `git show
  <target_commit>:<manifest>`.

## 4. New audit artifacts to create

Under `research/wp2/mission10a_env_audit_2026-09-26/`:

1. `error_records.jsonl`
2. `error_taxonomy_summary.json`
3. `dependency_declaration_matrix.json`
4. `frozen_v2_installed_state.json`
5. `pytest_plugin_state.json`
6. `category_exclusion_analysis.json`
7. `preregistered_materiality_rule.json`
8. `probe_selection.json`
9. `probe_results.json` (only if the optional probe runs)
10. `v3_impact_estimate.json`
11. `mission10a_summary.json`

Each with schema/version, created date, source artifact identities/hashes,
deterministic ordering.

## 5. Existing docs/progress files to update

- `PROGRESS.md` — Goal→Outcomes→Drivers→Actions→Schedule→Tracking→Reflection
  block (compact, inside existing PROGRESS.md, per Mission-10A section 26).
- `DECISIONS.md` — append audit decision/assumptions (append-only).
- `docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_STOP_REPORT_2026-09-26.md` — new
  human-readable STOP report.
- `docs/LIVE_STATUS.json` + 4 current-facing files via
  `scripts/render_live_status.py --write` (end of mission outcome block).
- Docs errata ONLY where machine-readable evidence supports the exact corrections
  listed in Mission-10A section 25 (COLLECTION_ERROR 41 not 40; evidence-size
  wording if recomputation confirms; SETUP_ERROR:MISSING_FIXTURE subtype when
  supported). No frozen Mission-09 scientific outcome rewrite — errata appended.

## 6. Code/scripts to add or modify

- New zero-LLM audit scripts under `scripts/` (prefix `wp2_m10a_`):
  error taxonomy parser + reconciliation, fixture→package mapping,
  declared-vs-installed matrix, plugin-state introspection, category-exclusion
  analysis, materiality decision, probe selection, scratch-probe runner
  (ENG-only), summary/aggregation. Deterministic, no LLM.
- New tests under `tests/unit/wp2/` covering the audit logic (error parser,
  declaration resolution, plugin state, materiality, probe reconciliation).
- No change to frozen harness/era/oracle code. `scripts/wp2_linux_dryrun.py`
  and `scripts/wp2_p2p_u_v2_exec.py` are READ-ONLY references.

## 7. Dependencies affected

- No dependency install/upgrade in the frozen V2 environment.
- The optional scratch probe creates a disposable NON-FROZEN derivative
  container only; it may install ONLY the project-declared historical
  test/dev dependency group or exact missing package set at historical
  locked/pinned versions. Scratch is labeled
  `NON_FROZEN_EXPLORATORY_ENV_PROBE` and is never merged into frozen artifacts.

## 8. Explicitly stated (non-negotiables)

- **NO frozen image mutation** (no retag/overwrite of `wp2-era-*`, no global
  cache semantics change).
- **NO oracle rewrite** (no Mission-07 C4/C2, Mission-08 V1, Mission-09
  P2P-S/P2P-U artifact modification).
- **NO generation**, **NO Smoke execution**, **NO HOLDOUT/VALIDATION/MAIN
  execution**, **NO DEV-47 P2P-U execution**, **NO INTERNAL_TEST**, **NO RESERVE**.
- **NO automatic continuation into Env V3 / Smoke / DEV-47.** The audit STOPS
  after producing one decision token and waits for Ahmed.

## 9. Verification plan (targeted)

- Error parser: fixture/module-not-found extraction, phase detection,
  normalization, duplicate/missing-raw-message handling.
- Declaration resolution: pyproject groups, poetry.lock, uv.lock, pinned
  requirements, no-lock fallback, markers.
- Plugin state: package absent / installed-no-entry-point /
  entry-point-registered-not-loaded / loaded-fixture-visible.
- Materiality logic: V3-recommended / V2-adequate / inconclusive cases.
- Probe reconciliation: exact node identity, class transitions, missing/duplicate/
  orphan guards.
- py_compile + ruff + mypy (production audit modules) + targeted unit tests.
  No full historical project suite.

## 10. Scientific guardrails honored

- Ground Truth evaluation-only; no leakage across the frozen split firewall.
- C: free-space guards preserved (warning <40 GiB, hard stop <32 GiB; current
  ≈50.4 GiB).
- Frozen artifacts are IMMUTABLE; all evidence is read or derived, never
  overwritten.
- LOCKFILE-FIRST: any scratch probe uses the exact historical locked/pinned
  versions; never unconstrained `pip install`.