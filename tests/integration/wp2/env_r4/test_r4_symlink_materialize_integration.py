"""R4-C symlink materialization successor - real bounded integration qualification.

Mission M17_D7_R4C_SYMLINK_MATERIALIZATION (instrumentation/environment only).

Qualifies the successor against the REAL Unit-6 and Unit-7 target commits (the
proven symlink cases) using local qualified images and ``--network=none``.
No dependency install, no target tests, no downloads, no pull/build, and no
behavioral calibration.

Checks:
  - materialization succeeds;
  - CLAUDE.md is a symlink, readlink == AGENTS.md (Unit 6 + Unit 7);
  - saleor/graphql/CLAUDE.md is a symlink, readlink == ../AGENTS.md (Unit 6);
  - regular/executable modes preserved;
  - all expected entries present (no unexpected Git-tree entry dropped);
  - repeated materialization deterministic (tree identity stable).
"""
from __future__ import annotations

import uuid

import pytest

from benchmark.wp2.env_r4.linux_tree_materialize import (
    ensure_empty_volume,
    remove_volume,
)
from benchmark.wp2.env_r4.linux_tree_wiring import LinuxTreeWiring, R4MaterializationSource
from benchmark.wp2.linux_adapter import WslDockerBackend

MATERIALIZE_IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"
WSL_REPO = "/opt/wp2_v2/saleor-cache"
DISTRO = "Ubuntu-24.04"

# Unit-6 (vu-13c1de1de71e) and Unit-7 (vu-b78ebcf3e530) target commits.
UNIT6_COMMIT = "e0f2933d58b973ae61ca26b22a89da026aaaa7ad"
UNIT7_COMMITS = [
    "3bf31ab2fefca154d841803c9fc71057938ce5f9",
    "95dbffbc523a5a8865ead2a2649913491ac8e89c",
    "b356a525ba2ab918b85b6b617ac4df499e70e247",
    "ce3b63edecef7c942ac88888a4bc77149086bbd3",
    "ffe3a3ece0fb29cfbb7c02a032c86da31d17e8b3",
]


def _ready() -> tuple[bool, str]:
    try:
        backend = WslDockerBackend(distro=DISTRO)
        r = backend.run(["version", "--format", "{{.Server.Version}}"], timeout_s=60)
        if r.returncode != 0:
            return False, "docker engine unavailable"
        r = backend.run(["image", "inspect", MATERIALIZE_IMAGE], timeout_s=60)
        if r.returncode != 0:
            return False, f"local image {MATERIALIZE_IMAGE} not present"
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{WSL_REPO}:/src:ro",
                "--entrypoint", "bash", MATERIALIZE_IMAGE,
                "-lc", f"git -C /src rev-parse --verify '{UNIT6_COMMIT}'",
            ],
            timeout_s=120,
        )
        if r.returncode != 0:
            return False, f"target commit not reachable from {WSL_REPO}"
        return True, ""
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)


READY, READY_REASON = _ready()


def _wiring() -> LinuxTreeWiring:
    return LinuxTreeWiring(
        WslDockerBackend(distro=DISTRO),
        R4MaterializationSource(
            image=MATERIALIZE_IMAGE,
            repo_linux_path=WSL_REPO,
            image_verified=True,
        ),
    )


def _fresh_volume() -> str:
    name = f"r4c_symlink_{uuid.uuid4().hex[:10]}"
    ensure_empty_volume(WslDockerBackend(distro=DISTRO), name)
    return name


def _git_blob_text(commit: str, path: str) -> str:
    """Authoritative symlink target = exact Git blob bytes (object authority)."""
    import subprocess

    r = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "git", "-C", WSL_REPO, "cat-file", "-p", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, f"git blob read failed {commit}:{path}: {r.stderr}"
    return r.stdout


@pytest.mark.skipif(not READY, reason=READY_REASON if READY else "substrate not ready")
class TestUnit6SymlinkQualification:
    def test_materialize_unit6_symlinks(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        m = _wiring().materializer
        vol = _fresh_volume()
        try:
            count = m.materialize(UNIT6_COMMIT, vol)
            assert count > 0
            # Top-level symlink: target == exact Git blob.
            expected_top = _git_blob_text(UNIT6_COMMIT, "CLAUDE.md")
            r1 = m.verify_symlink(UNIT6_COMMIT, vol, "CLAUDE.md", expected_top)
            assert r1["is_symlink"] is True, r1
            assert r1["target_match"] is True, r1
            # Nested relative symlink: target == exact Git blob (object
            # authority; not assumed from descriptive text).
            expected_nested = _git_blob_text(UNIT6_COMMIT, "saleor/graphql/CLAUDE.md")
            r2 = m.verify_symlink(UNIT6_COMMIT, vol, "saleor/graphql/CLAUDE.md", expected_nested)
            assert r2["is_symlink"] is True, r2
            assert r2["target_match"] is True, r2
            # regular/executable modes preserved.
            r3 = m.verify_file(UNIT6_COMMIT, vol, "manage.py", 0o755, "0000", resolve=False)
            assert r3["present"] is True and r3["mode_match"] is True, r3
        finally:
            remove_volume(backend, vol)

    def test_materialize_unit6_no_entries_dropped(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        m = _wiring().materializer
        vol = _fresh_volume()
        try:
            count = m.materialize(UNIT6_COMMIT, vol)
            entries = m.tree_entries(UNIT6_COMMIT)
            assert count == len(entries), f"{count} materialized vs {len(entries)} tree entries"
        finally:
            remove_volume(backend, vol)

    def test_materialize_unit6_deterministic_identity(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        m = _wiring().materializer
        vol1 = _fresh_volume()
        vol2 = _fresh_volume()
        try:
            m.materialize(UNIT6_COMMIT, vol1)
            m.materialize(UNIT6_COMMIT, vol2)
            id1 = m.materialized_tree_identity(UNIT6_COMMIT, vol1)
            id2 = m.materialized_tree_identity(UNIT6_COMMIT, vol2)
            assert id1 == id2
        finally:
            remove_volume(backend, vol1)
            remove_volume(backend, vol2)


@pytest.mark.skipif(not READY, reason=READY_REASON if READY else "substrate not ready")
class TestUnit7SymlinkQualification:
    def test_materialize_unit7_member_commits(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        m = _wiring().materializer
        for commit in UNIT7_COMMITS:
            vol = _fresh_volume()
            try:
                count = m.materialize(commit, vol)
                assert count > 0
                expected = _git_blob_text(commit, "CLAUDE.md")
                r = m.verify_symlink(commit, vol, "CLAUDE.md", expected)
                assert r["is_symlink"] is True, f"{commit}: {r}"
                assert r["target_match"] is True, f"{commit}: {r}"
                entries = m.tree_entries(commit)
                assert count == len(entries), f"{commit}: {count} vs {len(entries)}"
            finally:
                remove_volume(backend, vol)
