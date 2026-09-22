"""WP-1b label-access guard (prediction side).

Installs a ``sys.addaudithook`` hook that raises ``PermissionError`` whenever
the current process opens a file that carries (or can reveal) outcome labels
while predictions are being produced. Once installed it cannot be removed;
install it only in the prediction process (the MAIN_297 / variance runner).

Forbidden (relative to the project root, case-insensitive):

* ``research/transparency/saleor_candidate_metadata.json`` and any
  ``*candidate_metadata*`` file: holds ``eligibility.proxy_paths`` for EVERY
  Saleor task, including the 786 SEALED RESERVE outcomes;
* anything under ``research/saleor-reserve-300-rmcss/`` (opened proxies,
  candidate rows, memory bundles - none is an agent input);
* any file whose name contains ``proxies`` / ``proxy`` / ``gold`` /
  ``expected_affected`` / ``outcome`` / ``hidden``;
* any path with a ``hidden`` directory segment;
* inside ``benchmark_data/real_commit_impact_saleor/`` everything EXCEPT
  ``scientific/<task>/case_manifest.json`` and ``scientific/<task>/public/*``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_FORBIDDEN_NAME_FRAGMENTS: tuple[str, ...] = (
    "candidate_metadata",
    "proxies",
    "proxy",
    "gold",
    "expected_affected",
    "outcome",
    "hidden",
)
_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "research/saleor-reserve-300-rmcss/",
    "research/transparency/saleor_candidate_metadata",
)
_SALEOR_DATA = "benchmark_data/real_commit_impact_saleor/"

_installed_roots: list[str] = []
_installed_modes: dict[str, str] = {}


def is_forbidden_relative(rel: str) -> bool:
    """Decide on a project-relative POSIX path (exposed for tests)."""
    low = rel.replace("\\", "/").lower().lstrip("./")
    if any(low.startswith(p) for p in _FORBIDDEN_PREFIXES):
        return True
    parts = low.split("/")
    if "hidden" in parts[:-1]:
        return True
    name = parts[-1]
    if any(frag in name for frag in _FORBIDDEN_NAME_FRAGMENTS):
        return True
    if low.startswith(_SALEOR_DATA):
        tail = low[len(_SALEOR_DATA):].split("/")
        # allowed: scientific/<task>/case_manifest.json | scientific/<task>/public/<file>
        allowed_manifest = len(tail) == 3 and tail[0] == "scientific" and tail[2] == "case_manifest.json"
        allowed_public = len(tail) == 4 and tail[0] == "scientific" and tail[2] == "public"
        return not (allowed_manifest or allowed_public)
    return False


def is_sealed_relative(rel: str) -> bool:
    """Scoring-side policy: the opened RESERVE-300 proxies ARE allowed, but the
    786 sealed RESERVE outcomes (candidate metadata, hidden dirs, any Saleor
    data outside ``scientific/<task>/{case_manifest.json,public/*}``) are not."""
    low = rel.replace("\\", "/").lower().lstrip("./")
    parts = low.split("/")
    if "candidate_metadata" in parts[-1] or "hidden" in parts[:-1]:
        return True
    if low.startswith(_SALEOR_DATA):
        tail = low[len(_SALEOR_DATA):].split("/")
        allowed_manifest = len(tail) == 3 and tail[0] == "scientific" and tail[2] == "case_manifest.json"
        allowed_public = len(tail) == 4 and tail[0] == "scientific" and tail[2] == "public"
        return not (allowed_manifest or allowed_public)
    return False


def _hook(event: str, args: tuple[Any, ...]) -> None:
    if event != "open" or not args:
        return
    target = args[0]
    if isinstance(target, int) or target is None:
        return
    try:
        path = os.path.abspath(os.fsdecode(target))
    except (TypeError, ValueError):
        return
    norm = path.replace("\\", "/")
    for root in _installed_roots:
        if norm.lower().startswith(root.lower() + "/"):
            rel = norm[len(root) + 1:]
            if _installed_modes.get(root) == "scoring":
                if is_sealed_relative(rel):
                    raise PermissionError(f"SEALED_OUTCOME_ACCESS_VIOLATION: scoring process opened {rel}")
            elif is_forbidden_relative(rel):
                raise PermissionError(f"LABEL_ACCESS_VIOLATION: prediction process opened {rel}")


def _install(project_dir: Path, mode: str) -> None:
    root = os.path.abspath(str(project_dir)).replace("\\", "/").rstrip("/")
    if root in _installed_roots:
        if _installed_modes[root] != mode:
            raise RuntimeError("a different guard mode is already installed for this project root")
        return
    first = not _installed_roots
    _installed_roots.append(root)
    _installed_modes[root] = mode
    if first:
        sys.addaudithook(_hook)


def install_label_access_guard(project_dir: Path) -> None:
    """Prediction-side guard: no label-bearing file may be opened (idempotent)."""
    _install(project_dir, "prediction")


def install_sealed_outcome_guard(project_dir: Path) -> None:
    """Scoring-side guard: opened RESERVE-300 proxies allowed; 786 sealed outcomes not."""
    _install(project_dir, "scoring")
