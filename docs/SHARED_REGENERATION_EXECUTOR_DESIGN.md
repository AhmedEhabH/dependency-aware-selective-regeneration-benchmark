# Shared Regeneration Executor Design

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** DESIGN — Not Implemented

---

## 1. Purpose

This document specifies the **shared regeneration executor** architecture required by RD-V2-04 (Measurement Boundary) and RD-V2-06 (Experiment Structure). The same executor must be used by all end-to-end conditions (Experiments B, C, D) to ensure fair comparison of token efficiency, correctness, and quality outcomes.

**Architecture Flow:**
```
RequirementDelta
→ ImpactStrategy (scope selection)
→ ImpactPrediction
→ RegenerationPlan
→ Shared LLM Executor
→ Patch Application
→ Functional Validation
→ Regression Validation
→ Architecture Validation
→ Bounded Repair Loop
→ Final RunRecord
```

---

## 2. Component Interfaces

### 2.1 RequirementDelta

```python
@dataclass(frozen=True)
class RequirementDelta:
    scenario_id: str
    requirement_before: str
    requirement_after: str
    acceptance_criteria: tuple[str, ...]
    repository: RepositorySnapshot
    artifact_universe: ArtifactUniverse
    # Ground truth (hidden from strategy, used only by executor for validation)
    expected_affected_artifacts: tuple[ExpectedArtifact, ...]
    hidden_tests: tuple[HiddenTest, ...]
```

### 2.2 ImpactStrategy (Protocol)

```python
@runtime_checkable
class ImpactStrategy(Protocol):
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction: ...
```

**Returns:** `ImpactPrediction` with `decisions: tuple[ImpactDecision, ...]`, `errors`, `token_usage`

### 2.3 ImpactPrediction → RegenerationPlan

```python
@dataclass(frozen=True)
class RegenerationPlan:
    plan_id: str
    scenario_id: str
    strategy_name: str
    # From ImpactPrediction.decisions
    artifacts_to_regenerate: tuple[ArtifactRef, ...]  # action=regenerate
    artifacts_to_preserve: tuple[ArtifactRef, ...]    # action=preserve
    artifacts_for_review: tuple[ArtifactRef, ...]     # action=human_review
    # Metadata
    impact_prediction: ImpactPrediction
    created_at: datetime
```

**Transformation Rules:**
- `ImpactDecision.action == ActionKind.regenerate` → `artifacts_to_regenerate`
- `ImpactDecision.action == ActionKind.preserve` → `artifacts_to_preserve`
- `ImpactDecision.action == ActionKind.human_review` → `artifacts_for_review`
- If `ImpactPrediction.errors`: plan is invalid → immediate failure record

### 2.4 Shared LLM Executor

```python
class SharedLLMExecutor:
    def __init__(
        self,
        backend: LLMBackend,
        prompt_builder: PromptBuilder,
        context_limiter: ContextLimiter,
        patch_parser: PatchParser,
    ) -> None:
        ...

    def execute_regeneration(
        self,
        plan: RegenerationPlan,
        isolation: IsolationContext,
        budget: BudgetManager,
    ) -> RegenerationResult:
        """Run regeneration for all artifacts in plan. Returns patches + token accounting."""
        ...
```

### 2.5 RegenerationResult

```python
@dataclass(frozen=True)
class RegenerationResult:
    patches: tuple[Patch, ...]           # One per regenerated artifact
    token_usage: TokenUsage              # Aggregated across all artifacts
    model_calls: int                     # Total LLM calls
    duration_seconds: float
    failures: tuple[RegenerationFailure, ...]  # Per-artifact failures
```

### 2.6 Patch Application

```python
class PatchApplicator:
    def apply(
        self,
        patches: tuple[Patch, ...],
        workspace: WorkspacePath,
        isolation: IsolationContext,
    ) -> PatchApplicationResult:
        """Atomically apply all patches or rollback on any failure."""
        ...

@dataclass(frozen=True)
class PatchApplicationResult:
    applied: tuple[Patch, ...]
    failed: tuple[FailedPatch, ...]      # patch, error
    workspace_snapshot: str              # Commit SHA or snapshot ID
```

### 2.7 Validation Pipeline

```python
class ValidationPipeline:
    def __init__(
        self,
        functional_validator: FunctionalValidator,
        regression_validator: RegressionValidator,
        architecture_validator: ArchitectureValidator,
    ) -> None:
        ...

    def validate(
        self,
        workspace: WorkspacePath,
        scenario: Scenario,
        plan: RegenerationPlan,
    ) -> ValidationResult:
        """Run all validations in sequence. Stop on first failure if configured."""
        ...
```

#### Validation Stages (Ordered)

| Stage | Validator | Input | Output | Failure Effect |
|-------|-----------|-------|--------|----------------|
| 1 | Functional | Workspace + acceptance criteria | Pass/Fail + details | → Repair loop |
| 2 | Regression | Workspace + hidden tests | Pass/Fail + details | → Repair loop |
| 3 | Architecture | Workspace + rules | Pass/Fail + violations | → Repair loop (or fail fast) |

### 2.8 Bounded Repair Loop

```python
class BoundedRepairLoop:
    def __init__(
        self,
        executor: SharedLLMExecutor,
        applicator: PatchApplicator,
        validator: ValidationPipeline,
        budget: BudgetManager,
        max_repair_attempts: int = 2,  # Protocol: 1 initial + 2 repairs
    ) -> None:
        ...

    def execute(
        self,
        initial_plan: RegenerationPlan,
        isolation: IsolationContext,
    ) -> RepairOutcome:
        """Run validation → repair → re-validate until success or budget exhausted."""
        ...
```

**Repair Policy (per protocol):**
- Maximum 2 repair attempts (3 total attempts including initial)
- Each repair: re-run executor on failed artifacts with error context
- Repair prompt includes: previous patch, validation failure details, file context
- If all attempts exhausted → final failure record

### 2.9 Final RunRecord

```python
@dataclass(frozen=True)
class RunRecord:
    identity: RunIdentity
    status: RunStatus
    prediction: ImpactPrediction | None
    regeneration: RegenerationResult | None
    validation: ValidationResult | None
    repair: RepairOutcome | None
    token_usage: TokenUsage          # AGGREGATED: selection + regeneration + repair
    duration_seconds: float
    failures: tuple[FailureRecord, ...]
    schema_version: str = "1.0"
```

---

## 3. Artifact Eligibility Rules

| Artifact Property | Eligible for Regeneration? |
|-------------------|---------------------------|
| In `artifact_universe` | Yes |
| `action == regenerate` in plan | Yes |
| `action == preserve` | No (must remain unchanged) |
| `action == human_review` | No (excluded from auto-regeneration) |
| Binary/non-text | No (excluded; marked as preserve) |
| Outside repository root | No (isolation violation) |
| > MAX_FILE_SIZE (100KB) | No (truncated context only) |

---

## 4. Prompt Construction

### 4.1 Regeneration Prompt Template

```
Repository: {repo_name} @ {commit_sha}
File: {artifact_path}
Change Required: {requirement_before} -> {requirement_after}
Acceptance Criteria:
{criteria_list}

Current File Content:
```{language}
{file_content}
```

Generate the complete updated file content that satisfies the requirement change.
Output ONLY the file content, no explanations, no markdown fences.
```

### 4.2 Repair Prompt Template (Attempt N)

```
Previous attempt failed validation.

File: {artifact_path}
Requirement Change: {requirement_before} -> {requirement_after}
Acceptance Criteria:
{criteria_list}

Previous Patch:
```diff
{previous_patch}
```

Validation Failure:
{validation_error_details}

Current File Content (after failed patch):
```{language}
{current_file_content}
```

Generate a corrected complete file content that addresses the validation failure.
Output ONLY the file content.
```

### 4.3 Context Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Max file content per call | 50,000 chars | Truncate with notice |
| Max prompt tokens | 32,000 | ContextLimiter rejects oversized |
| Max completion tokens | 8,192 | Backend parameter |
| Language detection | From file extension | For syntax highlighting |

---

## 5. Patch Format

### 5.1 Patch Dataclass

```python
@dataclass(frozen=True)
class Patch:
    artifact_path: str
    original_content: str
    new_content: str
    language: str
    # Unified diff (for logging/debugging)
    unified_diff: str
```

### 5.2 Patch Parser

- **Input:** LLM completion (raw text)
- **Output:** `Patch` or `ParseFailure`
- **Strategy:** Treat completion as full file replacement (simpler, more reliable than diff)
- **Validation:** New content must be syntactically valid for language (ast.parse for Python)

---

## 6. Workspace Isolation

| Property | Specification |
|----------|---------------|
| **Isolation root** | Per-run temporary directory |
| **Snapshot** | Git commit before regeneration |
| **Rollback** | `git checkout` to snapshot on any failure |
| **Concurrency** | One run per workspace (no sharing) |
| **Cleanup** | Automatic on completion (configurable retention) |

### 6.1 Patch Application Policy

1. **Atomic batch:** All patches applied in single transaction
2. **Order independence:** Patches target disjoint files
3. **Conflict detection:** If two patches target same file → failure
4. **Binary safety:** Only text files patched; binaries preserved
5. **Verification:** Post-apply, verify file contents match `new_content`

---

## 7. Validation Sequence

```python
def validate(workspace, scenario, plan):
    # Stage 1: Functional (acceptance criteria)
    functional_result = functional_validator.validate(workspace, scenario.acceptance_criteria)
    if not functional_result.passed:
        return ValidationResult(stage="functional", passed=False, details=functional_result)

    # Stage 2: Regression (hidden tests)
    regression_result = regression_validator.validate(workspace, scenario.hidden_tests)
    if not regression_result.passed:
        return ValidationResult(stage="regression", passed=False, details=regression_result)

    # Stage 3: Architecture (rules)
    arch_result = architecture_validator.validate(workspace, scenario.repository)
    if not arch_result.passed:
        return ValidationResult(stage="architecture", passed=False, details=arch_result)

    return ValidationResult(stage="complete", passed=True)
```

### 7.1 Validators

| Validator | Implementation | Protocol Reference |
|-----------|---------------|-------------------|
| **Functional** | Run scenario-specific test commands; check exit codes, output | `EXECUTION_AND_FAILURE_POLICY.md` |
| **Regression** | Run hidden test suite (ground truth); compare pass/fail | `GROUND_TRUTH_PROTOCOL.md` |
| **Architecture** | Static analysis: import cycles, layer violations, forbidden patterns | `ARCHITECTURE_VALIDATION_PLAN.md` |

---

## 8. Token and Timing Attribution

**All measurements must attribute to correct stage:**

```python
@dataclass(frozen=True)
class TokenUsage:
    # Selection stage (ImpactStrategy.analyze_impact)
    selection_prompt_tokens: int = 0
    selection_completion_tokens: int = 0
    selection_total_tokens: int = 0
    selection_model_calls: int = 0
    selection_duration_seconds: float = 0.0

    # Regeneration stage (SharedLLMExecutor.execute_regeneration)
    regeneration_prompt_tokens: int = 0
    regeneration_completion_tokens: int = 0
    regeneration_total_tokens: int = 0
    regeneration_model_calls: int = 0
    regeneration_duration_seconds: float = 0.0

    # Repair stage (BoundedRepairLoop)
    repair_prompt_tokens: int = 0
    repair_completion_tokens: int = 0
    repair_total_tokens: int = 0
    repair_model_calls: int = 0
    repair_duration_seconds: float = 0.0

    # Validation stage (no LLM calls)
    validation_duration_seconds: float = 0.0

    # Totals (computed)
    @property
    def total_workflow_tokens(self) -> int:
        return (self.selection_total_tokens +
                self.regeneration_total_tokens +
                self.repair_total_tokens)

    @property
    def total_workflow_model_calls(self) -> int:
        return (self.selection_model_calls +
                self.regeneration_model_calls +
                self.repair_model_calls)

    @property
    def total_workflow_duration_seconds(self) -> float:
        return (self.selection_duration_seconds +
                self.regeneration_duration_seconds +
                self.repair_duration_seconds +
                self.validation_duration_seconds)
```

**Attribution Rules:**
- `ImpactStrategy.analyze_impact()` → all tokens/calls/duration → `selection_*`
- `SharedLLMExecutor.execute_regeneration()` → `regeneration_*`
- `BoundedRepairLoop` internal LLM calls → `repair_*`
- `ValidationPipeline` → `validation_duration_seconds` only

---

## 9. Checkpoint Boundaries

| Checkpoint | State Saved | Resume Capability |
|------------|-------------|-------------------|
| **After scope selection** | `ImpactPrediction`, `RegenerationPlan` | Full resume from regeneration |
| **After regeneration** | `RegenerationResult`, applied patches | Resume from validation |
| **After validation** | `ValidationResult` | Resume from repair (if failed) |
| **After each repair attempt** | Updated patches, validation result | Resume next repair or finalize |

**Checkpoint Data Model:**
```python
@dataclass
class ExecutorCheckpoint:
    run_id: str
    stage: CheckpointStage  # SELECTION_DONE, REGENERATION_DONE, VALIDATION_DONE, REPAIR_ATTEMPT_N
    plan: RegenerationPlan
    regeneration_result: RegenerationResult | None
    validation_result: ValidationResult | None
    repair_attempt: int
    token_usage: TokenUsage
    workspace_snapshot: str
```

---

## 10. Reporting Impact

The executor produces data for:

| Report | Source |
|--------|--------|
| Token efficiency (H4) | `total_workflow_tokens`, `total_workflow_model_calls` |
| Latency (H4) | `total_workflow_duration_seconds` |
| Repair burden | `repair_model_calls`, `repair_duration_seconds`, `repair_outcome.total_attempts` |
| Correctness (H1-H3) | `ValidationResult` stages, `repair_outcome.success` |
| Scope quality | `ImpactPrediction` precision/recall (Experiment A) |
| Ablation contributions | Per-signal comparison via shared executor |

---

## 11. Integration Points

| Upstream | Interface | Downstream |
|----------|-----------|------------|
| `ImpactStrategy` | `analyze_impact()` → `ImpactPrediction` | `RegenerationPlanner` |
| `RegenerationPlanner` | `ImpactPrediction` → `RegenerationPlan` | `SharedLLMExecutor` |
| `LLMBackend` | `generate()` → `LLMResponse` | `SharedLLMExecutor` |
| `IsolationContext` | Workspace, snapshots | `PatchApplicator`, `ValidationPipeline` |
| `BudgetManager` | Token/attempt/timeout enforcement | All stages |
| `GroundTruthComparator` | `RunRecord` → metrics | Statistics/Reporting |

---

## 12. Implementation Dependencies (New/Modified)

| Module | Status | Description |
|--------|--------|-------------|
| `benchmark.execution.regeneration_executor` | **NEW** | `SharedLLMExecutor`, `PromptBuilder`, `ContextLimiter` |
| `benchmark.execution.patch` | **NEW** | `Patch`, `PatchParser`, `PatchApplicator` |
| `benchmark.execution.validation` | **NEW** | `ValidationPipeline`, validators |
| `benchmark.execution.repair` | **MODIFIED** | `BoundedRepairLoop` (extends existing `RepairLoop`) |
| `benchmark.execution.runner` | **MODIFIED** | `BenchmarkRunner` → integrates executor |
| `benchmark.core.models` | **MODIFIED** | Add `RegenerationPlan`, `RegenerationResult`, `Patch`, `TokenUsage` extensions |
| `benchmark.core.protocols` | **MODIFIED** | Add `RegenerationExecutor`, `PatchApplicator`, `Validator` protocols |

---

## 13. Acceptance Criteria

- [ ] Single executor class used by all end-to-end strategies
- [ ] Token attribution separated by stage (selection/regeneration/repair/validation)
- [ ] Patch application atomic with rollback
- [ ] Validation runs in fixed order: functional → regression → architecture
- [ ] Repair loop bounded (max 2 attempts) with error context injection
- [ ] Checkpointing at all 4 boundaries
- [ ] Resume from any checkpoint reproduces identical results
- [ ] All quality gates pass: ruff, mypy, pytest
- [ ] Dry-run executes without LLM calls

---

**Status:** DESIGN COMPLETE — Ready for implementation (SU-0010)
**Blockers:** None — design is self-contained
**Dependencies:** `REPOSITORY_AGENT_BASELINE_SPEC.md` (parallel)