from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    LLMResponse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    TokenUsage,
)
from benchmark.strategies.iterative_agent import (
    AGENT_CONTROL_MAX_COMPLETION_TOKENS,
    IterativeRepositoryAgentStrategy,
)


class _RecordingBackend:
    """Mock backend that records the max_tokens of every control-plane call."""

    def __init__(self, final_action: str):
        self._final_action = final_action
        self.requested_max_tokens: list[int] = []
        self._call = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.requested_max_tokens.append(max_tokens)
        if self._final_action == "final":
            body = (
                '{"action": "final", "selected_paths": ["todo/models.py"], '
                '"rationale": "model change"}'
            )
        else:
            body = '{"action": "final", "selected_paths": ["todo/models.py"], "rationale": "done"}'
        self._call += 1
        return LLMResponse(
            text=body,
            token_usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
            finish_reason="stop",
        )


def _make_universe() -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=(ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),),
    )


def _make_change() -> RequirementChange:
    return RequirementChange(
        before="no priority field",
        after="add priority field",
    )


def _make_repo() -> RepositorySnapshot:
    return RepositorySnapshot(
        identity=RepositoryIdentity(name="todo", url="https://example.invalid/todo"),
        commit_sha="aaaaaaaa",
        path=str(Path(__file__).parent),
    )


class TestAgentControlPlaneCap:
    def test_control_plane_requests_never_exceed_cap(self) -> None:
        backend = _RecordingBackend(final_action="final")
        strategy = IterativeRepositoryAgentStrategy(backend)
        tmp = Path(__file__).parent
        strategy.begin_run(tmp)
        backend.requested_max_tokens.clear()

        strategy.analyze_impact(
            repository=_make_repo(),
            requirement_change=_make_change(),
            artifact_universe=_make_universe(),
            max_completion_tokens_per_call=4096,
            remaining_total_workflow_tokens=None,
        )

        assert backend.requested_max_tokens, "expected at least one agent call"
        for requested in backend.requested_max_tokens:
            assert requested <= AGENT_CONTROL_MAX_COMPLETION_TOKENS, (
                f"control-plane call requested {requested} completion tokens, "
                f"over the {AGENT_CONTROL_MAX_COMPLETION_TOKENS} cap"
            )

    def test_control_cap_takes_precedence_over_full_edit_cap(self) -> None:
        """The source-edit cap may be 4096, but control-plane calls stay <= 512."""
        assert AGENT_CONTROL_MAX_COMPLETION_TOKENS < 4096
        backend = _RecordingBackend(final_action="final")
        strategy = IterativeRepositoryAgentStrategy(backend)
        tmp = Path(__file__).parent
        strategy.begin_run(tmp)
        backend.requested_max_tokens.clear()

        strategy.analyze_impact(
            repository=_make_repo(),
            requirement_change=_make_change(),
            artifact_universe=_make_universe(),
            max_completion_tokens_per_call=4096,
            remaining_total_workflow_tokens=None,
        )
        assert all(m <= AGENT_CONTROL_MAX_COMPLETION_TOKENS for m in backend.requested_max_tokens)

    def test_constructor_rejects_non_positive_cap(self) -> None:
        backend = _RecordingBackend(final_action="final")
        with pytest.raises(ValueError):
            IterativeRepositoryAgentStrategy(
                backend, agent_control_max_completion_tokens=0
            )
        with pytest.raises(ValueError):
            IterativeRepositoryAgentStrategy(
                backend, agent_control_max_completion_tokens=-5
            )

    def test_custom_cap_is_honored_and_precedes_source_edit_cap(self) -> None:
        custom_cap = 256
        assert custom_cap < AGENT_CONTROL_MAX_COMPLETION_TOKENS
        backend = _RecordingBackend(final_action="final")
        strategy = IterativeRepositoryAgentStrategy(
            backend, agent_control_max_completion_tokens=custom_cap
        )
        tmp = Path(__file__).parent
        strategy.begin_run(tmp)
        backend.requested_max_tokens.clear()

        strategy.analyze_impact(
            repository=_make_repo(),
            requirement_change=_make_change(),
            artifact_universe=_make_universe(),
            max_completion_tokens_per_call=4096,
            remaining_total_workflow_tokens=None,
        )
        assert backend.requested_max_tokens
        assert all(m <= custom_cap for m in backend.requested_max_tokens)


class TestAgentControlConfig:
    def test_pipeline_config_default_and_validation(self) -> None:
        from benchmark.execution.pipeline import PipelineConfig

        assert PipelineConfig(protocol_version="1.2").agent_control_max_completion_tokens == 512
        assert (
            PipelineConfig(
                protocol_version="1.2", agent_control_max_completion_tokens=256
            ).agent_control_max_completion_tokens
            == 256
        )
        with pytest.raises(ValueError):
            PipelineConfig(protocol_version="1.2", agent_control_max_completion_tokens=0)
        with pytest.raises(ValueError):
            PipelineConfig(protocol_version="1.2", agent_control_max_completion_tokens=True)

    def test_runner_config_default_and_validation(self) -> None:
        from benchmark.execution.runner import RunnerConfig

        base = dict(
            strategy_name="iterative_repository_agent",
            backend_name="qwen",
            protocol_version="1.2",
        )
        assert RunnerConfig(**base).agent_control_max_completion_tokens == 512
        assert (
            RunnerConfig(**base, agent_control_max_completion_tokens=128)
            .agent_control_max_completion_tokens
            == 128
        )
        with pytest.raises(ValueError):
            RunnerConfig(**base, agent_control_max_completion_tokens=-1)
        with pytest.raises(ValueError):
            RunnerConfig(**base, agent_control_max_completion_tokens=True)
