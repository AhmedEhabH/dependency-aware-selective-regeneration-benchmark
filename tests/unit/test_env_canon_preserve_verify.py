"""Unit tests for the D7 R3 evidence-preservation verifier.

The F2P fail-closed negatives are exercised against temporary fixtures only;
the real source store is never modified or used for negatives.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.env_canon_preserve_verify as ecp


def _write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _make_small_manifest(store_root: Path, repo_root: Path, dest_rel: str) -> dict:
    src = _write_bytes(store_root / "src" / "artifact.bin", b"authoritative-payload-v1\n")
    evidence_dir = ecp.evidence_root(repo_root)
    _write_bytes(evidence_dir / dest_rel, b"authoritative-payload-v1\n")
    sha = ecp.sha256_file(src)
    manifest = {
        "mission": "test-fixture",
        "source_store": str(store_root),
        "dest_root": ecp.DEST_DIR_REL.as_posix(),
        "immutable_copy": True,
        "artifact_count": 1,
        "artifacts": [
            {
                "source_abs": str(src),
                "dest_rel": dest_rel,
                "sha256_source": sha,
                "sha256_dest": sha,
                "size_bytes": src.stat().st_size,
                "classification": ecp.HARNESS,
                "immutable_copy": True,
            }
        ],
    }
    (evidence_dir / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


@pytest.fixture
def fixture_dirs(tmp_path: Path) -> tuple[Path, Path]:
    store_root = tmp_path / "store"
    repo_root = tmp_path / "repo"
    store_root.mkdir()
    repo_root.mkdir()
    return store_root, repo_root


def test_copy_preservation_set_is_byte_for_byte(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    repo_root = tmp_path / "repo"
    for src_rel, _, _ in ecp.PRESERVATION_SET:
        _write_bytes(store_root / src_rel, src_rel.encode("utf-8") + b"\n")

    manifest = ecp.copy_preservation_set(store_root, repo_root)

    assert manifest["artifact_count"] == len(ecp.PRESERVATION_SET)
    for artifact in manifest["artifacts"]:
        dest = repo_root / ecp.DEST_DIR_REL / artifact["dest_rel"]
        assert dest.is_file()
        assert ecp.sha256_file(dest) == artifact["sha256_source"]
        assert ecp.sha256_file(dest) == artifact["sha256_dest"]
        assert artifact["immutable_copy"] is True


def test_f1_deliberate_hash_mismatch_detected(fixture_dirs: tuple[Path, Path]) -> None:
    store_root, repo_root = fixture_dirs
    manifest = _make_small_manifest(store_root, repo_root, "harness/probe.py")
    dest = repo_root / ecp.DEST_DIR_REL / "harness" / "probe.py"
    dest.write_bytes(b"tampered-payload-v2\n")

    passed, problems = ecp.verify_byte_match(manifest, repo_root)
    assert not passed
    assert any("byte mismatch" in problem for problem in problems)

    passed, problems = ecp.verify_p1_source_copy_hash(manifest, repo_root)
    assert not passed
    assert any("copy hash mismatch" in problem for problem in problems)


def test_f2_missing_required_artifact_fails(fixture_dirs: tuple[Path, Path]) -> None:
    store_root, repo_root = fixture_dirs
    manifest = _make_small_manifest(store_root, repo_root, "harness/probe.py")
    (repo_root / ecp.DEST_DIR_REL / "harness" / "probe.py").unlink()

    passed, problems = ecp.verify_required_present(manifest, repo_root)
    assert not passed
    assert any("required artifact missing" in problem for problem in problems)


def test_f3_unexpected_large_payload_rejected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    evidence_dir = repo_root / ecp.DEST_DIR_REL
    _write_bytes(evidence_dir / "payload.bin", b"x" * 2048)

    passed, problems = ecp.verify_size_cap(repo_root, max_bytes=1024)
    assert not passed
    assert any("exceeds cap" in problem for problem in problems)


def test_f4_wheel_docker_cache_paths_rejected() -> None:
    assert ecp.is_forbidden_path("built_wheelhouse/some-1.0-py3-none-any.whl")
    assert ecp.is_forbidden_path("docker/layer.tar")
    assert ecp.is_forbidden_path("harness/__pycache__/probe.cpython-313.pyc")
    assert ecp.is_forbidden_path("cache/npm")
    assert ecp.is_forbidden_path("harness/ok.py") is False

    manifest = {
        "artifacts": [
            {"dest_rel": "built_wheelhouse/bcrypt.whl", "classification": ecp.SUPPORTING},
            {"dest_rel": "harness/ok.py", "classification": ecp.HARNESS},
        ]
    }
    passed, problems = ecp.verify_no_forbidden_paths(manifest)
    assert not passed
    assert any("built_wheelhouse/bcrypt.whl" in problem for problem in problems)


def test_f5_source_dest_byte_mismatch_fails_closed(fixture_dirs: tuple[Path, Path]) -> None:
    store_root, repo_root = fixture_dirs
    manifest = _make_small_manifest(store_root, repo_root, "harness/probe.py")
    dest = repo_root / ecp.DEST_DIR_REL / "harness" / "probe.py"
    dest.write_bytes(b"different-content-than-source\n")

    passed, problems = ecp.verify_byte_match(manifest, repo_root)
    assert not passed
    passed, problems = ecp.verify_p1_source_copy_hash(manifest, repo_root)
    assert not passed


def test_p2_requires_full_harness_tree() -> None:
    harness = [{"dest_rel": rel, "classification": ecp.HARNESS} for rel in ecp.REQUIRED_HARNESS_FILES[:-1]]
    partial = {"artifacts": harness}
    passed, problems = ecp.verify_p2_harness_tree(partial)
    assert not passed
    assert any("not represented" in problem for problem in problems)
