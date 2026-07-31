"""Deterministic scripted LLM backend for the R5 nine-record production-path smoke.

Engineering-only scripted orchestration proof. The scripted token magnitudes are
engineering metrics and do not predict Qwen cost. This module is test-only and is
never exposed through production provider factories or Kaggle choices.

The backend inspects prompts only to identify the public requirement text, the
requested artifact path, and the Agent action stage. It never reads Ground Truth,
evaluator assets, scenario.expected_affected_artifacts, or production strategy
internals. It never chooses scope for Monolithic or Selective.
"""

from __future__ import annotations

import enum
import json
from pathlib import Path
from typing import Any

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage
from tests.support.evaluator_fixture_workspaces import get_correct_sources_for_scenario

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BASELINE_TODO_REPO = _PROJECT_ROOT / "benchmark_data" / "repositories" / "todo"

SMOKE_V2_EDITABLE_PATHS: tuple[str, ...] = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

# Fixed Agent final-selection mapping keyed only by public scenario identity.
# This is a scripted orchestration proof, not model reasoning evidence.
_SMOKE_V2_AGENT_FINAL_PATHS: dict[str, tuple[str, ...]] = {
    "todo-smoke-001": ("todo/models.py", "todo/serializers.py", "todo/views.py"),
    "todo-smoke-002": ("todo/models.py", "todo/views.py"),
    "todo-smoke-003": (
        "todo/models.py",
        "todo/serializers.py",
        "todo/permissions.py",
        "todo/views.py",
    ),
}

_SMOKE_V2_SEARCH_QUERY: dict[str, str] = {
    "todo-smoke-001": "priority",
    "todo-smoke-002": "deleted_at",
    "todo-smoke-003": "owner",
}

# Unique public-requirement markers, checked in scenario order. Each marker set
# only matches requirement text of its own scenario across the three frozen YAMLs.
_SCENARIO_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("todo-smoke-001", ("priority", "Priority")),
    ("todo-smoke-002", ("deleted_at", "soft deletion")),
    ("todo-smoke-003", ("authorization", "Project ownership", "Unauthorized")),
)


class ScriptedSmokeV2Mode(enum.Enum):
    MONOLITHIC = "monolithic"
    SELECTIVE = "selective"
    AGENT = "iterative_repository_agent"


def deterministic_token_count(text: str) -> int:
    """Deterministic engineering-only token estimate.

    Positive for every input, including the empty string.
    """
    return max(1, (len(text) + 3) // 4)


def classify_scenario_id(prompt: str) -> str:
    """Classify the frozen scenario from public requirement text only."""
    for scenario_id, markers in _SCENARIO_MARKERS:
        if any(marker in prompt for marker in markers):
            return scenario_id
    return ""


def extract_artifact_path_from_generation_prompt(prompt: str) -> str:
    """Extract the requested artifact path from a regeneration prompt."""
    marker = "Artifact path: "
    start = prompt.find(marker)
    if start < 0:
        return ""
    line = prompt[start + len(marker):].split("\n", 1)[0]
    return line.strip()


def _is_agent_initial_prompt(prompt: str) -> bool:
    return "You are analyzing a code repository" in prompt


def _is_agent_revise_prompt(prompt: str) -> bool:
    return "You previously selected files for modification" in prompt


def _is_agent_prompt(prompt: str) -> bool:
    return _is_agent_initial_prompt(prompt) or _is_agent_revise_prompt(prompt)


def _baseline_content(path: str, baseline_repo: Path) -> str:
    candidate = baseline_repo / path
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")
    return ""


class ScriptedSmokeV2Backend:
    """Deterministic backend satisfying the real LLMBackend protocol."""

    token_accounting_mode = "fixture_or_approximate"

    def __init__(
        self,
        mode: ScriptedSmokeV2Mode = ScriptedSmokeV2Mode.MONOLITHIC,
        *,
        baseline_repo: Path | None = None,
        fail_mode: str = "none",
        search_query_override: str | None = None,
        final_paths_override: tuple[str, ...] | None = None,
    ) -> None:
        if not isinstance(mode, ScriptedSmokeV2Mode):
            raise ValueError(f"mode must be a ScriptedSmokeV2Mode, got {mode!r}")
        self._mode = mode
        self._baseline_repo = baseline_repo or _BASELINE_TODO_REPO
        self._fail_mode = fail_mode
        self._search_query_override = search_query_override
        self._final_paths_override = final_paths_override
        self.reset()

    def reset(self) -> None:
        """Reset all per-run state so no state leaks between records."""
        self._call_count = 0
        self._generation_calls = 0
        self._captured_max_tokens: list[int] = []
        self._captured_prompts: list[str] = []
        self._generation_paths_requested: list[str] = []
        self._agent_actions_returned: list[dict[str, Any]] = []
        self._agent_stage = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        return deterministic_token_count(prompt)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 1:
            raise ValueError(f"max_tokens must be a positive integer, got {max_tokens!r}")
        self._call_count += 1
        self._captured_max_tokens.append(max_tokens)
        self._captured_prompts.append(prompt)

        if self._fail_mode == "zero_calls":
            raise ModelBackendError(
                message="scripted backend: zero generation calls",
                context={"call_count": self._call_count},
            )

        prompt_tokens = self.count_prompt_tokens(prompt)

        if self._mode is ScriptedSmokeV2Mode.AGENT and _is_agent_prompt(prompt):
            return self._agent_response(prompt, max_tokens, prompt_tokens)

        return self._generation_response(prompt, max_tokens, prompt_tokens)

    def _generation_response(
        self, prompt: str, max_tokens: int, prompt_tokens: int
    ) -> LLMResponse:
        self._generation_calls += 1
        artifact_path = extract_artifact_path_from_generation_prompt(prompt)
        self._generation_paths_requested.append(artifact_path)
        content = self._resolve_generation_content(prompt, artifact_path)
        return self._make_response(content, prompt_tokens, max_tokens)

    def _resolve_generation_content(self, prompt: str, artifact_path: str) -> str:
        if self._fail_mode == "empty_source":
            return ""
        scenario_id = classify_scenario_id(prompt)
        if scenario_id:
            correct = get_correct_sources_for_scenario(scenario_id)
            if artifact_path in correct:
                return correct[artifact_path]
        return _baseline_content(artifact_path, self._baseline_repo)

    def _agent_response(
        self, prompt: str, max_tokens: int, prompt_tokens: int
    ) -> LLMResponse:
        action = self._final_action(prompt) if _is_agent_revise_prompt(prompt) else self._next_agent_action(prompt)
        self._agent_actions_returned.append(action)
        return self._make_response(json.dumps(action), prompt_tokens, max_tokens)

    def _next_agent_action(self, prompt: str) -> dict[str, Any]:
        scenario_id = classify_scenario_id(prompt)
        steps: list[dict[str, Any]] = [
            {"action": "list_files", "path": "."},
            {
                "action": "search_text",
                "query": self._search_query_override or _SMOKE_V2_SEARCH_QUERY.get(scenario_id, ""),
                "path": ".",
            },
            {"action": "read_file", "path": "todo/models.py"},
        ]
        if self._agent_stage < len(steps):
            action = steps[self._agent_stage]
            self._agent_stage += 1
            return action
        self._agent_stage += 1
        return self._final_action(prompt)

    def _final_action(self, prompt: str) -> dict[str, Any]:
        scenario_id = classify_scenario_id(prompt)
        paths = self._final_paths_override or _SMOKE_V2_AGENT_FINAL_PATHS.get(scenario_id, ())
        return {
            "action": "final",
            "selected_paths": list(paths),
            "rationale": "scripted orchestration proof: fixed scenario-scoped mapping",
            "requires_iteration": False,
        }

    def _make_response(self, text: str, prompt_tokens: int, max_tokens: int) -> LLMResponse:
        completion = min(max_tokens, deterministic_token_count(text))
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion,
            total_tokens=prompt_tokens + completion,
        )
        return LLMResponse(text=text, token_usage=usage, finish_reason="stop")

    @property
    def mode(self) -> ScriptedSmokeV2Mode:
        return self._mode

    @property
    def fail_mode(self) -> str:
        return self._fail_mode

    @property
    def generate_call_count(self) -> int:
        return self._call_count

    @property
    def generation_call_count(self) -> int:
        return self._generation_calls

    @property
    def captured_max_tokens(self) -> list[int]:
        return list(self._captured_max_tokens)

    @property
    def captured_prompts(self) -> list[str]:
        return list(self._captured_prompts)

    @property
    def generation_paths_requested(self) -> list[str]:
        return list(self._generation_paths_requested)

    @property
    def agent_actions_returned(self) -> list[dict[str, Any]]:
        return [dict(a) for a in self._agent_actions_returned]
