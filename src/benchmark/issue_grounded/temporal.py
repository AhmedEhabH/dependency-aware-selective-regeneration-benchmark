"""Issue-grounded intent headroom - strict temporal validity (T3).

PRIMARY TEMPORALLY CLEAN issue text requires:
    issue.created_at < target_commit_time
    AND issue.updated_at <= target_commit_time

If `updated_at` is later than the target commit, the currently retrieved
title/body may contain post-target edits and cannot be proven to equal the
pre-change issue text -> `TEMPORALLY_UNCERTAIN`, excluded from the PRIMARY
clean analysis and reported descriptively only.

Both timestamps are normalized to UTC for comparison (GitHub returns ISO8601
with +00:00/"Z"; the case manifest target_commit_time carries an explicit
offset, e.g. +03:00).
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

CLEAN = "TEMPORALLY_CLEAN"
UNCERTAIN = "TEMPORALLY_UNCERTAIN"
SYNTAX_ERROR = "TEMPORAL_SYNTAX_ERROR"


def _parse_iso(text: str) -> datetime | None:
    """Parse an ISO8601 timestamp to an aware UTC datetime (lenient)."""
    if not text:
        return None
    s = text.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            # GitHub sometimes returns e.g. '2023-08-22T17:04:23Z' only.
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def temporal_status(issue_created_at: str, issue_updated_at: str, target_commit_time: str) -> str:
    """Return CLEAN / UNCERTAIN / SYNTAX_ERROR for one candidate issue."""
    created = _parse_iso(issue_created_at)
    updated = _parse_iso(issue_updated_at)
    target = _parse_iso(target_commit_time)
    if created is None or updated is None or target is None:
        return SYNTAX_ERROR
    if created < target and updated <= target:
        return CLEAN
    return UNCERTAIN


def target_time_or_none(target_commit_time: Any) -> datetime | None:
    return _parse_iso(str(target_commit_time))
