"""WP-2 environment canon source-fidelity amendment R1 — P2P/F2P tests.

Mission M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_DESIGN_AND_FREEZE.

Covers the required property tests:

P1  registry package remains registry package
P2  directory-source PyXB remains DIRECTORY and preserves vendored/pyxb
P3  directory-source authorizenet remains DIRECTORY
P4  equal name/version + different source bytes => different canonical identities
P5  exact historical extraction repeated twice => identical source-tree hash
P6  artifact provenance points to the exact historical source
P7  registry-only closures remain unchanged
P8  both statically exposed D7 units use the generic source-aware rule
P9  source-aware closure is deterministic

and the failure tests:

F1  flatten DIRECTORY to name/version => FAIL
F2  replace vendored PyXB with registry PyXB 1.2.5 => FAIL
F3  replace with PyXB-X => FAIL
F4  use current mutable checkout instead of target commit => FAIL
F5  missing source path => FAIL CLOSED
F6  tree-hash mismatch => FAIL CLOSED
F7  ambiguous source identity => FAIL CLOSED
F8  attempt network fallback => FAIL
F9  task-ID-specific special case => FAIL
F10 mutate frozen R3 artifacts => FAIL

Tests that require the historical Saleor checkout or the read-only store skip
cleanly when those local resources are absent (hermetic default suite).
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from benchmark.wp2 import source_fidelity_r1 as sf

SALEOR_REPO = (
    r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355"
    r"\project\dist\pilot-repo-cache\saleor"
)
STORE_LOCKS = Path(r"D:\wp2_env_store\artifacts\locks")

EXPOSED = {
    "saleor-rc-e6198146186d": "e6198146186d1c782bf46f6c9439fa05b1049b2f",
    "saleor-rc-19bb9b070965": "19bb9b0709654010d1b4e4e9049af119d3b28815",
}

FROZEN_CANON_WHEELS = {
    "pyxb-1.2.5-py3-none-any.whl": (
        r"D:\wp2_env_store\built_wheelhouse\canon_r4b\py312"
        r"\pyxb__1.2.5____py312\wheels\pyxb-1.2.5-py3-none-any.whl",
        "52a256ce138aa2a4031a86789ba8edbe5379eb4ca96391eb4c572092894092d9",
    ),
    "authorizenet-1.1.4-py3-none-any.whl": (
        r"D:\wp2_env_store\built_wheelhouse\canon_r4b\py312"
        r"\authorizenet__1.1.4____py312\wheels\authorizenet-1.1.4-py3-none-any.whl",
        "d5e8d38de4c7ac6c4e8d2cbe190fcbb5427995c9da760ba3eba60e0faaa94e36",
    ),
}

HISTORICAL_CONTENT_PY_SHA256 = (
    "2a4b80093dcddb99a5a5db201143b130d69a332b69bf7ee596e633f051aea7ff"
)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {args}: {proc.stderr}")
    return proc.stdout.strip()


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> tuple[Path, str]:
    """Hermetic git repo with two vendored directory packages.

    ``vendored/pyxb`` ships content.py using ``collections.abc.MutableSequence``
    (the historical-compatible expression); ``vendored/authorizenet`` ships a
    minimal SDK.  Returns (repo_dir, target_commit).
    """
    repo = tmp_path / "saleor"
    repo.mkdir()
    _git(repo, "-c", "init.defaultBranch=main", "init", "-q")
    _git(repo, "config", "user.name", "sf-test")
    _git(repo, "config", "user.email", "sf-test@example.invalid")
    for rel, text in {
        "vendored/pyxb/pyxb/__init__.py": "# vendored pyxb 1.2.5\n",
        "vendored/pyxb/pyxb/binding/content.py": (
            "from collections.abc import MutableSequence\n"
            "class _PluralBinding(MutableSequence):\n"
            "    pass\n"
        ),
        "vendored/authorizenet/authorizenet/__init__.py": "# vendored sdk 1.1.4\n",
        "pyproject.toml": '[tool.poetry.dependencies]\npython = "~3.12"\n',
    }.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "vendored packages")
    commit = _git(repo, "rev-parse", "HEAD")
    return repo, commit


LOCK_TEMPLATE = """\
[[package]]
name = "PyXB"
version = "1.2.5"
optional = false
python-versions = "*"
develop = true
[package.source]
type = "directory"
url = "vendored/pyxb"

[[package]]
name = "authorizenet"
version = "1.1.4"
optional = false
python-versions = "*"
develop = true
[package.source]
type = "directory"
url = "vendored/authorizenet"

[[package]]
name = "django"
version = "3.2.7"
optional = false
python-versions = ">=3.8"

[[package]]
name = "requests"
version = "2.31.0"
optional = false
python-versions = ">=3.7"
[package.dependencies]
lxml = "==4.*"
"""

REGISTRY_ONLY_LOCK = """\
[[package]]
name = "django"
version = "3.2.7"
optional = false
python-versions = ">=3.8"

[[package]]
name = "requests"
version = "2.31.0"
optional = false
python-versions = ">=3.7"
"""


def _real_repo_or_skip() -> Path:
    if not Path(SALEOR_REPO).is_dir():
        pytest.skip("historical Saleor checkout not present")
    return Path(SALEOR_REPO)


def _lock_text(task: str) -> str:
    path = STORE_LOCKS / f"{task}_poetry.toml"
    if not path.is_file():
        pytest.skip(f"store lock not present: {path}")
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# P2P
# --------------------------------------------------------------------------- #

def test_p1_registry_package_remains_registry_package() -> None:
    source_type, reference = sf.classify_poetry_source({"type": "registry", "url": "https://pypi.org/simple"})
    assert source_type == sf.SOURCE_TYPE_REGISTRY
    identity = sf.SourceIdentity(
        name="requests", version="2.31.0", source_type=sf.SOURCE_TYPE_REGISTRY,
        source_reference=None, target_commit="x",
    )
    assert identity.canonical_pin() == "requests==2.31.0@REGISTRY"
    assert sf.assert_offline_source() == []


def test_p2_directory_pyxb_remains_directory_and_preserves_vendored_pyxb() -> None:
    repo = _real_repo_or_skip()
    commit = EXPOSED["saleor-rc-e6198146186d"]
    identity = sf.build_source_identity(
        name="PyXB", version="1.2.5",
        source_type=sf.SOURCE_TYPE_DIRECTORY,
        source_reference="vendored/pyxb",
        target_commit=commit, repo_dir=str(repo),
    )
    assert identity.source_type == sf.SOURCE_TYPE_DIRECTORY
    assert identity.source_reference == "vendored/pyxb"
    assert identity.source_tree_sha256
    per_file = identity.to_dict()
    assert per_file["source_tree_sha256"]


def test_p2_synthetic_same_directory_semantics(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    identity = sf.build_source_identity(
        name="PyXB", version="1.2.5",
        source_type=sf.SOURCE_TYPE_DIRECTORY,
        source_reference="vendored/pyxb",
        target_commit=commit, repo_dir=str(repo),
    )
    assert identity.source_type == sf.SOURCE_TYPE_DIRECTORY
    assert identity.source_reference == "vendored/pyxb"
    assert "@DIRECTORY:vendored/pyxb#" in identity.canonical_pin()


def test_p3_directory_authorizenet_remains_directory() -> None:
    repo = _real_repo_or_skip()
    commit = EXPOSED["saleor-rc-e6198146186d"]
    identity = sf.build_source_identity(
        name="authorizenet", version="1.1.4",
        source_type=sf.SOURCE_TYPE_DIRECTORY,
        source_reference="vendored/authorizenet",
        target_commit=commit, repo_dir=str(repo),
    )
    assert identity.source_type == sf.SOURCE_TYPE_DIRECTORY
    assert identity.source_reference == "vendored/authorizenet"
    assert identity.source_tree_sha256


def test_p4_equal_name_version_different_source_bytes_different_identity(
    tmp_path: Path,
) -> None:
    # Two synthetic repos vendoring PyXB==1.2.5 with different bytes.
    def _make_repo(dir_: Path, content: str) -> tuple[Path, str]:
        repo = dir_ / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        _git(repo, "-c", "init.defaultBranch=main", "init", "-q")
        _git(repo, "config", "user.name", "sf-test")
        _git(repo, "config", "user.email", "sf-test@example.invalid")
        p = repo / "vendored/pyxb/pyxb/binding/content.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "v")
        return repo, _git(repo, "rev-parse", "HEAD")

    repo_a, commit_a = _make_repo(tmp_path / "a", "class A:\n    pass\n")
    repo_b, commit_b = _make_repo(tmp_path / "b", "class B:\n    pass\n")
    id_a = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit_a, str(repo_a),
    )
    id_b = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit_b, str(repo_b),
    )
    assert id_a.source_tree_sha256 != id_b.source_tree_sha256
    assert id_a.canonical_pin() != id_b.canonical_pin()
    assert id_a.identity_sha256() != id_b.identity_sha256()


def test_p5_repeated_extraction_identical_tree_hash(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    first = sf.extract_source_tree(str(repo), commit, "vendored/pyxb")
    second = sf.extract_source_tree(str(repo), commit, "vendored/pyxb")
    assert first["tree_sha256"] == second["tree_sha256"]
    assert first["per_file_hashes"] == second["per_file_hashes"]
    assert first["file_count"] == second["file_count"]


def test_p6_provenance_points_to_exact_historical_source(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    identity = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit, str(repo),
    )
    provenance = sf.artifact_provenance(
        identity,
        build_toolchain="setuptools-70.1.0+wheel-0.45.1 (offline)",
        build_inputs=["vendored/pyxb/pyxb/binding/content.py"],
        output_filename="pyxb-1.2.5-py3-none-any.whl",
        output_sha256="a" * 64,
        metadata_name="PyXB",
        metadata_version="1.2.5",
        python_tag="py3-none-any",
        build_log_sha256="b" * 64,
    )
    assert provenance["source_type"] == sf.SOURCE_TYPE_DIRECTORY
    assert provenance["vendored_source_path"] == "vendored/pyxb"
    assert provenance["source_tree_sha256"] == identity.source_tree_sha256
    assert provenance["target_commit"] == commit
    assert provenance["reproducibility_class"] == sf.REPRO_CLASS_SOURCE_IDENTITY_REPRODUCIBLE


def test_p7_registry_only_closure_unchanged() -> None:
    closure = sf.derive_source_aware_closure(
        REGISTRY_ONLY_LOCK, "deadbeef", python_version="3.12"
    )
    assert closure["n_fail_closed"] == 0
    legacy = {"django==3.2.7", "requests==2.31.0"}
    source_aware = {p.split("@")[0] for p in closure["pins"]}
    assert source_aware == legacy
    for pin in closure["pins"]:
        assert pin.endswith("@REGISTRY")


def test_p8_both_exposed_units_use_generic_rule() -> None:
    repo = _real_repo_or_skip()
    assert sf.assert_no_task_specific_branch() == []
    for task, commit in EXPOSED.items():
        closure = sf.derive_source_aware_closure(
            _lock_text(task), commit, str(repo), python_version="3.12"
        )
        pins = {p for p in closure["pins"] if "DIRECTORY" in p}
        assert any("pyxb==1.2.5@DIRECTORY:vendored/pyxb#" in p for p in pins)
        assert any("authorizenet==1.1.4@DIRECTORY:vendored/authorizenet#" in p for p in pins)
        assert closure["n_fail_closed"] == 0
        # generic rule: the same DIRECTORY tree hash covers both units
        for p in pins:
            assert "saleor-rc-" not in p


def test_p9_source_aware_closure_deterministic(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    a = sf.derive_source_aware_closure(LOCK_TEMPLATE, commit, str(repo), python_version="3.12")
    b = sf.derive_source_aware_closure(LOCK_TEMPLATE, commit, str(repo), python_version="3.12")
    assert a["closure_identity_sha256"] == b["closure_identity_sha256"]
    assert a["pins"] == b["pins"]
    assert a["records"] == b["records"]


# --------------------------------------------------------------------------- #
# F2P
# --------------------------------------------------------------------------- #

def test_f1_flatten_directory_to_name_version_fails(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    identity = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit, str(repo),
    )
    canonical = identity.canonical_pin()
    flattened = "pyxb==1.2.5"
    assert canonical != flattened
    assert sf.closure_identity_sha256([canonical]) != sf.closure_identity_sha256([flattened])


def test_f2_replace_vendored_pyxb_with_registry_pyxb_125_fails() -> None:
    repo = _real_repo_or_skip()
    commit = EXPOSED["saleor-rc-e6198146186d"]
    vendored = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit, str(repo),
    )
    registry = sf.SourceIdentity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_REGISTRY, None, target_commit=commit,
    )
    assert vendored.canonical_pin() != registry.canonical_pin()
    assert vendored.identity_sha256() != registry.identity_sha256()


def test_f3_replace_with_pyxb_x_fails() -> None:
    repo = _real_repo_or_skip()
    commit = EXPOSED["saleor-rc-e6198146186d"]
    vendored = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit, str(repo),
    )
    pyxb_x = sf.SourceIdentity(
        "pyxb-x", "1.2.6.2", sf.SOURCE_TYPE_REGISTRY, None, target_commit=commit,
    )
    # different distribution name: can never satisfy the PyXB==1.2.5 pin
    assert pyxb_x.canonical_pin() != vendored.canonical_pin()
    assert pyxb_x.name != vendored.name


def test_f4_mutable_checkout_instead_of_target_commit_fails(
    tmp_git_repo: tuple[Path, str],
) -> None:
    repo, commit = tmp_git_repo
    committed_hash = sf.extract_source_tree(str(repo), commit, "vendored/pyxb")["tree_sha256"]
    # mutate the working tree (committed bytes stay untouched)
    mutated = repo / "vendored/pyxb/pyxb/binding/content.py"
    mutated.write_text("# mutated\n", encoding="utf-8")
    worktree_hash = sf.canonical_tree_hash_from_working_dir(str(repo / "vendored/pyxb"))
    assert worktree_hash != committed_hash
    # extraction must still return the committed bytes (immune to mutation)
    again = sf.extract_source_tree(str(repo), commit, "vendored/pyxb")["tree_sha256"]
    assert again == committed_hash


def test_f5_missing_source_path_fails_closed(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    with pytest.raises(sf.SourcePathMissing):
        sf.extract_source_tree(str(repo), commit, "vendored/nonexistent")
    with pytest.raises(sf.SourcePathMissing):
        sf.build_source_identity(
            "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/nonexistent",
            commit, str(repo),
        )


def test_f6_tree_hash_mismatch_fails_closed(tmp_git_repo: tuple[Path, str]) -> None:
    repo, commit = tmp_git_repo
    identity = sf.build_source_identity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb",
        commit, str(repo),
    )
    wrong = "0" * 64
    with pytest.raises(sf.SourceTreeMismatch):
        sf.verify_source_tree(identity, wrong)


def test_f7_ambiguous_source_identity_fails_closed() -> None:
    # directory source without a url reference
    with pytest.raises(sf.AmbiguousSourceIdentity):
        sf.classify_poetry_source({"type": "directory"})
    # local-source identity without a tree hash
    identity = sf.SourceIdentity(
        "PyXB", "1.2.5", sf.SOURCE_TYPE_DIRECTORY, "vendored/pyxb", None, None,
    )
    with pytest.raises(sf.AmbiguousSourceIdentity):
        identity.canonical_pin()


def test_f8_network_fallback_fails() -> None:
    assert sf.assert_offline_source() == []


def test_f9_task_id_special_case_fails() -> None:
    assert sf.assert_no_task_specific_branch() == []


def test_f10_mutate_frozen_r3_artifacts_fails() -> None:
    # The implementation never writes to the store / frozen artifacts.
    assert sf.assert_no_store_mutation_calls() == []
    # Regression guard: frozen R3 canonical wheel hashes are unchanged.
    for _filename, (path, expected) in FROZEN_CANON_WHEELS.items():
        wheel = Path(path)
        if not wheel.is_file():
            pytest.skip(f"store wheel not present: {path}")
        actual = hashlib.sha256(wheel.read_bytes()).hexdigest()
        assert actual == expected