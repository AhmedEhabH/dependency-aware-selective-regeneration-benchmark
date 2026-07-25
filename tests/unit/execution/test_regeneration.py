from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, LLMResponse, TokenUsage
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import SharedRegenerationExecutor
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import RegenerationPlan


def _make_backend(response_text: str = "replacement content"):
    class _Mock:
        def __init__(self, text: str):
            self._text = text

        async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
            pt = max(1, len(prompt) // 4)
            ct = max(1, len(self._text) // 4)
            return LLMResponse(
                text=self._text,
                token_usage=TokenUsage(
                    prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
                ),
                finish_reason="stop",
            )

    return _Mock(response_text)


def _make_plan(*, action: str = "regenerate") -> RegenerationPlan:
    ref = ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source)
    return RegenerationPlan(
        ordered_artifacts=(ref,),
        actions={"src/main.py": ActionKind(action)},
    )


def _make_isolation(tmp_path: Path, workspace_subdir: str = "ws") -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / workspace_subdir
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
    return iso, ws_root


class TestSharedRegenerationExecutor:
    def test_mock_backend_produces_replacement_content(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original content", encoding="utf-8")

        backend = _make_backend("replacement content")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "generated"
        assert result.artifacts[0].content == "replacement content"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "replacement content"

    def test_empty_generation_is_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original content", encoding="utf-8")

        backend = _make_backend("  ")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.failures) == 1
        assert "Empty generation" in result.failures[0]
        assert result.artifacts[0].status == "rejected"

    def test_malformed_response_is_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original", encoding="utf-8")

        backend = _make_backend("")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.failures) >= 1
        assert result.artifacts[0].status == "rejected"

    def test_path_traversal_is_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        evil_ref = ArtifactRef(path="../../etc/passwd", artifact_type=ArtifactType.configuration)
        plan = RegenerationPlan(
            ordered_artifacts=(evil_ref,),
            actions={"../../etc/passwd": ActionKind.regenerate},
        )
        backend = _make_backend("evil content")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(plan, iso)

        assert len(result.failures) == 1
        assert "Path traversal" in result.failures[0]
        assert result.artifacts[0].status == "rejected"

    def test_isolated_workspace_file_changes(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original", encoding="utf-8")

        backend = _make_backend("new content")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        executor.execute(plan, iso)

        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "new content"

    def test_canonical_source_remains_unchanged(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        orig = "original source content"
        (src / "main.py").write_text(orig, encoding="utf-8")

        canonical_backup = Path(tmp_path / "canonical_backup")
        canonical_backup.mkdir()
        (canonical_backup / "main.py").write_text(orig, encoding="utf-8")

        backend = _make_backend("replacement content")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        executor.execute(plan, iso)

        assert (canonical_backup / "main.py").read_text(encoding="utf-8") == orig

    def test_regeneration_token_accounting(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "main.py").write_text("original", encoding="utf-8")

        backend = _make_backend("replacement content")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert result.prompt_tokens > 0
        assert result.completion_tokens > 0
        assert result.total_tokens > 0
        assert result.model_calls == 1

    def test_human_review_artifact_is_skipped(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        ref = ArtifactRef(path="src/review.py", artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"src/review.py": ActionKind.human_review},
        )
        backend = _make_backend("should not be called")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(plan, iso)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "skipped"
        assert result.model_calls == 0

    def test_preserve_artifact_is_not_executed(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        ref = ArtifactRef(path="src/preserved.py", artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"src/preserved.py": ActionKind.preserve},
        )
        backend = _make_backend("should not be called")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(plan, iso)

        assert result.model_calls == 0

    def test_missing_source_file_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        ref = ArtifactRef(path="src/nonexistent.py", artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"src/nonexistent.py": ActionKind.regenerate},
        )
        backend = _make_backend("content")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(plan, iso)

        assert len(result.failures) == 1
        assert "not found" in result.failures[0].lower()
