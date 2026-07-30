from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from benchmark.core.models import RunRecord
from benchmark.evaluation.engine import EvaluationResult


@dataclass(frozen=True)
class ExportConfig:
    format: str = "json"
    include_metadata: bool = True
    pretty_print: bool = True


class NotebookExporter:
    def __init__(self, config: ExportConfig | None = None) -> None:
        self._config = config or ExportConfig()

    def export(
        self,
        results: tuple[EvaluationResult, ...],
        records: tuple[RunRecord, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        export_data: dict[str, Any] = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "results_count": len(results),
            "results": [self._serialize_result(r) for r in results],
        }

        if records:
            export_data["records"] = [self._serialize_record(r) for r in records]

        if metadata:
            export_data["metadata"] = metadata

        return export_data

    def export_to_json(
        self,
        results: tuple[EvaluationResult, ...],
        records: tuple[RunRecord, ...] | None = None,
        metadata: dict[str, Any] | None = None,
        path: str | Path | None = None,
    ) -> str:
        data = self.export(results, records, metadata)

        json_str = json.dumps(data, indent=2 if self._config.pretty_print else None, default=str)

        if path:
            Path(path).write_text(json_str)

        return json_str

    def export_to_dataframe(
        self,
        results: tuple[EvaluationResult, ...],
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []

        for result in results:
            base_row = {
                "scenario_id": result.scenario_id,
                "strategy_name": result.strategy_name,
                "passed": result.passed,
                "message": result.message,
            }

            for metric in result.metrics:
                base_row[metric.name] = metric.value

            rows.append(base_row)

        return pd.DataFrame(rows)

    def _serialize_result(self, result: EvaluationResult) -> dict[str, Any]:
        return {
            "scenario_id": result.scenario_id,
            "strategy_name": result.strategy_name,
            "passed": result.passed,
            "message": result.message,
            "metrics": [
                {"name": m.name, "value": m.value, "unit": m.unit, "details": m.details}
                for m in result.metrics
            ],
        }

    def _serialize_record(self, record: RunRecord) -> dict[str, Any]:
        return {
            "run_id": record.identity.run_id,
            "protocol_version": record.identity.protocol_version,
            "repository_commit_sha": record.identity.repository_commit_sha,
            "scenario_id": record.identity.scenario_id,
            "strategy_name": record.identity.strategy_name,
            "timestamp": record.identity.timestamp.isoformat() if record.identity.timestamp else None,
            "status": record.status.value,
            "duration_seconds": record.duration_seconds,
            "token_usage": {
                "prompt_tokens": record.token_usage.prompt_tokens,
                "completion_tokens": record.token_usage.completion_tokens,
                "total_tokens": record.token_usage.total_tokens,
            } if record.token_usage else None,
            "prediction": self._serialize_prediction(record.prediction) if record.prediction else None,
            "failures": [
                {"failure_kind": f.failure_kind.value, "message": f.message, "details": f.details}
                for f in record.failures
            ] if record.failures else None,
            # End-to-end workflow metrics (SU-0010B2)
            "selection_prompt_tokens": record.selection_prompt_tokens,
            "selection_completion_tokens": record.selection_completion_tokens,
            "selection_total_tokens": record.selection_total_tokens,
            "selection_model_calls": record.selection_model_calls,
            "selection_duration_seconds": record.selection_duration_seconds,
            "regeneration_prompt_tokens": record.regeneration_prompt_tokens,
            "regeneration_completion_tokens": record.regeneration_completion_tokens,
            "regeneration_total_tokens": record.regeneration_total_tokens,
            "regeneration_model_calls": record.regeneration_model_calls,
            "regeneration_duration_seconds": record.regeneration_duration_seconds,
            "functional_validation_duration_seconds": record.functional_validation_duration_seconds,
            "functional_validation_passed": record.functional_validation_passed,
            "migration_generation_passed": record.migration_generation_passed,
            "migration_duration_seconds": record.migration_duration_seconds,
            "generated_migration_paths": list(record.generated_migration_paths),
            "baseline_validation_passed": record.baseline_validation_passed,
            "baseline_validation_duration_seconds": record.baseline_validation_duration_seconds,
            "scenario_evaluator_passed": record.scenario_evaluator_passed,
            "scenario_evaluator_duration_seconds": record.scenario_evaluator_duration_seconds,
            "scenario_evaluator_checks": list(record.scenario_evaluator_checks),
            "total_workflow_tokens": record.total_workflow_tokens,
            "total_workflow_model_calls": record.total_workflow_model_calls,
            "total_workflow_duration_seconds": record.total_workflow_duration_seconds,
            "selected_artifact_count": record.selected_artifact_count,
            "regenerated_artifact_count": record.regenerated_artifact_count,
            "preserved_artifact_count": record.preserved_artifact_count,
            "unresolved_human_review_count": record.unresolved_human_review_count,
        }

    def _serialize_prediction(self, prediction: Any) -> dict[str, Any] | None:
        if not prediction:
            return {}
        return {
            "decisions": [
                {
                    "artifact": {"path": d.artifact.path, "artifact_type": d.artifact.artifact_type.value},
                    "action": d.action.value,
                    "rationale": d.rationale,
                    "supporting_evidence": [
                        {"description": e.description, "source": e.source}
                        for e in d.supporting_evidence
                    ] if d.supporting_evidence else None,
                }
                for d in prediction.decisions
            ],
            "errors": list(prediction.errors) if prediction.errors else None,
        }


class PublicationTableBuilder:
    def __init__(self) -> None:
        self._format_precision = 4

    def build_strategy_comparison_table(
        self,
        results: tuple[EvaluationResult, ...],
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []

        for result in results:
            row = {
                "Scenario": result.scenario_id,
                "Strategy": result.strategy_name,
                "Passed": result.passed,
            }

            for metric in result.metrics:
                if metric.value is not None:
                    row[metric.name] = round(metric.value, self._format_precision)
                else:
                    row[metric.name] = "N/A"

            rows.append(row)

        df = pd.DataFrame(rows)

        columns = ["Scenario", "Strategy", "Passed"]
        metric_cols = [m.name for m in results[0].metrics if results[0].metrics]
        columns.extend(metric_cols)

        df = df[[c for c in columns if c in df.columns]]

        return df

    def build_repository_summary_table(
        self,
        results: tuple[EvaluationResult, ...],
    ) -> pd.DataFrame:
        repo_data: dict[str, dict[str, int]] = {}

        for result in results:
            repo = result.scenario_id.rsplit("-", 2)[0] if "-" in result.scenario_id else result.scenario_id
            if repo not in repo_data:
                repo_data[repo] = {"total": 0, "passed": 0, "failed": 0}

            repo_data[repo]["total"] += 1
            if result.passed:
                repo_data[repo]["passed"] += 1
            else:
                repo_data[repo]["failed"] += 1

        rows = []
        for repo, stats in repo_data.items():
            total = stats["total"]
            pass_rate = round(stats["passed"] / total, self._format_precision) if total > 0 else 0
            rows.append(
                {
                    "Repository": repo,
                    "Total Runs": total,
                    "Passed": stats["passed"],
                    "Failed": stats["failed"],
                    "Pass Rate": pass_rate,
                }
            )

        return pd.DataFrame(rows)

    def build_aggregate_table(
        self,
        results: tuple[EvaluationResult, ...],
    ) -> pd.DataFrame:
        strategy_data: dict[str, dict[str, Any]] = {}

        for result in results:
            strategy = result.strategy_name
            if strategy not in strategy_data:
                strategy_data[strategy] = {"total": 0, "passed": 0, "metrics": {}}

            strategy_data[strategy]["total"] += 1
            if result.passed:
                strategy_data[strategy]["passed"] += 1

            for metric in result.metrics:
                if metric.name not in strategy_data[strategy]["metrics"]:
                    strategy_data[strategy]["metrics"][metric.name] = []
                if metric.value is not None:
                    strategy_data[strategy]["metrics"][metric.name].append(metric.value)

        rows = []
        for strategy, data in strategy_data.items():
            row = {
                "Strategy": strategy,
                "Total Runs": data["total"],
                "Passed": data["passed"],
                "Pass Rate": round(data["passed"] / data["total"], self._format_precision) if data["total"] > 0 else 0,
            }

            for metric_name, values in data["metrics"].items():
                if values:
                    row[f"{metric_name}_mean"] = round(float(np.mean(values)), self._format_precision)
                    row[f"{metric_name}_std"] = round(float(np.std(values)), self._format_precision)

            rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def build_latex_table(
        self,
        df: pd.DataFrame,
        caption: str = "",
        label: str = "",
    ) -> str:
        result = df.to_latex(caption=caption, label=label, index=False)
        return str(result)

    def build_markdown_table(self, df: pd.DataFrame) -> str:
        result = df.to_markdown(index=False)
        return str(result)

    def export_all_formats(
        self,
        results: tuple[EvaluationResult, ...],
        output_dir: str | Path,
        prefix: str = "evaluation",
    ) -> dict[str, str]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        files: dict[str, str] = {}

        strategy_df = self.build_strategy_comparison_table(results)
        files[f"{prefix}_strategy_comparison.csv"] = strategy_df.to_csv(index=False)
        files[f"{prefix}_strategy_comparison.md"] = strategy_df.to_markdown(index=False)

        repo_df = self.build_repository_summary_table(results)
        files[f"{prefix}_repository_summary.csv"] = repo_df.to_csv(index=False)
        files[f"{prefix}_repository_summary.md"] = repo_df.to_markdown(index=False)

        agg_df = self.build_aggregate_table(results)
        files[f"{prefix}_aggregate.csv"] = agg_df.to_csv(index=False)
        files[f"{prefix}_aggregate.md"] = agg_df.to_markdown(index=False)

        for name, content in files.items():
            if name.endswith(".csv") or name.endswith(".md"):
                (output_dir / name).write_text(content)

        return files
