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


class StaticOnlyStrategy:
    """Static dependency graph analysis only — no LLM, no semantics."""

    def __init__(self, graph: DependencyGraph | None = None) -> None:
        self._graph = graph

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        if self._graph is None:
            return ImpactPrediction(
                errors=("static strategy: no dependency graph provided",),
            )

        changed_paths = self._find_changed_paths(requirement_change, artifact_universe)
        impacted = self._propagate(changed_paths, self._graph)

        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            if artifact.path in impacted or artifact.path in changed_paths:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale="static: reachable from changed artifact in dependency graph",
                        supporting_evidence=(
                            SupportingEvidence(
                                description=f"Dependency graph propagation from {changed_paths}",
                                source="static_graph",
                            ),
                        ),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="static: not reachable from changed artifacts",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))

    def _find_changed_paths(
        self,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> set[str]:
        return {a.path for a in artifact_universe.artifacts}

    def _propagate(
        self, seeds: set[str], graph: DependencyGraph
    ) -> set[str]:
        adjacency: dict[str, set[str]] = {}
        for src, dst in graph.edges:
            adjacency.setdefault(src, set()).add(dst)
            adjacency.setdefault(dst, set()).add(src)

        visited: set[str] = set(seeds)
        queue = list(seeds)
        while queue:
            node = queue.pop()
            for neighbour in adjacency.get(node, set()):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        return visited
