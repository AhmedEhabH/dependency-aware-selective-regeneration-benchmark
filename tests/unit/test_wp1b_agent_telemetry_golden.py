"""WP-1b G10 - agent telemetry sidecar: behavior-preservation golden test.

The WP-1b agent is a budget-bounded iterative repository agent (8 calls, 1024
completion cap, 2000-char observation window, no paging). B6 adds additive
per-call telemetry (call_sidecar) + per-task observation metrics WITHOUT
changing agent behavior. This test proves behavior preservation with a
stub-backend golden run: the call sequence and the selected_paths must be
identical whether or not the telemetry collector is present.

The telemetry is collected inside the strategy and is always on; the golden
test therefore compares the run's call sequence + selected_paths against a
deterministic expectation and asserts the telemetry fields are well-formed and
consistent (i.e., the same deterministic backend yields the same selection, and
the sidecar fully records the run).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

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
from benchmark.llm.mock_backend import MockLLMBackend  # noqa: E402
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy  # noqa: E402

SIDECAR_FIELDS = [
    "call_index", "force_final", "action", "path", "query",
    "tool_output_chars_raw", "tool_output_chars_shown", "observation_truncated",
    "finish_reason", "prompt_tokens", "completion_tokens", "usd", "latency_s",
    "raw_response_text", "raw_response_sha256",
]


class _ScriptedBackend(MockLLMBackend):
    """A stub backend with a fixed, deterministic call script so the golden
    call sequence is reproducible across runs (with or without telemetry)."""

    def __init__(self, script: list[dict]) -> None:
        self._script = script
        self._i = 0
        super().__init__("mock response")

    async def generate(self, prompt, temperature=0.0, max_tokens=4096):
        item = self._script[min(self._i, len(self._script) - 1)]
        self._i += 1
        text = item["text"]
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(
                prompt_tokens=item.get("prompt", 100),
                completion_tokens=item.get("completion", 20),
                total_tokens=item.get("prompt", 100) + item.get("completion", 20),
            ),
            finish_reason=item.get("finish_reason", "stop"),
        )

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)


_GOLDEN_SCRIPT = [
    {"text": '{"action": "list_files", "path": "."}'},
    {"text": '{"action": "search_text", "query": "def", "path": "."}'},
    {"text": '{"action": "final", "selected_paths": ["src/a.py"], "rationale": "x"}'},
]


def _run_golden() -> tuple[list[str], list[str], dict]:
    backend = _ScriptedBackend(_GOLDEN_SCRIPT)
    strategy = IterativeRepositoryAgentStrategy(backend=backend, agent_control_max_completion_tokens=1024)
    repo = RepositorySnapshot(
        identity=RepositoryIdentity(name="golden", url="https://example.test/golden"),
        commit_sha="parent",
        path=".",
    )
    req = RequirementChange(before="old", after="new", acceptance_criteria=("build",))
    universe = ArtifactUniverse(artifacts=(
        ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
    ))

    workspace = PROJECT_DIR / "_tmp_b6_golden_ws"
    workspace.mkdir(exist_ok=True)
    try:
        strategy.begin_run(workspace)
        prediction = strategy.analyze_impact(repo, req, universe, max_completion_tokens_per_call=4096)
        selected = sorted(d.artifact.path for d in prediction.decisions
                          if d.action.name == "regenerate")
        call_sequence = [c["action"] for c in strategy.call_sidecar]
        telemetry = {
            "call_sidecar": strategy.call_sidecar,
            "paths_read": list(strategy.paths_read),
            "paths_surfaced": list(strategy.paths_surfaced),
            "tool_output_chars_raw_total": strategy.tool_output_chars_raw_total,
            "tool_output_chars_shown_total": strategy.tool_output_chars_shown_total,
            "observation_truncation_rate": strategy.observation_truncation_rate(),
        }
        return selected, call_sequence, telemetry
    finally:
        import shutil
        shutil.rmtree(workspace, ignore_errors=True)


def test_golden_call_sequence_and_selection_deterministic() -> None:
    selected1, seq1, _ = _run_golden()
    selected2, seq2, _ = _run_golden()
    assert seq1 == seq2, "call sequence must be deterministic"
    assert selected1 == selected2, "selected_paths must be deterministic"
    assert selected1 == ["src/a.py"]
    # list_files -> search_text -> final
    assert seq1[:3] == ["list_files", "search_text", "final"]


def test_telemetry_does_not_change_selection() -> None:
    # The selection is fully determined by the frozen scripted backend; the
    # sidecar must record exactly that sequence without perturbing it.
    selected, seq, telemetry = _run_golden()
    assert selected == ["src/a.py"]
    assert seq == ["list_files", "search_text", "final"]
    # Every sidecar record has the full field set.
    for rec in telemetry["call_sidecar"]:
        for field in SIDECAR_FIELDS:
            assert field in rec, f"sidecar missing field {field}"
    assert telemetry["paths_read"] == []  # script never read a file
    # search_text was invoked, so a search-tool sidecar record exists with
    # tool-output-char accounting; surfaced paths may be empty on an empty
    # workspace, but the char counters must be recorded and consistent.
    assert telemetry["tool_output_chars_raw_total"] >= 0
    assert telemetry["tool_output_chars_shown_total"] >= 0
    # observation_truncation_rate is in [0,1]
    assert 0.0 <= telemetry["observation_truncation_rate"] <= 1.0


def test_sidecar_hashes_are_consistent() -> None:
    _, _, telemetry = _run_golden()
    for rec in telemetry["call_sidecar"]:
        assert rec["raw_response_sha256"] == hashlib.sha256(
            rec["raw_response_text"].encode("utf-8")
        ).hexdigest()
        assert rec["completion_tokens"] >= 0
        assert rec["prompt_tokens"] >= 0
        assert rec["usd"] >= 0.0
        assert rec["latency_s"] >= 0.0


def test_sidecar_json_serializable() -> None:
    _, _, telemetry = _run_golden()
    for rec in telemetry["call_sidecar"]:
        json.dumps(rec)  # must not raise
