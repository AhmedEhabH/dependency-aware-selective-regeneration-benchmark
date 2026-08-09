from __future__ import annotations

import json
import math
import sys
import time
from argparse import Namespace
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from benchmark.checkpoint.persistence import (
    RunRecordData,
    RunRecordStore,
)
from benchmark.core.enums import ArtifactType, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    LLMResponse,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.pipeline import PipelineConfig
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.dependency_scope import ArtifactDescriptor, DependencyGraph
from benchmark.statistics.reporting import NotebookExporter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FixedTokenBackend:
    token_accounting_mode: str = "fixture_or_approximate"

    def __init__(
        self,
        tokens: TokenUsage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        vary_output: bool = False,
    ):
        self._tokens = tokens
        self._vary_output = vary_output
        self.call_count = 0
        self.captured_max_tokens: list[int] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return self._tokens.prompt_tokens

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.call_count += 1
        self.captured_max_tokens.append(max_tokens)
        text = f"value = {self.call_count}\n" if self._vary_output else "content"
        return LLMResponse(text=text, token_usage=self._tokens, finish_reason="stop")


class _SentinelBackend:
    token_accounting_mode: str = "fixture_or_approximate"

    def __init__(self, responses: list[TokenUsage]):
        self._responses = responses
        self._idx = 0
        self.call_count = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        return self._responses[self._idx].prompt_tokens if self._idx < len(self._responses) else 10

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        tu = self._responses[self._idx] if self._idx < len(self._responses) else TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        self._idx += 1
        self.call_count += 1
        return LLMResponse(text=f"value = {self.call_count}\n", token_usage=tu, finish_reason="stop")


class _ThreeFileBackend:
    token_accounting_mode: str = "fixture_or_approximate"

    def __init__(self, per_call_limit: int = 4096):
        self.captured_max_tokens: list[int] = []
        self.call_count = 0
        self._limit = per_call_limit

    def count_prompt_tokens(self, prompt: str) -> int:
        return 10

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.captured_max_tokens.append(max_tokens)
        self.call_count += 1
        return LLMResponse(
            text="content",
            token_usage=TokenUsage(prompt_tokens=13, completion_tokens=5, total_tokens=18),
            finish_reason="stop",
        )


class _StrategyBackend:
    token_accounting_mode = "fixture_or_approximate"

    def __init__(self, responses: list[tuple[str, TokenUsage]] | None = None):
        self._responses = responses or []
        self._idx = 0
        self.call_count = 0
        self.captured_max_tokens: list[int] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return 50

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.call_count += 1
        self.captured_max_tokens.append(max_tokens)
        text, tu = self._responses[self._idx] if self._idx < len(self._responses) else ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "test"}', TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60))
        self._idx += 1
        return LLMResponse(text=text, token_usage=tu, finish_reason="stop")


class _ExactExhaustToolBackend:
    token_accounting_mode = "fixture_or_approximate"

    def __init__(self, usage: TokenUsage):
        self._usage = usage
        self.call_count = 0
        self.captured_max_tokens: list[int] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return 0

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.call_count += 1
        self.captured_max_tokens.append(max_tokens)
        return LLMResponse(
            text='{"action": "list_files", "path": "."}',
            token_usage=self._usage,
            finish_reason="stop",
        )


def _make_scenario(
    artifacts: tuple[ArtifactRef, ...] = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),),
    before: str = "old requirement",
    after: str = "new requirement",
    evaluator_asset: str = "",
) -> Scenario:
    return Scenario(
        scenario_id="test_r4_scenario",
        repository="test_repo",
        blast_radius="localized",
        requirement_before=before,
        requirement_after=after,
        change_type="modify",
        rationale="test",
        expected_affected_artifacts=artifacts,
        evaluator_asset=evaluator_asset,
    )


def _setup_workspace(tmp_path: Path, artifacts: tuple[ArtifactRef, ...]) -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    active_root = snap_base / "test_repo" / "test_revision"
    active_root.mkdir(parents=True, exist_ok=True)
    for a in artifacts:
        p = ws_root / a.path.lstrip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("original content")
        snap_target = active_root / a.path.lstrip("/")
        snap_target.parent.mkdir(parents=True, exist_ok=True)
        snap_target.write_text("original content")
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    return iso, ws_root


def _make_runner(
    tmp_path: Path,
    strategy: Any,
    backend: Any,
    isolation: IsolationContext,
    enable_regeneration: bool = False,
    validation_command: list[str] | None = None,
    strategy_name: str = "monolithic",
    max_attempts: int = 3,
    max_tokens: int = 0,
    max_completion_tokens_per_call: int = 4096,
    editable_artifact_paths: tuple[str, ...] = ("src/a.py",),
    canonical_project_root: Path | None = None,
    python_executable: str | None = None,
) -> BenchmarkRunner:
    cfg = RunnerConfig(
        strategy_name=strategy_name,
        backend_name="mock",
        protocol_version="1.0",
        timeout_seconds=0,
        max_attempts=max_attempts,
        max_tokens=max_tokens,
        max_completion_tokens_per_call=max_completion_tokens_per_call,
        max_total_workflow_tokens=max_tokens,
        enable_regeneration=enable_regeneration,
        validation_command=validation_command or [sys.executable, "-c", "exit(0)"],
        validation_timeout=5,
        editable_artifact_paths=editable_artifact_paths,
        canonical_project_root=canonical_project_root,
        python_executable=python_executable or sys.executable,
    )
    return BenchmarkRunner(strategy=strategy, backend=backend, isolation=isolation, config=cfg)


# ---------------------------------------------------------------------------
# I. CLI and config identity
# ---------------------------------------------------------------------------


def test_cli_defaults_resolve_to_4096_and_unlimited() -> None:
    cfg = PipelineConfig(protocol_version="1.0")
    assert cfg.max_completion_tokens_per_call == 4096
    assert cfg.resolved_max_total_workflow_tokens == 0


def _capture_cli_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    **kwargs: Any,
) -> tuple[list[PipelineConfig], dict[str, Any]]:
    from seven_arm_benchmark import _run_single_scenario_strategy

    captured: list[PipelineConfig] = []

    class _CapturingPipelineConfig(PipelineConfig):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            captured.append(self)

    class _StubPipeline:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def run_scenario_by_id(self, scenario_id: str) -> RunRecord:
            return RunRecord(
                identity=RunIdentity(
                    run_id="cli_capture",
                    protocol_version="1.0",
                    repository_commit_sha="abc",
                    scenario_id=scenario_id,
                    strategy_name="monolithic",
                ),
                status=RunStatus.succeeded,
            )

    class _StubProvider:
        def get_scenario(self, scenario_id: str) -> Scenario:
            return _make_scenario()

    monkeypatch.setattr("benchmark.execution.pipeline.PipelineConfig", _CapturingPipelineConfig)
    monkeypatch.setattr("benchmark.execution.pipeline.BenchmarkPipeline", _StubPipeline)

    result_dict, success = _run_single_scenario_strategy(
        scenario_id="test_r4_scenario",
        strategy_name="monolithic",
        scenario_provider=_StubProvider(),
        dry_run=False,
        profile="smoke",
        model_path=None,
        protocol_version="1.0",
        max_attempts=3,
        timeout_seconds=0,
        dep_graph=None,
        workspace_dir=tmp_path / "cli_workspace",
        **kwargs,
    )
    return captured, result_dict


def test_cli_explicit_limits_reach_pipeline_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured, result_dict = _capture_cli_config(
        monkeypatch,
        tmp_path,
        max_completion_tokens_per_call=2048,
        max_total_workflow_tokens=9000,
    )
    assert len(captured) == 1
    assert captured[0].max_completion_tokens_per_call == 2048
    assert captured[0].resolved_max_total_workflow_tokens == 9000
    assert result_dict["strategy_name"] == "monolithic"
    assert result_dict["scenario_id"] == "test_r4_scenario"
    assert result_dict["status"] == "succeeded"


def test_cli_legacy_only_total_resolves_and_persists_9000(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured, result_dict = _capture_cli_config(
        monkeypatch,
        tmp_path,
        max_tokens=9000,
        max_total_workflow_tokens=0,
    )
    assert len(captured) == 1
    assert captured[0].resolved_max_total_workflow_tokens == 9000
    assert captured[0].max_total_workflow_tokens == 9000
    assert result_dict["max_total_workflow_tokens"] == 9000


def test_cli_equal_positive_legacy_and_explicit_total_accepted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured, result_dict = _capture_cli_config(
        monkeypatch,
        tmp_path,
        max_tokens=9000,
        max_total_workflow_tokens=9000,
    )
    assert len(captured) == 1
    assert captured[0].resolved_max_total_workflow_tokens == 9000
    assert result_dict["max_total_workflow_tokens"] == 9000


def test_cli_differing_positive_totals_rejected_before_runner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ValueError):
        _capture_cli_config(
            monkeypatch,
            tmp_path,
            max_tokens=9000,
            max_total_workflow_tokens=7000,
        )


def test_cli_conflicting_legacy_and_explicit_total_fails() -> None:
    with pytest.raises(ValueError):
        PipelineConfig(protocol_version="1.0", max_tokens_per_run=4096, max_total_workflow_tokens=8192)


def test_config_hash_changes_with_per_call_limit() -> None:
    from seven_arm_benchmark import _compute_config_hash

    ns1 = Namespace(max_completion_tokens_per_call=2048, max_total_workflow_tokens=0, max_tokens=0, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    ns2 = Namespace(max_completion_tokens_per_call=4096, max_total_workflow_tokens=0, max_tokens=0, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    assert _compute_config_hash(ns1) != _compute_config_hash(ns2)


def test_config_hash_changes_with_total_limit() -> None:
    from seven_arm_benchmark import _compute_config_hash

    ns1 = Namespace(max_completion_tokens_per_call=4096, max_total_workflow_tokens=0, max_tokens=0, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    ns2 = Namespace(max_completion_tokens_per_call=4096, max_total_workflow_tokens=5000, max_tokens=0, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    assert _compute_config_hash(ns1) != _compute_config_hash(ns2)


def test_legacy_and_explicit_equivalent_total_share_hash() -> None:
    from seven_arm_benchmark import _compute_config_hash

    ns_explicit = Namespace(max_completion_tokens_per_call=4096, max_total_workflow_tokens=5000, max_tokens=0, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    ns_legacy = Namespace(max_completion_tokens_per_call=4096, max_total_workflow_tokens=0, max_tokens=5000, dry_run=False, profile="smoke", strategy=None, max_attempts=3, timeout=0, protocol_version="1.0")
    assert _compute_config_hash(ns_explicit) == _compute_config_hash(ns_legacy)


# ---------------------------------------------------------------------------
# J. Monolithic and Selective public path
# ---------------------------------------------------------------------------


def test_public_monolithic_three_file_run_gives_each_call_4096(tmp_path: Path) -> None:
    artifacts = (
        ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/c.py", artifact_type=ArtifactType.source),
    )
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _ThreeFileBackend()
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        strategy_name="monolithic",
        max_tokens=0,
        editable_artifact_paths=("src/a.py", "src/b.py", "src/c.py"),
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.succeeded
    assert len(backend.captured_max_tokens) == 3
    assert backend.captured_max_tokens == [4096, 4096, 4096]


def test_public_selective_three_file_run_gives_each_call_4096(tmp_path: Path) -> None:
    artifacts = (
        ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="src/c.py", artifact_type=ArtifactType.source),
    )
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _ThreeFileBackend()
    from benchmark.strategies import HybridSelectiveStrategy
    desc_a = ArtifactDescriptor(
        path="src/a.py", category="source", description="core module implementation",
        provides_symbols=("module",), typical_change_triggers=("refactor",),
    )
    desc_b = ArtifactDescriptor(
        path="src/b.py", category="source", description="core module implementation",
        provides_symbols=("module",), typical_change_triggers=("refactor",),
    )
    desc_c = ArtifactDescriptor(
        path="src/c.py", category="source", description="core module implementation",
        provides_symbols=("module",), typical_change_triggers=("refactor",),
    )
    strategy = HybridSelectiveStrategy(
        graph=DependencyGraph(nodes=("src/a.py", "src/b.py", "src/c.py"), edges=()),
        artifact_descriptors=(desc_a, desc_b, desc_c),
    )
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        strategy_name="selective",
        max_tokens=0,
        editable_artifact_paths=("src/a.py", "src/b.py", "src/c.py"),
    )
    record = runner.run(_make_scenario(artifacts, before="refactor module", after="refactor subsystem"))
    assert record.status == RunStatus.succeeded
    assert len(backend.captured_max_tokens) == 3
    assert backend.captured_max_tokens == [4096, 4096, 4096]


def test_public_monolithic_initial_and_repair_metrics_are_separate(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _FixedTokenBackend()
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="monolithic",
        max_attempts=3,
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.regeneration_model_calls == 1
    assert record.repair_model_calls >= 1
    assert record.repair_attempts >= 1
    assert record.regeneration_total_tokens > 0
    assert record.repair_total_tokens > 0


def test_public_selective_initial_and_repair_metrics_are_separate(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _FixedTokenBackend()
    from benchmark.strategies import HybridSelectiveStrategy
    desc = ArtifactDescriptor(
        path="src/a.py", category="source", description="core module implementation",
        provides_symbols=("module",), typical_change_triggers=("refactor",),
    )
    strategy = HybridSelectiveStrategy(
        graph=DependencyGraph(nodes=("src/a.py",), edges=()),
        artifact_descriptors=(desc,),
    )
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="selective",
        max_attempts=3,
    )
    record = runner.run(_make_scenario(artifacts, before="refactor module", after="refactor subsystem"))
    assert record.regeneration_model_calls == 1
    assert record.repair_model_calls >= 1


def test_public_failed_repair_preserves_all_consumed_tokens(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _FixedTokenBackend()
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="monolithic",
        max_attempts=2,
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.failed
    assert record.selection_total_tokens >= 0
    assert record.regeneration_total_tokens > 0
    assert record.total_workflow_tokens == record.selection_total_tokens + record.regeneration_total_tokens + record.repair_total_tokens


# ---------------------------------------------------------------------------
# K. Persistence and reporting
# ---------------------------------------------------------------------------


def test_record_dict_contains_complete_r4_metrics(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    backend = _FixedTokenBackend()
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        strategy_name="monolithic",
    )
    record = runner.run(_make_scenario(artifacts))
    d = asdict(record)
    for key in ("repair_prompt_tokens", "repair_completion_tokens", "repair_total_tokens", "repair_model_calls", "repair_duration_seconds", "repair_attempts", "token_accounting_mode"):
        assert key in d, f"Missing key: {key}"


def test_run_record_data_contains_complete_r4_metrics(tmp_path: Path) -> None:
    data = RunRecordData(
        run_id="test", profile="p", repository_id="r", scenario_id="s", strategy_id="st", repetition=1, seed=42, status="succeeded",
        repair_prompt_tokens=19, repair_completion_tokens=8, repair_total_tokens=27,
        repair_model_calls=1, repair_duration_seconds=3.0, repair_attempts=1,
        token_accounting_mode="exact_tokenizer",
    )
    assert data.repair_prompt_tokens == 19
    assert data.repair_total_tokens == 27
    assert data.repair_attempts == 1
    assert data.token_accounting_mode == "exact_tokenizer"


def test_jsonl_round_trip_preserves_complete_r4_metrics(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs")
    data = RunRecordData(
        run_id="jsonl_r4_test", profile="p", repository_id="r", scenario_id="s", strategy_id="st", repetition=1, seed=42, status="succeeded",
        repair_prompt_tokens=19, repair_completion_tokens=8, repair_total_tokens=27,
        repair_model_calls=1, repair_duration_seconds=3.0, repair_attempts=1,
        token_accounting_mode="fixture_or_approximate",
    )
    store.append(data)
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].repair_prompt_tokens == 19
    assert loaded[0].repair_total_tokens == 27
    assert loaded[0].repair_attempts == 1
    assert loaded[0].token_accounting_mode == "fixture_or_approximate"


def test_old_jsonl_defaults_r4_fields(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs2")
    old_data = {
        "run_id": "old_test", "profile": "p", "repository_id": "r", "scenario_id": "s",
        "strategy_id": "st", "repetition": 1, "seed": 42, "status": "succeeded",
        "token_usage": {"prompt": 10, "completion": 5, "total": 15},
        "duration_seconds": 1.0,
    }
    with open(store.path, "a", encoding="utf-8") as f:
        f.write(json.dumps(old_data, sort_keys=True) + "\n")
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].repair_prompt_tokens == 0
    assert loaded[0].repair_total_tokens == 0
    assert loaded[0].repair_attempts == 0
    assert loaded[0].token_accounting_mode == "unknown"


def test_idempotency_compares_repair_fields(tmp_path: Path) -> None:
    from benchmark.checkpoint.persistence import RunRecordIntegrityError

    store = RunRecordStore(tmp_path / "runs3")
    data = RunRecordData(
        run_id="idempotent_r4", profile="p", repository_id="r", scenario_id="s", strategy_id="st", repetition=1, seed=42, status="succeeded",
        repair_prompt_tokens=19, repair_total_tokens=27,
    )
    store.append(data)
    store.append(data)
    loaded = store.load_all()
    assert len(loaded) == 1
    data_diff = RunRecordData(
        run_id="idempotent_r4", profile="p", repository_id="r", scenario_id="s", strategy_id="st", repetition=1, seed=42, status="succeeded",
        repair_prompt_tokens=99, repair_total_tokens=27,
    )
    with pytest.raises(RunRecordIntegrityError):
        store.append(data_diff)


def test_reporting_serializes_complete_r4_metrics(tmp_path: Path) -> None:
    exporter = NotebookExporter()
    record = RunRecord(
        identity=RunIdentity(run_id="r4_report", protocol_version="1.0", repository_commit_sha="abc", scenario_id="s", strategy_name="st"),
        status=RunStatus.succeeded,
        token_usage=TokenUsage(prompt_tokens=19, completion_tokens=8, total_tokens=27),
        repair_prompt_tokens=19, repair_completion_tokens=8, repair_total_tokens=27,
        repair_model_calls=1, repair_duration_seconds=3.0, repair_attempts=1,
        token_accounting_mode="exact_tokenizer",
        total_workflow_tokens=27, total_workflow_model_calls=1, total_workflow_duration_seconds=3.0,
    )
    export = exporter.export(results=(), records=(record,))
    rec = export["records"][0]
    assert rec["repair_prompt_tokens"] == 19
    assert rec["repair_total_tokens"] == 27
    assert rec["repair_attempts"] == 1
    assert rec["token_accounting_mode"] == "exact_tokenizer"


def test_model_metadata_labels_exact_qwen_accounting(tmp_path: Path) -> None:
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
    assert KaggleQwenBackend.token_accounting_mode == "exact_tokenizer"
    data = RunRecordData(
        run_id="meta_test", profile="p", repository_id="r", scenario_id="s", strategy_id="st", repetition=1, seed=42, status="succeeded",
        model_metadata={"model": "qwen2.5-coder", "token_accounting_mode": "exact_tokenizer"},
    )
    assert data.model_metadata["token_accounting_mode"] == "exact_tokenizer"


def test_model_metadata_labels_approximate_engineering_accounting(tmp_path: Path) -> None:
    from benchmark.llm.mock_backend import MockLLMBackend
    assert MockLLMBackend.token_accounting_mode == "approximate_character"


# ---------------------------------------------------------------------------
# L. Validation duration accumulation
# ---------------------------------------------------------------------------


def test_public_repair_accumulates_migration_duration_across_attempts(tmp_path: Path) -> None:
    iso, ws_root = _setup_workspace(tmp_path, (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))
    backend = _FixedTokenBackend()
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    scenario = _make_scenario()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="monolithic",
        max_attempts=3,
    )
    record = runner.run(scenario)
    assert record.migration_duration_seconds == 0.0


def test_public_repair_accumulates_baseline_duration_across_attempts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from benchmark.execution.validation import FunctionalValidationResult

    class _FailingBaselineValidator:
        def validate(self, workspace_root=None, command=None, timeout=None) -> FunctionalValidationResult:
            return FunctionalValidationResult(
                passed=False, exit_code=1, stdout="baseline failure", stderr="",
                duration_seconds=0.5,
            )

    monkeypatch.setattr("benchmark.execution.runner.FunctionalValidator", _FailingBaselineValidator)

    iso, ws_root = _setup_workspace(tmp_path, (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))
    backend = _FixedTokenBackend(vary_output=True)
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(0)"],
        strategy_name="monolithic",
        max_attempts=3,
    )
    record = runner.run(_make_scenario())
    assert record.status == RunStatus.failed
    assert math.isclose(record.baseline_validation_duration_seconds, 1.5, rel_tol=1e-9, abs_tol=1e-9)
    assert record.repair_attempts == 2


def test_public_repair_accumulates_evaluator_duration_across_attempts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult

    def _failing_evaluator(
        canonical_project_root=None,
        evaluator_asset=None,
        generated_workspace=None,
        python_executable=None,
        timeout=None,
    ) -> ScenarioEvaluatorResult:
        return ScenarioEvaluatorResult(
            passed=False, exit_code=1, stdout="", stderr="", error="evaluator failure",
            checks=(), duration_seconds=0.7,
        )

    monkeypatch.setattr(
        "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
        _failing_evaluator,
    )

    iso, ws_root = _setup_workspace(tmp_path, (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))
    backend = _FixedTokenBackend(vary_output=True)
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    scenario = _make_scenario(evaluator_asset="evaluator.py")
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(0)"],
        strategy_name="monolithic",
        max_attempts=3,
        canonical_project_root=tmp_path,
    )
    record = runner.run(scenario)
    assert record.status == RunStatus.failed
    assert math.isclose(record.scenario_evaluator_duration_seconds, 2.1, rel_tol=1e-9, abs_tol=1e-9)
    assert record.repair_attempts == 2


def test_public_total_duration_equals_stage_sum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from benchmark.execution.validation import FunctionalValidationResult

    class _FailingBaselineValidator:
        def validate(self, workspace_root=None, command=None, timeout=None) -> FunctionalValidationResult:
            return FunctionalValidationResult(
                passed=False, exit_code=1, stdout="baseline failure", stderr="",
                duration_seconds=0.5,
            )

    monkeypatch.setattr("benchmark.execution.runner.FunctionalValidator", _FailingBaselineValidator)

    iso, ws_root = _setup_workspace(tmp_path, (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),))
    backend = _FixedTokenBackend(vary_output=True)
    from benchmark.strategies import MonolithicRegenerationStrategy
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(0)"],
        strategy_name="monolithic",
        max_attempts=3,
    )
    record = runner.run(_make_scenario())
    stage_sum = (
        record.selection_duration_seconds
        + record.regeneration_duration_seconds
        + record.repair_duration_seconds
        + record.migration_duration_seconds
        + record.baseline_validation_duration_seconds
        + record.scenario_evaluator_duration_seconds
    )
    assert math.isclose(
        record.total_workflow_duration_seconds, stage_sum,
        rel_tol=1e-9, abs_tol=1e-9,
    )
    assert math.isclose(record.baseline_validation_duration_seconds, 1.5, rel_tol=1e-9, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# M. Sentinel arithmetic test
# ---------------------------------------------------------------------------


def test_public_runner_to_jsonl_to_reporting_preserves_metric_identity(tmp_path: Path) -> None:
    from benchmark.strategies import MonolithicRegenerationStrategy

    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    call_responses = [
        TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18),
        TokenUsage(prompt_tokens=13, completion_tokens=5, total_tokens=18),
        TokenUsage(prompt_tokens=17, completion_tokens=6, total_tokens=23),
    ]
    backend = _SentinelBackend(call_responses)
    strategy = MonolithicRegenerationStrategy()
    runner = _make_runner(
        tmp_path, strategy, backend, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="monolithic",
        max_attempts=3,
        editable_artifact_paths=("src/a.py",),
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.failed

    d = asdict(record)
    d["max_completion_tokens_per_call"] = 2048
    d["max_total_workflow_tokens"] = 9000

    assert d["selection_prompt_tokens"] == 0
    assert d["selection_completion_tokens"] == 0
    assert d["selection_total_tokens"] == 0
    assert d["selection_model_calls"] == 0
    assert d["selection_tool_calls"] == 0
    assert d["selection_inspected_file_count"] == 0
    assert d["selection_tool_transcript"] == ()
    assert d["regeneration_prompt_tokens"] == 11
    assert d["regeneration_completion_tokens"] == 7
    assert d["regeneration_total_tokens"] == 18
    assert d["regeneration_model_calls"] == 1
    assert d["repair_prompt_tokens"] == 30
    assert d["repair_completion_tokens"] == 11
    assert d["repair_total_tokens"] == 41
    assert d["repair_model_calls"] == 2
    assert d["repair_attempts"] == 2
    assert d["migration_duration_seconds"] == 0.0
    assert d["scenario_evaluator_duration_seconds"] == 0.0
    assert d["scenario_evaluator_checks"] == ()
    assert d["total_workflow_tokens"] == 59
    assert d["total_workflow_model_calls"] == 3
    assert d["selected_artifact_count"] == 1
    assert d["regenerated_artifact_count"] == 1
    assert d["preserved_artifact_count"] == 0
    assert d["unresolved_human_review_count"] == 0
    assert d["token_accounting_mode"] == "fixture_or_approximate"
    assert d["token_usage"] == {"prompt_tokens": 41, "completion_tokens": 18, "total_tokens": 59}

    from seven_arm_benchmark import _to_run_record_data
    rd = _to_run_record_data(
        d,
        run_id="r4_boundary_test",
        profile="smoke",
        repository_id="test_repo",
        scenario_id="test_r4",
        strategy_id="monolithic",
        repetition=1,
        model_identity="mock",
        dry_run=True,
        protocol_version="1.0",
        source_commit="abc",
        config_hash="test",
        started_at="now",
        ended_at="now",
        hw_id="cpu",
        sw_id="python3.11",
        max_attempts=3,
    )
    assert rd.selection_prompt_tokens == 0
    assert rd.selection_total_tokens == 0
    assert rd.regeneration_prompt_tokens == 11
    assert rd.regeneration_total_tokens == 18
    assert rd.repair_prompt_tokens == 30
    assert rd.repair_total_tokens == 41
    assert rd.repair_attempts == 2
    assert rd.total_workflow_tokens == 59
    assert rd.total_workflow_model_calls == 3
    assert rd.selected_artifact_count == 1
    assert rd.regenerated_artifact_count == 1
    assert rd.preserved_artifact_count == 0
    assert rd.unresolved_human_review_count == 0
    assert rd.token_accounting_mode == "fixture_or_approximate"
    assert rd.model_metadata["max_completion_tokens_per_call"] == "2048"
    assert rd.model_metadata["max_total_workflow_tokens"] == "9000"

    store = RunRecordStore(tmp_path / "runs_final")
    store.append(rd)
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].selection_total_tokens == 0
    assert loaded[0].regeneration_total_tokens == 18
    assert loaded[0].repair_prompt_tokens == 30
    assert loaded[0].repair_total_tokens == 41
    assert loaded[0].repair_attempts == 2
    assert loaded[0].total_workflow_tokens == 59
    assert loaded[0].selected_artifact_count == 1
    assert loaded[0].regenerated_artifact_count == 1
    assert loaded[0].preserved_artifact_count == 0
    assert loaded[0].unresolved_human_review_count == 0
    assert loaded[0].token_accounting_mode == "fixture_or_approximate"
    assert loaded[0].model_metadata["max_completion_tokens_per_call"] == "2048"
    assert loaded[0].model_metadata["max_total_workflow_tokens"] == "9000"

    exporter = NotebookExporter()
    export = exporter.export(results=(), records=(record,))
    rec = export["records"][0]
    assert rec["selection_total_tokens"] == 0
    assert rec["selection_model_calls"] == 0
    assert rec["selection_tool_calls"] == 0
    assert rec["selection_inspected_file_count"] == 0
    assert rec["regeneration_prompt_tokens"] == 11
    assert rec["regeneration_total_tokens"] == 18
    assert rec["regeneration_model_calls"] == 1
    assert rec["repair_prompt_tokens"] == 30
    assert rec["repair_total_tokens"] == 41
    assert rec["repair_model_calls"] == 2
    assert rec["repair_attempts"] == 2
    assert rec["migration_duration_seconds"] == 0.0
    assert rec["scenario_evaluator_duration_seconds"] == 0.0
    assert rec["scenario_evaluator_checks"] == []
    assert rec["total_workflow_tokens"] == 59
    assert rec["total_workflow_model_calls"] == 3
    assert rec["selected_artifact_count"] == 1
    assert rec["regenerated_artifact_count"] == 1
    assert rec["preserved_artifact_count"] == 0
    assert rec["unresolved_human_review_count"] == 0
    assert rec["token_accounting_mode"] == "fixture_or_approximate"
    assert rec["token_usage"] == {"prompt_tokens": 41, "completion_tokens": 18, "total_tokens": 59}


# ---------------------------------------------------------------------------
# Agent public path tests
# ---------------------------------------------------------------------------


def test_public_agent_selection_revision_and_code_repair_are_separate(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    sb = _StrategyBackend(responses=[
        ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "first"}', TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60)),
        ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "second"}', TokenUsage(prompt_tokens=60, completion_tokens=15, total_tokens=75)),
    ])
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    rb = _FixedTokenBackend()
    scenario = _make_scenario(artifacts)
    runner = _make_runner(
        tmp_path, strategy, rb, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="iterative_repository_agent",
        max_attempts=3,
    )
    record = runner.run(scenario)
    assert record.status == RunStatus.failed
    assert record.selection_model_calls >= 1
    assert record.regeneration_model_calls >= 1 or record.repair_model_calls >= 1
    total = record.selection_total_tokens + record.regeneration_total_tokens + record.repair_total_tokens
    assert record.total_workflow_tokens == total
    assert record.selection_total_tokens > 0


def test_public_agent_selection_tokens_are_not_double_counted(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    sb = _StrategyBackend(responses=[
        ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "first"}', TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60)),
    ])
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    rb = _FixedTokenBackend()
    runner = _make_runner(
        tmp_path, strategy, rb, iso,
        enable_regeneration=True,
        strategy_name="iterative_repository_agent",
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.succeeded
    assert record.selection_prompt_tokens == 50
    assert record.selection_completion_tokens == 10
    assert record.selection_total_tokens == 60
    assert record.selection_model_calls == 1
    assert record.regeneration_total_tokens == 15
    assert record.regeneration_model_calls == 1
    assert record.repair_total_tokens == 0
    assert record.total_workflow_tokens == 75
    assert record.total_workflow_tokens == (
        record.selection_total_tokens
        + record.regeneration_total_tokens
        + record.repair_total_tokens
    )


def test_public_agent_tool_duration_is_submetric_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from benchmark.strategies.repository_tools import RepositoryTools
    original_list_files = RepositoryTools.list_files

    def _slow_list_files(self, path: str) -> list[str]:
        time.sleep(0.05)
        return original_list_files(self, path)

    monkeypatch.setattr(RepositoryTools, "list_files", _slow_list_files)

    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    sb = _StrategyBackend(responses=[
        ('{"action": "list_files", "path": "."}', TokenUsage(prompt_tokens=30, completion_tokens=5, total_tokens=35)),
        ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "second"}', TokenUsage(prompt_tokens=20, completion_tokens=5, total_tokens=25)),
    ])
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    rb = _FixedTokenBackend()
    runner = _make_runner(
        tmp_path, strategy, rb, iso,
        enable_regeneration=True,
        strategy_name="iterative_repository_agent",
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.succeeded
    assert record.selection_tool_calls == 1
    assert record.selection_tool_duration_seconds > 0
    assert record.selection_duration_seconds >= record.selection_tool_duration_seconds
    stage_sum = (
        record.selection_duration_seconds
        + record.regeneration_duration_seconds
        + record.repair_duration_seconds
        + record.migration_duration_seconds
        + record.baseline_validation_duration_seconds
        + record.scenario_evaluator_duration_seconds
    )
    assert math.isclose(
        record.total_workflow_duration_seconds, stage_sum,
        rel_tol=1e-9, abs_tol=1e-9,
    )


def test_public_agent_failed_run_preserves_selection_and_repair_metrics(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    sb = _StrategyBackend(responses=[
        ('{"action": "final", "selected_paths": ["src/a.py"], "rationale": "first"}', TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60)),
    ])
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    rb = _FixedTokenBackend()
    runner = _make_runner(
        tmp_path, strategy, rb, iso,
        enable_regeneration=True,
        validation_command=[sys.executable, "-c", "exit(1)"],
        strategy_name="iterative_repository_agent",
        max_attempts=3,
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.failed
    assert record.selection_total_tokens == 180
    assert record.selection_model_calls == 3
    assert record.regeneration_total_tokens == 15
    assert record.regeneration_model_calls == 1
    assert record.repair_total_tokens == 15
    assert record.repair_model_calls == 1
    assert record.repair_attempts == 1
    assert record.total_workflow_tokens == 210


# ---------------------------------------------------------------------------
# N. Exact-exhaustion production-path regression (R4 audit correction)
# ---------------------------------------------------------------------------


def test_public_iterative_agent_exact_exhaustion_is_not_reopened(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    ab = _ExactExhaustToolBackend(TokenUsage(prompt_tokens=0, completion_tokens=20, total_tokens=20))
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=ab)
    runner = _make_runner(
        tmp_path, strategy, ab, iso,
        enable_regeneration=True,
        strategy_name="iterative_repository_agent",
        max_attempts=3,
        max_tokens=20,
        editable_artifact_paths=("src/a.py",),
    )
    record = runner.run(_make_scenario(artifacts))
    assert ab.call_count == 1
    assert ab.captured_max_tokens == [20]
    assert record.selection_model_calls == 1
    assert record.regeneration_model_calls == 0
    assert record.repair_model_calls == 0
    assert record.total_workflow_model_calls == 1
    assert record.selection_total_tokens == 20
    assert record.regeneration_total_tokens == 0
    assert record.total_workflow_tokens == 20
    assert record.regenerated_artifact_count == 0
    assert record.status == RunStatus.failed
    assert any("no paths selected" in f.message for f in record.failures)


def test_public_iterative_agent_unlimited_workflow_stays_unlimited(tmp_path: Path) -> None:
    artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    iso, ws_root = _setup_workspace(tmp_path, artifacts)
    sb = _StrategyBackend(responses=[
        (
            '{"action": "final", "selected_paths": ["src/a.py"], "rationale": "ok"}',
            TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
        ),
    ])
    from benchmark.strategies import IterativeRepositoryAgentStrategy
    strategy = IterativeRepositoryAgentStrategy(backend=sb)
    rb = _FixedTokenBackend()
    runner = _make_runner(
        tmp_path, strategy, rb, iso,
        enable_regeneration=True,
        strategy_name="iterative_repository_agent",
        max_tokens=0,
        editable_artifact_paths=("src/a.py",),
    )
    record = runner.run(_make_scenario(artifacts))
    assert record.status == RunStatus.succeeded
    assert sb.call_count == 1
    assert sb.captured_max_tokens == [4096]
    assert record.selection_model_calls == 1
    assert record.selection_total_tokens == 60
    assert record.regeneration_model_calls == 1
    assert record.total_workflow_tokens == 75
