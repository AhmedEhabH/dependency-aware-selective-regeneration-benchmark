from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)

INITIAL_PROMPT_TEMPLATE = """\
You are an AI software engineer analyzing a repository to determine which artifacts need regeneration after a requirement change.

Repository: {repo_name}
Repository path: {repo_path}
Commit: {commit_sha}

Requirement change:
  Before: {before}
  After: {after}

Acceptance criteria:
{acceptance_criteria}

Artifacts:
{artifact_list}

Analyze each artifact's relevance to the requirement change. Consider:
- The artifact's purpose based on its path and type
- Whether it likely contains logic affected by the change
- Whether it needs modification, can be preserved, or needs human review

Respond with a valid JSON object containing:
{{
  "decisions": [
    {{
      "path": "artifact/path",
      "action": "regenerate" | "preserve" | "human_review",
      "rationale": "brief explanation"
    }}
  ],
  "requires_iteration": true | false
}}

Select only artifacts that are genuinely affected. Prefer preservation over unnecessary regeneration.

Output compact JSON only — no markdown fences, no preamble, no trailing commentary.
"""

REVISE_PROMPT_TEMPLATE = """\
You are an AI software engineer revising your previous plan based on validation feedback.

Requirement change:
  Before: {before}
  After: {after}

Artifacts:
{artifact_list}

Previous decisions:
{previous_decisions}

Validation result:
  Exit code: {exit_code}
  Validation stdout:
{val_stdout}
  Validation stderr:
{val_stderr}

Current workspace state (previously generated/selected files):
{workspace_summary}

Remaining attempts: {remaining_attempts}
Remaining token budget: {remaining_tokens}

Revise your plan. Consider:
- The validation errors indicate specific issues in the regenerated code
- You may need to select different artifacts or change your approach
- You can generate replacement code for the same or different files
- If validation already passed, return the same decisions

Respond with a valid JSON object containing:
{{
  "decisions": [
    {{
      "path": "artifact/path",
      "action": "regenerate" | "preserve" | "human_review",
      "rationale": "brief explanation"
    }}
  ],
  "requires_iteration": true | false
}}

If no further changes are needed, set requires_iteration to false.

Output compact JSON only — no markdown fences, no preamble, no trailing commentary.
"""


def _build_artifact_list(artifact_universe: ArtifactUniverse) -> str:
    lines = []
    for a in artifact_universe.artifacts:
        lines.append(f"  - {a.path} ({a.artifact_type.value})")
    return "\n".join(lines)


def _build_decision_list(prediction: ImpactPrediction) -> str:
    lines = []
    for d in prediction.decisions:
        lines.append(f"  - {d.artifact.path}: {d.action.value} ({d.rationale})")
    return "\n".join(lines) if lines else "  (no decisions)"


class IterativeRepositoryAgentStrategy:
    """Iterative agent that revises its plan using validation feedback."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self._last_requires_iteration: bool = True

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        max_tokens: int = 0,
    ) -> ImpactPrediction:
        prompt = INITIAL_PROMPT_TEMPLATE.format(
            repo_name=repository.identity.name,
            repo_path=repository.path,
            commit_sha=repository.commit_sha,
            before=requirement_change.before,
            after=requirement_change.after,
            acceptance_criteria=self._format_criteria(requirement_change.acceptance_criteria),
            artifact_list=_build_artifact_list(artifact_universe),
        )

        import asyncio

        response = asyncio.get_event_loop().run_until_complete(
            self._backend.generate(prompt=prompt, temperature=0.0, max_tokens=max_tokens if max_tokens > 0 else 0)
        )

        parsed = self._parse_response(response.text, artifact_universe)
        tok = response.token_usage
        if tok and (tok.prompt_tokens > 0 or tok.completion_tokens > 0):
            object.__setattr__(parsed, "token_usage", tok)
        if parsed.errors:
            fr = response.finish_reason or "unknown"
            object.__setattr__(parsed, "errors", (f"finish_reason={fr}: {parsed.errors[0]}",))
        return parsed

    def revise_plan(
        self,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        previous_prediction: ImpactPrediction,
        exit_code: int,
        val_stdout: str,
        val_stderr: str,
        workspace_summary: str,
        remaining_attempts: int,
        remaining_tokens: int,
    ) -> ImpactPrediction:
        prompt = REVISE_PROMPT_TEMPLATE.format(
            before=requirement_change.before,
            after=requirement_change.after,
            artifact_list=_build_artifact_list(artifact_universe),
            previous_decisions=_build_decision_list(previous_prediction),
            exit_code=exit_code,
            val_stdout=val_stdout[:2000],
            val_stderr=val_stderr[:2000],
            workspace_summary=workspace_summary[:3000],
            remaining_attempts=remaining_attempts,
            remaining_tokens=remaining_tokens,
        )

        import asyncio

        mt = remaining_tokens if remaining_tokens > 0 else 0
        response = asyncio.get_event_loop().run_until_complete(
            self._backend.generate(prompt=prompt, temperature=0.0, max_tokens=mt)
        )

        parsed = self._parse_response(response.text, artifact_universe)
        tok = response.token_usage
        if tok and (tok.prompt_tokens > 0 or tok.completion_tokens > 0):
            object.__setattr__(parsed, "token_usage", tok)
        if parsed.errors:
            fr = response.finish_reason or "unknown"
            object.__setattr__(parsed, "errors", (f"finish_reason={fr}: {parsed.errors[0]}",))
        return parsed

    @property
    def last_requires_iteration(self) -> bool:
        return self._last_requires_iteration

    def _format_criteria(self, criteria: tuple[str, ...]) -> str:
        if not criteria:
            return "  (none specified)"
        return "\n".join(f"  - {c}" for c in criteria)

    def _parse_response(
        self,
        text: str,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return ImpactPrediction(
                errors=(f"iterative agent: could not parse LLM response as JSON: {text[:200]}",),
            )

        if not isinstance(data, dict):
            return ImpactPrediction(
                errors=(f"iterative agent: expected JSON object, got {type(data).__name__}",),
            )

        raw_decisions = data.get("decisions", [])
        if not isinstance(raw_decisions, list):
            return ImpactPrediction(
                errors=("iterative agent: 'decisions' must be a list",),
            )

        requires_iteration = data.get("requires_iteration", True)
        self._last_requires_iteration = bool(requires_iteration)
        known_paths = {a.path for a in artifact_universe.artifacts}
        decisions: list[ImpactDecision] = []

        for entry in raw_decisions:
            if not isinstance(entry, dict):
                continue

            path = entry.get("path", "")
            if path not in known_paths:
                continue

            action_str = entry.get("action", "preserve")
            try:
                action = ActionKind(action_str)
            except ValueError:
                action = ActionKind.preserve

            ref = next(a for a in artifact_universe.artifacts if a.path == path)
            decisions.append(
                ImpactDecision(
                    artifact=ref,
                    action=action,
                    rationale=entry.get("rationale", "iterative_agent decision"),
                    supporting_evidence=(
                        SupportingEvidence(
                            description="iterative agent analysis",
                            source="iterative_agent_strategy",
                        ),
                    ),
                )
            )

        return ImpactPrediction(decisions=tuple(decisions))
