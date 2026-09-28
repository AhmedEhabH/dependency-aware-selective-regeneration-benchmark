"""WP-2 Mission-11 E2E Smoke - multi-file patch format (B5).

Parser for the Appendix P1 format: a ``FILE: <path>`` line followed by one or
more SEARCH/REPLACE blocks. Reuses the frozen exact_patch block semantics
(literal match, exactly-once, blocks applied in order, fail-closed, the D048
one-trailing-newline recovery and nothing else). Outputs final texts per edited
file plus a unified diff (git --no-index style, a/ b/ prefixes).
"""
from __future__ import annotations

import re
from typing import Any

from benchmark.wp2.e2e.spec import ARMS  # noqa: F401  (documented boundary)
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

_ERROR_TYPES = (
    "PARSE_ERROR", "NO_BLOCKS", "OUT_OF_SCOPE_FILE", "TEST_PATH",
    "SEARCH_NOT_FOUND", "SEARCH_AMBIGUOUS", "EMPTY_SEARCH",
)


def parse_multi_file_patch(text: str) -> list[tuple[str, list[Any]]]:
    """Parse the P1 format into [(path, [ExactPatchBlock, ...]), ...]."""
    from benchmark.wp2.e2e.patch_format import _parse_file_sections
    return _parse_file_sections(text)


def _parse_file_sections(text: str) -> list[tuple[str, list[Any]]]:
    from benchmark.execution.exact_patch import parse_exact_patch

    sections: list[tuple[str, list[Any]]] = []
    current_path: str | None = None
    current_buf: list[str] = []
    current_start = 0
    lines = text.splitlines(keepends=True)

    def flush() -> None:
        nonlocal current_path, current_buf, current_start
        if current_path is None:
            return
        body = "".join(current_buf)
        try:
            blocks = parse_exact_patch(body)
        except Exception as exc:
            raise ValueError(f"PARSE_ERROR:{current_path}: {exc}") from exc
        sections.append((current_path, blocks))
        current_path = None
        current_buf = []

    i = 0
    while i < len(lines):
        m = re.match(r"^FILE:\s*(\S+)\s*$", lines[i].rstrip("\n"))
        if m:
            flush()
            current_path = m.group(1)
            current_start = i
        else:
            current_buf.append(lines[i])
        i += 1
    flush()
    if not sections:
        raise ValueError("NO_BLOCKS: no FILE sections found")
    return sections


def apply_patch(parent_texts: dict[str, str], sections: list[tuple[str, list[Any]]],
                editable: set[str]) -> dict[str, str]:
    """Apply sections in order to parent_texts; fail-closed with named errors."""
    from benchmark.execution.exact_patch import ExactPatchError, apply_exact_patches

    out = dict(parent_texts)
    for path, blocks in sections:
        if is_test_path_v2(path):
            raise ValueError(f"TEST_PATH:{path}")
        if path not in editable:
            raise ValueError(f"OUT_OF_SCOPE_FILE:{path}")
        if path not in out:
            raise ValueError(f"OUT_OF_SCOPE_FILE:{path}")
        content = out[path]
        try:
            applied = apply_exact_patches(content, blocks)
        except ExactPatchError as exc:
            raise ValueError(f"SEARCH_ERROR:{path}: {exc}") from exc
        out[path] = applied
    return out


def unified_diff(old: dict[str, str], new: dict[str, str]) -> str:
    """Unified diff (git apply-able) with a/ b/ prefixes, relative paths."""
    import difflib
    parts: list[str] = []
    for path in sorted(set(old) | set(new)):
        if old.get(path) == new.get(path):
            continue
        old_lines = (old.get(path) or "").splitlines(keepends=True)
        new_lines = (new.get(path) or "").splitlines(keepends=True)
        parts.append(f"diff --git a/{path} b/{path}")
        parts.append("--- " + f"a/{path}")
        parts.append("+++ " + f"b/{path}")
        hunk = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{path}",
                                         tofile=f"b/{path}", n=3))
        # strip the first 2 header lines difflib adds (---/+++ with full paths)
        for line in hunk[2:]:
            parts.append(line.rstrip("\n"))
    return "\n".join(parts) + "\n"


def named_error(exc: ValueError) -> str:
    return str(exc)
