from __future__ import annotations

from typing import TYPE_CHECKING

from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    SupportingEvidence,
)

if TYPE_CHECKING:
    from benchmark.core.protocols import LLMBackend


class RepositoryAgentStrategy:
    """LLM-powered strategy: sends full repository context to an LLM for analysis."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        import asyncio

        prompt = self._build_prompt(repository, requirement_change, artifact_universe)
        try:
            response = asyncio.get_event_loop().run_until_complete(
                self._backend.generate(prompt=prompt, temperature=0.0, max_tokens=4096)
            )
            return self._parse_response(response.text, artifact_universe)
        except Exception as exc:
            return ImpactPrediction(
                errors=(f"agent strategy failed: {exc}",),
            )

    def _build_prompt(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> str:
        artifact_lines = "\n".join(
            f"  - {a.path} ({a.artifact_type.value})"
            for a in artifact_universe.artifacts
        )
        return (
            f"Repository: {repository.identity.name} @ {repository.commit_sha}\n"
            f"Change: {requirement_change.before} -> {requirement_change.after}\n"
            f"Artifacts:\n{artifact_lines}\n"
            f"Which artifacts need regeneration? Reply JSON list of paths."
        )

    def _parse_response(
        self, text: str, artifact_universe: ArtifactUniverse
    ) -> ImpactPrediction:
        import json

        try:
            data = json.loads(text)
            if not isinstance(data, list):
                data = []
        except (json.JSONDecodeError, TypeError):
            data = []

        known_paths = {a.path for a in artifact_universe.artifacts}
        decisions: list[ImpactDecision] = []
        for path in data:
            if isinstance(path, str) and path in known_paths:
                ref = next(a for a in artifact_universe.artifacts if a.path == path)
                decisions.append(
                    ImpactDecision(
                        artifact=ref,
                        action=ActionKind.regenerate,
                        rationale="agent: LLM identified for regeneration",
                        supporting_evidence=(
                            SupportingEvidence(
                                description="LLM agent analysis",
                                source="agent_strategy",
                            ),
                        ),
                    )
                )
        return ImpactPrediction(decisions=tuple(decisions))
