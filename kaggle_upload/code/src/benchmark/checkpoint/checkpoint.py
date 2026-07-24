from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckpointData:
    profile: str
    execution_plan_hash: str
    planned_run_ids: list[str] = field(default_factory=list)
    completed_run_ids: list[str] = field(default_factory=list)
    failed_run_ids: list[str] = field(default_factory=list)
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


class CheckpointManager:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._path = runs_dir / "checkpoint.json"

    @property
    def path(self) -> Path:
        return self._path

    def write_atomic(self, data: CheckpointData) -> None:
        data.last_update = datetime.now(timezone.utc).isoformat()
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
        data.last_update = datetime.now(timezone.utc).isoformat()
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
                "completed_at": datetime.now(timezone.utc).isoformat(),
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
