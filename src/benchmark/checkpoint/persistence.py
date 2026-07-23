from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    protocol_version: str = "1.0"
    source_commit: str = ""
    config_hash: str = ""
    timestamp: str = ""


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_config_hash(config_obj: object) -> str:
    raw = json.dumps(config_obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_run_id(scenario_id: str, strategy_name: str, repetition: int) -> str:
    return f"{scenario_id}_{strategy_name}_rep{repetition}_{uuid.uuid4().hex[:8]}"


class RunRecordStore:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._path = runs_dir / "run_records.jsonl"

    @property
    def path(self) -> Path:
        return self._path

    def append(self, record: RunRecordData) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
            f.flush()

    def load_all(self) -> list[RunRecordData]:
        if not self._path.is_file():
            return []
        records: list[RunRecordData] = []
        with open(self._path, "r", encoding="utf-8") as f:
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
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
