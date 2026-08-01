"""R7C-REAL-RUN-ROOT-CLOSURE: Kaggle Scientific Smoke preflight gate.

Engineering evidence only. A preflight run:
  * never creates an Experiment ID
  * never creates a RunRecord
  * never performs HF sync
  * never creates workspace result records

It validates the pinned runtime, the baseline Todo workspace (``manage.py
check`` + ``makemigrations todo --check --dry-run``), the int8 Qwen load, a
deterministic 64-token probe, and a >= 2.0 GiB free-VRAM headroom assertion.
The machine-readable result is written to ``kaggle_preflight.json`` outside the
scientific experiment tree.
"""

from __future__ import annotations

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

_REQUIRED_IMPORTS: tuple[tuple[str, str], ...] = (
    ("django", "get_version"),
    ("djangorestframework", "VERSION"),
    ("pytest", "__version__"),
    ("pytest_django", "__version__"),
    ("accelerate", "__version__"),
    ("bitsandbytes", "__version__"),
    ("torch", "__version__"),
    ("transformers", "__version__"),
)


@dataclass(frozen=True)
class KaggleSmokePreflightResult:
    passed: bool
    checks: tuple[str, ...] = ()
    rejection_reason: str = ""
    model_identity: str = ""
    quantization_mode: str = ""
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


def _import_version(name: str, attr: str) -> str:
    try:
        module = __import__(name)
    except Exception:
        return "NOT_INSTALLED"
    value = getattr(module, attr, None)
    if callable(value):
        try:
            value = value()
        except Exception:
            value = "unknown"
    return str(value) if value is not None else "unknown"


def collect_dependency_versions() -> tuple[tuple[str, str], ...]:
    """Exact installed versions of the pinned Smoke runtime and Kaggle stack."""
    records: list[tuple[str, str]] = []
    for name, attr in _REQUIRED_IMPORTS:
        records.append((name, _import_version(name, attr)))
    return tuple(records)


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
) -> dict[str, Any]:
    """Load int8 Qwen, run the deterministic probe, and return memory metrics."""
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

    backend = KaggleQwenBackend(
        model_name="qwen2.5-coder",
        model_path=model_path,
        quantization_mode="int8",
    )
    backend.load()
    response = backend.run_probe(max_tokens=PROBE_MAX_TOKENS, prompt=PROBE_PROMPT)

    import torch

    allocated_gib = torch.cuda.memory_allocated(0) / (1024**3)
    reserved_gib = torch.cuda.memory_reserved(0) / (1024**3)
    total_mem = torch.cuda.get_device_properties(0).total_memory
    free_gib = max(0.0, total_mem - torch.cuda.memory_reserved(0)) / (1024**3)
    gpu_count = torch.cuda.device_count()

    metrics: dict[str, Any] = {
        "model_identity": backend.model_identity,
        "quantization_mode": backend.quantization_mode,
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
) -> KaggleSmokePreflightResult:
    """Run the full Kaggle Smoke preflight gate.

    Returns a KaggleSmokePreflightResult. The caller must exit non-zero on
    ``passed=False`` and must not create any experiment state.
    """
    start = time.monotonic()
    os.environ.setdefault("PYTORCH_ALLOC_CONF", CANONICAL_ALLOC_CONF)

    checks: list[str] = []
    dependencies = collect_dependency_versions()

    # 1. Exact dependency / import verification
    missing = [name for name, ver in dependencies if ver == "NOT_INSTALLED"]
    if missing:
        checks.append(
            f"dependency_import_verification: FAIL (missing: {', '.join(missing)})"
        )
    else:
        checks.append("dependency_import_verification: PASS")

    preflight_root = Path(preflight_root)
    preflight_root.mkdir(parents=True, exist_ok=True)

    # 2. Baseline Todo workspace staging
    staged = None
    try:
        staged = _stage_baseline_workspace(Path(data_dir), preflight_root)
        checks.append(f"baseline_staging: PASS ({staged.name})")
    except Exception as exc:
        checks.append(f"baseline_staging: FAIL ({exc})")

    # 3. python manage.py check
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
    if staged is not None:
        rc, out, err = _run_in_workspace(
            staged, "manage.py", "makemigrations", BASELINE_REPO, "--check", "--dry-run"
        )
        if rc == 0:
            checks.append("makemigrations_check: PASS")
        else:
            checks.append(
                f"makemigrations_check: FAIL (exit={rc} {err[:200].strip()})"
            )
    else:
        checks.append("makemigrations_check: SKIP (no staged baseline)")

    # 5. Qwen int8 load + 64-token probe + VRAM headroom
    probe_metrics: dict[str, Any] = {}
    probe_failure = ""
    try:
        probe_metrics = _qwen_probe_metrics(model_path)
        checks.append("qwen_int8_load: PASS")
        free_gib = float(probe_metrics["free_vram_after_probe_gib"])
        if free_gib >= MIN_FREE_VRAM_GIB:
            checks.append(f"vram_headroom: PASS (free={free_gib:.2f} GiB)")
        else:
            checks.append(
                f"vram_headroom: FAIL (free={free_gib:.2f} GiB < {MIN_FREE_VRAM_GIB:.1f} GiB)"
            )
    except Exception as exc:
        probe_failure = f"{type(exc).__name__}: {exc}"
        checks.append("qwen_int8_load: FAIL")
        checks.append("vram_headroom: FAIL (probe did not run)")

    failed = [c for c in checks if ": FAIL" in c or ": SKIP" in c]
    passed = not failed and not missing

    rejection = ""
    if failed:
        rejection = "; ".join(failed)
    elif missing:
        rejection = "Missing pinned runtime dependencies: " + ", ".join(missing)
    elif probe_failure:
        rejection = probe_failure

    duration = time.monotonic() - start
    result = KaggleSmokePreflightResult(
        passed=passed,
        checks=tuple(checks),
        rejection_reason=rejection,
        model_identity=str(probe_metrics.get("model_identity", "")),
        quantization_mode=str(probe_metrics.get("quantization_mode", "")),
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
            "model_identity": result.model_identity,
            "quantization_mode": result.quantization_mode,
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
        f"model_identity: {result.model_identity or 'N/A'}",
        f"quantization_mode: {result.quantization_mode or 'N/A'}",
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
