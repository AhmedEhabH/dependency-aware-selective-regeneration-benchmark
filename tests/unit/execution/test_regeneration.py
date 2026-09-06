from pathlib import Path

import pytest

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    LLMResponse,
    RegenerationScenarioContext,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import (
    SharedRegenerationExecutor,
    build_generation_prompt,
)
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import RegenerationPlan


def _make_backend(response_text: str = "replacement content"):
    class _Mock:
        def __init__(self, text: str):
            self._text = text
            self.prompt_tokens = 0
            self.completion_tokens = 0

        async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
            pt = max(1, len(prompt) // 4)
            ct = max(1, len(self._text) // 4)
            self.prompt_tokens += pt
            self.completion_tokens += ct
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
    def test_generation_prompt_includes_file_instruction_and_role_contract(self) -> None:
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="Task has no priority",
            requirement_after="Task gains Priority with HIGH, MEDIUM, LOW",
            acceptance_criteria=("TaskSerializer exposes priority",),
            architecture_constraints=(
                "Priority choices must be an Enum on the Task model",
                "Priority filtering must be in the view, not the serializer",
            ),
            expected_actions=(("todo/serializers.py", "modify"),),
            artifact_instructions=(("todo/serializers.py", "expose priority"),),
        )

        prompt = build_generation_prompt(
            artifact_path="todo/serializers.py",
            current_content="from rest_framework import serializers\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=context,
        )

        assert "File-specific instruction: expose priority" in prompt
        assert "Define or edit serializers only" in prompt
        assert "do not re-declare model enums" in prompt.lower()
        assert "viewsets, permissions, or routes" in prompt
        assert "Do not add a new third-party dependency" in prompt
        assert "Priority filtering must be in the view, not the serializer" in prompt

        model_prompt = build_generation_prompt(
            artifact_path="todo/models.py",
            current_content="from django.db import models\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=RegenerationScenarioContext(
                scenario_id="todo-smoke-001",
                requirement_before="old",
                requirement_after="new",
                expected_actions=(("todo/models.py", "modify"),),
            ),
        )
        assert "max_length to hold the longest stored value" in model_prompt

    def test_preserve_prompt_requires_exact_current_content(self) -> None:
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/models.py", "modify"),),
        )

        prompt = build_generation_prompt(
            artifact_path="todo/permissions.py",
            current_content="ORIGINAL = True\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=context,
        )

        assert "Expected action for this file: preserve" in prompt
        assert "No scenario change is required" in prompt
        assert "return the current file content byte-identically" in prompt.lower()

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

    def test_generated_file_bytes_preserve_lf_literally(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original content", encoding="utf-8")

        text = "first line\nsecond line\n"
        backend = _make_backend(text)
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert result.artifacts[0].status == "generated"
        written = (ws_root / "src/main.py").read_bytes()
        assert written == text.encode("utf-8"), (
            "Generated content must be written literally without OS line-ending translation"
        )
        assert b"\r\n" not in written


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

    def test_markdown_fenced_output_is_normalized_and_accepted(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original content", encoding="utf-8")

        backend = _make_backend("```python\nprint('hello')\n```")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert result.failures == ()
        assert result.artifacts[0].status == "generated"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "print('hello')"

    def test_fully_fenced_output_is_normalized_and_accepted(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original content", encoding="utf-8")

        backend = _make_backend("```\nplain content\n```")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert result.failures == ()
        assert result.artifacts[0].status == "generated"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == "plain content"

    def test_unbalanced_code_fence_is_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        orig = "original content"
        (src / "main.py").write_text(orig, encoding="utf-8")

        backend = _make_backend("```\ncontent without closing fence")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.failures) == 1
        assert "unbalanced_fence" in result.failures[0]
        assert result.artifacts[0].status == "rejected"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == orig

    def test_multiple_fenced_regions_are_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        orig = "original content"
        (src / "main.py").write_text(orig, encoding="utf-8")

        backend = _make_backend("```\nfirst\n```\n```\nsecond\n```")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.failures) == 1
        assert "multiple_fences" in result.failures[0]
        assert result.artifacts[0].status == "rejected"
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == orig

    def test_non_fenced_output_is_accepted(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("original", encoding="utf-8")

        backend = _make_backend("valid python code")
        executor = SharedRegenerationExecutor(backend)
        plan = _make_plan()
        result = executor.execute(plan, iso)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "generated"

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

    def test_guard_rejected_attempt_keeps_metrics_exact_and_writes_zero_files(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )
        todo = ws_root / "todo"
        todo.mkdir()
        original = "from django.db import models\nclass Task(models.Model):\n    pass\n"
        output = (
            "from django.db import models\n"
            "class Task(models.Model):\n"
            "    class Priority(models.TextChoices):\n"
            "        HIGH = 'HIGH', 'High'\n"
            "        MEDIUM = 'MEDIUM', 'Medium'\n"
            "        LOW = 'LOW', 'Low'\n"
            "    priority = models.CharField(max_length=5, "
            "choices=Priority.choices, default=Priority.MEDIUM)\n"
        )
        target = todo / "models.py"
        target.write_text(original, encoding="utf-8")
        ref = ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"todo/models.py": ActionKind.regenerate},
        )
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/models.py", "modify"),),
        )

        backend = _make_backend(output)
        result = SharedRegenerationExecutor(backend).execute(
            plan, iso, scenario_context=context
        )

        assert result.artifacts[0].status == "rejected"
        assert "choice_max_length_too_small" in "\n".join(result.failures)
        assert target.read_text(encoding="utf-8") == original
        assert result.model_calls == 1
        assert result.prompt_tokens == backend.prompt_tokens
        assert result.completion_tokens == backend.completion_tokens
        assert result.total_tokens == backend.prompt_tokens + backend.completion_tokens

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

    def test_preserve_rejection_retains_response_hash_and_preview(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        todo = ws_root / "todo"
        todo.mkdir()
        original = "from rest_framework.permissions import BasePermission\n"
        (todo / "permissions.py").write_text(original, encoding="utf-8")
        ref = ArtifactRef(
            path="todo/permissions.py", artifact_type=ArtifactType.source
        )
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"todo/permissions.py": ActionKind.regenerate},
        )
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/models.py", "modify"),),
        )
        backend = _make_backend(
            "from rest_framework.permissions import BasePermission\nCHANGED = True\n"
        )

        result = SharedRegenerationExecutor(backend).execute(
            plan, iso, scenario_context=context
        )

        assert result.artifacts[0].status == "rejected"
        assert "response_sha256=" in result.failures[0]
        assert "response_excerpt_json=" in result.failures[0]
        assert "CHANGED = True" in result.failures[0]
        assert (todo / "permissions.py").read_text(encoding="utf-8") == original

    @pytest.mark.parametrize(
        ("artifact_path", "current", "generated", "expected_failure"),
        (
            (
                "todo/models.py",
                "from django.db import models\nclass Task(models.Model):\n    pass\n",
                (
                    "from django.db import models\n"
                    "class Task(models.Model):\n"
                    "    class Priority(models.TextChoices):\n"
                    "        HIGH = 'HIGH', 'High'\n"
                    "        MEDIUM = 'MEDIUM', 'Medium'\n"
                    "        LOW = 'LOW', 'Low'\n"
                    "    priority = models.CharField(max_length=5, "
                    "choices=Priority.choices, default=Priority.MEDIUM)\n"
                ),
                "choice_max_length_too_small",
            ),
            (
                "todo/serializers.py",
                "from rest_framework import serializers\n",
                (
                    "from django.db import models\n"
                    "from rest_framework import serializers, viewsets\n"
                    "class Priority(models.TextChoices):\n"
                    "    HIGH = 'HIGH', 'High'\n"
                    "class TaskViewSet(viewsets.ModelViewSet):\n"
                    "    pass\n"
                ),
                "module_role_violation",
            ),
            (
                "todo/views.py",
                "from rest_framework import viewsets\n",
                (
                    "from django.db import models\n"
                    "from rest_framework import viewsets\n"
                    "from rest_framework_simplejwt.authentication import JWTAuthentication\n"
                    "class Task(models.Model):\n"
                    "    pass\n"
                ),
                "undeclared_dependency: rest_framework_simplejwt",
            ),
            (
                "todo/views.py",
                "from django.db import models\nfrom rest_framework import viewsets\n",
                (
                    "from django.db import models\n"
                    "from rest_framework import viewsets\n"
                    "class Task(models.Model):\n"
                    "    pass\n"
                ),
                "module_role_violation",
            ),
        ),
    )
    def test_observed_qwen_architecture_failures_are_rejected_before_validation(
        self,
        tmp_path: Path,
        artifact_path: str,
        current: str,
        generated: str,
        expected_failure: str,
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )
        target = ws_root / artifact_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(current, encoding="utf-8")
        ref = ArtifactRef(path=artifact_path, artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={artifact_path: ActionKind.regenerate},
        )
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=((artifact_path, "modify"),),
        )

        result = SharedRegenerationExecutor(_make_backend(generated)).execute(
            plan, iso, scenario_context=context
        )

        assert result.artifacts[0].status == "rejected"
        assert expected_failure in "\n".join(result.failures)
        assert target.read_text(encoding="utf-8") == current

    def test_oracle_priority_outputs_pass_generic_artifact_contract(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )
        todo = ws_root / "todo"
        todo.mkdir()
        current = "from django.db import models\nclass Task(models.Model):\n    pass\n"
        output = (
            "from django.db import models\n"
            "class Task(models.Model):\n"
            "    class Priority(models.TextChoices):\n"
            "        HIGH = 'HIGH', 'High'\n"
            "        MEDIUM = 'MEDIUM', 'Medium'\n"
            "        LOW = 'LOW', 'Low'\n"
            "    priority = models.CharField(max_length=6, "
            "choices=Priority.choices, default=Priority.MEDIUM)\n"
        )
        target = todo / "models.py"
        target.write_text(current, encoding="utf-8")
        ref = ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source)
        plan = RegenerationPlan(
            ordered_artifacts=(ref,),
            actions={"todo/models.py": ActionKind.regenerate},
        )
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/models.py", "modify"),),
        )

        result = SharedRegenerationExecutor(_make_backend(output)).execute(
            plan, iso, scenario_context=context
        )

        assert result.failures == ()
        assert result.artifacts[0].status == "generated"
        assert target.read_text(encoding="utf-8") == output


class TestAtomicRegenerationAttempt:
    """POST-SMOKE-CALIBRATION-CLOSURE Closure A.

    A single regeneration attempt is atomic: either every artifact in that
    attempt passes validation and every staged byte is written, or none of
    them are written. Atomicity applies per generation/repair attempt, never
    across separate iterative-agent iterations.
    """

    @staticmethod
    def _make_plan(paths: tuple[str, ...], action: str = "regenerate") -> RegenerationPlan:
        refs = tuple(
            ArtifactRef(path=p, artifact_type=ArtifactType.source)
            for p in paths
        )
        return RegenerationPlan(
            ordered_artifacts=refs,
            actions={p: ActionKind(action) for p in paths},
        )

    @staticmethod
    def _write_sources(ws_root: Path, paths: tuple[str, ...], contents: tuple[str, ...]) -> None:
        for rel, text in zip(paths, contents, strict=True):
            target = ws_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

    def _context(self, paths: tuple[str, ...]) -> RegenerationScenarioContext:
        return RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=tuple((p, "modify") for p in paths),
        )

    def test_one_invalid_plus_two_valid_artifacts_yield_zero_workspace_writes(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        original = "original content\n"
        self._write_sources(ws_root, paths, (original, original, original))
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )

        backend = _make_backend(
            "from rest_framework_simplejwt.authentication import JWTAuthentication\n"
        )
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )

        assert len(result.failures) >= 1
        assert any("undeclared_dependency" in f for f in result.failures)
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == original, rel

    def test_all_valid_artifacts_are_written_exactly_once(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        self._write_sources(ws_root, paths, ("old a\n", "old b\n", "old c\n"))
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )

        backend = _make_backend("x = 1\n")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )

        assert result.failures == ()
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == "x = 1\n", rel

    def test_preserve_only_rejection_yields_zero_writes(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py")
        self._write_sources(ws_root, paths, ("keep a\n", "keep b\n"))
        context = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/b.py", "modify"),),
        )

        backend = _make_backend("changed content\n")
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, scenario_context=context
        )

        assert any("out_of_scope_change" in f for f in result.failures)
        assert (ws_root / "todo/a.py").read_text(encoding="utf-8") == "keep a\n"
        assert (ws_root / "todo/b.py").read_text(encoding="utf-8") == "keep b\n"

    def test_later_iterative_agent_iteration_commits_independently(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        original = "original content\n"
        self._write_sources(ws_root, paths, (original, original, original))
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )

        bad_backend = _make_backend(
            "from rest_framework_simplejwt.authentication import JWTAuthentication\n"
        )
        first = SharedRegenerationExecutor(bad_backend).execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )
        assert any("undeclared_dependency" in f for f in first.failures)
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == original

        good_backend = _make_backend("x = 2\n")
        second = SharedRegenerationExecutor(good_backend).execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )
        assert second.failures == ()
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == "x = 2\n", rel

    def test_atomic_abort_remarks_staged_generated_artifact_as_aborted(
        self, tmp_path: Path
    ) -> None:
        """Closure B atomic metric truth: valid staged + invalid artifact.

        The valid artifact is staged but the attempt aborts atomically, so its
        status is re-marked ``aborted`` (never ``generated``), nothing is
        written, and hash/content evidence remains available.
        """
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py")
        original = "original content\n"
        self._write_sources(ws_root, paths, (original, original))
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )

        class _FirstValidSecondInvalid:
            def __init__(self) -> None:
                self.prompt_tokens = 0
                self.completion_tokens = 0
                self._call = 0

            async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
                self._call += 1
                text = (
                    "x = 1\n"
                    if self._call == 1
                    else "from rest_framework_simplejwt.authentication import JWTAuthentication\n"
                )
                pt = max(1, len(prompt) // 4)
                ct = max(1, len(text) // 4)
                self.prompt_tokens += pt
                self.completion_tokens += ct
                return LLMResponse(
                    text=text,
                    token_usage=TokenUsage(
                        prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
                    ),
                    finish_reason="stop",
                )

        backend = _FirstValidSecondInvalid()
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )

        assert any("undeclared_dependency" in f for f in result.failures)
        statuses = {a.path: a.status for a in result.artifacts}
        assert statuses["todo/a.py"] == "aborted"
        assert statuses["todo/b.py"] == "rejected"
        assert result.artifact_hashes
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == original, rel

    def test_all_valid_artifacts_written_once_with_matching_count(
        self, tmp_path: Path
    ) -> None:
        """All-valid control: every artifact written exactly once and the
        generated count equals the number of files written."""
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        original = "original content\n"
        self._write_sources(ws_root, paths, (original, original, original))
        (ws_root / "requirements.txt").write_text(
            "django>=5.0,<6.0\ndjangorestframework>=3.15,<4.0\n",
            encoding="utf-8",
        )

        backend = _make_backend("x = 1\n")
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, scenario_context=self._context(paths)
        )

        assert result.failures == ()
        generated = [a for a in result.artifacts if a.status == "generated"]
        assert len(generated) == len(paths)
        assert result.model_calls == len(paths)
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == "x = 1\n", rel


class TestModelCallDeadline:
    """POST-SMOKE-CALIBRATION-CLOSURE Closure A at the executor level.

    The cooperative deadline is checked immediately before and immediately
    after every backend model call. When it fires no further call is made,
    no staged write is committed, and the consumed call/tokens are preserved.
    """

    @staticmethod
    def _make_plan(paths: tuple[str, ...], action: str = "regenerate") -> RegenerationPlan:
        refs = tuple(
            ArtifactRef(path=p, artifact_type=ArtifactType.source)
            for p in paths
        )
        return RegenerationPlan(
            ordered_artifacts=refs,
            actions={p: ActionKind(action) for p in paths},
        )

    @staticmethod
    def _write_sources(ws_root: Path, paths: tuple[str, ...]) -> None:
        for rel in paths:
            target = ws_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"original {rel}\n", encoding="utf-8")

    def test_deadline_before_call_makes_no_call(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("src/a.py", "src/b.py", "src/c.py")
        self._write_sources(ws_root, paths)
        backend = _make_backend("replacement content")

        result = SharedRegenerationExecutor(
            backend, can_start_model_call=lambda: False
        ).execute(self._make_plan(paths), iso)

        assert result.model_calls == 0
        assert result.model_call_budget_exhausted is True
        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "aborted"
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == f"original {rel}\n"

    def test_deadline_after_call_consumes_call_and_stops_loop(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("src/a.py", "src/b.py", "src/c.py")
        self._write_sources(ws_root, paths)
        backend = _make_backend("replacement content")
        guard_calls = 0

        def guard() -> bool:
            nonlocal guard_calls
            guard_calls += 1
            return guard_calls <= 1

        result = SharedRegenerationExecutor(
            backend, can_start_model_call=guard
        ).execute(self._make_plan(paths), iso)

        assert result.model_calls == 1
        assert result.model_call_budget_exhausted is True
        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "aborted"
        assert result.artifacts[0].content == "replacement content"
        assert result.total_tokens == result.prompt_tokens + result.completion_tokens
        assert result.total_tokens > 0
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == f"original {rel}\n"


class TestRepairNoProgress:
    """POST-SMOKE-CALIBRATION-CLOSURE Closure B.

    When a repair round reproduces the exact prior output hash for an artifact,
    the round stops before further model calls, records repair_no_progress, and
    does not start another repair round for that unchanged failure.
    """

    @staticmethod
    def _make_plan(paths: tuple[str, ...], action: str = "regenerate") -> RegenerationPlan:
        refs = tuple(
            ArtifactRef(path=p, artifact_type=ArtifactType.source)
            for p in paths
        )
        return RegenerationPlan(
            ordered_artifacts=refs,
            actions={p: ActionKind(action) for p in paths},
        )

    @staticmethod
    def _write_sources(ws_root: Path, paths: tuple[str, ...], contents: tuple[str, ...]) -> None:
        for rel, text in zip(paths, contents, strict=True):
            target = ws_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

    @staticmethod
    def _sha256(text: str) -> str:
        import hashlib

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def test_identical_hash_stops_round_before_later_artifact_calls(
        self, tmp_path: Path
    ) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        self._write_sources(ws_root, paths, ("old\n", "old\n", "old\n"))
        same_output = "unchanged bad output\n"

        backend = _make_backend(same_output)
        prior = {path: self._sha256(same_output) for path in paths}

        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, prior_attempt_hashes=prior
        )

        assert result.repair_no_progress is True
        assert result.model_calls == 1
        assert len(result.artifacts) == 1
        assert result.artifacts[0].status == "rejected"
        assert any("repair_no_progress" in f for f in result.failures)
        assert result.artifact_hashes[paths[0]] == self._sha256(same_output)
        for rel in paths:
            assert (ws_root / rel).read_text(encoding="utf-8") == "old\n"

    def test_changed_hash_continues_round(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py")
        self._write_sources(ws_root, paths, ("old\n", "old\n"))
        prior = {paths[0]: self._sha256("different\n")}

        backend = _make_backend("new output\n")
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, prior_attempt_hashes=prior
        )

        assert result.repair_no_progress is False
        assert result.model_calls == 2
        assert result.artifact_hashes[paths[0]] == self._sha256("new output\n")

    def test_truthful_token_accounting_after_no_progress(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        paths = ("todo/a.py", "todo/b.py", "todo/c.py")
        self._write_sources(ws_root, paths, ("old\n", "old\n", "old\n"))
        same_output = "stalled output\n"

        backend = _make_backend(same_output)
        prior = {path: self._sha256(same_output) for path in paths}
        result = SharedRegenerationExecutor(backend).execute(
            self._make_plan(paths), iso, prior_attempt_hashes=prior
        )

        assert result.model_calls == 1
        assert result.total_tokens == result.prompt_tokens + result.completion_tokens
        assert result.prompt_tokens > 0
        assert result.completion_tokens > 0
class TestRepairPromptExactPatchContract:
    """D13r1 F4: the repair context must NOT contradict exact-patch mode.

    The legacy repair context told the model to "Return the complete
    replacement file content" — a direct contradiction of the EXACT PATCH
    output contract (SEARCH/REPLACE blocks only) that was appended right
    above it. A repair in exact-patch mode must never instruct complete-file
    regeneration (the D13 canary root cause for the 56k-char djangoCMS file).
    """

    def _repair_context(self) -> str:
        from benchmark.execution.regeneration import REPAIR_CONTEXT_PROMPT_TEMPLATE

        return REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
            stage="baseline_validation",
            exit_code=1,
            root_cause="AssertionError: priority not exposed",
            generation_failures="- (none recorded)",
            stdout="(none)",
            stderr="(none)",
        )

    def test_exact_patch_prompt_with_repair_has_no_complete_file_instruction(self) -> None:
        prompt = build_generation_prompt(
            requirement_delta="add priority",
            artifact_path="todo/models.py",
            language_hint="python",
            current_content="class Task:\n    pass\n",
            repair_context=self._repair_context(),
            expected_action="modify",
            output_mode="exact_patch",
        )
        assert "EXACT PATCH mode" in prompt
        assert "Return the complete replacement file content" not in prompt
        assert "Return only the complete replacement file content" not in prompt
        assert "<<<<<<< SEARCH" in prompt

    def test_exact_patch_repair_prompt_still_demands_patch_blocks(self) -> None:
        prompt = build_generation_prompt(
            requirement_delta="add priority",
            artifact_path="todo/models.py",
            language_hint="python",
            current_content="class Task:\n    pass\n",
            repair_context=self._repair_context(),
            expected_action="modify",
            output_mode="exact_patch",
        )
        assert "Follow the output contract already stated above" in prompt
        assert prompt.index("EXACT PATCH mode") < prompt.index(
            "Follow the output contract"
        )

    def test_complete_file_mode_repair_still_instructs_complete_file(self) -> None:
        prompt = build_generation_prompt(
            requirement_delta="add priority",
            artifact_path="todo/models.py",
            language_hint="python",
            current_content="class Task:\n    pass\n",
            repair_context=self._repair_context(),
            expected_action="modify",
            output_mode="complete_file",
        )
        assert "Return only the complete replacement file content" in prompt
        assert "<<<<<<< SEARCH" not in prompt

    def test_repair_context_appended_after_output_contract(self) -> None:
        prompt = build_generation_prompt(
            requirement_delta="add priority",
            artifact_path="todo/models.py",
            language_hint="python",
            current_content="class Task:\n    pass\n",
            repair_context=self._repair_context(),
            expected_action="modify",
            output_mode="exact_patch",
        )
        assert prompt.rstrip().endswith("without explanation or markdown fences.")
