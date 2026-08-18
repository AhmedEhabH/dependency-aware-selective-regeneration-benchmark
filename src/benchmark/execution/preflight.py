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

import contextlib
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
EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)
PROBE_MAX_TOKENS = 64
PROBE_PROMPT = "def add(a, b):\n    return a + b\n"
CANONICAL_ALLOC_CONF = "expandable_segments:True"
BASELINE_REPO = "todo"
LONG_CONTEXT_TARGET_PROMPT_TOKENS = 12000
LONG_CONTEXT_MAX_TOKENS = 64

_REPO_PREFLIGHT_BLOCKED_SUFFIX = "repository preflight failed"


class RepositoryPreflightUnavailableError(RuntimeError):
    """Repo-preflight evidence is missing, unreadable, or reports overall != PASS."""


def load_repo_preflight_evidence(path: str | Path) -> dict[str, Any]:
    """Fail-closed loader for the ``pilot-repo-preflight-cell`` evidence file.

    Returns the parsed evidence only when ``overall == "PASS"``; any other
    outcome raises ``RepositoryPreflightUnavailableError`` so the model-load
    preflight can never proceed after a FAILED repository preflight.
    """
    evidence_path = Path(path)
    if not evidence_path.is_file():
        raise RepositoryPreflightUnavailableError(
            f"repo-preflight evidence missing: {evidence_path}"
        )
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RepositoryPreflightUnavailableError(
            f"repo-preflight evidence invalid json: {evidence_path} "
            f"({type(exc).__name__})"
        ) from exc
    if not isinstance(evidence, dict):
        raise RepositoryPreflightUnavailableError(
            f"repo-preflight evidence not an object: {evidence_path}"
        )
    if evidence.get("overall") != "PASS":
        raise RepositoryPreflightUnavailableError(
            f"overall != PASS for repo-preflight evidence {evidence_path}"
        )
    return evidence

_REQUIRED_IMPORTS: tuple[tuple[str, str, str, str | None], ...] = (
    ("django", "Django", "django", "5.2.16"),
    ("djangorestframework", "djangorestframework", "rest_framework", "3.17.1"),
    ("pytest", "pytest", "pytest", "8.4.2"),
    ("pytest_django", "pytest-django", "pytest_django", "4.12.0"),
    ("accelerate", "accelerate", "accelerate", "1.14.0"),
    ("bitsandbytes", "bitsandbytes", "bitsandbytes", "0.49.2"),
    ("torch", "torch", "torch", None),
    ("transformers", "transformers", "transformers", "4.57.6"),
)


@dataclass(frozen=True)
class GpuVramSnapshot:
    device_index: int
    gpu_name: str
    allocated_gib: float
    reserved_gib: float
    free_gib: float
    total_gib: float


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
    gpu_vram_by_device: tuple[GpuVramSnapshot, ...] = ()
    free_vram_after_probe_gib: float = 0.0
    allocated_vram_gib: float = 0.0
    reserved_vram_gib: float = 0.0
    probe_prompt_tokens: int = 0
    probe_completion_tokens: int = 0
    long_context_probe: dict[str, Any] | None = None
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


def _collect_gpu_vram_snapshots() -> tuple[GpuVramSnapshot, ...]:
    """Capture ordered per-device VRAM evidence for every visible GPU.

    Returns an empty tuple when CUDA is unavailable. Every visible device is
    synchronized before its memory is read. A failure for one GPU is raised, never
    silently dropped. No tensors are allocated.
    """
    try:
        import torch
    except Exception:
        return ()
    if not torch.cuda.is_available():
        return ()
    snapshots: list[GpuVramSnapshot] = []
    for index in range(torch.cuda.device_count()):
        torch.cuda.synchronize(index)
        allocated_gib = torch.cuda.memory_allocated(index) / (1024**3)
        reserved_gib = torch.cuda.memory_reserved(index) / (1024**3)
        free_bytes, total_bytes = torch.cuda.mem_get_info(index)
        snapshots.append(
            GpuVramSnapshot(
                device_index=index,
                gpu_name=str(torch.cuda.get_device_name(index)),
                allocated_gib=round(allocated_gib, 3),
                reserved_gib=round(reserved_gib, 3),
                free_gib=round(free_bytes / (1024**3), 3),
                total_gib=round(total_bytes / (1024**3), 3),
            )
        )
    return tuple(snapshots)


def _create_qwen_backend(
    model_path: str,
    quantization_mode: str,
) -> Any:
    """Create a KaggleQwenBackend instance (no load yet)."""
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

    return KaggleQwenBackend(
        model_name="qwen2.5-coder",
        model_path=model_path,
        quantization_mode=quantization_mode,
    )


def _qwen_probe_metrics(
    model_path: str,
    quantization_mode: str,
    *,
    _backend: Any = None,
) -> dict[str, Any]:
    """Load Qwen with the requested quantization, probe it, and return metrics.

    When ``_backend`` is provided and already loaded, reuse it instead of
    constructing a second backend (single model load per preflight cell).
    """
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

    if _backend is not None:
        backend = _backend
    else:
        backend = KaggleQwenBackend(
            model_name="qwen2.5-coder",
            model_path=model_path,
            quantization_mode=quantization_mode,
        )
    backend.load()
    response = backend.run_probe(max_tokens=PROBE_MAX_TOKENS, prompt=PROBE_PROMPT)

    import torch

    gpu_count = int(torch.cuda.device_count())
    snapshots = _collect_gpu_vram_snapshots()
    if gpu_count > 0 and not snapshots:
        raise RuntimeError(
            "CUDA is queryable but no per-GPU VRAM snapshots were collected"
        )
    if snapshots:
        free_gib = min(snapshot.free_gib for snapshot in snapshots)
        allocated_gib = sum(snapshot.allocated_gib for snapshot in snapshots)
        reserved_gib = sum(snapshot.reserved_gib for snapshot in snapshots)
        gpu_name = snapshots[0].gpu_name
    else:
        free_gib = 0.0
        allocated_gib = 0.0
        reserved_gib = 0.0
        gpu_name = ""

    metrics: dict[str, Any] = {
        "model_identity": backend.model_identity,
        "requested_quantization_mode": backend.quantization_mode,
        "model_checkpoint_basename": backend.checkpoint_basename,
        "checkpoint_quantization_method": backend.checkpoint_quantization_method,
        "model_memory_footprint_bytes": backend.model_memory_footprint_bytes,
        "device_map_summary": backend.device_map_summary,
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
        "gpu_vram_by_device": snapshots,
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


def _run_long_context_probe(
    model_path: str, quantization_mode: str, *, _backend: Any = None,
) -> dict[str, Any]:
    """Run the long-context stress probe as a separate monkeypatchable step.

    When ``_backend`` is provided and already loaded, reuse it instead of
    constructing a second model load (single model load per preflight cell).
    """
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend

    if _backend is not None:
        lc_backend = _backend
    else:
        lc_backend = KaggleQwenBackend(
            model_name="qwen2.5-coder",
            model_path=model_path,
            quantization_mode=quantization_mode,
        )
        lc_backend.load()
    return lc_backend.run_long_context_probe(
        target_prompt_tokens=LONG_CONTEXT_TARGET_PROMPT_TOKENS,
        max_tokens=LONG_CONTEXT_MAX_TOKENS,
    )


def _static_model_metadata(
    model_path: str, quantization_mode: str
) -> dict[str, Any]:
    """Model/GPU metadata derivable WITHOUT loading the model.

    Reads ``config.json`` (model identity, checkpoint slug, quantization method)
    and CUDA device discovery only. Never loads weights, so it stays truthful
    even when ``from_pretrained`` OOMs or fails.
    """
    from benchmark.llm.kaggle_qwen_backend import (
        _checkpoint_identity_slug,
        _checkpoint_quantization_method,
        _read_checkpoint_config,
        compute_model_identity,
    )

    metadata: dict[str, Any] = {
        "requested_quantization_mode": quantization_mode,
        "model_identity": "",
        "model_checkpoint_basename": "",
        "checkpoint_quantization_method": "",
        "gpu_count": 0,
        "gpu_name": "",
        "gpu_vram_by_device": (),
    }
    with contextlib.suppress(Exception):
        metadata["model_identity"] = compute_model_identity(model_path, quantization_mode)
    with contextlib.suppress(Exception):
        metadata["model_checkpoint_basename"] = _checkpoint_identity_slug(Path(model_path))
    with contextlib.suppress(Exception):
        metadata["checkpoint_quantization_method"] = _checkpoint_quantization_method(
            _read_checkpoint_config(Path(model_path))
        )
    try:
        import torch

        if torch.cuda.is_available():
            metadata["gpu_count"] = torch.cuda.device_count()
            metadata["gpu_name"] = torch.cuda.get_device_name(0)
            metadata["gpu_vram_by_device"] = _collect_gpu_vram_snapshots()
    except Exception:
        pass
    return metadata


def run_kaggle_smoke_preflight(
    *,
    model_path: str,
    data_dir: str | Path,
    preflight_root: str | Path,
    json_output_path: str | Path | None = None,
    quantization_mode: str = "bnb-int8",
    repo_preflight_json_path: str | Path | None = None,
) -> KaggleSmokePreflightResult:
    """Run the full Kaggle Smoke preflight gate.

    Returns a KaggleSmokePreflightResult. The caller must exit non-zero on
    ``passed=False`` and must not create any experiment state.

    ``repo_preflight_json_path`` optionally points at the repo-preflight
    evidence written by the pilot notebook's earlier ``pilot-repo-preflight-cell``
    (``overall`` field). When provided, the model load is fail-closed: missing,
    unreadable, or non-PASS evidence blocks staging and the Qwen probe and marks
    the affected checks ``SKIP (repository preflight failed)``.
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

    # Repo-preflight evidence gate: the model probe must never run after a
    # FAILED (or missing) repository preflight.
    repo_preflight_failed = False
    if repo_preflight_json_path is not None:
        try:
            load_repo_preflight_evidence(repo_preflight_json_path)
            checks.append("repository_preflight_evidence: PASS")
        except RepositoryPreflightUnavailableError as exc:
            repo_preflight_failed = True
            checks.append(
                f"repository_preflight_evidence: FAIL ({type(exc).__name__}: {exc})"
            )

    # Fail fast before staging or loading the model when the declared runtime
    # contract is absent or version-drifted, or when the repo preflight failed.
    runtime_contract_failed = bool(dependency_issues) or not python_supported
    blocked = runtime_contract_failed or repo_preflight_failed
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
    elif repo_preflight_failed:
        checks.extend(
            (
                f"baseline_staging: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"manage_py_check: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"makemigrations_check: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"qwen_model_load[{quantization_mode}]: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"device_map_gpu_only: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"vram_headroom: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"gpu_count_expected: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
                f"checkpoint_not_prequantized: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
            )
        )

    # 2. Baseline Todo workspace staging
    staged = None
    if not blocked:
        try:
            staged = _stage_baseline_workspace(Path(data_dir), preflight_root)
            checks.append(f"baseline_staging: PASS ({staged.name})")
        except Exception as exc:
            checks.append(f"baseline_staging: FAIL ({exc})")

    # 3. python manage.py check
    if not blocked:
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
    if not blocked:
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
    _shared_backend = None
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
    if not blocked and not baseline_failed:
        try:
            _shared_backend = _create_qwen_backend(model_path, quantization_mode)
            probe_metrics = _qwen_probe_metrics(model_path, quantization_mode, _backend=_shared_backend)
            checks.append(f"qwen_model_load[{quantization_mode}]: PASS")
            device_map = str(probe_metrics.get("device_map_summary", ""))
            lowered_map = device_map.lower()
            if device_map and "cpu" not in lowered_map and "disk" not in lowered_map:
                checks.append(f"device_map_gpu_only: PASS ({device_map})")
            else:
                checks.append(f"device_map_gpu_only: FAIL ({device_map or 'missing'})")
            gpu_count = int(probe_metrics.get("gpu_count", 0) or 0)
            if gpu_count in EXPECTED_VISIBLE_GPU_COUNTS:
                checks.append(f"gpu_count_expected: PASS ({gpu_count})")
            else:
                expected = " or ".join(str(c) for c in EXPECTED_VISIBLE_GPU_COUNTS)
                checks.append(f"gpu_count_expected: FAIL ({gpu_count}; expected {expected})")
            checkpoint_method = str(probe_metrics.get("checkpoint_quantization_method", "") or "")
            if not checkpoint_method:
                checks.append("checkpoint_not_prequantized: PASS")
            else:
                checks.append(f"checkpoint_not_prequantized: FAIL (method={checkpoint_method})")
            snapshots = probe_metrics.get("gpu_vram_by_device", ())
            if not isinstance(snapshots, tuple):
                snapshots = tuple(snapshots)
            gpu_count = int(probe_metrics.get("gpu_count", 0) or 0)
            failing_devices = [
                snapshot
                for snapshot in snapshots
                if snapshot.free_gib < MIN_FREE_VRAM_GIB
            ]
            if failing_devices:
                details = "; ".join(
                    f"GPU {snapshot.device_index} free={snapshot.free_gib:.2f} GiB "
                    f"< {MIN_FREE_VRAM_GIB:.1f} GiB"
                    for snapshot in failing_devices
                )
                checks.append(f"vram_headroom: FAIL ({details})")
            elif gpu_count > 0 and not snapshots:
                checks.append("vram_headroom: FAIL (no per-GPU VRAM snapshots collected)")
            else:
                free_gib = float(
                    probe_metrics.get("free_vram_after_probe_gib", 0.0) or 0.0
                )
                checks.append(
                    f"vram_headroom: PASS (minimum free across {gpu_count} GPU(s)="
                    f"{free_gib:.2f} GiB)"
                )
        except Exception as exc:
            probe_failure = f"{type(exc).__name__}: {exc}"
            probe_metrics = _static_model_metadata(model_path, quantization_mode)
            checks.append(f"qwen_model_load[{quantization_mode}]: FAIL ({probe_failure})")
            checks.append("device_map_gpu_only: FAIL (probe did not run)")
            checks.append("vram_headroom: FAIL (probe did not run)")
            checks.append("gpu_count_expected: FAIL (probe did not run)")
            checks.append("checkpoint_not_prequantized: FAIL (probe did not run)")
    elif not blocked:
        checks.append(f"qwen_model_load[{quantization_mode}]: SKIP (baseline preflight failed)")
        checks.append("device_map_gpu_only: SKIP (baseline preflight failed)")
        checks.append("vram_headroom: SKIP (baseline preflight failed)")
        checks.append("gpu_count_expected: SKIP (baseline preflight failed)")
        checks.append("checkpoint_not_prequantized: SKIP (baseline preflight failed)")

    failed = [c for c in checks if ": FAIL" in c or ": SKIP" in c]
    passed = not failed and not blocked

    # Long-context stress probe (>= 12k tokens): engineering evidence only.
    # Reuses the single backend loaded above (no second model load).
    long_context_probe: dict[str, Any] | None = None
    if passed and not probe_failure:
        try:
            long_context_probe = _run_long_context_probe(
                model_path, quantization_mode, _backend=_shared_backend,
            )
            if long_context_probe.get("passed"):
                checks.append(
                    f"long_context_probe: PASS (prompt_tokens={long_context_probe['prompt_tokens']}, "
                    f"completion_tokens={long_context_probe['completion_tokens']}, "
                    f"elapsed={long_context_probe['elapsed_seconds']}s)"
                )
            else:
                checks.append(
                    f"long_context_probe: FAIL (prompt_tokens={long_context_probe.get('prompt_tokens', 0)}, "
                    f"completion_tokens={long_context_probe.get('completion_tokens', 0)})"
                )
        except Exception as exc:
            long_context_probe = {
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            checks.append(f"long_context_probe: FAIL ({type(exc).__name__}: {exc})")

    # Re-evaluate pass/fail after long-context probe
    failed = [c for c in checks if ": FAIL" in c or ": SKIP" in c]
    passed = not failed and not blocked

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
        checkpoint_quantization_method=str(probe_metrics.get("checkpoint_quantization_method", "")),
        model_memory_footprint_bytes=int(probe_metrics.get("model_memory_footprint_bytes", 0) or 0),
        device_map_summary=str(probe_metrics.get("device_map_summary", "")),
        gpu_count=int(probe_metrics.get("gpu_count", 0) or 0),
        gpu_name=str(probe_metrics.get("gpu_name", "")),
        gpu_vram_by_device=tuple(probe_metrics.get("gpu_vram_by_device", ())),
        free_vram_after_probe_gib=float(probe_metrics.get("free_vram_after_probe_gib", 0.0) or 0.0),
        allocated_vram_gib=float(probe_metrics.get("allocated_vram_gib", 0.0) or 0.0),
        reserved_vram_gib=float(probe_metrics.get("reserved_vram_gib", 0.0) or 0.0),
        probe_prompt_tokens=int(probe_metrics.get("probe_prompt_tokens", 0) or 0),
        probe_completion_tokens=int(probe_metrics.get("probe_completion_tokens", 0) or 0),
        long_context_probe=long_context_probe,
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
            "gpu_vram_by_device": [
                {
                    "device_index": snapshot.device_index,
                    "gpu_name": snapshot.gpu_name,
                    "allocated_gib": snapshot.allocated_gib,
                    "reserved_gib": snapshot.reserved_gib,
                    "free_gib": snapshot.free_gib,
                    "total_gib": snapshot.total_gib,
                }
                for snapshot in result.gpu_vram_by_device
            ],
            "free_vram_after_probe_gib": result.free_vram_after_probe_gib,
            "allocated_vram_gib": result.allocated_vram_gib,
            "reserved_vram_gib": result.reserved_vram_gib,
            "probe_prompt_tokens": result.probe_prompt_tokens,
            "probe_completion_tokens": result.probe_completion_tokens,
            "long_context_probe": result.long_context_probe,
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
    ]
    for snapshot in result.gpu_vram_by_device:
        lines.append(
            f"  gpu_vram[{snapshot.device_index}] {snapshot.gpu_name} "
            f"alloc={snapshot.allocated_gib:.3f} reserved={snapshot.reserved_gib:.3f} "
            f"free={snapshot.free_gib:.3f} total={snapshot.total_gib:.3f} GiB"
        )
    lines.extend([
        f"probe_tokens: {result.probe_prompt_tokens}+{result.probe_completion_tokens}",
    ])
    if result.long_context_probe:
        lc = result.long_context_probe
        lines.append(
            f"long_context_probe: prompt_tokens={lc.get('prompt_tokens', '?')} "
            f"completion_tokens={lc.get('completion_tokens', '?')} "
            f"elapsed={lc.get('elapsed_seconds', '?')}s "
            f"cache={lc.get('cache_implementation', '?')} "
            f"passed={lc.get('passed', '?')}"
        )
    lines.extend([
        f"duration_seconds: {result.duration_seconds}",
    ])
    for check in result.checks:
        lines.append(f"  - {check}")
    for name, version in result.dependencies:
        lines.append(f"  dep {name}: {version}")
    if result.rejection_reason:
        lines.append(f"rejection_reason: {result.rejection_reason}")
    return "\n".join(lines)


class LaunchAuthorizationError(RuntimeError):
    """Raised when pilot launch authorization fails any gate."""


def validate_pilot_launch_authorization(
    *,
    repo_preflight_json: str | Path,
    model_preflight_json: str | Path,
    dryrun_dir: str | Path,
    expected_source_commit: str,
    expected_source_tag: str,
    expected_model_identity: str,
    expected_quantization: str = "bnb-nf4",
    expected_deployed_build_id: str = "",
) -> None:
    """Fail-closed pilot launch authorization gate.

    Re-reads ALL evidence files from disk immediately before launch. Must pass
    every gate before experiment creation, output directory population, model
    load, HF sync, or any scientific model call.

    Raises ``LaunchAuthorizationError`` on any failure.
    """
    errors: list[str] = []

    # --- Repository preflight evidence ---
    repo_path = Path(repo_preflight_json)
    if not repo_path.is_file():
        errors.append(f"repo_preflight.json missing: {repo_path}")
    else:
        try:
            repo_evidence = json.loads(repo_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"repo_preflight.json unreadable: {type(exc).__name__}: {exc}")
            repo_evidence = {}
        if isinstance(repo_evidence, dict):
            if repo_evidence.get("overall") != "PASS":
                errors.append(
                    f"repo_preflight.json overall={repo_evidence.get('overall')!r} (expected PASS)"
                )
            repos = repo_evidence.get("repositories", {})
            if isinstance(repos, dict):
                for repo_id in ("todo", "djangocms", "saleor"):
                    repo_data = repos.get(repo_id)
                    if not isinstance(repo_data, dict) or not repo_data.get("passed"):
                        errors.append(
                            f"repo_preflight.json repositories.{repo_id}.passed != true"
                        )
            else:
                errors.append("repo_preflight.json missing 'repositories' object")

    # --- Model preflight evidence ---
    model_path = Path(model_preflight_json)
    if not model_path.is_file():
        errors.append(f"model_preflight.json missing: {model_path}")
    else:
        try:
            model_evidence = json.loads(model_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"model_preflight.json unreadable: {type(exc).__name__}: {exc}")
            model_evidence = {}
        if isinstance(model_evidence, dict):
            if not model_evidence.get("passed"):
                errors.append("model_preflight.json passed != true")
            if model_evidence.get("model_identity") != expected_model_identity:
                errors.append(
                    f"model_preflight.json model_identity="
                    f"{model_evidence.get('model_identity')!r} "
                    f"(expected {expected_model_identity!r})"
                )
            if model_evidence.get("requested_quantization_mode") != expected_quantization:
                errors.append(
                    f"model_preflight.json quantization="
                    f"{model_evidence.get('requested_quantization_mode')!r} "
                    f"(expected {expected_quantization!r})"
                )
            checks_list = model_evidence.get("checks", [])
            if isinstance(checks_list, list):
                repo_preflight_check = [
                    c for c in checks_list if "repository_preflight_evidence" in c
                ]
                if not repo_preflight_check:
                    errors.append(
                        "model_preflight.json missing repository_preflight_evidence "
                        "check (positive PASS required)"
                    )
                else:
                    if any("FAIL" in c for c in repo_preflight_check):
                        errors.append(
                            "model_preflight.json repository_preflight_evidence check FAILED"
                        )
                    elif not any("PASS" in c for c in repo_preflight_check):
                        errors.append(
                            "model_preflight.json repository_preflight_evidence check "
                            "exists but contains no PASS signal"
                        )
            # C4/D: long_context_probe must be present, passed, and meet thresholds.
            lc_probe = model_evidence.get("long_context_probe")
            if not isinstance(lc_probe, dict):
                errors.append(
                    "model_preflight.json long_context_probe missing or not a dict"
                )
            else:
                if not lc_probe.get("passed"):
                    errors.append(
                        "model_preflight.json long_context_probe passed != true"
                    )
                lc_tokens = lc_probe.get("prompt_tokens", 0) or 0
                lc_target = lc_probe.get("target_prompt_tokens", 0) or 0
                lc_completion = lc_probe.get("completion_tokens", 0) or 0
                lc_cache = lc_probe.get("cache_implementation", "")
                if lc_target < 12000:
                    errors.append(
                        f"model_preflight.json long_context_probe target_prompt_tokens={lc_target} (expected >= 12000)"
                    )
                if lc_tokens < 12000:
                    errors.append(
                        f"model_preflight.json long_context_probe prompt_tokens={lc_tokens} (expected >= 12000)"
                    )
                if lc_completion <= 0:
                    errors.append(
                        "model_preflight.json long_context_probe completion_tokens <= 0"
                    )
                if lc_cache != "offloaded":
                    errors.append(
                        "model_preflight.json long_context_probe "
                        f"cache_implementation={lc_cache!r} (expected 'offloaded')"
                    )

    # --- Dry-run records + source_identity.json (C1-C4) ---
    dryrun_path = Path(dryrun_dir) / "run_records.jsonl"
    source_identity_path = Path(dryrun_dir) / "source_identity.json"
    if not dryrun_path.is_file():
        errors.append(f"dryrun records missing: {dryrun_path}")
    else:
        try:
            lines = [
                line.strip()
                for line in dryrun_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            records = [json.loads(line) for line in lines]
        except (OSError, ValueError) as exc:
            errors.append(f"dryrun records unreadable: {type(exc).__name__}: {exc}")
            records = []

        if records:
            # C4: strict topology
            if len(records) != 48:
                errors.append(f"dryrun record count={len(records)} (expected 48)")
            run_ids = [r.get("run_id") for r in records]
            if len(set(run_ids)) != 48:
                errors.append(f"dryrun unique run_ids={len(set(run_ids))} (expected 48)")

            failed_records = [r for r in records if r.get("status") != "succeeded"]
            if failed_records:
                errors.append(
                    f"dryrun has {len(failed_records)} non-succeeded records"
                )

            # C4: repo distribution exactly todo=16, djangocms=16, saleor=16
            repo_counts = {}
            for r in records:
                rid = r.get("repository_id", "")
                repo_counts[rid] = repo_counts.get(rid, 0) + 1
            expected_repo = {"todo": 16, "djangocms": 16, "saleor": 16}
            if repo_counts != expected_repo:
                errors.append(f"dryrun repo_counts={repo_counts} (expected {expected_repo})")

            # C4: strategy distribution exactly iterative_repository_agent=24, selective=24
            strat_counts = {}
            for r in records:
                sid = r.get("strategy_id", "")
                strat_counts[sid] = strat_counts.get(sid, 0) + 1
            expected_strat = {"iterative_repository_agent": 24, "selective": 24}
            if strat_counts != expected_strat:
                errors.append(f"dryrun strategy_counts={strat_counts} (expected {expected_strat})")

            # C4: repetition distribution exactly rep1=24, rep2=24
            rep_counts = {}
            for r in records:
                rep = r.get("repetition", 0)
                rep_counts[rep] = rep_counts.get(rep, 0) + 1
            expected_rep = {1: 24, 2: 24}
            if rep_counts != expected_rep:
                errors.append(f"dryrun rep_counts={rep_counts} (expected {expected_rep})")

            # C4: model_calls exactly 0 on EVERY record
            nonzero_calls = [r for r in records if (r.get("model_calls") or 0) != 0]
            if nonzero_calls:
                errors.append(
                    f"dryrun has {len(nonzero_calls)} records with model_calls != 0"
                )

            # C4: token_usage total exactly 0 on EVERY record
            nonzero_tokens = [r for r in records if (r.get("total_tokens") or 0) != 0]
            if nonzero_tokens:
                errors.append(
                    f"dryrun has {len(nonzero_tokens)} records with token_usage total != 0"
                )

            # C1: exact source commit on EVERY record (strict, no set membership)
            if expected_source_commit and expected_source_commit != "unknown-source":
                bad_source = [r for r in records if r.get("source_commit") != expected_source_commit]
                if bad_source:
                    errors.append(
                        f"dryrun has {len(bad_source)} records with source_commit != {expected_source_commit}"
                    )

    # --- source_identity.json (C3) ---
    if source_identity_path.is_file():
        try:
            si = json.loads(source_identity_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"source_identity.json unreadable: {type(exc).__name__}: {exc}")
            si = {}
        if isinstance(si, dict):
            if si.get("dry_run") is not True:
                errors.append(f"source_identity.json dry_run={si.get('dry_run')!r} (expected true)")
            if si.get("profile") != "pilot":
                errors.append(f"source_identity.json profile={si.get('profile')!r} (expected 'pilot')")
            if si.get("protocol_version") != "1.0":
                errors.append(
                    f"source_identity.json protocol_version="
                    f"{si.get('protocol_version')!r} (expected '1.0')"
                )
            if expected_source_commit and si.get("source_commit") != expected_source_commit:
                errors.append(
                    f"source_identity.json source_commit="
                    f"{si.get('source_commit')!r} (expected {expected_source_commit!r})"
                )
            if expected_source_tag and si.get("source_tag") != expected_source_tag:
                errors.append(
                    f"source_identity.json source_tag={si.get('source_tag')!r} (expected {expected_source_tag!r})"
                )
            if expected_deployed_build_id and si.get("deployed_build_id") != expected_deployed_build_id:
                errors.append(
                    f"source_identity.json deployed_build_id={si.get('deployed_build_id')!r} "
                    f"(expected {expected_deployed_build_id!r})"
                )
            if si.get("model_identity") != "dry-run:mock":
                errors.append(
                    f"source_identity.json model_identity={si.get('model_identity')!r} (expected 'dry-run:mock')"
                )
    else:
        errors.append(f"source_identity.json missing: {source_identity_path}")

    # --- HF token ---
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not hf_token:
        errors.append("HF_TOKEN is missing or blank in the environment")

    if errors:
        raise LaunchAuthorizationError(
            "PILOT LAUNCH AUTHORIZATION FAILED:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
