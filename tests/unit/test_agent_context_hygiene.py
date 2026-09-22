"""WP-1b G12 - agent context hygiene (RED/GREEN tests).

Amendment WP1B_G12_AGENT_CONTEXT_HYGIENE_2026_09_22 (D1 APPROVED). The four
changes to the selection loop of iterative_agent.py:

1. Action echo prepended to every tool result:
   `[call {k}/8] you requested: {action} path="{path}" query="{query}"`
   (empty fields omitted).
2. Call counter appended before every non-final call:
   `[control] Call {k} of 8. Calls left before the forced final: {8-k}.`
   Per Ahmed's clarification, early `action=final` availability is already
   visible in the frozen schema, so the counter does NOT repeat it.
3. Named rejection: the rejection warning names the exact repeated request.
4. Truncation note when a tool output exceeds the 2000-char observation
   window.

All four assertions must FAIL on the pre-G12 code (RED) and PASS on the
post-G12 code (GREEN).
"""

from __future__ import annotations

from pathlib import Path

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
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy


class _ScriptedBackend:
    """Stub backend returning a fixed JSON response per call and recording prompts."""

    def __init__(self, script: list[str]) -> None:
        self._script = script
        self._i = 0
        self.prompts: list[str] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate(
        self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096
    ) -> LLMResponse:
        self.prompts.append(prompt)
        text = self._script[min(self._i, len(self._script) - 1)]
        self._i += 1
        prompt_tok = max(1, len(prompt) // 4)
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tok,
                completion_tokens=10,
                total_tokens=prompt_tok + 10,
            ),
            finish_reason="stop",
        )


def _run(
    workspace: Path, script: list[str], paths: tuple[str, ...]
) -> tuple[IterativeRepositoryAgentStrategy, _ScriptedBackend]:
    backend = _ScriptedBackend(script)
    strategy = IterativeRepositoryAgentStrategy(backend=backend, agent_control_max_completion_tokens=1024)
    repo = RepositorySnapshot(
        identity=RepositoryIdentity(name="test_repo", url="https://example.test/test_repo"),
        commit_sha="parent",
        path=".",
    )
    req = RequirementChange(before="old", after="new", acceptance_criteria=())
    universe = ArtifactUniverse(
        artifacts=tuple(ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in paths)
    )
    strategy.begin_run(workspace)
    strategy.analyze_impact(repo, req, universe)
    return strategy, backend


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "src").mkdir(exist_ok=True)
    (ws / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (ws / "src" / "b.py").write_text("y = 2\n", encoding="utf-8")
    big = "line of content\n" * 300  # ~4500 chars
    (ws / "src" / "big.py").write_text(big, encoding="utf-8")
    return ws


def test_action_echo_in_next_prompt(tmp_path: Path) -> None:
    """After a tool call, the next prompt contains the echo line of that request."""
    ws = _workspace(tmp_path)
    script = [
        '{"action": "read_file", "path": "src/a.py"}',
        '{"action": "final", "selected_paths": ["src/a.py"], "rationale": "x"}',
    ]
    _, backend = _run(ws, script, ("src/a.py", "src/b.py"))
    assert len(backend.prompts) >= 2
    next_prompt = backend.prompts[1]
    assert '[call 1/8] you requested: read_file path="src/a.py"' in next_prompt


def test_call_counter_in_every_non_final_prompt(tmp_path: Path) -> None:
    """Every non-final prompt contains the call counter."""
    ws = _workspace(tmp_path)
    script = [
        '{"action": "read_file", "path": "src/a.py"}',
        '{"action": "read_file", "path": "src/b.py"}',
        '{"action": "final", "selected_paths": ["src/a.py", "src/b.py"], "rationale": "x"}',
    ]
    _, backend = _run(ws, script, ("src/a.py", "src/b.py"))
    assert len(backend.prompts) >= 3
    assert "[control] Call 1 of 8. Calls left before the forced final: 7." in backend.prompts[0]
    assert "[control] Call 2 of 8. Calls left before the forced final: 6." in backend.prompts[1]
    assert "[control] Call 3 of 8. Calls left before the forced final: 5." in backend.prompts[2]


def test_named_rejection_for_repeated_request(tmp_path: Path) -> None:
    """A rejected repeat produces the named-rejection text (exact repeated request)."""
    ws = _workspace(tmp_path)
    script = [
        '{"action": "read_file", "path": "src/a.py"}',
        '{"action": "read_file", "path": "src/a.py"}',
        '{"action": "final", "selected_paths": ["src/a.py"], "rationale": "x"}',
    ]
    _, backend = _run(ws, script, ("src/a.py", "src/b.py"))
    assert len(backend.prompts) >= 3
    prompt_after_repeat = backend.prompts[2]
    assert (
        '[control warning] Rejected: identical to your previous request '
        '(read_file path="src/a.py").'
    ) in prompt_after_repeat


def test_truncation_note_for_long_read(tmp_path: Path) -> None:
    """A read longer than 2000 chars produces the truncation note."""
    ws = _workspace(tmp_path)
    big_text = (ws / "src" / "big.py").read_text(encoding="utf-8")
    big_size = len(big_text)
    assert big_size > 2000
    script = [
        '{"action": "read_file", "path": "src/big.py"}',
        '{"action": "final", "selected_paths": ["src/big.py"], "rationale": "x"}',
    ]
    _, backend = _run(ws, script, ("src/big.py", "src/b.py"))
    assert len(backend.prompts) >= 2
    prompt_after_read = backend.prompts[1]
    assert (
        f"[note] Output truncated: showing the first 2000 of {big_size} characters."
        in prompt_after_read
    )
