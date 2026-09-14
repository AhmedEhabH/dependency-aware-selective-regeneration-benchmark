"""README Markdown table structural regression check.

Ensures every Markdown table in README.md has a separator row whose column
count equals the header's column count. One extra separator cell silently
breaks table rendering on GitHub, so this must fail closed.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = ROOT / "README.md"

# A separator cell is optional-alignment-prefix/suffix dashes (e.g. "---",
# "---:", ":---", ":---:").
_SEPARATOR_CELL = re.compile(r":?-+:?")


def _split_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_separator_row(line: str) -> bool:
    cells = _split_cells(line)
    return bool(cells) and all(_SEPARATOR_CELL.fullmatch(cell) for cell in cells)


def find_malformed_tables(text: str) -> list[tuple[int, int, int]]:
    """Return (line_no, header_cols, separator_cols) for malformed tables."""
    lines = text.splitlines()
    malformed: list[tuple[int, int, int]] = []
    for idx, line in enumerate(lines):
        if not _is_separator_row(line):
            continue
        prev = idx - 1
        while prev >= 0 and not lines[prev].strip():
            prev -= 1
        if prev < 0:
            continue
        header_cells = _split_cells(lines[prev])
        separator_cells = _split_cells(line)
        if header_cells and len(header_cells) != len(separator_cells):
            malformed.append((idx + 1, len(header_cells), len(separator_cells)))
    return malformed


class TestReadmeMarkdownTableStructure:
    """Regression: every README table header and separator agree in columns."""

    def test_readme_exists(self) -> None:
        assert README_PATH.is_file(), "README.md must exist"

    def test_no_malformed_separator_rows(self) -> None:
        text = README_PATH.read_text(encoding="utf-8")
        malformed = find_malformed_tables(text)
        assert not malformed, (
            "README.md contains Markdown tables whose separator row has a "
            "different column count than the header "
            f"(line, header_cols, separator_cols): {malformed}"
        )

    def test_detector_is_not_a_noop(self) -> None:
        # Prove the detector actually catches a one-extra-cell separator.
        bad = "| A | B |\n|---|---|---:|\n"
        hits = find_malformed_tables(bad)
        assert hits and hits[0][1] == 2 and hits[0][2] == 3
        good = "| A | B |\n|---|---|\n"
        assert find_malformed_tables(good) == []
