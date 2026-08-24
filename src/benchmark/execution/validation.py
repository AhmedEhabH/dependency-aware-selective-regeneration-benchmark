from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionalValidationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


class FunctionalValidator:
    def validate(
        self,
        workspace_root: str | Path,
        command: list[str],
        timeout: int = 30,
        env: dict[str, str] | None = None,
    ) -> FunctionalValidationResult:
        """Run the validation command with cwd=workspace_root.

        ``env`` carries the frozen per-repository validation environment
        overrides (e.g. Saleor's DATABASE_URL/CACHE_URL/SECRET_KEY/TZ). The
        child process environment is the parent environment plus exactly these
        overrides; the parent's ``os.environ`` is never mutated.
        """
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(workspace_root),
                timeout=timeout,
                env=run_env,
            )
            duration = time.monotonic() - start
            return FunctionalValidationResult(
                passed=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            return FunctionalValidationResult(
                passed=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                duration_seconds=duration,
            )
        except FileNotFoundError:
            duration = time.monotonic() - start
            return FunctionalValidationResult(
                passed=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                duration_seconds=duration,
            )
        except OSError as e:
            duration = time.monotonic() - start
            return FunctionalValidationResult(
                passed=False,
                exit_code=-1,
                stdout="",
                stderr=f"OS error: {e}",
                duration_seconds=duration,
            )
