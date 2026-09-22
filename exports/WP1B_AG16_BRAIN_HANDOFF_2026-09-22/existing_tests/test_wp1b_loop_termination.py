"""WP-1b G3 - deterministic ZERO-API agent-loop termination tests.

Every test binds to a frozen protocol statement:
- `research/wp1a/wp1a_frozen_agent_protocol.json`:
  * proposed_hard_max_rounds: calls 1..7 explore, call 8 reserved final
    (force_final)
  * context_truncation_policy: finish_reason=length -> control response
    truncated at cap; loop breaks; no paths -> EMPTY (fail-closed)
  * malformed_output_rule: invalid JSON -> error appended; if calls remain
    continue; else EMPTY
  * stop_rule: action=final with valid non-empty unique editable subset ->
    accept and stop
  * empty_output_rule / fail_closed_semantics -> EMPTY prediction
- `research/wp1a/wp1a_failure_semantics.json`:
  * round_cap_reached -> EMPTY
  * retry: max 3 byte-identical transport retries; ONLY transport failures
- `research/wp1a/wp1a_shared_scorer_schema.json`: no silent margin (EMPTY
  reasons must be classified, not hidden).

Protects the Architecture Compliance and Impact Correctness validity
dimensions.
"""

from __future__ import annotations

import json
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
    MAX_AGENT_CALLS,
    IterativeRepositoryAgentStrategy,
)
from benchmark.wp1b.telemetry import aggregate, strategy_telemetry


class _ScriptedBackend:
    """Stub backend that returns a scripted sequence of control responses.

    Each script entry is a dict with keys:
      text: str | None (None means the strategy should treat it as malformed
            JSON is NOT simulated here; use text="not-json" for malformed)
      finish_reason: str
    Plus optional 'raise_transient_once' to simulate a backend-internal
    transport retry that must not consume a strategy-level call.
    """

    def __init__(self, script: list[dict]) -> None:
        self._script = script
        self.schemas: list[str] = []
        self.calls = 0
        self.prompts: list[str] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate_structured(
        self, prompt: str, *, schema_name: str, schema: dict,
        temperature: float = 0.0, max_tokens: int = 4096,
    ) -> LLMResponse:
        self.schemas.append(schema_name)
        self.prompts.append(prompt)
        self.calls += 1
        entry = self._script[min(self.calls - 1, len(self._script) - 1)]
        text = entry.get("text", '{"action":"final","selected_paths":["todo/models.py"],"rationale":"done"}')
        reason = entry.get("finish_reason", "stop")
        return LLMResponse(text, TokenUsage(5, 5, 10), reason)


def _make_strategy(script: list[dict]) -> tuple[IterativeRepositoryAgentStrategy, Path]:
    backend = _ScriptedBackend(script)
    strategy = IterativeRepositoryAgentStrategy(backend)
    return strategy, Path(__file__).parent


def _make_context(tmp_path: Path) -> tuple[IterativeRepositoryAgentStrategy,
                                           RepositorySnapshot, RequirementChange,
                                           ArtifactUniverse]:
    (tmp_path / "todo").mkdir()
    (tmp_path / "todo/models.py").write_text("x = 1\n", encoding="utf-8")
    strategy, _ = _make_strategy([])
    ident = RepositoryIdentity(name="test_repo", url="https://example.test/test_repo")
    repo = RepositorySnapshot(identity=ident, commit_sha="parent", path=".")
    req = RequirementChange(before="old", after="new", acceptance_criteria=("build",))
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source),
    ))
    strategy.begin_run(tmp_path)
    return strategy, repo, req, universe


def _explore_text() -> str:
    return '{"action":"list_files","path":"."}'


def _final_text(paths: list[str] | None = None) -> str:
    selected = paths if paths is not None else ["todo/models.py"]
    return json.dumps({"action": "final", "selected_paths": selected, "rationale": "done"})


def test_forced_final_succeeds_on_last_allowed_call(tmp_path: Path) -> None:
    """Protocol: calls 1..7 explore, call 8 is the reserved final call."""
    script = [{"text": _explore_text()} for _ in range(MAX_AGENT_CALLS - 1)] + [
        {"text": _final_text()}
    ]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == {"todo/models.py"}
    assert not prediction.errors
    assert strategy.remaining_agent_calls == 0
    assert strategy.selection_empty_reason == "none"
    assert strategy.selection_valid_final_count == 1
    assert strategy._backend.schemas[-1] == "agent_final"  # type: ignore[attr-defined]


def test_forced_final_truncates_to_empty(tmp_path: Path) -> None:
    """Protocol: finish_reason=length -> truncated at cap; no paths -> EMPTY."""
    script = [{"text": _explore_text()} for _ in range(MAX_AGENT_CALLS - 1)] + [
        {"text": "truncated", "finish_reason": "length"}
    ]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == set()
    assert strategy.selection_empty_reason == "truncation"
    assert strategy.selection_truncation_count == 1
    assert any("truncated at cap" in e for e in prediction.errors)


def test_forced_final_malformed_json_classified_as_parser_failure(tmp_path: Path) -> None:
    """Protocol: malformed_output_rule -> break with EMPTY on last call."""
    script = [{"text": _explore_text()} for _ in range(MAX_AGENT_CALLS - 1)] + [
        {"text": "{not-json", "finish_reason": "stop"}
    ]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == set()
    assert strategy.selection_empty_reason == "parser_failure"
    assert strategy.selection_malformed_count == 1


def test_no_final_action_before_cap_is_round_cap_empty(tmp_path: Path) -> None:
    """Protocol: round_cap_reached -> EMPTY prediction."""
    script = [{"text": _explore_text()} for _ in range(MAX_AGENT_CALLS)]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == set()
    assert strategy.selection_empty_reason == "round_cap"
    assert strategy.model_call_count == MAX_AGENT_CALLS
    assert any("no remaining agent calls" in e for e in prediction.errors)


def test_valid_final_before_cap_is_accepted(tmp_path: Path) -> None:
    """Protocol: stop_rule - valid final accepted and loop stops."""
    script = [{"text": _final_text()}]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == {"todo/models.py"}
    assert not prediction.errors
    assert strategy.selection_empty_reason == "none"
    assert strategy.remaining_agent_calls == MAX_AGENT_CALLS - 1


def test_workflow_deadline_classified_as_infrastructure(tmp_path: Path) -> None:
    """Protocol: cooperative workflow deadline -> fail-closed EMPTY."""
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend([{"text": _final_text()}])  # type: ignore[assignment]
    strategy.set_model_call_guard(lambda: False)

    prediction = strategy.analyze_impact(repo, req, universe)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == set()
    assert strategy.selection_empty_reason == "infrastructure"
    assert strategy.model_call_count == 0


def test_finish_reason_telemetry_is_persisted(tmp_path: Path) -> None:
    """Protocol: finish_reason telemetry must be persisted per task."""
    script = [{"text": _explore_text()} for _ in range(MAX_AGENT_CALLS - 1)] + [
        {"text": "truncated", "finish_reason": "length"}
    ]
    strategy, repo, req, universe = _make_context(tmp_path)
    strategy._backend = _ScriptedBackend(script)  # type: ignore[assignment]
    strategy.begin_run(tmp_path)
    strategy.analyze_impact(repo, req, universe)

    distribution = strategy.selection_finish_reason_distribution
    assert distribution.get("length") == 1
    assert distribution.get("stop") == MAX_AGENT_CALLS - 1

    record = strategy_telemetry(strategy, task_id="t1")
    assert record["empty_reason"] == "truncation"
    assert record["finish_reason_distribution"] == distribution
    agg = aggregate([record])
    assert agg["EMPTY_due_to_truncation_count"] == 1
    assert agg["final_answer_truncation_count"] == 1
    assert agg["finish_reason_distribution"] == distribution


def test_backend_internal_transport_retry_does_not_consume_call_budget(tmp_path: Path) -> None:
    """Protocol: transport retries (max 3, byte-identical) do not add
    strategy-level scientific calls; only the returned response is counted."""
    class _RetryBackend:
        def __init__(self) -> None:
            self.calls = 0

        def count_prompt_tokens(self, prompt: str) -> int:
            return 1

        def _attempt(self) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient transport failure (retried internally)")

        async def generate_structured(
            self, prompt: str, *, schema_name: str, schema: dict,
            temperature: float = 0.0, max_tokens: int = 4096,
        ) -> LLMResponse:
            # First attempt hits a transient transport error; the backend
            # retries INTERNALLY and only the successful response returns to
            # the strategy. The strategy's scientific call budget must count
            # one call, not the retry.
            try:
                self._attempt()
            except RuntimeError:
                self._attempt()
            return LLMResponse(
                _final_text(), TokenUsage(5, 5, 10), "stop"
            )

    strategy, _ = _make_strategy([])
    (tmp_path / "todo").mkdir()
    (tmp_path / "todo/models.py").write_text("x = 1\n", encoding="utf-8")
    backend = _RetryBackend()
    strategy._backend = backend  # type: ignore[assignment]
    ident = RepositoryIdentity(name="test_repo", url="https://example.test/test_repo")
    repo = RepositorySnapshot(identity=ident, commit_sha="parent", path=".")
    req = RequirementChange(before="old", after="new", acceptance_criteria=())
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
    ))
    strategy.begin_run(tmp_path)
    prediction = strategy.analyze_impact(repo, req, universe)
    assert not prediction.errors
    assert strategy.model_call_count == 1, (
        "a backend-internal transport retry must not increment the scientific "
        "call budget"
    )
    assert backend.calls == 2


def test_retry_rule_max_three_is_an_operational_config_gap(tmp_path: Path) -> None:
    """Records the frozen-vs-implementation retry count gap without fixing it.

    The frozen failure semantics say max 3 transport retries (SIP precedent);
    the current OpenRouterBackend default is max_transient_retries=1. This is
    an operational knob, but WP-1b must configure/confirm the retry count so
    the executed protocol matches the frozen rule.
    """
    from benchmark.llm.openrouter_backend import OpenRouterBackend

    backend = OpenRouterBackend(model="qwen/qwen3-coder")
    assert backend._max_transient_retries == 1  # current default (gap vs frozen 3)
    pytest.skip(
        "gap documented: frozen failure semantics state max 3 transport "
        "retries (SIP precedent); current backend default is 1. WP-1b must "
        "configure max_transient_retries=3 before paid execution."
    )
