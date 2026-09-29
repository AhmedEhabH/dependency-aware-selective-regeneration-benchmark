"""Shared constants and helpers for the v2.2 kit (brain-authored)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[4]
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
V22_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v22"
EVALUATOR_SETS = (PROJECT / "research" / "wp2" / "harness_v3_2026-09-26" / "evaluator_only"
                  / "eng_evaluator_sets_v3.json")

SMOKE_VERSION_V22 = "wp2-e2e-smoke-eng-v22"
TERMINAL = frozenset({"NO_SCOPE", "INVALID_AFTER_REPAIR", "APPLIED"})
FORBIDDEN_STATUS = frozenset({"GENERATION_FAIL"})
VARIANCE_TASKS = ("saleor-rc-2d45b76a52f2", "saleor-rc-644f33094857",
                  "saleor-rc-d220843b5418")
VARIANCE_ARM = "GOLD_HARD"
VARIANCE_LABELS = ("var_r1", "var_r2")
SCIENTIFIC_CEILING_USD = 2.00
WORST_EPISODE_USD = 0.08
WSL_DISTRO = "Ubuntu-24.04"
ERA_IMAGES = ("wp2-era-py38", "wp2-era-py39", "wp2-era-py312")
PG_CONTAINER = "wp2-pg"


def norm_sha256(path: Path) -> str:
    """SHA-256 with CRLF normalized to LF for text files (autocrlf-proof)."""
    data = Path(path).read_bytes()
    if b"\x00" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def json_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def planned_main() -> list[tuple[str, str, str]]:
    """(task_id, arm, label) in the frozen order: task sorted, arm order of spec.ARMS."""
    from benchmark.wp2.e2e.spec import ARMS, SMOKE_TASKS
    return [(t, a, a) for t in sorted(SMOKE_TASKS) for a in ARMS]


def planned_variance() -> list[tuple[str, str, str]]:
    return [(t, VARIANCE_ARM, lab) for t in sorted(VARIANCE_TASKS) for lab in VARIANCE_LABELS]


def episode_path(root: Path, subdir: str, task_id: str, label: str) -> Path:
    return root / subdir / task_id / label / "episode.json"


def read_status(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("status")
    except (ValueError, OSError):
        return "UNREADABLE"


Runner = Callable[[list[str], int], subprocess.CompletedProcess]


def _default_runner(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def env_identity(runner: Runner = _default_runner) -> dict[str, Any]:
    """Docker identities of the evaluation environment (drift detection)."""
    out: dict[str, Any] = {"era_images": {}, "postgres": {}, "errors": []}
    base = ["wsl", "-d", WSL_DISTRO, "--", "docker"]
    for img in ERA_IMAGES:
        r = runner(base + ["image", "inspect", "--format", "{{.Id}}", img], 120)
        if r.returncode == 0 and r.stdout.strip():
            out["era_images"][img] = r.stdout.strip()
        else:
            out["errors"].append(f"image {img} missing")
    r = runner(base + ["inspect", "--format", "{{.Image}}", PG_CONTAINER], 120)
    if r.returncode == 0 and r.stdout.strip():
        image_id = r.stdout.strip()
        out["postgres"]["image_id"] = image_id
        r2 = runner(base + ["image", "inspect", "--format", "{{json .RepoDigests}}", image_id], 120)
        out["postgres"]["repo_digests"] = (json.loads(r2.stdout) if r2.returncode == 0
                                           and r2.stdout.strip().startswith("[") else [])
    else:
        out["errors"].append(f"container {PG_CONTAINER} missing")
    return out
