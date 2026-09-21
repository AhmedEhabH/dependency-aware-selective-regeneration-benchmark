"""WP-1b D2 tool-budget semantics — RED→GREEN test.

Amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`: `search_text` backend scanning must
NOT consume `MAX_DISTINCT_FILES`; `read_file` keeps `MAX_DISTINCT_FILES = 30`.

Scenario that FAILS on the current code (before the D2 fix): a workspace with
>= 60 small .py files in nested folders. `search_text("needle", ".")` scans in
alphabetical order and reserves a distinct file per scanned file, so the first
search exhausts the whole 30-file budget before it reaches the late file that
contains the needle. Every later `read_file` then fails with the frozen
`Max distinct files limit (30) reached` error.

After the fix: the search finds the needle in the late file, and an early file
can still be read.
"""

from __future__ import annotations

from pathlib import Path

from benchmark.strategies.repository_tools import RepositoryTools


def _make_nested_python_workspace(root: Path, n: int = 60) -> None:
    """Create `n` small .py files spread over nested folders f0/..f5/."""
    for i in range(n):
        folder = root / f"d{i % 6}"
        folder.mkdir(parents=True, exist_ok=True)
        content = f"# file {i}\nvalue = {i}\n"
        if i == n - 1:
            content += "needle = True\n"
        (folder / f"f{i:03d}.py").write_text(content, encoding="utf-8")


def test_search_then_read_both_succeed_after_d2_fix(tmp_path: Path) -> None:
    _make_nested_python_workspace(tmp_path)
    tools = RepositoryTools(tmp_path)
    search = tools.search_text("needle", ".")
    assert search.ok, f"search_text must succeed (D2); error={search.error!r}"
    assert "needle = True" in search.output
    # The late file that contains the needle must be present in the results.
    assert "f059.py" in search.output

    # read_file must still work on an early file: search must not have consumed
    # the distinct-file budget.
    read = tools.read_file("d0/f000.py")
    assert read.ok, f"read_file must succeed after search (D2); error={read.error!r}"
    assert "value = 0" in read.output


def test_search_finds_late_file_after_d2_fix(tmp_path: Path) -> None:
    _make_nested_python_workspace(tmp_path)
    tools = RepositoryTools(tmp_path)
    search = tools.search_text("needle", ".")
    assert search.ok
    # The match line format is `path:line:content`.
    assert "f059.py:" in search.output
    assert "needle = True" in search.output


def test_read_only_still_bound_by_30_files(tmp_path: Path) -> None:
    """read_file alone keeps MAX_DISTINCT_FILES = 30 (unchanged knob)."""
    _make_nested_python_workspace(tmp_path, n=60)
    tools = RepositoryTools(tmp_path)
    ok_count = 0
    for i in range(60):
        result = tools.read_file(f"d{i % 6}/f{i:03d}.py")
        if result.ok:
            ok_count += 1
        else:
            assert "limit" in result.error.lower()
            break
    assert ok_count == 30
