from __future__ import annotations

from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    AcceptanceCriterion,
    ArchitectureConstraint,
    ArtifactRef,
    LLMResponse,
    RegenerationScenarioContext,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import (
    REPAIR_CONTEXT_PROMPT_TEMPLATE,
    SharedRegenerationExecutor,
    build_generation_prompt,
)
from benchmark.selection.planner import RegenerationPlan

GOLD_SENTINEL_PATH = "todo/z_gold_sentinel_path.py"
GOLD_SENTINEL_LABEL = "GOLD_SENTINEL_EXPOSE_PRIORITY"


def _make_backend(response_text: str):
    class _Mock:
        async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
            return LLMResponse(
                text=response_text,
                token_usage=TokenUsage(),
                finish_reason="stop",
            )

    return _Mock()


def _scientific_context() -> RegenerationScenarioContext:
    """A context as built by the scientific profile (gold hidden)."""
    return RegenerationScenarioContext(
        scenario_id="todo-smoke-001",
        requirement_before="old",
        requirement_after="new",
        acceptance_criteria=("Task model has priority field",),
        architecture_constraints=("Priority filtering must be in the view",),
        expected_actions=(),
        artifact_instructions=(),
        gold_isolated=True,
    )


def _gold_rich_context() -> RegenerationScenarioContext:
    return RegenerationScenarioContext(
        scenario_id="todo-smoke-001",
        requirement_before="old",
        requirement_after="new",
        acceptance_criteria=("app runs",),
        expected_actions=(),
        artifact_instructions=(),
    )


class TestGoldSentinelNeverInScientificPrompt:
    def test_scientific_generation_prompt_has_no_sentinel(self) -> None:
        prompt = build_generation_prompt(
            artifact_path="todo/models.py",
            current_content="from django.db import models\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=_scientific_context(),
        )
        assert GOLD_SENTINEL_PATH not in prompt
        assert GOLD_SENTINEL_LABEL not in prompt

    def test_scientific_repair_prompt_has_no_sentinel(self) -> None:
        repair = REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
            stage="scenario_evaluator",
            exit_code=1,
            root_cause=f"{GOLD_SENTINEL_LABEL} failure",
            generation_failures="- (none recorded)",
            stdout="(none)",
            stderr="(none)",
        )
        prompt = build_generation_prompt(
            artifact_path="todo/models.py",
            current_content="from django.db import models\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=_scientific_context(),
            repair_context=repair,
        )
        assert GOLD_SENTINEL_PATH not in prompt

    def test_gold_instructions_never_reach_prompt_even_if_scenario_has_them(self) -> None:
        """Defense-in-depth: a scientific (gold-isolated) context is ignored for
        gold-derived instruction/path content even if gold content is present,
        and the explicit plan-derived expected action wins."""
        ctx = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=((GOLD_SENTINEL_PATH, "modify"),),
            artifact_instructions=((GOLD_SENTINEL_PATH, GOLD_SENTINEL_LABEL),),
            gold_isolated=True,
        )
        prompt = build_generation_prompt(
            artifact_path="todo/models.py",
            current_content="from django.db import models\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=ctx,
            expected_action="modify",
        )
        assert GOLD_SENTINEL_LABEL not in prompt
        assert GOLD_SENTINEL_PATH not in prompt

    def test_non_isolated_context_keeps_historical_instruction(self) -> None:
        ctx = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            expected_actions=(("todo/serializers.py", "modify"),),
            artifact_instructions=(("todo/serializers.py", "expose priority"),),
        )
        prompt = build_generation_prompt(
            artifact_path="todo/serializers.py",
            current_content="from rest_framework import serializers\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=ctx,
            expected_action="modify",
        )
        assert "File-specific instruction: expose priority" in prompt


class TestRunnerBuildsGoldFreeContext:
    def _make_iso(self, tmp_path: Path) -> IsolationContext:
        from benchmark.repositories.workspace import WorkspacePath

        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True, exist_ok=True)
        return IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            snapshot_base=tmp_path / "snap",
            active_snapshot_root=tmp_path / "active",
        )

    def test_runner_scientific_context_drops_gold(self, tmp_path: Path) -> None:
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig

        class _FakeStrategy:
            pass

        iso = self._make_iso(tmp_path)
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),  # type: ignore[arg-type]
            backend=None,
            isolation=iso,
            config=RunnerConfig(
                strategy_name="scientific",
                backend_name="openrouter",
                protocol_version="1.0",
                max_attempts=1,
                enable_regeneration=False,
                scientific_gold_isolation=True,
            ),
        )
        scenario = Scenario(
            scenario_id="todo-smoke-001",
            repository="todo",
            change_type="modify",
            blast_radius="localized",  # type: ignore[arg-type]
            requirement_before="old",
            requirement_after="new",
            rationale="test",
            acceptance_criteria=(AcceptanceCriterion(description="app runs"),),
            architecture_constraints=(ArchitectureConstraint(description="single app"),),
            expected_actions=(
                (ArtifactRef(path=GOLD_SENTINEL_PATH, artifact_type=ArtifactType.source), ActionKind.regenerate),
            ),
            expected_artifact_instructions=((GOLD_SENTINEL_PATH, GOLD_SENTINEL_LABEL),),
        )
        ctx = runner._build_scenario_context(scenario)
        assert ctx.expected_actions == ()
        assert ctx.artifact_instructions == ()
        assert GOLD_SENTINEL_PATH not in str(ctx)

    def test_non_scientific_context_keeps_gold(self, tmp_path: Path) -> None:
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig

        class _FakeStrategy:
            pass

        iso = self._make_iso(tmp_path)
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),  # type: ignore[arg-type]
            backend=None,
            isolation=iso,
            config=RunnerConfig(
                strategy_name="selective",
                backend_name="test",
                protocol_version="1.0",
                max_attempts=1,
                enable_regeneration=False,
                scientific_gold_isolation=False,
            ),
        )
        scenario = Scenario(
            scenario_id="todo-smoke-001",
            repository="todo",
            change_type="modify",
            blast_radius="localized",  # type: ignore[arg-type]
            requirement_before="old",
            requirement_after="new",
            rationale="test",
            expected_actions=(
                (ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source), ActionKind.regenerate),
            ),
        )
        ctx = runner._build_scenario_context(scenario)
        assert "todo/models.py" in {p for p, _a in ctx.expected_actions}


class TestExactPatchDrivenByPlanActions:
    def test_exact_patch_mode_active_from_plan_action(self, tmp_path: Path) -> None:
        iso, ws_root = _make_workdir_isolation(tmp_path)
        src = ws_root / "src"
        src.mkdir()
        (src / "main.py").write_text("print('v1')\n", encoding="utf-8", newline="")

        plan = RegenerationPlan(
            ordered_artifacts=(ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),),
            actions={"src/main.py": ActionKind.regenerate},
        )
        backend = _make_backend(
            "<<<<<<< SEARCH\nprint('v1')\n=======\nprint('v2')\n>>>>>>> REPLACE"
        )
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(
            plan,
            iso,
            scenario_context=_scientific_context(),
            enable_exact_patch=True,
        )
        assert result.artifacts[0].status == "generated"
        assert "print('v2')" in (ws_root / "src/main.py").read_text(encoding="utf-8")


def _make_workdir_isolation(tmp_path: Path) -> tuple[IsolationContext, Path]:
    from benchmark.repositories.workspace import WorkspacePath

    ws_root = tmp_path / "ws_exact"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
    return iso, ws_root


class TestGenericGuardWithoutGold:
    def _run(self, tmp_path: Path, response_text: str, path: str = "src/main.py") -> str:
        iso, ws_root = _make_workdir_isolation(tmp_path)
        parent = ws_root / Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)
        (ws_root / path).write_text("print('current')\n", encoding="utf-8", newline="")

        plan = RegenerationPlan(
            ordered_artifacts=(ArtifactRef(path=path, artifact_type=ArtifactType.source),),
            actions={path: ActionKind.regenerate},
        )
        backend = _make_backend(response_text)
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(
            plan,
            iso,
            scenario_context=_scientific_context(),
            enable_exact_patch=False,
        )
        joined = "; ".join(result.failures)
        return joined

    def test_invalid_syntax_rejected_without_gold(self, tmp_path: Path) -> None:
        failures = self._run(tmp_path, "def broken(:\n")
        assert "python_syntax_error" in failures

    def test_undeclared_dependency_rejected_without_gold(self, tmp_path: Path) -> None:
        failures = self._run(tmp_path, "import nonexistent_pkg_xx\nx = 1\n")
        assert "undeclared_dependency" in failures

    def test_role_violation_rejected_without_gold(self, tmp_path: Path) -> None:
        from benchmark.execution.regeneration import _python_artifact_contract_failures

        output_text = (
            "from rest_framework import serializers\n"
            "class BadViewSet(serializers.ModelSerializer):\n"
            "    pass\n"
        )
        failures_bundle = _python_artifact_contract_failures(
            artifact_path="todo/serializers.py",
            output_text=output_text,
            current_content="",
            workspace_root=str(tmp_path),
        )
        assert any("module_role_violation" in f for f in failures_bundle)
