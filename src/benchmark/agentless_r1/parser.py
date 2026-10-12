"""Deterministic Agentless file-list output parser (frozen).

Implements the official parse pipeline:

1. ``content.strip().split('\\n')`` (official ``_parse_model_return_lines``);
2. keep only lines that exactly equal a full repo-relative path in the frozen
   file set (official ``correct_file_paths``); preserve first-appearance order;
3. slice to ``top_n`` (official default 3);
4. prediction set = deduplicated set of the top-N corrected paths.

Empty / malformed / nonexistent-path / over-top-N behaviour is frozen and
classified deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmark.agentless_r1.prompt import TOP_N


@dataclass(frozen=True)
class ParseResult:
    classification: str  # "VALID" | "EMPTY" | "MALFORMED"
    corrected_ordered: tuple[str, ...]
    top_n_slice: tuple[str, ...]
    prediction_set: frozenset[str]
    dropped_line_count: int
    duplicate_count: int
    more_than_top_n: bool
    notes: tuple[str, ...] = field(default_factory=tuple)


def parse_file_list(
    content: str,
    file_set: set[str],
    *,
    top_n: int = TOP_N,
) -> ParseResult:
    if content is None or not content.strip():
        return ParseResult(
            classification="EMPTY",
            corrected_ordered=(),
            top_n_slice=(),
            prediction_set=frozenset(),
            dropped_line_count=0,
            duplicate_count=0,
            more_than_top_n=False,
            notes=("empty output",),
        )

    lines = content.strip().split("\n")
    dropped: list[str] = []
    corrected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in file_set:
            corrected.append(stripped)
        else:
            dropped.append(stripped)

    corrected_ordered = tuple(corrected)
    duplicate_count = len(corrected) - len(set(corrected))
    top_n_slice = tuple(corrected[:top_n])
    prediction_set = frozenset(corrected[:top_n]) if corrected[:top_n] else frozenset()
    more_than_top_n = len(corrected) > top_n

    if not corrected:
        return ParseResult(
            classification="MALFORMED",
            corrected_ordered=(),
            top_n_slice=(),
            prediction_set=frozenset(),
            dropped_line_count=len(dropped),
            duplicate_count=0,
            more_than_top_n=False,
            notes=(f"no line matched any file in the frozen structure ({len(dropped)} dropped)",),
        )

    return ParseResult(
        classification="VALID",
        corrected_ordered=corrected_ordered,
        top_n_slice=top_n_slice,
        prediction_set=prediction_set,
        dropped_line_count=len(dropped),
        duplicate_count=duplicate_count,
        more_than_top_n=more_than_top_n,
        notes=(),
    )
