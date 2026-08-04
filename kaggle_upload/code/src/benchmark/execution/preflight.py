"""R7C-REAL-RUN-ROOT-CLOSURE: Kaggle Scientific Smoke preflight gate.

Engineering evidence only. A preflight run:
  * never creates an Experiment ID
  * never creates a RunRecord
  * never performs HF sync
  * never creates workspace result records

It validates the pinned runtime, the baseline Todo workspace (``manage.py
check`` + ``makemigrations todo --check --dry-run``), the requested Qwen load
quantization (``bnb-int8``, ``bnb-nf4``, or ``fp16``), a deterministic 64-token
probe, and a >= 2.0 GiB free-VRAM headroom assertion. The machine-readable
result is written to ``kaggle_preflight.json`` outside the scientific experiment
tree.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MIN_FREE_VRAM_GIB = 2.0
PROBE_MAX_TOKENS = 64
PROBE_PROMPT = "def add(a, b):\n    return a + b\n"
CANONICAL_ALLOC_CONF = "expandable_segments:True"
BASELINE_REPO = "todo"

_REQUIRED_IMPORTS: tuple[tuple[str, str, str, str | None], ...] = (
    ("django", "Django", "django", "5.2.16"),
    ("djangorestframework", "djangorestframework", "rest_framework", "3.17.1"),
    ("pytest", "pytest", "pytest", "8.4.2"),
    ("pytest_django", "pytest-django", "pytest_django", "4.12.0"),
    ("accelerate", "accelerate", "accelerate", "1.14.0"),
    ("bitsandbytes", "bitsandbytes", "bitsandbytes", "0.49.2"),
    ("torch", "torch", "torch", None),
    ("transformers", "transformers", "transformers", None),
)


@dataclass(frozen=True)
class KaggleSmokePreflightResult:
    passed: bool
    checks: tuple[str, ...] = ()
    rejection_reason: str = ""
    python_version: str = ""
    model_identity: str = ""
    requested_quantization_mode: str = ""
    model_checkpoint_basename: str = ""
    checkpoint_quantization_method: str = ""
    model_memory_footprint_bytes: int = 0
    device_map_summary: str = ""
    gpu_count: int = 0
    gpu_name: str = ""
    free_vram_after_probe_gib: float = 0.0
    allocated_vram_gib: float = 0.0
    reserved_vram_gib: float = 0.0
    probe_prompt_tokens: int = 0
    probe_completion_tokens: int = 0
    dependencies: tuple[tuple[str, str], ...] = ()
    duration_seconds: float = 0.0


def _import_version(distribution: str, module_name: str) -> str:
    try:
        importlib.import_module(module_name)
    except Exception:
        return "NOT_INSTALLED"
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def collect_dependency_versions() -> tuple[tuple[str, str], ...]:
    """Exact installed versions of the pinned Smoke runtime and Kaggle stack."""
    records: list[tuple[str, str]] = []
    for key, distribution, module_name, _expected in _REQUIRED_IMPORTS:
        records.append((key, _import_version(distribution, module_name)))
    return tuple(records)


def _python_runtime_status() -> tuple[str, bool]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return version, sys.version_info[:2] in ((3, 11), (3, 12))


def _dependency_issues(
    dependencies: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    expected = {key: version for key, _dist, _module, version in _REQUIRED_IMPORTS}
    issues: list[str] = []
    for key, actual in dependencies:
        if actual == "NOT_INSTALLED":
            issues.append(f"{key}=NOT_INSTALLED")
            continue
        pinned = expected[key]
        if pinned is not None and actual != pinned:
            issues.append(f"{key}={actual} (expected {pinned})")
    return tuple(issues)


def _stage_baseline_workspace(data_dir: Path, preflight_root: Path) -> Path:
    src = data_dir / "repositories" / BASELINE_REPO
    if not src.is_dir():
        raise FileNotFoundError(
            f"Baseline Todo repository not found under data-dir: {src}"
        )
    dst = preflight_root / f"baseline_{BASELINE_REPO}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def _run_in_workspace(workspace: Path, *argv: str, timeout: int = 180) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, *argv],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s: {' '.join(argv)}"


def _qwen_probe_metrics(
    model_path: str,
    quantization_mode: str,
) -> dict[str, Any]:
    """Load Qwen with the requested quantization, probe it, and return metrics."""
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

    backend = KaggleQwenBackend(
        model_name="qwen2.5-coder",
        model_path=model_path,
        quantization_mode=quantization_mode,
    )
    backend.load()
    response = backend.run_probe(max_tokens=PROBE_MAX_TOKENS, prompt=PROBE_PROMPT)

    import torch

    allocated_gib = torch.cuda.memory_allocated(0) / (1024**3)
    reserved_gib = torch.cuda.memory_reserved(0) / (1024**3)
    torch.cuda.synchronize(0)
    free_bytes, _total_bytes = torch.cuda.mem_get_info(0)
    free_gib = free_bytes / (1024**3)
    gpu_count = torch.cuda.device_count()

    metrics: dict[str, Any] = {
        "model_identity": backend.model_identity,
        "requested_quantization_mode": backend.quantization_mode,
        "model_checkpoint_basename": backend.checkpoint_basename,
        "checkpoint_quantization_method": backend.checkpoint_quantization_method,
        "model_memory_footprint_bytes": backend.model_memory_footprint_bytes,
        "device_map_summary": backend.device_map_summary,
        "gpu_count": gpu_count,
        "gpu_name": torch.cuda.get_device_name(0),
        "allocated_vram_gib": round(allocated_gib, 3),
        "reserved_vram_gib": round(reserved_gib, 3),
        "free_vram_after_probe_gib": round(free_gib, 3),
        "probe_prompt_tokens": response.token_usage.prompt_tokens,
        "probe_completion_tokens": response.token_usage.completion_tokens,
    }
    return metrics


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_kaggle_smoke_preflight(
    *,
    model_path: str,
    data_dir: str | Path,
    preflight_root: str | Path,
    json_output_path: str | Path | None = None,
    quantization_mode: str = "bnb-int8",
) -> KaggleSmokePreflightResult:
    """Run the full Kaggle Smoke preflight gate.

    Returns a KaggleSmokePreflightResult. The caller must exit non-zero on
    ``passed=False`` and must not create any experiment state.
    """
    start = time.monotonic()
    os.environ.setdefault("PYTORCH_ALLOC_CONF", CANONICAL_ALLOC_CONF)

    checks: list[str] = []
    dependencies = collect_dependency_versions()

    python_version, python_supported = _python_runtime_status()
    if python_supported:
        checks.append(f"python_runtime: PASS ({python_version})")
    else:
        checks.append(
            f"python_runtime: FAIL ({python_version}; expected Python 3.11 or 3.12)"
        )

    # 1. Exact dependency / import verification
    dependency_issues = _dependency_issues(dependencies)
    if dependency_issues:
        checks.append(
            "dependency_import_verification: FAIL ("
            + "; ".join(dependency_issues)
            + ")"
        )
    else:
        checks.append("dependency_import_verification: PASS")

    preflight_root = Path(preflight_root)
    preflight_root.mkdir(parents=True, exist_ok=True)

    # Fail fast before staging or loading the model when the declared runtime
    # contract is absent or version-drifted.
    runtime_contract_failed = bool(dependency_issues) or not python_supported
    if runtime_contract_failed:
        checks.extend(
            (
                "baseline_staging: SKIP (runtime contract failed)",
                "manage_py_check: SKIP (runtime contract failed)",
                "makemigrations_check: SKIP (runtime contract failed)",
                f"qwen_model_load[{quantization_mode}]: SKIP (runtime contract failed)",
                "device_map_gpu_only: SKIP (runtime contract failed)",
                "vram_headroom: SKIP (runtime contract failed)",
                "gpu_count_expected: SKIP (runtime contract failed)",
                "checkpoint_not_prequantized: SKIP (runtime contract failed)",
            )
        )

    # 2. Baseline Todo workspace staging
    staged = None
    if not runtime_contract_failed:
        try:
            staged = _stage_baseline_workspace(Path(data_dir), preflight_root)
            checks.append(f"baseline_staging: PASS ({staged.name})")
        except Exception as exc:
            checks.append(f"baseline_staging: FAIL ({exc})")

    # 3. python manage.py check
    if not runtime_contract_failed:
        if staged is not None:
            rc, out, err = _run_in_workspace(staged, "manage.py", "check")
            if rc == 0:
                checks.append("manage_py_check: PASS")
            else:
                checks.append(
                    f"manage_py_check: FAIL (exit={rc} {err[:200].strip()})"
                )
        else:
            checks.append("manage_py_check: SKIP (no staged baseline)")

    # 4. python manage.py makemigrations todo --check --dry-run
    if not runtime_contract_failed:
        if staged is not None:
            rc, out, err = _run_in_workspace(
                staged,
                "manage.py",
                "makemigrations",
                BASELINE_REPO,
                "--check",
                "--dry-run",
            )
            if rc == 0:
                checks.append("makemigrations_check: PASS")
            else:
                checks.append(
                    f"makemigrations_check: FAIL (exit={rc} {err[:200].strip()})"
                )
        else:
            checks.append("makemigrations_check: SKIP (no staged baseline)")

    # 5. Qwen load (requested quantization) + 64-token probe + VRAM headroom
    probe_metrics: dict[str, Any] = {}
    probe_failure = ""
    baseline_failed = any(
        check.startswith(
            (
                "baseline_staging: FAIL",
                "manage_py_check: FAIL",
                "makemigrations_check: FAIL",
            )
        )
        for check in checks
    )
    if not runtime_contract_failed and not baseline_failed:
        try:
            probe_metrics = _qwen_probe_metrics(model_path, quantization_mode)
            checks.append(f"qwen_model_load[{quantization_mode}]: PASS")
            device_map = str(probe_metrics.get("device_map_summary", ""))
            lowered_map = device_map.lower()
            if device_map and "cpu" not in lowered_map and "disk" not in lowered_map:
                checks.append(f"device_map_gpu_only: PASS ({device_map})")
            else:
                checks.append(f"device_map_gpu_only: FAIL ({device_map or 'missing'})")
            gpu_count = int(probe_metrics.get("gpu_count", 0) or 0)
            if gpu_count == 1:
                checks.append("gpu_count_expected: PASS (1)")
            else:
                checks.append(f"gpu_count_expected: FAIL ({gpu_count})")
            checkpoint_method = str(probe_metrics.get("checkpoint_quantization_method", "") or "")
            if not checkpoint_method:
                checks.append("checkpoint_not_prequantized: PASS")
            else:
                checks.append(f"checkpoint_not_prequantized: FAIL (method={checkpoint_method})")
            free_gib = float(probe_metrics["free_vram_after_probe_gib"])
            if free_gib >= MIN_FREE_VRAM_GIB:
                checks.append(f"vram_headroom: PASS (free={free_gib:.2f} GiB)")
            else:
                checks.append(
                    f"vram_headroom: FAIL (free={free_gib:.2f} GiB < {MIN_FREE_VRAM_GIB:.1f} GiB)"
                )
        except Exception as exc:
            probe_failure = f"{type(exc).__name__}: {exc}"
            checks.append(f"qwen_model_load[{quantization_mode}]: FAIL ({probe_failure})")
            checks.append("device_map_gpu_only: FAIL (probe did not run)")
            checks.append("vram_headroom: FAIL (probe did not run)")
            checks.append("gpu_count_expected: FAIL (probe did not run)")
            checks.append("checkpoint_not_prequantized: FAIL (probe did not run)")
    elif not runtime_contract_failed:
        checks.append(f"qwen_model_load[{quantization_mode}]: SKIP (baseline preflight failed)")
        checks.append("device_map_gpu_only: SKIP (baseline preflight failed)")
        checks.append("vram_headroom: SKIP (baseline preflight failed)")
        checks.append("gpu_count_expected: SKIP (baseline preflight failed)")
        checks.append("checkpoint_not_prequantized: SKIP (baseline preflight failed)")

    failed = [c for c in checks if ": FAIL" in c or ": SKIP" in c]
    passed = not failed and not runtime_contract_failed

    rejection = ""
    if failed:
        rejection = "; ".join(failed)
    elif dependency_issues:
        rejection = "Pinned runtime dependency verification failed: " + "; ".join(
            dependency_issues
        )
    elif probe_failure:
        rejection = probe_failure

    duration = time.monotonic() - start
    result = KaggleSmokePreflightResult(
        passed=passed,
        checks=tuple(checks),
        rejection_reason=rejection,
        python_version=python_version,
        model_identity=str(probe_metrics.get("model_identity", "")),
        requested_quantization_mode=str(probe_metrics.get("requested_quantization_mode", "")),
        model_checkpoint_basename=str(probe_metrics.get("model_checkpoint_basename", "")),
        checkpoint_quantization_method=str(probe_metrics.get("checkpoint_quantization_method", "") or ""),
        model_memory_footprint_bytes=int(probe_metrics.get("model_memory_footprint_bytes", 0) or 0),
        device_map_summary=str(probe_metrics.get("device_map_summary", "")),
        gpu_count=int(probe_metrics.get("gpu_count", 0) or 0),
        gpu_name=str(probe_metrics.get("gpu_name", "")),
        free_vram_after_probe_gib=float(probe_metrics.get("free_vram_after_probe_gib", 0.0) or 0.0),
        allocated_vram_gib=float(probe_metrics.get("allocated_vram_gib", 0.0) or 0.0),
        reserved_vram_gib=float(probe_metrics.get("reserved_vram_gib", 0.0) or 0.0),
        probe_prompt_tokens=int(probe_metrics.get("probe_prompt_tokens", 0) or 0),
        probe_completion_tokens=int(probe_metrics.get("probe_completion_tokens", 0) or 0),
        dependencies=dependencies,
        duration_seconds=round(duration, 3),
    )

    if json_output_path is not None:
        payload: dict[str, object] = {
            "schema": "kaggle_smoke_preflight.v1",
            "phase": "R7C-REAL-RUN-ROOT-CLOSURE",
            "passed": result.passed,
            "rejection_reason": result.rejection_reason,
            "checks": list(result.checks),
            "python_version": result.python_version,
            "model_identity": result.model_identity,
            "model_checkpoint_basename": result.model_checkpoint_basename,
            "requested_quantization_mode": result.requested_quantization_mode,
            "checkpoint_quantization_method": result.checkpoint_quantization_method,
            "model_memory_footprint_bytes": result.model_memory_footprint_bytes,
            "device_map_summary": result.device_map_summary,
            "gpu_count": result.gpu_count,
            "gpu_name": result.gpu_name,
            "free_vram_after_probe_gib": result.free_vram_after_probe_gib,
            "allocated_vram_gib": result.allocated_vram_gib,
            "reserved_vram_gib": result.reserved_vram_gib,
            "probe_prompt_tokens": result.probe_prompt_tokens,
            "probe_completion_tokens": result.probe_completion_tokens,
            "dependencies": [list(pair) for pair in result.dependencies],
            "duration_seconds": result.duration_seconds,
        }
        _write_json(Path(json_output_path), payload)

    return result


def render_preflight_table(result: KaggleSmokePreflightResult) -> str:
    """Render a concise human-readable table for the preflight gate."""
    lines = [
        "=== KAGGLE SMOKE PREFLIGHT ===",
        f"passed: {result.passed}",
        f"python_version: {result.python_version or 'N/A'}",
        f"model_identity: {result.model_identity or 'N/A'}",
        f"requested_quantization_mode: {result.requested_quantization_mode or 'N/A'}",
        f"model_checkpoint_basename: {result.model_checkpoint_basename or 'N/A'}",
        f"checkpoint_quantization_method: {result.checkpoint_quantization_method or 'N/A'}",
        f"model_memory_footprint_bytes: {result.model_memory_footprint_bytes}",
        f"gpu_count: {result.gpu_count}",
        f"gpu_name: {result.gpu_name or 'N/A'}",
        f"free_vram_after_probe_gib: {result.free_vram_after_probe_gib:.3f}",
        f"allocated_vram_gib: {result.allocated_vram_gib:.3f}",
        f"reserved_vram_gib: {result.reserved_vram_gib:.3f}",
        f"probe_tokens: {result.probe_prompt_tokens}+{result.probe_completion_tokens}",
        f"duration_seconds: {result.duration_seconds}",
    ]
    for check in result.checks:
        lines.append(f"  - {check}")
    for name, version in result.dependencies:
        lines.append(f"  dep {name}: {version}")
    if result.rejection_reason:
        lines.append(f"rejection_reason: {result.rejection_reason}")
    return "\n".join(lines)
