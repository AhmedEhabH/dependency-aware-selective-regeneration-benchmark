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


class TraceabilityOnlyStrategy:
    """Test-coverage traceability only — which tests cover which artifacts."""

    def __init__(self, coverage_map: dict[str, list[str]] | None = None) -> None:
        self._coverage_map = coverage_map or {}

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        covered_artifacts: set[str] = set()
        for _test, sources in self._coverage_map.items():
            covered_artifacts.update(sources)

        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            if artifact.path in covered_artifacts:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale="traceability: covered by test traceability map",
                        supporting_evidence=(
                            SupportingEvidence(
                                description="Test coverage traceability",
                                source="traceability",
                            ),
                        ),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="traceability: not covered by any test",
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))
