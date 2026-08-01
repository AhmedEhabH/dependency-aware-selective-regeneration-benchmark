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
