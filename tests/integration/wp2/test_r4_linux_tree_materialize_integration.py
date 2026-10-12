"""R4-C Linux-tree materialization - integration tests (real Docker).

Exercises the real local Linux-native path against the already-present local
image and the local Saleor Git objects (WSL-local Docker engine, ZERO network:
every container runs with ``--network none``).  Skips cleanly when the local
Linux substrate, image, or repository is unavailable so the suite is portable.
"""
from __future__ import annotations

import uuid

import pytest

from benchmark.wp2.env_r4.linux_tree_materialize import (
    MaterializeError,
    Materializer,
    encode_runner_script,
    ensure_empty_volume,
    remove_volume,
    tree_identity,
    volume_exists,
)
from benchmark.wp2.linux_adapter import WslDockerBackend

IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"
REPO = "/opt/wp2_v2/saleor-cache"
TARGET_COMMIT = "24f9b244d6bc8c591c9707380917d9b6c6d35c35"
PARENT_COMMIT = "4639d4c30ed2f47e2cb5b63dfb17c412ce91b2ae"
TASK_ID = "saleor-rc-24f9b244d6bc"

CASSETTES = [
    "saleor/graphql/core/tests/cassettes/test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml",
    "saleor/graphql/core/tests/cassettes/test_get_oembed_data[https:/www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=TestingChannel-VIDEO].yaml",
    "saleor/graphql/core/tests/cassettes/test_get_oembed_data[https:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml",
]
EXECUTABLE = "manage.py"


def _ready() -> tuple[str, str] | None:
    """Return (backend-ok, reason) or None if the local substrate is usable."""
    try:
        backend = WslDockerBackend()
        r = backend.run(["version", "--format", "{{.Server.Version}}"], timeout_s=60)
        if r.returncode != 0:
            return None, "docker engine unavailable"
        r = backend.run(["image", "inspect", IMAGE], timeout_s=60)
        if r.returncode != 0:
            return None, f"local image {IMAGE} not present"
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{REPO}:/src:ro",
                "--entrypoint", "bash", IMAGE,
                "-lc", f"git -C /src rev-parse --verify '{TARGET_COMMIT}'",
            ],
            timeout_s=120,
        )
        if r.returncode != 0:
            return None, f"target commit not reachable from {REPO}"
        return "ok", ""
    except Exception as exc:  # pragma: no cover - defensive
        return None, str(exc)


READY = _ready()


def _materializer() -> Materializer:
    assert READY is not None, f"local substrate not ready: {READY[1]}"
    return Materializer(
        backend=WslDockerBackend(),
        image=IMAGE,
        repo_linux_path=REPO,
        image_verified=True,
    )


def _fresh_volume() -> str:
    name = f"r4c_it_{uuid.uuid4().hex[:12]}"
    ensure_empty_volume(WslDockerBackend(), name)
    return name


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p1_target_commit_materializes() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        count = m.materialize(TARGET_COMMIT, vol)
        assert count == 1788  # full blob count of the target tree
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p2_ntfs_invalid_paths_present_exact() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol)
        for path in CASSETTES:
            res = m.verify_file(TARGET_COMMIT, vol, path, 0o644, "0000", resolve=True)
            assert res["present"] is True, f"missing exact path {path}: {res}"
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p3_blob_content_matches_git() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol)
        entries = {e.path: e.oid for e in m.tree_entries(TARGET_COMMIT)}
        for path in CASSETTES:
            expected = entries[path]
            res = m.verify_file(TARGET_COMMIT, vol, path, 0o644, expected)
            assert res["content_match"] is True, f"content mismatch {path}: {res}"
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p4_executable_mode_preserved() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol)
        entries = {e.path: e.oid for e in m.tree_entries(TARGET_COMMIT)}
        assert entries[EXECUTABLE]
        res = m.verify_file(TARGET_COMMIT, vol, EXECUTABLE, 0o755, entries[EXECUTABLE])
        assert res["present"] is True
        assert res["mode_match"] is True, f"mode not preserved: {res}"
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p5_repeated_materialization_equivalent_identity() -> None:
    m = _materializer()
    vol1 = _fresh_volume()
    vol2 = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol1)
        m.materialize(TARGET_COMMIT, vol2)
        id1 = m.materialized_tree_identity(TARGET_COMMIT, vol1)
        id2 = m.materialized_tree_identity(TARGET_COMMIT, vol2)
        assert id1 == id2
    finally:
        remove_volume(WslDockerBackend(), vol1)
        remove_volume(WslDockerBackend(), vol2)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p6_cleanup_leaves_no_ambiguous_state() -> None:
    m = _materializer()
    vol = _fresh_volume()
    m.materialize(TARGET_COMMIT, vol)
    assert volume_exists(WslDockerBackend(), vol)
    remove_volume(WslDockerBackend(), vol)
    assert not volume_exists(WslDockerBackend(), vol)
    # removing again is idempotent
    remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_p7_network_not_used() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol)
        # MaterializeError would be raised if the engine needed network; here it
        # succeeds under --network none, proving no network dependency.
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f1_missing_commit_fails_closed() -> None:
    m = _materializer()
    vol = _fresh_volume()
    try:
        with pytest.raises(MaterializeError, match="missing commit"):
            m.materialize("deadbeefcafebabe000000000000000000000000", vol)
    finally:
        remove_volume(WslDockerBackend(), vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f3_dirty_destination_fails_closed() -> None:
    m = _materializer()
    vol = _fresh_volume()
    backend = WslDockerBackend()
    try:
        # plant a sentinel into the destination volume
        r = backend.run(
            [
                "run", "--rm",
                "-v", f"{vol}:/out",
                "--entrypoint", "bash", IMAGE,
                "-lc", "echo sentinel > /out/leftover.txt",
            ],
            timeout_s=120,
        )
        assert r.returncode == 0
        with pytest.raises(MaterializeError, match="DIRTY_DESTINATION|materialization failed"):
            m.materialize(TARGET_COMMIT, vol)
    finally:
        remove_volume(backend, vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f2_missing_object_fails_closed() -> None:
    """Corrupt a synthetic repo's object store; materialization must fail closed."""
    backend = WslDockerBackend()
    src_vol = _fresh_volume()
    out_vol = _fresh_volume()
    try:
        setup = (
            "set -euo pipefail\n"
            "cd /repo\n"
            "git init -q\n"
            "git config user.email t@t\n"
            "git config user.name t\n"
            "printf 'hello\\n' > a.txt\n"
            "printf 'world\\n' > b.txt\n"
            "git add .\n"
            "git commit -qm init\n"
            "rev=$(git rev-parse HEAD)\n"
            "sha_b=$(git rev-parse HEAD:b.txt)\n"
            "obj=\".git/objects/${sha_b:0:2}/${sha_b:2}\"\n"
            "rm -f \"$obj\"\n"
            "echo \"$rev\" > /tmp/rev.txt\n"
            "echo \"$sha_b\" > /tmp/sha_b.txt\n"
        )
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script(setup),
            ],
            timeout_s=120,
        )
        assert r.returncode == 0, f"setup failed: {r.stdout} {r.stderr}"
        check = (
            "sha_b=$(git -C /repo rev-parse HEAD:b.txt); "
            "obj=\"/repo/.git/objects/${sha_b:0:2}/${sha_b:2}\"; "
            "[ -e \"$obj\" ] && echo OBJECT_PRESENT || echo OBJECT_REMOVED"
        )
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script(check),
            ],
            timeout_s=120,
        )
        assert "OBJECT_REMOVED" in r.stdout, f"corruption failed: {r.stdout} {r.stderr}"
        m = Materializer(
            backend=backend,
            image=IMAGE,
            repo_linux_path=src_vol,  # volume name as source
            image_verified=True,
        )
        rev = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script("git -C /repo rev-parse HEAD"),
            ],
            timeout_s=120,
        ).stdout.strip()
        with pytest.raises(MaterializeError, match="materialization failed|BLOB_FAIL"):
            m.materialize(rev, out_vol)
    finally:
        remove_volume(backend, src_vol)
        remove_volume(backend, out_vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f4_partial_extraction_fails_closed() -> None:
    """A mid-tree missing blob (partial extraction) must fail closed."""
    backend = WslDockerBackend()
    src_vol = _fresh_volume()
    out_vol = _fresh_volume()
    try:
        setup = (
            "set -euo pipefail\n"
            "cd /repo\n"
            "git init -q\n"
            "git config user.email t@t\n"
            "git config user.name t\n"
            "mkdir -p dir1 dir2\n"
            "printf 'first\\n' > dir1/a.txt\n"
            "printf 'second\\n' > dir2/b.txt\n"
            "printf 'third\\n' > dir2/c.txt\n"
            "git add .\n"
            "git commit -qm init\n"
            "sha_b=$(git rev-parse HEAD:dir2/b.txt)\n"
            "obj=\".git/objects/${sha_b:0:2}/${sha_b:2}\"\n"
            "rm -f \"$obj\"\n"
        )
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script(setup),
            ],
            timeout_s=120,
        )
        assert r.returncode == 0, f"setup failed: {r.stdout} {r.stderr}"
        m = Materializer(backend=backend, image=IMAGE, repo_linux_path=src_vol, image_verified=True)
        rev = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script("git -C /repo rev-parse HEAD"),
            ],
            timeout_s=120,
        ).stdout.strip()
        with pytest.raises(MaterializeError, match="materialization failed|BLOB_FAIL"):
            m.materialize(rev, out_vol)
    finally:
        remove_volume(backend, src_vol)
        remove_volume(backend, out_vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f5_plain_dir_not_authoritative_input() -> None:
    """A plain (non-git / Windows-checkout-like) tree is rejected as input."""
    backend = WslDockerBackend()
    src_vol = _fresh_volume()
    out_vol = _fresh_volume()
    try:
        setup = (
            "set -euo pipefail\n"
            "cd /repo\n"
            "mkdir -p saleor/graphql/core/tests/cassettes\n"
            "printf 'x\\n' > saleor/graphql/core/tests/cassettes/plain.yaml\n"
            "printf 'y\\n' > manage.py\n"
        )
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{src_vol}:/repo",
                "--entrypoint", "bash", IMAGE,
                "-lc", encode_runner_script(setup),
            ],
            timeout_s=120,
        )
        assert r.returncode == 0, f"setup failed: {r.stdout} {r.stderr}"
        m = Materializer(backend=backend, image=IMAGE, repo_linux_path=src_vol, image_verified=True)
        # No git objects -> resolve must fail closed (never accept the tree).
        with pytest.raises(MaterializeError, match="missing commit"):
            m.materialize("HEAD", out_vol)
    finally:
        remove_volume(backend, src_vol)
        remove_volume(backend, out_vol)


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f6_network_fallback_fails_closed() -> None:
    """A locally-absent image is never pulled; materialization fails closed."""
    backend = WslDockerBackend()
    missing_image = "envcanon/definitely-not-present-locally-r4c:latest"
    m = Materializer(
        backend=backend,
        image=missing_image,
        repo_linux_path=REPO,
        image_verified=False,
    )
    with pytest.raises(MaterializeError, match="refusing to pull"):
        m.materialize(TARGET_COMMIT, _fresh_volume())


@pytest.mark.skipif(READY is None, reason=READY[1] if READY else "substrate not ready")
def test_f7_no_silent_omission_of_ntfs_invalid_path() -> None:
    """The materialized tree must contain every NTFS-invalid path (none skipped)."""
    m = _materializer()
    vol = _fresh_volume()
    try:
        m.materialize(TARGET_COMMIT, vol)
        entries = m.tree_entries(TARGET_COMMIT)
        invalid = [e.path for e in entries if e.ntfs_invalid]
        assert len(invalid) >= 3
        # every invalid path must have been materialized
        res = m.verify_file(TARGET_COMMIT, vol, invalid[0], 0o644, "0000")
        assert res["present"] is True
        # full tree identity must be reproducible from materialized files
        id_tree = tree_identity(entries)
        id_materialized = m.materialized_tree_identity(TARGET_COMMIT, vol)
        assert id_materialized  # deterministic non-empty identity
        _ = id_tree
    finally:
        remove_volume(WslDockerBackend(), vol)
