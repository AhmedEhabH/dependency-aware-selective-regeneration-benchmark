"""WP-2 Linux filesystem adapter - unit tests (ZERO API).

Verifies amendment D / Mission 07 §5-6: the adapter must detect historical
filenames that are invalid on Windows (e.g. cassette with ``?``), guarantee the
checkout used for tests lives on a Linux filesystem, and translate worktree
paths deterministically.
"""

from __future__ import annotations

from benchmark.wp2.linux_adapter import (
    WslDockerBackend,
    contains_windows_invalid_char,
    translate_worktree_path,
    validate_linux_filesystem_required,
)


def test_detects_question_mark_cassette() -> None:
    # The known Saleor historical filename that broke Windows worktree add.
    path = (
        "saleor/graphql/core/tests/cassettes/"
        "test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml"
    )
    assert contains_windows_invalid_char(path)


def test_clean_paths_pass() -> None:
    assert not contains_windows_invalid_char("saleor/product/tests/test_models.py")


def test_validate_returns_only_invalid_paths() -> None:
    bad = "saleor/graphql/core/tests/cassettes/test_get_oembed_data[http:/www.youtube.com/watch?v=x].yaml"
    clean = "saleor/order/tests/test_order.py"
    out = validate_linux_filesystem_required([clean, bad])
    assert out == [bad]


def test_translate_worktree_path_deterministic() -> None:
    w = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\_workspace\wp2_v2\worktrees\abc123_t"
    t = translate_worktree_path(w)
    assert t.startswith("/workspace/")
    assert "_workspace/wp2_v2/worktrees/abc123_t" in t


def test_translate_mount_point() -> None:
    t = translate_worktree_path(r"C:\data\saleor", mount_point="/mnt/c", container_root="/src")
    assert t.startswith("/mnt/c/data/saleor")


def test_wsl_docker_backend_never_points_to_desktop(monkeypatch) -> None:
    # The WSL-local engine path must invoke the docker CLI INSIDE the WSL distro
    # (``wsl -d Ubuntu-24.04 -- docker ...``), never the Windows Docker Desktop
    # client.
    import subprocess

    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    backend = WslDockerBackend()
    res = backend.run(["info", "--format", "{{.Root}}"])
    assert res.returncode == 0
    assert captured["cmd"][:4] == ["wsl", "-d", "Ubuntu-24.04", "--"]
    assert captured["cmd"][4:] == ["docker", "info", "--format", "{{.Root}}"]
