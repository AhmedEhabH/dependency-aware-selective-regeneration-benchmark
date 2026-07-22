from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from benchmark.repositories.workspace import WorkspacePath, check_isolation, validate_workspace_path


@dataclass(frozen=True)
class IsolationReport:
    passed: bool
    violations: tuple[str, ...] = ()
    message: str = ""


PathValidator = Callable[[Path], list[str]]


class IsolationContext:
    def __init__(
        self,
        workspace: WorkspacePath,
        snapshot_base: str | Path | None = None,
        validator: PathValidator | None = None,
    ) -> None:
        self._workspace = workspace
        self._snapshot_base = Path(snapshot_base) if snapshot_base else workspace.snapshots
        self._validator = validator or self._default_check

    @property
    def workspace(self) -> WorkspacePath:
        return self._workspace

    @property
    def snapshot_base(self) -> Path:
        return self._snapshot_base

    def verify(self) -> IsolationReport:
        ws_path = validate_workspace_path(self._workspace.root)
        violations: list[str] = check_isolation(ws_path, self._snapshot_base)
        violations.extend(self._validator(self._snapshot_base))
        if violations:
            return IsolationReport(
                passed=False,
                violations=tuple(violations),
                message="Isolation check failed: " + "; ".join(violations),
            )
        return IsolationReport(passed=True, message="Isolation check passed")

    def check_private_data_access(self, paths: tuple[str, ...]) -> IsolationReport:
        violations: list[str] = []
        for p in paths:
            resolved = Path(p).resolve()
            if not resolved.exists():
                continue
            if self._is_private_path(resolved):
                violations.append(f"Private data path detected: {resolved}")
        if violations:
            return IsolationReport(
                passed=False,
                violations=tuple(violations),
                message="Private data access detected: " + "; ".join(violations),
            )
        return IsolationReport(passed=True, message="No private data access detected")

    def make_run_directory(self, run_id: str) -> Path:
        run_dir = self._workspace.runs / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def make_temp_directory(self, prefix: str = "exec") -> Path:
        tmp_dir = self._workspace.temp / f"{prefix}_{id(self)}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    @staticmethod
    def _default_check(_base: Path) -> list[str]:
        return []

    @staticmethod
    def _is_private_path(path: Path) -> bool:
        private_indicators = {"private", "secret", "hidden", ".kaggle", "ground_truth"}
        return any(indicator in path.parts for indicator in private_indicators)
