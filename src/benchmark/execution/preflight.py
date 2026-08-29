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

from benchmark.llm.kaggle_qwen_backend import GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND

logger = logging.getLogger(__name__)

MIN_FREE_VRAM_GIB = 2.0
EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)
PROBE_MAX_TOKENS = 64
PROBE_PROMPT = "def add(a, b):\n    return a + b\n"
CANONICAL_ALLOC_CONF = "expandable_segments:True"
BASELINE_REPO = "todo"
LONG_CONTEXT_TARGET_PROMPT_TOKENS = 12000
LONG_CONTEXT_MAX_TOKENS = 64

# D9: real-Qwen generation-deadline canary. The canary installs a deterministic
# counter guard that becomes false after a tiny bounded number of stopping-
# criterion checks, so the workflow-deadline path (NOT EOS/length) is proven
# target-side after only a few decode tokens. completion_tokens is bounded to
# this tiny range (>= 1 and <= the check limit); the canonical bound constant
# lives in the backend and is imported above (single source of truth).

# D9: public canonical remote for the pre-launch annotated-tag peel proof.
KAGGLE_PUBLIC_CANONICAL_REMOTE = (
    "https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git"
)
PILOT_STABLE_TAG = "v0.9.22-pilot-exec-ready"
REMOTE_TAG_PROOF_TIMEOUT_SECONDS = 30

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
    requested_attn_implementation: str = ""
    effective_attn_implementation: str = ""
    sdpa_kernel_policy: str = ""
    gqa_compatibility_mode: str = ""
    long_context_probe: dict[str, Any] | None = None
    generation_deadline_probe: dict[str, Any] | None = None
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
    # V0.9.22 T4 GQA closure: load evidence is collected INDEPENDENTLY of the
    # short-generation probe. A generation failure (e.g. T4 "No available
    # kernel") must not erase the truthful "weights loaded" evidence, so the
    # reported qwen_model_load stays PASS and the memory footprint stays > 0.
    backend.load()

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
        # V0.9.22 long-context attention closure evidence (fail-closed downstream).
        "requested_attn_implementation": str(
            getattr(backend, "requested_attention_implementation", "") or ""
        ),
        "effective_attn_implementation": str(
            getattr(backend, "effective_attention_implementation", "") or ""
        ),
        "sdpa_kernel_policy": str(getattr(backend, "sdpa_kernel_policy", "") or ""),
        # V0.9.22 T4 GQA repeat-KV compatibility mode (repeat_kv_sm75 on sm75).
        "gqa_compatibility_mode": str(getattr(backend, "gqa_compatibility_mode", "") or ""),
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
        "gpu_vram_by_device": snapshots,
        "allocated_vram_gib": round(allocated_gib, 3),
        "reserved_vram_gib": round(reserved_gib, 3),
        "free_vram_after_probe_gib": round(free_gib, 3),
        "probe_prompt_tokens": 0,
        "probe_completion_tokens": 0,
        # Populated by the separate short-generation probe stage; empty means the
        # probe has not run yet or failed (load evidence above is preserved).
        "short_generation_probe_error": "",
    }

    # Short deterministic generation probe, kept separate from load evidence so
    # a generation failure cannot rewrite load metrics to zero/N/A.
    try:
        response = backend.run_probe(max_tokens=PROBE_MAX_TOKENS, prompt=PROBE_PROMPT)
        metrics["probe_prompt_tokens"] = int(response.token_usage.prompt_tokens)
        metrics["probe_completion_tokens"] = int(response.token_usage.completion_tokens)
    except Exception as exc:
        metrics["short_generation_probe_error"] = f"{type(exc).__name__}: {exc}"

    # D9: cheap real-Qwen generation-deadline canary (workflow-deadline path, not
    # EOS/length). Fail-closed: any error becomes a non-passing canary that the
    # launch-authorization gate rejects. Only the real backend provides the probe;
    # mocked unit backends simply omit it (their legacy assertions are unaffected,
    # while a real launch always requires it).
    canary_runner = getattr(backend, "run_generation_deadline_probe", None)
    if callable(canary_runner):
        try:
            metrics["generation_deadline_probe"] = canary_runner()
        except Exception as exc:
            metrics["generation_deadline_probe"] = {
                "passed": False,
                "deadline_fired": False,
                "finish_reason": "",
                "completion_tokens": 0,
                "error": f"{type(exc).__name__}: {exc}",
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
    result = lc_backend.run_long_context_probe(
        target_prompt_tokens=LONG_CONTEXT_TARGET_PROMPT_TOKENS,
        max_tokens=LONG_CONTEXT_MAX_TOKENS,
    )
    return dict(result)


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
        "requested_attn_implementation": "",
        "effective_attn_implementation": "",
        "sdpa_kernel_policy": "",
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


def _generation_deadline_probe_errors(value: Any) -> list[str]:
    """Fail-closed audit of the real-Qwen generation-deadline canary evidence.

    Returns a list of error strings (empty == PASS). The canary MUST have fired
    the workflow-deadline path (``finish_reason == 'timeout'``,
    ``deadline_fired == true``) with a tiny positive completion-token count, and
    wrong types / missing fields / EOS-or-length / underflow / overflow all fail
    closed (the canary is never allowed to silently report EOS or a bound overrun
    as the deadline proof).
    """
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["model_preflight.json generation_deadline_probe missing or not a dict"]
    if value.get("passed") is not True:
        errors.append("model_preflight.json generation_deadline_probe passed != true")
    if value.get("deadline_fired") is not True:
        errors.append("model_preflight.json generation_deadline_probe deadline_fired != true")
    finish = value.get("finish_reason")
    if finish != "timeout":
        errors.append(
            "model_preflight.json generation_deadline_probe "
            f"finish_reason={finish!r} (expected 'timeout')"
        )
    completion = value.get("completion_tokens")
    if isinstance(completion, bool) or not isinstance(completion, int):
        errors.append(
            "model_preflight.json generation_deadline_probe "
            f"completion_tokens={completion!r} (expected int)"
        )
    else:
        if completion < 1:
            errors.append(
                "model_preflight.json generation_deadline_probe "
                f"completion_tokens={completion} (expected >= 1)"
            )
        if completion > GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND:
            errors.append(
                "model_preflight.json generation_deadline_probe "
                f"completion_tokens={completion} (upper bound "
                f"{GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND})"
            )
    return errors


def verify_remote_annotated_tag_peel(
    *,
    source_commit: str,
    tag: str = PILOT_STABLE_TAG,
    remote: str = KAGGLE_PUBLIC_CANONICAL_REMOTE,
    timeout: int = REMOTE_TAG_PROOF_TIMEOUT_SECONDS,
) -> dict[str, str]:
    """Bounded, no-shell remote annotated-tag peel proof (pre-launch gate only).

    Runs ``git ls-remote --tags <remote> refs/tags/<tag> refs/tags/<tag>^{}`` as
    an exact argv (no shell, no credentials) and requires BOTH the annotated tag
    object ref and its peeled ``^{}`` ref, with the peeled commit equal to the
    notebook's exact ``SOURCE_COMMIT``. Any miss — lightweight tag, missing tag,
    malformed/duplicate output, wrong peel, non-zero exit, timeout, network/DNS/
    TLS failure, or missing ``git`` — raises ``LaunchAuthorizationError``.

    This is an engineering pre-launch gate ONLY; it is not included in any
    scientific run duration or metric and never prints credentials.
    """
    errors: list[str] = []
    peeled_target = f"refs/tags/{tag}^{{}}"
    ref_target = f"refs/tags/{tag}"
    argv = ["git", "ls-remote", "--tags", remote, ref_target, peeled_target]
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        raise LaunchAuthorizationError(
            "REMOTE TAG PEEL PROOF FAILED: 'git' is not installed/on PATH"
        ) from None
    except subprocess.TimeoutExpired:
        raise LaunchAuthorizationError(
            f"REMOTE TAG PEEL PROOF FAILED: git ls-remote timed out after "
            f"{timeout}s against {remote}"
        ) from None
    except OSError as exc:
        raise LaunchAuthorizationError(
            f"REMOTE TAG PEEL PROOF FAILED: git ls-remote raised "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if completed.returncode != 0:
        raise LaunchAuthorizationError(
            "REMOTE TAG PEEL PROOF FAILED: git ls-remote exited "
            f"{completed.returncode} (stderr: "
            f"{(completed.stderr or '').strip()[:300]})"
        )

    lines = [ln.strip() for ln in (completed.stdout or "").splitlines() if ln.strip()]
    ref_line: str | None = None
    peel_line: str | None = None
    duplicates = False
    for ln in lines:
        parts = ln.split()
        if len(parts) != 2:
            errors.append(f"malformed git ls-remote line: {ln[:120]!r}")
            continue
        commit, refname = parts
        if refname == ref_target:
            if ref_line is not None:
                duplicates = True
            ref_line = commit
        elif refname == peeled_target:
            if peel_line is not None:
                duplicates = True
            peel_line = commit

    if duplicates:
        errors.append(f"duplicate/malformed git ls-remote output for {tag}")
    if ref_line is None:
        errors.append(
            f"annotated tag ref refs/tags/{tag} not present (lightweight or missing)"
        )
    if peel_line is None:
        errors.append(f"annotated tag peel {peeled_target} not present")
    if peel_line is not None and peel_line != source_commit:
        errors.append(
            f"annotated tag peel {peel_line!r} != source_commit {source_commit!r}"
        )
    if len(peel_line or "") < 40 or len(ref_line or "") < 40:
        errors.append("git ls-remote returned a malformed/truncated commit hash")

    if errors:
        raise LaunchAuthorizationError(
            "REMOTE TAG PEEL PROOF FAILED:\n"
            + "\n".join(f"  - {e}" for e in errors)
            + f"\n  remote={remote} tag={tag}"
        )
    return {"tag": tag, "peel": peel_line or "", "ref": ref_line or ""}


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
                "attention_policy: SKIP (runtime contract failed)",
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
                f"attention_policy: SKIP ({_REPO_PREFLIGHT_BLOCKED_SUFFIX})",
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
        short_probe_passed = False
        try:
            _shared_backend = _create_qwen_backend(model_path, quantization_mode)
            probe_metrics = _qwen_probe_metrics(model_path, quantization_mode, _backend=_shared_backend)
            # V0.9.22 T4 GQA closure: load evidence is reported independently of
            # the short-generation probe. The weights either loaded (PASS) or
            # they did not (FAIL); a later generation failure cannot rewrite this.
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
            # V0.9.22: canonical attention evidence gate (fail-closed). The
            # v0.9.21 target OOM proved the effective attention path had
            # materialized the quadratic math fallback; the preflight must
            # refuse to pass (and refuse to run the 12k probe) unless the
            # requested/effective implementation and fused-kernel policy are
            # all canonical.
            from benchmark.llm.kaggle_qwen_backend import (
                KAGGLE_ATTENTION_IMPLEMENTATION,
                KAGGLE_SDPA_KERNEL_POLICY,
            )

            requested_attn = str(probe_metrics.get("requested_attn_implementation", "") or "")
            effective_attn = str(probe_metrics.get("effective_attn_implementation", "") or "")
            kernel_policy = str(probe_metrics.get("sdpa_kernel_policy", "") or "")
            gqa_mode = str(probe_metrics.get("gqa_compatibility_mode", "") or "")
            if (
                requested_attn == KAGGLE_ATTENTION_IMPLEMENTATION
                and effective_attn == KAGGLE_ATTENTION_IMPLEMENTATION
                and kernel_policy == KAGGLE_SDPA_KERNEL_POLICY
            ):
                checks.append(
                    "attention_policy: PASS (requested=sdpa effective=sdpa "
                    f"kernel_policy={KAGGLE_SDPA_KERNEL_POLICY} "
                    f"gqa_compat={gqa_mode or 'native'})"
                )
            else:
                checks.append(
                    f"attention_policy: FAIL (requested={requested_attn or 'missing'} "
                    f"effective={effective_attn or 'missing'} "
                    f"kernel_policy={kernel_policy or 'missing'}; "
                    f"expected requested=sdpa effective=sdpa "
                    f"kernel_policy={KAGGLE_SDPA_KERNEL_POLICY})"
                )
            # V0.9.22 T4 GQA: the short deterministic generation probe is a SEPARATE
            # stage. A failure here (e.g. T4 "No available kernel") is reported as
            # short_generation_probe: FAIL while the load evidence above is kept
            # truthful (footprint > 0, device_map preserved). The 12k probe must
            # be skipped, never executed with a broken generation path.
            short_probe_error = str(probe_metrics.get("short_generation_probe_error", "") or "")
            if short_probe_error:
                checks.append(f"short_generation_probe: FAIL ({short_probe_error})")
            else:
                checks.append(
                    f"short_generation_probe: PASS "
                    f"(completion_tokens={probe_metrics.get('probe_completion_tokens', 0)})"
                )
                short_probe_passed = True
            # D9: real-Qwen generation-deadline canary (present only when the real
            # backend ran it). When present it is fail-closed: any validation
            # error flips this check to FAIL and the whole preflight to not-passed.
            deadline_probe = probe_metrics.get("generation_deadline_probe")
            if deadline_probe is not None:
                deadline_errors = _generation_deadline_probe_errors(deadline_probe)
                if deadline_errors:
                    checks.append(
                        "generation_deadline_probe: FAIL ("
                        + "; ".join(
                            e.replace("model_preflight.json generation_deadline_probe ", "")
                            for e in deadline_errors
                        )
                        + ")"
                    )
                else:
                    checks.append(
                        "generation_deadline_probe: PASS "
                        f"(finish_reason={deadline_probe.get('finish_reason')}, "
                        f"completion_tokens={deadline_probe.get('completion_tokens')})"
                    )
            snapshots = probe_metrics.get("gpu_vram_by_device", ())
            if not isinstance(snapshots, tuple):
                snapshots = tuple(snapshots)
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
            checks.append("attention_policy: FAIL (probe did not run)")
            checks.append("vram_headroom: FAIL (probe did not run)")
            checks.append("gpu_count_expected: FAIL (probe did not run)")
            checks.append("checkpoint_not_prequantized: FAIL (probe did not run)")
            short_probe_passed = False
    elif not blocked:
        checks.append(f"qwen_model_load[{quantization_mode}]: SKIP (baseline preflight failed)")
        checks.append("device_map_gpu_only: SKIP (baseline preflight failed)")
        checks.append("attention_policy: SKIP (baseline preflight failed)")
        checks.append("vram_headroom: SKIP (baseline preflight failed)")
        checks.append("gpu_count_expected: SKIP (baseline preflight failed)")
        checks.append("checkpoint_not_prequantized: SKIP (baseline preflight failed)")
        short_probe_passed = False

    failed = [c for c in checks if ": FAIL" in c or ": SKIP" in c]
    passed = not failed and not blocked

    # Long-context stress probe (>= 12k tokens): engineering evidence only.
    # Reuses the single backend loaded above (no second model load). It only
    # runs when load + attention policy + VRAM + short-generation probe all PASS;
    # a broken short-generation path fails closed (SKIP) instead of attempting
    # the expensive 12k probe.
    long_context_probe: dict[str, Any] | None = None
    load_and_policy_ok = not any(
        c.startswith(
            (
                "qwen_model_load: FAIL",
                "attention_policy: FAIL",
                "device_map_gpu_only: FAIL",
                "gpu_count_expected: FAIL",
                "checkpoint_not_prequantized: FAIL",
                "vram_headroom: FAIL",
            )
        )
        for c in checks
    )
    # The 12k probe must only run when load + policy + VRAM + short-generation
    # all PASS with a real backend. When the short-generation probe or a policy
    # gate fails, the 12k probe is skipped (fail-closed) instead of attempting the
    # expensive probe. The real run always retains the loaded backend, so the SKIP
    # branch is reached whenever a stage failed.
    if passed and not probe_failure and load_and_policy_ok and short_probe_passed and _shared_backend is not None:
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
    elif _shared_backend is not None:
        checks.append(
            "long_context_probe: SKIP (load/policy/short-generation stage failed "
            "or blocked; not executed)"
        )
        long_context_probe = long_context_probe or {
            "passed": False,
            "skipped": True,
        }

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
        requested_attn_implementation=str(probe_metrics.get("requested_attn_implementation", "") or ""),
        effective_attn_implementation=str(probe_metrics.get("effective_attn_implementation", "") or ""),
        sdpa_kernel_policy=str(probe_metrics.get("sdpa_kernel_policy", "") or ""),
        gqa_compatibility_mode=str(probe_metrics.get("gqa_compatibility_mode", "") or ""),
        long_context_probe=long_context_probe,
        generation_deadline_probe=probe_metrics.get("generation_deadline_probe"),
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
            "requested_attn_implementation": result.requested_attn_implementation,
            "effective_attn_implementation": result.effective_attn_implementation,
            "sdpa_kernel_policy": result.sdpa_kernel_policy,
            "gqa_compatibility_mode": result.gqa_compatibility_mode,
            "long_context_probe": result.long_context_probe,
            "generation_deadline_probe": result.generation_deadline_probe,
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
        f"requested_attn_implementation: {result.requested_attn_implementation or 'N/A'}",
        f"effective_attn_implementation: {result.effective_attn_implementation or 'N/A'}",
        f"sdpa_kernel_policy: {result.sdpa_kernel_policy or 'N/A'}",
        f"gqa_compatibility_mode: {result.gqa_compatibility_mode or 'N/A'}",
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
    if result.generation_deadline_probe:
        dp = result.generation_deadline_probe
        lines.append(
            f"generation_deadline_probe: finish_reason={dp.get('finish_reason', '?')} "
            f"deadline_fired={dp.get('deadline_fired', '?')} "
            f"completion_tokens={dp.get('completion_tokens', '?')} "
            f"passed={dp.get('passed', '?')}"
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


def _expect_zero_int(field: str, value: Any) -> str | None:
    """Fail-closed int-zero evidence check (no ``or 0`` coercion).

    ``None``, booleans, strings, floats, and non-zero ints all produce an error
    message naming ``field``; only an exact ``int`` 0 passes. ``bool`` is a
    subclass of ``int``, so it is rejected explicitly.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return f"{field}={value!r} (expected int 0)"
    if value != 0:
        return f"{field}={value!r} (expected 0)"
    return None


def _collect_dryrun_evidence_errors(
    dryrun_dir: str | Path,
    *,
    expected_source_commit: str,
    expected_source_tag: str,
    expected_deployed_build_id: str = "",
    expected_model_identity: str = "dry-run:mock",
) -> tuple[list[str], dict[str, Any]]:
    """Fail-closed dry-run evidence auditor for the REAL ``RunRecordData`` schema.

    Single private implementation shared by ``validate_pilot_dryrun_evidence``
    and ``validate_pilot_launch_authorization`` so the schema contract exists in
    exactly one place. Returns ``(errors, summary)``; an empty ``errors`` list
    means the evidence is launch-ready. Strict, coercion-free checks: missing /
    ``None`` / bool / string / float / non-zero values all fail.

    Per-record contract (48 records; real serializer never writes a top-level
    ``total_tokens``):
      * unique non-empty ``run_id``, ``status == "succeeded"``
      * topology: todo=16, djangocms=16, saleor=16,
        iterative_repository_agent=24, selective=24, rep1=24, rep2=24
      * exact ``source_commit`` on EVERY record
      * ``model_calls == 0``
      * ``token_usage: {prompt: 0, completion: 0, total: 0}``
      * ``total_workflow_model_calls == 0`` and ``total_workflow_tokens == 0``
      * phase fields ``selection/regeneration/repair`` ``_model_calls`` and
        ``_total_tokens`` == 0

    ``source_identity.json`` contract: ``dry_run is True``, ``profile ==
    'pilot'``, ``protocol_version == '1.0'``, exact commit/tag/build id, and
    ``model_identity`` == ``expected_model_identity``.
    """
    errors: list[str] = []
    summary: dict[str, Any] = {
        "passed": False,
        "record_count": 0,
        "unique_run_ids": 0,
        "repo_counts": {},
        "strategy_counts": {},
        "rep_counts": {},
        "model_calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_workflow_model_calls": 0,
        "total_workflow_tokens": 0,
        "source_commit": "",
        "source_tag": "",
        "deployed_build_id": "",
        "model_identity": "",
    }

    dryrun_path = Path(dryrun_dir) / "run_records.jsonl"
    source_identity_path = Path(dryrun_dir) / "source_identity.json"

    records: list[dict[str, Any]] = []
    if not dryrun_path.is_file():
        errors.append(f"dryrun records missing: {dryrun_path}")
    else:
        try:
            lines = [
                line.strip()
                for line in dryrun_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            parsed = [json.loads(line) for line in lines]
        except (OSError, ValueError) as exc:
            errors.append(f"dryrun records unreadable: {type(exc).__name__}: {exc}")
            parsed = []
        records = [r for r in parsed if isinstance(r, dict)]

    summary["record_count"] = len(records)
    if len(records) != 48:
        errors.append(f"dryrun record count={len(records)} (expected 48)")

    run_ids: list[object] = []
    repo_counts: dict[str, int] = {}
    strat_counts: dict[str, int] = {}
    rep_counts: dict[Any, int] = {}
    model_calls_total = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    total_workflow_model_calls = 0
    total_workflow_tokens = 0

    for index, record in enumerate(records):
        rid = record.get("run_id")
        run_ids.append(rid)
        if not isinstance(rid, str) or not rid:
            errors.append(
                f"record {index}: run_id={rid!r} (expected non-empty string)"
            )

        status = record.get("status")
        if status != "succeeded":
            errors.append(
                f"record {rid!r}: status={status!r} (expected 'succeeded')"
            )

        repository_id = record.get("repository_id", "")
        repo_counts[repository_id] = repo_counts.get(repository_id, 0) + 1
        strategy_id = record.get("strategy_id", "")
        strat_counts[strategy_id] = strat_counts.get(strategy_id, 0) + 1
        repetition = record.get("repetition")
        rep_counts[repetition] = rep_counts.get(repetition, 0) + 1

        if record.get("source_commit") != expected_source_commit:
            errors.append(
                f"record {rid!r}: source_commit={record.get('source_commit')!r} "
                f"(expected {expected_source_commit!r})"
            )

        model_calls = record.get("model_calls")
        if isinstance(model_calls, int) and not isinstance(model_calls, bool):
            model_calls_total += model_calls
        if isinstance(model_calls, int) and not isinstance(model_calls, bool) and model_calls != 0:
            errors.append(
                f"record {rid!r}: model_calls != 0 (actual {model_calls!r})"
            )
        elif not isinstance(model_calls, int) or isinstance(model_calls, bool):
            errors.append(
                f"record {rid!r}: model_calls={model_calls!r} (expected int 0)"
            )

        # token_usage mapping (real serializer: {"prompt": 0, "completion": 0, "total": 0}).
        token_usage = record.get("token_usage")
        if not isinstance(token_usage, dict):
            errors.append(
                f"record {rid!r}: token_usage={token_usage!r} "
                f"(expected dict with prompt/completion/total)"
            )
        else:
            for token_key in ("prompt", "completion", "total"):
                if token_key not in token_usage:
                    errors.append(
                        f"record {rid!r}: token_usage.{token_key} missing "
                        f"(expected int 0)"
                    )
                    continue
                token_value = token_usage[token_key]
                error = _expect_zero_int(f"record {rid!r}: token_usage.{token_key}", token_value)
                if error:
                    errors.append(error)
                if token_key == "prompt" and isinstance(token_value, int) and not isinstance(token_value, bool):
                    prompt_tokens += token_value
                if token_key == "completion" and isinstance(token_value, int) and not isinstance(token_value, bool):
                    completion_tokens += token_value
                if token_key == "total" and isinstance(token_value, int) and not isinstance(token_value, bool):
                    total_tokens += token_value

        workflow_calls = record.get("total_workflow_model_calls")
        error = _expect_zero_int(f"record {rid!r}: total_workflow_model_calls", workflow_calls)
        if error:
            errors.append(error)
        if isinstance(workflow_calls, int) and not isinstance(workflow_calls, bool):
            total_workflow_model_calls += workflow_calls

        workflow_tokens = record.get("total_workflow_tokens")
        error = _expect_zero_int(f"record {rid!r}: total_workflow_tokens", workflow_tokens)
        if error:
            errors.append(error)
        if isinstance(workflow_tokens, int) and not isinstance(workflow_tokens, bool):
            total_workflow_tokens += workflow_tokens

        for phase_field in (
            "selection_model_calls",
            "regeneration_model_calls",
            "repair_model_calls",
            "selection_total_tokens",
            "regeneration_total_tokens",
            "repair_total_tokens",
        ):
            value = record.get(phase_field)
            if phase_field not in record:
                errors.append(
                    f"record {rid!r}: {phase_field} missing (expected int 0)"
                )
                continue
            error = _expect_zero_int(f"record {rid!r}: {phase_field}", value)
            if error:
                errors.append(error)

    summary["unique_run_ids"] = len({rid for rid in run_ids if rid is not None})
    if len({rid for rid in run_ids if rid is not None}) != 48:
        errors.append(
            f"dryrun unique run_ids="
            f"{len({rid for rid in run_ids if rid is not None})} (expected 48)"
        )
    summary["repo_counts"] = repo_counts
    expected_repo = {"todo": 16, "djangocms": 16, "saleor": 16}
    if repo_counts != expected_repo:
        errors.append(f"dryrun repo_counts={repo_counts} (expected {expected_repo})")
    summary["strategy_counts"] = strat_counts
    expected_strat = {"iterative_repository_agent": 24, "selective": 24}
    if strat_counts != expected_strat:
        errors.append(
            f"dryrun strategy_counts={strat_counts} (expected {expected_strat})"
        )
    numeric_rep_counts = {
        key: value
        for key, value in rep_counts.items()
        if isinstance(key, int) and not isinstance(key, bool)
    }
    summary["rep_counts"] = numeric_rep_counts
    expected_rep = {1: 24, 2: 24}
    if numeric_rep_counts != expected_rep:
        errors.append(
            f"dryrun rep_counts={rep_counts} (expected {expected_rep})"
        )
    summary["model_calls"] = model_calls_total
    summary["prompt_tokens"] = prompt_tokens
    summary["completion_tokens"] = completion_tokens
    summary["total_tokens"] = total_tokens
    summary["total_workflow_model_calls"] = total_workflow_model_calls
    summary["total_workflow_tokens"] = total_workflow_tokens

    # --- source_identity.json (C3) ---
    if not source_identity_path.is_file():
        errors.append(f"source_identity.json missing: {source_identity_path}")
    else:
        si: dict[str, Any] = {}
        try:
            loaded = json.loads(source_identity_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                si = loaded
        except (OSError, ValueError) as exc:
            errors.append(f"source_identity.json unreadable: {type(exc).__name__}: {exc}")
        summary["source_commit"] = str(si.get("source_commit", ""))
        summary["source_tag"] = str(si.get("source_tag", ""))
        summary["deployed_build_id"] = str(si.get("deployed_build_id", ""))
        summary["model_identity"] = str(si.get("model_identity", ""))
        if si.get("dry_run") is not True:
            errors.append(
                f"source_identity.json dry_run={si.get('dry_run')!r} (expected true)"
            )
        if si.get("profile") != "pilot":
            errors.append(
                f"source_identity.json profile={si.get('profile')!r} (expected 'pilot')"
            )
        if si.get("protocol_version") != "1.0":
            errors.append(
                f"source_identity.json protocol_version="
                f"{si.get('protocol_version')!r} (expected '1.0')"
            )
        if expected_source_commit and si.get("source_commit") != expected_source_commit:
            errors.append(
                f"source_identity.json source_commit={si.get('source_commit')!r} "
                f"(expected {expected_source_commit!r})"
            )
        if expected_source_tag and si.get("source_tag") != expected_source_tag:
            errors.append(
                f"source_identity.json source_tag={si.get('source_tag')!r} "
                f"(expected {expected_source_tag!r})"
            )
        if expected_deployed_build_id and si.get("deployed_build_id") != expected_deployed_build_id:
            errors.append(
                f"source_identity.json deployed_build_id={si.get('deployed_build_id')!r} "
                f"(expected {expected_deployed_build_id!r})"
            )
        if si.get("model_identity") != expected_model_identity:
            errors.append(
                f"source_identity.json model_identity={si.get('model_identity')!r} "
                f"(expected {expected_model_identity!r})"
            )

    summary["passed"] = not errors
    return errors, summary


def validate_pilot_dryrun_evidence(
    *,
    dryrun_dir: str | Path,
    expected_source_commit: str,
    expected_source_tag: str,
    expected_deployed_build_id: str = "",
    expected_model_identity: str = "dry-run:mock",
) -> dict[str, Any]:
    """Fail-closed dry-run evidence gate against the REAL ``RunRecordData`` schema.

    Re-validates the full 48-cell mock dry-run artifact (records + source
    identity) exactly as generated by the CLI ``--dry-run`` run. Strict and
    coercion-free: missing / ``None`` / bool / string / float / non-zero token
    and call fields fail closed. Returns the truthful summary only when every
    check passes; raises ``LaunchAuthorizationError`` on any failure.
    """
    errors, summary = _collect_dryrun_evidence_errors(
        dryrun_dir,
        expected_source_commit=expected_source_commit,
        expected_source_tag=expected_source_tag,
        expected_deployed_build_id=expected_deployed_build_id,
        expected_model_identity=expected_model_identity,
    )
    if errors:
        raise LaunchAuthorizationError(
            "PILOT DRY-RUN EVIDENCE VALIDATION FAILED:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
    return summary


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
    from benchmark.llm.kaggle_qwen_backend import (
        KAGGLE_ATTENTION_IMPLEMENTATION,
        KAGGLE_SDPA_GQA_COMPATIBILITY,
        KAGGLE_SDPA_KERNEL_POLICY,
    )

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
            # V0.9.22: canonical attention evidence is mandatory for launch.
            requested_attn = str(model_evidence.get("requested_attn_implementation", "") or "")
            effective_attn = str(model_evidence.get("effective_attn_implementation", "") or "")
            kernel_policy = str(model_evidence.get("sdpa_kernel_policy", "") or "")
            if requested_attn != KAGGLE_ATTENTION_IMPLEMENTATION:
                errors.append(
                    f"model_preflight.json requested_attn_implementation="
                    f"{requested_attn!r} (expected {KAGGLE_ATTENTION_IMPLEMENTATION!r})"
                )
            if effective_attn != KAGGLE_ATTENTION_IMPLEMENTATION:
                errors.append(
                    f"model_preflight.json effective_attn_implementation="
                    f"{effective_attn!r} (expected {KAGGLE_ATTENTION_IMPLEMENTATION!r})"
                )
            if kernel_policy != KAGGLE_SDPA_KERNEL_POLICY:
                errors.append(
                    f"model_preflight.json sdpa_kernel_policy="
                    f"{kernel_policy!r} (expected {KAGGLE_SDPA_KERNEL_POLICY!r})"
                )
            # V0.9.22 T4 GQA: when the model evidence reports a GQA compatibility
            # mode it must equal the canonical repeat-KV sm75 mode. Absent (older
            # evidence) is tolerated for backward compatibility; present-but-wrong
            # fails closed.
            gqa_mode = str(model_evidence.get("gqa_compatibility_mode", "") or "")
            if gqa_mode and gqa_mode != KAGGLE_SDPA_GQA_COMPATIBILITY:
                errors.append(
                    f"model_preflight.json gqa_compatibility_mode="
                    f"{gqa_mode!r} (expected {KAGGLE_SDPA_GQA_COMPATIBILITY!r})"
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
            # D9: the real-Qwen generation-deadline canary is mandatory for launch.
            # Missing / wrong-type / false fields / EOS-or-length / underflow /
            # overflow all fail closed (the canary proves the deadline path fired).
            errors.extend(
                _generation_deadline_probe_errors(
                    model_evidence.get("generation_deadline_probe")
                )
            )

    # --- Dry-run records + source_identity.json (C1-C4, REAL RunRecordData schema) ---
    # Single source of truth: the private collector shared with
    # validate_pilot_dryrun_evidence keeps the schema contract in ONE place so a
    # notebook/CLI check can never drift from the launch gate.
    dryrun_errors, _summary = _collect_dryrun_evidence_errors(
        dryrun_dir,
        expected_source_commit=expected_source_commit,
        expected_source_tag=expected_source_tag,
        expected_deployed_build_id=expected_deployed_build_id,
        expected_model_identity="dry-run:mock",
    )
    errors.extend(dryrun_errors)

    # --- HF token ---
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not hf_token:
        errors.append("HF_TOKEN is missing or blank in the environment")

    if errors:
        raise LaunchAuthorizationError(
            "PILOT LAUNCH AUTHORIZATION FAILED:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
