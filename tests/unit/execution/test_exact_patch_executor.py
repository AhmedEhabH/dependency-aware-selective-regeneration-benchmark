from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, LLMResponse, TokenUsage
from benchmark.execution.exact_patch import ExactPatchError, parse_patch_envelope
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import PATCH_MAX_COMPLETION_TOKENS, SharedRegenerationExecutor
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import RegenerationPlan


def _backend_with(text: str):
    class _Mock:
        def __init__(self, text: str):
            self._text = text
            self.prompt_tokens = 0
            self.completion_tokens = 0

        async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
            pt = 20
            ct = max(1, len(self._text) // 4)
            self.prompt_tokens += pt
            self.completion_tokens += ct
            return LLMResponse(
                text=self._text,
                token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
                finish_reason="stop",
            )

    return _Mock(text)


class _StructuredBackend:
    def __init__(self, payload: str, *, finish_reason: str = "stop") -> None:
        self.payload = payload
        self.finish_reason = finish_reason
        self.calls: list[tuple[str, dict, int]] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate_structured(
        self, prompt: str, *, schema_name: str, schema: dict,
        temperature: float = 0.0, max_tokens: int = 4096,
    ) -> LLMResponse:
        self.calls.append((schema_name, schema, max_tokens))
        return LLMResponse(
            text=self.payload,
            token_usage=TokenUsage(20, 10, 30),
            finish_reason=self.finish_reason,
        )


def _make_plan(path: str = "src/main.py") -> RegenerationPlan:
    ref = ArtifactRef(path=path, artifact_type=ArtifactType.source)
    return RegenerationPlan(ordered_artifacts=(ref,), actions={path: ActionKind("regenerate")})


def _make_isolation(tmp_path: Path) -> tuple[IsolationContext, Path, Path]:
    ws_root = tmp_path / "ws"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap = tmp_path / "snapshots"
    snap.mkdir(exist_ok=True)
    iso = IsolationContext(workspace=WorkspacePath(root=str(ws_root)), snapshot_base=snap)
    return iso, ws_root, snap


class TestExactPatchExecutor:

    def test_patch_envelope_schema_is_strict_and_ordered(self) -> None:
        blocks = parse_patch_envelope(
            '{"patches":[{"search":"a = 1\\n","replace":"a = 2\\n"},'
            '{"search":"b = 1\\n","replace":"b = 2\\n"}]}'
        )
        assert [(b.search, b.replace) for b in blocks] == [
            ("a = 1\n", "a = 2\n"),
            ("b = 1\n", "b = 2\n"),
        ]

    def test_patch_envelope_rejects_empty_search_and_trailing_prose(self) -> None:
        with pytest.raises(ExactPatchError, match="search"):
            parse_patch_envelope('{"patches":[{"search":"","replace":"x"}]}')
        with pytest.raises(ExactPatchError, match="JSON"):
            parse_patch_envelope('{"patches":[{"search":"x","replace":"y"}]} prose')

    def test_v11_uses_native_patch_envelope_and_8192_cap(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("value = 1\n", encoding="utf-8", newline="")
        backend = _StructuredBackend(
            '{"patches":[{"search":"value = 1\\n","replace":"value = 2\\n"}]}'
        )

        result = SharedRegenerationExecutor(backend).execute(
            _make_plan(), iso, enable_exact_patch=True,
            protocol_version="scientific-wip-impactplan-v1.1",
        )

        assert result.failures == ()
        assert backend.calls[0][0] == "patch_envelope"
        assert backend.calls[0][2] == PATCH_MAX_COMPLETION_TOKENS == 8192
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "value = 2\n"

    def test_v11_length_finish_is_a_visible_failure_without_cap_raise(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        (ws_root / "src").mkdir()
        original = "value = 1\n"
        (ws_root / "src/main.py").write_text(original, encoding="utf-8", newline="")
        backend = _StructuredBackend('{"patches":[]}', finish_reason="length")

        result = SharedRegenerationExecutor(backend).execute(
            _make_plan(), iso, enable_exact_patch=True,
            protocol_version="scientific-wip-impactplan-v1.1",
        )

        assert any("finish_reason=length" in failure for failure in result.failures)
        assert [call[2] for call in backend.calls] == [8192]
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == original
    def test_modify_target_uses_exact_patch(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("def f():\n    return 1\n", encoding="utf-8", newline="")

        patch = (
            "<<<<<<< SEARCH\n    return 1\n=======\n    return 2\n>>>>>>> REPLACE\n"
        )
        executor = SharedRegenerationExecutor(_backend_with(patch))
        result = executor.execute(_make_plan(), iso, enable_exact_patch=True)

        assert result.artifacts[0].status == "generated"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "def f():\n    return 2\n"

    def test_multi_block_patch_applied_in_order(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("a = 1\nb = 2\n", encoding="utf-8", newline="")

        patch = (
            "<<<<<<< SEARCH\na = 1\n=======\na = 10\n>>>>>>> REPLACE\n"
            "<<<<<<< SEARCH\nb = 2\n=======\nb = 20\n>>>>>>> REPLACE\n"
        )
        executor = SharedRegenerationExecutor(_backend_with(patch))
        result = executor.execute(_make_plan(), iso, enable_exact_patch=True)

        assert result.artifacts[0].status == "generated"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "a = 10\nb = 20\n"

    def test_invalid_patch_fails_closed(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        original = "def f():\n    return 1\n"
        (src / "main.py").write_text(original, encoding="utf-8")

        # SEARCH not found -> fail closed, no file change.
        bad_patch = (
            "<<<<<<< SEARCH\n    return 99\n=======\n    return 2\n>>>>>>> REPLACE\n"
        )
        executor = SharedRegenerationExecutor(_backend_with(bad_patch))
        result = executor.execute(_make_plan(), iso, enable_exact_patch=True)

        assert result.artifacts[0].status == "rejected"
        assert any("exact_patch_failed" in f for f in result.failures)
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == original

    def test_garbage_response_fails_closed(self, tmp_path: Path) -> None:
        iso, ws_root, _ = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        original = "def f():\n    return 1\n"
        (src / "main.py").write_text(original, encoding="utf-8")

        executor = SharedRegenerationExecutor(_backend_with("not a patch at all"))
        result = executor.execute(_make_plan(), iso, enable_exact_patch=True)

        assert result.artifacts[0].status == "rejected"
        assert any("exact_patch_failed" in f for f in result.failures)
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == original
