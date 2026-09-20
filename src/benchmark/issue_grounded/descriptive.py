"""Issue-grounded intent headroom - descriptive path-mention detection (T3).

Pure, deterministic literal-mention detection (no model). Reports whether a
query text mentions any proxy-changed target file by exact path, basename, or
module prefix. Used ONLY for descriptive sensitivity analysis; tasks with
path mentions are NOT deleted from the primary result.
"""
from __future__ import annotations

from pathlib import Path


def _basename(path: str) -> str:
    return Path(path.replace("\\", "/")).name


def detect_path_mentions(issue_text: str, proxy_files: list[str]) -> dict:
    """Detect literal mentions of proxy target files in the issue text.

    Returns {"exact_path", "basename", "module", "any_mention"} sorted sets.
    Basenames shorter than 4 characters are excluded (common-token noise).
    """
    text = issue_text or ""
    exact = [p for p in proxy_files if p in text]
    bases = []
    for p in proxy_files:
        b = _basename(p)
        if len(b) >= 4 and b in text:
            bases.append(p)
    modules = []
    for p in proxy_files:
        parts = p.split("/")
        for i in range(len(parts), 1, -1):
            prefix = "/".join(parts[:i])
            if prefix in text:
                modules.append(p)
                break
    return {
        "exact_path": sorted(set(exact)),
        "basename": sorted(set(bases)),
        "module": sorted(set(modules)),
        "any_mention": sorted(set(exact) | set(bases) | set(modules)),
    }
