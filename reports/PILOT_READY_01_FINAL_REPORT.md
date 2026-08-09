# PILOT-READY-01 Final Report — Multi-Repo Selective Input Contract Closure

## 1. Executor identity

- Provider: openrouter
- Model: nvidia/nemotron-3-ultra:free
- Build/session label: opencode/big-pickle (local session on Windows/PowerShell)
- Elapsed time: closure work executed 2026-08-10 (Gates 1–7, exact 48-cell dry-run, docs closure)

## 2. Git state before work

- Branch: `feat/pilot-ready-01`
- Local HEAD: `34ecf786901aec29659ea039a8f1fdf00039b5f2`
- Remote feature HEAD: `34ecf786901aec29659ea039a8f1fdf00039b5f2`
- origin/main: `592fc508ba1df596f685d80f2e0a35a4317d0299`
- Working tree: clean (verified before docs changes)
- Existing pushed commits being preserved: `34ecf78` (fix(pilot): close multi-repo selective input contracts), `c638ad4` (docs/validation records), `24ef163` (freeze), `061844e`, `bf954a0` — none amended, rebased, or rewritten

## 3. Where we are

- Active task: PILOT-READY-01 (Pilot readiness closure)
- Feature status: CLOSED (2026-08-10)
- Near-term goal: main merge of the closure + stable tag `v0.9.0-pilot-ready`, then `PILOT-EXEC-01`
- Long-term research goal: dependency-aware selective regeneration research experiment (Smoke complete/accepted; Pilot next)
- Pilot started? NO

## 4. Exact changes made

| File | Symbol/section changed | Previous problem | Exact change | Why this is the root-cause fix | Dependencies affected | Tests covering it | Scientific semantics changed? |
|------|------------------------|------------------|--------------|-------------------------------|-----------------------|-------------------|-------------------------------|
| `seven_arm_benchmark.py` | `build_dependency_graph` (line ~521) | On mixed-repository plans the function silently reused the FIRST repository's graph for every run | Now fails closed (`ValueError`) when scenarios span more than one repository; single-repository semantics documented in the docstring | Mixed-repo Pilot plans can no longer silently feed repo A's dependency graph into repo B's runs | `build_repository_dependency_graphs`, Pilot run loop | `tests/unit/test_pilot_multi_repo_input_contract.py` (14) | NO |
| `seven_arm_benchmark.py` | `build_repository_dependency_graphs` (new, line 611) | No per-repository graph existed; one graph served all repos | New function groups scenarios by `scenario.repository` and returns `{repo_id: graph}` with one graph per repository | Repository-specific impact inputs now come from that repository's own scenarios/profile | Pilot run loop `_dep_graphs` | `tests/unit/test_pilot_multi_repo_input_contract.py` (14) | NO |
| `seven_arm_benchmark.py` | Pilot run loop `_dep_graphs` (line ~2199, used at ~2506) | Looked up a single global graph | `_dep_graphs = build_repository_dependency_graphs(...)`; `run_arm(..., dep_graph=_dep_graphs[repository_id], ...)` per run spec; per-repo `_editable_paths[repo_id]`, `_artifact_descriptors[repo_id]` | Each Pilot run consumes its own repository's graph/editable universe/descriptors | `src/benchmark/repositories/snapshot.py`, `src/benchmark/selection/dependency_scope.py` | `tests/integration/test_pilot_multi_repo_production_path.py` (12) | NO |
| `src/benchmark/repositories/snapshot.py` | `expand_editable_paths` (line ~237), `_EXPANSION_EXCLUDED_DIRS` (line 82), `resolve_allowed_artifacts` (line ~296) | Editable-path expansion was applied globally instead of per repository profile; directory policy entries were not resolved to concrete files with strict guards | Per-repository expansion: directory entries deterministically expanded to concrete repository-relative `.py` files; strict guards (repository-relative only, no traversal/backslash, duplicates rejected, tests/migrations/caches never expandable, empty directory resolution fails closed) | Editable universe must be file-granular and bounded per repository or regeneration scope leaks | `benchmark.repositories.snapshot` import at `seven_arm_benchmark.py` ~2133 | `tests/unit/test_pilot_multi_repo_input_contract.py` (14), `tests/integration/test_pilot_multi_repo_production_path.py` (12) | NO |
| `src/benchmark/repositories/loader.py` | `_normalize_artifact_catalog` (line ~19), `load_manifest` (line ~135) | Artifact-catalog normalization produced category-key descriptors for django CMS/Saleor instead of file-granular catalog items | Catalog items are normalized to file-granular entries (reject category-key/grouping entries) so the dependency scope can resolve file-level descriptors | Category-key descriptors could not map onto per-repo file universes | `src/benchmark/selection/dependency_scope.py` | `tests/unit/test_pilot_multi_repo_input_contract.py` (14) | NO |
| `src/benchmark/selection/dependency_scope.py` | `descriptors_from_profile` (line ~143) | Descriptors were not guaranteed to be file-granular and within the per-repo editable universe | Returns file-granular descriptors ⊆ the per-repo editable universe (single `ProfileArtifactDescriptor.profile_id` invariant) | Ensures selective strategy selects only artifacts that are truly editable for that repository | `src/benchmark/repositories/snapshot.py` | `tests/unit/test_pilot_multi_repo_input_contract.py` (14), `tests/integration/test_pilot_multi_repo_production_path.py` (12) | NO |
| `tests/integration/test_real_smoke.py` | `STRATEGIES_WITH_MISSING_PREREQS` (line ~120) | Stale expectation: `selective` was listed as expecting failure on missing prerequisites | Corrected set = `{"agent"}`; `has_missing_prereqs` at line ~135 | The stale expectation was a leftover from the pre-Pilot era; the real contract is that only `agent` expects missing-prereq failure | none | `tests/integration/test_real_smoke.py` (9) | NO |
| `tests/unit/test_pilot_multi_repo_input_contract.py` (new, 14 tests) | n/a | No unit contract existed for per-repo graphs, editable universes, and file-granular descriptors | Added the 14-test unit contract (mixed-repo fail-closed, per-repo graph keys, editable expansion guards, catalog normalization, descriptor granularity) | Locks the fixed contracts at unit level | none | self | NO |
| `tests/integration/test_pilot_multi_repo_production_path.py` (new, 12 tests) | n/a | No focused production-path integration contract existed for multi-repo plans | Added the 12-test integration contract exercising the full production path with mixed repositories (run loop, per-repo graphs, editable paths, descriptors), repeated twice with no state leak | Proves the production path end-to-end, not just unit-level contracts | production run loop | self (repeated run = no state leak) | NO |

## 5. Before -> After behavior

Mixed-repository dependency graph (root cause A):

Before:
```
mixed scenarios -> first repo's snapshot -> ONE graph -> reused for every run (repo A graph feeds repo B runs)
```
After:
```
mixed scenarios -> group by repository -> graph[repo_id] (one graph per repo) -> run uses _dep_graphs[repository_id]
mixed scenarios -> build_dependency_graph -> ValueError (fail closed, no silent single-repo reuse)
```

Editable directory expansion (root cause B):

Before:
```
global expansion -> one editable path set applied to every repository (cross-repo scope leakage)
```
After:
```
per-repository expand_editable_paths(snapshot, allowed) -> _editable_paths[repo_id]
directory policy entries deterministically expanded to file-granular repository-relative .py paths with strict guards (no traversal / no tests/migrations/caches / empty expansion fails closed)
```

Artifact catalog normalization (root cause C):

Before:
```
catalog normalization -> category-key descriptors (grouping entries) for django CMS / Saleor
```
After:
```
_normalize_artifact_catalog -> file-granular catalog items
descriptors_from_profile -> file-granular descriptors ⊆ per-repo editable universe (single profile_id invariant)
```

Stale integration expectation (root cause D):

Before:
```
STRATEGIES_WITH_MISSING_PREREQS contained "selective" -> real-smoke expected selective to fail on missing prereqs
```
After:
```
STRATEGIES_WITH_MISSING_PREREQS = {"agent"} -> only agent expects missing-prereq failure; selective runs normally
```

## 6. Test evidence

| Gate | Exact command | Result | Passed | Failed | Skipped | Runtime | Fresh output? | Notes |
|------|---------------|--------|--------|--------|---------|---------|----------------|-------|
| 1 (targeted unit) | `python -m pytest -q tests/unit/test_pilot_multi_repo_input_contract.py` | PASS | 14 | 0 | 0 | — | YES | unit contract for per-repo graphs/editable universes/descriptors |
| 2 (integration) | `python -m pytest -q tests/integration/test_real_smoke.py` | PASS | 9 | 0 | 0 | — | YES | corrected stale expectation set |
| 3 (repeated stateful integration) | `python -m pytest -q tests/integration/test_pilot_multi_repo_production_path.py` | PASS (run twice) | 12 | 0 | 0 | — | YES | run twice with no state leak; not an 8/8 targeted dry-run |
| 4 (static) | `ruff check` (changed files), `mypy --strict` (changed prod files), `python -m py_compile` | PASS | — | 0 new | — | — | YES | feature-caused mypy findings fixed; 5 pre-existing mypy + 3 pre-existing ruff recorded as debt |
| 5 (exact 48-cell dry-run) | `python seven_arm_benchmark.py --dry-run --profile pilot` (fresh dir `runs/pilot_dryrun_48cell_20260810_012744`) | PASS | 48 planned / 48 terminal / 48 succeeded | 0 | 0 pending | — | YES | 48 unique deterministic run IDs, 0 missing, 0 dups; config_hash `7ef6ffc7a2c0d369`; protocol 1.0; source_commit `34ecf78`; checkpoint `completed` |
| 6 (isolation/evidence/export) | `python -m pytest -q tests/unit/test_pilot_readiness.py tests/unit/test_pilot_multi_repo_input_contract.py tests/integration/test_pilot_multi_repo_production_path.py tests/unit/test_su0005_explicit_identity.py tests/unit/test_su0006_recovery_activation.py tests/unit/test_su0007_continuous_execution.py tests/integration/test_real_smoke.py` | PASS | 142 | 0 | 0 | 5.55 s | YES | identity/provenance, fresh-output fail-closed, recovery/no-residue, cross-repo isolation |
| 7 (final full suite) | `python -m pytest -q` | PASS | 2,026 | 0 | 33 | 736.29 s | YES | prior RED baseline = 1 failed / 2,013 passed / 33 skipped |

## 7. Exact Pilot matrix evidence

- scenario count: 12 (todo-loc-001, todo-loc-002, todo-mod-004, todo-cross-007, djangocms-loc-002, djangocms-mod-004, djangocms-mod-005, djangocms-cross-007, saleor-loc-001, saleor-loc-002, saleor-mod-004, saleor-cross-007)
- strategy count: 2 (selective, iterative_repository_agent)
- repetitions: 2
- expected total: 48
- actual total: 48
- unique run IDs: 48
- missing IDs: 0
- duplicate IDs: 0
- counts per repository: todo=16, djangocms=16, saleor=16
- counts per strategy: selective=24, iterative_repository_agent=24
- counts per repetition: 1=24, 2=24
- output directory: `runs/pilot_dryrun_48cell_20260810_012744` (gitignored, not committed)
- checkpoint freshness: checkpoint.json `completion_status = completed`, `total_completed = 48`, `last_update` after final run; `COMPLETED` marker present
- Pilot real execution status: NOT STARTED (dry-run only, deterministic mock backend)

## 8. Pre-Benchmark Validation

- Dataset Validation: PASS (carried forward — benchmark data unchanged; repository_versions.yaml `verified` for Todo / django CMS 5.0.0 / Saleor 3.23.0). Evidence: repository profile files + PILOT-READY-01-DJANGOCMS/SALEOR validation records.
- Prompt Validation: PASS (carried forward — no prompt changes in this feature; frozen). Evidence: previous prompt gate, no diff to prompt artifacts.
- Pipeline Smoke Test: PASS (integration suite green including real-smoke; corrected stale expectation). Evidence: Gate 2 + Gate 6.
- Dry Run: PASS (exact fresh 48-cell Pilot dry-run 48/48 deterministic). Evidence: Gate 5 + section 7.
- Integration Test: PASS (production-path 12 ×2, isolation 142, final full suite 2,026). Evidence: Gates 3/6/7.
- Metric Verification: PASS (carried forward — no metric/evaluator change; scenario evaluator checks present per dry-run record). Evidence: no metric files modified; `git diff --stat` for the closure covers only the files in section 4.

Remaining risk (if any): Pilot is a real model run on Kaggle; the dry-run proves the harness/planning contract, not model behavior. Pre-registered Pilot budget remains a PILOT-EXEC-01 responsibility.

## 9. Independent code audit

- Correctness: per-repo graph/editable-universe/descriptor wiring is exercised by 14 unit + 12 integration tests and 48/48 dry-run.
- Failure modes: mixed-repo input now fails closed (no silent reuse); empty directory expansion fails closed; path traversal/backslash/duplicates rejected.
- Edge-case coverage: unit contract covers mixed repos, per-repo keys, expansion guards, catalog normalization, descriptor granularity.
- Test realism: production-path integration test uses the real run loop with the pilot profile scenario set.
- Stage-transition coupling: editable paths and descriptors are keyed by `repository_id` exactly like `_dep_graphs`; no cross-key reuse.
- No Ground Truth leakage: `build_dependency_graph` docstring unchanged ("never creates nodes from scenario.expected_affected_artifacts"); Ground Truth stays evaluation-only.
- No cross-repository contamination: per-repo graphs/universes; repeated integration run shows no state leak.
- Model/config identity: pilot profile/config hash `7ef6ffc7a2c0d369`; frozen matrix unchanged; dry-run protocol 1.0.
- Backward compatibility with accepted Smoke: smoke strategy/scenario semantics untouched; only the stale `selective` prereq expectation corrected to `{"agent"}`.
- Over-engineering audit: no unplanned framework/refactor; changes are scoped to the pilot multi-repo input contract and its tests/docs.

## 10. Plan adherence

- Did we stay inside PILOT-READY-01? YES.
- Did we add any unplanned framework/refactor? NO.
- Did we modify prompts/metrics/scientific thresholds? NO.
- Did we touch accepted Smoke evidence/history? NO.
- Did we start Pilot? NO.
- Did we satisfy every frozen closure gate? YES (Gates 1–7 all PASS).

## 11. Technical debt

NOW:
- None. No item blocks PILOT-READY-01; all frozen closure gates pass.

NEXT:
- 5 pre-existing mypy findings (`seven_arm_benchmark.py` lines 521, 627 no-untyped-def; 1360 backend arg-type; 2581 record_store.append; 2842 no-untyped-def) and 3 pre-existing ruff findings (`ARG001 profile`, `ARG001 strategy_name`, `SIM113 run_count` in `seven_arm_benchmark.py`). Impact: static noise, not behavior. Disposition: address before the main benchmark if those files are exercised. Reason not to fix now: pre-existing, untouched lines; out of feature scope and would risk churn during Pilot readiness.
- Pre-registered Pilot execution budget (token/GPU) for PILOT-EXEC-01. Impact: cost control on Kaggle. Disposition: part of PILOT-EXEC-01. Reason not to fix now: budget freeze is a PILOT-EXEC-01 decision per DA-09.

LATER:
- OpenRouter backend is provider-integration only (no retries/streaming/fallback routing). Impact: external API robustness only. Disposition: unrelated cleanup.
- Real repository dependency inference remains deferred (profiles carry the ground-truth-free graph data). Impact: none for Pilot. Disposition: future research.

## 12. Documentation updated

- `README.md` — new Current Status blockquote "PILOT-READY-01 = CLOSED (2026-08-10)"; "Current validated state" 1,958 → 2,026; roadmap PILOT-READY-01 → `[x] CLOSED`, PILOT-EXEC-01 next.
- `SYSTEM_STATE.md` — Current Truth rewritten (branch/HEAD, PILOT-READY-01 CLOSED, 2,026/33/0, Pilot NOT STARTED, next PILOT-EXEC-01, frozen matrix, tag); Current Phase prepended PILOT-READY-01 closure paragraph (root causes A–D + all gates); Current Task/Previous Task restructured; line ~226 and Exact Next Task sections updated.
- `TODO.md` — Current = PILOT-EXEC-01 PENDING (matrix + budget pre-registration); Previous = PILOT-READY-01 CLOSED with full gate detail.
- `docs/START_HERE.md` — CURRENT STATE line (2026-08-10, 2,026, PILOT-READY-01 CLOSED, next PILOT-EXEC-01, tag); Next Task CURRENT paragraph rewritten; line ~59 pointer updated.
- `docs/PROJECT_HANDOFF.md` — new top Handoff type "PILOT-READY-01 CLOSED (2026-08-10)"; CURRENT PROJECT STATE updated; EXACT NEXT TASK changed to PILOT-EXEC-01; recovery command 1,958 → 2,026; PILOT-READY-01 BLOCKERS updated; historical pointer ~line 732 updated.
- `docs/MASTER_IMPLEMENTATION_PLAN.md` — line 8 execution-track blockquote appended PILOT-READY-01 CLOSED closure; line 25 next-task pointer; line 40 authorize-Pilot marker; line ~97 Pilot entry; line ~105 boundary entry.
- `reports/latest_phase_report.md` — CURRENT TRUTH line rewritten; new "Latest closure — PILOT-READY-01" section; previous MAIN-GREEN-01 section demoted.
- `reports/PROJECT_HEALTH_REPORT.md` — Report Date 2026-08-10; Branch CURRENT line rewritten; far-goal step list + Next action updated to PILOT-EXEC-01.
- `DECISION_LOG.md` — new `Decision D024 — PILOT-READY-01 Closure` (format matched D001–D023).
- `docs/RESEARCHER_DECISIONS_DA_AC.md` — DA-07 Amendment 001 already recorded (2026-08-09) before any Pilot result; no new amendment needed.
- `selective_updates/CHANGE_INDEX.md` — new newest-first row `PILOT-READY-01-PILOT-READINESS-CLOSURE` (2026-08-10) linking to this report + the Django CMS/Saleor validation records.
- `reports/PILOT_READY_01_FINAL_REPORT.md` — this document (new).

Consistency contract satisfied: all state docs agree on PILOT-READY-01 CLOSED, Pilot NOT STARTED, next PILOT-EXEC-01, frozen matrix (Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2 strategies / 2 repetitions = 48 cells; Todo / django CMS / Saleor), full suite 2,026/33/0, tag `v0.9.0-pilot-ready`.

## 13. GitHub durability

- code commit SHA: `34ecf786901aec29659ea039a8f1fdf00039b5f2` (`fix(pilot): close multi-repo selective input contracts`)
- docs commit SHA: `0f3b7fa2c366e72685212d8c63ae81c655bc09bb` (`docs(pilot): close PILOT-READY-01 readiness evidence`)
- feature remote SHA: `0f3b7fa` == local feature HEAD (asserted after push)
- merge commit SHA: `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (`merge(pilot): close PILOT-READY-01`)
- origin/main SHA: `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` after the non-ff merge (was `592fc508ba1df596f685d80f2e0a35a4317d0299` before closure)
- tag name: `v0.9.0-pilot-ready` (annotated; tag object `d26aaba9612d84de055d0560aa57e02a29489699`)
- tag dereferenced commit: `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` == final main merge commit (verified with `git rev-parse 'v0.9.0-pilot-ready^{commit}'` and `git ls-remote --tags origin`)
- local == remote assertions: feature branch local == remote after push; main local `90a4282` == `origin/main` `90a4282` after push; tag pushed and dereferences to the final main merge commit

## 14. Final milestone result

`PILOT-READY-01 CLOSED`

- Remaining blockers: none
- Pilot started: NO
- Next task: `PILOT-EXEC-01` (Pilot execution with the frozen matrix; pre-register the execution budget)
- Near-term goal: stable tag `v0.9.0-pilot-ready` on main (this closure)
- Long-term goal: dependency-aware selective regeneration research experiment
