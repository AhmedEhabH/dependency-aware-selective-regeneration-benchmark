from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScenarioEvaluatorResult:
    passed: bool
    exit_code: int
    checks: tuple[str, ...]
    error: str
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass(frozen=True)
class _ValidatedEvaluatorRequest:
    canonical_project_root: Path
    evaluator_root: Path
    evaluator_asset_path: Path
    evaluator_asset_relative: str
    generated_workspace: Path
    python_executable: str
    timeout: int


@dataclass(frozen=True)
class _TrustedEvaluatorAsset:
    source_path: Path
    relative_path: str
    content: bytes
    sha256: str


@dataclass(frozen=True)
class _EvaluatorCommandOutcome:
    succeeded: bool
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class _ParsedEvaluatorPayload:
    passed: bool
    checks: tuple[str, ...]
    error: str


_EVALUATOR_ASSETS_PREFIX = "tests/evaluator_assets/"


def _coerce_subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _containment_check(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _validate_evaluator_request(
    canonical_project_root: str | Path,
    evaluator_asset: str,
    generated_workspace: str | Path,
    *,
    python_executable: str,
    timeout: int,
) -> _ValidatedEvaluatorRequest | str:
    try:
        if not isinstance(canonical_project_root, (str, Path)):
            return "canonical_project_root must be a string or Path"
        if not isinstance(generated_workspace, (str, Path)):
            return "generated_workspace must be a string or Path"
        if not isinstance(evaluator_asset, str):
            return "evaluator_asset must be a string"
        if not isinstance(python_executable, str):
            return "python_executable must be a string"
        if type(timeout) is not int:
            return "timeout must be an integer"
        if timeout <= 0:
            return "timeout must be a positive integer"

        if not evaluator_asset.strip():
            return "evaluator_asset must be a non-empty string"
        if "\x00" in evaluator_asset:
            return "evaluator_asset must not contain NUL"
        if "\\" in evaluator_asset:
            return "evaluator_asset must not contain backslash"
        if evaluator_asset.startswith("/"):
            return "evaluator_asset must not be absolute"
        if ".." in evaluator_asset.split("/"):
            return "evaluator_asset must not contain '..'"

        asset_normalized = Path(evaluator_asset).as_posix()
        if not asset_normalized.startswith(_EVALUATOR_ASSETS_PREFIX):
            return "evaluator_asset must start with tests/evaluator_assets/"
        if not asset_normalized.endswith(".py"):
            return "evaluator_asset must have a .py suffix"

        cpr = Path(canonical_project_root).resolve()
        if not cpr.exists():
            return "canonical_project_root does not exist"
        if not cpr.is_dir():
            return "canonical_project_root is not a directory"

        evaluator_root = cpr / "tests" / "evaluator_assets"
        if not evaluator_root.exists():
            return "evaluator_assets directory not found under canonical_project_root"
        if not evaluator_root.is_dir():
            return "evaluator_assets path is not a directory"
        if evaluator_root.is_symlink():
            return "evaluator_assets directory must not be a symlink"

        relative_suffix = asset_normalized[len(_EVALUATOR_ASSETS_PREFIX):]
        asset_lexical = evaluator_root / relative_suffix

        if asset_lexical.is_symlink():
            return "evaluator_asset must not be a symlink"

        for component in asset_lexical.parents:
            if component == evaluator_root:
                break
            if component.is_symlink():
                return "evaluator_asset path must not contain symlink components"
            try:
                component.relative_to(evaluator_root)
            except ValueError:
                break

        evaluator_asset_path = asset_lexical.resolve(strict=True)
        try:
            evaluator_asset_path.relative_to(evaluator_root)
        except ValueError:
            return "evaluator_asset must resolve beneath evaluator_assets directory"

        if not evaluator_asset_path.exists():
            return "evaluator_asset file does not exist"
        if not evaluator_asset_path.is_file():
            return "evaluator_asset path is not a file"

        gw = Path(generated_workspace).resolve()
        if not gw.exists():
            return "generated_workspace does not exist"
        if not gw.is_dir():
            return "generated_workspace is not a directory"

        if gw == cpr:
            return "generated_workspace must not equal canonical_project_root"
        if _containment_check(gw, cpr):
            return "generated_workspace must not be inside canonical_project_root"
        if _containment_check(cpr, gw):
            return "canonical_project_root must not be inside generated_workspace"

        workspace_evaluator_path = gw / "tests" / "evaluator_assets"
        if workspace_evaluator_path.exists():
            return "generated workspace must not contain tests/evaluator_assets"

        if not python_executable.strip():
            return "python_executable must be a non-empty string"
        if "\x00" in python_executable:
            return "python_executable must not contain NUL"

        return _ValidatedEvaluatorRequest(
            canonical_project_root=cpr,
            evaluator_root=evaluator_root,
            evaluator_asset_path=evaluator_asset_path,
            evaluator_asset_relative=asset_normalized,
            generated_workspace=gw,
            python_executable=python_executable,
            timeout=timeout,
        )
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        return f"evaluator validation error: {exc}"


def _load_trusted_evaluator_asset(
    request: _ValidatedEvaluatorRequest,
) -> _TrustedEvaluatorAsset | str:
    try:
        content = request.evaluator_asset_path.read_bytes()
    except (OSError, RuntimeError) as exc:
        return f"failed to read evaluator asset: {exc}"
    sha = hashlib.sha256(content).hexdigest()
    return _TrustedEvaluatorAsset(
        source_path=request.evaluator_asset_path,
        relative_path=request.evaluator_asset_relative,
        content=content,
        sha256=sha,
    )


def _execute_evaluator_subprocess(
    request: _ValidatedEvaluatorRequest,
    trusted: _TrustedEvaluatorAsset,
) -> _EvaluatorCommandOutcome:
    try:
        with tempfile.TemporaryDirectory(prefix="benchmark_evaluator_") as tmpdir_str:
            tmpdir = Path(tmpdir_str).resolve()
            if _containment_check(tmpdir, request.generated_workspace):
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr="temporary directory is inside generated workspace",
                )
            if _containment_check(tmpdir, request.canonical_project_root):
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr="temporary directory is inside canonical project root",
                )

            copied_path = tmpdir / "scenario_evaluator.py"
            try:
                copied_path.write_bytes(trusted.content)
            except (OSError, RuntimeError) as exc:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"failed to copy evaluator asset: {exc}",
                )

            copied_hash = hashlib.sha256(copied_path.read_bytes()).hexdigest()
            if copied_hash != trusted.sha256:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr="copied evaluator hash does not match trusted source",
                )

            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONPATH"] = (
                str(request.generated_workspace)
                + os.pathsep
                + env.get("PYTHONPATH", "")
            )

            command = [
                request.python_executable,
                str(copied_path),
                str(request.generated_workspace),
            ]

            try:
                proc = subprocess.run(
                    command,
                    cwd=str(tmpdir),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=request.timeout,
                )
                return _EvaluatorCommandOutcome(
                    succeeded=proc.returncode == 0,
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                )
            except subprocess.TimeoutExpired as e:
                stdout = _coerce_subprocess_text(e.stdout)
                stderr = _coerce_subprocess_text(e.stderr)
                if stderr:
                    stderr += "\n"
                stderr += "Evaluator timed out"
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout=stdout,
                    stderr=stderr,
                )
            except FileNotFoundError:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Python executable not found: {request.python_executable}",
                )
            except ValueError as exc:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Invalid subprocess argument: {exc}",
                )
            except OSError as e:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"OS error: {e}",
                )
            except subprocess.SubprocessError as e:
                return _EvaluatorCommandOutcome(
                    succeeded=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Subprocess error: {e}",
                )
    except (OSError, RuntimeError) as exc:
        return _EvaluatorCommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout="",
            stderr=f"temporary directory error: {exc}",
        )


def _parse_evaluator_payload(
    outcome: _EvaluatorCommandOutcome,
) -> _ParsedEvaluatorPayload | str:
    stripped = outcome.stdout.strip()
    if not stripped:
        return "evaluator produced no stdout"
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return f"evaluator stdout is not valid JSON: {exc}"
    if not isinstance(data, dict):
        return "evaluator stdout must be a JSON object"

    required_keys = {"passed", "checks", "error"}
    missing = required_keys - set(data.keys())
    if missing:
        return f"evaluator JSON missing required keys: {', '.join(sorted(missing))}"
    unknown = set(data.keys()) - required_keys
    if unknown:
        return f"evaluator JSON contains unknown keys: {', '.join(sorted(unknown))}"
    if not isinstance(data["passed"], bool):
        return "evaluator JSON 'passed' must be a boolean"
    if not isinstance(data["checks"], list):
        return "evaluator JSON 'checks' must be a list"
    if not isinstance(data["error"], str):
        return "evaluator JSON 'error' must be a string"

    checks: list[str] = []
    for i, item in enumerate(data["checks"]):
        if not isinstance(item, str):
            return f"evaluator JSON 'checks[{i}]' must be a string"
        if not item.strip():
            return f"evaluator JSON 'checks[{i}]' must be a non-empty string"
        checks.append(item)

    if len(checks) != len(set(checks)):
        return "evaluator JSON 'checks' contains duplicate entries"

    if data["passed"] and data["error"]:
        return "evaluator passed=true but error is non-empty"
    if not data["passed"] and not data["error"]:
        return "evaluator passed=false but error is empty"

    return _ParsedEvaluatorPayload(
        passed=data["passed"],
        checks=tuple(checks),
        error=data["error"],
    )


def _combine_evaluator_diagnostics(
    request: _ValidatedEvaluatorRequest | str,
    trusted: _TrustedEvaluatorAsset | str,
    outcome: _EvaluatorCommandOutcome,
    payload: _ParsedEvaluatorPayload | str,
) -> tuple[str, ...]:
    diags: list[str] = []
    if isinstance(request, str):
        diags.append(f"validation error: {request}")
    if isinstance(trusted, str):
        diags.append(f"asset error: {trusted}")
    if not outcome.succeeded:
        diags.append(f"subprocess exit code: {outcome.exit_code}")
    if outcome.stderr:
        diags.append(f"subprocess stderr: {outcome.stderr.strip()}")
    if isinstance(payload, str):
        diags.append(f"payload error: {payload}")
    return tuple(diags)


def run_scenario_evaluator(
    canonical_project_root: str | Path,
    evaluator_asset: str,
    generated_workspace: str | Path,
    *,
    python_executable: str,
    timeout: int = 180,
) -> ScenarioEvaluatorResult:
    start = time.monotonic()

    request = _validate_evaluator_request(
        canonical_project_root=canonical_project_root,
        evaluator_asset=evaluator_asset,
        generated_workspace=generated_workspace,
        python_executable=python_executable,
        timeout=timeout,
    )
    if isinstance(request, str):
        duration = time.monotonic() - start
        return ScenarioEvaluatorResult(
            passed=False,
            exit_code=-1,
            checks=(),
            error=request,
            stdout="",
            stderr=request,
            duration_seconds=duration,
        )

    trusted = _load_trusted_evaluator_asset(request)
    if isinstance(trusted, str):
        duration = time.monotonic() - start
        return ScenarioEvaluatorResult(
            passed=False,
            exit_code=-1,
            checks=(),
            error=trusted,
            stdout="",
            stderr=trusted,
            duration_seconds=duration,
        )

    outcome = _execute_evaluator_subprocess(request, trusted)
    payload = _parse_evaluator_payload(outcome)

    diagnostics = _combine_evaluator_diagnostics(request, trusted, outcome, payload)

    if isinstance(payload, str):
        duration = time.monotonic() - start
        return ScenarioEvaluatorResult(
            passed=False,
            exit_code=outcome.exit_code,
            checks=(),
            error=payload,
            stdout=outcome.stdout,
            stderr="\n".join(diagnostics) if diagnostics else outcome.stderr,
            duration_seconds=duration,
        )

    passed = (
        outcome.exit_code == 0
        and payload.passed
        and payload.error == ""
        and len(payload.checks) > 0
    )

    duration = time.monotonic() - start
    return ScenarioEvaluatorResult(
        passed=passed,
        exit_code=outcome.exit_code,
        checks=payload.checks,
        error=payload.error,
        stdout=outcome.stdout,
        stderr="\n".join(diagnostics) if diagnostics else outcome.stderr,
        duration_seconds=duration,
    )
