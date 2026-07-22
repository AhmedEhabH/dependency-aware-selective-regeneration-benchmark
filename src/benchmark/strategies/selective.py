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


class HybridSelectiveStrategy:
    """Main strategy: combines static graph + semantic + traceability signals."""

    def __init__(
        self,
        graph: DependencyGraph | None = None,
        coverage_map: dict[str, list[str]] | None = None,
        semantic_threshold: float = 0.5,
    ) -> None:
        self._graph = graph
        self._coverage_map = coverage_map or {}
        self._semantic_threshold = semantic_threshold

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        graph_impacted = self._graph_signal(artifact_universe)
        semantic_impacted = self._semantic_signal(requirement_change, artifact_universe)
        traceability_impacted = self._traceability_signal(artifact_universe)

        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            signals: list[str] = []
            if artifact.path in graph_impacted:
                signals.append("graph")
            if artifact.path in semantic_impacted:
                signals.append("semantic")
            if artifact.path in traceability_impacted:
                signals.append("traceability")

            if len(signals) >= 2:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale=f"selective: {len(signals)} signals agree ({', '.join(signals)})",
                        supporting_evidence=tuple(
                            SupportingEvidence(
                                description=f"Signal: {s}",
                                source=f"selective_{s}",
                            )
                            for s in signals
                        ),
                    )
                )
            elif len(signals) == 1:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.human_review,
                        rationale=f"selective: only 1 signal ({signals[0]}), needs human review",
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="selective: no signals indicate impact",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))

    def _graph_signal(self, artifact_universe: ArtifactUniverse) -> set[str]:
        if self._graph is None:
            return set()
        adjacency: dict[str, set[str]] = {}
        for src, dst in self._graph.edges:
            adjacency.setdefault(src, set()).add(dst)
            adjacency.setdefault(dst, set()).add(src)

        seeds = {a.path for a in artifact_universe.artifacts}
        visited: set[str] = set(seeds)
        queue = list(seeds)
        while queue:
            node = queue.pop()
            for neighbour in adjacency.get(node, set()):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        return visited

    def _semantic_signal(
        self,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> set[str]:
        change_text = f"{requirement_change.before} {requirement_change.after}".lower()
        change_tokens = set(change_text.split())
        impacted: set[str] = set()
        for artifact in artifact_universe.artifacts:
            path_tokens = set(
                artifact.path.lower().replace("/", " ").replace("_", " ").replace(".", " ").split()
            )
            if not change_tokens or not path_tokens:
                continue
            intersection = change_tokens & path_tokens
            union = change_tokens | path_tokens
            similarity = len(intersection) / len(union) if union else 0.0
            if similarity >= self._semantic_threshold:
                impacted.add(artifact.path)
        return impacted

    def _traceability_signal(self, artifact_universe: ArtifactUniverse) -> set[str]:
        covered: set[str] = set()
        for _test, sources in self._coverage_map.items():
            covered.update(sources)
        return covered & {a.path for a in artifact_universe.artifacts}
