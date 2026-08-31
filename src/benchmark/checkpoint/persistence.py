from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("benchmark.persistence")


@dataclass
class RunRecordData:
    run_id: str
    profile: str
    repository_id: str
    scenario_id: str
    strategy_id: str
    repetition: int
    seed: int
    status: str
    failure_details: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0})
    duration_seconds: float = 0.0
    model_metadata: dict[str, str] = field(default_factory=dict)
    protocol_version: str = "1.1"
    source_commit: str = ""
    config_hash: str = ""
    timestamp: str = ""
    started_at: str = ""
    ended_at: str = ""
    model_calls: int = 0
    hardware_identity: str = ""
    software_environment_identity: str = ""
    failure_classification: str = ""

    # Selection stage metrics (SU-0010A)
    selection_prompt_tokens: int = 0
    selection_completion_tokens: int = 0
    selection_total_tokens: int = 0
    selection_model_calls: int = 0
    selection_duration_seconds: float = 0.0

    # Regeneration stage metrics
    regeneration_prompt_tokens: int = 0
    regeneration_completion_tokens: int = 0
    regeneration_total_tokens: int = 0
    regeneration_model_calls: int = 0
    regeneration_duration_seconds: float = 0.0

    # Functional validation stage metrics
    functional_validation_duration_seconds: float = 0.0
    functional_validation_passed: bool | None = None

    # Total workflow metrics (aggregated)
    total_workflow_tokens: int = 0
    total_workflow_model_calls: int = 0
    total_workflow_duration_seconds: float = 0.0

    # Migration generation stage metrics
    migration_generation_passed: bool | None = None
    migration_duration_seconds: float = 0.0
    generated_migration_paths: list[str] = field(default_factory=list)

    # Baseline validation stage metrics
    baseline_validation_passed: bool | None = None
    baseline_validation_duration_seconds: float = 0.0

    # Scenario evaluator stage metrics
    scenario_evaluator_passed: bool | None = None
    scenario_evaluator_duration_seconds: float = 0.0
    scenario_evaluator_checks: list[str] = field(default_factory=list)

    # Repair stage metrics
    repair_prompt_tokens: int = 0
    repair_completion_tokens: int = 0
    repair_total_tokens: int = 0
    repair_model_calls: int = 0
    repair_duration_seconds: float = 0.0
    repair_attempts: int = 0
    token_accounting_mode: str = "unknown"

    # Selection tool/agent stage metrics
    selection_tool_calls: int = 0
    selection_tool_duration_seconds: float = 0.0
    selection_inspected_file_count: int = 0
    selection_tool_transcript: list[str] = field(default_factory=list)

    # Artifact counting
    selected_artifact_count: int = 0
    regenerated_artifact_count: int = 0
    preserved_artifact_count: int = 0
    unresolved_human_review_count: int = 0


def _utc_now_str() -> str:
    return datetime.now(UTC).isoformat()


def compute_config_hash(config_obj: object) -> str:
    raw = json.dumps(config_obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def detect_hardware_identity() -> str:
    """Detect GPU hardware identity. Returns 'cpu' when no CUDA GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            capability = torch.cuda.get_device_capability(0)
            return f"{gpu_name}:sm_{capability[0]}{capability[1]}"
        return "cpu"
    except ImportError:
        return "cpu"


def detect_software_environment_identity() -> str:
    """Detect a deterministic software environment fingerprint."""
    import platform
    import sys
    parts: list[str] = [
        f"python={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        f"platform={platform.system().lower()}",
    ]
    try:
        import torch
        parts.append(f"torch={torch.__version__}")
        if torch.cuda.is_available():
            parts.append(f"cuda={torch.version.cuda}")
    except ImportError:
        parts.append("torch=absent")
    return "|".join(parts)


RETRYABLE_FAILURE_CLASSIFICATIONS: set[str] = {
    "environment_preflight",
    "environment",
    "gpu_incompatible",
    "cuda_error",
}


def failure_is_retryable(record: RunRecordData) -> bool:
    """Determine if a failed/cancelled run should be retried on resume.

    Environment-related failures are retryable because they may succeed on
    different hardware (e.g. T4 instead of P100).  Model-output and timeout
    failures are not retryable.
    """
    return record.failure_classification.lower() in RETRYABLE_FAILURE_CLASSIFICATIONS


def _records_content_equal(a: RunRecordData, b: RunRecordData) -> bool:
    """Compare two RunRecordData for content equality (ignoring timestamp)."""
    a_dict = asdict(a)
    b_dict = asdict(b)
    a_dict.pop("timestamp", None)
    b_dict.pop("timestamp", None)
    return a_dict == b_dict


def make_run_id(
    scenario_id: str,
    strategy_name: str,
    repetition: int,
    protocol_version: str = "",
    config_hash: str = "",
) -> str:
    payload = json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": repetition,
        "protocol_version": protocol_version,
        "config_hash": config_hash,
    }, sort_keys=True)
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{repetition}_{suffix}"


class RunRecordIntegrityError(Exception):
    """Raised when a Run ID already exists with conflicting content."""


class RunRecordStore:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._path = runs_dir / "run_records.jsonl"

    @property
    def path(self) -> Path:
        return self._path

    def append(self, record: RunRecordData) -> None:
        existing = self._index_by_run_id()
        if record.run_id in existing:
            existing_rec = existing[record.run_id]
            if _records_content_equal(existing_rec, record):
                logger.info("Idempotent skip: Run ID %s already exists with identical content", record.run_id)
                return
            raise RunRecordIntegrityError(
                f"Run ID '{record.run_id}' already exists with conflicting content. "
                f"Existing status={existing_rec.status}, new status={record.status}. "
                "This indicates a canonical Run ID collision."
            )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
            f.flush()

    def _index_by_run_id(self) -> dict[str, RunRecordData]:
        index: dict[str, RunRecordData] = {}
        for rec in self.load_all():
            index[rec.run_id] = rec
        return index

    def load_all(self) -> list[RunRecordData]:
        if not self._path.is_file():
            return []
        records: list[RunRecordData] = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(RunRecordData(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(f"Corrupted run record in {self._path}: {e}") from e
        return records

    def get_completed_run_ids(self) -> set[str]:
        return {r.run_id for r in self.load_all() if r.status in ("succeeded", "failed", "timed_out", "cancelled")}

    def count(self) -> int:
        if not self._path.is_file():
            return 0
        count = 0
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
