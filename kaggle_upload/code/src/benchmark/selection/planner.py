from __future__ import annotations

from dataclasses import dataclass, field

from benchmark.core.enums import ActionKind
from benchmark.core.models import ArtifactRef, ArtifactUniverse, ImpactPrediction


@dataclass(frozen=True)
class ArtifactSelection:
    artifacts: tuple[ArtifactRef, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class RegenerationPlan:
    ordered_artifacts: tuple[ArtifactRef, ...] = ()
    actions: dict[str, ActionKind] = field(default_factory=dict)

    def __post_init__(self) -> None:
        pass


class ArtifactSelector:
    """Determines which artifacts are impacted based on an ImpactPrediction."""

    def select(
        self,
        prediction: ImpactPrediction,
        artifact_universe: ArtifactUniverse,
    ) -> ArtifactSelection:
        selected: list[ArtifactRef] = []
        for decision in prediction.decisions:
            if decision.action in (ActionKind.regenerate, ActionKind.human_review):
                selected.append(decision.artifact)

        if not selected:
            selected = list(artifact_universe.artifacts)

        return ArtifactSelection(
            artifacts=tuple(selected),
            rationale=f"selected {len(selected)} artifacts from {len(prediction.decisions)} decisions",
        )


class RegenerationPlanner:
    """Orders impacted artifacts in dependency-safe regeneration order."""

    def plan(
        self,
        selection: ArtifactSelection,
        prediction: ImpactPrediction,
    ) -> RegenerationPlan:
        action_map: dict[str, ActionKind] = {}
        for decision in prediction.decisions:
            action_map[decision.artifact.path] = decision.action

        regenerate_first = [
            a for a in selection.artifacts
            if action_map.get(a.path) == ActionKind.regenerate
        ]
        review_later = [
            a for a in selection.artifacts
            if action_map.get(a.path) == ActionKind.human_review
        ]
        validate_last = [
            a for a in selection.artifacts
            if action_map.get(a.path) == ActionKind.validate_only
        ]

        ordered = regenerate_first + review_later + validate_last
        return RegenerationPlan(
            ordered_artifacts=tuple(ordered),
            actions={a.path: action_map.get(a.path, ActionKind.regenerate) for a in ordered},
        )
