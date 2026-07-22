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


class FullContextStrategy:
    """Upper-bound reference: all signals available (graph + semantic + tests + LLM context)."""

    def __init__(
        self,
        graph: DependencyGraph | None = None,
        coverage_map: dict[str, list[str]] | None = None,
        semantic_threshold: float = 0.3,
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
        graph_set = self._graph_propagate(artifact_universe)
        semantic_set = self._semantic_similarity(requirement_change, artifact_universe)
        trace_set = self._traceability(artifact_universe)

        all_impacted = graph_set | semantic_set | trace_set

        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            signals: list[str] = []
            if artifact.path in graph_set:
                signals.append("graph")
            if artifact.path in semantic_set:
                signals.append("semantic")
            if artifact.path in trace_set:
                signals.append("traceability")

            if len(signals) >= 2:
                action = ActionKind.regenerate
                rationale = f"full_context: {len(signals)} signals ({', '.join(signals)})"
            elif len(signals) == 1:
                action = ActionKind.regenerate
                rationale = f"full_context: single signal ({signals[0]})"
            else:
                action = ActionKind.preserve
                rationale = "full_context: no signals"

            if artifact.path in all_impacted:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=action,
                        rationale=rationale,
                        supporting_evidence=tuple(
                            SupportingEvidence(
                                description=f"Signal: {s}",
                                source=f"full_context_{s}",
                            )
                            for s in signals
                        ) or (SupportingEvidence(description="No signals", source="full_context"),),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="full_context: not reached by any signal",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))

    def _graph_propagate(self, artifact_universe: ArtifactUniverse) -> set[str]:
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
            for nb in adjacency.get(node, set()):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return visited

    def _semantic_similarity(
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
            sim = len(intersection) / len(union) if union else 0.0
            if sim >= self._semantic_threshold:
                impacted.add(artifact.path)
        return impacted

    def _traceability(self, artifact_universe: ArtifactUniverse) -> set[str]:
        covered: set[str] = set()
        for _test, sources in self._coverage_map.items():
            covered.update(sources)
        return covered & {a.path for a in artifact_universe.artifacts}
