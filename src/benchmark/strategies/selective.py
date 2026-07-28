from __future__ import annotations

from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactUniverse,
    DependencyGraph,
    ImpactDecision,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    SupportingEvidence,
)
from benchmark.selection.dependency_scope import ArtifactDescriptor, select_dependency_scope


class HybridSelectiveStrategy:
    def __init__(
        self,
        graph: DependencyGraph | None = None,
        artifact_descriptors: tuple[ArtifactDescriptor, ...] = (),
    ) -> None:
        self._graph = graph or DependencyGraph()
        self._artifact_descriptors = artifact_descriptors

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        selected = select_dependency_scope(
            requirement_change,
            artifact_universe,
            self._artifact_descriptors,
            self._graph,
        )

        if not selected:
            return ImpactPrediction(
                errors=(
                    "selective: no seed artifacts matched the requirement. "
                    "Cannot determine impacted scope from available descriptors.",
                ),
                decisions=tuple(
                    ImpactDecision(
                        artifact=a,
                        action=ActionKind.preserve,
                        rationale="selective: no impact scope determined",
                        supporting_evidence=(
                            SupportingEvidence(
                                description="No seed artifacts determined from requirement analysis",
                                source="selective",
                            ),
                        ),
                    )
                    for a in artifact_universe.artifacts
                ),
            )

        selected_set = set(selected)
        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            if artifact.path in selected_set:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale="selective: artifact in dependency scope",
                        supporting_evidence=(
                            SupportingEvidence(
                                description="Artifact selected by dependency-aware scope analysis",
                                source="selective",
                            ),
                        ),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="selective: artifact outside dependency scope",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))
