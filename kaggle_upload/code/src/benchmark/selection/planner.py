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

    @property
    def regenerate_artifact_paths(self) -> tuple[str, ...]:
        return tuple(
            a.path for a in self.ordered_artifacts
            if self.actions.get(a.path) == ActionKind.regenerate
        )

    @property
    def human_review_artifact_paths(self) -> tuple[str, ...]:
        return tuple(
            a.path for a in self.ordered_artifacts
            if self.actions.get(a.path) == ActionKind.human_review
        )


def compute_artifact_counts(prediction: ImpactPrediction) -> dict[str, int]:
    regenerate = 0
    preserve = 0
    human_review = 0
    for decision in prediction.decisions:
        if decision.action == ActionKind.regenerate:
            regenerate += 1
        elif decision.action == ActionKind.preserve:
            preserve += 1
        elif decision.action == ActionKind.human_review:
            human_review += 1
    return {
        "selected": regenerate + human_review,
        "regenerate": regenerate,
        "preserve": preserve,
        "human_review": human_review,
    }


class ArtifactSelector:
    """Determines which artifacts are impacted based on an ImpactPrediction.

    Policy:
    - ``regenerate`` artifacts enter the selection (to be executed).
    - ``human_review`` artifacts enter the selection (recorded as unresolved).
    - ``preserve`` artifacts are excluded from selection.
    - Deterministic ordering is guaranteed by preserving decision order.
    """

    def select(
        self,
        prediction: ImpactPrediction,
        artifact_universe: ArtifactUniverse,  # noqa: ARG002 — kept for interface stability
    ) -> ArtifactSelection:
        selected: list[ArtifactRef] = []
        for decision in prediction.decisions:
            if decision.action in (ActionKind.regenerate, ActionKind.human_review):
                selected.append(decision.artifact)

        return ArtifactSelection(
            artifacts=tuple(selected),
            rationale=f"selected {len(selected)} artifacts from {len(prediction.decisions)} decisions",
        )


class RegenerationPlanner:
    """Orders impacted artifacts in deterministic regeneration order.

    Ordering:
    1. ``regenerate`` artifacts first (executed).
    2. ``human_review`` artifacts second (recorded, not executed).
    3. ``validate_only`` artifacts last.
    """

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
