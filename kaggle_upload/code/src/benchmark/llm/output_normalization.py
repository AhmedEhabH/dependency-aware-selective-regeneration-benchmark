"""Strict single-fence normalization contract for model output.

Contract (from the R7B-SMOKE-FINISH directive):

- whitespace-only payload => ``empty``;
- raw non-fenced payload => return the original text exactly (``raw``);
- accept exactly one complete outer fenced block (reason ``single_fence_stripped``);
- optional opening language token may be ``python``, ``py``, ``json``, or empty;
- preserve the body bytes except normalized outer line endings;
- any run of three or more backticks triggers fence validation;
- opening fence must be the first logical line;
- closing fence must be the final logical line;
- opening and closing fence lengths must match;
- reject same-line/inline fenced payload (``unbalanced_fence``);
- reject prose before/after the fence (``mixed_prose``);
- reject multiple blocks (``multiple_fences``);
- reject unsupported language (``unbalanced_fence``);
- reject unbalanced fences (``unbalanced_fence``);
- reject an empty block (``empty``);

Whitespace may be trimmed only for classification, never for the returned raw
payload: raw source bytes, leading blank lines, indentation, and final
newlines are preserved exactly.

The JSON parser applies normalization and then ``json.loads``; the parsed
payload must be an object. No heuristic extraction from the middle of
arbitrary prose is performed.
"""

from __future__ import annotations

import json
import re

__all__ = ["normalize_single_payload", "parse_single_json_object"]

_ALLOWED_LANGUAGE_TOKENS = frozenset({"python", "py", "json"})

_HAS_BACKTICK_RUN = re.compile(r"`{3,}")

# Structural fence-only line: whitespace, a backtick run of 3+, whitespace, an
# optional single language token, whitespace. Group 1 is the backtick run,
# group 2 the optional token.
_FENCE_MATCH = re.compile(r"^[ \t]*(`{3,})[ \t]*(\S*)[ \t]*$")


def _fence_parts(line: str) -> tuple[str, str] | None:
    """Return ``(backtick_run, language_token)`` for a fence-only line."""
    match = _FENCE_MATCH.match(line)
    if match is None:
        return None
    return match.group(1), match.group(2)


def normalize_single_payload(text: str) -> tuple[str | None, str]:
    """Normalize one model payload.

    Returns ``(normalized_body, reason)``. On rejection ``normalized_body`` is
    ``None`` and ``reason`` is one of ``empty``, ``mixed_prose``,
    ``multiple_fences``, or ``unbalanced_fence``.
    """
    if not text or not text.strip():
        return None, "empty"

    if not _HAS_BACKTICK_RUN.search(text):
        return text, "raw"

    lines = text.splitlines()
    markers = [i for i, line in enumerate(lines) if _fence_parts(line) is not None]

    if len(markers) > 2:
        return None, "multiple_fences"
    if len(markers) < 2:
        return None, "unbalanced_fence"
    if markers[0] != 0 or markers[1] != len(lines) - 1:
        return None, "mixed_prose"

    open_fence = _fence_parts(lines[0])
    close_fence = _fence_parts(lines[-1])
    if open_fence is None or close_fence is None:
        return None, "unbalanced_fence"
    open_run, open_token = open_fence
    close_run, _close_token = close_fence
    if open_token != "" and open_token not in _ALLOWED_LANGUAGE_TOKENS:
        return None, "unbalanced_fence"
    if open_run != close_run:
        return None, "unbalanced_fence"

    body = "\n".join(lines[1:-1])
    if not body.strip():
        return None, "empty"
    return body, "single_fence_stripped"


def parse_single_json_object(text: str) -> tuple[dict[str, object] | None, str]:
    """Parse a JSON object after strict single-fence normalization.

    Returns ``(data, reason)`` where ``reason`` is the normalization reason for
    accepted payloads or one of ``invalid_json`` / ``not_object`` on failure.
    """
    body, reason = normalize_single_payload(text)
    if body is None:
        return None, reason
    if reason not in ("raw", "single_fence_stripped"):
        return None, reason
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_json"
    if not isinstance(data, dict):
        return None, "not_object"
    return data, reason
