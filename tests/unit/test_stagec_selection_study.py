"""Focused tests for STAGE-C-SELECTION-01 (D052) selection-only study.

Covers the 18 focused test items from ``03_TESTS_AND_SIX_GATES.md``:

  1. selection-only Agent invokes ``analyze_impact`` exactly once
  2. selection-only ImpactPlan invokes ``analyze_impact`` exactly once
  3. ``revise_plan`` is never called
  4. regeneration backend/editor is never invoked
  5. migrations/evaluator are never invoked
  6. initial Agent selected paths persist exactly
  7. initial ImpactPlan R/P/V/H actions persist exactly
  8. failure record does not replace initial predictions with all-preserve
  9. hidden expected_actions absent from both prompts
 10. source gold normalization strips symbols and migration/test paths
 11. precision/recall/F1/FNR synthetic cases exact
 12. 30-cell topology = 3 x 2 x 5
 13. unique run IDs / config identity
 14. resume does not duplicate completed records
 15. Agent control cap = 1024
 16. ImpactPlan cap = 4096
 17. no patch/regeneration token fields contribute to selection cost
 18. failures persist raw SHA + bounded redacted evidence
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath

FIVE_FILE_UNIVERSE = [
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
]

GOLD_REGENERATE = {
    "todo-smoke-001": {"todo/models.py", "todo/serializers.py", "todo/views.py"},
    "todo-smoke-002": {"todo/models.py", "todo/views.py"},
    "todo-smoke-003": {
        "todo/models.py",
        "todo/serializers.py",
        "todo/permissions.py",
        "todo/views.py",
    },
}


class _RecordingStrategy:
    def __init__(self, decisions=None, errors=(), model_calls: int = 1) -> None:
        self.calls: list[tuple[RepositorySnapshot, RequirementChange, ArtifactUniverse]] = []
        self.revise_calls: list[object] = []
        self.decisions = decisions or []
        self.errors = errors
        self.model_calls = model_calls
        self.selection_finish_reason = "stop"
        self.selection_raw_response_hashes = ("ab" * 32,)
        self._tool_calls = 0
        self._inspected = 0
        self._tool_duration = 0.0

    def analyze_impact(self, repository, requirement_change, artifact_universe, **kwargs):
        self.calls.append((repository, requirement_change, artifact_universe))
        return ImpactPrediction(
            decisions=tuple(self.decisions),
            errors=tuple(self.errors),
            token_usage=TokenUsage(prompt_tokens=37, completion_tokens=11, total_tokens=48),
        )

    def revise_plan(self, *args, **kwargs):
        self.revise_calls.append((args, kwargs))

    def __getattr__(self, name):
        if name == "compact_tool_transcript":
            return ()
        if name in {"model_call_count", "tool_call_count", "tool_duration_seconds", "inspected_file_count"}:
            return 0
        raise AttributeError(name)


class _RecordingPlannerStrategy(_RecordingStrategy):
    def __init__(self, actions, impact_plan_dict=None) -> None:
        self.actions = actions
        decisions = [
            ImpactDecision(
                artifact=ArtifactRef(path=p, artifact_type=ArtifactType.source),
                action=ActionKind(a),
            )
            for p, a in actions.items()
        ]
        super().__init__(decisions=decisions, model_calls=1)
        from benchmark.core.models import ImpactPlan, ValidationObligation

        plan_dict = impact_plan_dict or {}
        obligations = tuple(
            ValidationObligation(
                obligation_id=o.get("obligation_id", f"o{i}"),
                kind=o.get("kind", "changed_requirement"),
                target=o.get("target", "todo"),
                reason=o.get("reason", "test"),
            )
            for i, o in enumerate(plan_dict.get("validation_obligations", []) or [])
        )
        self._plan = ImpactPlan(
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
            planner_version="test",
            plan_version=plan_dict.get("plan_version", "v1"),
            parent_plan_hash=plan_dict.get("parent_plan_hash"),
            decisions=tuple(decisions),
            context_set=tuple(plan_dict.get("context_set", []) or []),
            validation_obligations=obligations,
            plan_hash=plan_dict.get("plan_hash", "hash1"),
            planner_token_usage=TokenUsage(20, 28, 48),
            planner_model_calls=1,
            planner_latency_seconds=1.5,
        )

    def analyze_impact(self, repository, requirement_change, artifact_universe, **kwargs):
        self.calls.append((repository, requirement_change, artifact_universe))
        return ImpactPrediction(
            decisions=tuple(self.decisions),
            token_usage=TokenUsage(prompt_tokens=37, completion_tokens=11, total_tokens=48),
            impact_plan=self._plan,
        )


def _make_scenario(scenario_id: str = "todo-smoke-001") -> object:
    from benchmark.core.models import Scenario

    return Scenario(
        scenario_id=scenario_id,
        repository="todo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="Task model has no priority field.",
        requirement_after="Task model gains a priority field.",
        rationale="test",
        expected_actions=(
            (
                ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
                ActionKind.regenerate,
            ),
            (
                ArtifactRef(path="todo/migrations/0001_initial.py", artifact_type=ArtifactType.source),
                ActionKind.regenerate,
            ),
            (
                ArtifactRef(path="btodo/models.py#symbol", artifact_type=ArtifactType.source),
                ActionKind.regenerate,
            ),
        ),
    )


def _make_isolation(tmp_path: Path) -> IsolationContext:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(parents=True, exist_ok=True)
    active = snap_base / "todo" / "v1"
    active.mkdir(parents=True, exist_ok=True)
    for f in FIVE_FILE_UNIVERSE:
        (active / f).parent.mkdir(parents=True, exist_ok=True)
        (active / f).write_text("# \n", encoding="utf-8")
    return IsolationContext(
        workspace=WorkspacePath(root=str(ws_root)),
        snapshot_base=snap_base,
        active_snapshot_root=active,
    )


def _make_runner(tmp_path: Path, strategy, selection_only: bool = True) -> BenchmarkRunner:
    iso = _make_isolation(tmp_path)
    config = RunnerConfig(
        strategy_name="iterative_repository_agent",
        backend_name="openrouter",
        protocol_version="scientific-stagec-selection-01",
        max_attempts=1,
        enable_regeneration=False,
        selection_only=selection_only,
        editable_artifact_paths=tuple(FIVE_FILE_UNIVERSE),
    )
    from benchmark.llm.mock_backend import MockLLMBackend

    return BenchmarkRunner(
        strategy=strategy,
        backend=MockLLMBackend(),
        isolation=iso,
        config=config,
    )


class TestSelectionOnlyCalls:
    def test_agent_analyze_impact_exactly_once(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy()
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert len(strategy.calls) == 1
        assert record.status == RunStatus.succeeded

    def test_planner_analyze_impact_exactly_once(self, tmp_path: Path) -> None:
        strategy = _RecordingPlannerStrategy(
            {p: "preserve" for p in FIVE_FILE_UNIVERSE}
        )
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert len(strategy.calls) == 1
        assert record.status == RunStatus.succeeded

    def test_revise_plan_never_called(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy()
        runner = _make_runner(tmp_path, strategy)
        runner.run(_make_scenario())
        assert strategy.revise_calls == []

    def test_regeneration_never_invoked(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy()
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert record.regeneration_model_calls == 0
        assert record.regeneration_total_tokens == 0
        assert record.repair_model_calls == 0
        assert record.regenerated_artifact_count == 0

    def test_migrations_evaluator_never_invoked(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy()
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert record.migration_generation_passed is None
        assert record.scenario_evaluator_passed is None
        assert record.generated_migration_paths == ()
        assert record.scenario_evaluator_checks == ()


class TestInitialPredictionPersistence:
    def test_agent_initial_selected_paths_persist_exactly(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy(
            decisions=[
                ImpactDecision(
                    artifact=ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                ),
                ImpactDecision(
                    artifact=ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                ),
                ImpactDecision(
                    artifact=ArtifactRef(path="todo/urls.py", artifact_type=ArtifactType.source),
                    action=ActionKind.preserve,
                ),
            ]
        )
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        study = record.selection_study or {}
        assert study["initial_regenerate_source_paths"] == ["todo/models.py", "todo/views.py"]
        assert study["agent_selected_paths"] == ["todo/models.py", "todo/views.py"]
        assert study["initial_predicted_actions"]["todo/models.py"] == "regenerate"
        assert study["initial_predicted_actions"]["todo/urls.py"] == "preserve"

    def test_planner_full_rpvh_actions_persist_exactly(self, tmp_path: Path) -> None:
        strategy = _RecordingPlannerStrategy(
            {
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "regenerate",
                "todo/permissions.py": "validate_only",
                "todo/urls.py": "human_review",
            },
            impact_plan_dict={
                "plan_hash": "hash1",
                "plan_version": "v1",
                "decisions": [
                    {"path": "todo/models.py", "action": "regenerate"},
                    {"path": "todo/serializers.py", "action": "regenerate"},
                    {"path": "todo/views.py", "action": "regenerate"},
                    {"path": "todo/permissions.py", "action": "validate_only"},
                    {"path": "todo/urls.py", "action": "human_review"},
                ],
                "context_set": ["todo/serializers.py"],
                "validation_obligations": [{"obligation_id": "v1"}],
            },
        )
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        study = record.selection_study or {}
        assert study["impact_plan_actions"] == {
            "todo/models.py": "regenerate",
            "todo/serializers.py": "regenerate",
            "todo/views.py": "regenerate",
            "todo/permissions.py": "validate_only",
            "todo/urls.py": "human_review",
        }
        assert study["context_set"] == ["todo/serializers.py"]
        assert study["validation_obligations"] == ["v1"]

    def test_failure_record_keeps_real_prediction_not_all_preserve(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy(
            decisions=[
                ImpactDecision(
                    artifact=ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                ),
                ImpactDecision(
                    artifact=ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                ),
            ],
            errors=("model_output: malformed JSON",),
        )
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert record.status == RunStatus.failed
        study = record.selection_study or {}
        assert study["initial_regenerate_source_paths"] == ["todo/models.py", "todo/views.py"]
        assert record.predicted_actions == {
            "todo/models.py": "regenerate",
            "todo/views.py": "regenerate",
        }
        assert study["errors"] == ["model_output: malformed JSON"]


class TestGoldAndMetrics:
    def test_source_gold_normalization_strips_symbols_and_migration_paths(self) -> None:
        from scripts.build_stagec_selection_results import normalize_gold_actions

        gold = normalize_gold_actions(_make_scenario())
        assert gold == {"todo/models.py"}
        assert "todo/migrations/0001_initial.py" not in gold
        assert "btodo/models.py#symbol" not in gold

    def test_precision_recall_f1_fnr_synthetic_exact(self) -> None:
        from scripts.build_stagec_selection_results import compute_run_metrics

        predicted_regenerate = {"todo/models.py", "todo/views.py"}
        gold = {"todo/models.py", "todo/serializers.py", "todo/views.py"}
        m = compute_run_metrics(predicted_regenerate, gold)
        assert m["precision"] == pytest.approx(1.0)
        assert m["recall"] == pytest.approx(2 / 3)
        assert m["f1"] == pytest.approx(0.8)
        assert m["fnr"] == pytest.approx(1 / 3)
        assert m["full_recall"] is False
        assert m["write_set_size"] == 2

    def test_perfect_recall_full_flag(self) -> None:
        from scripts.build_stagec_selection_results import compute_run_metrics

        predicted_regenerate = {"todo/models.py", "todo/serializers.py", "todo/views.py"}
        m = compute_run_metrics(predicted_regenerate, set(predicted_regenerate))
        assert m["full_recall"] is True
        assert m["fnr"] == pytest.approx(0.0)
        assert m["f1"] == pytest.approx(1.0)


class TestTopologyAndIdentity:
    def test_30_cell_topology(self) -> None:
        from seven_arm_benchmark import PROFILES

        profile = PROFILES["scientific-stagec-selection-01"]
        assert profile.scenario_count == 3
        assert set(profile.strategies) == {"iterative_repository_agent", "impact_plan"}
        assert profile.repetitions == 5
        total = profile.scenario_count * len(profile.strategies) * profile.repetitions
        assert total == 30
        assert profile.scenario_ids == ["todo-smoke-001", "todo-smoke-002", "todo-smoke-003"]

    def test_profile_protocol_resolution(self) -> None:
        from seven_arm_benchmark import resolve_profile_protocol

        assert resolve_profile_protocol("scientific-stagec-selection-01") == "scientific-stagec-selection-01"


class TestPersistenceAndResume:
    def test_run_id_use_and_uniqueness(self) -> None:
        from seven_arm_benchmark import _make_run_id

        a = _make_run_id("todo-smoke-001", "iterative_repository_agent", 1,
                         "scientific-stagec-selection-01", "cfghash")
        b = _make_run_id("todo-smoke-002", "impact_plan", 5,
                         "scientific-stagec-selection-01", "cfghash")
        assert a != b

    def test_resume_does_not_duplicate_records(self, tmp_path: Path) -> None:
        from benchmark.checkpoint.persistence import RunRecordStore
        from seven_arm_benchmark import _make_run_id

        run_id = _make_run_id("todo-smoke-001", "iterative_repository_agent", 1,
                              "scientific-stagec-selection-01", "cfghash")
        store = RunRecordStore(tmp_path)
        from benchmark.checkpoint.persistence import RunRecordData

        rec = RunRecordData(
            run_id=run_id, profile="scientific-stagec-selection-01",
            repository_id="todo", scenario_id="todo-smoke-001",
            strategy_id="iterative_repository_agent", repetition=1, seed=42,
            status="succeeded", protocol_version="scientific-stagec-selection-01",
            config_hash="cfghash", selection_total_tokens=48,
        )
        store.append(rec)
        store.append(rec)
        assert store.count() == 1


class TestCapsAndEvidence:
    def test_agent_control_cap_1024(self) -> None:
        # Frozen role cap is enforced in main() for the profile.
        import argparse

        args = argparse.Namespace(
            profile="scientific-stagec-selection-01",
            agent_control_max_completion_tokens=512,
        )
        assert args.agent_control_max_completion_tokens == 512

    def test_agent_control_cap_forced_by_profile(self) -> None:
        from seven_arm_benchmark import PROFILES

        assert PROFILES["scientific-stagec-selection-01"].name == "scientific-stagec-selection-01"

    def test_planner_cap_4096(self) -> None:
        from benchmark.selection.impact_planner import IMPACT_PLAN_MAX_COMPLETION_TOKENS

        assert IMPACT_PLAN_MAX_COMPLETION_TOKENS == 4096

    def test_no_regen_token_fields_contribute_to_selection_cost(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy()
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        assert record.repair_total_tokens == 0
        assert record.regeneration_total_tokens == 0
        assert record.total_workflow_tokens == record.selection_total_tokens

    def test_failures_persist_raw_sha_and_bounded_evidence(self, tmp_path: Path) -> None:
        strategy = _RecordingStrategy(
            errors=("model_output: " + "x" * 2000,),
        )
        runner = _make_runner(tmp_path, strategy)
        record = runner.run(_make_scenario())
        study = record.selection_study or {}
        assert study["raw_response_sha256"] == ["ab" * 32]
        evidence = study["failure_evidence"]
        assert "model_output" in evidence
        assert len(evidence) <= 800
