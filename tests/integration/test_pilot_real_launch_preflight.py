"""PILOT-EXEC-01: real-launch validation preflight integration contract.

Proves (03_VALIDATION_CONTRACT.md, 05_REAL_PREBENCHMARK_GATE Pipeline Smoke
Test) with real or faithful local fixtures that:

- all three pinned Pilot repository snapshots materialize from their exact
  immutable commits into a pristine staging area;
- every selected repository enters the validation preflight path with its
  frozen validation command and the pristine staged snapshot as cwd;
- a real end-to-end preflight of the (fast) Todo repository PASSes;
- the preflight result fails closed per repository when a frozen command
  fails.

The Saleor/django CMS preflights require external services (PostgreSQL/Valkey)
and their full dependency environments; those are executed as real gate
evidence outside this fast integration test (see the closure ledger).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
FROZEN_MANIFEST = PROJECT_DIR / "benchmark_data" / "manifests" / "pilot_validation_commands.yaml"

# Reusable git-checkout acquisition cache for the external pinned repositories
# (django CMS, Saleor). Kept outside the bundle.
REPO_CACHE = PROJECT_DIR.parent / "_workspace" / "cache" / "repositories"

PILOT_REPOSITORIES = ("todo", "djangocms", "saleor")

PINNED_SHAS = {
    "todo": "b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
    "djangocms": "0f633fc9fa213357f4202482aab2b0edad680f95",
    "saleor": "e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
}


def _load_snapshot_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "pilot_repo_snapshot_under_test",
        str(SCRIPTS_DIR / "pilot_repo_snapshot.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_command_map() -> Any:
    from benchmark.repositories.validation_commands import load_validation_commands

    return load_validation_commands(FROZEN_MANIFEST)


snapshot_mod = _load_snapshot_module()
command_map = _load_command_map()


@pytest.fixture(scope="module")
def materialized(tmp_path_factory: Any) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("pilot-materialized")
    data_repositories = root / "data" / "repositories"
    evidence = snapshot_mod.materialize_repositories(
        data_repositories_dir=data_repositories,
        repo_cache=REPO_CACHE,
        allow_acquire=True,
    )
    return data_repositories, evidence


class TestSnapshotMaterialization:
    def test_all_three_pinned_snapshots_materialize(self, materialized: Any) -> None:
        data_repositories, evidence = materialized
        assert set(evidence) == set(PILOT_REPOSITORIES)
        for repo_id, pin_sha in PINNED_SHAS.items():
            entry = evidence[repo_id]
            assert entry["requested_sha"] == pin_sha
            if repo_id == "todo":
                assert entry["mode"] == "embedded"
                assert entry["resolved_head"] == "embedded"
            else:
                assert entry["resolved_head"] == pin_sha, (
                    f"{repo_id} resolved to {entry['resolved_head']}, expected {pin_sha}"
                )
            assert entry["file_count"] > 0
            assert entry["content_hash"]
            staged_root = data_repositories / repo_id
            assert staged_root.is_dir()
            assert not (staged_root / ".git").exists()

    def test_materialized_todo_matches_embedded_source(self, materialized: Any) -> None:
        _, evidence = materialized
        canonical = snapshot_mod.EMBEDDED_TODO_SOURCE
        assert snapshot_mod._tree_content_hash(canonical) == evidence["todo"]["content_hash"]


class TestPreflightRunnerPath:
    def _staged_roots(self, tmp_path: Path) -> dict[str, Path]:
        staging_root = tmp_path / "staged"
        staging_root.mkdir()
        return {repo: staging_root / repo for repo in PILOT_REPOSITORIES}

    def test_every_repo_enters_preflight_with_frozen_command(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        calls: list[dict[str, Any]] = []

        def fake_run(argv: list[str], cwd: Path, env: dict[str, str], timeout: int, label: str) -> dict[str, Any]:
            calls.append({"argv": argv, "cwd": Path(cwd), "label": label})
            return {
                "label": label,
                "command": argv,
                "passed": True,
                "exit_code": 0,
                "duration_seconds": 0.001,
                "output_tail": "stubbed",
            }

        monkeypatch.setattr(snapshot_mod, "_run_command", fake_run)
        staged_roots = self._staged_roots(tmp_path)
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=REPO_CACHE,
            venv_pythons={repo: "/opt/venv/bin/python" for repo in PILOT_REPOSITORIES},
            repos=PILOT_REPOSITORIES,
            timeout=60,
        )
        assert result["overall"] == "PASS"
        assert set(result["repositories"]) == set(PILOT_REPOSITORIES)
        for repo_id in PILOT_REPOSITORIES:
            entry = result["repositories"][repo_id]
            assert entry["passed"] is True
            frozen = command_map.require(repo_id)
            repo_calls = [c for c in calls if c["cwd"] == staged_roots[repo_id]]
            assert repo_calls, f"repo '{repo_id}' never entered the preflight path"
            primary = next(c for c in repo_calls if c["label"] == "primary")
            assert tuple(primary["argv"]) == frozen.resolve_interpreter("/opt/venv/bin/python"), (
                f"repo '{repo_id}' ran a different frozen command: {primary['argv']}"
            )

    def test_preflight_fails_closed_on_failing_command(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        def fake_run(argv: list[str], cwd: Path, env: dict[str, str], timeout: int, label: str) -> dict[str, Any]:
            return {
                "label": label,
                "command": argv,
                "passed": False,
                "exit_code": 1,
                "duration_seconds": 0.001,
                "output_tail": "stubbed failure",
            }

        monkeypatch.setattr(snapshot_mod, "_run_command", fake_run)
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=REPO_CACHE,
            venv_pythons={repo: "/opt/venv/bin/python" for repo in PILOT_REPOSITORIES},
            repos=PILOT_REPOSITORIES,
            timeout=60,
        )
        assert result["overall"] == "FAIL"
        assert all(
            not entry["passed"] for entry in result["repositories"].values()
        )

    def test_real_todo_preflight_passes_end_to_end(self, tmp_path: Path) -> None:
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=REPO_CACHE,
            venv_pythons={"todo": sys.executable},
            repos=("todo",),
            timeout=300,
        )
        assert result["overall"] == "PASS"
        todo = result["repositories"]["todo"]
        assert todo["passed"] is True
        primary = todo["commands"][0]
        assert primary["exit_code"] == 0
        assert "passed" in primary["output_tail"] or primary["exit_code"] == 0


class TestMissingInterpreterFailsClosed:
    def test_missing_venv_python_for_selected_repo(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError):
            snapshot_mod.run_preflight(
                manifest_path=FROZEN_MANIFEST,
                staging_root=tmp_path / "staged",
                repo_cache=REPO_CACHE,
                venv_pythons={"todo": sys.executable},
                repos=PILOT_REPOSITORIES,
                timeout=60,
            )
