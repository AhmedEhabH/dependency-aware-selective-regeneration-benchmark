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
import json
import shutil
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from benchmark.repositories.validation_commands import FrozenValidationCommand

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


class TestBoundedCommandLogs:
    """SALEOR-DIAGNOSTICS: bounded full-output logs + relative ``log_path``."""

    def _fake_run(self, argv: list[str], **kwargs: object) -> types.SimpleNamespace:
        if argv[:2] == ["python", "-c"]:
            return types.SimpleNamespace(
                returncode=0,
                stdout='{"python_version": "3.11.0", "platform": "test"}',
                stderr="",
            )
        if "--lf" in argv:
            return types.SimpleNamespace(
                returncode=0, stdout="2 passed, 317 deselected, 1 skipped in 3.00s", stderr=""
            )
        if "--collect-only" in argv:
            return types.SimpleNamespace(returncode=0, stdout="collected 1 item", stderr="")
        body = "\n".join(f"line_{i:04d}" for i in range(400))
        return types.SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=(
                "=================== FAILURES ===================\n"
                f"{body}\n"
                "FAILED saleor/graphql/checkout/tests/test_checkout.py::test_one\n"
                "319 failed, 6056 passed, 1 skipped in 512.00s\n"
            ),
        )

    def test_run_command_persists_full_primary_log_beyond_tail_cap(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(snapshot_mod.subprocess, "run", self._fake_run)
        logs_dir = tmp_path / "logs"
        record = snapshot_mod._run_command(
            ["python", "-m", "pytest", "-q", "saleor/graphql/checkout/tests"],
            cwd=tmp_path,
            env={},
            timeout=30,
            label="primary",
            logs_dir=logs_dir,
            log_prefix="saleor",
        )
        assert record["passed"] is False
        assert record["exit_code"] == 1
        assert record["log_path"] == "logs/saleor-primary.log"
        log_file = logs_dir / "saleor-primary.log"
        assert log_file.is_file()
        content = log_file.read_text(encoding="utf-8")
        assert content.count("line_") == 400, "the full body must be persisted, not just the tail"
        assert "319 failed, 6056 passed" in content
        assert "line_0001" not in record["output_tail"], (
            "output_tail keeps only the last 25 lines; the persisted log must exceed it"
        )

    def test_bounded_log_cap_keeps_head_and_tail(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "bounded.log"
        text = "A" * 500 + "MIDDLE" + "Z" * 500
        snapshot_mod._write_bounded_log(text, path, limit=300)
        content = path.read_text(encoding="utf-8")
        assert content.startswith("A" * 100)
        assert content.endswith("Z" * 100)
        assert "[TRUNCATED" in content
        assert len(content) <= 300


class TestSaleorFailureDiagnostics:
    """SALEOR-DIAGNOSTICS: persist the primary failure artifact and prove the
    serial last-failed rerun never changes the primary verdict."""

    @staticmethod
    def _nodeids() -> tuple[str, ...]:
        return tuple(
            f"saleor/graphql/checkout/tests/test_checkout_{i % 64}.py::test_case_{i}"
            for i in range(319)
        )

    def _write_lastfailed(self, staging_dir: Path) -> None:
        cache = staging_dir / ".pytest_cache" / "v" / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "lastfailed").write_text(
            json.dumps(dict.fromkeys(self._nodeids(), True)), encoding="utf-8"
        )

    def _saleor_command(self) -> FrozenValidationCommand:
        return FrozenValidationCommand(
            repo_id="saleor",
            scenario_ids=("saleor-loc-001",),
            dependency_runtime="poetry",
            dependency_file="pyproject.toml",
            services=("postgresql", "valkey"),
            env=(
                ("DATABASE_URL", "postgres://saleor:saleor@127.0.0.1:5433/saleor"),
                ("REDIS_URL", "redis://127.0.0.1:6379/0"),
            ),
            command=("{python}", "-m", "pytest", "-q", "saleor/graphql/checkout/tests"),
            additional_commands=(("{python}", "-m", "pytest", "--collect-only", "-q"),),
            description="saleor baseline validation",
        )

    def _patch_runtime(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        base_fake_run = TestBoundedCommandLogs()._fake_run

        def _fake_run_with_gate(
            argv: list[str], **kwargs: object
        ) -> types.SimpleNamespace:
            gate_nodeid = (
                "saleor/graphql/checkout/tests/benchmark/"
                "test_checkout_mutations.py::test_create_checkout"
            )
            if gate_nodeid in argv:
                assert argv == [
                    "python",
                    "-m",
                    "pytest",
                    "-n",
                    "0",
                    "-x",
                    "--tb=line",
                    "--no-header",
                    "-q",
                    gate_nodeid,
                ]
                assert argv.count("-m") == 1
                assert "pytest" not in argv[3:]
                assert "saleor/graphql/checkout/tests" not in argv
                return types.SimpleNamespace(
                    returncode=0, stdout="1 passed in 0.50s", stderr=""
                )
            return base_fake_run(argv, **kwargs)

        monkeypatch.setattr(snapshot_mod.subprocess, "run", _fake_run_with_gate)
        monkeypatch.setattr(snapshot_mod, "_copy_embedded_tree", lambda source, target: None)
        monkeypatch.setattr(
            snapshot_mod, "_service_reachable", lambda url, timeout=5.0: True
        )

    def test_load_lastfailed_parses_319_checkout_nodeids(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        self._write_lastfailed(staging_dir)
        count, nodeids = snapshot_mod._load_lastfailed(staging_dir)
        assert count == 319
        assert len(nodeids) == 319
        assert all(n.startswith("saleor/graphql/checkout/tests") for n in nodeids)
        assert nodeids == tuple(sorted(nodeids))

    def test_load_lastfailed_missing_cache_returns_none(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        assert snapshot_mod._load_lastfailed(staging_dir) is None

    def test_run_repo_preflight_writes_diagnostics_without_touching_primary_verdict(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_runtime(monkeypatch)
        run_root = tmp_path / "run"
        staging_dir = run_root / "repo_staging" / "saleor"
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / "saleor" / "core").mkdir(parents=True, exist_ok=True)
        (staging_dir / "saleor" / "core" / "rlimit.py").write_text(
            "# dummy; contains: except ImportError\n", encoding="utf-8"
        )
        self._write_lastfailed(staging_dir)
        repo_source = tmp_path / "saleor-src"
        repo_source.mkdir()

        result = snapshot_mod.run_repo_preflight(
            repo_id="saleor",
            staging_dir=staging_dir,
            repo_cache=None,
            venv_python="python",
            command=self._saleor_command(),
            timeout=300,
            repo_source=repo_source,
            logs_dir=run_root / "logs",
            diagnostics_dir=run_root,
        )

        primary = result["commands"][0]
        assert primary["label"] == "primary"
        assert primary["passed"] is False
        assert primary["exit_code"] == 1
        assert primary["log_path"] == "logs/saleor-primary.log"
        primary_log = (run_root / "logs" / "saleor-primary.log").read_text(encoding="utf-8")
        assert "319 failed, 6056 passed, 1 skipped" in primary_log

        diag_path = run_root / "saleor_failure_diagnostics.json"
        assert diag_path.is_file()
        payload = json.loads(diag_path.read_text(encoding="utf-8"))
        assert payload["repo_id"] == "saleor"
        assert payload["primary_exit_code"] == 1
        assert payload["primary_command"][:2] == ["python", "-m"]
        assert payload["failed_count"] == 319
        assert payload["failed_nodeids"] == sorted(payload["failed_nodeids"])
        assert len(payload["failed_nodeids"]) == 319
        assert all(
            n.startswith("saleor/graphql/checkout/tests") for n in payload["failed_nodeids"]
        )
        assert payload["failures_by_source_file"]["saleor/graphql/checkout/tests/test_checkout_0.py"] > 0
        assert payload["failed_subtree_prefixes"] == ["saleor/graphql/checkout/tests"]
        assert payload["lastfailed_serial_status"] == "RAN"
        assert payload["lastfailed_serial_command"] == [
            "python",
            "-m",
            "pytest",
            "--lf",
            "-n",
            "0",
            "-x",
            "-vv",
            "--tb=long",
        ]
        assert payload["lastfailed_serial_exit_code"] == 0
        assert payload["lastfailed_serial_passed"] is True
        assert payload["lastfailed_serial_log_path"] == "logs/saleor-lastfailed-serial.log"
        assert payload["diagnostic_versions"]["python_version"] == "3.11.0"

        assert result["passed"] is False, "diagnostics must never flip the primary verdict"
        serial = [r for r in result["commands"] if r["label"] == "additional-1"]
        assert serial == [], "the serial rerun is diagnostic-only and not a declared command"

    # --- lastfailed-guard tests (audit delta) --------------------------------

    @staticmethod
    def _primary_record() -> dict[str, object]:
        return {
            "label": "primary",
            "command": ["python", "-m", "pytest", "-q"],
            "passed": False,
            "exit_code": 1,
            "log_path": "logs/saleor-primary.log",
        }

    def _call_diagnostics(
        self,
        monkeypatch: pytest.MonkeyPatch,
        staging_dir: Path,
        logs_dir: Path | None = None,
    ) -> dict[str, object]:
        spy_calls: list[str] = []
        _orig = snapshot_mod._run_lastfailed_serial

        def _spy(*args: object, **kwargs: object) -> dict[str, object]:
            spy_calls.append("called")
            return _orig(*args, **kwargs)  # type: ignore[no-any-return]

        monkeypatch.setattr(snapshot_mod, "_run_lastfailed_serial", _spy)
        diag = snapshot_mod._collect_saleor_failure_diagnostics(
            python="python",
            staging_dir=staging_dir,
            env={},
            timeout=30,
            primary=self._primary_record(),
            logs_dir=logs_dir,
        )
        return diag, spy_calls

    def test_missing_lastfailed_skips_serial_subprocess(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        diag, spy = self._call_diagnostics(monkeypatch, staging)
        assert spy == [], "no serial pytest invocation when lastfailed cache is absent"
        assert diag["lastfailed_serial_status"] == "SKIPPED_NO_LASTFAILED"
        assert diag["lastfailed_serial_command"] is None
        assert diag["lastfailed_serial_exit_code"] is None
        assert diag["lastfailed_serial_passed"] is None
        assert diag["failed_count"] == 0
        assert diag["failed_nodeids"] == []
        assert diag["lastfailed_cache_read"] is False

    def test_empty_lastfailed_skips_serial_subprocess(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        cache = staging / ".pytest_cache" / "v" / "cache"
        cache.mkdir(parents=True)
        (cache / "lastfailed").write_text("{}", encoding="utf-8")
        diag, spy = self._call_diagnostics(monkeypatch, staging)
        assert spy == [], "no serial pytest invocation when lastfailed cache is empty"
        assert diag["lastfailed_serial_status"] == "SKIPPED_NO_LASTFAILED"
        assert diag["failed_count"] == 0
        assert diag["lastfailed_cache_read"] is True

    def test_malformed_lastfailed_skips_serial_subprocess(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        cache = staging / ".pytest_cache" / "v" / "cache"
        cache.mkdir(parents=True)
        (cache / "lastfailed").write_text("[not-a-dict]", encoding="utf-8")
        diag, spy = self._call_diagnostics(monkeypatch, staging)
        assert spy == [], "no serial pytest invocation when lastfailed cache is malformed"
        assert diag["lastfailed_serial_status"] == "SKIPPED_NO_LASTFAILED"
        assert diag["failed_count"] == 0
        assert diag["lastfailed_cache_read"] is False

    def test_nonempty_lastfailed_runs_serial_subprocess(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        self._write_lastfailed(staging)
        diag, spy = self._call_diagnostics(monkeypatch, staging)
        assert spy == ["called"], "serial pytest must run when lastfailed is non-empty"
        assert diag["lastfailed_serial_status"] == "RAN"
        assert diag["lastfailed_serial_command"] is not None
        assert diag["failed_count"] == 319

    def test_all_guard_cases_keep_primary_verdict_fail(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Every possible lastfailed state must preserve the FAIL verdict."""

        def _write_empty_cache(d: Path) -> None:
            cache = d / ".pytest_cache" / "v" / "cache"
            cache.mkdir(parents=True)
            (cache / "lastfailed").write_text("{}", encoding="utf-8")

        def _write_bad_cache(d: Path) -> None:
            cache = d / ".pytest_cache" / "v" / "cache"
            cache.mkdir(parents=True)
            (cache / "lastfailed").write_text("bad", encoding="utf-8")

        setcases: list[tuple[str, Any]] = [
            ("missing", lambda d: None),
            ("empty", _write_empty_cache),
            ("malformed", _write_bad_cache),
            ("nonempty", self._write_lastfailed),
        ]
        for label, setup in setcases:
            staging = tmp_path / f"staging-{label}"
            staging.mkdir()
            setup(staging)
            diag, _ = self._call_diagnostics(monkeypatch, staging)
            assert diag["primary_exit_code"] == 1, f"FAIL verdict flipped for {label}"
            assert diag["failed_count"] >= 0


class TestSaleorBaselineFlakePolicy:
    """v0.9.20 Task F: evidence-backed pristine baseline-flake classification.

    The frozen pristine Saleor validation command historically exits non-zero
    with a nondeterministic ~31-36 order/pricing cluster (Gate 9 ledger). The
    policy tolerates ONLY that exact frozen nodeid set, ONLY while every nodeid
    still passes a current serial rerun; anything else fails closed.
    """

    FLAKY_NODEIDS = (
        "saleor/graphql/order/tests/test_order.py::test_order_lines_first",
        "saleor/graphql/checkout/tests/test_checkout.py::test_checkout_prices",
        "saleor/product/tests/test_product.py::test_pricing_annotation",
    )

    def _saleor_pin_sha(self) -> str:
        pins = {p.repo_id: p for p in snapshot_mod.DEFAULT_PINS}
        return str(pins["saleor"].commit_sha)

    def _write_small_lastfailed(self, staging_dir: Path) -> None:
        cache = staging_dir / ".pytest_cache" / "v" / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "lastfailed").write_text(
            json.dumps(dict.fromkeys(self.FLAKY_NODEIDS, True)), encoding="utf-8"
        )

    def _profile(
        self,
        nodeids: tuple[str, ...] = FLAKY_NODEIDS,
        *,
        serial_passed: bool = True,
        sha: str | None = None,
        command: tuple[str, ...] | None = None,
        schema: str | None = None,
    ) -> dict[str, Any]:
        saleor_command = TestSaleorFailureDiagnostics._saleor_command(self)
        return {
            "schema": schema or snapshot_mod.BASELINE_PROFILE_SCHEMA,
            "task": "PILOT-EXEC-01",
            "saleor_commit_sha": sha or self._saleor_pin_sha(),
            "frozen_validation_command": list(command or saleor_command.command),
            "failed_nodeids": sorted(nodeids),
            "per_nodeid_serial_rerun": [
                {"nodeid": n, "exit_code": 0 if serial_passed else 1,
                 "passed": serial_passed}
                for n in sorted(nodeids)
            ],
            "created_utc": "2026-08-24T00:00:00+00:00",
        }

    def _patch_flake_runtime(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        rerun_passes: bool = True,
    ) -> list[list[str]]:
        """Fake runtime: gate PASS, primary FAIL with the flaky set, serial
        baseline-flake reruns pass/fail per ``rerun_passes``."""
        calls: list[list[str]] = []

        def _fake_run(argv: list[str], **kwargs: object) -> types.SimpleNamespace:
            calls.append(list(argv))
            joined = " ".join(str(a) for a in argv)
            if argv[:2] == ["python", "-c"]:
                return types.SimpleNamespace(returncode=0, stdout="{}", stderr="")
            if "--lf" in argv:
                return types.SimpleNamespace(
                    returncode=0, stdout="3 passed", stderr=""
                )
            if "--collect-only" in argv:
                return types.SimpleNamespace(
                    returncode=0, stdout="collected 1 item", stderr=""
                )
            if "--no-header" in argv and any(
                n in argv for n in self.FLAKY_NODEIDS
            ):
                if rerun_passes:
                    return types.SimpleNamespace(
                        returncode=0, stdout="1 passed in 0.30s", stderr=""
                    )
                return types.SimpleNamespace(
                    returncode=1, stdout="", stderr="assert 2 == 3\n1 failed"
                )
            if "test_create_checkout" in joined:
                return types.SimpleNamespace(
                    returncode=0, stdout="1 passed in 0.50s", stderr=""
                )
            return types.SimpleNamespace(
                returncode=1,
                stdout="",
                stderr=(
                    "FAILED saleor/graphql/order/tests/test_order.py::test_order_lines_first\n"
                    "3 failed, 6056 passed in 512.00s\n"
                ),
            )

        monkeypatch.setattr(snapshot_mod.subprocess, "run", _fake_run)
        monkeypatch.setattr(snapshot_mod, "_copy_embedded_tree", lambda s, t: None)
        monkeypatch.setattr(
            snapshot_mod, "_service_reachable", lambda url, timeout=5.0: True
        )
        return calls

    def _run_saleor(
        self,
        tmp_path: Path,
        *,
        baseline_profile: dict[str, Any] | None = None,
        emit_path: Path | None = None,
        lastfailed_nodeids: tuple[str, ...] | None = None,
    ) -> tuple[dict[str, Any], Path]:
        staging_dir = tmp_path / "repo_staging" / "saleor"
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / "saleor" / "core").mkdir(parents=True, exist_ok=True)
        (staging_dir / "saleor" / "core" / "rlimit.py").write_text(
            "# dummy; contains: except ImportError\n", encoding="utf-8"
        )
        if lastfailed_nodeids is None:
            self._write_small_lastfailed(staging_dir)
        else:
            cache = staging_dir / ".pytest_cache" / "v" / "cache"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / "lastfailed").write_text(
                json.dumps(dict.fromkeys(lastfailed_nodeids, True)),
                encoding="utf-8",
            )
        repo_source = tmp_path / "saleor-src"
        repo_source.mkdir(exist_ok=True)
        result = snapshot_mod.run_repo_preflight(
            repo_id="saleor",
            staging_dir=staging_dir,
            repo_cache=None,
            venv_python="python",
            command=TestSaleorFailureDiagnostics._saleor_command(self),
            timeout=300,
            repo_source=repo_source,
            logs_dir=tmp_path / "logs",
            diagnostics_dir=None,
            baseline_profile=baseline_profile,
            emit_baseline_profile_path=emit_path,
        )
        return result, staging_dir

    # --- loader validation ----------------------------------------------------

    def test_loader_accepts_valid_profile(self, tmp_path: Path) -> None:
        path = tmp_path / "profile.json"
        path.write_text(json.dumps(self._profile()), encoding="utf-8")
        loaded = snapshot_mod.load_baseline_profile(
            path,
            expected_saleor_sha=self._saleor_pin_sha(),
            expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                self
            ).command,
        )
        assert loaded["schema"] == snapshot_mod.BASELINE_PROFILE_SCHEMA

    def test_loader_rejects_wrong_schema(self, tmp_path: Path) -> None:
        path = tmp_path / "profile.json"
        path.write_text(json.dumps(self._profile(schema="other.v9")), encoding="utf-8")
        with pytest.raises(RuntimeError, match="unsupported schema"):
            snapshot_mod.load_baseline_profile(
                path,
                expected_saleor_sha=self._saleor_pin_sha(),
                expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                    self
                ).command,
            )

    def test_loader_rejects_wrong_saleor_sha(self, tmp_path: Path) -> None:
        path = tmp_path / "profile.json"
        path.write_text(json.dumps(self._profile(sha="deadbeef")), encoding="utf-8")
        with pytest.raises(RuntimeError, match="targets Saleor snapshot"):
            snapshot_mod.load_baseline_profile(
                path,
                expected_saleor_sha=self._saleor_pin_sha(),
                expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                    self
                ).command,
            )

    def test_loader_rejects_different_frozen_command(self, tmp_path: Path) -> None:
        path = tmp_path / "profile.json"
        path.write_text(
            json.dumps(self._profile(command=("{python}", "-m", "pytest"))),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="different frozen validation command"):
            snapshot_mod.load_baseline_profile(
                path,
                expected_saleor_sha=self._saleor_pin_sha(),
                expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                    self
                ).command,
            )

    def test_loader_rejects_deterministic_serial_failure_recorded_in_profile(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "profile.json"
        path.write_text(
            json.dumps(self._profile(serial_passed=False)), encoding="utf-8"
        )
        with pytest.raises(RuntimeError, match="deterministic failures are not flakes"):
            snapshot_mod.load_baseline_profile(
                path,
                expected_saleor_sha=self._saleor_pin_sha(),
                expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                    self
                ).command,
            )

    # --- classification behavior ----------------------------------------------

    def test_classified_baseline_failure_passes_with_explicit_evidence(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        result, _ = self._run_saleor(
            tmp_path, baseline_profile=self._profile()
        )
        primary = result["commands"][0]
        assert primary["passed"] is False, "raw command truth must be preserved"
        assert primary["exit_code"] == 1
        assert result["command_passed"] is False
        classification = result["baseline_classification"]
        assert classification["status"] == "CLASSIFIED"
        assert classification["classified"] is True
        assert sorted(classification["classified_nodeids"]) == sorted(
            self.FLAKY_NODEIDS
        )
        assert result["passed"] is True

    def test_new_nodeid_absent_from_profile_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        new_nodeid = "saleor/graphql/order/tests/test_new.py::test_regression"
        profile = self._profile(self.FLAKY_NODEIDS)
        result, _ = self._run_saleor(
            tmp_path,
            baseline_profile=profile,
            lastfailed_nodeids=(*self.FLAKY_NODEIDS, new_nodeid),
        )
        classification = result["baseline_classification"]
        assert classification["status"] == "FAILED_UNCLASSIFIED_NODEIDS"
        assert classification["unclassified_nodeids"] == [new_nodeid]
        assert classification["classified"] is False
        assert result["passed"] is False
        assert result["command_passed"] is False

    def test_deterministic_serial_rerun_failure_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=False)
        result, _ = self._run_saleor(tmp_path, baseline_profile=self._profile())
        classification = result["baseline_classification"]
        assert classification["status"] == "FAILED_DETERMINISTIC_SERIAL_FAILURES"
        assert sorted(classification["deterministic_failures"]) == sorted(
            self.FLAKY_NODEIDS
        )
        assert classification["classified"] is False
        assert result["passed"] is False

    def test_missing_lastfailed_with_profile_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        result, _ = self._run_saleor(
            tmp_path,
            baseline_profile=self._profile(),
            lastfailed_nodeids=(),
        )
        classification = result["baseline_classification"]
        assert classification["status"] == "NOT_CLASSIFIED_NO_LASTFAILED"
        assert classification["classified"] is False
        assert result["passed"] is False

    def test_no_profile_keeps_legacy_fail_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        result, _ = self._run_saleor(tmp_path)
        assert "baseline_classification" not in result
        assert result["command_passed"] is False
        assert result["passed"] is False

    def test_serial_reruns_use_exact_serial_argv(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        calls = self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        result, _ = self._run_saleor(tmp_path, baseline_profile=self._profile())
        assert result["passed"] is True
        reruns = [
            c for c in calls if "--no-header" in c and any(n in c for n in self.FLAKY_NODEIDS)
        ]
        assert len(reruns) == len(self.FLAKY_NODEIDS)
        for argv in reruns:
            assert argv[:3] == ["python", "-m", "pytest"]
            assert argv[3:5] == ["-n", "0"], "policy requires serial (-n 0) reruns"
            assert argv.count("-m") == 1
            assert sum(1 for a in argv if str(a).startswith("saleor/")) == 1

    # --- emission mode ---------------------------------------------------------

    def test_emit_mode_writes_profile_and_never_changes_verdict(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        emit_path = tmp_path / "evidence" / "fresh_profile.json"
        result, _ = self._run_saleor(tmp_path, emit_path=emit_path)
        assert emit_path.is_file()
        payload = json.loads(emit_path.read_text(encoding="utf-8"))
        assert payload["schema"] == snapshot_mod.BASELINE_PROFILE_SCHEMA
        assert payload["saleor_commit_sha"] == self._saleor_pin_sha()
        assert payload["frozen_validation_command"] == list(
            TestSaleorFailureDiagnostics._saleor_command(self).command
        )
        assert payload["full_run_exit_code"] == 1
        assert sorted(payload["failed_nodeids"]) == sorted(self.FLAKY_NODEIDS)
        assert all(
            entry["passed"] is True for entry in payload["per_nodeid_serial_rerun"]
        )
        assert len(payload["per_nodeid_serial_rerun"]) == len(self.FLAKY_NODEIDS)
        assert payload["created_utc"]
        assert payload["profile_source_commit"]
        # Emission alone never flips the verdict.
        assert "baseline_classification" not in result
        assert result["passed"] is False

    def test_emitted_profile_round_trips_through_loader(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch_flake_runtime(monkeypatch, rerun_passes=True)
        emit_path = tmp_path / "fresh_profile.json"
        self._run_saleor(tmp_path, emit_path=emit_path)
        loaded = snapshot_mod.load_baseline_profile(
            emit_path,
            expected_saleor_sha=self._saleor_pin_sha(),
            expected_frozen_command=TestSaleorFailureDiagnostics._saleor_command(
                self
            ).command,
        )
        assert loaded["failed_count"] == len(self.FLAKY_NODEIDS)
