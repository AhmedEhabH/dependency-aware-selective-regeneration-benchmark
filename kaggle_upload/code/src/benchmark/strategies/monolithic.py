from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    SupportingEvidence,
)


class MonolithicRegenerationStrategy:
    """Baseline strategy: regenerate every artifact unconditionally."""

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        decisions = tuple(
            ImpactDecision(
                artifact=artifact,
                action=ActionKind.regenerate,
                rationale="monolithic: all artifacts regenerated",
                supporting_evidence=(
                    SupportingEvidence(
                        description="Monolithic strategy regenerates all artifacts",
                        source="monolithic",
                    ),
                ),
            )
            for artifact in artifact_universe.artifacts
        )
        return ImpactPrediction(decisions=decisions)
