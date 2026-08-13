"""PILOT-EXEC-01: hermetic repository snapshot contract (Gate 3).

The default suite constructs synthetic LOCAL git repositories and pins with
matching commits; it never touches developer-local ``_workspace/cache`` or the
network. Real pinned acquisition of django CMS/Saleor is the explicit Gate 8
step outside the default suite.

Covers:

- exact requested commit exported, no ``.git`` in the target;
- wrong/missing commit fails closed;
- missing repo cache (None or empty) fails closed without network;
- stable content hash, file count/size evidence, deterministic replacement;
- embedded-mode tree copy contract;
- hash/copy exclusions (.git, cache dirs).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"


def _load_snapshot_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "pilot_repo_snapshot_unit_under_test",
        str(SCRIPTS_DIR / "pilot_repo_snapshot.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


snapshot_mod = _load_snapshot_module()

requires_git = pytest.mark.skipif(
    shutil.which("git") is None, reason="git executable required for synthetic repos"
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _make_synthetic_repo(tmp_path: Path) -> tuple[Path, str]:
    """Create a git checkout at ``<cache>/djangocms`` with a committed tree.

    The cache layout mirrors the production contract (a git checkout must exist
    at ``repo_cache / repo_id``) so materialization resolves the pinned commit
    entirely from local objects -- no network.
    """
    checkout = tmp_path / "cache" / "djangocms"
    checkout.parent.mkdir(parents=True, exist_ok=True)
    checkout.mkdir()
    _git(checkout, "init", "-q")
    _git(checkout, "config", "user.email", "test@example.invalid")
    _git(checkout, "config", "user.name", "Pilot Test")
    (checkout / "src").mkdir()
    (checkout / "src" / "hello.py").write_text("def hello():\n    return 42\n", encoding="utf-8")
    (checkout / "README.md").write_text("# synthetic\n", encoding="utf-8")
    _git(checkout, "add", "-A")
    _git(checkout, "commit", "-q", "-m", "initial")
    return checkout, _git(checkout, "rev-parse", "HEAD")


def _pin(repo_id: str, commit_sha: str) -> Any:
    return snapshot_mod.RepositoryPin(
        repo_id=repo_id,
        commit_sha=commit_sha,
        mode="git",
        url="https://example.invalid/synthetic",
        embedded_source=None,
    )


@pytest.fixture
def synthetic_git(tmp_path: Path) -> tuple[Path, str]:
    return _make_synthetic_repo(tmp_path)


def _repo_cache(synthetic_git: tuple[Path, str]) -> Path:
    return synthetic_git[0].parent


class TestGitModeMaterialization:
    @requires_git
    def test_exact_requested_commit_exported(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        target = tmp_path / "export"
        evidence = snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=target
        )
        assert (target / "src" / "hello.py").is_file()
        assert (target / "README.md").is_file()
        assert evidence.requested_sha == sha
        assert evidence.resolved_head == sha
        assert evidence.file_count == 2

    @requires_git
    def test_no_git_directory_in_export(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        target = tmp_path / "export"
        snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=target
        )
        assert not (target / ".git").exists()

    @requires_git
    def test_stable_content_hash(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        first = snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=tmp_path / "export-1"
        )
        second = snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=tmp_path / "export-2"
        )
        assert first.content_hash == second.content_hash
        assert first.file_count == second.file_count == 2
        assert first.size_bytes == second.size_bytes > 0

    @requires_git
    def test_target_replacement_is_deterministic(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        target = tmp_path / "export"
        target.mkdir()
        (target / "stale.txt").write_text("stale\n", encoding="utf-8")
        evidence = snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=target
        )
        assert not (target / "stale.txt").exists()
        assert (target / "src" / "hello.py").is_file()
        assert evidence.file_count == 2

    @requires_git
    def test_wrong_commit_fails_closed(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, _sha = synthetic_git
        with pytest.raises(RuntimeError):
            snapshot_mod.materialize_repository(
                _pin("djangocms", "0" * 40), repo_cache=_repo_cache(synthetic_git), target_dir=tmp_path / "export"
            )

    @requires_git
    def test_missing_commit_fails_closed(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, _sha = synthetic_git
        with pytest.raises(RuntimeError):
            snapshot_mod.materialize_repository(
                _pin("djangocms", "f" * 40), repo_cache=_repo_cache(synthetic_git), target_dir=tmp_path / "export"
            )

    @requires_git
    def test_missing_repo_cache_fails_closed(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        with pytest.raises(RuntimeError):
            snapshot_mod.materialize_repository(
                _pin("djangocms", sha), repo_cache=None, target_dir=tmp_path / "export"
            )

    @requires_git
    def test_empty_repo_cache_fails_closed(
        self, tmp_path: Path, synthetic_git: tuple[Path, str]
    ) -> None:
        _repo, sha = synthetic_git
        empty_cache = tmp_path / "empty-cache"
        empty_cache.mkdir()
        with pytest.raises(RuntimeError):
            snapshot_mod.materialize_repository(
                _pin("djangocms", sha), repo_cache=empty_cache, target_dir=tmp_path / "export"
            )

    @requires_git
    def test_no_network_required(self, tmp_path: Path, synthetic_git: tuple[Path, str]) -> None:
        _repo, sha = synthetic_git
        target = tmp_path / "export"
        snapshot_mod.materialize_repository(
            _pin("djangocms", sha), repo_cache=_repo_cache(synthetic_git), target_dir=target
        )
        assert (target / "README.md").is_file()


class TestEmbeddedMode:
    def test_embedded_tree_copied_without_git_or_caches(self, tmp_path: Path) -> None:
        source = tmp_path / "embedded-src"
        (source / "nested").mkdir(parents=True)
        (source / "a.py").write_text("x = 1\n", encoding="utf-8")
        (source / "nested" / "b.py").write_text("y = 2\n", encoding="utf-8")
        (source / ".git").mkdir()
        (source / ".git" / "HEAD").write_text("ref: junk\n", encoding="utf-8")
        (source / "__pycache__").mkdir()
        (source / "__pycache__" / "a.cpython-311.pyc").write_bytes(b"junk")
        pin = snapshot_mod.RepositoryPin(
            repo_id="todo",
            commit_sha="embedded",
            mode="embedded",
            embedded_source=source,
        )
        target = tmp_path / "embedded-target"
        evidence = snapshot_mod.materialize_repository(pin, repo_cache=None, target_dir=target)
        assert (target / "a.py").is_file()
        assert (target / "nested" / "b.py").is_file()
        assert not (target / ".git").exists()
        assert not (target / "__pycache__").exists()
        assert evidence.mode == "embedded"
        assert evidence.file_count == 2


class TestTreeHashContract:
    def test_tree_content_hash_excludes_git_and_cache_dirs(self, tmp_path: Path) -> None:
        tree = tmp_path / "tree"
        (tree / ".git").mkdir(parents=True)
        (tree / ".git" / "HEAD").write_text("ref: junk\n", encoding="utf-8")
        (tree / "__pycache__").mkdir()
        (tree / "__pycache__" / "x.pyc").write_bytes(b"junk")
        (tree / "real.py").write_text("z = 3\n", encoding="utf-8")
        digest = snapshot_mod._tree_content_hash(tree)
        assert digest
        # Adding content inside excluded directories changes nothing.
        (tree / ".git" / "packed-refs").write_text("junk\n", encoding="utf-8")
        (tree / "__pycache__" / "y.pyc").write_bytes(b"junk")
        assert snapshot_mod._tree_content_hash(tree) == digest
        # Changing an eligible file changes the hash.
        (tree / "real.py").write_text("z = 4\n", encoding="utf-8")
        assert snapshot_mod._tree_content_hash(tree) != digest

    def test_default_pins_frozen_identity(self) -> None:
        pins = {p.repo_id: p for p in snapshot_mod.DEFAULT_PINS}
        assert set(pins) == {"todo", "djangocms", "saleor"}
        assert pins["todo"].mode == "embedded"
        assert pins["djangocms"].mode == "git"
        assert pins["saleor"].mode == "git"
