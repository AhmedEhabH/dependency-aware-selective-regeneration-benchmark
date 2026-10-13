"""R4-C symlink materialization successor - focused unit tests (pure logic).

Mission M17_D7_R4C_SYMLINK_MATERIALIZATION (instrumentation/environment only).

Proves the R4-C successor semantics required by the frozen exact-tree-fidelity
contract:

  100644 -> regular file (unchanged)
  100755 -> executable regular file (unchanged)
  120000 -> real Linux symbolic link (new)
  all other modes (incl. 160000 gitlink) -> fail closed

No Docker required (pure logic + embedded script inspection).
"""
from __future__ import annotations

import pytest

from benchmark.wp2.env_r4.linux_tree_materialize import (
    MATERIALIZE_SCRIPT,
    MaterializeError,
    git_mode_to_unix,
    parse_tree_line,
    tree_identity,
)


def test_mode_120000_is_symlink_not_regular() -> None:
    # 1. mode 120000 is recognized as a symlink, not a regular blob.
    assert git_mode_to_unix("120000") == 0o777
    assert git_mode_to_unix("100644") == 0o644
    assert git_mode_to_unix("100755") == 0o755


def test_parse_tree_line_accepts_symlink() -> None:
    e = parse_tree_line("120000 47dc3e3d863cfb5727b87d785d09abf9743c0a72\tCLAUDE.md")
    assert e.mode == "120000"
    assert e.oid == "47dc3e3d863cfb5727b87d785d09abf9743c0a72"
    assert e.path == "CLAUDE.md"
    assert e.unix_mode == 0o777


def test_parse_tree_line_nested_relative_symlink_preserved() -> None:
    # 3. nested relative link path + oid preserved exactly (no normalization).
    e = parse_tree_line("120000 deadbeef\tCLAUDE.md")
    assert e.path == "CLAUDE.md"
    e2 = parse_tree_line("120000 deadbeef\tsaleor/graphql/CLAUDE.md")
    assert e2.path == "saleor/graphql/CLAUDE.md"


def test_regular_and_executable_modes_unchanged() -> None:
    # 6 + 7. existing 100644 / 100755 semantics unchanged.
    reg = parse_tree_line("100644 aaa\tsaleor/settings.py")
    exe = parse_tree_line("100755 bbb\tmanage.py")
    assert reg.unix_mode == 0o644
    assert exe.unix_mode == 0o755


def test_gitlink_160000_still_fails_closed() -> None:
    # 8. unsupported mode 160000 still fails closed.
    with pytest.raises(MaterializeError, match="non-blob"):
        parse_tree_line("160000 9fa8966173273be2db43c4431915327d45d7affb\tsub")
    with pytest.raises(MaterializeError):
        git_mode_to_unix("160000")


def test_materialize_script_creates_real_symlink_and_keeps_gitlinks_closed() -> None:
    # 2 + 5. script must create a symlink via `ln -s` (never copy/dereference),
    # and must keep non-120000/non-100644/non-100755 modes fail-closed.
    assert "120000)" in MATERIALIZE_SCRIPT
    assert "ln -s" in MATERIALIZE_SCRIPT
    assert "SYMLINK_FAIL" in MATERIALIZE_SCRIPT
    assert "SYMLINK_TARGET_FAIL" in MATERIALIZE_SCRIPT
    assert "UNEXPECTED_MODE" in MATERIALIZE_SCRIPT
    # symlinks are never chmod-ed / never written as regular blobs
    assert "120000) um=" not in MATERIALIZE_SCRIPT
    assert "\r" not in MATERIALIZE_SCRIPT


def test_tree_identity_includes_symlink_and_is_order_independent() -> None:
    # 9 + 10. deterministic identity including symlinks.
    a = parse_tree_line("100755 x\tmanage.py")
    b = parse_tree_line("120000 y\tCLAUDE.md")
    c = parse_tree_line("100644 z\tsaleor/settings.py")
    id1 = tree_identity([a, b, c])
    id2 = tree_identity([c, a, b])
    assert id1 == id2
    # symmetric identity is mode+path (OID is content, not identity — matches
    # the pre-existing provider contract; a symlink entry is distinct from a
    # regular blob at the same path).
    assert tree_identity([a, b, c]) != tree_identity([a, c])
    assert tree_identity([a, parse_tree_line("100644 w\tCLAUDE.md"), c]) != id1


def test_blobs_only_tree_identity_stable() -> None:
    # 6/7/10. a blobs-only tree identity is unaffected by the successor.
    entries = [
        parse_tree_line("100644 a\tREADME.md"),
        parse_tree_line("100755 b\tmanage.py"),
    ]
    assert tree_identity(entries) == tree_identity(list(reversed(entries)))
    assert all(e.unix_mode in (0o644, 0o755) for e in entries)
