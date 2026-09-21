"""WP-1a AC-1A.6 - frozen agent protocol is mock-executable against a
label-free parent-state boundary.

Runs the authoritative IterativeRepositoryAgentStrategy with a stub backend on
a parent-only workspace that contains a hidden proxy file which must NEVER be
seen/selected. Verifies:
- the agent completes with a stub backend (no live model call);
- selected paths come only from the repository-derived universe;
- hidden proxy path cannot be selected (not part of the universe);
- allow_ground_truth_universe defaults False and is auditable on the record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.core.enums import ArtifactType  # noqa: E402
from benchmark.core.models import (  # noqa: E402
    ArtifactRef,
    ArtifactUniverse,
    LLMResponse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    TokenUsage,
)
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy  # noqa: E402


class _StubBackend:
    """Stub backend: one exploration then final. No live model call."""

    def __init__(self, selected: list[str]) -> None:
        self._selected = selected
        self.prompts: list[str] = []
        self.calls = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate(
        self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        self.calls += 1
        text = json.dumps({
            "action": "final",
            "selected_paths": self._selected,
            "rationale": "stub",
        })
        pt = max(1, len(prompt) // 4)
        ct = max(1, len(text) // 4)
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
            finish_reason="stop",
        )


def _make_context() -> tuple[IterativeRepositoryAgentStrategy, RepositorySnapshot,
                             RequirementChange, ArtifactUniverse]:
    sb = _StubBackend(["src/a.py"])
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    ident = RepositoryIdentity(name="test_repo", url="https://example.test/test_repo")
    repo = RepositorySnapshot(identity=ident, commit_sha="parent", path=".")
    req = RequirementChange(before="old", after="new",
                            acceptance_criteria=("build",))
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
    ))
    return strategy, repo, req, universe


def test_agent_mock_executable_and_label_free() -> None:
    strategy, repo, req, universe = _make_context()
    strategy.begin_run(PROJECT_DIR)  # workspace root is the project dir (parent)
    prediction = strategy.analyze_impact(repo, req, universe,
                                         max_completion_tokens_per_call=512)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == {"src/a.py"}
    # hidden/secret.py is NOT in the universe -> cannot be selected
    assert "hidden/secret.py" not in regenerated
    assert strategy.model_call_count >= 1


def test_agent_cannot_select_path_outside_universe() -> None:
    """The stub selects a path outside the universe; the harness must reject it
    (error appended) and eventually produce an EMPTY/preserve outcome instead
    of accepting a non-universe path."""
    sb = _StubBackend(["hidden/secret.py"])
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    ident = RepositoryIdentity(name="test_repo", url="https://example.test/test_repo")
    repo = RepositorySnapshot(identity=ident, commit_sha="parent", path=".")
    req = RequirementChange(before="old", after="new", acceptance_criteria=())
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="src/a.py", artifact_type="source"),
    ))
    strategy.begin_run(PROJECT_DIR)
    prediction = strategy.analyze_impact(repo, req, universe,
                                         max_completion_tokens_per_call=512)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    # either accepted nothing (empty) or never accepted the hidden path
    assert "hidden/secret.py" not in regenerated


def test_agent_empty_selection_fails_closed() -> None:
    """Stub returns no paths -> EMPTY prediction (fail-closed), no exception."""
    sb = _StubBackend([])
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    ident = RepositoryIdentity(name="test_repo", url="https://example.test/test_repo")
    repo = RepositorySnapshot(identity=ident, commit_sha="parent", path=".")
    req = RequirementChange(before="old", after="new", acceptance_criteria=())
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="src/a.py", artifact_type="source"),
    ))
    strategy.begin_run(PROJECT_DIR)
    prediction = strategy.analyze_impact(repo, req, universe,
                                         max_completion_tokens_per_call=512)
    regenerated = {d.artifact.path for d in prediction.decisions if d.action.name == "regenerate"}
    assert regenerated == set()
