"""PILOT-EXEC-01: real-launch validation preflight integration contract.

Proves (03_VALIDATION_CONTRACT.md, 05_REAL_PREBENCHMARK_GATE Pipeline Smoke
Test) that:

- every selected repository enters the shared preflight path with its frozen
  validation command and a pristine staged snapshot as cwd;
- the shared preflight is fail-closed on services: an unreachable declared
  required service (PostgreSQL/Valkey for Saleor) FAILS the repository even when
  every command would pass;
- the returned record distinguishes service checks, command checks and the
  overall pass;
- a real end-to-end preflight of the (fast, embedded) Todo repository PASSes
  with no network and no developer-local cache.

The Saleor/django CMS real preflights require external services
(PostgreSQL/Valkey) and their full dependency environments; those are executed
as explicit Gate 8/9 evidence outside this hermetic test (see the closure
ledger). The default suite never touches ``_workspace/cache`` or the network.
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

PILOT_REPOSITORIES = ("todo", "djangocms", "saleor")

PINNED_SHAS = {
    "todo": "b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
    "djangocms": "0f633fc9fa213357f4202482aab2b0edad680f95",
    "saleor": "e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
}

# Gate-C service topology (proved by preflight): PostgreSQL 127.0.0.1:5433,
# Valkey/Redis 127.0.0.1:6379. Distinct from the earlier local readiness record
# (Valkey 6380); never claimed to be the same topology.
POSTGRES_URL = "postgres://saleor:saleor@127.0.0.1:5433/saleor"
VALKEY_URL = "redis://127.0.0.1:6379/0"


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


def _stub_materialization(monkeypatch: Any) -> list[str]:
    """Stub git-checkout materialization with a deterministic local stage.

    The staged directory receives no real files; command execution is itself
    stubbed by the caller, so this only proves wiring and fail-closed logic.
    """
    materialized: list[str] = []

    def fake_materialize(
        pin: Any,
        repo_cache: Path | None,
        target_dir: Path,
        *,
        allow_acquire: bool = False,
    ) -> Any:
        materialized.append(pin.repo_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        return snapshot_mod.SnapshotEvidence(
            repo_id=pin.repo_id,
            mode="hermetic",
            requested_sha=pin.commit_sha,
            resolved_head="hermetic",
            file_count=0,
            content_hash="hermetic",
            size_bytes=0,
        )

    monkeypatch.setattr(snapshot_mod, "materialize_repository", fake_materialize)
    monkeypatch.setattr(
        snapshot_mod,
        "apply_windows_infra_workarounds",
        lambda staged_dir, repo_id: [],
    )
    return materialized


def _stub_run_command(monkeypatch: Any, *, passed: bool) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_run(argv: list[str], cwd: Path, env: dict[str, str], timeout: int, label: str) -> dict[str, Any]:
        calls.append({"argv": argv, "cwd": Path(cwd), "label": label})
        return {
            "label": label,
            "command": argv,
            "passed": passed,
            "exit_code": 0 if passed else 1,
            "duration_seconds": 0.001,
            "output_tail": "stubbed",
        }

    monkeypatch.setattr(snapshot_mod, "_run_command", fake_run)
    return calls


def _stub_service_reachability(monkeypatch: Any, unreachable: set[str] | None = None) -> None:
    unreachable = set(unreachable or ())

    def fake_reachable(url: str) -> bool:
        return url not in unreachable

    monkeypatch.setattr(snapshot_mod, "_service_reachable", fake_reachable)


def _hermetic_preflight(tmp_path: Path, monkeypatch: Any, *, repos: tuple[str, ...]) -> dict[str, Any]:
    _stub_materialization(monkeypatch)
    _stub_run_command(monkeypatch, passed=True)
    _stub_service_reachability(monkeypatch, unreachable=set())
    return snapshot_mod.run_preflight(
        manifest_path=FROZEN_MANIFEST,
        staging_root=tmp_path / "staged",
        repo_cache=None,
        venv_pythons={repo: "/opt/venv/bin/python" for repo in repos},
        repos=repos,
        timeout=60,
    )


class TestSnapshotMaterializationHermetic:
    def test_embedded_todo_materializes_without_cache_or_network(self, tmp_path: Path) -> None:
        pin = next(p for p in snapshot_mod.DEFAULT_PINS if p.repo_id == "todo")
        target = tmp_path / "materialized-todo"
        evidence = snapshot_mod.materialize_repository(
            pin, repo_cache=None, target_dir=target
        )
        assert evidence.repo_id == "todo"
        assert evidence.mode == "embedded"
        assert evidence.requested_sha == PINNED_SHAS["todo"]
        assert evidence.file_count > 0
        assert not (target / ".git").exists()

    def test_materialized_todo_matches_embedded_source(self, tmp_path: Path) -> None:
        canonical = snapshot_mod.EMBEDDED_TODO_SOURCE
        assert snapshot_mod._tree_content_hash(canonical) == snapshot_mod._tree_content_hash(
            canonical
        )

    def test_hermetic_preflight_uses_repo_source_evidence(self, tmp_path: Path) -> None:
        source = tmp_path / "bundled-todo"
        source.mkdir()
        (source / "marker.py").write_text("x = 1\n", encoding="utf-8")
        result = snapshot_mod.run_repo_preflight(
            repo_id="todo",
            staging_dir=tmp_path / "staged-todo",
            repo_cache=None,
            venv_python=sys.executable,
            command=command_map.require("todo"),
            timeout=60,
            repo_source=source,
        )
        assert result["mode"] == "bundled"
        assert result["resolved_head"] == "bundled"
        assert result["file_count"] == 1
        assert (tmp_path / "staged-todo" / "marker.py").is_file()


class TestPreflightRunnerPath:
    def test_every_repo_enters_preflight_with_frozen_command(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        calls = _stub_run_command(monkeypatch, passed=True)
        _stub_materialization(monkeypatch)
        _stub_service_reachability(monkeypatch, unreachable=set())
        staged_roots = {repo: tmp_path / "staged" / repo for repo in PILOT_REPOSITORIES}
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
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
        _stub_materialization(monkeypatch)
        _stub_run_command(monkeypatch, passed=False)
        _stub_service_reachability(monkeypatch, unreachable=set())
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
            venv_pythons={repo: "/opt/venv/bin/python" for repo in PILOT_REPOSITORIES},
            repos=PILOT_REPOSITORIES,
            timeout=60,
        )
        assert result["overall"] == "FAIL"
        assert all(
            not entry["passed"] for entry in result["repositories"].values()
        )
        for repo_id in PILOT_REPOSITORIES:
            assert result["repositories"][repo_id]["command_passed"] is False

    def test_real_todo_preflight_passes_end_to_end(self, tmp_path: Path) -> None:
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
            venv_pythons={"todo": sys.executable},
            repos=("todo",),
            timeout=300,
        )
        assert result["overall"] == "PASS"
        todo = result["repositories"]["todo"]
        assert todo["passed"] is True
        primary = todo["commands"][0]
        assert primary["exit_code"] == 0


class TestServiceFailClosed:
    def test_required_postgres_unreachable_fails(self, tmp_path: Path, monkeypatch: Any) -> None:
        _stub_materialization(monkeypatch)
        _stub_run_command(monkeypatch, passed=True)
        _stub_service_reachability(monkeypatch, unreachable={POSTGRES_URL})
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
            venv_pythons={repo: "/opt/venv/bin/python" for repo in PILOT_REPOSITORIES},
            repos=PILOT_REPOSITORIES,
            timeout=60,
        )
        assert result["overall"] == "FAIL"
        saleor = result["repositories"]["saleor"]
        assert saleor["command_passed"] is True
        assert saleor["services_passed"] is False
        assert saleor["passed"] is False
        assert saleor["services"] == [
            {"name": "postgresql", "url_scheme": "postgres", "required": True, "reachable": False},
            {"name": "valkey", "url_scheme": "redis", "required": True, "reachable": True},
        ]

    def test_required_valkey_unreachable_fails(self, tmp_path: Path, monkeypatch: Any) -> None:
        _stub_materialization(monkeypatch)
        _stub_run_command(monkeypatch, passed=True)
        _stub_service_reachability(monkeypatch, unreachable={VALKEY_URL})
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
            venv_pythons={repo: "/opt/venv/bin/python" for repo in PILOT_REPOSITORIES},
            repos=("saleor",),
            timeout=60,
        )
        assert result["overall"] == "FAIL"
        saleor = result["repositories"]["saleor"]
        assert saleor["command_passed"] is True
        assert saleor["services_passed"] is False
        assert saleor["passed"] is False

    def test_both_services_reachable_and_commands_pass_passes(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        result = _hermetic_preflight(tmp_path, monkeypatch, repos=("saleor",))
        assert result["overall"] == "PASS"
        saleor = result["repositories"]["saleor"]
        assert saleor["command_passed"] is True
        assert saleor["services_passed"] is True
        assert saleor["passed"] is True

    def test_repo_without_services_passes_without_probes(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        _stub_materialization(monkeypatch)
        _stub_run_command(monkeypatch, passed=True)
        calls: list[str] = []

        def fake_reachable(url: str) -> bool:
            calls.append(url)
            raise AssertionError(f"unexpected service probe: {url}")

        monkeypatch.setattr(snapshot_mod, "_service_reachable", fake_reachable)
        result = snapshot_mod.run_preflight(
            manifest_path=FROZEN_MANIFEST,
            staging_root=tmp_path / "staged",
            repo_cache=None,
            venv_pythons={"todo": "/opt/venv/bin/python"},
            repos=("todo",),
            timeout=60,
        )
        assert result["overall"] == "PASS"
        todo = result["repositories"]["todo"]
        assert todo["passed"] is True
        assert todo["services"] == []
        assert not calls

    def test_service_evidence_appears_in_returned_record(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        result = _hermetic_preflight(tmp_path, monkeypatch, repos=("saleor",))
        saleor = result["repositories"]["saleor"]
        service_names = {entry["name"] for entry in saleor["services"]}
        assert service_names == {"postgresql", "valkey"}
        assert all(entry["required"] for entry in saleor["services"])
        assert all(entry["reachable"] for entry in saleor["services"])

    def test_missing_repo_source_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError):
            snapshot_mod.run_repo_preflight(
                repo_id="todo",
                staging_dir=tmp_path / "staged-todo",
                repo_cache=None,
                venv_python=sys.executable,
                command=command_map.require("todo"),
                timeout=60,
                repo_source=tmp_path / "does-not-exist",
            )


class TestMissingInterpreterFailsClosed:
    def test_missing_venv_python_for_selected_repo(self, tmp_path: Path, monkeypatch: Any) -> None:
        _stub_materialization(monkeypatch)
        _stub_run_command(monkeypatch, passed=True)
        with pytest.raises(RuntimeError):
            snapshot_mod.run_preflight(
                manifest_path=FROZEN_MANIFEST,
                staging_root=tmp_path / "staged",
                repo_cache=None,
                venv_pythons={"todo": sys.executable},
                repos=PILOT_REPOSITORIES,
                timeout=60,
            )
