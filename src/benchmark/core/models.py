from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, FailureKind, RunStatus


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Requirement and Artifact Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RequirementChange:
    before: str
    after: str
    acceptance_criteria: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.before:
            raise ValueError("RequirementChange.before must not be empty")
        if not self.after:
            raise ValueError("RequirementChange.after must not be empty")


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    artifact_type: ArtifactType

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("ArtifactRef.path must not be empty")


@dataclass(frozen=True)
class ArtifactUniverse:
    artifacts: tuple[ArtifactRef, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for ref in self.artifacts:
            if ref.path in seen:
                raise ValueError(f"Duplicate artifact path: {ref.path}")
            seen.add(ref.path)

    def contains(self, path: str) -> bool:
        return any(a.path == path for a in self.artifacts)


@dataclass(frozen=True)
class ArchitectureConstraint:
    description: str

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("ArchitectureConstraint.description must not be empty")


@dataclass(frozen=True)
class AcceptanceCriterion:
    description: str

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("AcceptanceCriterion.description must not be empty")


# ---------------------------------------------------------------------------
# Repository and Scenario Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RepositoryIdentity:
    name: str
    url: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("RepositoryIdentity.name must not be empty")
        if not self.url:
            raise ValueError("RepositoryIdentity.url must not be empty")


@dataclass(frozen=True)
class RepositorySnapshot:
    identity: RepositoryIdentity
    commit_sha: str
    path: str

    def __post_init__(self) -> None:
        if not self.commit_sha:
            raise ValueError("RepositorySnapshot.commit_sha must not be empty")
        if not self.path:
            raise ValueError("RepositorySnapshot.path must not be empty")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    repository: str
    change_type: str
    blast_radius: BlastRadius
    requirement_before: str
    requirement_after: str
    rationale: str
    acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()
    expected_affected_artifacts: tuple[ArtifactRef, ...] = ()
    expected_actions: tuple[tuple[ArtifactRef, ActionKind], ...] = ()
    architecture_constraints: tuple[ArchitectureConstraint, ...] = ()
    hidden_tests: tuple[str, ...] = ()
    evaluator_asset: str = ""
    post_generation_command: tuple[str, ...] = ()
    require_new_migration: bool = False

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("Scenario.scenario_id must not be empty")
        if not self.repository:
            raise ValueError("Scenario.repository must not be empty")


@dataclass(frozen=True)
class ScenarioSequence:
    scenarios: tuple[Scenario, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for s in self.scenarios:
            if s.scenario_id in seen:
                raise ValueError(f"Duplicate scenario_id in sequence: {s.scenario_id}")
            seen.add(s.scenario_id)


# ---------------------------------------------------------------------------
# Impact Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupportingEvidence:
    description: str
    source: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("SupportingEvidence.description must not be empty")


@dataclass(frozen=True)
class ImpactDecision:
    artifact: ArtifactRef
    action: ActionKind
    rationale: str = ""
    supporting_evidence: tuple[SupportingEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale:
            object.__setattr__(self, "rationale", "")


@dataclass(frozen=True)
class ImpactPrediction:
    decisions: tuple[ImpactDecision, ...] = ()
    errors: tuple[str, ...] = ()
    token_usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        if self.decisions and self.errors:
            pass


# ---------------------------------------------------------------------------
# Execution Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    max_iterations: int = 3
    max_tokens: int = 0
    timeout_seconds: int = 0

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("Budget.max_iterations must be >= 1")
        if self.max_tokens < 0:
            raise ValueError("Budget.max_tokens must be >= 0")
        if self.timeout_seconds < 0:
            raise ValueError("Budget.timeout_seconds must be >= 0")


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0:
            raise ValueError("TokenUsage.prompt_tokens must be >= 0")
        if self.completion_tokens < 0:
            raise ValueError("TokenUsage.completion_tokens must be >= 0")
        if self.total_tokens < 0:
            raise ValueError("TokenUsage.total_tokens must be >= 0")


@dataclass(frozen=True)
class LLMResponse:
    text: str
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    finish_reason: str = ""

    def __post_init__(self) -> None:
        pass


@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    protocol_version: str
    repository_commit_sha: str
    scenario_id: str
    strategy_name: str
    timestamp: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("RunIdentity.run_id must not be empty")
        if not self.protocol_version:
            raise ValueError("RunIdentity.protocol_version must not be empty")
        if not self.repository_commit_sha:
            raise ValueError("RunIdentity.repository_commit_sha must not be empty")
        if not self.scenario_id:
            raise ValueError("RunIdentity.scenario_id must not be empty")
        if not self.strategy_name:
            raise ValueError("RunIdentity.strategy_name must not be empty")


@dataclass(frozen=True)
class FailureRecord:
    failure_kind: FailureKind
    message: str
    details: str = ""
    stage: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("FailureRecord.message must not be empty")


MODEL_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class RunRecord:
    identity: RunIdentity
    status: RunStatus
    prediction: ImpactPrediction | None = None
    failures: tuple[FailureRecord, ...] = ()
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    duration_seconds: float = 0.0
    schema_version: str = MODEL_SCHEMA_VERSION

    # Selection stage metrics
    selection_prompt_tokens: int = 0
    selection_completion_tokens: int = 0
    selection_total_tokens: int = 0
    selection_model_calls: int = 0
    selection_duration_seconds: float = 0.0
    selection_tool_calls: int = 0
    selection_tool_duration_seconds: float = 0.0
    selection_inspected_file_count: int = 0
    selection_tool_transcript: tuple[str, ...] = ()

    # Regeneration stage metrics
    regeneration_prompt_tokens: int = 0
    regeneration_completion_tokens: int = 0
    regeneration_total_tokens: int = 0
    regeneration_model_calls: int = 0
    regeneration_duration_seconds: float = 0.0

    # Functional validation stage metrics
    functional_validation_duration_seconds: float = 0.0

    # Migration generation stage metrics
    migration_generation_passed: bool | None = None
    migration_duration_seconds: float = 0.0
    generated_migration_paths: tuple[str, ...] = ()

    # Baseline validation stage metrics
    baseline_validation_passed: bool | None = None
    baseline_validation_duration_seconds: float = 0.0

    # Scenario evaluator stage metrics
    scenario_evaluator_passed: bool | None = None
    scenario_evaluator_duration_seconds: float = 0.0
    scenario_evaluator_checks: tuple[str, ...] = ()

    # Total workflow metrics (aggregated)
    total_workflow_tokens: int = 0
    total_workflow_model_calls: int = 0
    total_workflow_duration_seconds: float = 0.0

    # Artifact counting
    selected_artifact_count: int = 0
    regenerated_artifact_count: int = 0
    preserved_artifact_count: int = 0
    unresolved_human_review_count: int = 0
    functional_validation_passed: bool | None = None

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError("RunRecord.duration_seconds must be >= 0")
        if self.selection_duration_seconds < 0:
            raise ValueError("RunRecord.selection_duration_seconds must be >= 0")
        if self.selection_tool_duration_seconds < 0:
            raise ValueError("RunRecord.selection_tool_duration_seconds must be >= 0")
        if self.selection_tool_calls < 0:
            raise ValueError("RunRecord.selection_tool_calls must be >= 0")
        if self.selection_inspected_file_count < 0:
            raise ValueError("RunRecord.selection_inspected_file_count must be >= 0")
        if self.regeneration_duration_seconds < 0:
            raise ValueError("RunRecord.regeneration_duration_seconds must be >= 0")
        if self.functional_validation_duration_seconds < 0:
            raise ValueError("RunRecord.functional_validation_duration_seconds must be >= 0")
        if self.total_workflow_duration_seconds < 0:
            raise ValueError("RunRecord.total_workflow_duration_seconds must be >= 0")
        if self.migration_duration_seconds < 0:
            raise ValueError("RunRecord.migration_duration_seconds must be >= 0")
        if self.baseline_validation_duration_seconds < 0:
            raise ValueError("RunRecord.baseline_validation_duration_seconds must be >= 0")
        if self.scenario_evaluator_duration_seconds < 0:
            raise ValueError("RunRecord.scenario_evaluator_duration_seconds must be >= 0")


# ---------------------------------------------------------------------------
# Validation and Result Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    message: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ValidationCheck.name must not be empty")


@dataclass(frozen=True)
class ValidationReport:
    run_identity: RunIdentity
    checks: tuple[ValidationCheck, ...] = ()
    passed: bool = False
    schema_version: str = MODEL_SCHEMA_VERSION


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: float | None
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MetricValue.name must not be empty")


@dataclass(frozen=True)
class AnalysisReport:
    title: str
    metrics: tuple[MetricValue, ...] = ()
    summary: str = ""
    schema_version: str = MODEL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("AnalysisReport.title must not be empty")


# ---------------------------------------------------------------------------
# Graph and Provenance Models (used by protocol interfaces)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[str, ...] = ()
    edges: tuple[tuple[str, str], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProvenanceEvent:
    timestamp: datetime
    layer: str
    action: str
    input_hash: str
    output_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
