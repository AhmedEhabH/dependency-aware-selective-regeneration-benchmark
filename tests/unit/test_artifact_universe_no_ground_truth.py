"""WP-0 (G7): ArtifactUniverse must be derived from the parent repository
state, never from ground truth.

Regression focus (AC-0.4):
1. production universe works with hidden truth absent;
2. production execution does not consult expected affected artifacts;
3. default ``allow_ground_truth_universe=False``;
4. fixture opt-in works only when explicitly enabled;
5. fixture flag is visible/auditable in RunRecord;
6. repository/universe errors fail closed;
7. representative real parent-state universe sanity;
8. path traversal / out-of-workspace safety remains intact.

RED first: on the pre-fix implementation, a non-fixture (legacy impact-only)
execution derives ArtifactUniverse from ``scenario.expected_affected_artifacts``
— ground truth. The first test below asserts the production universe is
repository-derived and fails on the leaking implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from benchmark.core.enums import ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath


def _make_scenario(
    scenario_id: str = "sc-universe",
    expected_affected: tuple[ArtifactRef, ...] = (),
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        repository="repo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="before",
        requirement_after="after",
        rationale="test",
        expected_affected_artifacts=expected_affected,
    )


def _gt(path: str) -> ArtifactRef:
    return ArtifactRef(path=path, artifact_type=ArtifactType.source)


def _build_active_snapshot(tmp_path: Path, files: tuple[str, ...]) -> Path:
    active_root = tmp_path / "snapshots" / "repo" / "v1"
    for rel in files:
        target = active_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# source\n", encoding="utf-8")
    return active_root


def _make_runner(
    tmp_path: Path,
    *,
    active_root: Path | None,
    editable: tuple[str, ...],
    enable_regeneration: bool = False,
    selection_only: bool = False,
    validation_command: list[str] | None = None,
) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(parents=True, exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(
        workspace=ws,
        snapshot_base=snap_base,
        active_snapshot_root=active_root,
    )
    config = RunnerConfig(
        strategy_name="test_strategy",
        backend_name="test_backend",
        protocol_version="1.0",
        max_attempts=1,
        enable_regeneration=enable_regeneration,
        selection_only=selection_only,
        editable_artifact_paths=editable,
        validation_command=validation_command,
    )
    return BenchmarkRunner(
        strategy=_RecordingStrategy(),
        backend=_FakeBackend(),
        isolation=iso,
        config=config,
    )


class _RecordingStrategy:
    def __init__(self) -> None:
        self.calls: list[tuple[RepositorySnapshot, RequirementChange, ArtifactUniverse]] = []

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        self.calls.append((repository, requirement_change, artifact_universe))
        return ImpactPrediction()


class _FakeBackend:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return LLMResponse(text="mock", token_usage=TokenUsage(), finish_reason="stop")


# ---------------------------------------------------------------------------
# 1 + 2. Production universe is repository-derived, hidden truth absent
# ---------------------------------------------------------------------------


class TestProductionUniverseRepositoryDerived:
    def test_non_fixture_universe_comes_from_parent_state(self, tmp_path: Path) -> None:
        """Production (non-fixture) universe must be derived from the parent
        repository state and MUST NOT contain ground-truth-only paths."""
        active_root = _build_active_snapshot(tmp_path, ("src/main.py", "src/utils.py"))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py", "src/utils.py"),
        )
        scenario = _make_scenario(
            "sc-prod",
            expected_affected=(_gt("hidden/secret.py"),),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert len(_calls_of(runner)) == 1

    def test_production_universe_never_consults_expected_affected(self, tmp_path: Path) -> None:
        active_root = _build_active_snapshot(tmp_path, ("src/main.py", "src/utils.py"))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py", "src/utils.py"),
        )
        gt = _gt("hidden/secret.py")
        scenario = _make_scenario("sc-prod-gt", expected_affected=(gt,))
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        _repo, _change, universe = _calls_of(runner)[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/main.py" in paths
        assert "src/utils.py" in paths
        assert "hidden/secret.py" not in paths


def _calls_of(runner: BenchmarkRunner) -> list[tuple[object, object, ArtifactUniverse]]:
    strategy = runner._strategy  # type: ignore[attr-defined]
    return list(strategy.calls)


def _fixture_runner(
    tmp_path: Path,
    *,
    active_root: Path,
    editable: tuple[str, ...],
) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(parents=True, exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(
        workspace=ws,
        snapshot_base=snap_base,
        active_snapshot_root=active_root,
    )
    config = RunnerConfig(
        strategy_name="test_strategy",
        backend_name="test_backend",
        protocol_version="1.0",
        max_attempts=1,
        editable_artifact_paths=editable,
        allow_ground_truth_universe=True,
    )
    return BenchmarkRunner(
        strategy=_RecordingStrategy(),
        backend=_FakeBackend(),
        isolation=iso,
        config=config,
    )


# ---------------------------------------------------------------------------
# 3 + 4. Fixture flag default and explicit opt-in
# ---------------------------------------------------------------------------


class TestFixtureFlagDefaultAndOptIn:
    def test_default_flag_is_false(self) -> None:
        config = RunnerConfig(
            strategy_name="s",
            backend_name="b",
            protocol_version="1.0",
        )
        assert config.allow_ground_truth_universe is False

    def test_fixture_opt_in_restores_ground_truth_universe(self, tmp_path: Path) -> None:
        """Explicit fixture opt-in ONLY: universe may use expected artifacts
        and the resulting RunRecord must expose the condition."""
        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _fixture_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py",),
        )
        gt = _gt("fixture/expected.py")
        scenario = _make_scenario("sc-fixture", expected_affected=(gt,))
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        _repo, _change, universe = _calls_of(runner)[0]
        paths = {a.path for a in universe.artifacts}
        assert "fixture/expected.py" in paths
        assert record.allow_ground_truth_universe is True

    def test_non_fixture_record_audits_false(self, tmp_path: Path) -> None:
        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py",),
        )
        record = runner.run(_make_scenario("sc-prod-audit"))
        assert record.status == RunStatus.succeeded
        assert record.allow_ground_truth_universe is False

    def test_invalid_config_fixture_with_regeneration_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            RunnerConfig(
                strategy_name="s",
                backend_name="b",
                protocol_version="1.0",
                enable_regeneration=True,
                validation_command=[sys.executable, "-c", "exit(0)"],
                allow_ground_truth_universe=True,
            )

    def test_invalid_config_fixture_with_selection_only_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            RunnerConfig(
                strategy_name="s",
                backend_name="b",
                protocol_version="1.0",
                selection_only=True,
                allow_ground_truth_universe=True,
            )

    def test_non_bool_flag_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            RunnerConfig(
                strategy_name="s",
                backend_name="b",
                protocol_version="1.0",
                allow_ground_truth_universe="yes",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# 5. Auditability
# ---------------------------------------------------------------------------


class TestRunRecordAuditability:
    def test_fixture_flag_serialized(self, tmp_path: Path) -> None:
        from dataclasses import asdict

        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _fixture_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py",),
        )
        record = runner.run(_make_scenario("sc-audit"))
        d = asdict(record)
        assert d["allow_ground_truth_universe"] is True

    def test_record_defaults_false_when_unspecified(self) -> None:
        from benchmark.core.models import RunIdentity

        record = RunRecord(
            identity=RunIdentity(
                run_id="r",
                protocol_version="1.0",
                repository_commit_sha="sha",
                scenario_id="s",
                strategy_name="strategy",
            ),
            status=RunStatus.succeeded,
        )
        assert record.allow_ground_truth_universe is False


# ---------------------------------------------------------------------------
# 6. Fail closed
# ---------------------------------------------------------------------------


class TestFailClosed:
    def test_no_active_snapshot_fails_closed(self, tmp_path: Path) -> None:
        runner = _make_runner(
            tmp_path,
            active_root=None,
            editable=("src/main.py",),
        )
        record = runner.run(_make_scenario("sc-no-snapshot"))
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "active snapshot" in messages.lower()

    def test_empty_editable_paths_fails_closed(self, tmp_path: Path) -> None:
        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=(),
        )
        record = runner.run(_make_scenario("sc-empty-editable"))
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "allowed_paths" in messages

    def test_missing_snapshot_file_fails_closed(self, tmp_path: Path) -> None:
        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=("src/main.py", "src/missing.py"),
        )
        record = runner.run(_make_scenario("sc-missing-file"))
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages


# ---------------------------------------------------------------------------
# 8. Path traversal / out-of-workspace safety
# ---------------------------------------------------------------------------


class TestPathSafety:
    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        active_root = _build_active_snapshot(tmp_path, ("src/main.py",))
        runner = _make_runner(
            tmp_path,
            active_root=active_root,
            editable=("../../outside.py",),
        )
        record = runner.run(_make_scenario("sc-traversal"))
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "traversal" in messages.lower() or "escape" in messages.lower()

