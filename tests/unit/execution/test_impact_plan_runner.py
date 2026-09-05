from __future__ import annotations

import json
from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArchitectureConstraint,
    ArtifactRef,
    ArtifactUniverse,
    LLMResponse,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import SharedRegenerationExecutor
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.impact_planner import (
    MockImpactPlanner,
    PlannerInput,
)
from benchmark.strategies.impact_plan import ImpactPlanSelectiveStrategy

_CANDIDATES = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

GOLD_SENTINEL = "GOLD_SENTINEL_EXPOSE_PRIORITY"


def _universe(paths=_CANDIDATES) -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=tuple(ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in paths)
    )


def _scenario() -> Scenario:
    return Scenario(
        scenario_id="todo-smoke-001",
        repository="todo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="Task has no priority",
        requirement_after="Task gains Priority with HIGH, MEDIUM, LOW",
        rationale="test",
        acceptance_criteria=(AcceptanceCriterion(description="TaskSerializer exposes priority"),),
        architecture_constraints=(
            ArchitectureConstraint(description="Priority filtering must be in the view"),
        ),
        expected_actions=(
            (
                ArtifactRef(path="todo/serializers.py", artifact_type=ArtifactType.source),
                ActionKind.regenerate,
            ),
        ),
        expected_artifact_instructions=(("todo/serializers.py", GOLD_SENTINEL),),
    )


def _make_iso(tmp_path: Path) -> IsolationContext:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap = tmp_path / "snapshots"
    snap.mkdir(exist_ok=True)
    active = snap / "active"
    active.mkdir(exist_ok=True)
    for p in _CANDIDATES:
        f = active / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"# {p}\n", encoding="utf-8")
    (ws_root / "todo").mkdir(exist_ok=True)
    for p in _CANDIDATES:
        f = ws_root / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"# {p}\n", encoding="utf-8")
    return IsolationContext(
        workspace=WorkspacePath(root=str(ws_root)),
        snapshot_base=snap,
        active_snapshot_root=active,
    )


class _ImpactRunner:
    def __init__(self, tmp_path: Path, *, plan_r_paths: frozenset[str], plan_v_paths: frozenset[str] = frozenset()):
        self.tmp_path = tmp_path
        self.iso = _make_iso(tmp_path)
        self.planner = MockImpactPlanner(r_paths=plan_r_paths, v_paths=plan_v_paths)
        self.strategy = ImpactPlanSelectiveStrategy(planner=self.planner)
        self.record: RunRecord | None = None

    def runner(self) -> BenchmarkRunner:
        return BenchmarkRunner(
            strategy=self.strategy,
            backend=_FakeBackend(),
            isolation=self.iso,
            config=RunnerConfig(
                strategy_name="impact_plan",
                backend_name="test_backend",
                protocol_version="1.0",
                max_attempts=1,
                enable_regeneration=True,
                validation_command=[__import__("sys").executable, "-c", "exit(0)"],
                editable_artifact_paths=_CANDIDATES,
                exact_patch=False,
                scientific_gold_isolation=True,
            ),
        )

    def run(self) -> RunRecord:
        self.record = self.runner().run(_scenario())
        return self.record


class _FakeBackend:
    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        return LLMResponse(text="# generated\n", token_usage=TokenUsage(1, 1, 2))


class TestImpactPlanPersistedBeforeWrite:
    def test_plan_sidecar_written_before_edit(self, tmp_path: Path) -> None:
        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        r.run()
        plan_dir = Path(r.iso.workspace.root) / "impact_plans"
        files = list(plan_dir.glob("*.json"))
        assert files, "impact plan sidecar was not persisted"
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert payload["plan_version"] == "v1"
        assert payload["write_set"] == ["todo/models.py"]

    def test_plan_hash_recorded(self, tmp_path: Path) -> None:
        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        record = r.run()
        assert record.impact_plan_hash
        assert record.impact_plan_version == "v1"
        assert record.impact_plan is not None


class TestWriteGuardPhysicallyBlocks:
    def test_preserve_not_written(self, tmp_path: Path) -> None:
        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        r.run()
        snapshot_path = Path(r.iso.active_snapshot_root)
        ws_path = Path(r.iso.workspace.root)
        # urls.py is PRESERVE -> must be byte-identical to the active snapshot
        for rel in ("todo/urls.py", "todo/serializers.py", "todo/permissions.py", "todo/views.py"):
            assert (ws_path / rel).read_bytes() == (snapshot_path / rel).read_bytes(), (
                f"{rel} was unexpectedly written"
            )

    def test_regenerate_written(self, tmp_path: Path) -> None:
        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        record = r.run()
        changed = list(record.changed_artifact_paths)
        assert "todo/models.py" in changed

    def test_validate_only_not_written(self, tmp_path: Path) -> None:
        r = _ImpactRunner(
            tmp_path,
            plan_r_paths=frozenset({"todo/models.py"}),
            plan_v_paths=frozenset({"todo/views.py"}),
        )
        r.run()
        snapshot_path = Path(r.iso.active_snapshot_root)
        ws_path = Path(r.iso.workspace.root)
        for rel in ("todo/views.py", "todo/urls.py", "todo/permissions.py"):
            assert (ws_path / rel).read_bytes() == (snapshot_path / rel).read_bytes(), (
                f"{rel} was unexpectedly written"
            )


class TestProhibitedWriteAttemptsBlockedAndLogged:
    def test_executor_counts_prohibited_write(self, tmp_path: Path) -> None:
        # A RegenerationPlan that (incorrectly) contains P/V/H ordered artifacts
        # must block them physically and count the attempt.
        from benchmark.core.models import ArtifactRef
        from benchmark.selection.planner import RegenerationPlan

        iso = _make_iso(tmp_path)
        plan = RegenerationPlan(
            ordered_artifacts=(
                ArtifactRef(path="todo/urls.py", artifact_type=ArtifactType.source),
                ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
            ),
            actions={
                "todo/urls.py": ActionKind.preserve,
                "todo/models.py": ActionKind.regenerate,
            },
        )
        executor = SharedRegenerationExecutor(_FakeBackend())
        result = executor.execute(plan, iso, enable_exact_patch=False)
        assert result.prohibited_write_attempts == 1
        assert "todo/urls.py" not in [a.path for a in result.artifacts if a.status == "generated"]


class TestGoldSentinelAbsentFromPlannerInputs:
    def test_planner_input_never_contains_gold(self, tmp_path: Path) -> None:
        inp = PlannerInput(
            requirement_change=RequirementChange(
                before="a", after="b", acceptance_criteria=("c",)
            ),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
            extra_architecture_constraints=(),
        )
        text = str(inp.requirement_change)
        assert GOLD_SENTINEL not in text

    def test_plan_prompt_template_has_no_gold(self) -> None:
        from benchmark.selection.impact_planner import PLANNER_PROMPT_TEMPLATE

        assert GOLD_SENTINEL not in PLANNER_PROMPT_TEMPLATE


class TestBoundedExpansion:
    def test_no_expansion_on_success(self, tmp_path: Path) -> None:
        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        record = r.run()
        assert record.impact_expansion_count == 0
        assert record.escalated_to_human_review is False
        assert not record.failures

    def test_missed_impact_exactly_one_expansion_then_h(self, tmp_path: Path) -> None:
        """Missed-impact validation failure -> exactly ONE v2 expansion -> H."""
        import sys

        # validation_command fails only while workspace lacks a marker file.
        failing_cmd = [
            sys.executable, "-c",
            "import os, pathlib; p = pathlib.Path(os.getenv('WS_ROOT', '.')) / 'fixed.ok'; "
            "raise SystemExit(0 if p.exists() else 1)",
        ]

        class _ExpandingRunner(_ImpactRunner):
            def runner(self) -> BenchmarkRunner:
                return BenchmarkRunner(
                    strategy=self.strategy,
                    backend=_FakeBackend(),
                    isolation=self.iso,
                    config=RunnerConfig(
                        strategy_name="impact_plan",
                        backend_name="test_backend",
                        protocol_version="1.0",
                        max_attempts=1,
                        enable_regeneration=True,
                        validation_command=failing_cmd,
                        editable_artifact_paths=_CANDIDATES,
                        exact_patch=False,
                        scientific_gold_isolation=True,
                    ),
                )

        r = _ExpandingRunner(
            tmp_path, plan_r_paths=frozenset({"todo/models.py"}),
        )
        # v1 validation fails; v2 re-runs with same workspace (still failing) -> H
        record = r.run()
        assert record.impact_expansion_count == 1, record.failures
        assert record.escalated_to_human_review is True
        assert record.status == RunStatus.failed
        assert any(f.stage == "human_review" for f in record.failures)

    def test_expansion_resolves_and_succeeds(self, tmp_path: Path) -> None:
        """If v2 generation fixes the requirement, the run ends SUCCEEDED with
        exactly one expansion and final plan version v2."""
        import sys

        class _FixingBackend:
            def __init__(self) -> None:
                self.calls = 0

            async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
                self.calls += 1
                if self.calls == 1:
                    return LLMResponse(text="# v1 no magic\n", token_usage=TokenUsage(1, 1, 2))
                return LLMResponse(text="# v2 has MAGIC_OK\n", token_usage=TokenUsage(1, 1, 2))

        cmd = [
            sys.executable, "-c",
            "import pathlib, sys; "
            "p = pathlib.Path('todo/models.py'); "
            "sys.exit(0 if p.exists() and 'MAGIC_OK' in p.read_text() else 1)",
        ]

        r = _ImpactRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        r.backend = _FixingBackend()

        class _ResolvingRunner(_ImpactRunner):
            def runner(self) -> BenchmarkRunner:
                return BenchmarkRunner(
                    strategy=self.strategy,
                    backend=self.backend,
                    isolation=self.iso,
                    config=RunnerConfig(
                        strategy_name="impact_plan",
                        backend_name="test_backend",
                        protocol_version="1.0",
                        max_attempts=1,
                        enable_regeneration=True,
                        validation_command=cmd,
                        editable_artifact_paths=_CANDIDATES,
                        exact_patch=False,
                        scientific_gold_isolation=True,
                    ),
                )

        r = _ResolvingRunner(tmp_path, plan_r_paths=frozenset({"todo/models.py"}))
        r.backend = _FixingBackend()
        record = r.run()
        assert record.impact_expansion_count == 1, record.failures
        assert record.escalated_to_human_review is False
        assert record.status == RunStatus.succeeded
        assert record.impact_plan_version == "v2", record.impact_plan_version

    def test_adjust_field_for_expansion(self, tmp_path: Path) -> None:
        """Record fields survive RunRecord construction (blocked-attempts field)."""
        rec = RunRecord(
            identity=RunIdentity(
                run_id="r1",
                protocol_version="1.0",
                repository_commit_sha="abc",
                scenario_id="todo-smoke-001",
                strategy_name="impact_plan",
            ),
            status=RunStatus.succeeded,
            token_usage=TokenUsage(1, 2, 3),
            prohibited_write_attempts=1,
            impact_plan={"plan": {"write_set": []}, "final_after_expansion": False},
            impact_plan_hash="h",
            impact_plan_version="v1",
            planner_prompt_tokens=5,
            planner_completion_tokens=5,
            planner_total_tokens=10,
            planner_model_calls=1,
            planner_latency_seconds=0.1,
        )
        assert rec.prohibited_write_attempts == 1
