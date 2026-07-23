from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from benchmark.core.exceptions import RepositoryError


@dataclass(frozen=True)
class WorkspacePath:
    root: str
    snapshots_dir: str = "snapshots"
    runs_dir: str = "runs"
    temp_dir: str = "tmp"

    def __post_init__(self) -> None:
        if not self.root:
            raise ValueError("WorkspacePath.root must not be empty")

    @property
    def snapshots(self) -> Path:
        return Path(self.root) / self.snapshots_dir

    @property
    def runs(self) -> Path:
        return Path(self.root) / self.runs_dir

    @property
    def temp(self) -> Path:
        return Path(self.root) / self.temp_dir


def validate_workspace_path(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise RepositoryError(f"Workspace path does not exist: {resolved}")
    if not resolved.is_dir():
        raise RepositoryError(f"Workspace path is not a directory: {resolved}")
    return resolved


def check_isolation(workspace: Path, snapshot_base: Path) -> list[str]:
    violations: list[str] = []
    try:
        ws_resolved = workspace.resolve()
        snap_resolved = snapshot_base.resolve()
    except (OSError, ValueError) as e:
        violations.append(f"Path resolution error: {e}")
        return violations

    if snap_resolved == ws_resolved:
        violations.append(
            f"Snapshot directory is the same as workspace root: {snap_resolved}"
        )
        return violations

    return violations
