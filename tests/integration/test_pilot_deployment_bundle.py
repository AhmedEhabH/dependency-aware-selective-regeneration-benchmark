"""PILOT-EXEC-01: Pilot deployment bundle integration contract.

Proves the Pilot-specific deployment bundle builder produces a deterministic
Pilot deployment artifact from current canonical sources WITHOUT touching the
historical Scientific Smoke bundle (``kaggle_upload/``).

Covers the exact Pilot bundle contract from 02_PILOT_DEPLOYMENT_FREEZE.md:
output isolation, canonical-to-Pilot parity, frozen deployment identity,
no forbidden files, manifest verification, deterministic rebuilds, bundled
CLI import, and the bundled exact 48-cell ``--dry-run --profile pilot``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
HISTORICAL_SMOKE_UPLOAD = PROJECT_DIR / "kaggle_upload"

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
        source_tag="v0.9.1-pilot-exec-ready",
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
        assert identity["source_tag"] == "v0.9.1-pilot-exec-ready"
        assert identity["created_utc"] == "2026-08-10T00:00:00+00:00"

    def test_identity_manifest_hashes_match_emitted_bytes(self, tmp_path: Path) -> None:
        output_root, _archive = _build(tmp_path, "2026-08-10T00:00:00+00:00", "a" * 40, "mhash")
        identity = json.loads(
            (output_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
        )
        for key, manifest_name in (
            ("code_manifest_sha256", "code_manifest.json"),
            ("data_manifest_sha256", "data_manifest.json"),
        ):
            manifest_bytes = (output_root / manifest_name).read_bytes()
            assert identity[key] == hashlib.sha256(manifest_bytes).hexdigest(), (
                f"identity {key} does not match emitted {manifest_name}"
            )

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
