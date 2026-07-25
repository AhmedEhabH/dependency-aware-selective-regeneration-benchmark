from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class CheckpointData:
    profile: str
    execution_plan_hash: str
    planned_run_ids: list[str] = field(default_factory=list)
    completed_run_ids: list[str] = field(default_factory=list)
    failed_run_ids: list[str] = field(default_factory=list)
    succeeded_run_ids: list[str] = field(default_factory=list)
    retryable_run_ids: list[str] = field(default_factory=list)
    pending_run_ids: list[str] = field(default_factory=list)
    current_run_id: str = ""
    total_planned: int = 0
    total_completed: int = 0
    protocol_version: str = "1.0"
    model_identity: str = ""
    config_hash: str = ""
    source_commit: str = ""
    last_update: str = ""
    completion_status: str = "incomplete"
    scenario_ids: list[str] = field(default_factory=list)
    strategy_names: list[str] = field(default_factory=list)
    declared_source_tag: str = ""
    deployed_build_id: str = ""
    attempted_run_ids: list[str] = field(default_factory=list)


class CheckpointManager:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._path = runs_dir / "checkpoint.json"

    @property
    def path(self) -> Path:
        return self._path

    def write_atomic(self, data: CheckpointData) -> None:
        data.last_update = datetime.now(UTC).isoformat()
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".tmp",
            dir=str(self._runs_dir),
        )
        try:
            json.dump(asdict(data), tmp, indent=2, sort_keys=True)
            tmp.close()
            shutil.move(tmp.name, str(self._path))
        except Exception:
            Path(tmp.name).unlink(missing_ok=True)
            raise

    def read(self) -> CheckpointData | None:
        if not self._path.is_file():
            return None
        raw = self._path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
            return CheckpointData(**data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise ValueError(f"Corrupted checkpoint: {e}") from e

    def exists(self) -> bool:
        return self._path.is_file()

    def normalize_from_records(self, record_store: Any) -> CheckpointData | None:
        """Recompute checkpoint fields from run records, enforcing invariants.

        Used on resume to repair legacy checkpoints and corrupted state:
          attempted = succeeded ∪ failed
          pending = planned - attempted
          succeeded ∩ failed = ∅
          attempted ∩ pending = ∅
        """
        cp = self.read()
        if cp is None:
            return None

        from benchmark.checkpoint.persistence import failure_is_retryable

        records_by_id: dict[str, Any] = {}
        for rec in record_store.load_all():
            records_by_id[rec.run_id] = rec

        completed: list[str] = []
        succeeded: list[str] = []
        failed: list[str] = []
        retryable: list[str] = []

        for rid in cp.planned_run_ids:
            rec = records_by_id.get(rid)
            if rec is None:
                continue
            if rec.status in ("succeeded", "failed", "timed_out", "cancelled"):
                completed.append(rid)
                if rec.status == "succeeded":
                    succeeded.append(rid)
                else:
                    failed.append(rid)
                    if failure_is_retryable(rec):
                        retryable.append(rid)

        pending = [rid for rid in cp.planned_run_ids if rid not in completed]

        cp.completed_run_ids = completed
        cp.attempted_run_ids = list(completed)
        cp.succeeded_run_ids = succeeded
        cp.failed_run_ids = failed
        cp.retryable_run_ids = retryable
        cp.pending_run_ids = pending
        cp.total_completed = len(completed)

        self.write_atomic(cp)
        return cp


@dataclass
class ProgressData:
    profile: str
    total_planned: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_pending: int = 0
    elapsed_seconds: float = 0.0
    completion_ratio: float = 0.0
    stage: str = "running"
    last_update: str = ""
    # Cross-session fields (SU-0008)
    total_attempted: int = 0
    total_succeeded: int = 0
    total_retryable: int = 0
    completion_status: str = ""
    experiment_run_duration_seconds: float = 0.0
    session_elapsed_seconds: float = 0.0
    report_generated_at: str = ""
    experiment_wall_clock_seconds: float | None = None
    experiment_wall_clock_unavailable_reason: str = ""


class ProgressManager:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._path = runs_dir / "progress.json"
        self._partial_summary_path = runs_dir / "benchmark_summary.partial.json"
        self._final_summary_path = runs_dir / "benchmark_summary.json"
        self._completed_marker = runs_dir / "COMPLETED"

    @property
    def path(self) -> Path:
        return self._path

    def write(self, data: ProgressData) -> None:
        data.last_update = datetime.now(UTC).isoformat()
        self._path.write_text(
            json.dumps(asdict(data), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def write_partial_summary(self, summary: dict[str, Any]) -> None:
        self._partial_summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def write_final_summary(self, summary: dict[str, Any]) -> None:
        self._final_summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def mark_completed(self) -> None:
        self._completed_marker.write_text(
            json.dumps({
                "completed_at": datetime.now(UTC).isoformat(),
                "status": "completed",
            }),
            encoding="utf-8",
        )

    def is_completed(self) -> bool:
        return self._completed_marker.is_file()

    def read_progress(self) -> ProgressData | None:
        if not self._path.is_file():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return ProgressData(**data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Corrupted progress: {e}") from e
