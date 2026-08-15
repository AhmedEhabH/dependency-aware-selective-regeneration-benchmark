"""PILOT-EXEC-01: Pilot deployment bundle integration contract.

Proves the Pilot-specific deployment bundle builder produces a deterministic
Pilot deployment artifact from current canonical sources WITHOUT touching the
historical Scientific Smoke bundle (``kaggle_upload/``).

Covers the exact Pilot bundle contract from 02_PILOT_DEPLOYMENT_FREEZE.md:
output isolation, canonical-to-Pilot parity, frozen deployment identity,
no forbidden files, manifest verification, deterministic rebuilds, bundled
CLI import, and the bundled exact 48-cell ``--dry-run --profile pilot``.

Also covers the PILOT-EXEC-01 KAGGLE-FILENAME-TRANSPORT contract: the ZIP has
zero archive members outside ``^[A-Za-z0-9._/-]+$`` (unsafe upstream names are
transported under deterministic hashed blobs plus a hashed path map), the
canonical tree keeps its original filenames, and the exact notebook restore
round-trips blobs back to original paths before manifest/repository-hash
verification, failing closed on traversal/collision/missing-blob maps.
"""

from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib
import zipfile
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
HISTORICAL_SMOKE_UPLOAD = PROJECT_DIR / "kaggle_upload"
CANONICAL_NOTEBOOK = PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"
DIST_ARTIFACT = PROJECT_DIR / "dist" / "pilot-kaggle-upload.zip"

# Transport constants and the Kaggle-safety predicate are read from the module
# under test to prevent contract drift (charset regex + reserved ``__name__``
# rule).

# Every bundle built in this file materializes repositories through the shared
# pilot_repo_snapshot module; the hermetic fixture replaces git-checkout
# acquisition with a deterministic local stub (no developer-local cache, no
# network). Real pinned acquisition is the explicit Gate 8 step, not part of
# the default suite.
pytestmark = pytest.mark.usefixtures("hermetic_pilot_repo_materialize")

PILOT_SCENARIO_IDS = [
    "todo-loc-001",
    "todo-loc-002",
    "todo-mod-004",
    "todo-cross-007",
    "djangocms-mod-005",
    "djangocms-loc-002",
    "djangocms-mod-004",
    "djangocms-cross-007",
    "saleor-loc-001",
    "saleor-loc-002",
    "saleor-mod-004",
    "saleor-cross-007",
]

FROZEN_IDENTITY = {
    "task": "PILOT-EXEC-01",
    "protocol_version": "1.0",
    "model_name": "Qwen/Qwen2.5-Coder-14B-Instruct",
    "quantization": "bnb-nf4",
    "timeout_seconds": 600,
    "max_attempts": 3,
    "max_completion_tokens_per_call": 4096,
    "max_total_workflow_tokens": 0,
    "scenario_count": 12,
    "strategy_count": 2,
    "repetitions": 2,
    "expected_cells": 48,
}

FORBIDDEN_FRAGMENTS = (
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".egg-info",
    ".env",
    ".pyc",
    "db.sqlite3",
    ".sqlite3",
)


def _load_pilot_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_pilot_upload_bundle_under_test",
        str(SCRIPTS_DIR / "build_pilot_upload_bundle.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


pilot_builder = _load_pilot_builder()

TRANSPORT_MAP_NAME = pilot_builder.TRANSPORT_MAP_NAME
TRANSPORT_BLOB_PREFIX = pilot_builder.TRANSPORT_BLOB_PREFIX
TRANSPORT_FILES_PREFIX = f"{TRANSPORT_BLOB_PREFIX}/files/"


def _tree_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for rel in sorted(p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((directory / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _build(tmp_path: Path, created_utc: str, source_commit: str, label: str) -> tuple[Path, Path]:
    output_root = tmp_path / f"pilot-upload-{label}"
    archive = tmp_path / f"pilot-upload-{label}.zip"
    pilot_builder.build_pilot_bundle(
        output_root=output_root,
        archive_path=archive,
        source_commit=source_commit,
        source_tag="v0.9.3-pilot-exec-ready",
        created_utc=created_utc,
    )
    return output_root, archive


class TestPilotBundleOutputIsolation:
    def test_historical_smoke_bundle_untouched(self, tmp_path: Path) -> None:
        before = _tree_sha256(HISTORICAL_SMOKE_UPLOAD)
        _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "iso")
        after = _tree_sha256(HISTORICAL_SMOKE_UPLOAD)
        assert after == before, "Pilot bundle build mutated the historical Smoke bundle"

    def test_writes_only_to_supplied_pilot_output_root(self, tmp_path: Path) -> None:
        output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "only")
        assert output_root.is_dir()
        assert archive.is_file()
        assert (output_root / "code" / "seven_arm_benchmark.py").is_file()
        assert (output_root / "code" / "configs" / "pilot.yaml").is_file()
        assert (output_root / "data" / "scenarios").is_dir()
        assert not (output_root / "notebooks" / "seven_arm_benchmark.ipynb").exists()

    def test_pilot_bundle_omits_historical_smoke_notebook(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "nb")
        notebooks = output_root / "notebooks"
        if notebooks.is_dir():
            files = [p for p in notebooks.rglob("*") if p.is_file()]
            assert all("seven_arm_benchmark.ipynb" not in p.name for p in files)


class TestPilotBundleParity:
    def test_critical_code_config_data_parity(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "parity")
        pairs = [
            (PROJECT_DIR / "seven_arm_benchmark.py", output_root / "code" / "seven_arm_benchmark.py"),
            (PROJECT_DIR / "configs" / "pilot.yaml", output_root / "code" / "configs" / "pilot.yaml"),
            (
                PROJECT_DIR / "src" / "benchmark" / "repositories" / "loader.py",
                output_root / "code" / "src" / "benchmark" / "repositories" / "loader.py",
            ),
            (
                PROJECT_DIR / "src" / "benchmark" / "repositories" / "snapshot.py",
                output_root / "code" / "src" / "benchmark" / "repositories" / "snapshot.py",
            ),
            (
                PROJECT_DIR / "src" / "benchmark" / "selection" / "dependency_scope.py",
                output_root / "code" / "src" / "benchmark" / "selection" / "dependency_scope.py",
            ),
            (
                PROJECT_DIR / "benchmark_data" / "manifests" / "repository_versions.yaml",
                output_root / "data" / "manifests" / "repository_versions.yaml",
            ),
        ]
        for canonical, bundled in pairs:
            assert bundled.is_file(), f"missing bundled file: {bundled}"
            assert _normalized_bytes(canonical) == _normalized_bytes(bundled), (
                f"parity mismatch: {bundled}"
            )

    def test_three_repository_profiles_parity(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "profiles")
        for repo in ("todo", "djangocms", "saleor"):
            canonical = PROJECT_DIR / "benchmark_data" / "repository_profiles" / f"{repo}.yaml"
            bundled = output_root / "data" / "repository_profiles" / f"{repo}.yaml"
            assert bundled.is_file(), f"missing bundled profile: {bundled}"
            assert _normalized_bytes(canonical) == _normalized_bytes(bundled)

    def test_twelve_pilot_scenarios_parity(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "scenarios")
        for scenario_id in PILOT_SCENARIO_IDS:
            canonical = PROJECT_DIR / "benchmark_data" / "scenarios" / f"{scenario_id}.yaml"
            bundled = output_root / "data" / "scenarios" / f"{scenario_id}.yaml"
            assert bundled.is_file(), f"missing bundled scenario: {bundled}"
            assert _normalized_bytes(canonical) == _normalized_bytes(bundled)


class TestPilotBundleIdentityAndManifests:
    def test_identity_has_exact_frozen_contract(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "identity")
        identity_path = output_root / "pilot_deployment_identity.json"
        assert identity_path.is_file()
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        for key, value in FROZEN_IDENTITY.items():
            assert identity.get(key) == value, f"identity[{key!r}] != {value!r}"
        assert identity["source_commit"] == "a" * 40
        assert identity["source_tag"] == "v0.9.3-pilot-exec-ready"
        assert identity["created_utc"] == "2026-08-10T00:00:00+00:00"

    def test_identity_manifest_hashes_match_emitted_bytes(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "mhash")
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        for key, manifest_name in (
            ("code_manifest_sha256", "code_manifest.json"),
            ("data_manifest_sha256", "data_manifest.json"),
            ("notebook_manifest_sha256", "notebook_manifest.json"),
            ("repository_snapshot_manifest_sha256", "repository_snapshot_manifest.json"),
        ):
            manifest_bytes = (output_root / manifest_name).read_bytes()
            assert identity[key] == hashlib.sha256(manifest_bytes).hexdigest(), (
                f"identity {key} does not match emitted {manifest_name}"
            )

    def test_three_repository_snapshots_materialized(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "snapshots")
        manifest = json.loads(
            (output_root / "repository_snapshot_manifest.json").read_text(encoding="utf-8")
        )
        repos = manifest["repositories"]
        assert set(repos) == {"todo", "djangocms", "saleor"}
        for repo_id, entry in repos.items():
            assert entry["file_count"] > 0
            assert entry["content_hash"]
            staged_root = output_root / "data" / "repositories" / repo_id
            assert staged_root.is_dir(), f"bundled snapshot missing: {staged_root}"
            assert not (staged_root / ".git").exists()

    def test_pilot_runtime_lock_bundled_and_manifested(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "lock")
        lock_path = output_root / "code" / "requirements-pilot-kaggle.lock"
        assert lock_path.is_file()
        assert _normalized_bytes(lock_path) == _normalized_bytes(
            PROJECT_DIR / "requirements-pilot-kaggle.lock"
        )
        code_manifest = json.loads(
            (output_root / "code_manifest.json").read_text(encoding="utf-8")
        )
        assert "requirements-pilot-kaggle.lock" in code_manifest

    def test_repo_env_provisioning_helper_bundled_byte_equal_and_hashed(
        self, tmp_path: Path
    ) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "envs")
        bundled = output_root / "code" / "scripts" / "pilot_kaggle_repo_envs.py"
        canonical = SCRIPTS_DIR / "pilot_kaggle_repo_envs.py"
        assert bundled.is_file()
        assert _normalized_bytes(bundled) == _normalized_bytes(canonical)
        code_manifest = json.loads(
            (output_root / "code_manifest.json").read_text(encoding="utf-8")
        )
        rel = "scripts/pilot_kaggle_repo_envs.py"
        assert rel in code_manifest
        entry_hash = code_manifest[rel]
        assert isinstance(entry_hash, str)
        assert entry_hash == hashlib.sha256(_normalized_bytes(bundled)).hexdigest()

    def test_no_forbidden_files_in_bundle(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "forbid")
        rels = [p.relative_to(output_root).as_posix() for p in output_root.rglob("*") if p.is_file()]
        for rel in rels:
            assert not any(fragment in rel for fragment in FORBIDDEN_FRAGMENTS), (
                f"forbidden item leaked into Pilot bundle: {rel}"
            )

    def test_second_deterministic_build_identical(self, tmp_path: Path) -> None:
        first_root, first_archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "det1")
        second_root, second_archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "det2")
        assert _tree_sha256(first_root) == _tree_sha256(second_root)
        assert first_archive.read_bytes() == second_archive.read_bytes()


class TestPilotBundleRuntime:
    def test_bundled_cli_imports_with_bundled_src(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "import")
        code_dir = output_root / "code"
        probe = (
            "import sys; "
            f"sys.path.insert(0, {str(code_dir)!r}); "
            "import seven_arm_benchmark; "
            "p = seven_arm_benchmark.PROFILES['pilot']; "
            "print(p.scenario_count, len(p.scenario_ids), p.repetitions, "
            "','.join(p.strategies), p.timeout_seconds)"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        assert result.stdout.strip() == "12 12 2 iterative_repository_agent,selective 600"

    def test_bundled_exact_dry_run_pilot_48_unique_cells(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "dryrun")
        script = output_root / "code" / "seven_arm_benchmark.py"
        data_dir = output_root / "data"
        output_dir = tmp_path / "dryrun-runs"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--dry-run",
                "--profile", "pilot",
                "--data-dir", str(data_dir),
                "--qwen-quantization", "bnb-nf4",
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        records_path = output_dir / "run_records.jsonl"
        assert records_path.is_file(), f"missing run_records.jsonl: {output_dir}"

        records = [
            json.loads(line)
            for line in records_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        run_ids = [r["run_id"] for r in records]
        assert len(records) == 48, f"expected 48 records, got {len(records)}"
        assert len(set(run_ids)) == 48, "duplicate run IDs in bundled dry-run"

        from collections import Counter

        repo_counts = Counter(r["repository_id"] for r in records)
        strategy_counts = Counter(r["strategy_id"] for r in records)
        rep_counts = Counter(r["repetition"] for r in records)
        assert repo_counts == {"todo": 16, "djangocms": 16, "saleor": 16}
        assert strategy_counts == {
            "iterative_repository_agent": 24,
            "selective": 24,
        }
        assert rep_counts == {1: 24, 2: 24}


class TestPilotKaggleTransport:
    """Kaggle-safe transport encoding contract (PILOT-EXEC-01 KAGGLE-FILENAME-TRANSPORT).

    The canonical bundle tree keeps every original upstream filename; the ZIP
    transports unsafe members under deterministic safe blobs plus a hashed path
    map; the Pilot notebook restores exact original paths BEFORE manifest and
    repository content-hash verification. The hermetic fixture seeds
    upstream-style unsafe names (``[ ] & @ =``) in every build.
    """

    @staticmethod
    def _unsafe_files_in_tree(root: Path) -> list[str]:
        return [
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file()
            and not pilot_builder.is_kaggle_safe_name(p.relative_to(root).as_posix())
        ]

    @staticmethod
    def _restore_cell_source() -> str:
        nb = json.loads(CANONICAL_NOTEBOOK.read_text(encoding="utf-8"))
        cell = next(c for c in nb["cells"] if c.get("id") == "transport-restore-cell")
        src = cell["source"]
        return src if isinstance(src, str) else "".join(src)

    def _run_restore(self, extract_root: Path) -> int:
        """Execute the REAL notebook restore cell against an extracted bundle."""
        namespace: dict[str, Any] = {
            "EXTRACT_ROOT": extract_root,
            "_json": json,
            "shutil": shutil,
            "_sha256_bytes": lambda data: hashlib.sha256(data).hexdigest(),
        }
        exec(self._restore_cell_source(), namespace)
        return int(namespace["_restored_count"])

    def _extract_and_restore(self, archive: Path, tmp_path: Path) -> Path:
        extract_root = tmp_path / "extract"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_root)
        self._run_restore(extract_root)
        return extract_root

    def test_zip_has_zero_unsafe_member_names(self, tmp_path: Path) -> None:
        _output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "zunsafe")
        with zipfile.ZipFile(archive) as zf:
            unsafe, reserved = pilot_builder.kaggle_unsafe_members(zf.namelist())
        assert unsafe == []
        assert reserved == []

    def test_remapped_members_match_unsafe_files_in_tree(self, tmp_path: Path) -> None:
        output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "remap")
        tree_unsafe = self._unsafe_files_in_tree(output_root)
        assert len(tree_unsafe) == 5, tree_unsafe  # 2 djangocms + 3 saleor hermetic seeds
        with zipfile.ZipFile(archive) as zf:
            members = zf.namelist()
        blobs = [n for n in members if n.startswith(f"{TRANSPORT_FILES_PREFIX}")]
        assert len(blobs) == len(tree_unsafe), (len(blobs), len(tree_unsafe))
        expected_blobs = {
            f"{TRANSPORT_FILES_PREFIX}{hashlib.sha256(rel.encode()).hexdigest()}.blob"
            for rel in tree_unsafe
        }
        assert set(blobs) == expected_blobs

    def test_safe_filename_remains_unchanged(self, tmp_path: Path) -> None:
        _output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "safe")
        with zipfile.ZipFile(archive) as zf:
            assert "code/configs/pilot.yaml" in zf.namelist()
            assert "data/repositories/todo/pilot_hermetic_marker.txt" in zf.namelist()

    def test_canonical_bundle_tree_keeps_original_unsafe_names(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "keepsrc")
        unsafe = self._unsafe_files_in_tree(output_root)
        assert len(unsafe) == 5
        assert any("sr@latin" in rel for rel in unsafe)
        assert any("[http]" in rel for rel in unsafe)
        assert any("[24.39-30.00-True]" in rel for rel in unsafe)
        assert not (output_root / TRANSPORT_BLOB_PREFIX).exists()

    def test_transport_mapping_deterministic(self, tmp_path: Path) -> None:
        _first_root, first_archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "mdet1")
        _second_root, second_archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "mdet2")
        with zipfile.ZipFile(first_archive) as zf:
            first = json.loads(zf.read(TRANSPORT_MAP_NAME).decode("utf-8"))
        with zipfile.ZipFile(second_archive) as zf:
            second = json.loads(zf.read(TRANSPORT_MAP_NAME).decode("utf-8"))
        assert first == second
        assert len(first) == 5

    def test_mapping_identity_hash_correct(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "idhash")
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        map_bytes = (output_root / TRANSPORT_MAP_NAME).read_bytes()
        assert identity["kaggle_transport_path_map_sha256"] == hashlib.sha256(map_bytes).hexdigest()
        assert len(identity["kaggle_transport_path_map_sha256"]) == 64

    def test_roundtrip_extract_restore_recreates_original_paths_and_bytes(self, tmp_path: Path) -> None:
        output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "rt")
        extract_root = self._extract_and_restore(archive, tmp_path)
        for rel in self._unsafe_files_in_tree(output_root):
            assert (extract_root / rel).is_file(), f"restore missed: {rel}"
            assert (extract_root / rel).read_bytes() == (output_root / rel).read_bytes()
        assert _tree_sha256(extract_root / "data") == _tree_sha256(output_root / "data")
        assert _tree_sha256(extract_root / "code") == _tree_sha256(output_root / "code")
        assert not (extract_root / TRANSPORT_BLOB_PREFIX).exists()

    def test_validator_rejects_old_reserved_transport_root(self) -> None:
        old_root_member = f"__kaggle_transport__/files/{'a' * 64}.blob"
        assert not pilot_builder.is_kaggle_safe_name("__kaggle_transport__")
        with pytest.raises(RuntimeError, match="KAGGLE PRE-UPLOAD VALIDATION FAILED"):
            pilot_builder.validate_archive_members_kaggle_ready([old_root_member])

    def test_validator_rejects_nested_reserved_name_component(self) -> None:
        with pytest.raises(RuntimeError, match="reserved-name"):
            pilot_builder.validate_archive_members_kaggle_ready(["data/x/__name__/y.txt"])
        with pytest.raises(RuntimeError, match="reserved-name"):
            pilot_builder.validate_archive_members_kaggle_ready(["data/__pycache__/y.txt"])
        assert not pilot_builder.is_kaggle_safe_name("data/__name__/y.txt")

    def test_validator_accepts_kaggle_transport_root(self) -> None:
        assert pilot_builder.is_kaggle_safe_name("kaggle_transport")
        assert pilot_builder.is_kaggle_safe_name("kaggle_transport/files")
        count = pilot_builder.validate_archive_members_kaggle_ready(
            [f"kaggle_transport/files/{'a' * 64}.blob", "data/x/y.txt"]
        )
        assert count == (0, 0)

    def test_validator_accepts_init_py_files(self) -> None:
        assert pilot_builder.is_kaggle_safe_name("code/src/benchmark/__init__.py")
        assert pilot_builder.validate_archive_members_kaggle_ready(
            ["code/src/benchmark/__init__.py", "data/repositories/saleor/__init__.py"]
        ) == (0, 0)

    def test_validator_rejects_unsafe_special_chars_member(self) -> None:
        with pytest.raises(RuntimeError, match="unsafe-special-char"):
            pilot_builder.validate_archive_members_kaggle_ready(["data/a[b].yaml"])
        assert not pilot_builder.is_kaggle_safe_name("saleor/core/tests/sr@latin/LC_MESSAGES/django.po")

    def test_reserved_name_member_is_transported_and_restored(self, tmp_path: Path) -> None:
        root = tmp_path / "tree"
        (root / "data").mkdir(parents=True)
        (root / "data" / "ok.txt").write_bytes(b"ok")
        reserved = root / "data" / "__pilot__" / "magic.txt"
        reserved.parent.mkdir(parents=True)
        reserved.write_bytes(b"reserved-name")
        mapping = pilot_builder.build_transport_path_map(root)
        assert list(mapping.values()) == ["data/__pilot__/magic.txt"]
        pilot_builder.write_transport_path_map(root, mapping)
        (root / "pilot_deployment_identity.json").write_text(
            json.dumps(
                {
                    "kaggle_transport_path_map_sha256": hashlib.sha256(
                        (root / TRANSPORT_MAP_NAME).read_bytes()
                    ).hexdigest()
                }
            ),
            encoding="utf-8",
        )
        archive = tmp_path / "t.zip"
        pilot_builder.create_deterministic_zip(root, archive, "2026-08-10T00:00:00+00:00")
        with zipfile.ZipFile(archive) as zf:
            members = zf.namelist()
        assert "data/__pilot__/magic.txt" not in members
        assert not any(
            pilot_builder.KAGGLE_RESERVED_NAME_RE.match(comp)
            for m in members
            for comp in m.split("/")
        )
        extract_root = tmp_path / "extract"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_root)
        self._run_restore(extract_root)
        assert (extract_root / "data" / "__pilot__" / "magic.txt").read_bytes() == b"reserved-name"
        assert (extract_root / "data" / "ok.txt").read_bytes() == b"ok"
        assert not (extract_root / TRANSPORT_BLOB_PREFIX).exists()

    def test_data_manifest_passes_after_restore(self, tmp_path: Path) -> None:
        output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "dman")
        extract_root = self._extract_and_restore(archive, tmp_path)
        manifest = json.loads((extract_root / "data_manifest.json").read_text(encoding="utf-8"))
        errors = []
        for rel, expected in sorted(manifest.items()):
            p = extract_root / "data" / rel
            if not p.is_file():
                errors.append(f"missing: {rel}")
            elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                errors.append(f"hash mismatch: {rel}")
        assert errors == []

    def test_repository_content_hash_passes_after_restore(self, tmp_path: Path) -> None:
        output_root, archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "rhash")
        extract_root = self._extract_and_restore(archive, tmp_path)
        snapshot = json.loads(
            (extract_root / "repository_snapshot_manifest.json").read_text(encoding="utf-8")
        )
        for repo_id, entry in snapshot["repositories"].items():
            repo_root = extract_root / "data" / "repositories" / repo_id
            digest = hashlib.sha256()
            for rel in sorted(
                p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*") if p.is_file()
            ):
                digest.update(rel.encode("utf-8"))
                digest.update(b"\0")
                digest.update((repo_root / rel).read_bytes())
                digest.update(b"\0")
            assert digest.hexdigest() == entry["content_hash"], (
                f"restored repo content hash mismatch: {repo_id}"
            )
        assert _tree_sha256(extract_root / "data") == _tree_sha256(output_root / "data")

    def test_path_traversal_mapping_fails_closed(self, tmp_path: Path) -> None:
        extract_root = tmp_path / "traversal"
        extract_root.mkdir(parents=True)
        blob_dir = extract_root / TRANSPORT_BLOB_PREFIX / "files"
        blob_dir.mkdir(parents=True)
        blob = blob_dir / f"{'a' * 64}.blob"
        blob.write_bytes(b"data")
        map_path = extract_root / TRANSPORT_MAP_NAME
        map_path.write_text(
            json.dumps({f"{TRANSPORT_FILES_PREFIX}{'a' * 64}.blob": "../escape.txt"})
            + "\n",
            encoding="utf-8",
        )
        identity_path = extract_root / "pilot_deployment_identity.json"
        identity_path.write_text(
            json.dumps(
                {"kaggle_transport_path_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()}
            ),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="safe relative path"):
            self._run_restore(extract_root)

    def test_destination_collision_fails_closed(self, tmp_path: Path) -> None:
        extract_root = tmp_path / "collision"
        extract_root.mkdir(parents=True)
        blob_dir = extract_root / TRANSPORT_BLOB_PREFIX / "files"
        blob_dir.mkdir(parents=True)
        blob = blob_dir / f"{'a' * 64}.blob"
        blob.write_bytes(b"data")
        dest = extract_root / "data" / "repos" / "existing[a].yaml"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"already-present")
        map_path = extract_root / TRANSPORT_MAP_NAME
        map_path.write_text(
            json.dumps(
                {f"{TRANSPORT_FILES_PREFIX}{'a' * 64}.blob": "data/repos/existing[a].yaml"}
            )
            + "\n",
            encoding="utf-8",
        )
        identity_path = extract_root / "pilot_deployment_identity.json"
        identity_path.write_text(
            json.dumps(
                {"kaggle_transport_path_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()}
            ),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="destination collision"):
            self._run_restore(extract_root)

    def test_duplicate_encoded_target_fails_closed(self, tmp_path: Path) -> None:
        extract_root = tmp_path / "dup"
        extract_root.mkdir(parents=True)
        blob_dir = extract_root / TRANSPORT_BLOB_PREFIX / "files"
        blob_dir.mkdir(parents=True)
        blob_a = blob_dir / f"{'a' * 64}.blob"
        blob_b = blob_dir / f"{'b' * 64}.blob"
        blob_a.write_bytes(b"one")
        blob_b.write_bytes(b"two")
        map_path = extract_root / TRANSPORT_MAP_NAME
        map_path.write_text(
            json.dumps(
                {
                    f"{TRANSPORT_FILES_PREFIX}{'a' * 64}.blob": "data/x.yaml",
                    f"{TRANSPORT_FILES_PREFIX}{'b' * 64}.blob": "data/x.yaml",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        identity_path = extract_root / "pilot_deployment_identity.json"
        identity_path.write_text(
            json.dumps(
                {"kaggle_transport_path_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()}
            ),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="destination collision"):
            self._run_restore(extract_root)

    def test_missing_blob_fails_closed(self, tmp_path: Path) -> None:
        extract_root = tmp_path / "missing"
        extract_root.mkdir(parents=True)
        map_path = extract_root / TRANSPORT_MAP_NAME
        map_path.write_text(
            json.dumps(
                {f"{TRANSPORT_FILES_PREFIX}{'c' * 64}.blob": "data/y.yaml"}
            )
            + "\n",
            encoding="utf-8",
        )
        identity_path = extract_root / "pilot_deployment_identity.json"
        identity_path.write_text(
            json.dumps(
                {"kaggle_transport_path_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()}
            ),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="transport blob missing"):
            self._run_restore(extract_root)


class TestPilotKaggleExpandedMount:
    """PILOT-EXEC-01 KAGGLE-AUTO-EXPANDED-MOUNT execution contract.

    Simulates the two real Kaggle input mounts - (A) the original frozen
    archive and (B) the auto-expanded ``pilot-kaggle-upload/`` directory plus a
    sibling ``.sha256`` sidecar - against the REAL notebook setup + input-verify
    + transport-restore + identity-verify cells. The notebook's frozen trust
    constants are overridden to match the bundle under test (mirroring what the
    tagged build freezes). Mode B must fail closed on every tamper/mis-mount,
    copy the expanded tree into the writable working root (never mutating
    /kaggle/input), and converge on the exact same canonical tree as Mode A.
    """

    @staticmethod
    def _cell_source(cell_id: str) -> str:
        nb = json.loads(CANONICAL_NOTEBOOK.read_text(encoding="utf-8"))
        cell = next(c for c in nb["cells"] if c.get("id") == cell_id)
        src = cell["source"]
        return src if isinstance(src, str) else "".join(src)

    @staticmethod
    def _setup_source(sim_input: Path) -> str:
        src = TestPilotKaggleExpandedMount._cell_source("setup-cell")
        marker = 'KAGGLE_INPUT = Path("/kaggle/input")'
        assert marker in src
        return src.replace(marker, f"KAGGLE_INPUT = Path({str(sim_input.resolve())!r})")

    @staticmethod
    def _make_model_mount(sim_input: Path) -> None:
        model_dir = sim_input / "models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / "model.safetensors").write_bytes(b"w")

    @staticmethod
    def _make_dataset_dir(sim_input: Path) -> Path:
        dataset = (
            sim_input
            / "datasets/ahmedehabh/dependency-aware-selective-regeneration-pilot"
        )
        dataset.mkdir(parents=True, exist_ok=True)
        return dataset

    @staticmethod
    def _archive_sha(archive: Path) -> str:
        return hashlib.sha256(archive.read_bytes()).hexdigest()

    @classmethod
    def _mount_expanded(cls, sim_input: Path, archive: Path) -> Path:
        dataset = cls._make_dataset_dir(sim_input)
        target = dataset / "pilot-kaggle-upload"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)
        (dataset / "pilot-kaggle-upload.zip.sha256").write_text(
            cls._archive_sha(archive), encoding="utf-8"
        )
        return dataset

    @classmethod
    def _mount_archive(cls, sim_input: Path, archive: Path) -> Path:
        dataset = cls._make_dataset_dir(sim_input)
        shutil.copy2(archive, dataset / "pilot-kaggle-upload.zip")
        (dataset / "pilot-kaggle-upload.zip.sha256").write_text(
            cls._archive_sha(archive), encoding="utf-8"
        )
        return dataset

    def _provision(
        self,
        sim_input: Path,
        working_root: Path,
        identity: dict[str, Any],
        frozen_archive_sha: str,
        *,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Exec the real setup cell then the real input-verify cell.

        The frozen trust constants are injected AFTER setup (which declares
        development placeholders) so the verify cell checks the bundle under
        test. ``extract_root`` is redirected to a writable working root.
        """
        self._make_model_mount(sim_input)
        ns: dict[str, Any] = {
            "os": os,
            "sys": sys,
            "subprocess": subprocess,
            "zipfile": zipfile,
            "_json": json,
            "socket": socket,
            "urllib": urllib,
            "shutil": shutil,
            "hashlib": hashlib,
            "datetime": datetime,
            "Path": Path,
            "KNOWN_PILOT_DATASET": (
                sim_input
                / "datasets/ahmedehabh/dependency-aware-selective-regeneration-pilot"
            ),
            "FALLBACK_PILOT_DATASET": (
                sim_input / "dependency-aware-selective-regeneration-pilot"
            ),
        }
        _saved_path = list(sys.path)
        try:
            exec(self._setup_source(sim_input), ns)
            deployment_paths = dict(ns["KAGGLE_DEPLOYMENT_PATHS"])
            deployment_paths["extract_root"] = working_root / "pilot_bundle"
            ns["KAGGLE_DEPLOYMENT_PATHS"] = deployment_paths
            ns["FROZEN_SOURCE_TAG"] = identity["source_tag"]
            ns["FROZEN_DEPLOYMENT"] = {k: identity[k] for k in FROZEN_IDENTITY}
            ns["FROZEN_MANIFEST_HASHES"] = {
                key: identity[key]
                for key in (
                    "code_manifest_sha256",
                    "data_manifest_sha256",
                    "repository_snapshot_manifest_sha256",
                    "kaggle_transport_path_map_sha256",
                )
            }
            if overrides:
                ns.update(overrides)
            exec(self._cell_source("pilot-archive-verify-cell"), ns)
        finally:
            sys.path[:] = _saved_path
        return ns

    def _finish_flow(self, ns: dict[str, Any]) -> int:
        """Exec the real transport-restore and identity-verify cells."""
        _saved_path = list(sys.path)
        try:
            exec(self._cell_source("transport-restore-cell"), ns)
            exec(self._cell_source("pilot-identity-verify-cell"), ns)
        finally:
            sys.path[:] = _saved_path
        return int(ns["_restored_count"])

    @staticmethod
    def _dry_run_records(ns: dict[str, Any], tmp_path: Path) -> list[dict[str, Any]]:
        extract_root = Path(ns["EXTRACT_ROOT"])
        script = extract_root / "code" / "seven_arm_benchmark.py"
        output_dir = tmp_path / "dryrun-expanded"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--dry-run",
                "--profile", "pilot",
                "--data-dir", str(extract_root / "data"),
                "--qwen-quantization", "bnb-nf4",
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        records_path = output_dir / "run_records.jsonl"
        return [
            json.loads(line)
            for line in records_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_archive_mode_roundtrip(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "archrt"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_archive(sim_input, archive)
        ns = self._provision(
            sim_input, tmp_path / "working", identity, self._archive_sha(archive)
        )
        assert ns["PILOT_INPUT_MODE"] == "archive"
        restored = self._finish_flow(ns)
        assert restored == 5, restored  # hermetic unsafe-file seed count
        extract_root = Path(ns["EXTRACT_ROOT"])
        assert _tree_sha256(extract_root / "data") == _tree_sha256(output_root / "data")
        assert _tree_sha256(extract_root / "code") == _tree_sha256(output_root / "code")

    def test_expanded_mode_copies_to_working_root_and_never_mutates_input(
        self, tmp_path: Path
    ) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "exprt"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._make_model_mount(sim_input)
        self._mount_expanded(sim_input, archive)
        before = _tree_sha256(sim_input)
        working = tmp_path / "working"
        ns = self._provision(
            sim_input, working, identity, self._archive_sha(archive)
        )
        assert ns["PILOT_INPUT_MODE"] == "expanded"
        assert _tree_sha256(sim_input) == before, "/kaggle/input mount was mutated"
        extract_root = Path(ns["EXTRACT_ROOT"])
        assert extract_root.is_dir()
        assert extract_root != Path(ns["PILOT_BUNDLE_INPUT"])
        assert extract_root.is_relative_to(working)
        assert (extract_root / "kaggle_transport").is_dir()
        assert (extract_root / "kaggle_transport_path_map.json").is_file()

    def test_expanded_mode_roundtrip_identical_to_archive_mode(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "modes"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sha = self._archive_sha(archive)

        sim_arch = tmp_path / "kaggle_input_archive"
        self._mount_archive(sim_arch, archive)
        ns_arch = self._provision(sim_arch, tmp_path / "working_arch", identity, sha)
        assert ns_arch["PILOT_INPUT_MODE"] == "archive"
        restored_arch = self._finish_flow(ns_arch)
        arch_root = Path(ns_arch["EXTRACT_ROOT"])

        sim_exp = tmp_path / "kaggle_input_expanded"
        self._mount_expanded(sim_exp, archive)
        ns_exp = self._provision(sim_exp, tmp_path / "working_exp", identity, sha)
        assert ns_exp["PILOT_INPUT_MODE"] == "expanded"
        restored_exp = self._finish_flow(ns_exp)
        exp_root = Path(ns_exp["EXTRACT_ROOT"])

        assert restored_arch == restored_exp == 5
        assert _tree_sha256(arch_root / "data") == _tree_sha256(exp_root / "data")
        assert _tree_sha256(arch_root / "code") == _tree_sha256(exp_root / "code")
        assert not (exp_root / "kaggle_transport").exists()

    def test_expanded_mode_data_manifest_and_repo_hashes_pass(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "exphash"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        ns = self._provision(sim_input, tmp_path / "working", identity, self._archive_sha(archive))
        self._finish_flow(ns)
        extract_root = Path(ns["EXTRACT_ROOT"])
        manifest = json.loads((extract_root / "data_manifest.json").read_text(encoding="utf-8"))
        errors = []
        for rel, expected in sorted(manifest.items()):
            p = extract_root / "data" / rel
            if not p.is_file():
                errors.append(f"missing: {rel}")
            elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                errors.append(f"hash mismatch: {rel}")
        assert errors == []
        snapshot = json.loads(
            (extract_root / "repository_snapshot_manifest.json").read_text(encoding="utf-8")
        )
        for repo_id, entry in snapshot["repositories"].items():
            repo_root = extract_root / "data" / "repositories" / repo_id
            digest = hashlib.sha256()
            for rel in sorted(
                p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*") if p.is_file()
            ):
                digest.update(rel.encode("utf-8"))
                digest.update(b"\0")
                digest.update((repo_root / rel).read_bytes())
                digest.update(b"\0")
            assert digest.hexdigest() == entry["content_hash"], (
                f"restored repo content hash mismatch: {repo_id}"
            )

    def test_expanded_mode_dry_run_48_cells(self, tmp_path: Path) -> None:
        _output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "expdry"
        )
        identity = json.loads(
            (_output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        ns = self._provision(sim_input, tmp_path / "working", identity, self._archive_sha(archive))
        self._finish_flow(ns)
        records = self._dry_run_records(ns, tmp_path)
        assert len(records) == 48
        run_ids = [r["run_id"] for r in records]
        assert len(set(run_ids)) == 48
        from collections import Counter

        assert Counter(r["repository_id"] for r in records) == {
            "todo": 16, "djangocms": 16, "saleor": 16
        }

    @pytest.mark.parametrize(
        "tamper, match",
        [
            ("sidecar_malformed", "SIDECAR MALFORMED"),
            ("identity_source_tag", "SOURCE TAG MISMATCH"),
            ("identity_deployment_field", "DEPLOYMENT IDENTITY MISMATCH"),
            ("manifest_bytes", "MANIFEST/MAP SHA MISMATCH"),
            ("notebook_manifest_self_consistency", "MANIFEST/MAP SHA MISMATCH"),
        ],
    )
    def test_expanded_mode_rejects_tampered_mount(
        self, tmp_path: Path, tamper: str, match: str
    ) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "tamper"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        expanded = dataset / "pilot-kaggle-upload"
        if tamper == "sidecar_malformed":
            (dataset / "pilot-kaggle-upload.zip.sha256").write_text("z" * 64, encoding="utf-8")
        elif tamper == "identity_source_tag":
            idp = expanded / "pilot_deployment_identity.json"
            doc = json.loads(idp.read_text(encoding="utf-8"))
            doc["source_tag"] = "v9.9.9-pilot-exec-ready"
            idp.write_text(json.dumps(doc), encoding="utf-8")
        elif tamper == "identity_deployment_field":
            idp = expanded / "pilot_deployment_identity.json"
            doc = json.loads(idp.read_text(encoding="utf-8"))
            doc["expected_cells"] = 47
            idp.write_text(json.dumps(doc), encoding="utf-8")
        elif tamper == "manifest_bytes":
            (expanded / "data_manifest.json").write_bytes(b"tampered")
        else:
            nb = expanded / "notebooks" / "pilot_exec_01.ipynb"
            nb.write_bytes(nb.read_bytes() + b"x")
        if tamper != "sidecar_malformed":
            (dataset / "pilot-kaggle-upload.zip.sha256").write_text(
                self._archive_sha(archive), encoding="utf-8"
            )
        with pytest.raises(RuntimeError, match=match):
            self._provision(
                sim_input, tmp_path / "working", identity, self._archive_sha(archive)
            )

    def test_expanded_mode_missing_sidecar_fails_closed(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "nosh"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        with pytest.raises(FileNotFoundError, match="missing SHA-256 sidecar"):
            self._provision(
                sim_input, tmp_path / "working", identity, self._archive_sha(archive)
            )

    def test_both_archive_and_expanded_fail_closed(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "both"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_archive(sim_input, archive)
        self._mount_expanded(sim_input, archive)
        with pytest.raises(RuntimeError, match="BOTH an original archive"):
            self._provision(
                sim_input, tmp_path / "working", identity, self._archive_sha(archive)
            )

    def test_two_expanded_candidates_fail_closed(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "twoexp"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        second = sim_input / "datasets/other/dependency-aware-selective-regeneration-pilot"
        second.mkdir(parents=True)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(second / "pilot-kaggle-upload")
        with pytest.raises(RuntimeError, match="Ambiguous Pilot bundle input mounts"):
            self._provision(
                sim_input, tmp_path / "working", identity, self._archive_sha(archive)
            )

    def test_no_input_shape_fails_closed(self, tmp_path: Path) -> None:
        output_root, _archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "noinput"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        with pytest.raises(FileNotFoundError, match="Cannot find"):
            self._provision(
                sim_input, tmp_path / "working", identity, "0" * 64
            )

    def test_non_empty_extract_root_fails_closed(self, tmp_path: Path) -> None:
        output_root, archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "nonempty"
        )
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        working = tmp_path / "working"
        (working / "pilot_bundle").mkdir(parents=True)
        (working / "pilot_bundle" / "stale.txt").write_text("x", encoding="utf-8")
        with pytest.raises(RuntimeError, match="refusing to reuse a non-empty"):
            self._provision(
                sim_input, working, identity, self._archive_sha(archive)
            )

    @pytest.mark.skipif(
        not DIST_ARTIFACT.is_file(),
        reason="current frozen Pilot artifact not present under dist/",
    )
    def test_real_kaggle_artifact_expanded_simulation(self, tmp_path: Path) -> None:
        """Full real-mount simulation against the frozen dist/ artifact.

        The dist archive is the exact frozen upload (v0.9.5 while developing,
        replaced by the v0.9.7 tagged rebuild at finalization). The frozen trust
        constants are overridden from the artifact's own identity so the current
        notebook logic is exercised against the real Kaggle-shaped mount: 50
        transport blobs restored, manifests verified, repo hashes verified, and
        the exact 48-cell dry-run passes.
        """
        with zipfile.ZipFile(DIST_ARTIFACT) as zf:
            identity = json.loads(
                zf.read("pilot_deployment_identity.json").decode("utf-8")
            )
        sha = hashlib.sha256(DIST_ARTIFACT.read_bytes()).hexdigest()
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(DIST_ARTIFACT) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        (dataset / "pilot-kaggle-upload.zip.sha256").write_text(sha, encoding="utf-8")
        ns = self._provision(
            sim_input,
            tmp_path / "working",
            identity,
            sha,
        )
        assert ns["PILOT_INPUT_MODE"] == "expanded"
        restored = self._finish_flow(ns)
        assert restored == 50, f"expected 50 transport blobs restored, got {restored}"
        records = self._dry_run_records(ns, tmp_path)
        assert len(records) == 48
        run_ids = [r["run_id"] for r in records]
        assert len(set(run_ids)) == 48
        from collections import Counter

        assert Counter(r["repository_id"] for r in records) == {
            "todo": 16, "djangocms": 16, "saleor": 16
        }


class TestPilotNotebookTrustFreeze:
    """Deterministic stable-anchor freeze (PILOT-EXEC-01 KAGGLE-AUTO-EXPANDED-MOUNT).

    The notebook embeds ONLY notebook-independent anchors: source tag, the
    deployment identity, and the four stable manifest/map hashes. The archive
    SHA and notebook-manifest SHA are self-referential (they hash the notebook
    bytes that would embed them) and are therefore NEVER frozen; they are
    verified self-consistently at runtime. The freezer must be a deterministic
    single pass (no hash iteration), write the four stable hashes, and be
    idempotent (second run changes nothing, archive byte-identical).
    """

    @staticmethod
    def _load_finalizer() -> Any:
        spec = importlib.util.spec_from_file_location(
            "finalize_pilot_notebook_trust_under_test",
            str(SCRIPTS_DIR / "finalize_pilot_notebook_trust.py"),
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_freezes_single_pass_and_is_idempotent(self, tmp_path: Path) -> None:
        mod = self._load_finalizer()
        notebook = tmp_path / "pilot_exec_01.ipynb"
        notebook.write_bytes(CANONICAL_NOTEBOOK.read_bytes())
        common = dict(
            notebook_path=notebook,
            output_root=tmp_path / "freeze-output",
            archive_path=tmp_path / "freeze-archive.zip",
            source_commit="a" * 40,
            source_tag="v0.9.8-pilot-exec-ready",
            created_utc="2026-08-13T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            report_path=tmp_path / "freeze-report.json",
        )
        first = mod.freeze(**common)
        assert first["status"] == "FROZEN"
        assert first["frozen_source_tag"] == "v0.9.8-pilot-exec-ready"
        assert len(first["archive_sha256"]) == 64
        assert set(first["frozen_manifest_hashes"]) == {
            "code_manifest_sha256",
            "data_manifest_sha256",
            "repository_snapshot_manifest_sha256",
            "kaggle_transport_path_map_sha256",
        }
        for key, value in first["frozen_manifest_hashes"].items():
            assert len(value) == 64, f"frozen {key} not 64 hex: {value}"
            assert value != "0" * 64, f"frozen {key} still a zero placeholder"
        assert first["frozen_deployment"]["task"] == "PILOT-EXEC-01"
        # The frozen notebook must now carry exactly the frozen values.
        written = mod.read_frozen_values(notebook)
        assert written["FROZEN_MANIFEST_HASHES"] == first["frozen_manifest_hashes"]
        assert written["FROZEN_SOURCE_TAG"] == "v0.9.8-pilot-exec-ready"
        assert "FROZEN_ARCHIVE_SHA" not in written
        assert "FROZEN_SOURCE_COMMIT" not in written

        # Idempotent: a second run changes no bytes and reproduces the archive.
        frozen_bytes = notebook.read_bytes()
        second = mod.freeze(**common)
        assert second["status"] == "FROZEN"
        assert second["frozen_manifest_hashes"] == first["frozen_manifest_hashes"]
        assert second["archive_sha256"] == first["archive_sha256"]
        assert notebook.read_bytes() == frozen_bytes

    def test_placeholder_notebook_is_still_frozen_shaped(self, tmp_path: Path) -> None:
        """The canonical development notebook must still carry well-formed anchors."""
        mod = self._load_finalizer()
        values = mod.read_frozen_values(CANONICAL_NOTEBOOK)
        assert values["FROZEN_SOURCE_TAG"] == "v0.9.8-pilot-exec-ready"
        assert isinstance(values["FROZEN_DEPLOYMENT"], dict)
        assert values["FROZEN_DEPLOYMENT"]["task"] == "PILOT-EXEC-01"
        assert set(values["FROZEN_MANIFEST_HASHES"]) == {
            "code_manifest_sha256",
            "data_manifest_sha256",
            "repository_snapshot_manifest_sha256",
            "kaggle_transport_path_map_sha256",
        }
        for key, value in values["FROZEN_MANIFEST_HASHES"].items():
            assert len(value) == 64, f"frozen {key} not 64 hex: {value}"
