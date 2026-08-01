# System State

## Current Phase
**R6 — ACCEPTED AND FROZEN — FREEZE AND MILESTONE-BRANCH PUBLICATION AUTHORIZED** (branch `experiment/three-arm-smoke-v2`)

The final independent re-audit (**GPT-5.6 Thinking**, 2026-08-01, audited HEAD `949e9c2`) **accepted R6** and authorized freeze and milestone-branch publication (recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). The bounded correction (one deployed-entrypoint regression test `40c7a47` plus documentation-truth cleanup at `949e9c2`) closed TD-R6-ENTRYPOINT-001 and defects D1–D6. R4 remains accepted and frozen at `f5ae826`; R5 remains accepted and frozen at `7761c48`. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; Kaggle not launched; push authorized and pending at this commit; tag not created; Pilot not authorized. Next: record the freeze, publish the branch, verify local/remote equality, then Kaggle environment preflight. Do not tag, merge, or launch Kaggle now.

## Phase State
```text
R4 = accepted and frozen (explicit freeze commit f5ae826)
R5 = accepted and frozen (independent re-audit 2026-08-01, recorded at 7761c48)
R6 = ACCEPTED AND FROZEN (independent re-audit 2026-08-01, recorded at 949e9c2)
Kaggle = not launched
Pilot = not authorized
README = updated in R6
push = authorized and pending at this commit
stable tag = blocked
```

## Previous Phase
**R5 — Nine Non-Dry Scripted Production Records — ACCEPTED AND FROZEN**

R5 proved exactly nine non-dry scripted production records (3 frozen scenarios × 3 arms × 1 repetition) through the real production orchestration path. R5 was accepted by the independent re-audit on 2026-08-01 at `7761c48`. The cleaned R5 tail is `8fafb50`, `a24a9cd`, `875e4d1`, `ee148fa`, `7761c48`. The old contaminated tail is preserved on `backup/r5-pre-audit-c3ecad2`.

## Current Task
R6 is **ACCEPTED AND FROZEN** and the milestone branch is authorized for publication. The test commit `40c7a47` proves the generated CLI entrypoint executes the exact 9-cell dry-run plan against the bundled data. Documentation truth defects D1–D6 (README badge/roadmap, SYSTEM_STATE identity, latest_phase_report, START_HERE, MASTER_IMPLEMENTATION_PLAN, PROJECT_HANDOFF) are closed at `949e9c2`. Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`; manifest committed-tree counts 0/0/0; Todo baseline tests deployed = 47; evaluator assets deployed = 3 + 3 fingerprints. Final accepted full suite = 1,648 passed / 32 skipped / 0 failed. Current task: record the R6 freeze, publish the branch with upstream, verify local/remote equality, then Kaggle preflight and nine real Qwen records.

## Recent Non-Phase Additions
- Added `README.md` (project overview, architecture, usage, license)
- Added `LICENSE` (MIT, copyright Ahmed Ehab H.)
- Added `reports/PROJECT_HEALTH_REPORT.md` (engineering dashboard)
- Legacy Seven-Arm Kaggle orchestration smoke passed (tag `v0.7.0-smoke-passed`): 7/7 arms, Qwen inference, non-publication — **historical orchestration evidence only, not V2 evidence**
- Audit merge commit `3a16596` on `main` adds `ARM_TO_PROTOCOL_EXECUTION_AUDIT.md`, `ARM_AUDIT_DECISION_REQUIRED.md`, `EXISTING_TAGS_AUDIT.md`

## Completed Work
- [x] Phase 0 — Bootstrap and Environment (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 1 — Input Audit (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 2A — Research Protocol Draft (DRAFT — superseded by v1.0)
- [x] Phase 2B — Protocol Freeze (FROZEN)
- [x] Phase 3 — Repository and Scenario Preparation (COMPLETE)
- [x] Phase 3.5 — Static Architecture Audit and Project Map (COMPLETE)
- [x] Phase 3.6 — Structure Remediation and Baseline Commit (COMPLETE)
- [x] **Phase 4A — Domain Models and Contracts** (COMPLETE)
- [x] **Phase 4B — Loaders and Validation** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement 6 StrEnum classes (ActionKind, ArtifactType, BlastRadius, RunStatus, FailureKind, EvidenceTier)
- [x] Implement 12 typed exception classes with context dict
- [x] Implement 24 frozen dataclass domain models with post-init validation
- [x] Implement 11 runtime-checkable protocol interfaces
- [x] Implement generic Registry[T] with freeze/lookup/list support
- [x] Implement ExecutionContext (controlled-immutable)
- [x] Implement 7 Pydantic v2 config models with cross-field validation
- [x] Implement YAML config loader and structural validation
- [x] Create package setup (pyproject.toml) with ruff/mypy/pytest config
- [x] Write 111 Phase 4A unit/contract/isolation tests (all passing)
- [x] Install package in editable mode for import resolution
- [x] Verify Phase 4A quality gates: ruff (pass), mypy (pass), pytest (111/111 pass), pip check (pass)
- [x] Create docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md
- [x] Create reports/PHASE4A_DOMAIN_MODELS_REPORT.md
- [x] **Phase 4B — Loaders and Validation** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement RepositoryLoaderBase with resolve_identity/resolve_snapshot
- [x] Implement RepositoryManifest, RepositoryVersionEntry, RepositoryProfile, ManifestCollection (frozen dataclasses)
- [x] Implement RepositoryLoader (YAML loading from manifests/ and repository_profiles/)
- [x] Implement SnapshotMetadata, create_snapshot_metadata, validate_snapshot
- [x] Implement WorkspacePath, validate_workspace_path, check_isolation
- [x] Implement ScenarioModel with to_core_scenario() and dual-format expected_actions parsing
- [x] Implement ScenarioLoader (load_all, load_by_repository)
- [x] Implement ScenarioValidator (required fields, duplicate actions)
- [x] Implement ScenarioSequencer (order by blast_radius)
- [x] Write 95 new Phase 4B tests (84 unit/contract + 11 integration)
- [x] Verify Phase 4B quality gates: 206/206 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md
- [x] Create reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md
- [x] Merge Phase 4B into main (commit `2fdc3c4`)
- [x] Reconcile SYSTEM_STATE.md for Phase 4B completion (this update)
- [x] Batch update all state files for Phase 4B → 4C transition
- [x] **Phase 4C — Model Backends** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement MockLLMBackend (deterministic, configurable response text)
- [x] Implement DryRunLLMBackend (fixture JSON loading with fallback)
- [x] Implement KaggleQwenBackend skeleton (lazy torch/transformers imports, safe locally)
- [x] Implement BackendFactory wrapping Registry[LLMBackend] with register/create/freeze
- [x] Write 23 new Phase 4C tests (22 unit + 1 isolation)
- [x] Verify Phase 4C quality gates: 229/229 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md
- [x] Create reports/PHASE4C_MODEL_BACKENDS_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4C completion (this update)
- [x] Batch update all state files for Phase 4C → 4D transition
- [x] **Phase 4D — Execution Core** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement BudgetManager with injectable Clock, multi-axis budget enforcement
- [x] Implement RunStateMachine with 6-state typed transitions and terminal-state protection
- [x] Implement RepairLoop with 1+2 attempt lifecycle and configurable FailureClassifier
- [x] Implement IsolationContext wrapping Phase 4B workspace utilities
- [x] Implement BenchmarkRunner coordinating strategy+backend+isolation into RunRecord
- [x] Implement BenchmarkPipeline with single/batch/dry-run modes
- [x] Write 59 new Phase 4D tests (all passing)
- [x] Verify Phase 4D quality gates: 288/288 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4D_EXECUTION_CORE_REFERENCE.md
- [x] Create reports/PHASE4D_EXECUTION_CORE_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4D completion (this update)
- [x] Batch update all state files for Phase 4D → 4E transition
- [x] **Phase 4E — Impact Strategies** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement 7 strategy patterns: monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan
- [x] Implement StrategyRegistry with register/create/freeze/lookup
- [x] Implement graph package: DependencyNode, DependencyEdge, DependencyGraphModel, PythonImportExtractor, ImpactPropagator, ScopeReducer
- [x] Implement selection package: ArtifactSelector, RegenerationPlanner
- [x] Write 43 new Phase 4E tests (all passing)
- [x] Verify Phase 4E quality gates: 332/332 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create reports/PHASE4E_IMPACT_STRATEGIES_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4E completion
- [x] Batch update all state files for Phase 4E → 4F transition
- [x] **Phase 4F — Evaluation Engine** (COMPLETE)
- [x] Create `src/benchmark/evaluation/` package with EvaluationEngine, MetricComputer
- [x] Create `src/benchmark/comparison/` package with GroundTruthComparator, ResultAggregator
- [x] Create `src/benchmark/statistics/` package with StatisticalAnalyzer, ConfidenceIntervalCalculator, EffectSizeComputer, NotebookExporter, PublicationTableBuilder
- [x] Implement primary metrics: recall, precision, F1, specificity, FPR, FNR
- [x] Implement secondary metrics: accuracy, action_accuracy
- [x] Implement confidence intervals: bootstrap, normal, Wilson, Agresti-Coull
- [x] Implement effect sizes: Cohen's d, Cliff's delta
- [x] Implement statistical analysis: Mann-Whitney U, non-inferiority tests
- [x] Implement notebook export: JSON, DataFrame
- [x] Implement publication tables: CSV, Markdown, LaTeX
- [x] Write 73 new Phase 4F tests (all passing)
- [x] Verify Phase 4F quality gates: 405/405 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Independent scientific audit: 2 defects found/fixed, 5 regression tests added (410 total)
- [x] Create docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md
- [x] Create reports/PHASE4F_EVALUATION_ENGINE_REPORT.md
- [x] Create reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4F completion and audit
- [x] **Phase 4F.1 — Scientific Evaluation Remediation** (COMPLETE)
- [x] Full `aggregate_run_records` implementation (micro + macro equal-weight)
- [x] `paired_bootstrap_ci()` for H1 (matched on repo-scenario-rep)
- [x] `benjamini_hochberg()` + `holm_correction()` for DA-14
- [x] NI sensitivity margins at 0.03 and 0.10 (DA-08)
- [x] Generalized binomial CI via `scipy.stats.norm.ppf`
- [x] Fixed BH implementation bug (descending sort → ascending + step-down)
- [x] 31 new tests (441 total); all quality gates pass
- [x] Create reports/PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md
- [x] **Kaggle Smoke Pass** (engineering validation complete)
- [x] Fix failure propagation: real Qwen errors, token_usage, smoke-stage tagging
- [x] Fix graph wiring: ProfileGraphBuilder, capabilities design, NullLLMBackend
- [x] 20 new regression tests (504 total + 1 skipped torch); all quality gates pass
- [x] Tag `v0.7.0-smoke-passed` at commit `0c58250` (main branch)

### Phase 4A/4B/4C Production — 22 files
6 under `src/benchmark/core/`: `__init__.py`, `context.py`, `enums.py`, `exceptions.py`, `models.py`, `protocols.py`, `registry.py`
7 under `src/benchmark/config/`: `__init__.py`, `models.py`, `loader.py`, `validation.py`
6 under `src/benchmark/repositories/`: `__init__.py`, `base.py`, `manifest.py`, `loader.py`, `snapshot.py`, `workspace.py`
5 under `src/benchmark/scenarios/`: `__init__.py`, `models.py`, `loader.py`, `validator.py`, `sequencing.py`
5 under `src/benchmark/llm/`: `__init__.py`, `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py`

### Phase 4D Production — 7 files
All under `src/benchmark/execution/`: `__init__.py`, `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`

### Phase 4F Production — 11 files
Evaluation package: `src/benchmark/evaluation/__init__.py`, `engine.py`, `metrics.py`
Comparison package: `src/benchmark/comparison/__init__.py`, `ground_truth.py`, `aggregator.py`
Statistics package: `src/benchmark/statistics/__init__.py`, `analysis.py`, `confidence_intervals.py`, `effect_sizes.py`, `reporting.py`

### Tests (Phase 4A–4F)
8 unit test files: `test_repositories_manifest.py` (15), `test_repositories_loader.py` (8), `test_repositories_snapshot.py` (12), `test_repositories_workspace.py` (9), `test_scenarios_models.py` (11), `test_scenarios_loader.py` (9), `test_scenarios_validator.py` (7), `test_scenarios_sequencing.py` (5)
2 integration test files: `test_repositories_integration.py` (6), `test_scenarios_integration.py` (5)
1 contract test file: `test_loaders_contract.py` (4)
3 test package init files

### Phase 4D Tests — 7 files
All under `tests/unit/execution/`: `__init__.py`, `test_budgets.py` (14), `test_state_machine.py` (13), `test_repair.py` (8), `test_isolation.py` (9), `test_runner.py` (7), `test_pipeline.py` (6)

### Phase 4E Tests — 3 files
All under `tests/unit/strategies/` and `tests/unit/graph/`, `tests/unit/selection/`: `__init__.py`, `test_strategies.py` (21), `test_graph.py` (16), `test_planner.py` (6)

### Phase 4F Tests — 8 files
All under `tests/unit/evaluation/`, `tests/unit/comparison/`, `tests/unit/statistics/`: `__init__.py` (×3), `test_engine.py` (7), `test_metrics.py` (13), `test_comparison.py` (14), `test_statistics.py` (24), `test_reporting.py` (15)

### Documentation (Phase 4A–4F)
`docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md`, `docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md`, `docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`, `docs/PHASE4D_EXECUTION_CORE_REFERENCE.md`, `docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md`
`reports/PHASE4A_DOMAIN_MODELS_REPORT.md`, `reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md`, `reports/PHASE4C_MODEL_BACKENDS_REPORT.md`, `reports/PHASE4D_EXECUTION_CORE_REPORT.md`, `reports/PHASE4F_EVALUATION_ENGINE_REPORT.md`, `reports/PROJECT_HEALTH_REPORT.md`

## Phase 4C — Files Created (5 production + 6 test + 2 doc = 13 new files, 1 modified)

### Production — 5 files
All under `src/benchmark/llm/`: `__init__.py`, `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py`

### Tests — 6 files
5 files under `tests/unit/llm/`: `__init__.py`, `test_llm_mock_backend.py` (6), `test_llm_dry_run_backend.py` (5), `test_llm_kaggle_qwen_backend.py` (3), `test_llm_factory.py` (8)
1 modified: `tests/test_import_isolation.py` (added LLM-specific import test)

### Documentation — 2 files
`docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`, `reports/PHASE4C_MODEL_BACKENDS_REPORT.md`

## Frozen Protocol Checksums (SHA-256)

| Document | Checksum |
|----------|----------|
| `docs/FINAL_RESEARCH_PROTOCOL.md` | `9D4A140C1CBA19C3076AF8C71AD859F243C31836FECD6026C2CD86CFC271B148` |
| `docs/GROUND_TRUTH_PROTOCOL.md` | `83F1ADB28CD99B6859BD7BE8189B22C2D272538CBB19B386D921F9DC728DD9E5` |
| `docs/SCENARIO_TAXONOMY.md` | `5FA4D7114E1993E2D8FB570EC9BAC4129F3956B09E7555C200C118E206D9BB62` |
| `docs/STATISTICAL_ANALYSIS_PLAN.md` | `FA8B76C41FF05462E80675B297917A904ECD4605CA5AD54C84740A38B6AB1D4C` |
| `docs/EXECUTION_AND_FAILURE_POLICY.md` | `FB3072880A6EBDD259707F9F64F50D56DF6DD4B04DBDE80E1E2867C80295F49E` |
| `docs/LEAKAGE_PREVENTION_PROTOCOL.md` | `F78AF1F57C8A59EA324E1996B4B172F7A02EF9D0D8EB66DD1D02F9EFD2B53910` |
| `docs/REPRODUCIBILITY_PROTOCOL.md` | `A59A666CC740BF2F9F9D9D193422892C1E064D99F6D264250C5625CFB35DB02E` |
| `docs/RESEARCHER_DECISIONS_DA_AC.md` | `1884352AF8813E794A25A1BAE947269BB343C788A22A933F59754B7DEE607BD3` |

## Environment Status
- **Platform:** Windows (win32)
- **Python (project env):** 3.11.5
- **Conda:** Anaconda (at C:\Users\Ahmed\AppData\Local\anaconda3)
- **Git:** 2.49.0
- **Project env:** `selective-regen-benchmark` — ACTIVATED AND VALIDATED
- **Package resolver:** conda (defaults channel) + pip
- **Dependency conflicts:** None

## Phase 4D — Files Created (7 production + 7 test + 2 doc = 16 new files)

### Production — 7 files
All under `src/benchmark/execution/`: `__init__.py`, `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`

### Tests — 7 files
All under `tests/unit/execution/`: `__init__.py`, `test_budgets.py` (14), `test_state_machine.py` (13), `test_repair.py` (8), `test_isolation.py` (9), `test_runner.py` (7), `test_pipeline.py` (6)

### Documentation — 2 files
`docs/PHASE4D_EXECUTION_CORE_REFERENCE.md`, `reports/PHASE4D_EXECUTION_CORE_REPORT.md`

## Local Checks Passed (Phase 4A + 4B + 4C + 4D + 4E)
- 6 StrEnum classes with stable string values: ✅
- 12 exception classes in typed hierarchy: ✅
- 24 frozen dataclass domain models with post-init validation: ✅
- 11 runtime-checkable protocol interfaces: ✅
- Generic Registry[T] with freeze/lookup/list: ✅
- ExecutionContext with controlled immutability: ✅
- 7 Pydantic v2 config models with cross-field validation: ✅
- YAML config loader and structural validation: ✅
- Package installable in editable mode: ✅
- Ruff lint+format: 0 violations (all source and test files): ✅
- Mypy strict: 0 errors (93 files): ✅
- Pytest: 441/441 passed: ✅
- pip check: no broken requirements: ✅
- Import isolation: torch/transformers not imported by benchmark.llm: ✅
- MockLLMBackend: deterministic output, protocol conformance: ✅
- DryRunLLMBackend: fixture loading with fallback: ✅
- KaggleQwenBackend: local execution raises ModelBackendError, lazy imports safe: ✅
- BackendFactory: register/create/freeze/contains/len with Registry: ✅
- Repository loader: loads real manifests and profiles: ✅
- Scenario loader: loads all 24 real scenario YAMLs: ✅
- Scenario validation: all scenarios pass structural validation: ✅
- Snapshot metadata: creation and validation: ✅
- Workspace isolation: prevents cross-run contamination: ✅
- All prior Phase 3/3.5/3.6 checks: ✅
- BudgetManager: injectable clock, multi-axis enforcement, reset: ✅
- RunStateMachine: 6-state lifecycle, typed transitions, terminal-state protection: ✅
- RepairLoop: 1+2 attempt lifecycle, error/benchmark handling, custom classifier: ✅
- IsolationContext: workspace verification, private data detection, directory creation: ✅
- BenchmarkRunner: full run lifecycle, dry_run, isolation failure, budget config: ✅
- BenchmarkPipeline: single/batch/dry-run modes, failure tracking: ✅
- Import isolation: benchmark.execution does not import torch/transformers: ✅
- 7 strategy implementations with ImpactStrategy protocol conformance: ✅
- StrategyRegistry with register/create/freeze/lookup: ✅
- Graph package: DependencyGraphModel, PythonImportExtractor, ImpactPropagator, ScopeReducer: ✅
- Selection package: ArtifactSelector, RegenerationPlanner: ✅
- Import isolation: benchmark.strategies, benchmark.graph, benchmark.selection do not import torch/transformers: ✅

## Kaggle Checks Pending
- Real model loading or inference
- Qwen model discovery
- GPU/torch availability
- Real benchmark runs
- Runtime metrics

## Current Branch
`experiment/three-arm-smoke-v2` (R4 frozen; R5 frozen; R6 ACCEPTED AND FROZEN at `949e9c2`; publication authorized and pending)

## Latest Commit
`docs(audit): close R6 handoff truth gaps` (949e9c2) — audited and accepted R6 HEAD; R6 freeze record pending at this commit

## Known Risks
1. **LR-3 — No test data boundary:** Test fixtures need a defined home outside `inputs/` and `src/`.
2. **LR-5 — Paper vs. implementation drift:** Must document any conflict rather than silently resolving.
3. **LR-7 — django CMS and Saleor not yet cloned locally:** Test suite runnability not verified locally beyond manifest documentation.
4. **LR-8 — Scenario content quality:** YAML files generated by automated agents; manual review recommended before Phase 4.

## Exact Next Task
1. Record the final R6 acceptance/freeze in the repository (this freeze pass)
2. Publish `experiment/three-arm-smoke-v2` to origin with upstream, verify local/remote equality
3. Record publication status, push again, verify final equality
4. Kaggle environment preflight and nine real Qwen Smoke records
5. Independent result audit, then `v2.0.0-scientific-smoke` tag
6. Pilot freeze and execution
7. Do not tag, merge, force-push, or launch Kaggle now

## Handoff Notes
Phase 4A–4F complete, Phase 4F.1 complete, R3B/R3C/R3D closures complete, R4 token/metric contract ACCEPTED AND FROZEN at `f5ae826`, R5 nine-scripted-records ACCEPTED AND FROZEN by the independent re-audit at `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 deployment closure is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The bounded final correction (test commit `40c7a47` proving the bundled CLI dry-run 9/9, plus documentation-truth cleanup D1–D6 at `949e9c2`) closed TD-R6-ENTRYPOINT-001. `.gitattributes` manifest-LF rule = audit-approved scope extension. No production, builder, bundle, notebook, or config changes were made in the correction pass. Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`; Todo baseline tests deployed = 47; evaluator assets deployed = 3 + 3 fingerprints. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; Kaggle not launched; branch publication authorized and pending at this commit; Pilot not authorized. Final accepted full suite at R6 closure: 1,648 passed, 32 skipped, 0 failed. Smoke evidence is non-publication. Do not claim publication results without research-profile runs under the frozen protocol. Pilot wording: exact final run denominator not frozen; minimum 7–12 changes across at least 3 real repositories; current descriptive 48-run config is not authorization. Do not download or run LLM locally. Do not modify frozen protocol documents. Do not modify anything under `inputs/`. Canonical project root is `project/` (where `.git` lives).

Environment activation:
```bash
conda activate selective-regen-benchmark
```

Run tests:
```bash
python -m pytest -q
```

R6_ACCEPTED_FREEZE_AND_PUBLISH_AUTHORIZED