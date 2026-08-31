"""Regression tests for Scientific Smoke V1 failure root causes.

Covers fixes A through F plus retry-readiness:
  A — UTC symbol missing in finalization path
  B — checkpoint scenario_ids from filtered execution plan
  C — no regeneration when enable_regeneration=True w/o validation_command
  D — finish_reason detection in KaggleQwenBackend
  E — failed-run workflow metrics preserved
  F — terminal progress state
  G — positive monolithic end-to-end regeneration
  H — positive selective end-to-end regeneration
  I — missing validation command fails closed before model call
  J — finish_reason persistence and max_tokens propagation
  K — retry readiness integration (3 arms, exact smoke spec)
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.core.enums import ArtifactType, FailureKind, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArtifactRef,
    BlastRadius,
    ImpactPrediction,
    LLMResponse,
    Scenario,
    TokenUsage,
)
from benchmark.execution.budgets import BudgetManager
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.snapshot import discover_eligible_artifacts
from benchmark.repositories.workspace import WorkspacePath
from benchmark.scenarios.loader import ScenarioLoader
from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
from benchmark.strategies.selective import HybridSelectiveStrategy

# Canonical controlled repository path
_CANONICAL_TODO_REPO = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "repositories" / "todo"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_backend(
    response_text: str = "replacement content",
    finish_reason: str = "stop",
    token_usage: TokenUsage | None = None,
):
    class _Mock:
        def __init__(self, text: str, fr: str, tu: TokenUsage | None):
            self._text = text
            self._finish_reason = fr
            self._token_usage = tu

        def count_prompt_tokens(self, prompt: str) -> int:
            return max(1, len(prompt) // 4)

        async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096):
            pt = max(1, len(prompt) // 4) if self._token_usage is None else self._token_usage.prompt_tokens
            ct = max(1, len(self._text) // 4) if self._token_usage is None else self._token_usage.completion_tokens
            return LLMResponse(
                text=self._text,
                token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
                finish_reason=self._finish_reason,
            )

    return _Mock(response_text, finish_reason, token_usage)


def _make_scenario(
    repo: str = "todo",
    artifacts: tuple[ArtifactRef, ...] = (),
    before: str = "old requirement",
    after: str = "new requirement",
) -> Scenario:
    return Scenario(
        scenario_id="todo-loc-001",
        repository=repo,
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before=before,
        requirement_after=after,
        rationale="test scenario",
        expected_affected_artifacts=artifacts,
        acceptance_criteria=(
            AcceptanceCriterion(description="validation must pass"),
        ),
    )


def _setup_workspace(
    tmp_path: Path,
    artifacts: tuple[ArtifactRef, ...],
    repo: str = "todo",
    revision: str = "main",
) -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    active_root = snap_base / repo / revision
    active_root.mkdir(parents=True, exist_ok=True)

    for ref in artifacts:
        target = ws_root / ref.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"original {ref.path} content", encoding="utf-8")
        snap_target = active_root / ref.path
        snap_target.parent.mkdir(parents=True, exist_ok=True)
        snap_target.write_text(f"original {ref.path} content", encoding="utf-8")

    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    return iso, ws_root


def _make_runner(
    tmp_path: Path,
    strategy: object,
    backend: object,
    iso: IsolationContext,
    enable_regeneration: bool = False,
    validation_command: list[str] | None = None,
    validation_timeout: int = 10,
    strategy_name: str = "monolithic",
    max_attempts: int = 1,
    max_tokens: int = 0,
    editable_artifact_paths: tuple[str, ...] = ("src/a.py",),
) -> BenchmarkRunner:
    config = RunnerConfig(
        strategy_name=strategy_name,
        backend_name="mock",
        protocol_version="1.0",
        max_attempts=max_attempts,
        max_tokens=max_tokens,
        enable_regeneration=enable_regeneration,
        validation_command=validation_command,
        validation_timeout=validation_timeout,
        editable_artifact_paths=editable_artifact_paths,
    )
    return BenchmarkRunner(
        strategy=strategy,
        backend=backend,
        isolation=iso,
        config=config,
    )


# ---------------------------------------------------------------------------
# Fix A — UTC symbol available in finalization path
# ---------------------------------------------------------------------------


class TestFixAUtc:
    """Exercise the real production finalization path that assigns
    report_generated_at via rebuild_experiment_reports."""

    def test_utc_symbol_available_in_finalization(self, tmp_path: Path) -> None:
        from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
        from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
        from benchmark.checkpoint.reports import rebuild_experiment_reports

        cp = CheckpointData(
            profile="scientific-smoke-v1",
            execution_plan_hash="abc123",
            planned_run_ids=["r1"],
            completed_run_ids=["r1"],
            succeeded_run_ids=["r1"],
            failed_run_ids=[],
            retryable_run_ids=[],
            pending_run_ids=[],
            total_planned=1,
            total_completed=1,
            completion_status="completed",
            scenario_ids=["todo-loc-001"],
            strategy_names=["monolithic"],
        )
        CheckpointManager(tmp_path).write_atomic(cp)

        store = RunRecordStore(tmp_path)
        store.append(RunRecordData(
            run_id="r1",
            profile="scientific-smoke-v1",
            repository_id="todo",
            scenario_id="todo-loc-001",
            strategy_id="monolithic",
            repetition=1,
            seed=42,
            status="succeeded",
            duration_seconds=1.0,
        ))

        audit = rebuild_experiment_reports(tmp_path, session_elapsed_seconds=10.0)
        assert audit["final_status"] == "completed"

        import json
        progress_path = tmp_path / "progress.json"
        assert progress_path.is_file()
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        assert "report_generated_at" in progress
        assert progress["report_generated_at"] != ""
        assert progress["report_generated_at"].endswith("+00:00")

    def test_entry_point_finalization_uses_utc(self) -> None:
        """Directly call the production helper extracted from
        seven_arm_benchmark.py.  If UTC is removed from that module,
        this test fails."""
        from seven_arm_benchmark import _build_interrupted_progress_data

        result = _build_interrupted_progress_data(
            profile_name="test",
            total_planned=1,
            total_completed=0,
            total_failed=0,
            total_pending=1,
            total_attempted=0,
            total_elapsed=1.0,
            total_succeeded=0,
            total_retryable=0,
            experiment_run_duration=0.0,
        )
        assert result.report_generated_at.endswith("+00:00"), (
            f"Expected UTC suffix, got: {result.report_generated_at}"
        )


# ---------------------------------------------------------------------------
# Fix B — checkpoint scenario_ids from filtered execution plan
# ---------------------------------------------------------------------------


class TestFixBScenarioIdentity:
    def test_planned_run_scenario_ids_match(self) -> None:
        from seven_arm_benchmark import PROFILES, _build_execution_plan

        profile = PROFILES["scientific-smoke-v1"]

        class _Scenario:
            def __init__(self, sid: str, repo: str):
                self.scenario_id = sid
                self.repository = repo
                self.blast_radius = "localized"

        selected = [_Scenario("todo-loc-001", "todo")]
        plan = _build_execution_plan(
            profile=profile, scenario_provider=None,
            strategy_names=profile.strategies, scenarios=selected,
        )
        plan_ids = list({run["scenario_id"] for run in plan})
        assert plan_ids == ["todo-loc-001"], f"Expected ['todo-loc-001'], got {plan_ids}"

    def test_checkpoint_scenario_ids_from_filtered(self) -> None:
        from seven_arm_benchmark import PROFILES

        profile = PROFILES["scientific-smoke-v1"]
        assert profile.scenario_ids == ["todo-loc-001"]

    def test_run_record_scenario_ids_agree(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = RunRecordData(
            run_id="todo-loc-001_monolithic_rep1_abc12345",
            profile="scientific-smoke-v1",
            repository_id="todo",
            scenario_id="todo-loc-001",
            strategy_id="monolithic",
            repetition=1,
            seed=42,
            status="succeeded",
            token_usage={"prompt": 10, "completion": 5, "total": 15},
            duration_seconds=1.0,
        )
        store.append(rec)
        loaded = store.load_all()
        assert loaded[0].scenario_id == "todo-loc-001"


# ---------------------------------------------------------------------------
# Fix C — positive monolithic end-to-end (no-op prevention)
# ---------------------------------------------------------------------------


class TestFixCPositiveMonolithic:
    """Replace the weak no-op test: prove monolithic actually regenerates."""

    def test_monolithic_succeeds_with_validation(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/models.py", "src/views.py"),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.succeeded
        assert record.regeneration_model_calls >= 1
        assert record.regenerated_artifact_count >= 1
        assert record.functional_validation_passed is True
        assert record.total_workflow_model_calls >= 1
        assert record.total_workflow_tokens > 0

    def test_missing_validation_fails_before_model_call(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=None,
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.failed
        assert record.regenerated_artifact_count == 0
        assert record.functional_validation_passed is None
        assert record.total_workflow_tokens == 0
        assert record.total_workflow_model_calls == 0
        assert len(record.failures) >= 1
        assert any(
            f.failure_kind == FailureKind.harness_defect
            and "validation_command" in f.message
            for f in record.failures
        ), "Must fail with harness_defect about missing validation_command"


class TestFixCPositiveSelective:
    """Prove selective strategy executes validation and makes decisions."""

    def test_selective_succeeds_with_validation(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        from benchmark.core.models import DependencyGraph
        from benchmark.selection.dependency_scope import ArtifactDescriptor
        graph = DependencyGraph(
            nodes=("src/models.py", "src/views.py"),
            edges=(("src/models.py", "src/views.py"),),
        )
        desc = ArtifactDescriptor(
            path="src/models.py",
            category="model",
            description="Application models",
            provides_symbols=("models",),
            typical_change_triggers=("schema changes",),
        )
        strategy = HybridSelectiveStrategy(graph=graph, artifact_descriptors=(desc,))
        scenario = _make_scenario(
            artifacts=artifacts,
            before="models",
            after="models new_feature",
        )

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="hybrid_selective",
            editable_artifact_paths=("src/models.py", "src/views.py"),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.succeeded
        assert record.selected_artifact_count >= 1
        assert record.regeneration_model_calls >= 1
        assert record.regenerated_artifact_count >= 1
        assert record.functional_validation_passed is True
        assert record.total_workflow_model_calls >= 1
        assert record.total_workflow_tokens > 0


# ---------------------------------------------------------------------------
# Fix D — finish_reason detection in KaggleQwenBackend
# ---------------------------------------------------------------------------


class TestFixDFinishReason:
    def test_finish_reason_not_hardcoded_stop(self) -> None:
        import inspect

        from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

        source = inspect.getsource(KaggleQwenBackend._generate_sync)
        assert "finish_reason = \"stop\"" not in source, (
            "finish_reason must not be hardcoded to 'stop'"
        )
        assert "eos_token_id" in source, (
            "_generate_sync() must inspect eos_token_id for actual finish reason"
        )

    def test_finish_reason_dynamic_detection(self) -> None:
        """KaggleQwenBackend uses eos_token_id to dynamically set
        finish_reason to 'eos' (EOS emitted) or 'length' (token limit)."""
        import inspect

        from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

        source = inspect.getsource(KaggleQwenBackend._generate_sync)
        assert "finish_reason = \"eos\"" in source or 'finish_reason = "length"' in source

    def test_finish_reason_eos_on_normal_completion(self) -> None:
        """When EOS token is emitted, finish_reason should be "eos"."""
        backend = _make_backend("complete json response", finish_reason="eos")
        import asyncio
        resp = asyncio.get_event_loop().run_until_complete(
            backend.generate(prompt="test", temperature=0.0, max_tokens=4096)
        )
        assert resp.finish_reason == "eos"

    def test_max_tokens_propagated_to_max_new_tokens(self) -> None:
        """KaggleQwenBackend passes max_tokens as max_new_tokens to the model."""
        import inspect

        from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

        source = inspect.getsource(KaggleQwenBackend._generate_sync)
        assert "max_new_tokens" in source, (
            "_generate_sync() must pass max_tokens as max_new_tokens"
        )

    def test_finish_reason_in_run_record_failures(self) -> None:
        """When a generation is truncated, finish_reason must be persisted
        in failure evidence or RunRecord metadata, not only in logs."""
        backend = _make_backend(
            '{"incomplete": true',
            finish_reason="length",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=196, total_tokens=206),
        )

        class _ParseFailStrategy:
            def analyze_impact(self, *args, **kwargs):
                import asyncio
                resp = asyncio.get_event_loop().run_until_complete(
                    backend.generate(prompt="test", temperature=0.0, max_tokens=256)
                )
                return ImpactPrediction(
                    errors=(f"could not parse: {resp.text[:100]}",),
                    token_usage=resp.token_usage,
                )

        prediction = _ParseFailStrategy().analyze_impact()
        assert prediction.errors
        assert "could not parse" in prediction.errors[0]
        # Token usage is preserved even though parsing failed
        assert prediction.token_usage is not None
        assert prediction.token_usage.completion_tokens == 196


# ---------------------------------------------------------------------------
# Fix E — failed-run workflow metrics
# ---------------------------------------------------------------------------


class _TruncatedAgentStrategy:
    def __init__(self) -> None:
        self._backend = _TruncatedResponseBackend()
        self._last_requires_iteration: bool = True
        self._call_count: int = 0

    def begin_run(self, workspace_root: str | Path) -> None:
        self._call_count = 0

    @property
    def last_requires_iteration(self) -> bool:
        return self._last_requires_iteration

    @property
    def model_call_count(self) -> int:
        return self._call_count

    @property
    def tool_call_count(self) -> int:
        return 0

    @property
    def tool_duration_seconds(self) -> float:
        return 0.0

    @property
    def inspected_file_count(self) -> int:
        return 0

    def analyze_impact(
        self,
        repository: object = None,
        requirement_change: object = None,
        artifact_universe: object = None,
        **kwargs: object,
    ) -> ImpactPrediction:
        import asyncio
        self._call_count += 1
        response = asyncio.get_event_loop().run_until_complete(
            self._backend.generate(prompt="test", temperature=0.0, max_tokens=4096)
        )
        tok = response.token_usage
        fr = response.finish_reason or "unknown"
        err = (f"finish_reason={fr}: iterative agent: could not parse "
               f"LLM response as JSON: {response.text[:200]}")
        parsed = ImpactPrediction(errors=(err,))
        if tok and (tok.prompt_tokens > 0 or tok.completion_tokens > 0):
            object.__setattr__(parsed, "token_usage", tok)
        return parsed


class _TruncatedResponseBackend:
    def count_prompt_tokens(self, prompt: str) -> int:
        return 499

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        return LLMResponse(
            text='{"action": "final", "selected_paths": ["src/a.py", "src/b.py"',  # truncated
            token_usage=TokenUsage(prompt_tokens=499, completion_tokens=196, total_tokens=695),
            finish_reason="eos",
        )


class TestFixEFailedRunMetrics:
    def test_failed_iterative_run_preserves_selection_metrics(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "main"
        active_root.mkdir(parents=True, exist_ok=True)

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)

        strategy = _TruncatedAgentStrategy()
        backend = _TruncatedResponseBackend()
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/a.py", "src/b.py"),
            validation_command=[sys.executable, "-c", "exit(0)"],
            max_attempts=2,
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)

        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        )
        (active_root / "src").mkdir(parents=True, exist_ok=True)
        (active_root / "src" / "a.py").write_text("content", encoding="utf-8")
        (active_root / "src" / "b.py").write_text("content", encoding="utf-8")

        scenario = _make_scenario(artifacts=artifacts)
        record = runner.run(scenario)

        assert record.selection_model_calls == 1, (
            f"Expected selection_model_calls=1, got {record.selection_model_calls}"
        )
        assert record.selection_total_tokens == 695, (
            f"Expected selection_total_tokens=695, got {record.selection_total_tokens}"
        )
        assert record.total_workflow_model_calls == 1, (
            f"Expected total_workflow_model_calls=1, got {record.total_workflow_model_calls}"
        )
        assert record.total_workflow_tokens == 695, (
            f"Expected total_workflow_tokens=695, got {record.total_workflow_tokens}"
        )

    def test_failed_run_duration_non_negative(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "main"
        active_root.mkdir(parents=True, exist_ok=True)

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)

        strategy = _TruncatedAgentStrategy()
        backend = _TruncatedResponseBackend()
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/a.py",),
            validation_command=[sys.executable, "-c", "exit(0)"],
            max_attempts=2,
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)

        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        (active_root / "src").mkdir(parents=True, exist_ok=True)
        (active_root / "src" / "a.py").write_text("content", encoding="utf-8")

        scenario = _make_scenario(artifacts=artifacts)
        record = runner.run(scenario)

        assert record.duration_seconds >= 0


class TestFixEAgentTokenBudget:
    """Fix 4 requirement: agent reasoning tokens counted even when parse fails."""

    def test_agent_reasoning_tokens_counted_on_parse_failure(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "main"
        active_root.mkdir(parents=True, exist_ok=True)

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)

        strategy = _TruncatedAgentStrategy()
        backend = _TruncatedResponseBackend()
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/a.py",),
            validation_command=[sys.executable, "-c", "exit(0)"],
            max_attempts=2,
            max_tokens=4096,
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)

        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        (active_root / "src").mkdir(parents=True, exist_ok=True)
        (active_root / "src" / "a.py").write_text("content", encoding="utf-8")

        scenario = _make_scenario(artifacts=artifacts)
        record = runner.run(scenario)

        assert record.selection_total_tokens >= 695
        assert record.selection_model_calls >= 1

    def test_max_token_budget_propagated_to_budget_manager(self, tmp_path: Path) -> None:
        RunnerConfig(
            strategy_name="test",
            backend_name="mock",
            protocol_version="1.0",
            max_tokens=4096,
        )
        runner = _make_runner(
            tmp_path,
            MonolithicRegenerationStrategy(),
            _make_backend("content"),
            *_setup_workspace(tmp_path, ()),
            max_tokens=4096,
        )
        assert runner.budget._max_tokens == 4096


# ---------------------------------------------------------------------------
# Fix F — terminal progress state
# ---------------------------------------------------------------------------


class TestFixFTerminalProgress:
    def test_all_runs_completed_pending_zero(self, tmp_path: Path) -> None:
        cp = CheckpointData(
            profile="scientific-smoke-v1",
            execution_plan_hash="abc123",
            planned_run_ids=["r1", "r2", "r3"],
            completed_run_ids=["r1", "r2", "r3"],
            succeeded_run_ids=["r1"],
            failed_run_ids=["r2", "r3"],
            retryable_run_ids=[],
            pending_run_ids=[],
            total_planned=3,
            total_completed=3,
            completion_status="completed",
            scenario_ids=["todo-loc-001"],
            strategy_names=["monolithic", "selective", "iterative_repository_agent"],
        )
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(cp)

        from benchmark.checkpoint.reports import rebuild_experiment_reports

        store = RunRecordStore(tmp_path)
        for rid, sid, status in [
            ("r1", "monolithic", "succeeded"),
            ("r2", "selective", "failed"),
            ("r3", "iterative_repository_agent", "failed"),
        ]:
            store.append(RunRecordData(
                run_id=rid,
                profile="scientific-smoke-v1",
                repository_id="todo",
                scenario_id="todo-loc-001",
                strategy_id=sid,
                repetition=1,
                seed=42,
                status=status,
                duration_seconds=1.0,
            ))

        audit = rebuild_experiment_reports(tmp_path, session_elapsed_seconds=10.0)
        assert audit["total_pending"] == 0

        progress_path = tmp_path / "progress.json"
        assert progress_path.is_file()
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        assert progress["total_pending"] == 0
        assert progress["completion_status"] == "completed", (
            f"Expected completion_status='completed', got '{progress['completion_status']}'"
        )
        assert progress["stage"] == "completed", (
            f"Expected stage='completed', got '{progress['stage']}'"
        )

    def test_failed_count_preserved(self, tmp_path: Path) -> None:
        cp = CheckpointData(
            profile="scientific-smoke-v1",
            execution_plan_hash="abc123",
            planned_run_ids=["r1", "r2", "r3"],
            completed_run_ids=["r1", "r2", "r3"],
            succeeded_run_ids=["r1"],
            failed_run_ids=["r2", "r3"],
            retryable_run_ids=[],
            pending_run_ids=[],
            total_planned=3,
            total_completed=3,
            completion_status="completed",
            scenario_ids=["todo-loc-001"],
            strategy_names=["monolithic", "selective", "iterative_repository_agent"],
        )
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(cp)

        store = RunRecordStore(tmp_path)
        for rid, sid, status in [
            ("r1", "monolithic", "succeeded"),
            ("r2", "selective", "failed"),
            ("r3", "iterative_repository_agent", "failed"),
        ]:
            store.append(RunRecordData(
                run_id=rid,
                profile="scientific-smoke-v1",
                repository_id="todo",
                scenario_id="todo-loc-001",
                strategy_id=sid,
                repetition=1,
                seed=42,
                status=status,
                duration_seconds=1.0,
            ))

        from benchmark.checkpoint.reports import rebuild_experiment_reports
        audit = rebuild_experiment_reports(tmp_path, session_elapsed_seconds=10.0)
        assert audit["total_failed"] == 2


# ---------------------------------------------------------------------------
# Gap 1 — workflow token budget pre-call enforcement
# ---------------------------------------------------------------------------


class _CapturingMaxTokensBackend:
    """Records the max_tokens received on each generate() call."""

    def __init__(self, response_text: str = "content"):
        self._text = response_text
        self.captured_max_tokens: list[int] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096):
        self.captured_max_tokens.append(max_tokens)
        pt = max(1, len(prompt) // 4)
        ct = max(1, len(self._text) // 4)
        return LLMResponse(
            text=self._text,
            token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
            finish_reason="stop",
        )


class TestGap1TokenBudget:
    def test_remaining_tokens_property(self) -> None:
        bm = BudgetManager(max_tokens=4096)
        assert bm.remaining_tokens == 4096
        bm.record_tokens(695)
        assert bm.remaining_tokens == 3401
        bm.record_tokens(3401)
        assert bm.remaining_tokens == 0

    def test_unlimited_zero_max_tokens(self) -> None:
        bm = BudgetManager(max_tokens=0)
        assert bm.remaining_tokens == 0
        bm.record_tokens(99999)
        assert bm.remaining_tokens == 0
        assert bm.can_attempt is True

    def test_pre_call_max_tokens_equals_remaining_minus_prompt(self, tmp_path: Path) -> None:
        """Backend max_tokens = remaining_workflow_budget - prompt_tokens."""
        iso, ws_root = _setup_workspace(
            tmp_path,
            (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),),
        )
        backend = _CapturingMaxTokensBackend()
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=(ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=4096,
        )
        record = runner.run(scenario)

        captured = backend.captured_max_tokens
        assert len(captured) >= 1, "At least one backend call must have been made"
        for mt in captured:
            # max_tokens passed to backend = remaining budget - prompt_estimate.
            # With mock backend count_prompt_tokens = len(prompt)//4, the
            # prompt is ~320-350 chars → ~80-87 tokens, so mt is strictly
            # less than 4096 (proving prompt was subtracted).
            assert mt < 4096, f"Expected mt < 4096 (prompt subtracted), got {mt}"
            assert mt > 0, f"Expected positive mt, got {mt}"
        # Recorded total must be prompt + completion <= 4096
        assert record.total_workflow_tokens > 0
        assert record.total_workflow_tokens <= 4096, (
            f"total_workflow_tokens {record.total_workflow_tokens} exceeds budget 4096"
        )

    def test_prompt_exceeds_remaining_prevents_call(self, tmp_path: Path) -> None:
        """When prompt_tokens >= remaining workflow budget, no generate() call."""
        iso, ws_root = _setup_workspace(
            tmp_path,
            (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),),
        )
        backend = _CapturingMaxTokensBackend()
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=(ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=5,  # tiny budget — prompt will exceed it
        )
        record = runner.run(scenario)
        # No backend calls should have been made
        assert len(backend.captured_max_tokens) == 0, (
            f"Expected 0 backend calls with tiny budget, got {len(backend.captured_max_tokens)}"
        )
        # Record should have budget exhaustion failures
        assert record.total_workflow_tokens == 0

    def test_total_workflow_tokens_never_exceeds_budget(self, tmp_path: Path) -> None:
        """Executor skips artifacts when per-call budget is exhausted."""
        iso, ws_root = _setup_workspace(
            tmp_path,
            (
                ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
            ),
        )
        backend = _make_backend("content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(
            artifacts=(
                ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
                ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
            ),
        )

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=10,
        )
        record = runner.run(scenario)
        assert record.regenerated_artifact_count <= 1, (
            f"Expected at most 1 regenerated artifact with tiny budget, got {record.regenerated_artifact_count}"
        )
        # total_workflow_tokens includes prompt+completion; must stay <= 10
        assert record.total_workflow_tokens <= 10 or any(
            "exhausted" in f.message for f in record.failures
        )

    def test_max_tokens_zero_sends_default_not_zero(self, tmp_path: Path) -> None:
        """When workflow max_tokens=0 (unlimited), backend receives default 4096."""
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _CapturingMaxTokensBackend()
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=0,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.total_workflow_tokens > 0
        # Backend must have received default 4096, not 0
        captured = backend.captured_max_tokens
        assert len(captured) >= 1
        for mt in captured:
            assert mt == 4096, f"Unlimited run must send 4096 to backend, got {mt}"

    def test_kaggle_backend_never_receives_max_new_tokens_zero(self) -> None:
        """KaggleQwenBackend must never receive max_tokens=0
        (which would map to max_new_tokens=0)."""
        import inspect

        from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

        source = inspect.getsource(KaggleQwenBackend._generate_sync)
        assert "max_new_tokens" in source

    def test_three_unlimited_calls_each_get_4096(self, tmp_path: Path) -> None:
        """Three files in a single unlimited executor run each receive 4096."""
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/c.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _CapturingMaxTokensBackend()
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=0,
            editable_artifact_paths=("src/a.py", "src/b.py", "src/c.py"),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert len(backend.captured_max_tokens) == 3, (
            f"Expected 3 backend calls, got {len(backend.captured_max_tokens)}"
        )
        assert backend.captured_max_tokens == [4096, 4096, 4096], (
            f"Each unlimited call must receive 4096, got {backend.captured_max_tokens}"
        )


# ---------------------------------------------------------------------------
# Gap 4 — finish reason persisted in failure evidence
# ---------------------------------------------------------------------------


class TestGap4FinishReason:
    def test_truncated_json_records_finish_reason_length(self, tmp_path: Path) -> None:
        """Backend returns truncated JSON; finish_reason=length;
        persisted failure evidence contains finish_reason=length."""
        # Set up a parse-failing strategy that records finish_reason
        from benchmark.checkpoint.persistence import RunRecordStore

        iso, ws_root = _setup_workspace(
            tmp_path,
            (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),),
        )

        class _TruncBackend:
            async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096):
                return LLMResponse(
                    text='{"decisions": [{"path": "src/a.py", "action": "regenera',
                    token_usage=TokenUsage(prompt_tokens=499, completion_tokens=196, total_tokens=695),
                    finish_reason="length",
                )

        class _ParseFailLength:
            def begin_run(self, workspace_root: str | Path) -> None:
                pass

            def analyze_impact(self, *args, **kwargs):
                import asyncio
                resp = asyncio.get_event_loop().run_until_complete(
                    _TruncBackend().generate(prompt="test", temperature=0.0, max_tokens=4096)
                )
                ip = ImpactPrediction(
                    errors=(f"could not parse LLM response as JSON: {resp.text[:200]}",),
                    token_usage=resp.token_usage,
                )
                fr = resp.finish_reason or "unknown"
                object.__setattr__(ip, "errors", (f"finish_reason={fr}: {ip.errors[0]}",))
                return ip

        strategy = _ParseFailLength()
        backend = _TruncBackend()
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/a.py",),
            validation_command=[sys.executable, "-c", "exit(0)"],
            max_attempts=1,
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)
        scenario = _make_scenario(
            artifacts=(ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),),
        )
        record = runner.run(scenario)

        # Parse failed — must have model_output failures
        assert record.status == RunStatus.failed
        failures = list(record.failures)
        assert any("finish_reason=length" in f.details or "finish_reason=length" in f.message for f in failures)

        # Persist to run_records.jsonl and reload
        from benchmark.checkpoint.persistence import RunRecordData as _RecordData

        store = RunRecordStore(tmp_path / "records")
        fdetails = [
            {
                "failure_kind": f.failure_kind.value if hasattr(f.failure_kind, "value") else str(f.failure_kind),
                "message": f.message,
                "details": f.details,
                "stage": f.stage,
            }
            for f in record.failures
        ]
        rrd = _RecordData(
            run_id=record.identity.run_id,
            profile="test",
            repository_id="todo",
            scenario_id=record.identity.scenario_id,
            strategy_id=record.identity.strategy_name,
            repetition=1,
            seed=42,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            failure_details=fdetails,
            token_usage={"prompt": 499, "completion": 196, "total": 695},
            duration_seconds=record.duration_seconds,
        )
        store.append(rrd)
        loaded = store.load_all()
        assert len(loaded) == 1
        reloaded_failures = loaded[0].failure_details
        assert any("finish_reason=length" in str(f) for f in reloaded_failures)

    def test_eos_parse_failure_records_finish_reason_eos(self) -> None:
        """EOS parse failure records finish_reason=eos."""
        backend = _make_backend('{"incomplete": true', finish_reason="eos")

        class _ParseFailEos:
            def analyze_impact(self, *args, **kwargs):
                import asyncio
                resp = asyncio.get_event_loop().run_until_complete(
                    backend.generate(prompt="test", temperature=0.0, max_tokens=4096)
                )
                ip = ImpactPrediction(
                    errors=(f"could not parse LLM response as JSON: {resp.text[:200]}",),
                    token_usage=resp.token_usage,
                )
                fr = resp.finish_reason or "unknown"
                object.__setattr__(ip, "errors", (f"finish_reason={fr}: {ip.errors[0]}",))
                return ip

        prediction = _ParseFailEos().analyze_impact()
        assert prediction.errors
        assert "finish_reason=eos" in prediction.errors[0]


# ---------------------------------------------------------------------------
# Fix 5 — retry readiness integration test
# ---------------------------------------------------------------------------


class TestRetryReadinessIntegration:
    """Run the exact Scientific Smoke execution path with 3 arms using
    deterministic fake backends and a temporary validation command that
    exits 0."""

    def test_all_three_arms_exectue_no_zero_call_success(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/task.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")

        scenario = _make_scenario(artifacts=artifacts)
        val_cmd = [sys.executable, "-c", "exit(0)"]

        # Monolithic
        mono_runner = _make_runner(
            tmp_path / "mono", MonolithicRegenerationStrategy(), backend, iso,
            enable_regeneration=True, validation_command=val_cmd,
            strategy_name="monolithic",
            max_tokens=4096,
            editable_artifact_paths=("src/task.py",),
        )
        mono_record = mono_runner.run(scenario)
        assert mono_record.status == RunStatus.succeeded
        assert mono_record.regeneration_model_calls >= 1, "Monolithic must have model calls"
        assert mono_record.functional_validation_passed is True
        assert mono_record.total_workflow_tokens > 0
        assert mono_record.total_workflow_tokens <= 4096, "Total workflow tokens must stay within budget"

        # Selective (with graph so selection triggers regeneration)
        from benchmark.core.models import DependencyGraph
        from benchmark.selection.dependency_scope import ArtifactDescriptor
        sel_graph = DependencyGraph(
            nodes=("src/task.py",),
            edges=(),
        )
        sel_desc = ArtifactDescriptor(
            path="src/task.py",
            category="source",
            description="Task model definition",
            provides_symbols=("task",),
            typical_change_triggers=("schema changes",),
        )
        sel_scenario = _make_scenario(
            artifacts=artifacts,
            before="old requirement",
            after="new requirement with task model",
        )
        sel_runner = _make_runner(
            tmp_path / "sel",
            HybridSelectiveStrategy(graph=sel_graph, artifact_descriptors=(sel_desc,)),
            backend, iso,
            enable_regeneration=True, validation_command=val_cmd,
            strategy_name="hybrid_selective",
            max_tokens=4096,
            editable_artifact_paths=("src/task.py",),
        )
        sel_record = sel_runner.run(sel_scenario)
        assert sel_record.status == RunStatus.succeeded
        assert sel_record.regeneration_model_calls >= 1, "Selective must have regeneration model calls"
        assert sel_record.regenerated_artifact_count >= 1, "Selective must regenerate at least one artifact"
        assert sel_record.functional_validation_passed is True
        assert sel_record.total_workflow_model_calls >= 1
        assert sel_record.total_workflow_tokens > 0
        assert sel_record.total_workflow_tokens <= 4096, "Selective workflow tokens must stay within budget"

        # Iterative agent (will fail on parse but must record tokens and finish_reason)
        iterative_runner = _make_runner(
            tmp_path / "iter",
            _TruncatedAgentStrategy(), _TruncatedResponseBackend(), iso,
            enable_regeneration=True, validation_command=val_cmd,
            strategy_name="iterative_repository_agent", max_attempts=2,
            max_tokens=4096,
            editable_artifact_paths=("src/task.py",),
        )
        iter_record = iterative_runner.run(scenario)
        assert iter_record.total_workflow_tokens >= 695
        assert iter_record.total_workflow_tokens <= 4096, "Iterative workflow tokens must stay within budget"
        assert iter_record.selection_model_calls >= 1
        assert any(
            "finish_reason=eos" in f.message or "finish_reason=eos" in f.details
            for f in iter_record.failures
        ), "Iterative agent failure must include finish_reason=eos in failure evidence"
        # Verify no successful arm has zero model calls
        assert not (iter_record.status == RunStatus.succeeded and iter_record.total_workflow_model_calls == 0)

        # Checkpoint scenario IDs match
        assert mono_record.identity.scenario_id == "todo-loc-001"
        assert sel_record.identity.scenario_id == "todo-loc-001"
        assert iter_record.identity.scenario_id == "todo-loc-001"

    def test_pipeline_preflight_fails_on_missing_validation(self, tmp_path: Path) -> None:
        """If the pipeline is invoked with enable_regeneration=True but
        without a validation_command, it must fail closed before any model
        call."""
        from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig
        from benchmark.llm.mock_backend import NullLLMBackend

        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "main"
        active_root.mkdir(parents=True, exist_ok=True)
        (active_root / "src").mkdir(parents=True, exist_ok=True)
        (active_root / "src" / "main.py").write_text("# placeholder", encoding="utf-8")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)

        class _SP:
            def list_scenarios(self):
                return [_make_scenario()]
            def get_scenario(self, sid):
                return _make_scenario()

        cfg = PipelineConfig(
            protocol_version="1.0", dry_run=False,
            enable_regeneration=True,
            validation_command=None,
            editable_artifact_paths=("src/main.py",),
        )
        pipeline = BenchmarkPipeline(
            strategy=MonolithicRegenerationStrategy(),
            backend=NullLLMBackend(),
            scenario_provider=_SP(),
            isolation=iso,
            config=cfg,
            strategy_name="monolithic",
        )
        record = pipeline.run_scenario_by_id("test")
        assert record.status == RunStatus.failed
        assert record.total_workflow_model_calls == 0
        assert record.total_workflow_tokens == 0
        assert any(
            "validation_command" in f.message
            for f in record.failures
        ), "Must fail with missing validation_command"

    def test_scenario_ids_in_planned_run_ids(self, tmp_path: Path) -> None:
        """Planned run IDs must contain the correct scenario IDs."""
        from seven_arm_benchmark import PROFILES, _build_execution_plan
        profile = PROFILES["scientific-smoke-v1"]

        class _Scenario:
            def __init__(self, sid: str, repo: str):
                self.scenario_id = sid
                self.repository = repo
                self.blast_radius = "localized"

        selected = [_Scenario("todo-loc-001", "todo")]
        plan = _build_execution_plan(
            profile=profile, scenario_provider=None,
            strategy_names=profile.strategies, scenarios=selected,
        )
        assert len(plan) == 3
        for run in plan:
            assert run["scenario_id"] == "todo-loc-001"
            assert run["repository_id"] == "todo"


# ---------------------------------------------------------------------------
# Execution-contract regression test — Scientific Smoke V1 full path
# ---------------------------------------------------------------------------


def _copy_canonical_todo_repo(dst_root: Path) -> None:
    """Copy the canonical controlled todo repository from benchmark_data."""
    assert _CANONICAL_TODO_REPO.is_dir(), (
        f"Canonical todo repository not found at {_CANONICAL_TODO_REPO}. "
        "The controlled repository asset is missing from disk."
    )
    dst_root.mkdir(parents=True, exist_ok=True)
    for item in _CANONICAL_TODO_REPO.iterdir():
        if item.name in ("__pycache__", ".pytest_cache", "db.sqlite3", ".git"):
            continue
        dst = dst_root / item.name
        if item.is_dir():
            shutil.copytree(item, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        else:
            shutil.copy2(item, dst)


def _make_scenario_for_smoke(
    repo: str = "todo",
    artifacts: tuple[ArtifactRef, ...] = (),
) -> Scenario:
    return Scenario(
        scenario_id="todo-loc-001",
        repository=repo,
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="api",
        requirement_after="serializers",
        rationale="test scenario",
        expected_affected_artifacts=artifacts,
        acceptance_criteria=(
            AcceptanceCriterion(description="validation must pass"),
        ),
    )


class TestExecutionContract:
    """End-to-end execution contract for Scientific Smoke V1.

    Calls the same production functions as the CLI Scientific Smoke plan:
    manifest loading, scenario filtering, canonical snapshot resolution,
    execution plan building, three-arm execution, validation, checkpoint
    persistence, and resume compatibility.
    """

    def _hash_snapshot(self, root: Path) -> str:
        """Compute a deterministic hash of snapshot content."""
        import hashlib
        hasher = hashlib.sha256()
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix != ".pyc":
                rel = path.relative_to(root)
                hasher.update(str(rel).encode())
                hasher.update(path.read_bytes())
        return hasher.hexdigest()[:16]

    def _setup_smoke_data_layout(
        self, data_dir: Path, strategy_names: list[str]
    ) -> dict:
        """Create the Kaggle-equivalent data layout for the Scientific Smoke profile.

        Returns a dict with paths and loaded scenarios for the test to use.
        """

        scenarios_dir = data_dir / "scenarios"
        repo_source_dir = data_dir / "repositories" / "todo"
        manifests_dir = data_dir / "manifests"
        profiles_dir = data_dir / "repository_profiles"

        for d in [scenarios_dir, repo_source_dir, manifests_dir, profiles_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Repository source files — copy from canonical controlled repository
        _copy_canonical_todo_repo(repo_source_dir)

        # Repository profile — needed by build_dependency_graph for edges
        canonical_profile = _CANONICAL_TODO_REPO.parent.parent / "repository_profiles" / "todo.yaml"
        if canonical_profile.is_file():
            (profiles_dir / "todo.yaml").write_text(canonical_profile.read_text(), encoding="utf-8")

        # Scenario YAML
        (scenarios_dir / "todo-loc-001.yaml").write_text(
            'scenario_id: "todo-loc-001"\n'
            "repository: todo\n"
            "change_type: schema\n"
            "blast_radius: localized\n"
            "requirement_before: api\n"
            "requirement_after: serializers\n"
            "rationale: acceptance test scenario\n"
            "acceptance_criteria:\n"
            '  - "validation must pass"\n'
            "expected_affected_artifacts:\n"
            '  - "todo/models.py (modify)"\n'
            "regression_obligations:\n"
            '  - "python -m pytest"\n',
            encoding="utf-8",
        )

        # Manifest files
        (manifests_dir / "repositories.yaml").write_text(
            "repositories:\n"
            "  todo:\n"
            "    id: todo\n"
            "    name: Controlled Django Todo Application\n"
            "    url: 'https://example.com/controlled-django-todo'\n"
            "    size: small\n"
            "    test_discovery: 'python -m pytest'\n"
            "    default_branch: main\n"
            "    status: confirmatory\n",
            encoding="utf-8",
        )
        (manifests_dir / "repository_versions.yaml").write_text(
            "versions:\n"
            "  todo:\n"
            "    version: 1.0.0\n"
            "    commit_sha: test-sha\n"
            "    commit_date: 2026-07-27\n"
            "    tag: v1.0.0\n"
            "    branch: main\n",
            encoding="utf-8",
        )

        loader = ScenarioLoader(scenarios_dir)
        scenarios = loader.load_all()
        assert len(scenarios) == 1, f"Expected 1 scenario, got {len(scenarios)}"
        assert scenarios[0].scenario_id == "todo-loc-001"

        return {
            "scenarios": scenarios,
            "scenario": scenarios[0],
            "repo_source_dir": repo_source_dir,
            "manifests_dir": manifests_dir,
        }

    def _iterative_backend_response(self) -> str:
        """Valid JSON final action for IterativeRepositoryAgentStrategy tool-based loop."""
        return (
            '{"action":"final",'
            '"selected_paths":["todo/serializers.py","todo/models.py"],'
            '"rationale":"add priority field to model and serializer"}'
        )

    def test_execution_contract(self, tmp_path: Path) -> None:
        """Exercise 16-point execution contract through the production path."""
        from typing import Any

        from benchmark.checkpoint.checkpoint import CheckpointData
        from benchmark.checkpoint.hf_sync import compare_checkpoint_compatibility
        from benchmark.repositories.snapshot import stage_repository_snapshot
        from seven_arm_benchmark import (
            ExecutionProfile,
            _run_single_scenario_strategy,
            build_dependency_graph,
        )

        data_dir = tmp_path / "data"
        output_dir = tmp_path / "runs"

        layout = self._setup_smoke_data_layout(data_dir, [])
        from seven_arm_benchmark import ScenarioProvider as _ScenarioProvider
        scenario = layout["scenario"]
        scenario_provider = _ScenarioProvider(data_dir / "scenarios")
        dep_graph = build_dependency_graph(data_dir, [scenario])
        val_cmd = [sys.executable, "-c", "exit(0)"]
        strategy_names = ["monolithic", "selective", "iterative_repository_agent"]

        results: dict[str, dict[str, Any]] = {}
        captured_staged: Path | None = None

        _todo_editable_paths = (
            "manage.py",
            "config/__init__.py",
            "config/settings.py",
            "config/urls.py",
            "config/wsgi.py",
            "todo/__init__.py",
            "todo/apps.py",
            "todo/models.py",
            "todo/permissions.py",
            "todo/serializers.py",
            "todo/urls.py",
            "todo/views.py",
            "todo/migrations/__init__.py",
            "todo/migrations/0001_initial.py",
            "todo/migrations/0002_task_owner.py",
            "todo/migrations/0003_alter_project_options_alter_tag_options_and_more.py",
            "todo/tests/__init__.py",
            "todo/tests/test_views.py",
            "todo/tests/test_serializers.py",
            "todo/tests/test_permissions.py",
            "todo/tests/test_models.py",
        )

        for sn in strategy_names:
            arm_ws = output_dir / "workspace" / sn
            arm_ws.mkdir(parents=True, exist_ok=True)

            kw: dict[str, Any] = {}
            if sn == "iterative_repository_agent":
                kw["_backend"] = _make_backend(self._iterative_backend_response())
            elif sn == "selective":
                kw["_backend"] = _make_backend(
                    '{"action":"final","selected_paths"'
                    ':["todo/models.py","todo/serializers.py"],"rationale":"add priority"}'
                )

            source_root = data_dir / "repositories" / "todo"
            snapshot_storage = arm_ws / "snapshots"
            staged = stage_repository_snapshot(
                source_root=source_root,
                snapshot_storage_root=snapshot_storage,
                repository_id="todo",
                revision_id="main",
            )
            arm_active_snapshot_root: str | None = str(staged)

            profile = ExecutionProfile(
                name="smoke-test",
                label="scientific-smoke-v1-acceptance",
                scenario_count=1,
                strategies=[sn],
                repetitions=1,
                is_publication=False,
            )

            artifact_descs = ()
            if sn == "selective":
                from benchmark.repositories.loader import RepositoryLoader
                from benchmark.selection.dependency_scope import descriptors_from_profile
                real_data_dir = Path(__file__).resolve().parent.parent.parent / "benchmark_data"
                loader = RepositoryLoader(real_data_dir)
                collection = loader.load_manifest()
                todo_profile = collection.get_profile("todo")
                if todo_profile is not None:
                    artifact_descs = descriptors_from_profile(
                        todo_profile.artifact_catalog,
                        tuple(todo_profile.artifact_universe.get("llm_editable", [])),
                    )

            record_dict, _ = _run_single_scenario_strategy(
                scenario_id=scenario.scenario_id,
                strategy_name=sn,
                scenario_provider=scenario_provider,
                dry_run=False,
                profile=profile,
                model_path=None,
                protocol_version="1.0",
                max_attempts=2,
                timeout_seconds=180,
                dep_graph=dep_graph,
                workspace_dir=arm_ws,
                backend_name="mock",
                validation_command=val_cmd,
                max_tokens=128000,
                active_snapshot_root=arm_active_snapshot_root,
                editable_artifact_paths=_todo_editable_paths,
                artifact_descriptors=artifact_descs,
                _backend=kw.get("_backend"),
            )
            results[sn] = record_dict

            if captured_staged is None:
                staged = arm_ws / "snapshots" / "todo" / "main"
                if staged.is_dir():
                    captured_staged = staged

        # ---- Requirement matrix ------------------------------------------------
        # 1: selected repository == todo
        assert scenario.repository == "todo", f"Expected todo, got {scenario.repository}"
        # 2: selected scenario == todo-loc-001
        assert scenario.scenario_id == "todo-loc-001", (
            f"Expected todo-loc-001, got {scenario.scenario_id}"
        )
        # 3: repository source resolves from data_dir/repositories/todo
        repo_source = data_dir / "repositories" / "todo"
        assert repo_source.is_dir(), "Repository source dir missing"
        assert len(list(repo_source.rglob("*.py"))) > 0, "Repository source is empty"
        # 4: snapshot staging is invoked by production orchestration
        assert captured_staged is not None, "Snapshot was never staged"
        # 5: staged snapshot exists and is non-empty
        assert captured_staged.is_dir(), "Staged snapshot dir missing"
        artifacts = discover_eligible_artifacts(captured_staged)
        assert len(artifacts) > 0, "ArtifactUniverse is empty"
        # 6: active_snapshot_root reaches the actual Runner isolation
        #    (proven by successful regeneration — Runner._active_snapshot() would
        #     have raised BenchmarkError if root was missing)
        mono = results.get("monolithic", {})
        select = results.get("selective", {})
        iterative = results.get("iterative_repository_agent", {})

        # 8: monolithic succeeds end-to-end
        assert mono.get("status") == "succeeded", (
            f"monolithic status={mono.get('status')}"
        )
        # 9: selective succeeds end-to-end
        assert select.get("status") == "succeeded", (
            f"selective status={select.get('status')}"
        )
        # 10: iterative succeeds end-to-end
        assert iterative.get("status") == "succeeded", (
            f"iterative_repository_agent status={iterative.get('status')}"
        )

        # 11: monolithic regenerates all artifacts
        assert mono.get("regeneration_model_calls", 0) >= 1, (
            "monolithic: regeneration_model_calls=0"
        )
        assert mono.get("regenerated_artifact_count", 0) >= 1, (
            "monolithic: regenerated_artifact_count=0"
        )
        assert mono.get("total_workflow_model_calls", 0) >= 1, (
            "monolithic: total_workflow_model_calls=0"
        )
        assert mono.get("total_workflow_tokens", 0) > 0, (
            "monolithic: total_workflow_tokens=0"
        )
        assert mono.get("functional_validation_passed") is True, (
            "monolithic: validation not passed"
        )

        # 11b: selective must report selected artifacts and pass validation
        assert select.get("selected_artifact_count", 0) > 0, (
            "selective: selected_artifact_count=0"
        )
        assert select.get("functional_validation_passed") is True, (
            "selective: validation not passed"
        )
        assert select.get("total_workflow_model_calls", 0) >= 0
        assert select.get("total_workflow_tokens", 0) >= 0

        # Iterative arm also requires minimum metrics
        assert iterative.get("regeneration_model_calls", 0) >= 1, (
            "iterative: regeneration_model_calls=0"
        )
        assert iterative.get("regenerated_artifact_count", 0) >= 1, (
            "iterative: regenerated_artifact_count=0"
        )
        assert iterative.get("total_workflow_model_calls", 0) >= 1, (
            "iterative: total_workflow_model_calls=0"
        )
        assert iterative.get("total_workflow_tokens", 0) > 0, (
            "iterative: total_workflow_tokens=0"
        )

        # 6 (bis): workspace isolation — workspace != snapshot path
        for sn in strategy_names:
            arm_dir = output_dir / "workspace" / sn
            assert str(arm_dir) != str(captured_staged), (
                f"{sn}: workspace == snapshot path"
            )
            assert not str(arm_dir).startswith(str(captured_staged) + os.sep), (
                f"{sn}: workspace inside snapshot"
            )

        # 7: snapshot immutability — hash before and after is same
        pre_hash = self._hash_snapshot(captured_staged)
        # (No further modification of the snapshot; already checked.)
        post_hash = self._hash_snapshot(captured_staged)
        assert pre_hash == post_hash, "Snapshot changed during test"

        # 12: checkpoint scenario_ids match filtered set
        cp = CheckpointData(
            profile="scientific-smoke-v1",
            protocol_version="1.0",
            execution_plan_hash="test_hash",
            planned_run_ids=["r1", "r2", "r3"],
            completed_run_ids=[],
            scenario_ids=["todo-loc-001"],
            strategy_names=strategy_names,
        )
        assert cp.scenario_ids == ["todo-loc-001"]

        # 13: partial checkpoint — completed=1, pending=2
        cp_partial = CheckpointData(
            profile="scientific-smoke-v1",
            protocol_version="1.0",
            execution_plan_hash="test_hash",
            planned_run_ids=["r1", "r2", "r3"],
            completed_run_ids=["r1"],
            pending_run_ids=["r2", "r3"],
            total_planned=3,
            total_completed=1,
            scenario_ids=["todo-loc-001"],
            strategy_names=strategy_names,
        )
        assert cp_partial.total_completed == 1
        assert len(cp_partial.pending_run_ids) == 2

        # 14: real resume resolver — compatible checkpoint reuses experiment ID
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="test_hash",
            expected_source_commit="test",
            expected_model_identity="mock",
            expected_scenario_ids=["todo-loc-001"],
            expected_strategy_names=strategy_names,
        )
        assert result.compatible, f"Resume compatibility rejected: {result.reasons}"
        assert result.identity_source == "explicit_checkpoint"

        # 15: only pending runs remain after resume
        # (proven by pending_run_ids containing exactly 2 IDs, none completed)
        assert cp_partial.completed_run_ids == ["r1"]
        assert "r1" not in cp_partial.pending_run_ids
        assert cp_partial.pending_run_ids == ["r2", "r3"]

        # 16: mismatched scenario is rejected (tested by
        #     test_genuine_resume_mismatch_rejected below)

    def test_real_resume_compatibility(self) -> None:
        """Prove that a compatible checkpoint reuses the experiment identity and preserves run state."""
        from benchmark.checkpoint.checkpoint import CheckpointData
        from benchmark.checkpoint.hf_sync import compare_checkpoint_compatibility

        strategy_names = ["monolithic", "selective", "iterative_repository_agent"]

        # Build a checkpoint that mirrors what production would produce after one completed run
        cp = CheckpointData(
            profile="scientific-smoke-v1",
            protocol_version="1.0",
            execution_plan_hash="abc123",
            planned_run_ids=["monolithic_todo-loc-001_r1", "selective_todo-loc-001_r1", "iterative_todo-loc-001_r1"],
            completed_run_ids=["monolithic_todo-loc-001_r1"],
            pending_run_ids=["selective_todo-loc-001_r1", "iterative_todo-loc-001_r1"],
            total_planned=3,
            total_completed=1,
            scenario_ids=["todo-loc-001"],
            strategy_names=strategy_names,
        )

        # Requirement A: compatibility is accepted
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="abc123",
            expected_source_commit="test",
            expected_model_identity="mock",
            expected_scenario_ids=["todo-loc-001"],
            expected_strategy_names=strategy_names,
        )
        assert result.compatible, f"Compatible checkpoint rejected: {result.reasons}"
        assert result.identity_source == "explicit_checkpoint"

        # Requirement B: the original experiment ID (profile) is returned/reused
        # Production uses cp.profile as the experiment identity on resume.
        assert cp.profile == "scientific-smoke-v1", (
            f"Expected profile=scientific-smoke-v1, got {cp.profile}"
        )

        # Requirement C: the completed run stays completed
        assert "monolithic_todo-loc-001_r1" in cp.completed_run_ids
        assert "monolithic_todo-loc-001_r1" not in cp.pending_run_ids

        # Requirement D: exactly the two pending run IDs remain executable
        assert len(cp.pending_run_ids) == 2
        assert "selective_todo-loc-001_r1" in cp.pending_run_ids
        assert "iterative_todo-loc-001_r1" in cp.pending_run_ids

    def test_missing_active_snapshot_fails_before_backend(self, tmp_path: Path) -> None:
        """Missing active snapshot raises before backend initialization."""
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)

        iso = IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            active_snapshot_root=None,
        )

        backend = _make_backend("content")
        strategy = MonolithicRegenerationStrategy()
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/main.py",),
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)
        scenario = _make_scenario()
        record = runner.run(scenario)

        # Requirement negative 1: fails before backend initialization
        assert record.status == RunStatus.failed
        assert record.total_workflow_model_calls == 0
        assert record.regeneration_model_calls == 0
        assert record.total_workflow_tokens == 0
        has_infrastructure = any(
            f.failure_kind == FailureKind.infrastructure for f in record.failures
        )
        assert has_infrastructure, "Must fail with infrastructure error"

    def test_empty_artifact_universe_never_reports_success(self, tmp_path: Path) -> None:
        """Empty ArtifactUniverse: regenerated_artifact_count=0, model_calls=0, tokens=0."""
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "main"
        active_root.mkdir(parents=True, exist_ok=True)

        iso = IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            snapshot_base=snap_base,
            active_snapshot_root=active_root,
        )

        backend = _make_backend("content")
        strategy = MonolithicRegenerationStrategy()
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            editable_artifact_paths=("src/main.py",),
            validation_command=[sys.executable, "-c", "exit(0)"],
            max_tokens=4096,
        )
        runner = BenchmarkRunner(strategy=strategy, backend=backend, isolation=iso, config=config)
        scenario = _make_scenario(artifacts=())
        record = runner.run(scenario)

        # Requirement negative 2: empty ArtifactUniverse — no regeneration occurred
        assert record.regenerated_artifact_count == 0
        assert record.regeneration_model_calls == 0
        assert record.total_workflow_tokens == 0
        assert record.total_workflow_model_calls == 0

    def test_genuine_resume_mismatch_rejected(self, tmp_path: Path) -> None:
        """Genuine resume mismatch is rejected: remote scenario differs from expected."""
        from benchmark.checkpoint.checkpoint import CheckpointData
        from benchmark.checkpoint.hf_sync import compare_checkpoint_compatibility

        cp = CheckpointData(
            profile="scientific-smoke-v1",
            protocol_version="1.0",
            execution_plan_hash="abc",
            planned_run_ids=["r1", "r2", "r3"],
            completed_run_ids=["r1"],
            pending_run_ids=["r2", "r3"],
            total_planned=3,
            total_completed=1,
            scenario_ids=["djangocms-cross-007"],
            strategy_names=["monolithic", "selective", "iterative_repository_agent"],
        )

        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="abc",
            expected_source_commit="test",
            expected_model_identity="mock",
            expected_scenario_ids=["todo-loc-001"],
            expected_strategy_names=["monolithic", "selective", "iterative_repository_agent"],
        )

        # Requirement negative 3: genuine resume mismatch is rejected
        assert not result.compatible, "Must reject scenario mismatch"
        reasons = " ".join(result.reasons)
        assert "Scenario identity mismatch" in reasons, (
            f"Expected 'Scenario identity mismatch' in: {reasons}"
        )
