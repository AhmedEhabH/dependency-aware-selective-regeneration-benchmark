from __future__ import annotations

from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    SupportingEvidence,
)


class SemanticOnlyStrategy:
    """Semantic similarity analysis only — no graph, no tests."""

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        change_text = f"{requirement_change.before} {requirement_change.after}"

        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            similarity = self._compute_similarity(change_text, artifact.path)
            if similarity >= self._threshold:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale=f"semantic: similarity {similarity:.3f} >= threshold {self._threshold}",
                        supporting_evidence=(
                            SupportingEvidence(
                                description=f"Text similarity score: {similarity:.3f}",
                                source="semantic_embedding",
                            ),
                        ),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale=f"semantic: similarity {similarity:.3f} < threshold {self._threshold}",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))

    def _compute_similarity(self, text: str, path: str) -> float:
        text_lower = text.lower()
        path_lower = path.lower()
        text_tokens = set(text_lower.split())
        path_tokens = set(path_lower.replace("/", " ").replace("_", " ").replace(".", " ").split())
        if not text_tokens or not path_tokens:
            return 0.0
        intersection = text_tokens & path_tokens
        union = text_tokens | path_tokens
        return len(intersection) / len(union) if union else 0.0
