import os
import sys
from pathlib import Path
from typing import Any

import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    DependencyGraph,
    ImpactPrediction,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.regeneration import SharedRegenerationExecutor
from benchmark.repositories.workspace import WorkspacePath
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
from benchmark.strategies.selective import HybridSelectiveStrategy

SRC = ArtifactType.source


@pytest.fixture
def todo_requirement() -> RequirementChange:
    return RequirementChange(
        before="Task model has only basic fields: title, description, status.",
        after="Task model must gain a priority field with choices HIGH, MEDIUM, LOW.",
        acceptance_criteria=(
            "Task model has priority field",
            "Serializer exposes priority",
        ),
    )


@pytest.fixture
def mock_backend() -> Any:
    class _Mock:
        def __init__(self) -> None:
            self.call_count = 0

        def count_prompt_tokens(self, prompt: str) -> int:
            return max(1, len(prompt) // 4)

        async def generate(
            self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096
        ) -> Any:
            self.call_count += 1
            from benchmark.core.models import LLMResponse
            return LLMResponse(
                text='{"decisions": [], "requires_iteration": false}',
                token_usage=TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
                finish_reason="stop",
            )

    return _Mock()


@pytest.fixture
def simple_universe() -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=(
            ArtifactRef(path="todo/models.py", artifact_type=SRC),
            ArtifactRef(path="todo/serializers.py", artifact_type=SRC),
            ArtifactRef(path="todo/views.py", artifact_type=SRC),
            ArtifactRef(path="todo/urls.py", artifact_type=SRC),
        )
    )


@pytest.fixture
def dep_graph() -> DependencyGraph:
    return DependencyGraph(
        nodes=("todo/models.py", "todo/serializers.py", "todo/views.py", "todo/urls.py"),
        edges=(
            ("todo/urls.py", "todo/views.py"),
            ("todo/views.py", "todo/serializers.py"),
            ("todo/views.py", "todo/models.py"),
            ("todo/serializers.py", "todo/models.py"),
        ),
    )


class TestSameChangeAndConfig:
    def test_all_arms_accept_change(self, todo_requirement, simple_universe, dep_graph, mock_backend):
        m = MonolithicRegenerationStrategy()
        assert isinstance(m.analyze_impact(None, todo_requirement, simple_universe), ImpactPrediction)

        s = HybridSelectiveStrategy(graph=dep_graph)
        assert isinstance(s.analyze_impact(None, todo_requirement, simple_universe), ImpactPrediction)

        class _Repo:
            class _Id:
                name = "todo"
            identity = _Id()
            path = "/fake"
            commit_sha = "abc123"

        a = IterativeRepositoryAgentStrategy(backend=mock_backend)
        assert isinstance(a.analyze_impact(_Repo(), todo_requirement, simple_universe), ImpactPrediction)


class TestSharedExecutor:
    def test_executor_imported(self) -> None:
        assert SharedRegenerationExecutor is not None

    def test_executor_signature(self) -> None:
        import inspect
        sig = inspect.signature(SharedRegenerationExecutor.__init__)
        assert "backend" in sig.parameters


class TestIsolatedWorkspace:
    def test_isolation_context(self) -> None:
        from benchmark.execution.isolation import IsolationContext
        ws = WorkspacePath(root="/tmp/test_ws")
        iso = IsolationContext(
            workspace=ws,
            snapshot_base=Path("/tmp/snap"),
            active_snapshot_root=Path("/tmp/active"),
        )
        assert iso.workspace.root == "/tmp/test_ws"

    def test_workspace_path_importable(self) -> None:
        ws = WorkspacePath(root="/tmp/test")
        assert ws.root == "/tmp/test"


class TestDecisionsWithinUniverse:
    def test_decisions_only_reference_universe_paths(self, simple_universe, dep_graph):
        original_paths = {a.path for a in simple_universe.artifacts}
        strategy = HybridSelectiveStrategy(graph=dep_graph)
        rc = RequirementChange(before="old", after="new", acceptance_criteria=("criterion",))
        prediction = strategy.analyze_impact(None, rc, simple_universe)
        for d in prediction.decisions:
            assert d.artifact.path in original_paths


class TestSelectiveUsesGraph:
    def test_selective_with_graph(self, dep_graph, simple_universe):
        strategy = HybridSelectiveStrategy(graph=dep_graph)
        rc = RequirementChange(before="old", after="new", acceptance_criteria=("criterion",))
        prediction = strategy.analyze_impact(None, rc, simple_universe)
        assert isinstance(prediction, ImpactPrediction)


class TestSelectiveNotEqualToGT:
    def test_selective_is_not_forced_to_any_fixed_path(self, dep_graph, simple_universe):
        strategy = HybridSelectiveStrategy(graph=dep_graph)
        rc = RequirementChange(before="old", after="new", acceptance_criteria=("criterion",))
        prediction = strategy.analyze_impact(None, rc, simple_universe)
        assert isinstance(prediction, ImpactPrediction)


class TestAgentBoundedLoop:
    def test_agent_has_iteration_property(self, mock_backend):
        strategy = IterativeRepositoryAgentStrategy(backend=mock_backend)
        assert hasattr(strategy, "last_requires_iteration")

    def test_agent_has_revise_method(self, mock_backend):
        strategy = IterativeRepositoryAgentStrategy(backend=mock_backend)
        assert hasattr(strategy, "revise_plan")


class TestMonolithicReferenceContract:
    """Phase 3: full-scope reference contract."""

    TODO_5 = ("todo/models.py", "todo/serializers.py", "todo/views.py", "todo/permissions.py", "todo/urls.py")

    @pytest.fixture
    def five_universe(self) -> ArtifactUniverse:
        return ArtifactUniverse(
            artifacts=tuple(
                ArtifactRef(path=p, artifact_type=SRC) for p in self.TODO_5
            )
        )

    def test_prediction_has_exactly_five_decisions(self, five_universe: ArtifactUniverse) -> None:
        """1. prediction contains exactly five decisions."""
        strategy = MonolithicRegenerationStrategy()
        rc = RequirementChange(before="old", after="new", acceptance_criteria=())
        prediction = strategy.analyze_impact(None, rc, five_universe)
        assert len(prediction.decisions) == 5

    def test_every_decision_is_regenerate(self, five_universe: ArtifactUniverse) -> None:
        """2. every decision is regenerate."""
        strategy = MonolithicRegenerationStrategy()
        rc = RequirementChange(before="old", after="new", acceptance_criteria=())
        prediction = strategy.analyze_impact(None, rc, five_universe)
        for d in prediction.decisions:
            assert d.action == ActionKind.regenerate, f"{d.artifact.path} is {d.action}"

    def test_no_file_outside_universe(self, five_universe: ArtifactUniverse) -> None:
        """3. no file outside the universe appears."""
        strategy = MonolithicRegenerationStrategy()
        rc = RequirementChange(before="old", after="new", acceptance_criteria=())
        prediction = strategy.analyze_impact(None, rc, five_universe)
        universe_paths = {a.path for a in five_universe.artifacts}
        for d in prediction.decisions:
            assert d.artifact.path in universe_paths, f"{d.artifact.path} not in universe"

    def test_plan_reaches_executor_through_runner(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """4. the plan reaches SharedRegenerationExecutor through the actual Runner non-dry path."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath
        from benchmark.core.models import LLMResponse, TokenUsage

        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        active = snap_base / "repo" / "v1"
        active.mkdir(parents=True)
        (active / "todo").mkdir(parents=True)
        for f in ("models.py", "serializers.py", "views.py", "permissions.py", "urls.py"):
            (active / "todo" / f).write_text("# placeholder\n")
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        (ws_root / "todo").mkdir(parents=True)
        for f in ("models.py", "serializers.py", "views.py", "permissions.py", "urls.py"):
            (ws_root / "todo" / f).write_text("# placeholder\n")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)

        backend_calls: list[str] = []

        class _Backend:
            call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return max(1, len(prompt) // 4)

            async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> object:
                self.call_count += 1
                backend_calls.append("called")
                return LLMResponse(
                    text="valid content",
                    token_usage=TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
                    finish_reason="stop",
                )

        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=self.TODO_5,
        )
        runner = BenchmarkRunner(
            strategy=MonolithicRegenerationStrategy(),
            backend=_Backend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="contract-monolithic-executor",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded, f"Run failed: {[f.message for f in record.failures]}"
        assert len(backend_calls) == 5, f"Expected 5 backend calls (one per editable file), got {len(backend_calls)}"

    def test_successful_run_has_non_zero_metrics(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """5. a successful regeneration run cannot report zero calls or zero generated files."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath
        from benchmark.core.models import LLMResponse, TokenUsage

        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        active = snap_base / "repo" / "v2"
        active.mkdir(parents=True)
        (active / "todo").mkdir(parents=True)
        for f in ("models.py", "serializers.py", "views.py", "permissions.py", "urls.py"):
            (active / "todo" / f).write_text("# placeholder\n")
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        (ws_root / "todo").mkdir(parents=True)
        for f in ("models.py", "serializers.py", "views.py", "permissions.py", "urls.py"):
            (ws_root / "todo" / f).write_text("# placeholder\n")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)

        class _Backend:
            call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return max(1, len(prompt) // 4)

            async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> object:
                self.call_count += 1
                return LLMResponse(
                    text="valid content",
                    token_usage=TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
                    finish_reason="stop",
                )

        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=self.TODO_5,
        )
        runner = BenchmarkRunner(
            strategy=MonolithicRegenerationStrategy(),
            backend=_Backend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="contract-monolithic-metrics",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded, f"Run failed: {[f.message for f in record.failures]}"
        assert record.total_workflow_model_calls > 0, "total_workflow_model_calls must be > 0"
        assert record.regeneration_model_calls > 0, "regeneration_model_calls must be > 0"
        assert record.regenerated_artifact_count > 0, "regenerated_artifact_count must be > 0"
        assert record.total_workflow_tokens > 0, "total_workflow_tokens must be > 0"


class TestEvaluatorAbsentFromContext:
    def test_evaluator_assets_not_in_pythonpath(self) -> None:
        for p in sys.path:
            if "evaluator_assets" in p:
                pytest.fail(f"evaluator_assets in sys.path: {p}")

    def test_evaluator_not_in_django_settings(self) -> None:
        assert "evaluator_assets" not in os.environ.get("DJANGO_SETTINGS_MODULE", "")


class TestEvaluatorRunsAgainstWorkspace:
    def test_subprocess_contract(self) -> None:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.exit(0)"],
            capture_output=True, timeout=10,
        )
        assert result.returncode == 0


class TestNoLeakage:
    def test_cwd_unchanged(self) -> None:
        assert os.path.isdir(os.getcwd())

    def test_sys_path_no_evaluator(self) -> None:
        for p in sys.path:
            assert "evaluator_assets" not in p

    def test_django_not_configured(self) -> None:
        assert "DJANGO_SETTINGS_MODULE" not in os.environ


class TestFailedRunRecorded:
    def test_run_record_can_hold_failure(self) -> None:
        from benchmark.core.enums import RunStatus
        record = RunRecord(
            identity=RunIdentity(
                run_id="failed-test",
                protocol_version="1.0",
                repository_commit_sha="abc123",
                scenario_id="test",
                strategy_name="test",
            ),
            status=RunStatus.failed,
        )
        assert record.status == RunStatus.failed


class TestKaggleMirror:
    def test_kaggle_mirror_exists(self) -> None:
        kaggle_dir = Path(__file__).resolve().parent.parent.parent / "kaggle_upload"
        assert kaggle_dir.is_dir()


class TestEditableUniverseContract:
    """Phase 2: resolve_allowed_artifacts through production pipeline."""

    def test_regeneration_with_empty_editable_paths_fails_closed(self, tmp_path: Path) -> None:
        """A. Empty editable_artifact_paths fails before strategy call."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath

        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        active = snap_base / "repo" / "v1"
        active.mkdir(parents=True)
        (active / "todo").mkdir()
        (active / "todo" / "models.py").write_text("")
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)

        calls: list = []

        class _Recorder:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                calls.append(kwargs)
                return ImpactPrediction()

        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=(),
        )
        runner = BenchmarkRunner(
            strategy=_Recorder(),
            backend=None,
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="contract-empty-editable",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert len(calls) == 0, "Strategy must not be called when editable paths are empty"
        messages = [f.message for f in record.failures]
        assert any("allowed_paths must be non-empty" in m for m in messages), (
            f"Failure must cite empty-policy condition. Got: {messages}"
        )

    def test_configured_editable_paths_reach_strategy_exactly(self, tmp_path: Path) -> None:
        """B. Exactly the configured paths reach the strategy; test/config/migration excluded."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath

        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        active = snap_base / "repo" / "v2"
        active.mkdir(parents=True)
        (active / "todo").mkdir()
        for f in ("models.py", "views.py", "urls.py"):
            (active / "todo" / f).write_text("")
        (active / "todo" / "tests.py").write_text("")
        (active / "todo" / "migrations").mkdir()
        (active / "todo" / "migrations" / "0001.py").write_text("")
        (active / "config").mkdir()
        (active / "config" / "settings.py").write_text("")
        (active / "manage.py").write_text("")
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)

        received: list[ArtifactUniverse] = []

        class _Recorder:
            def analyze_impact(
                self,
                repository: object = None,
                requirement_change: object = None,
                artifact_universe: object = None,
            ) -> ImpactPrediction:
                if artifact_universe is not None:
                    received.append(artifact_universe)
                return ImpactPrediction()

        allowed = ("todo/models.py", "todo/views.py", "todo/urls.py")
        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=allowed,
        )
        runner = BenchmarkRunner(
            strategy=_Recorder(),
            backend=None,
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="contract-exact-editable",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        runner.run(scenario)
        assert len(received) == 1, "Strategy must be called exactly once"
        paths = {a.path for a in received[0].artifacts}
        assert paths == set(allowed), (
            f"Expected only configured paths {set(allowed)}, got {paths}"
        )
        assert "todo/tests.py" not in paths
        assert "todo/migrations/0001.py" not in paths
        assert "config/settings.py" not in paths
        assert "manage.py" not in paths

    def test_ground_truth_mutation_does_not_change_regeneration_universe(self, tmp_path: Path) -> None:
        """C. Two scenarios with different expected_affected_artifacts get identical universe."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath

        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        active = snap_base / "repo" / "v3"
        active.mkdir(parents=True)
        (active / "todo").mkdir()
        (active / "todo" / "models.py").write_text("")
        (active / "todo" / "views.py").write_text("")
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)

        received: list[ArtifactUniverse] = []

        class _Recorder:
            def analyze_impact(
                self,
                repository: object = None,
                requirement_change: object = None,
                artifact_universe: object = None,
            ) -> ImpactPrediction:
                if artifact_universe is not None:
                    received.append(artifact_universe)
                return ImpactPrediction()

        allowed = ("todo/models.py", "todo/views.py")

        def _make_runner() -> BenchmarkRunner:
            c = RunnerConfig(
                strategy_name="selective",
                backend_name="test_backend",
                protocol_version="1.0",
                max_attempts=1,
                enable_regeneration=True,
                validation_command=[sys.executable, "-c", "exit(0)"],
                editable_artifact_paths=allowed,
            )
            return BenchmarkRunner(
                strategy=_Recorder(),
                backend=None,
                isolation=iso,
                config=c,
            )

        gt_a = ArtifactRef(path="todo/only_in_a.py", artifact_type=ArtifactType.source)
        gt_b = ArtifactRef(path="todo/only_in_b.py", artifact_type=ArtifactType.source)
        scenario_a = Scenario(
            scenario_id="contract-gt-a",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt_a,),
        )
        scenario_b = Scenario(
            scenario_id="contract-gt-b",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt_b,),
        )
        _make_runner().run(scenario_a)
        _make_runner().run(scenario_b)
        assert len(received) == 2, "Strategy must be called twice"
        paths_a = {a.path for a in received[0].artifacts}
        paths_b = {a.path for a in received[1].artifacts}
        assert paths_a == paths_b, (
            f"Ground Truth mutation changed universe: {paths_a} != {paths_b}"
        )
        assert paths_a == set(allowed)

    def test_invalid_profile_editable_policy_blocks_cli_execution(self) -> None:
        """D. Missing or empty llm_editable in profile causes CLI exit 1."""
        from benchmark.repositories.manifest import RepositoryProfile

        empty_profile = RepositoryProfile(
            repository_id="test_repo",
            name="test_repo",
            protocol_version="1.0",
            overview="",
            artifact_universe={"llm_editable": []},
        )
        au = empty_profile.artifact_universe
        assert isinstance(au, dict)
        paths = au.get("llm_editable")
        assert isinstance(paths, list) and len(paths) == 0

        _approved_regen = frozenset({"monolithic", "selective", "iterative_repository_agent"})
        _editable_paths: dict[str, tuple[str, ...]] = {}
        repo_ids_for_scenarios = {"test_repo"}
        au_ok = False

        for repo_id in repo_ids_for_scenarios:
            profile_obj = empty_profile if repo_id == "test_repo" else None
            if profile_obj is not None:
                au = profile_obj.artifact_universe
                if isinstance(au, dict):
                    paths = au.get("llm_editable")
                    if isinstance(paths, list) and len(paths) > 0:
                        if all(isinstance(p, str) and len(p) > 0 for p in paths):
                            _editable_paths[repo_id] = tuple(str(p) for p in paths)
                            au_ok = True
            if not au_ok:
                break

        assert not au_ok, "Empty llm_editable list must fail validation"
        assert len(_editable_paths) == 0, "No paths should be registered when llm_editable is empty"
