"""WP-2 Mission-11 E2E Smoke - multi-file patch format (B5).

Parser for the Appendix P1 format: a ``FILE: <path>`` line followed by one or
more SEARCH/REPLACE blocks. Reuses the frozen exact_patch block semantics
(literal match, exactly-once, blocks applied in order, fail-closed, the D048
one-trailing-newline recovery and nothing else). Outputs final texts per edited
file plus a unified diff (git --no-index style, a/ b/ prefixes).

Mission-12 Interface v2 additions (I01-I03, G): ``extract_envelope``, the
SEARCH matching ladder (exact -> right-strip tolerant), and ``SEARCH_ELLIPSIS``
rejection. The v1 functions below are unchanged; v2 entry points are suffixed
``_v2``.
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


# ---------------------------------------------------------------------------
# Interface v2 (I01-I03 / wrapper G): envelope extraction, matching ladder,
# SEARCH_ELLIPSIS. The v1 parse/apply functions above are unchanged.
# ---------------------------------------------------------------------------

_PREAMBLE_FILE_RE = re.compile(r"^FILE:\s*\S+")
_FENCE_RE = re.compile(r"^```.*$")
_ELLIPSIS_RE = re.compile(r"^(\.\.\.|…|#\s*\.\.\.)\s*$")


def extract_envelope(text: str) -> tuple[str, dict]:
    """I01 envelope extraction.

    (a) drop every line before the first ``^FILE: `` line;
    (b) outside SEARCH/REPLACE bodies, drop lines that are markdown fences
        (``^```.*$``) and any other non-``FILE:`` lines (interstitial prose);
    (c) drop everything after the last ``>>>>>>> REPLACE``.

    Content inside SEARCH and REPLACE bodies is never altered.
    Returns (clean_text, stats) where stats has:
      preamble_lines, fence_lines, interstitial_lines, trailing_lines
    """
    stats = {"preamble_lines": 0, "fence_lines": 0,
             "interstitial_lines": 0, "trailing_lines": 0}
    lines = text.splitlines(keepends=True)

    # (a) find the first FILE: line
    first_file = -1
    for i, ln in enumerate(lines):
        if _PREAMBLE_FILE_RE.match(ln):
            first_file = i
            break
    if first_file == -1:
        stats["preamble_lines"] = len(lines)
        return "", stats
    stats["preamble_lines"] = first_file

    # (c) find the last REPLACE marker
    last_replace = -1
    for i in range(first_file, len(lines)):
        if lines[i].rstrip("\r\n") == ">>>>>>> REPLACE":
            last_replace = i
    if last_replace == -1:
        last_replace = len(lines)  # no REPLACE marker: nothing trailing to keep

    clean: list[str] = []
    in_block = False
    for i in range(first_file, min(last_replace + 1, len(lines))):
        ln = lines[i]
        stripped = ln.rstrip("\r\n")
        if stripped == "<<<<<<< SEARCH":
            in_block = True
            clean.append(ln)
            continue
        if stripped == ">>>>>>> REPLACE":
            in_block = False
            clean.append(ln)
            continue
        if in_block or _PREAMBLE_FILE_RE.match(ln):
            # inside a body, or a FILE: line -> keep verbatim
            clean.append(ln)
            continue
        # outside any body
        if _FENCE_RE.match(ln):
            stats["fence_lines"] += 1
        else:
            stats["interstitial_lines"] += 1

    trailing = len(lines) - (last_replace + 1)
    if last_replace >= len(lines):
        trailing = 0
    stats["trailing_lines"] = max(0, trailing)
    return "".join(clean), stats


def _contains_ellipsis(body: str) -> bool:
    return any(_ELLIPSIS_RE.match(ln.rstrip("\r\n")) for ln in body.splitlines())


def _right_strip_lines(s: str) -> str:
    return "\n".join(ln.rstrip() for ln in s.split("\n"))


def parse_multi_file_patch_v2(text: str) -> tuple[list[tuple[str, list[Any]]], dict]:
    """Interface-v2 parse: envelope extraction (I01) + SEARCH_ELLIPSIS check (I03).

    Returns (sections, stats). sections entries are (path, [ExactPatchBlock,...])
    exactly like v1; stats carries the envelope counts and an ``ellipsis`` flag.
    Raises ValueError('SEARCH_ELLIPSIS:<path>') if a SEARCH body is only an
    ellipsis line.
    """
    clean, stats = extract_envelope(text)
    if not clean.strip():
        raise ValueError("NO_BLOCKS: no FILE sections found")
    sections = _parse_file_sections(clean)
    for path, blocks in sections:
        for block in blocks:
            if _contains_ellipsis(block.search):
                stats.setdefault("ellipsis", [])
                stats["ellipsis"].append(path)
                raise ValueError(f"SEARCH_ELLIPSIS:{path}")
    stats.setdefault("ellipsis", [])
    return sections, stats


def _tolerant_matches(content: str, search: str) -> int:
    """I02 ladder step 2: unique count with every line right-stripped on both sides."""
    c_lines = content.splitlines()
    s_lines = [ln.rstrip() for ln in search.splitlines()]
    if not s_lines:
        return 0
    count = 0
    n = len(s_lines)
    for i in range(len(c_lines) - n + 1):
        if all(c_lines[i + k].rstrip() == s_lines[k] for k in range(n)):
            count += 1
            if count > 1:
                return count
    return count


def _tolerant_match_span(content: str, search: str) -> tuple[int, int] | None:
    """Return (start_line, end_line_exclusive) of the unique tolerant match."""
    c_lines = content.splitlines()
    s_lines = [ln.rstrip() for ln in search.splitlines()]
    n = len(s_lines)
    found: list[tuple[int, int]] = []
    for i in range(len(c_lines) - n + 1):
        if all(c_lines[i + k].rstrip() == s_lines[k] for k in range(n)):
            found.append((i, i + n))
            if len(found) > 1:
                return None
    return found[0] if found else None


def apply_patch_v2(parent_texts: dict[str, str], sections: list[tuple[str, list[Any]]],
                   editable: set[str]) -> tuple[dict[str, str], list[dict]]:
    """I02 matching ladder + apply. Returns (out, block_results).

    block_results: per applied block dict with keys path, block_index, mode
    ('EXACT' | 'WHITESPACE_TOLERANT'), applied bool. Fail-closed on zero or
    ambiguous matches; no other fuzzy matching beyond I02.
    """
    from benchmark.execution.exact_patch import ExactPatchError, apply_exact_patches

    out = dict(parent_texts)
    results: list[dict] = []
    for path, blocks in sections:
        if is_test_path_v2(path):
            raise ValueError(f"TEST_PATH:{path}")
        if path not in editable:
            raise ValueError(f"OUT_OF_SCOPE_FILE:{path}")
        if path not in out:
            raise ValueError(f"OUT_OF_SCOPE_FILE:{path}")
        content = out[path]
        for bi, block in enumerate(blocks, start=1):
            search = block.search
            count = content.count(search)
            mode = "EXACT"
            if count == 0:
                # ladder step 2: right-strip every line on both sides
                count = _tolerant_matches(content, search)
                mode = "WHITESPACE_TOLERANT"
            if count == 0:
                raise ValueError(
                    f"SEARCH_ERROR:{path}: block {bi}: SEARCH content not found "
                    f"in current file (count=0); search={search[:80]!r}")
            if count > 1:
                raise ValueError(
                    f"SEARCH_ERROR:{path}: block {bi}: SEARCH content is "
                    f"ambiguous, matched {count} times; search={search[:80]!r}")
            if mode == "EXACT":
                try:
                    content = apply_exact_patches(content, [block])
                except ExactPatchError as exc:
                    raise ValueError(f"SEARCH_ERROR:{path}: {exc}") from exc
            else:
                span = _tolerant_match_span(content, search)
                if span is None:
                    raise ValueError(
                        f"SEARCH_ERROR:{path}: block {bi}: tolerant span lost; "
                        f"search={search[:80]!r}")
                start, end = span
                ends_nl = content.endswith("\n")
                c_lines = content.splitlines()
                repl_lines = block.replace.splitlines()
                new_lines = c_lines[:start] + repl_lines + c_lines[end:]
                content = "\n".join(new_lines)
                if ends_nl:
                    content += "\n"
            results.append({"path": path, "block_index": bi,
                            "mode": mode, "applied": True})
        out[path] = content
    return out, results
