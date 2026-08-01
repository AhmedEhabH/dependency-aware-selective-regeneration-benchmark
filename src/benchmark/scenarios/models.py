from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius
from benchmark.core.models import (
    AcceptanceCriterion,
    ArchitectureConstraint,
    ArtifactRef,
    Scenario,
)


def _parse_blast_radius(value: str) -> BlastRadius:
    try:
        return BlastRadius(value)
    except ValueError as err:
        raise ValueError(f"Invalid blast_radius: {value}") from err


def _parse_artifact_ref(ref_str: str) -> ArtifactRef:
    path_part = ref_str.split(":", 1)[0].strip() if ":" in ref_str else ref_str.strip()
    if not path_part:
        raise ValueError(f"Cannot parse artifact ref: {ref_str}")
    ext = path_part.rsplit(".", 1)[-1].lower() if "." in path_part else ""
    type_map: dict[str, ArtifactType] = {
        "py": ArtifactType.source,
        "js": ArtifactType.source,
        "ts": ArtifactType.source,
        "html": ArtifactType.source,
        "css": ArtifactType.source,
        "yaml": ArtifactType.configuration,
        "yml": ArtifactType.configuration,
        "json": ArtifactType.configuration,
        "toml": ArtifactType.configuration,
        "cfg": ArtifactType.configuration,
        "ini": ArtifactType.configuration,
        "md": ArtifactType.documentation,
        "rst": ArtifactType.documentation,
        "txt": ArtifactType.documentation,
    }
    artifact_type = type_map.get(ext, ArtifactType.source)
    return ArtifactRef(path=path_part, artifact_type=artifact_type)


def _parse_artifact_instruction(ref_str: str) -> tuple[str, str] | None:
    """Parse ``path:instruction`` while keeping legacy path-only entries valid."""
    if ":" not in ref_str:
        return None
    path_part, instruction = ref_str.split(":", 1)
    path = path_part.strip()
    detail = instruction.strip()
    if not path or not detail:
        return None
    return path, detail


_ACTION_ALIASES: dict[str, ActionKind] = {
    "modify": ActionKind.regenerate,
    "create": ActionKind.regenerate,
}


def _parse_action_kind(value: str) -> ActionKind:
    if value in _ACTION_ALIASES:
        return _ACTION_ALIASES[value]
    try:
        return ActionKind(value)
    except ValueError as err:
        raise ValueError(f"Invalid action_kind: {value}") from err


@dataclass(frozen=True)
class ScenarioModel:
    scenario_id: str
    repository: str
    change_type: str
    blast_radius: str
    requirement_before: str
    requirement_after: str
    rationale: str
    acceptance_criteria: tuple[str, ...] = ()
    expected_affected_artifacts: tuple[str, ...] = ()
    expected_actions: dict[str, str] = field(default_factory=dict)
    regression_obligations: tuple[str, ...] = ()
    architecture_constraints: tuple[str, ...] = ()
    hidden_tests: tuple[dict[str, str], ...] = ()
    evaluator_asset: str = ""
    post_generation_command: tuple[str, ...] = ()
    require_new_migration: bool = False

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("ScenarioModel.scenario_id must not be empty")
        if not self.repository:
            raise ValueError("ScenarioModel.repository must not be empty")
        if not self.change_type:
            raise ValueError("ScenarioModel.change_type must not be empty")
        if not self.blast_radius:
            raise ValueError("ScenarioModel.blast_radius must not be empty")
        if not self.requirement_before:
            raise ValueError("ScenarioModel.requirement_before must not be empty")
        if not self.requirement_after:
            raise ValueError("ScenarioModel.requirement_after must not be empty")
        if not self.rationale:
            raise ValueError("ScenarioModel.rationale must not be empty")
        if not isinstance(self.post_generation_command, tuple):
            raise ValueError("ScenarioModel.post_generation_command must be a tuple")
        if not isinstance(self.require_new_migration, bool):
            raise ValueError("ScenarioModel.require_new_migration must be a bool")
        if not isinstance(self.evaluator_asset, str):
            raise ValueError("ScenarioModel.evaluator_asset must be a string")

    def to_core_scenario(self) -> Scenario:
        blast = _parse_blast_radius(self.blast_radius)

        criteria = tuple(
            AcceptanceCriterion(description=c) for c in self.acceptance_criteria
        )

        arch_constraints = tuple(
            ArchitectureConstraint(description=c) for c in self.architecture_constraints
        )

        affected = tuple(
            _parse_artifact_ref(a) for a in self.expected_affected_artifacts
        )
        artifact_instructions = tuple(
            parsed
            for raw in self.expected_affected_artifacts
            if (parsed := _parse_artifact_instruction(raw)) is not None
        )

        seen_actions: set[tuple[str, ActionKind]] = set()
        actions: list[tuple[ArtifactRef, ActionKind]] = []
        for ref_str, action_str in self.expected_actions.items():
            ref = _parse_artifact_ref(ref_str)
            action = _parse_action_kind(action_str)
            key = (ref.path, action)
            if key not in seen_actions:
                seen_actions.add(key)
                actions.append((ref, action))

        hidden_raw: list[str] = []
        for ht in self.hidden_tests:
            if isinstance(ht, dict):
                desc = ht.get("description", "")
                if desc:
                    hidden_raw.append(desc)
            elif isinstance(ht, str):
                hidden_raw.append(ht)

        return Scenario(
            scenario_id=self.scenario_id,
            repository=self.repository,
            change_type=self.change_type,
            blast_radius=blast,
            requirement_before=self.requirement_before,
            requirement_after=self.requirement_after,
            rationale=self.rationale,
            acceptance_criteria=criteria,
            expected_affected_artifacts=affected,
            expected_artifact_instructions=artifact_instructions,
            expected_actions=tuple(actions),
            architecture_constraints=arch_constraints,
            hidden_tests=tuple(hidden_raw),
            evaluator_asset=self.evaluator_asset,
            post_generation_command=self.post_generation_command,
            require_new_migration=self.require_new_migration,
        )

    @staticmethod
    def _normalize_expected_actions(raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        result: dict[str, str] = {}
        for key, value in raw.items():
            if isinstance(value, list):
                for path in value:
                    result[str(path)] = str(key)
            elif isinstance(value, str):
                result[str(key)] = value
            else:
                result[str(key)] = str(value)
        return result

    @staticmethod
    def from_yaml_mapping(data: dict[str, Any]) -> ScenarioModel:
        hidden_raw = data.get("hidden_tests", [])
        hidden_normalized: list[dict[str, str]] = []
        for item in hidden_raw:
            if isinstance(item, dict):
                hidden_normalized.append(
                    {
                        "description": str(item.get("description", "")),
                        "type": str(item.get("type", "")),
                    }
                )
            elif isinstance(item, str):
                hidden_normalized.append({"description": item, "type": ""})

        raw_command = data.get("post_generation_command", [])
        if not isinstance(raw_command, list):
            raise ValueError("ScenarioModel.post_generation_command must be a list")
        command_items: list[str] = []
        for item in raw_command:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    "ScenarioModel.post_generation_command items must be non-empty strings"
                )
            command_items.append(item)
        command_tuple = tuple(command_items)

        raw_migration = data.get("require_new_migration", False)
        if not isinstance(raw_migration, bool):
            raise ValueError("ScenarioModel.require_new_migration must be a bool")

        raw_evaluator_asset = data.get("evaluator_asset", "")
        if not isinstance(raw_evaluator_asset, str):
            raise ValueError("ScenarioModel.evaluator_asset must be a string")

        return ScenarioModel(
            scenario_id=str(data.get("scenario_id", "")),
            repository=str(data.get("repository", "")),
            change_type=str(data.get("change_type", "")),
            blast_radius=str(data.get("blast_radius", "")),
            requirement_before=str(data.get("requirement_before", "")),
            requirement_after=str(data.get("requirement_after", "")),
            rationale=str(data.get("rationale", "")),
            acceptance_criteria=tuple(str(c) for c in data.get("acceptance_criteria", [])),
            expected_affected_artifacts=tuple(
                str(a) for a in data.get("expected_affected_artifacts", [])
            ),
            expected_actions=ScenarioModel._normalize_expected_actions(
                data.get("expected_actions", {})
            ),
            regression_obligations=tuple(
                str(r) for r in data.get("regression_obligations", [])
            ),
            architecture_constraints=tuple(
                str(c) for c in data.get("architecture_constraints", [])
            ),
            hidden_tests=tuple(hidden_normalized),
            evaluator_asset=raw_evaluator_asset,
            post_generation_command=command_tuple,
            require_new_migration=raw_migration,
        )
