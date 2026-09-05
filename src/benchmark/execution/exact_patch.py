"""Exact SEARCH/REPLACE patch format shared by every regeneration strategy.

The exact-patch format is deliberately narrow and fail-closed.  A model output
is a sequence of one or more self-delimited blocks:

    <<<<<<< SEARCH
    <exact block to find>
    =======
    <replacement block>
    >>>>>>> REPLACE

Semantics:

- SEARCH and REPLACE contents are matched and substituted LITERALLY.  There is
  no regex, no fuzzy matching, and no whitespace normalisation.
- Every SEARCH block must occur EXACTLY ONCE in the (current) content being
  patched.  Zero or multiple matches are both hard errors (_fail-closed_).
- Blocks are applied in order; a later block sees the result of earlier
  blocks, mirroring a real edit session.
- Delimiter lines start at column 0 (leading whitespace is never part of the
  delimiting markers).  Within a block, the first ``=======`` line separates
  SEARCH from REPLACE; a trailing ``>>>>>>> REPLACE`` line terminates it.
- Any malformed block (missing markers, wrong order, unterminated, empty
  SEARCH, extra delimiters) raises :class:`ExactPatchError`.

The executor uses this parser to turn a model response into the exact final
file for "modify" targets, replacing the complete-file regeneration mode that
required the model to resynthesise whole (potentially enormous) files.
"""

from __future__ import annotations

from dataclasses import dataclass


class ExactPatchError(ValueError):
    """Raised when a model patch is malformed or a SEARCH block is ambiguous."""


@dataclass(frozen=True)
class ExactPatchBlock:
    search: str
    replace: str


_SEARCH_MARKER = "<<<<<<< SEARCH"
_REPLACE_MARKER = ">>>>>>> REPLACE"
_DIVIDER = "======="


def _strip_trailing_newline(line: str) -> str:
    if line.endswith("\n"):
        return line[:-1]
    return line


def _is_marker_line(line: str, marker: str) -> bool:
    stripped = _strip_trailing_newline(line)
    return stripped == marker


def parse_exact_patch(text: str) -> list[ExactPatchBlock]:
    """Parse a full exact-patch payload into an ordered list of blocks.

    Raises :class:`ExactPatchError` on any structural defect; no partial result
    is ever returned.
    """
    if not text or not text.strip():
        raise ExactPatchError("exact patch is empty")

    lines = text.splitlines(keepends=True)
    blocks: list[ExactPatchBlock] = []
    i = 0
    n = len(lines)

    while i < n:
        if not lines[i].strip():
            i += 1
            continue

        if not _is_marker_line(lines[i], _SEARCH_MARKER):
            raise ExactPatchError(
                "expected '<<<<<<< SEARCH' block start, found: "
                f"{_strip_trailing_newline(lines[i])!r}"
            )
        i += 1

        search_lines: list[str] = []
        while i < n and not _is_marker_line(lines[i], _DIVIDER):
            if _is_marker_line(lines[i], _REPLACE_MARKER):
                raise ExactPatchError(
                    "replacement marker before SEARCH/REPLACE divider"
                )
            search_lines.append(lines[i])
            i += 1

        if i >= n:
            raise ExactPatchError(
                "SEARCH block not terminated by a '=======' divider"
            )
        i += 1

        replace_lines: list[str] = []
        while i < n and not _is_marker_line(lines[i], _REPLACE_MARKER):
            if _is_marker_line(lines[i], _SEARCH_MARKER):
                raise ExactPatchError(
                    "new '<<<<<<< SEARCH' marker before closing the previous block"
                )
            replace_lines.append(lines[i])
            i += 1

        if i >= n:
            raise ExactPatchError(
                "REPLACE block not terminated by a '>>>>>>> REPLACE' marker"
            )
        i += 1

        search = "".join(search_lines)
        replace = "".join(replace_lines)
        if not search.strip():
            raise ExactPatchError("SEARCH block is empty")
        blocks.append(ExactPatchBlock(search=search, replace=replace))

    if not blocks:
        raise ExactPatchError("no SEARCH/REPLACE blocks found")
    return blocks


def apply_exact_patches(current_content: str, blocks: list[ExactPatchBlock]) -> str:
    """Apply *blocks* literally and fail-closed against *current_content*.

    Each SEARCH block must match exactly once; otherwise :class:`ExactPatchError`
    is raised and no edit is committed.
    """
    content = current_content
    for index, block in enumerate(blocks, start=1):
        search = block.search
        count = content.count(search)
        if count == 0 and search.endswith("\n\n"):
            # Bounded delimiter-boundary recovery: models sometimes emit one
            # extra blank line immediately before the SEARCH/REPLACE divider.
            # Recover only when removing exactly one trailing newline yields a
            # unique literal match. No other whitespace/fuzzy matching occurs.
            candidate = search[:-1]
            candidate_count = content.count(candidate)
            if candidate_count == 1:
                search = candidate
                count = 1
        if count == 0:
            raise ExactPatchError(
                f"block {index}: SEARCH content not found in current file "
                f"(count=0); search={block.search[:80]!r}"
            )
        if count > 1:
            raise ExactPatchError(
                f"block {index}: SEARCH content is ambiguous, matched {count} "
                f"times; search={block.search[:80]!r}"
            )
        content = content.replace(search, block.replace, 1)
    return content
