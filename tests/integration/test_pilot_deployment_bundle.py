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
import re
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
    "protocol_version": "1.1",
    "model_name": "Qwen/Qwen2.5-Coder-14B-Instruct",
    "quantization": "bnb-nf4",
    "timeout_seconds": 1200,
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
    """Construction-only bundle (NOT a release-gated artifact).

    These builds exercise output isolation, parity, manifests, runtime and
    transport; they intentionally build with the embedded-notebook trust gate
    disabled because the canonical notebook legitimately still carries
    development/stale anchors until the finalizer freezes a release.
    """
    output_root = tmp_path / f"pilot-upload-{label}"
    archive = tmp_path / f"pilot-upload-{label}.zip"
    pilot_builder.build_pilot_bundle(
        output_root=output_root,
        archive_path=archive,
        source_commit=source_commit,
        source_tag="v0.9.3-pilot-exec-ready",
        created_utc=created_utc,
        validate_notebook_trust=False,
    )
    return output_root, archive


PILOT_SOURCE_TAG = "v0.9.22-d10-candidate"


def _build_frozen(
    tmp_path: Path, created_utc: str, source_commit: str, label: str
) -> tuple[Path, Path, Path]:
    """Build a FINALIZED hermetic bundle whose notebook anchors match identity.

    Runs the real two-pass freezer on a temp copy of the canonical notebook
    (discovery build with the gate off, write anchors, then a validation build
    with the gate on). Returns ``(output_root, archive, frozen_notebook)``. The
    provisioning cells MUST be exec'd from ``frozen_notebook`` - not the
    canonical notebook - because only the frozen copy carries the anchors that
    match the bundle's identity. Nothing is injected.
    """
    finalizer = _load_finalizer()
    notebook_dir = tmp_path / f"pilot_frozen_{label}"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    notebook = notebook_dir / "pilot_exec_01.ipynb"
    notebook.write_bytes(CANONICAL_NOTEBOOK.read_bytes())
    output_root = tmp_path / f"pilot-upload-{label}"
    archive = tmp_path / f"pilot-upload-{label}.zip"
    report = finalizer.freeze(
        notebook_path=notebook,
        output_root=output_root,
        archive_path=archive,
        source_commit=source_commit,
        source_tag=PILOT_SOURCE_TAG,
        created_utc=created_utc,
        repo_cache=None,
        allow_acquire=False,
        report_path=tmp_path / f"freeze-report-{label}.json",
    )
    assert report["status"] == "FROZEN", report
    return output_root, archive, notebook


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

    def test_baseline_flake_profile_bundled_byte_equal_and_manifested(
        self, tmp_path: Path
    ) -> None:
        """v0.9.20 Task F: once the frozen baseline-flake evidence profile
        exists, every Pilot bundle must ship it byte-equal under code/reports/
        and manifest it. Before the first target-shaped evidence run the source
        profile legitimately does not exist; the deployed preflight cell fails
        closed on its absence, and this test asserts the consistent state."""
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "bfp")
        bundled = output_root / "code" / "reports" / "pilot_saleor_baseline_flaky_profile.json"
        source = PROJECT_DIR / "reports" / "pilot_saleor_baseline_flaky_profile.json"
        if not source.is_file():
            assert not bundled.exists(), (
                "bundled baseline-flake profile appeared without a source artifact"
            )
            return
        assert bundled.is_file()
        assert _normalized_bytes(bundled) == _normalized_bytes(source)
        code_manifest = json.loads(
            (output_root / "code_manifest.json").read_text(encoding="utf-8")
        )
        rel = "reports/pilot_saleor_baseline_flaky_profile.json"
        assert rel in code_manifest
        entry_hash = code_manifest[rel]
        assert isinstance(entry_hash, str)
        assert entry_hash == hashlib.sha256(_normalized_bytes(bundled)).hexdigest()
        payload = json.loads(bundled.read_text(encoding="utf-8"))
        assert payload["schema"] == "pilot_saleor_baseline_flaky_profile.v1"
        assert payload["failed_nodeids"]
        assert all(
            entry["passed"] is True for entry in payload["per_nodeid_serial_rerun"]
        )


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
        assert result.stdout.strip() == "12 12 2 iterative_repository_agent,selective 1200"

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


def _dist_artifact_is_current_release() -> bool:
    if not DIST_ARTIFACT.is_file():
        return False
    with zipfile.ZipFile(DIST_ARTIFACT) as zf:
        identity = json.loads(zf.read("pilot_deployment_identity.json").decode("utf-8"))
    return identity.get("source_tag") == PILOT_SOURCE_TAG


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
    def _cell_source(cell_id: str, notebook_path: Path = CANONICAL_NOTEBOOK) -> str:
        nb = json.loads(notebook_path.read_text(encoding="utf-8"))
        cell = next(c for c in nb["cells"] if c.get("id") == cell_id)
        src = cell["source"]
        return src if isinstance(src, str) else "".join(src)

    @staticmethod
    def _setup_source(sim_input: Path, notebook_path: Path = CANONICAL_NOTEBOOK) -> str:
        src = TestPilotKaggleExpandedMount._cell_source("setup-cell", notebook_path)
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
        notebook_path: Path,
        *,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Exec the real setup cell then the real input-verify cell.

        The setup cell declares the notebook's frozen trust constants (source
        tag, deployment identity, the four stable manifest/map hashes). NO
        identity values are injected here: the cell source comes from the exact
        notebook that was bundled (a finalized copy for hermetic builds), so the
        anchors in the exec namespace already match the bundle under test.
        ``overrides`` exists ONLY for negative tamper tests and must be named as
        such at the call site. ``extract_root`` is redirected to a writable
        working root.
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
            exec(self._setup_source(sim_input, notebook_path), ns)
            deployment_paths = dict(ns["KAGGLE_DEPLOYMENT_PATHS"])
            deployment_paths["extract_root"] = working_root / "pilot_bundle"
            ns["KAGGLE_DEPLOYMENT_PATHS"] = deployment_paths
            if overrides:
                ns.update(overrides)
            exec(self._cell_source("pilot-archive-verify-cell", notebook_path), ns)
        finally:
            sys.path[:] = _saved_path
        return ns

    def _finish_flow(self, ns: dict[str, Any], notebook_path: Path = CANONICAL_NOTEBOOK) -> int:
        """Exec the real transport-restore and identity-verify cells."""
        _saved_path = list(sys.path)
        try:
            exec(self._cell_source("transport-restore-cell", notebook_path), ns)
            exec(self._cell_source("pilot-identity-verify-cell", notebook_path), ns)
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
        output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "archrt"
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_archive(sim_input, archive)
        ns = self._provision(sim_input, tmp_path / "working", frozen_notebook)
        assert ns["PILOT_INPUT_MODE"] == "archive"
        restored = self._finish_flow(ns, frozen_notebook)
        assert restored == 5, restored  # hermetic unsafe-file seed count
        extract_root = Path(ns["EXTRACT_ROOT"])
        assert _tree_sha256(extract_root / "data") == _tree_sha256(output_root / "data")
        assert _tree_sha256(extract_root / "code") == _tree_sha256(output_root / "code")

    def test_expanded_mode_copies_to_working_root_and_never_mutates_input(
        self, tmp_path: Path
    ) -> None:
        output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "exprt"
        )
        sim_input = tmp_path / "kaggle_input"
        self._make_model_mount(sim_input)
        self._mount_expanded(sim_input, archive)
        before = _tree_sha256(sim_input)
        working = tmp_path / "working"
        ns = self._provision(sim_input, working, frozen_notebook)
        assert ns["PILOT_INPUT_MODE"] == "expanded"
        assert _tree_sha256(sim_input) == before, "/kaggle/input mount was mutated"
        extract_root = Path(ns["EXTRACT_ROOT"])
        assert extract_root.is_dir()
        assert extract_root != Path(ns["PILOT_BUNDLE_INPUT"])
        assert extract_root.is_relative_to(working)
        assert (extract_root / "kaggle_transport").is_dir()
        assert (extract_root / "kaggle_transport_path_map.json").is_file()

    def test_expanded_mode_roundtrip_identical_to_archive_mode(self, tmp_path: Path) -> None:
        output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "modes"
        )
        sim_arch = tmp_path / "kaggle_input_archive"
        self._mount_archive(sim_arch, archive)
        ns_arch = self._provision(sim_arch, tmp_path / "working_arch", frozen_notebook)
        assert ns_arch["PILOT_INPUT_MODE"] == "archive"
        restored_arch = self._finish_flow(ns_arch, frozen_notebook)
        arch_root = Path(ns_arch["EXTRACT_ROOT"])

        sim_exp = tmp_path / "kaggle_input_expanded"
        self._mount_expanded(sim_exp, archive)
        ns_exp = self._provision(sim_exp, tmp_path / "working_exp", frozen_notebook)
        assert ns_exp["PILOT_INPUT_MODE"] == "expanded"
        restored_exp = self._finish_flow(ns_exp, frozen_notebook)
        exp_root = Path(ns_exp["EXTRACT_ROOT"])

        assert restored_arch == restored_exp == 5
        assert _tree_sha256(arch_root / "data") == _tree_sha256(exp_root / "data")
        assert _tree_sha256(arch_root / "code") == _tree_sha256(exp_root / "code")
        assert not (exp_root / "kaggle_transport").exists()

    def test_expanded_mode_data_manifest_and_repo_hashes_pass(self, tmp_path: Path) -> None:
        output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "exphash"
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        ns = self._provision(sim_input, tmp_path / "working", frozen_notebook)
        self._finish_flow(ns, frozen_notebook)
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
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "expdry"
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        ns = self._provision(sim_input, tmp_path / "working", frozen_notebook)
        self._finish_flow(ns, frozen_notebook)
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
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "tamper"
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
            self._provision(sim_input, tmp_path / "working", frozen_notebook)

    def test_expanded_mode_missing_sidecar_fails_closed(self, tmp_path: Path) -> None:
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "nosh"
        )
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        with pytest.raises(FileNotFoundError, match="missing SHA-256 sidecar"):
            self._provision(sim_input, tmp_path / "working", frozen_notebook)

    def test_both_archive_and_expanded_fail_closed(self, tmp_path: Path) -> None:
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "both"
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_archive(sim_input, archive)
        self._mount_expanded(sim_input, archive)
        with pytest.raises(RuntimeError, match="BOTH an original archive"):
            self._provision(sim_input, tmp_path / "working", frozen_notebook)

    def test_two_expanded_candidates_fail_closed(self, tmp_path: Path) -> None:
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "twoexp"
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
            self._provision(sim_input, tmp_path / "working", frozen_notebook)

    def test_no_input_shape_fails_closed(self, tmp_path: Path) -> None:
        _output_root, _archive = _build(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "noinput"
        )
        sim_input = tmp_path / "kaggle_input"
        with pytest.raises(FileNotFoundError, match="Cannot find"):
            self._provision(sim_input, tmp_path / "working", CANONICAL_NOTEBOOK)

    def test_non_empty_extract_root_fails_closed(self, tmp_path: Path) -> None:
        _output_root, archive, frozen_notebook = _build_frozen(
            tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "nonempty"
        )
        sim_input = tmp_path / "kaggle_input"
        self._mount_expanded(sim_input, archive)
        working = tmp_path / "working"
        (working / "pilot_bundle").mkdir(parents=True)
        (working / "pilot_bundle" / "stale.txt").write_text("x", encoding="utf-8")
        with pytest.raises(RuntimeError, match="refusing to reuse a non-empty"):
            self._provision(sim_input, working, frozen_notebook)

    @pytest.mark.skipif(
        not _dist_artifact_is_current_release(),
        reason="current frozen Pilot artifact under dist/ is not the current release tag",
    )
    def test_real_kaggle_artifact_expanded_simulation(self, tmp_path: Path) -> None:
        """Full real-mount simulation against the frozen dist/ artifact.

        The dist archive is the exact frozen upload (replaced by the v0.9.12
        tagged rebuild at finalization). The notebook source used for the
        setup/verify cells is the canonical notebook, which the finalizer
        freezes with the real anchors; NO identity values are injected. The
        verify cell must pass against the artifact as-is: 50 transport blobs
        restored, manifests verified, repo hashes verified, and the exact
        48-cell dry-run passes.
        """
        sha = hashlib.sha256(DIST_ARTIFACT.read_bytes()).hexdigest()
        sim_input = tmp_path / "kaggle_input"
        dataset = self._make_dataset_dir(sim_input)
        with zipfile.ZipFile(DIST_ARTIFACT) as zf:
            zf.extractall(dataset / "pilot-kaggle-upload")
        (dataset / "pilot-kaggle-upload.zip.sha256").write_text(sha, encoding="utf-8")
        ns = self._provision(sim_input, tmp_path / "working", CANONICAL_NOTEBOOK)
        assert ns["PILOT_INPUT_MODE"] == "expanded"
        restored = self._finish_flow(ns, CANONICAL_NOTEBOOK)
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
            source_tag=PILOT_SOURCE_TAG,
            created_utc="2026-08-13T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            report_path=tmp_path / "freeze-report.json",
        )
        first = mod.freeze(**common)
        assert first["status"] == "FROZEN"
        assert first["frozen_source_tag"] == PILOT_SOURCE_TAG
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
        assert written["FROZEN_SOURCE_TAG"] == PILOT_SOURCE_TAG
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
        assert values["FROZEN_SOURCE_TAG"] == PILOT_SOURCE_TAG
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


STALE_CODE_MANIFEST_SHA = "99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96"


def _tamper_notebook(
    src: Path,
    dest: Path,
    *,
    source_tag: str | None = None,
    deployment_fields: dict[str, Any] | None = None,
    manifest_hashes: dict[str, str] | None = None,
) -> Path:
    """Copy a notebook and tamper its frozen trust anchors (byte-safe, JSON-roundtrip)."""
    nb = json.loads(src.read_text(encoding="utf-8"))
    setup = next(c for c in nb["cells"] if c.get("id") == "setup-cell")
    text = setup["source"]
    text = text if isinstance(text, str) else "".join(text)
    if source_tag is not None:
        new, n = re.subn(
            r'FROZEN_SOURCE_TAG = "[^"]*"',
            f'FROZEN_SOURCE_TAG = "{source_tag}"',
            text,
        )
        assert n == 1, "FROZEN_SOURCE_TAG pattern not found"
        text = new
    if deployment_fields:
        match = re.search(r"(FROZEN_DEPLOYMENT\s*=\s*\{.*?\})", text, re.DOTALL)
        assert match is not None, "FROZEN_DEPLOYMENT block not found"
        block = match.group(1)
        new_block = block
        for key, value in deployment_fields.items():
            new_block, n = re.subn(
                rf'"{key}":\s*[^,}}]+',
                f'"{key}": {value}',
                new_block,
            )
            assert n == 1, f"deployment field {key!r} not found"
        text = text.replace(block, new_block)
    if manifest_hashes:
        match = re.search(r"(FROZEN_MANIFEST_HASHES\s*=\s*\{.*?\})", text, re.DOTALL)
        assert match is not None, "FROZEN_MANIFEST_HASHES block not found"
        block = match.group(1)
        new_block = block
        for key, value in manifest_hashes.items():
            new_block, n = re.subn(
                rf'"{key}":\s*"[0-9a-fA-F]*"',
                f'"{key}": "{value}"',
                new_block,
            )
            assert n == 1, f"manifest hash {key!r} not found"
        text = text.replace(block, new_block)
    setup["source"] = text.splitlines(keepends=True) if "\n" in text else text
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    return dest


class TestPilotReleaseTrustGate:
    """Release trust gate regression suite (Gates 1, 3, 4 of v0.9.10 closure).

    Gate 1: a bundle whose embedded frozen code-manifest hash is stale (the
    exact v0.9.9 value) MUST fail the normal ``build_pilot_bundle`` gate.
    Gate 3: the finalizer repairs a stale code anchor in one pass, the real
    setup+verify cells then pass with NO identity injection, and a second run
    is byte-idempotent.
    Gate 4: the builder gate predicate rejects every tampered anchor
    (tag / deployment field / code / data / repo / transport) and accepts a
    finalized notebook.
    """

    @staticmethod
    def _build_validated(
        tmp_path: Path,
        label: str,
        notebook: Path,
        source_tag: str = PILOT_SOURCE_TAG,
    ) -> dict[str, Any]:
        return pilot_builder.build_pilot_bundle(
            output_root=tmp_path / f"pilot-upload-{label}",
            archive_path=tmp_path / f"pilot-upload-{label}.zip",
            source_commit="a" * 40,
            source_tag=source_tag,
            created_utc="2026-08-13T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            notebook=notebook,
            validate_notebook_trust=True,
            verify_source_provenance=False,
        )

    def test_gate1_stale_code_anchor_fails_release_build(self, tmp_path: Path) -> None:
        """Exact v0.9.9 regression: stale embedded code hash + zero placeholders."""
        tampered = _tamper_notebook(
            CANONICAL_NOTEBOOK,
            tmp_path / "gate1" / "pilot_exec_01.ipynb",
            manifest_hashes={
                "code_manifest_sha256": STALE_CODE_MANIFEST_SHA,
                "data_manifest_sha256": "0" * 64,
                "repository_snapshot_manifest_sha256": "0" * 64,
                "kaggle_transport_path_map_sha256": "0" * 64,
            },
        )
        with pytest.raises(RuntimeError) as exc:
            self._build_validated(tmp_path, "gate1", tampered)
        msg = str(exc.value)
        assert "PILOT DEPLOYMENT MANIFEST/MAP SHA MISMATCH" in msg
        assert "code_manifest_sha256" in msg
        assert STALE_CODE_MANIFEST_SHA in msg

    def test_gate3_finalizer_repairs_stale_anchor_and_verifies_without_injection(
        self, tmp_path: Path
    ) -> None:
        """One freeze pass repairs a stale code anchor; real cells then pass cleanly."""
        stale = _tamper_notebook(
            CANONICAL_NOTEBOOK,
            tmp_path / "gate3-stale" / "pilot_exec_01.ipynb",
            manifest_hashes={"code_manifest_sha256": STALE_CODE_MANIFEST_SHA},
        )
        mod = _load_finalizer()
        frozen_nb = tmp_path / "gate3-frozen" / "pilot_exec_01.ipynb"
        frozen_nb.parent.mkdir(parents=True, exist_ok=True)
        frozen_nb.write_bytes(stale.read_bytes())
        output_root = tmp_path / "pilot-upload-gate3"
        archive = tmp_path / "pilot-upload-gate3.zip"
        report = mod.freeze(
            notebook_path=frozen_nb,
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag=PILOT_SOURCE_TAG,
            created_utc="2026-08-13T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            report_path=tmp_path / "gate3-report.json",
        )
        assert report["status"] == "FROZEN"
        assert report["frozen_manifest_hashes"]["code_manifest_sha256"] != STALE_CODE_MANIFEST_SHA
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        assert (
            report["frozen_manifest_hashes"]["code_manifest_sha256"]
            == identity["code_manifest_sha256"]
        )

        mount = TestPilotKaggleExpandedMount()
        sim_input = tmp_path / "kaggle_input"
        mount._mount_expanded(sim_input, archive)
        ns = mount._provision(sim_input, tmp_path / "working", frozen_nb)
        assert ns["PILOT_INPUT_MODE"] == "expanded"
        restored = mount._finish_flow(ns, frozen_nb)
        assert restored == 5, f"expected 5 hermetic unsafe-file seeds, got {restored}"

        frozen_bytes = frozen_nb.read_bytes()
        second = mod.freeze(
            notebook_path=frozen_nb,
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag=PILOT_SOURCE_TAG,
            created_utc="2026-08-13T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            report_path=tmp_path / "gate3-report-2.json",
        )
        assert second["status"] == "FROZEN"
        assert second["frozen_manifest_hashes"] == report["frozen_manifest_hashes"]
        assert second["archive_sha256"] == report["archive_sha256"]
        assert frozen_nb.read_bytes() == frozen_bytes

    @pytest.mark.parametrize(
        ("tamper_kwargs", "expected_fragment"),
        [
            ({"source_tag": "v9.9.9-pilot-exec-ready"}, "FROZEN_SOURCE_TAG"),
            ({"deployment_fields": {"expected_cells": 47}}, "FROZEN_DEPLOYMENT"),
            ({"manifest_hashes": {"code_manifest_sha256": "0" * 64}}, "code_manifest_sha256"),
            ({"manifest_hashes": {"data_manifest_sha256": "0" * 64}}, "data_manifest_sha256"),
            (
                {"manifest_hashes": {"repository_snapshot_manifest_sha256": "0" * 64}},
                "repository_snapshot_manifest_sha256",
            ),
            (
                {"manifest_hashes": {"kaggle_transport_path_map_sha256": "0" * 64}},
                "kaggle_transport_path_map_sha256",
            ),
        ],
    )
    def test_gate4_every_tampered_anchor_fails(
        self, tmp_path: Path, tamper_kwargs: dict[str, Any], expected_fragment: str
    ) -> None:
        tampered = _tamper_notebook(
            CANONICAL_NOTEBOOK,
            tmp_path / "gate4" / "pilot_exec_01.ipynb",
            **tamper_kwargs,
        )
        with pytest.raises(RuntimeError) as exc:
            self._build_validated(tmp_path, "gate4", tampered)
        msg = str(exc.value)
        assert expected_fragment in msg

    def test_gate4_finalized_notebook_passes_builder_gate(self, tmp_path: Path) -> None:
        """A properly finalized notebook builds cleanly through the gate."""
        _output_root, archive, frozen_nb = _build_frozen(
            tmp_path, "2026-08-13T12:00:00+00:00", "a" * 40, "gate4pass"
        )
        identity = self._build_validated(tmp_path, "gate4pass", frozen_nb)
        assert identity["source_tag"] == PILOT_SOURCE_TAG
        assert len(identity["code_manifest_sha256"]) == 64


class TestD96NoGitHubLaunchRuntimeDependency:
    """PILOT-EXEC-01 D9.6: the runtime upload artifact contains NO GitHub launch
    dependency. The bundled code and notebook carry the local-evidence-only
    launch authorization contract - no git/ls-remote, no remote tag-peel gate,
    no GITHUB_TOKEN, no credential or network helper."""

    FORBIDDEN_RUNTIME_FRAGMENTS = (
        "verify_remote_annotated_tag_peel",
        "KAGGLE_PUBLIC_CANONICAL_REMOTE",
        "REMOTE_TAG_PROOF_TIMEOUT_SECONDS",
        "ls-remote",
        "github.com",
        "GITHUB_TOKEN",
        "ghp_",
        "PersonalAccessToken",
        "urlopen",
        "git clone",
        "git fetch",
        "git tag",
        "git rev-parse",
        "git -C",
    )

    def _bundled_sources(self, tmp_path: Path) -> tuple[Path, str, str, str]:
        output_root, _archive = _build(
            tmp_path, "2026-08-29T00:00:00+00:00", "c" * 40, "d96bundle"
        )
        preflight = output_root / "code" / "src" / "benchmark" / "execution" / "preflight.py"
        entry = output_root / "code" / "seven_arm_benchmark.py"
        notebook = output_root / "notebooks" / "pilot_exec_01.ipynb"
        assert preflight.is_file(), preflight
        assert entry.is_file(), entry
        assert notebook.is_file(), notebook
        return (
            output_root,
            preflight.read_text(encoding="utf-8"),
            entry.read_text(encoding="utf-8"),
            notebook.read_text(encoding="utf-8"),
        )

    def test_bundled_runtime_code_has_no_github_launch_machinery(
        self, tmp_path: Path
    ) -> None:
        _root, preflight_src, entry_src, _nb_src = self._bundled_sources(tmp_path)
        for name, src in (
            ("bundled preflight.py", preflight_src),
            ("bundled seven_arm_benchmark.py", entry_src),
        ):
            for fragment in self.FORBIDDEN_RUNTIME_FRAGMENTS:
                assert fragment not in src, (
                    f"{name} contains forbidden runtime fragment {fragment!r}"
                )

    def test_bundled_notebook_launch_cells_have_local_only_authorization(
        self, tmp_path: Path
    ) -> None:
        _root, _preflight_src, _entry_src, nb_src = self._bundled_sources(tmp_path)
        nb = json.loads(nb_src)
        cells = {c.get("id", ""): c for c in nb["cells"]}
        for cid in ("pilot-launch-cell", "pilot-resume-cell"):
            src = cells[cid]["source"]
            cell_src = src if isinstance(src, str) else "".join(src)
            for fragment in self.FORBIDDEN_RUNTIME_FRAGMENTS:
                assert fragment not in cell_src, (
                    f"bundled {cid} contains forbidden fragment {fragment!r}"
                )
            assert "validate_pilot_launch_authorization(" in cell_src
            assert not re.search(r"\bgit\b", cell_src)


class TestPilotBundleKeepsMarkdownNavigation:
    """PILOT-EXEC-01 label-closure: a future finalizer/bundle build must never
    drop the Markdown navigation cells. Proves the frozen (two-pass finalizer)
    bundled notebook still carries all 11 navigation Markdown cells with the
    exact ids, correct cell types, and the exact expected interspersed order."""

    MARKDOWN_NAV = {
        "pilot-step-00-session-setup-md": "setup-cell",
        "pilot-step-01-artifact-identity-md": "pilot-archive-verify-cell",
        "pilot-step-02-runtime-repository-setup-md": "install-lock-cell",
        "pilot-step-03-repository-preflight-md": "pilot-repo-preflight-cell",
        "pilot-step-04-gpu-model-input-md": "gpu-verify-cell",
        "pilot-step-05-model-preflight-md": "model-preflight-cell",
        "pilot-step-06-hf-secret-md": "secrets-cell",
        "pilot-step-07-pilot-canary-md": "pilot-canary-cell",
        "pilot-step-08-dryrun-md": "dryrun-cell",
        "pilot-step-09-launch-md": "pilot-launch-cell",
        "pilot-step-10-resume-md": "pilot-resume-cell",
        "pilot-step-11-verify-export-md": "pilot-verify-cell",
    }

    @staticmethod
    def _src(cell: dict[str, Any]) -> str:
        src = cell.get("source", "")
        return src if isinstance(src, str) else "".join(src)

    def test_frozen_bundle_retains_markdown_navigation(self, tmp_path: Path) -> None:
        _output_root, archive, _frozen_notebook = _build_frozen(
            tmp_path, "2026-08-29T12:00:00+00:00", "a" * 40, "mdnav"
        )
        with zipfile.ZipFile(archive) as zf:
            bundled = json.loads(zf.read("notebooks/pilot_exec_01.ipynb").decode("utf-8"))
        cells = bundled["cells"]
        ids = [c.get("id", "") for c in cells]
        for md_id, code_id in self.MARKDOWN_NAV.items():
            assert md_id in ids, f"finalizer dropped Markdown navigation cell {md_id}"
            i = ids.index(md_id)
            assert cells[i].get("cell_type") == "markdown"
            assert ids[i + 1] == code_id, (
                f"{md_id} must immediately precede {code_id}, precedes {ids[i + 1]}"
            )
        # No navigation cell may be duplicated and the code order is preserved.
        from collections import Counter

        dupes = [i for i, n in Counter(ids).items() if n != 1 and i in self.MARKDOWN_NAV]
        assert dupes == [], f"duplicate navigation ids in frozen bundle: {dupes}"
        code_ids = [c.get("id", "") for c in cells if c.get("cell_type") == "code"]
        assert code_ids == [
            "setup-cell",
            "pilot-archive-verify-cell",
            "transport-restore-cell",
            "pilot-identity-verify-cell",
            "install-lock-cell",
            "pilot-snapshot-verify-cell",
            "service-bootstrap-cell",
            "pilot-repo-preflight-cell",
            "gpu-verify-cell",
            "model-preflight-cell",
            "secrets-cell",
            "pilot-canary-cell",
            "dryrun-cell",
            "pilot-launch-cell",
            "pilot-resume-cell",
            "pilot-verify-cell",
            "pilot-export-cell",
        ]

    def test_frozen_bundle_navigation_headings_exact(self, tmp_path: Path) -> None:
        _output_root, archive, _frozen_notebook = _build_frozen(
            tmp_path, "2026-08-29T12:00:00+00:00", "a" * 40, "mdnavh"
        )
        with zipfile.ZipFile(archive) as zf:
            bundled = json.loads(zf.read("notebooks/pilot_exec_01.ipynb").decode("utf-8"))
        cells = {c.get("id", ""): c for c in bundled["cells"]}
        expected = {
            "pilot-step-00-session-setup-md": "## 0. Session Setup",
            "pilot-step-01-artifact-identity-md": "## 1. Artifact and Identity Verification",
            "pilot-step-02-runtime-repository-setup-md": "## 2. Runtime and Repository Setup",
            "pilot-step-03-repository-preflight-md": (
                "## 3. Repository Preflight, Heartbeat, and GQA Microprobe"
            ),
            "pilot-step-04-gpu-model-input-md": "## 4. GPU and Qwen Input Verification",
            "pilot-step-05-model-preflight-md": "## 5. Model Preflight Only",
            "pilot-step-06-hf-secret-md": "## 6. Hugging Face Results Secret",
            "pilot-step-07-pilot-canary-md": (
                "## 7. Pilot-Canary \u2014 Real End-to-End Gate (D10.3)"
            ),
            "pilot-step-08-dryrun-md": "## 8. Exact-Artifact 48-Cell Dry Run",
            "pilot-step-09-launch-md": (
                "## 9. Pilot Launch \u2014 STOP Until Stable Tag Is Confirmed"
            ),
            "pilot-step-10-resume-md": "## 10. Resume After External Interruption Only",
            "pilot-step-11-verify-export-md": "## 11. Final Verification and Export",
        }
        for md_id, heading in expected.items():
            assert md_id in cells, f"missing navigation cell in frozen bundle: {md_id}"
            assert heading in self._src(cells[md_id]), (
                f"{md_id} heading missing/incorrect in frozen bundle"
            )
        # Frozen source tag must still be present after the two-pass freeze.
        setup = "".join(self._src(cells["setup-cell"]))
        assert 'FROZEN_SOURCE_TAG = "v0.9.22-d10-candidate"' in setup
