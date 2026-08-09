from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from benchmark.core.enums import RunStatus
from benchmark.core.models import RunIdentity, RunRecord, TokenUsage
from benchmark.evaluation.engine import EvaluationResult
from benchmark.statistics.reporting import ExportConfig, NotebookExporter, PublicationTableBuilder


def _make_evaluation_result(
    scenario_id: str = "test-001",
    strategy_name: str = "strategy-a",
    passed: bool = True,
    metrics: tuple[Any, ...] = (),
) -> EvaluationResult:
    return EvaluationResult(
        scenario_id=scenario_id,
        strategy_name=strategy_name,
        passed=passed,
        message="Test message",
        metrics=metrics,
    )


class TestExportConfig:
    def test_defaults(self) -> None:
        config = ExportConfig()
        assert config.format == "json"
        assert config.include_metadata is True
        assert config.pretty_print is True

    def test_custom_values(self) -> None:
        config = ExportConfig(format="csv", include_metadata=False, pretty_print=False)
        assert config.format == "csv"
        assert config.include_metadata is False
        assert config.pretty_print is False


class TestNotebookExporter:
    def test_export_basic(self) -> None:
        exporter = NotebookExporter()
        results = (_make_evaluation_result(),)

        data = exporter.export(results)

        assert "version" in data
        assert "results_count" in data
        assert data["results_count"] == 1

    def test_export_with_metadata(self) -> None:
        exporter = NotebookExporter()
        results = (_make_evaluation_result(),)
        metadata = {"note": "test metadata"}

        data = exporter.export(results, metadata=metadata)

        assert "metadata" in data
        assert data["metadata"]["note"] == "test metadata"

    def test_export_to_json_string(self) -> None:
        exporter = NotebookExporter(ExportConfig(pretty_print=False))
        results = (_make_evaluation_result(),)

        json_str = exporter.export_to_json(results)

        parsed = json.loads(json_str)
        assert parsed["results_count"] == 1

    def test_export_to_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotebookExporter()
            results = (_make_evaluation_result(),)
            path = Path(tmpdir) / "test_export.json"

            exporter.export_to_json(results, path=str(path))

            assert path.exists()
            content = path.read_text()
            parsed = json.loads(content)
            assert parsed["results_count"] == 1

    def test_export_to_dataframe(self) -> None:
        exporter = NotebookExporter()
        results = (
            _make_evaluation_result(
                scenario_id="test-001",
                strategy_name="strategy-a",
                passed=True,
            ),
            _make_evaluation_result(
                scenario_id="test-002",
                strategy_name="strategy-b",
                passed=False,
            ),
        )

        df = exporter.export_to_dataframe(results)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "scenario_id" in df.columns
        assert "strategy_name" in df.columns
        assert "passed" in df.columns


class TestPublicationTableBuilder:
    def test_build_strategy_comparison_table(self) -> None:
        builder = PublicationTableBuilder()
        results = (
            _make_evaluation_result(scenario_id="test-001", strategy_name="strategy-a", passed=True),
            _make_evaluation_result(scenario_id="test-002", strategy_name="strategy-b", passed=False),
        )

        df = builder.build_strategy_comparison_table(results)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "Scenario" in df.columns
        assert "Strategy" in df.columns
        assert "Passed" in df.columns

    def test_build_repository_summary_table(self) -> None:
        builder = PublicationTableBuilder()
        results = (
            _make_evaluation_result(scenario_id="repo1-test-001", strategy_name="strategy-a", passed=True),
            _make_evaluation_result(scenario_id="repo1-test-002", strategy_name="strategy-a", passed=False),
            _make_evaluation_result(scenario_id="repo2-test-001", strategy_name="strategy-b", passed=True),
        )

        df = builder.build_repository_summary_table(results)

        assert isinstance(df, pd.DataFrame)
        assert "Repository" in df.columns
        assert "Pass Rate" in df.columns

    def test_build_aggregate_table(self) -> None:
        builder = PublicationTableBuilder()
        results = (
            _make_evaluation_result(scenario_id="test-001", strategy_name="strategy-a", passed=True),
            _make_evaluation_result(scenario_id="test-002", strategy_name="strategy-a", passed=True),
            _make_evaluation_result(scenario_id="test-003", strategy_name="strategy-b", passed=False),
        )

        df = builder.build_aggregate_table(results)

        assert isinstance(df, pd.DataFrame)
        assert "Strategy" in df.columns
        assert "Pass Rate" in df.columns

    def test_build_latex_table(self) -> None:
        builder = PublicationTableBuilder()
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        latex = builder.build_latex_table(df, caption="Test", label="tab:test")

        assert isinstance(latex, str)
        assert "Test" in latex
        assert "tab:test" in latex

    def test_build_markdown_table(self) -> None:
        builder = PublicationTableBuilder()
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        md = builder.build_markdown_table(df)

        assert isinstance(md, str)
        assert "|" in md

    def test_export_all_formats(self) -> None:
        builder = PublicationTableBuilder()

        with tempfile.TemporaryDirectory() as tmpdir:
            results = (_make_evaluation_result(),)
            files = builder.export_all_formats(results, output_dir=tmpdir, prefix="test")

            assert "test_strategy_comparison.csv" in files
            assert "test_strategy_comparison.md" in files
            assert "test_repository_summary.csv" in files
            assert "test_aggregate.csv" in files


class TestNotebookExporterSerialization:
    def test_serialize_result(self) -> None:
        exporter = NotebookExporter()
        result = _make_evaluation_result()

        serialized = exporter._serialize_result(result)

        assert serialized["scenario_id"] == result.scenario_id
        assert serialized["strategy_name"] == result.strategy_name
        assert serialized["passed"] == result.passed

    def test_serialize_record(self) -> None:
        exporter = NotebookExporter()
        record = RunRecord(
            identity=RunIdentity(
                run_id="test-run",
                protocol_version="1.0",
                repository_commit_sha="abc123",
                scenario_id="test-scenario",
                strategy_name="test-strategy",
            ),
            status=RunStatus.succeeded,
            duration_seconds=1.5,
        )

        serialized = exporter._serialize_record(record)

        assert serialized["run_id"] == "test-run"
        assert serialized["status"] == "succeeded"
        assert serialized["duration_seconds"] == 1.5

    def test_serialize_record_with_end_to_end_metrics(self) -> None:
        exporter = NotebookExporter()
        record = RunRecord(
            identity=RunIdentity(
                run_id="e2e-run",
                protocol_version="1.0",
                repository_commit_sha="abc123",
                scenario_id="test-scenario",
                strategy_name="selective",
            ),
            status=RunStatus.succeeded,
            duration_seconds=5.25,
            token_usage=TokenUsage(prompt_tokens=42, completion_tokens=44, total_tokens=86),
            selection_prompt_tokens=11,
            selection_completion_tokens=12,
            selection_total_tokens=23,
            selection_model_calls=1,
            selection_duration_seconds=3.25,
            regeneration_prompt_tokens=31,
            regeneration_completion_tokens=32,
            regeneration_total_tokens=63,
            regeneration_model_calls=3,
            regeneration_duration_seconds=2.0,
            functional_validation_duration_seconds=4.5,
            functional_validation_passed=True,
            total_workflow_tokens=86,
            total_workflow_model_calls=4,
            total_workflow_duration_seconds=5.25,
            selected_artifact_count=5,
            regenerated_artifact_count=3,
            preserved_artifact_count=1,
            unresolved_human_review_count=1,
        )

        serialized = exporter._serialize_record(record)

        assert serialized["selection_total_tokens"] == 23
        assert serialized["selection_model_calls"] == 1
        assert serialized["regeneration_total_tokens"] == 63
        assert serialized["regeneration_model_calls"] == 3
        assert serialized["functional_validation_duration_seconds"] == 4.5
        assert serialized["functional_validation_passed"] is True
        assert serialized["total_workflow_tokens"] == 86
        assert serialized["total_workflow_model_calls"] == 4
        assert serialized["total_workflow_duration_seconds"] == 5.25
        assert serialized["selected_artifact_count"] == 5
        assert serialized["regenerated_artifact_count"] == 3
        assert serialized["preserved_artifact_count"] == 1
        # Legacy fields preserved
        assert serialized["duration_seconds"] == 5.25
        assert serialized["token_usage"] is not None

    def test_serialize_record_with_functional_validation_none(self) -> None:
        exporter = NotebookExporter()
        record = RunRecord(
            identity=RunIdentity(
                run_id="none-fv",
                protocol_version="1.0",
                repository_commit_sha="abc",
                scenario_id="test",
                strategy_name="agent",
            ),
            status=RunStatus.succeeded,
            functional_validation_passed=None,
        )
        serialized = exporter._serialize_record(record)
        assert serialized["functional_validation_passed"] is None
