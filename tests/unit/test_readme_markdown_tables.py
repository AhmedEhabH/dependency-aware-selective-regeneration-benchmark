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


_MMD_GLOB = list((ROOT / "docs" / "diagrams").glob("*.mmd"))
_MERMAID_FENCE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


class TestReadmeMermaidRendering:
    """Regression: Mermaid sources (source of truth) must render on GitHub.

    README embeds deterministic static SVG fallbacks (docs/assets) and keeps
    the editable Mermaid sources under docs/diagrams/*.mmd as the source of
    truth. Literal backslash-n (`\n`) inside unquoted node labels is the known
    cause of "Unable to render rich display". Node labels must be double-quoted
    and use the HTML line break `<br/>` instead.
    """

    def _mermaid_blocks(self) -> list[str]:
        if _MMD_GLOB:
            return [p.read_text(encoding="utf-8") for p in sorted(_MMD_GLOB)]
        text = README_PATH.read_text(encoding="utf-8")
        blocks = _MERMAID_FENCE.findall(text)
        assert blocks, "README.md must contain at least one mermaid block"
        return blocks

    def test_no_literal_backslash_n_in_node_labels(self) -> None:
        for block in self._mermaid_blocks():
            for line in block.splitlines():
                line = line.strip()
                if not line or "[" not in line or "--> " in line:
                    continue
                # A node definition line such as `A[B\nlabel]` uses a literal
                # backslash-n inside unquoted brackets; GitHub fails to render.
                assert "\\n" not in line, f"literal \\n in mermaid node: {line!r}"

    def test_multiline_labels_use_quoted_br(self) -> None:
        # Any label that needs a line break must use a quoted "<br/>" form:
        #   ID["text<br/>more"]  — never ID[text\nmore].
        for block in self._mermaid_blocks():
            for line in block.splitlines():
                stripped = line.strip()
                if "[" not in stripped or "--> " in stripped or not stripped.endswith("]"):
                    continue
                if "<br/>" in stripped:
                    # Every <br/> occurrence must be inside a double-quoted label.
                    assert '"' in stripped, f"<br/> used without quoted label: {stripped!r}"

    def test_blocks_are_flowchart_with_balanced_brackets(self) -> None:
        for block in self._mermaid_blocks():
            assert block.lstrip().startswith("flowchart"), "mermaid block must be flowchart"
            for line in block.splitlines():
                if "[" in line or "]" in line:
                    assert line.count("[") == line.count("]"), f"unbalanced brackets: {line!r}"


class TestReadmeSvgFallbacks:
    """Regression: README embeds static SVG fallbacks referenced from docs/assets."""

    def test_svg_fallbacks_exist_and_are_embedded(self) -> None:
        text = README_PATH.read_text(encoding="utf-8")
        for mmd in sorted((ROOT / "docs" / "diagrams").glob("*.mmd")):
            svg = ROOT / "docs" / "assets" / f"{mmd.stem}.svg"
            assert svg.is_file(), f"missing static SVG fallback {svg}"
            assert f"docs/assets/{mmd.stem}.svg" in text, (
                f"README must embed the static SVG fallback for {mmd.stem}"
            )
            assert svg.read_text(encoding="utf-8").lstrip().startswith("<svg"), (
                f"SVG fallback {svg.name} is not well-formed XML"
            )
