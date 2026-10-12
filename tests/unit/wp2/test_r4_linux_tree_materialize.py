"""R4-C Linux-tree materialization - unit tests (pure logic, no Docker).

Covers the pure decision logic and fail-closed behavior of
``benchmark.wp2.env_r4.linux_tree_materialize`` with a fake backend so the
suite runs anywhere (no Docker required).  The real Linux-native Docker path is
exercised separately in ``tests/integration/wp2``.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from benchmark.wp2.env_r4.linux_tree_materialize import (
    MATERIALIZE_SCRIPT,
    MaterializeError,
    Materializer,
    ensure_empty_volume,
    git_mode_to_unix,
    parse_tree_line,
    remove_volume,
    tree_identity,
    volume_exists,
)
from benchmark.wp2.linux_adapter import CommandResult

CASSETTE = (
    "saleor/graphql/core/tests/cassettes/"
    "test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml"
)


@dataclass
class FakeBackend:
    """Stub LinuxBackend returning scripted CommandResults."""

    responses: dict[str, CommandResult]
    calls: list[list[str]] = None  # type: ignore[assignment]

    def _script(self, cmd: list[str]) -> str:
        if "-lc" in cmd:
            encoded = cmd[cmd.index("-lc") + 1]
            # decode the base64-transported runner: "echo <b64> | base64 -d | bash"
            if " | base64 -d" in encoded:
                payload = encoded.split(" | base64 -d")[0].removeprefix("echo ")
                import base64

                return base64.b64decode(payload).decode("utf-8")
            return encoded
        return " ".join(cmd)

    def run(self, cmd: list[str], *, timeout_s: int = 900) -> CommandResult:
        if self.calls is None:
            self.calls = []
        self.calls.append(list(cmd))
        script = self._script(cmd)
        if script.startswith("#!") or "MATERIALIZED" in script:
            needle = "script"
        elif "rev-parse --verify" in script:
            needle = "rev-parse"
        else:
            needle = "ls-tree" if "ls-tree" in script else "script"
        if needle in self.responses:
            return self.responses[needle]
        joined = " ".join(cmd)
        if "volume" in joined:
            return self.responses.get("volume", _fail())
        if "image" in joined:
            return self.responses.get("image", _fail())
        return _fail(f"unexpected command: {joined} (fail closed)")


def _ok(stdout: str = "") -> CommandResult:
    return CommandResult(0, stdout, "")


def _fail(stdout: str = "", stderr: str = "boom") -> CommandResult:
    return CommandResult(1, stdout, stderr)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_git_mode_to_unix() -> None:
    assert git_mode_to_unix("100755") == 0o755
    assert git_mode_to_unix("100644") == 0o644
    with pytest.raises(MaterializeError):
        git_mode_to_unix("120000")  # symlink not in scope -> fail closed


def test_parse_tree_line() -> None:
    e = parse_tree_line("100644 12acdf2c3e72479b10130ed4abe431e609e62f7e\t.dockerignore")
    assert e.mode == "100644"
    assert e.oid == "12acdf2c3e72479b10130ed4abe431e609e62f7e"
    assert e.path == ".dockerignore"
    assert not e.ntfs_invalid


def test_parse_tree_line_ntfs_invalid_path() -> None:
    e = parse_tree_line(f"100644 abc\t{CASSETTE}")
    assert e.ntfs_invalid


def test_parse_tree_line_non_blob_fails_closed() -> None:
    with pytest.raises(MaterializeError, match="non-blob"):
        parse_tree_line("160000 9fa8966173273be2db43c4431915327d45d7affb\tsub")
    with pytest.raises(MaterializeError):
        parse_tree_line("")
    with pytest.raises(MaterializeError):
        parse_tree_line("100644 abc")


def test_tree_identity_deterministic() -> None:
    a = parse_tree_line("100755 x\tmanage.py")
    b = parse_tree_line(f"100644 blob y\t{CASSETTE}")
    id1 = tree_identity([a, b])
    id2 = tree_identity([b, a])  # order-independent
    assert id1 == id2
    c = parse_tree_line("100644 blob z\tother.py")
    assert tree_identity([a, b, c]) != id1


def test_materialize_script_has_no_crlf_and_fail_closed_markers() -> None:
    assert "\r" not in MATERIALIZE_SCRIPT
    for marker in (
        "MISSING_COMMIT",
        "DIRTY_DESTINATION",
        "LS_TREE_FAIL",
        "NON_BLOB",
        "UNEXPECTED_MODE",
        "BLOB_FAIL",
        "cat-file blob",
        "chmod",
    ):
        assert marker in MATERIALIZE_SCRIPT


# ---------------------------------------------------------------------------
# Materializer fail-closed logic with a fake backend
# ---------------------------------------------------------------------------


def _materializer(responses: dict[str, CommandResult]) -> tuple[Materializer, FakeBackend]:
    backend = FakeBackend(responses)
    m = Materializer(
        backend=backend,
        image="envcanon/test-image:latest",
        repo_linux_path="/opt/wp2_v2/saleor-cache",
        image_verified=True,
    )
    return m, backend


def test_resolve_commit_missing_fails_closed() -> None:
    m, _ = _materializer({"rev-parse": _fail(stderr="fatal: Needed a single revision")})
    with pytest.raises(MaterializeError, match="missing commit"):
        m.resolve_commit("deadbeef")


def test_resolve_commit_success() -> None:
    m, _ = _materializer({"rev-parse": _ok("24f9b244d6bc8c591c9707380917d9b6c6d35c35\n")})
    assert m.resolve_commit("24f9b244d6bc") == "24f9b244d6bc8c591c9707380917d9b6c6d35c35"


def test_tree_entries_rejects_non_blob_fails_closed() -> None:
    m, _ = _materializer(
        {
            "rev-parse": _ok("c0ffee\n"),
            "ls-tree": _ok("100644 a\tfile.py\n160000 b\tsub\n"),
        }
    )
    with pytest.raises(MaterializeError, match="non-blob"):
        m.tree_entries("c0ffee")


def test_tree_entries_empty_tree_fails_closed() -> None:
    m, _ = _materializer({"rev-parse": _ok("c0ffee\n"), "ls-tree": _ok("")})
    with pytest.raises(MaterializeError, match="empty tree"):
        m.tree_entries("c0ffee")


def test_materialize_fails_closed_on_script_error() -> None:
    m, _ = _materializer(
        {
            "rev-parse": _ok("c0ffee\n"),
            "script": _fail(stdout="BLOB_FAIL abc saleor/x.py\n"),
        }
    )
    with pytest.raises(MaterializeError, match="materialization failed"):
        m.materialize("c0ffee", "vol")


def test_materialize_missing_count_marker_fails_closed() -> None:
    m, _ = _materializer(
        {"rev-parse": _ok("c0ffee\n"), "script": _ok("unexpected output\n")}
    )
    with pytest.raises(MaterializeError, match="no count marker"):
        m.materialize("c0ffee", "vol")


def test_materialize_returns_count() -> None:
    m, _ = _materializer(
        {"rev-parse": _ok("c0ffee\n"), "script": _ok("MATERIALIZED 42\n")}
    )
    assert m.materialize("c0ffee", "vol") == 42


def test_image_not_present_fails_closed_never_pulls() -> None:
    backend = FakeBackend({"image": _fail(stderr="no such image")})
    m = Materializer(backend, "envcanon/not-present:latest", "/repo")
    with pytest.raises(MaterializeError, match="refusing to pull"):
        m.resolve_commit("c0ffee")


def test_verify_file_missing_fails_closed() -> None:
    m, _ = _materializer(
        {"rev-parse": _ok("c0ffee\n"), "script": _fail(stdout="MISSING\n")}
    )
    res = m.verify_file("c0ffee", "vol", CASSETTE, 0o644, "abc123")
    assert res["present"] is False
    assert res["error"]


def test_verify_file_content_match() -> None:
    m, _ = _materializer(
        {
            "rev-parse": _ok("c0ffee\n"),
            "script": _ok("MODE 644\nOID abc123\n"),
        }
    )
    res = m.verify_file("c0ffee", "vol", CASSETTE, 0o644, "abc123")
    assert res["present"] is True
    assert res["mode_match"] is True
    assert res["content_match"] is True


def test_verify_file_content_mismatch() -> None:
    m, _ = _materializer(
        {
            "rev-parse": _ok("c0ffee\n"),
            "script": _ok("MODE 644\nOID DIFFERENT\n"),
        }
    )
    res = m.verify_file("c0ffee", "vol", CASSETTE, 0o644, "abc123")
    assert res["content_match"] is False


# ---------------------------------------------------------------------------
# Volume lifecycle helpers (fake backend)
# ---------------------------------------------------------------------------


def test_ensure_empty_volume_creates() -> None:
    backend = FakeBackend({"volume": _ok("vol\n")})
    ensure_empty_volume(backend, "vol")
    assert volume_exists(backend, "vol")


def test_remove_volume_idempotent() -> None:
    backend = FakeBackend(
        {"volume": _fail(stdout="", stderr="Error: No such volume: vol")}
    )
    remove_volume(backend, "vol")  # must not raise
