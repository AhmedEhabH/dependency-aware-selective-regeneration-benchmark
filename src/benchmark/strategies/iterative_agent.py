from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    SupportingEvidence,
    TokenUsage,
)
from benchmark.execution.budgets import resolve_completion_allowance

if TYPE_CHECKING:
    from benchmark.core.protocols import LLMBackend
    from benchmark.strategies.repository_tools import RepositoryTools

logger = logging.getLogger(__name__)

MAX_AGENT_CALLS: int = 8


class AgentCallsExhaustedError(Exception):
    """Raised when the agent has no remaining LLM calls."""
    pass

TOOL_SCHEMA = """
You have access to the following tools. Respond with exactly one JSON object.

1. list_files — List files in the repository.
   {"action": "list_files", "path": "<directory>"}

2. read_file — Read contents of a file.
   {"action": "read_file", "path": "<file_path>"}

3. search_text — Case-insensitive text search.
   {"action": "search_text", "query": "<text>", "path": "<directory>"}

4. final — Submit your final selected paths.
   {"action": "final", "selected_paths": ["path1", "path2"], "rationale": "..."}
"""

INITIAL_SYSTEM_PROMPT = """\
You are analyzing a code repository to determine which files need to be modified.
Use the tools to explore the repository, then submit your final selection.

Requirement change:
  Before: {before}
  After: {after}

Acceptance criteria:
{acceptance_criteria}

Editable paths:
{editable_paths}

{TOOL_SCHEMA}

Important rules:
- You may make up to 8 tool calls to explore.
- selected_paths must be a non-empty subset of the editable paths.
- Only include paths that actually need changes.
"""

REVISE_SYSTEM_PROMPT = """\
You previously selected files for modification. The validation step failed.
Revise your selection using the same tools.

Requirement change:
  Before: {before}
  After: {after}

Acceptance criteria:
{acceptance_criteria}

Editable paths:
{editable_paths}

Previous selected_paths: {previous_paths}
Validation exit code: {exit_code}
Validation stdout: {val_stdout}
Validation stderr: {val_stderr}

{TOOL_SCHEMA}

You have {remaining_calls} tool calls remaining.
Submit a revised final selection.
"""


def _format_criteria(criteria: tuple[str, ...]) -> str:
    if not criteria:
        return "  (none specified)"
    return "\n".join(f"  - {c}" for c in criteria)


def _parse_action_response(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if "action" in data:
        return data
    return None


def _parse_requires_iteration(action: dict[str, Any]) -> bool:
    val = action.get("requires_iteration", True) if isinstance(action, dict) else True
    return bool(val)


def _build_tool_context() -> str:
    return TOOL_SCHEMA.strip()


def _build_initial_prompt(
    requirement_change: RequirementChange,
    editable_paths: tuple[str, ...],
) -> str:
    return INITIAL_SYSTEM_PROMPT.format(
        before=requirement_change.before,
        after=requirement_change.after,
        acceptance_criteria=_format_criteria(requirement_change.acceptance_criteria),
        editable_paths="\n".join(f"  - {p}" for p in editable_paths),
        TOOL_SCHEMA=_build_tool_context(),
    )


def _build_revise_prompt(
    requirement_change: RequirementChange,
    editable_paths: tuple[str, ...],
    previous_paths: tuple[str, ...],
    exit_code: int,
    val_stdout: str,
    val_stderr: str,
    remaining_calls: int,
) -> str:
    return REVISE_SYSTEM_PROMPT.format(
        before=requirement_change.before,
        after=requirement_change.after,
        acceptance_criteria=_format_criteria(requirement_change.acceptance_criteria),
        editable_paths="\n".join(f"  - {p}" for p in editable_paths),
        previous_paths=", ".join(previous_paths),
        exit_code=exit_code,
        val_stdout=val_stdout[:2000],
        val_stderr=val_stderr[:2000],
        TOOL_SCHEMA=_build_tool_context(),
        remaining_calls=remaining_calls,
    )


class IterativeRepositoryAgentStrategy:
    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self._tool_calls: int = 0
        self._model_calls: int = 0
        self._tool_duration: float = 0.0
        self._prompt_tokens: int = 0
        self._completion_tokens: int = 0
        self._total_tokens: int = 0
        self._inspected_files: set[str] = set()
        self._tool_transcript: list[str] = []
        self._last_requires_iteration: bool = True
        self._remaining_agent_calls: int = 0
        self._tools: RepositoryTools | None = None

    def begin_run(self, workspace_root: str | Path) -> None:
        root = Path(workspace_root).resolve()
        if not root.is_dir():
            raise ValueError(f"workspace_root must be an existing directory: {root}")
        self._tool_calls = 0
        self._model_calls = 0
        self._tool_duration = 0.0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0
        self._inspected_files = set()
        self._tool_transcript = []
        self._last_requires_iteration = True
        self._remaining_agent_calls = 8
        from benchmark.strategies.repository_tools import RepositoryTools
        self._tools = RepositoryTools(
            workspace_root=root,
            max_distinct_files=30,
        )

    def _record_call(
        self, prompt_tok: int, completion_tok: int, total_tok: int
    ) -> None:
        self._model_calls += 1
        self._prompt_tokens += prompt_tok
        self._completion_tokens += completion_tok
        self._total_tokens += total_tok

    def _record_tool(self, name: str, path: str, result: str, duration: float) -> None:
        self._tool_calls += 1
        self._tool_duration += duration
        self._tool_transcript.append(f"[{self._tool_calls}] {name} {path} -> {result[:100]}")

    def _generate_agent_response(self, prompt: str, max_completion_tokens: int) -> LLMResponse:
        import asyncio
        if self._remaining_agent_calls <= 0:
            raise AgentCallsExhaustedError("No remaining agent calls")
        self._remaining_agent_calls -= 1
        response = asyncio.get_event_loop().run_until_complete(
            self._backend.generate(prompt=prompt, temperature=0.0, max_tokens=max_completion_tokens)
        )
        tok = response.token_usage
        if tok:
            self._record_call(tok.prompt_tokens, tok.completion_tokens, tok.total_tokens)
        return response

    def _invoke_tool(
        self,
        action_name: str,
        action: dict[str, Any],
        prompt: str,
    ) -> str:
        tools = self._tools
        assert tools is not None
        t0 = time.monotonic()
        if action_name == "list_files":
            tool_path = action.get("path", ".")
            result = tools.list_files(tool_path)
        elif action_name == "read_file":
            tool_path = action.get("path", "")
            result = tools.read_file(tool_path)
        elif action_name == "search_text":
            query = action.get("query", "")
            tool_path = action.get("path", ".")
            result = tools.search_text(query, tool_path)
        else:
            return f"\n[error] Unknown action: {action_name}"
        dur = time.monotonic() - t0
        tool_path_display = action.get("path", ".")
        if action_name == "search_text":
            tool_path_display = f"{action.get('query', '')} in {action.get('path', '.')}"
        self._record_tool(action_name, tool_path_display,
            result.output[:200] if result.ok else result.error, dur)
        tag = action_name
        if action_name == "read_file":
            self._inspected_files.add(str(action.get("path", "")))
        out = result.output[:2000] if result.ok else result.error
        return f"\n[result] {tag}:\n{out}"

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        max_tokens: int = 0,
        *,
        max_completion_tokens_per_call: int = 4096,
        remaining_total_workflow_tokens: int | None = None,
    ) -> ImpactPrediction:
        tools = self._tools
        assert tools is not None, "begin_run() must be called before analyze_impact()"
        editable_paths = tuple(a.path for a in artifact_universe.artifacts)
        editable_set = set(editable_paths)
        selected_paths: list[str] = []
        local_remaining = remaining_total_workflow_tokens
        has_limit = remaining_total_workflow_tokens is not None

        prompt = _build_initial_prompt(requirement_change, editable_paths)

        prompt_tok_before = self._prompt_tokens
        completion_tok_before = self._completion_tokens
        total_tok_before = self._total_tokens

        while True:
            prompt_estimate = self._backend.count_prompt_tokens(prompt)
            allowance = resolve_completion_allowance(
                max_completion_tokens_per_call=max_completion_tokens_per_call,
                remaining_total_workflow_tokens=local_remaining,
                prompt_tokens=prompt_estimate,
            )
            if allowance <= 0:
                break
            try:
                response = self._generate_agent_response(prompt, allowance)
            except AgentCallsExhaustedError:
                if selected_paths:
                    break
                return ImpactPrediction(
                    token_usage=TokenUsage(
                        prompt_tokens=self._prompt_tokens - prompt_tok_before,
                        completion_tokens=self._completion_tokens - completion_tok_before,
                        total_tokens=self._total_tokens - total_tok_before,
                    ),
                    errors=("iterative_agent: no remaining agent calls",),
                    decisions=tuple(
                        ImpactDecision(
                            artifact=a,
                            action=ActionKind.preserve,
                            rationale="iterative_agent: no remaining calls",
                        )
                        for a in artifact_universe.artifacts
                    ),
                )

            usage = response.token_usage
            if has_limit and local_remaining is not None:
                if usage.completion_tokens > allowance:
                    break
                if local_remaining > 0 and usage.total_tokens > local_remaining:
                    break
                local_remaining = max(0, local_remaining - usage.total_tokens)

            action = _parse_action_response(response.text)
            if action is None:
                prompt += "\n[error] Invalid JSON response"
                if self._remaining_agent_calls <= 0:
                    break
                continue

            action_name = action.get("action", "")
            if action_name == "final":
                raw_paths = action.get("selected_paths", [])
                if not isinstance(raw_paths, list):
                    prompt += "\n[error] selected_paths must be a list"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not raw_paths:
                    prompt += "\n[error] selected_paths must be non-empty"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not all(isinstance(p, str) for p in raw_paths):
                    prompt += "\n[error] every selected_path item must be a string"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if len(raw_paths) != len(set(raw_paths)):
                    prompt += "\n[error] selected_paths must be unique"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not all(p in editable_set for p in raw_paths):
                    bad = [p for p in raw_paths if p not in editable_set]
                    prompt += f"\n[error] paths not in editable universe: {bad}"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                selected_paths = list(raw_paths)
                self._last_requires_iteration = _parse_requires_iteration(action)
                break

            if action_name in ("list_files", "read_file", "search_text"):
                prompt += self._invoke_tool(action_name, action, prompt)
            else:
                prompt += f"\n[error] Unknown action: {action_name}"
                if self._remaining_agent_calls <= 0:
                    break

        delta_prompt = self._prompt_tokens - prompt_tok_before
        delta_completion = self._completion_tokens - completion_tok_before
        delta_total = self._total_tokens - total_tok_before

        if not selected_paths:
            self._last_requires_iteration = False
            return ImpactPrediction(
                token_usage=TokenUsage(
                    prompt_tokens=delta_prompt,
                    completion_tokens=delta_completion,
                    total_tokens=delta_total,
                ),
                errors=("iterative_agent: no paths selected after exploration",),
                decisions=tuple(
                    ImpactDecision(
                        artifact=a,
                        action=ActionKind.preserve,
                        rationale="iterative_agent: no paths selected",
                    )
                    for a in artifact_universe.artifacts
                ),
            )

        selected_set = set(selected_paths)
        decisions: list[ImpactDecision] = []
        for artifact in artifact_universe.artifacts:
            if artifact.path in selected_set:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.regenerate,
                        rationale="iterative_agent: selected by repository exploration",
                        supporting_evidence=(
                            SupportingEvidence(
                                description="Selected through bounded tool exploration",
                                source="iterative_agent_strategy",
                            ),
                        ),
                    )
                )
            else:
                decisions.append(
                    ImpactDecision(
                        artifact=artifact,
                        action=ActionKind.preserve,
                        rationale="iterative_agent: outside selected scope",
                    )
                )
        return ImpactPrediction(
            decisions=tuple(decisions),
            token_usage=TokenUsage(
                prompt_tokens=delta_prompt,
                completion_tokens=delta_completion,
                total_tokens=delta_total,
            ),
        )

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
        *,
        max_completion_tokens_per_call: int = 4096,
        remaining_total_workflow_tokens: int | None = None,
    ) -> ImpactPrediction:
        tools = self._tools
        assert tools is not None, "begin_run() must be called before revise_plan()"
        editable_paths = tuple(a.path for a in artifact_universe.artifacts)
        previous_paths = tuple(
            d.artifact.path for d in previous_prediction.decisions
            if d.action == ActionKind.regenerate
        )
        local_remaining = remaining_total_workflow_tokens
        has_limit = remaining_total_workflow_tokens is not None

        prompt = _build_revise_prompt(
            requirement_change, editable_paths, previous_paths,
            exit_code, val_stdout, val_stderr, self._remaining_agent_calls,
        )
        prompt += f"\nWorkspace summary:\n{workspace_summary[:2000]}"

        editable_set = set(editable_paths)

        prompt_tok_before = self._prompt_tokens
        completion_tok_before = self._completion_tokens
        total_tok_before = self._total_tokens

        while True:
            prompt_estimate = self._backend.count_prompt_tokens(prompt)
            allowance = resolve_completion_allowance(
                max_completion_tokens_per_call=max_completion_tokens_per_call,
                remaining_total_workflow_tokens=local_remaining,
                prompt_tokens=prompt_estimate,
            )
            if allowance <= 0:
                break
            try:
                response = self._generate_agent_response(prompt, allowance)
            except AgentCallsExhaustedError:
                break

            usage = response.token_usage
            if has_limit and local_remaining is not None:
                if usage.completion_tokens > allowance:
                    break
                if local_remaining > 0 and usage.total_tokens > local_remaining:
                    break
                local_remaining = max(0, local_remaining - usage.total_tokens)

            action = _parse_action_response(response.text)
            if action is None:
                prompt += "\n[error] Invalid JSON response"
                if self._remaining_agent_calls <= 0:
                    break
                continue

            action_name = action.get("action", "")
            if action_name == "final":
                raw_paths = action.get("selected_paths", [])
                if not isinstance(raw_paths, list):
                    prompt += "\n[error] selected_paths must be a list"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not raw_paths:
                    prompt += "\n[error] selected_paths must be non-empty"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not all(isinstance(p, str) for p in raw_paths):
                    prompt += "\n[error] every selected_path item must be a string"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if len(raw_paths) != len(set(raw_paths)):
                    prompt += "\n[error] selected_paths must be unique"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                if not all(p in editable_set for p in raw_paths):
                    bad = [p for p in raw_paths if p not in editable_set]
                    prompt += f"\n[error] paths not in editable universe: {bad}"
                    if self._remaining_agent_calls <= 0:
                        break
                    continue
                self._last_requires_iteration = _parse_requires_iteration(action)
                selected_set = set(raw_paths)
                decisions = [
                    ImpactDecision(
                        artifact=a,
                        action=ActionKind.regenerate if a.path in selected_set else ActionKind.preserve,
                        rationale="iterative_agent: revised selection",
                    )
                    for a in artifact_universe.artifacts
                ]
                delta_prompt = self._prompt_tokens - prompt_tok_before
                delta_completion = self._completion_tokens - completion_tok_before
                delta_total = self._total_tokens - total_tok_before
                return ImpactPrediction(
                    decisions=tuple(decisions),
                    token_usage=TokenUsage(
                        prompt_tokens=delta_prompt,
                        completion_tokens=delta_completion,
                        total_tokens=delta_total,
                    ),
                )

            if action_name in ("list_files", "read_file", "search_text"):
                prompt += self._invoke_tool(action_name, action, prompt)
            else:
                prompt += f"\n[error] Unknown action: {action_name}"
                if self._remaining_agent_calls <= 0:
                    break

        self._last_requires_iteration = False
        delta_prompt = self._prompt_tokens - prompt_tok_before
        delta_completion = self._completion_tokens - completion_tok_before
        delta_total = self._total_tokens - total_tok_before
        return ImpactPrediction(
            token_usage=TokenUsage(
                prompt_tokens=delta_prompt,
                completion_tokens=delta_completion,
                total_tokens=delta_total,
            ),
            errors=("iterative_agent: revision failed to select paths",),
            decisions=tuple(
                ImpactDecision(
                    artifact=a,
                    action=ActionKind.preserve,
                    rationale="iterative_agent: revision failed",
                )
                for a in artifact_universe.artifacts
            ),
        )

    def _set_requires_iteration(self, value: bool) -> None:
        self._last_requires_iteration = value

    @property
    def last_requires_iteration(self) -> bool:
        return self._last_requires_iteration

    @property
    def tool_call_count(self) -> int:
        return self._tool_calls

    @property
    def tool_duration_seconds(self) -> float:
        return self._tool_duration

    @property
    def model_call_count(self) -> int:
        return self._model_calls

    @property
    def prompt_tokens(self) -> int:
        return self._prompt_tokens

    @property
    def completion_tokens(self) -> int:
        return self._completion_tokens

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def inspected_file_count(self) -> int:
        return len(self._inspected_files)

    @property
    def remaining_agent_calls(self) -> int:
        return self._remaining_agent_calls

    @property
    def compact_tool_transcript(self) -> tuple[str, ...]:
        return tuple(self._tool_transcript)
