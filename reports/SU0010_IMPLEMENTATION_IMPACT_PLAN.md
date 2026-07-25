# SU-0010 Implementation Impact Plan

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** DESIGN — Implementation Dependency Graph

---

## 1. Overview

This document traces the implementation dependency graph for Research Design V2, from `ImpactPrediction` through `Kaggle Bundle`. Each node identifies current ownership, required interface changes, dependencies, test targets, and explicitly unaffected areas.

**Scope:** Changes to implement RD-V2 experimental design (Experiments A–D, shared executor, baseline spec, naming policy).
**Excludes:** SU-0011 (Repository Agent iterative implementation) — separate decision.

---

## 2. Dependency Graph

```text
ImpactPrediction
       │
       ▼
RegenerationPlan
       │
       ▼
Shared LLM Executor ◄── LLMBackend
       │
       ▼
Patch Application
       │
       ▼
Validation Pipeline
   ┌───┼───┐
   ▼   ▼   ▼
Func  Regr  Arch
Validation Validation Validation
   └───┼───┘
       ▼
Bounded Repair Loop
       │
       ▼
RunRecord
       │
       ▼
Checkpoint / HF Sync
       │
       ▼
Reports / Statistics
       │
       ▼
Kaggle Bundle
```

---

## 3. Node Specifications

### 3.1 ImpactPrediction → RegenerationPlan

| Aspect | Detail |
|--------|--------|
| **Current owning module** | `src/benchmark/selection/planner.py` — `RegenerationPlanner` |
| **New/modified interface** | `plan(prediction: ImpactPrediction, universe: ArtifactUniverse) → RegenerationPlan` |
| **Upstream dependencies** | `ImpactPrediction` (from strategy), `ArtifactUniverse` (from scenario) |
| **Downstream artifacts** | `RegenerationPlan` (ordered `RegenerationTask` with artifact, action, context) |
| **Targeted tests** | `tests/unit/selection/test_planner.py` — add `test_plan_from_hybrid_selective`, `test_plan_preserves_preserve_order` |
| **Generated derivatives** | `RegenerationPlan` fed to Shared Executor |
| **Explicitly unaffected** | Strategy implementations (`analyze_impact` unchanged) |

### 3.2 RegenerationPlan → Shared LLM Executor

| Aspect | Detail |
|--------|--------|
| **Current owning module** | **NEW** — `src/benchmark/execution/regeneration_executor.py` |
| **New/modified interface** | `execute(plan: RegenerationPlan, isolation: IsolationContext, backend: LLMBackend) → ExecutionResult` |
| **Upstream dependencies** | `RegenerationPlan`, `IsolationContext`, `LLMBackend` |
| **Downstream artifacts** | `ExecutionResult` (patches, token usage, durations, per-task status) |
| **Targeted tests** | `tests/unit/execution/test_regeneration_executor.py` (NEW) — mock backend, patch format, token accounting |
| **Generated derivatives** | Applied patches in isolated workspace |
| **Explicitly unaffected** | `BenchmarkRunner`, `RepairLoop` (consume `ExecutionResult`) |

### 3.3 Shared LLM Executor → Patch Application

| Aspect | Detail |
|--------|--------|
| **Current owning module** | **NEW** — `src/benchmark/execution/patch_applier.py` |
| **New/modified interface** | `apply(patches: list[Patch], workspace: WorkspacePath) → PatchApplicationResult` |
| **Upstream dependencies** | `ExecutionResult.patches`, `IsolationContext.workspace` |
| **Downstream artifacts** | Modified files in workspace; `PatchApplicationResult` (success/fail per patch) |
| **Targeted tests** | `tests/unit/execution/test_patch_applier.py` (NEW) — unified diff, conflict detection, rollback |
| **Generated derivatives** | Modified workspace state |
| **Explicitly unaffected** | Strategy code, graph, selection |

### 3.4 Patch Application → Functional Validation

| Aspect | Detail |
|--------|--------|
| **Current owning module** | **NEW** — `src/benchmark/execution/functional_validator.py` |
| **New/modified interface** | `validate(workspace: WorkspacePath, scenario: Scenario) → ValidationResult` |
| **Upstream dependencies** | Modified workspace, `Scenario.acceptance_criteria`, `Scenario.hidden_tests` |
| **Downstream artifacts** | `ValidationResult` (pass/fail, test output, duration) |
| **Targeted tests** | `tests/unit/execution/test_functional_validator.py` (NEW) — test discovery, execution, timeout |
| **Generated derivatives** | Test execution logs |
| **Explicitly unaffected** | `RepairLoop` (consumes `ValidationResult`) |

### 3.5 Patch Application → Regression Validation

| Aspect | Detail |
|--------|--------|
| **Current owning module** | **NEW** — `src/benchmark/execution/regression_validator.py` |
| **New/modified interface** | `validate(workspace: WorkspacePath, scenario: Scenario) → ValidationResult` |
| **Upstream dependencies** | Modified workspace, `Scenario.hidden_tests` (full suite), baseline results |
| **Downstream artifacts** | `ValidationResult` (regression count, failed tests) |
| **Targeted tests** | `tests/unit/execution/test_regression_validator.py` (NEW) |
| **Generated derivatives** | Regression test logs |
| **Explicitly unaffected** | Functional validator (separate concern) |

### 3.6 Patch Application → Architecture Validation

| Aspect | Detail |
|--------|--------|
| **Current owning module** | **NEW** — `src/benchmark/execution/architecture_validator.py` |
| **New/modified interface** | `validate(workspace: WorkspacePath, profile: RepositoryProfile) → ValidationResult` |
| **Upstream dependencies** | Modified workspace, `RepositoryProfile.boundaries`, `RepositoryProfile.layer_rules` |
| **Downstream artifacts** | `ValidationResult` (violations: layer crossing, forbidden deps, cyclic deps) |
| **Targeted tests** | `tests/unit/execution/test_architecture_validator.py` (NEW) |
| **Generated derivatives** | Architecture violation reports |
| **Explicitly unaffected** | Other validators |

### 3.7 Bounded Repair Loop

| Aspect | Detail |
|--------|--------|
| **Current owning module** | `src/benchmark/execution/repair.py` — `RepairLoop` (EXTEND) |
| **New/modified interface** | `execute(attempt_fn: Callable, validation_pipeline: ValidationPipeline) → RepairOutcome` |
| **Upstream dependencies** | `ValidationPipeline` (functional → regression → architecture), `BudgetManager` |
| **Downstream artifacts** | Final `RunRecord` with aggregated repair attempts |
| **Targeted tests** | `tests/unit/execution/test_repair.py` — extend with multi-validator pipeline |
| **Generated derivatives** | Repair attempt records |
| **Explicitly unaffected** | `BudgetManager`, `RunStateMachine` |

### 3.8 RunRecord

| Aspect | Detail |
|--------|--------|
| **Current owning module** | `src/benchmark/core/models.py` — `RunRecord` (EXTEND) |
| **New/modified interface** | Add fields: `selection_tokens`, `regeneration_tokens`, `repair_tokens`, `validation_durations`, `patch_sizes`, `unintended_diffs` |
| **Upstream dependencies** | All execution stages |
| **Downstream artifacts** | Checkpoint persistence, reports, statistics |
| **Targeted tests** | `tests/unit/test_models.py` — serialization, field validation |
| **Generated derivatives** | `RunRecord` → `CheckpointData`, `BenchmarkSummary` |
| **Explicitly unaffected** | `RunIdentity`, `TokenUsage` (base) |

### 3.9 Checkpoint / HF Sync

| Aspect | Detail |
|--------|--------|
| **Current owning module** | `src/benchmark/checkpoint/checkpoint.py` — `CheckpointManager` (EXTEND) |
| **New/modified interface** | `CheckpointData` extended with per-stage token accounting |
| **Upstream dependencies** | `RunRecord` |
| **Downstream artifacts** | `checkpoint.json`, HF sync payload |
| **Targeted tests** | `tests/unit/checkpoint/test_checkpoint.py` — extended schema |
| **Generated derivatives** | Resumable state |
| **Explicitly unaffected** | `ResumeManager`, `ResultsPackager` (consume extended schema) |

### 3.10 Reports / Statistics

| Aspect | Detail |
|--------|--------|
| **Current owning modules** | `src/benchmark/statistics/` (reporting, analysis), `src/benchmark/comparison/` (aggregator) |
| **New/modified interface** | Consume extended `RunRecord` fields; compute per-stage token efficiency |
| **Upstream dependencies** | Extended `RunRecord`, `CheckpointData` |
| **Downstream artifacts** | Publication tables, notebook exports, statistical analysis |
| **Targeted tests** | `tests/unit/statistics/test_reporting.py`, `test_analysis.py` — per-stage metrics |
| **Generated derivatives** | CSV, Markdown, LaTeX, JSON exports |
| **Explicitly unaffected** | Core statistical methods (bootstrap, effect sizes) |

### 3.11 Kaggle Bundle

| Aspect | Detail |
|--------|--------|
| **Current owning module** | `scripts/build_upload_bundle.py` |
| **New/modified interface** | Include new execution modules in code bundle; validate extended schemas in data bundle |
| **Upstream dependencies** | All production code, benchmark data |
| **Downstream artifacts** | `kaggle_upload/code/`, `kaggle_upload/data/` |
| **Targeted tests** | Bundle verification script (self-contained) |
| **Generated derivatives** | Kaggle dataset upload |
| **Explicitly unaffected** | Bundle builder logic (already deterministic) |

---

## 4. New/Modified Modules Summary

| Module | Status | Description |
|--------|--------|-------------|
| `benchmark.execution.regeneration_executor` | **NEW** | `SharedLLMExecutor`, `PromptBuilder`, `ContextLimiter` |
| `benchmark.execution.patch_applier` | **NEW** | `Patch`, `PatchParser`, `PatchApplier` |
| `benchmark.execution.validation` | **NEW** | `ValidationPipeline`, `FunctionalValidator`, `RegressionValidator`, `ArchitectureValidator` |
| `benchmark.execution.repair` | **MODIFIED** | `BoundedRepairLoop` (extends `RepairLoop`) |
| `benchmark.core.models` | **MODIFIED** | Add `RegenerationPlan`, `ExecutionResult`, `Patch`, extended `TokenUsage`, `RunRecord` |
| `benchmark.core.protocols` | **MODIFIED** | Add `RegenerationExecutor`, `PatchApplier`, `Validator` protocols |
| `benchmark.selection.planner` | **MODIFIED** | `RegenerationPlanner.plan()` signature |

---

## 5. Test Coverage Requirements

| Test File | Target | New Tests |
|-----------|--------|-----------|
| `tests/unit/selection/test_planner.py` | `RegenerationPlanner` | 8 |
| `tests/unit/execution/test_regeneration_executor.py` | **NEW** | 12 |
| `tests/unit/execution/test_patch_applier.py` | **NEW** | 10 |
| `tests/unit/execution/test_functional_validator.py` | **NEW** | 8 |
| `tests/unit/execution/test_regression_validator.py` | **NEW** | 8 |
| `tests/unit/execution/test_architecture_validator.py` | **NEW** | 8 |
| `tests/unit/execution/test_repair.py` | `RepairLoop` | +6 (multi-validator) |
| `tests/unit/test_models.py` | Extended models | +6 |
| `tests/unit/checkpoint/test_checkpoint.py` | Extended checkpoint | +4 |
| `tests/unit/statistics/test_reporting.py` | Per-stage metrics | +8 |
| **Total new tests** | | **~88** |

**Implementation Estimates (per researcher review):**

| Estimate | Status |
|----------|--------|
| ~21 days | **NON-BINDING ENGINEERING ESTIMATES** |
| ~88 tests | **NON-BINDING ENGINEERING ESTIMATES** |
| 10 implementation phases | **NON-BINDING ENGINEERING ESTIMATES** |

**These are planning estimates only. They must not determine implementation scope. The implementation will follow dependency-scoped, evidence-driven selective updates.**

---

## 6. Quality Gates

All new/modified code must pass:

- [ ] `ruff` — 0 violations
- [ ] `mypy --strict` — 0 errors
- [ ] `pytest` — 100% pass (including new tests)
- [ ] `pip check` — no conflicts
- [ ] Import isolation — no `torch`/`transformers` at package load
- [ ] Bundle builder — verification passes

---

## 7. Approved Implementation Sequence (per RD-V2 researcher review)

**Production implementation is expected to proceed incrementally:**

### SU-0010A — Minimal Shared Regeneration Path

```
ImpactPrediction
→ RegenerationPlan
→ Shared LLM Executor
→ Patch Application
→ Functional Validation
→ RunRecord
```

**Initial supported conditions:**
- `full_scope_reference`
- `hybrid_selective`

**Purpose:**
- Prove real patch generation
- Prove scope-dependent regeneration
- Prove per-stage token accounting
- Prove functional correctness
- Avoid implementing the entire architecture as one big-bang change

### SU-0010B — Validation, Repair, and Persistence Integration

- Regression validation
- Architecture validation
- Bounded repair
- Rollback
- Checkpoint/resume integration
- Complete reporting

### SU-0011 — Iterative Repository-Agent Baseline

- Bounded repository search
- File inspection
- Context refinement
- Scope selection
- The same shared executor
- The same validation
- The same repair policy

**The shared executor must precede the iterative-agent implementation because both confirmatory conditions must use the same execution and validation path.**

---

## 7.1 Original Sequential Phase List (Retained for Reference)

1. **Core models/protocols** — `RegenerationPlan`, `Patch`, `ExecutionResult`, protocols
2. **RegenerationPlanner** — `plan()` implementation
3. **PatchApplier** — unified diff, atomic apply, rollback
4. **Validators** — functional, regression, architecture (independent)
5. **SharedLLMExecutor** — prompt building, context limiting, batch execution
6. **BoundedRepairLoop** — multi-validator pipeline
7. **BenchmarkRunner integration** — wire executor into run flow
8. **RunRecord/Checkpoint extension** — per-stage token accounting
9. **Statistics/Reporting** — per-stage metrics
10. **Bundle validation** — end-to-end

---

## 8. Explicitly Unaffected Areas

| Area | Reason |
|------|--------|
| Strategy implementations (`analyze_impact`) | RD-V2 does not change impact analysis algorithms |
| Graph package (`builder`, `propagator`) | Scope selection unchanged |
| LLM backends (`MockLLMBackend`, `KaggleQwenBackend`) | Interface stable |
| Scenario/Repository loaders | Input format unchanged |
| BudgetManager, RunStateMachine | Interfaces stable |
| HF sync, ResultsPackager | Consume extended schema |

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Patch application conflicts | Medium | High | Deterministic ordering; validation before apply; rollback tests |
| Token accounting drift | Low | Medium | Unit tests per stage; aggregate verification |
| Validator flakiness (external test deps) | Medium | Medium | Mockable test runners; timeouts; isolation |
| Checkpoint schema migration | Low | High | Backward-compatible fields; versioned schema |
| Bundle size increase | Low | Low | New modules small; verify bundle size |

---

**Status:** DESIGN COMPLETE — Ready for implementation authorization
**Next Step:** Researcher approval → SU-0010 implementation branch