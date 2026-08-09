"""Unit tests for RepositoryTools workspace exploration primitives."""

import os
from pathlib import Path

import pytest

from benchmark.strategies.repository_tools import RepositoryTools


def _make_file(root: Path, rel: str, content: str = "hello world") -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


class TestResolve:
    def test_valid_path(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path)
        resolved = tools._resolve(".")
        assert resolved is not None
        assert resolved == tmp_path.resolve()

    def test_invalid_absolute(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path)
        resolved = tools._resolve("C:\\Windows\\System32\\config")
        assert resolved is None

    def test_invalid_parent_escape(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path)
        resolved = tools._resolve("..")
        assert resolved is None

    def test_invalid_backslash(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path)
        resolved = tools._resolve("sub\\file.py")
        assert resolved is None

    def test_escaping_symlink_rejected(self, tmp_path: Path) -> None:
        import os
        if os.name == "nt":
            pytest.skip("symlink tests require elevated permissions on Windows")
        outside = tmp_path / "outside.txt"
        outside.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        tools = RepositoryTools(tmp_path)
        resolved = tools._resolve("link.txt")
        assert resolved is None


class TestListFiles:
    def test_list_root(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "a.py")
        _make_file(tmp_path, "sub/b.py")
        tools = RepositoryTools(tmp_path)
        result = tools.list_files(".")
        assert result.ok
        assert "a.py" in result.output
        assert "sub/b.py" in result.output

    def test_escaping_symlink_not_listed(self, tmp_path: Path) -> None:
        if os.name == "nt":
            pytest.skip("symlink tests require elevated permissions on Windows")
        outside = tmp_path / "outside.txt"
        outside.write_text("secret")
        (tmp_path / "sub").mkdir()
        link = tmp_path / "sub" / "link.txt"
        link.symlink_to(outside)
        _make_file(tmp_path, "sub/normal.py")
        tools = RepositoryTools(tmp_path)
        result = tools.list_files(".")
        assert result.ok
        assert "link.txt" not in result.output


class TestReadFile:
    def test_read_ok(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "src/main.py", "print('hello')")
        tools = RepositoryTools(tmp_path)
        result = tools.read_file("src/main.py")
        assert result.ok
        assert "print('hello')" in result.output

    def test_read_nonexistent(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path)
        result = tools.read_file("nonexistent.py")
        assert not result.ok

    def test_read_escaping_symlink(self, tmp_path: Path) -> None:
        if os.name == "nt":
            pytest.skip("symlink tests require elevated permissions on Windows")
        outside = tmp_path / "outside.txt"
        outside.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        tools = RepositoryTools(tmp_path)
        result = tools.read_file("link.txt")
        assert not result.ok

    def test_distinct_file_limit(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path, max_distinct_files=2)
        _make_file(tmp_path, "a.py")
        _make_file(tmp_path, "b.py")
        _make_file(tmp_path, "c.py")
        r1 = tools.read_file("a.py")
        assert r1.ok
        r2 = tools.read_file("b.py")
        assert r2.ok
        r3 = tools.read_file("c.py")
        assert not r3.ok
        assert "limit" in r3.error.lower()


class TestSearchText:
    def test_search_finds_text(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "src/a.py", "def foo(): pass")
        _make_file(tmp_path, "src/b.py", "def bar(): pass")
        tools = RepositoryTools(tmp_path)
        result = tools.search_text("foo", ".")
        assert result.ok
        assert "foo" in result.output

    def test_search_empty_query_rejected(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "a.py", "content")
        tools = RepositoryTools(tmp_path)
        result = tools.search_text("", ".")
        assert not result.ok

    def test_search_inspects_files(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "a.py", "apple")
        _make_file(tmp_path, "b.py", "banana")
        _make_file(tmp_path, "c.py", "cherry")
        tools = RepositoryTools(tmp_path)
        tools.search_text("a", ".")
        assert tools.distinct_file_count >= 1

    def test_search_respects_file_cap(self, tmp_path: Path) -> None:
        tools = RepositoryTools(tmp_path, max_distinct_files=2)
        for i in range(5):
            _make_file(tmp_path, f"f{i}.py", f"content{i}")
        result = tools.search_text("content", ".")
        assert result.ok or "limit" in result.error.lower()
        assert tools.distinct_file_count <= 2

    def test_search_escaping_symlink_skipped(self, tmp_path: Path) -> None:
        if os.name == "nt":
            pytest.skip("symlink tests require elevated permissions on Windows")
        outside = tmp_path / "outside.txt"
        outside.write_text("apple")
        (tmp_path / "sub").mkdir()
        link = tmp_path / "sub" / "link.txt"
        link.symlink_to(outside)
        _make_file(tmp_path, "sub/real.py", "apple here")
        tools = RepositoryTools(tmp_path)
        result = tools.search_text("apple", ".")
        assert result.ok
        assert "outside.txt" not in result.output
        assert "sub/real.py" in result.output
