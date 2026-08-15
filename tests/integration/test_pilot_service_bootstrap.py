"""PILOT-EXEC-01 KAGGLE-POSTGRES-ROOT-FIX: hermetic service bootstrap contract.

Models the exact real Kaggle environment defect that blocked v0.9.6 preflight:

    /usr/lib/postgresql/14/bin/initdb ... -> initdb: error: cannot be run as root

The Kaggle notebook process runs as root while PostgreSQL initdb/pg_ctl refuse
root. The service-bootstrap-cell therefore switches the PostgreSQL server
lifecycle (initdb, pg_ctl and the postgres server it launches) to the
package-native unprivileged ``postgres`` OS account, fails closed before initdb
when that account is missing, and never falls back to root.

This module is the Gate H hermetic POSIX-oriented test seam: it execs the EXACT
definitions of ``notebooks/pilot_exec_01.ipynb`` cell ``service-bootstrap-cell``
(truncated at the ``# ---- Provision and prove`` provisioning marker) with
fakes for ``os``/``pwd``/``subprocess``/``socket``, so the tests exercise the
precise command construction that real Kaggle Cell 8 uses. The normal suite
never requires root and never touches real services.

Gates covered (taskpack 02_TEST_MATRIX.md):

- Gate B: root-mode contract (postgres user selected, initdb/pg_ctl NOT invoked
  as root, ownership/log/socket preparation, no shell=True, frozen endpoint);
- Gate C: non-root contract (no privilege switch, direct path, same endpoint);
- Gate D: missing service-user FAILS CLOSED before initdb;
- Gate E: partial private cluster state (fresh / initialized / incomplete);
- Gate F: service proof semantics (port-open-credentials-fail, port-never-open,
  both-success);
- Gate H: seam over the exact cell command construction.
- Gate R (PILOT-EXEC-01 KAGGLE-REDIS-PACKAGE-FALLBACK): the cell must NEVER
  install the two Redis-compatible ALTERNATIVE packages in one apt transaction
  (``apt-get install valkey-server redis-server`` aborts whenever one candidate
  is unavailable). It probes ``apt-cache policy <candidate>`` individually,
  installs EXACTLY ONE package per ``apt-get install``, falls back to the
  available candidate, fails closed with diagnostics when neither is available,
  refreshes apt metadata at most once per invocation, and never falls back to
  a pip client package or an in-process fake server.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
CANONICAL_NOTEBOOK = PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"
SERVICE_CELL_ID = "service-bootstrap-cell"
PROVISION_MARKER = "# ---- Provision and prove"

SERVICE_HOST = "127.0.0.1"
SALEOR_PG_PORT = 5433
SALEOR_REDIS_PORT = 6379
SALEOR_PG_USER = "saleor"
SALEOR_PG_DB = "saleor"
PG_UID = 999
PG_GID = 999


def _cell_source(cell_id: str) -> str:
    nb = json.loads(CANONICAL_NOTEBOOK.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c.get("id") == cell_id]
    assert len(cells) == 1, f"expected exactly one '{cell_id}' cell"
    src = cells[0]["source"]
    return src if isinstance(src, str) else "".join(src)


def _definitions_source() -> str:
    src = _cell_source(SERVICE_CELL_ID)
    assert PROVISION_MARKER in src, "provisioning marker missing from service cell"
    return src.split(PROVISION_MARKER)[0]


class _Ok:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _Conn:
    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *_args: Any) -> bool:
        return False


class _Ns:
    def __init__(self) -> None:
        self.ns: dict[str, Any] = {}
        self.run_calls: list[dict[str, Any]] = []
        self.chown_calls: list[tuple[str, int, int]] = []
        self.chmod_calls: list[tuple[str, int]] = []
        self.which_map: dict[str, str] = {}
        self.pg_bindir: Path | None = None
        self.fakebin: Path | None = None
        self.redis_started = False
        self.pg_started = False


def _exec_definitions(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    euid: int = 0,
    postgres_user: bool = True,
    port_open: bool = False,
    pg_port_open: bool | None = None,
    redis_port_open: bool | None = None,
    db_probe_ok: bool = True,
    role_present: bool = True,
    db_present: bool = True,
    apt_available: set[str] | None = None,
    install_fail: set[str] | None = None,
    version_fail: set[str] | None = None,
    start_fail: set[str] | None = None,
    provides: dict[str, tuple[str, ...]] | None = None,
    apt_get_missing: bool = False,
    apt_cache_missing: bool = False,
    present_bins: dict[str, str] | None = None,
) -> _Ns:
    """Exec the exact service-cell definitions with hermetic fakes.

    ``euid`` models the notebook effective uid (0 = root, like real Kaggle;
    non-zero = unprivileged). ``postgres_user`` models whether the package-native
    ``postgres`` OS account exists. ``port_open`` models whether a foreign
    process already listens on 127.0.0.1:5433/6379; ``pg_port_open`` and
    ``redis_port_open`` override the PG/Redis ports individually. ``apt_available``
    models the packages resolvable via ``apt-cache policy``; ``install_fail``
    models packages whose ``apt-get install`` exits nonzero; ``version_fail``
    models binaries whose ``--version`` command exits nonzero; ``start_fail``
    models binaries whose daemonize start exits nonzero; ``provides`` maps an OS
    package to the binary names it makes discoverable after a successful install.
    The private service paths are redirected under ``tmp_path`` (never /kaggle).
    """
    apt_available = set(apt_available or ())
    install_fail = set(install_fail or ())
    version_fail = set(version_fail or ())
    start_fail = set(start_fail or ())
    provides = dict(provides or {})
    pg_open = port_open if pg_port_open is None else pg_port_open
    redis_open = port_open if redis_port_open is None else redis_port_open

    if postgres_user:
        fake_pwd = types.SimpleNamespace(
            getpwnam=lambda _name: types.SimpleNamespace(pw_uid=PG_UID, pw_gid=PG_GID)
        )
    else:

        def _missing(_name: str) -> None:
            raise KeyError(_name)

        fake_pwd = types.SimpleNamespace(getpwnam=_missing)
    monkeypatch.setitem(sys.modules, "pwd", fake_pwd)

    state = _Ns()

    def fake_chown(path: Any, uid: int, gid: int) -> None:
        state.chown_calls.append((str(path), uid, gid))

    def fake_chmod(path: Any, mode: int) -> None:
        state.chmod_calls.append((str(path), mode))

    # The cell does ``import os as _os``; shim sys.modules["os"] so the exec'd
    # definitions observe a POSIX os (name="posix", geteuid=euid) WITHOUT touching
    # the real os module that pathlib/pytest rely on (os.name must stay "nt" here).
    fake_os = types.ModuleType("os")
    fake_os.name = "posix"
    fake_os.geteuid = lambda: euid
    fake_os.chown = fake_chown
    fake_os.chmod = fake_chmod
    fake_os.environ = os.environ
    fake_os.path = os.path
    fake_os.getenv = os.getenv
    fake_os.sep = os.sep
    monkeypatch.setitem(sys.modules, "os", fake_os)

    state.fakebin = tmp_path / "fakebin"
    state.fakebin.mkdir(parents=True, exist_ok=True)
    state.which_map = dict(present_bins or {})
    if not apt_get_missing:
        state.which_map.setdefault("apt-get", "/usr/bin/apt-get")
    if not apt_cache_missing:
        state.which_map.setdefault("apt-cache", "/usr/bin/apt-cache")

    def fake_which(name: str) -> str | None:
        return state.which_map.get(name)

    monkeypatch.setattr(shutil, "which", fake_which)

    def fake_run(cmd: list[str], **kwargs: Any) -> _Ok:
        state.run_calls.append({"cmd": list(cmd), "kwargs": dict(kwargs)})
        name = Path(str(cmd[0])).name
        args = [str(c) for c in cmd]
        if name == "apt-get" and len(args) > 1 and args[1] == "update":
            return _Ok()
        if name == "apt-get" and len(args) > 1 and args[1] == "install":
            packages = [a for a in args[2:] if not a.startswith("-")]
            if any(p in install_fail for p in packages):
                return _Ok(returncode=100)
            for p in packages:
                for binary in provides.get(p, (p,)):
                    state.which_map[binary] = str(state.fakebin / binary)
            return _Ok()
        if name == "apt-cache" and len(args) > 1 and args[1] == "policy":
            pkg = args[-1]
            if pkg in apt_available:
                return _Ok(stdout=f"{pkg}:\n  Candidate: 9.9.9\n")
            return _Ok(returncode=100)
        if name == "pg_config":
            return _Ok(stdout=str(state.pg_bindir) if state.pg_bindir else "")
        if args[-1] == "--version":
            if name in version_fail:
                return _Ok(returncode=1)
            return _Ok(stdout=f"{name} fake version 9.9.9\n")
        if "--daemonize" in args:
            if name in start_fail:
                return _Ok(returncode=1)
            state.redis_started = True
            return _Ok()
        if name == "pg_ctl":
            state.pg_started = True
            return _Ok()
        if name == "psql":
            sql = args[-1].strip()
            if sql == "SELECT 1":
                return _Ok(stdout="1" if db_probe_ok else "", stderr="")
            if "pg_roles" in sql:
                return _Ok(stdout="1" if role_present else "")
            if "pg_database" in sql:
                return _Ok(stdout="1" if db_present else "")
            if sql.startswith("CREATE ROLE") or sql.startswith("CREATE DATABASE"):
                return _Ok()
        return _Ok()

    monkeypatch.setattr(subprocess, "run", fake_run)

    def fake_conn(addr: Any, *_args: Any, **_kwargs: Any) -> _Conn:
        host, port = addr
        if port == SALEOR_PG_PORT and (pg_open or state.pg_started):
            return _Conn()
        if port == SALEOR_REDIS_PORT and (redis_open or state.redis_started):
            return _Conn()
        raise OSError("connection refused (port closed in hermetic model)")

    monkeypatch.setattr(socket, "create_connection", fake_conn)

    ns: dict[str, Any] = {}
    exec(compile(_definitions_source(), "<service-bootstrap-cell>", "exec"), ns)
    services = tmp_path / "pilot_services"
    ns["SERVICES_ROOT"] = services
    ns["PG_DATA_DIR"] = services / "postgres"
    ns["PG_LOG"] = services / "postgres.log"
    ns["REDIS_LOG"] = services / "valkey.log"
    state.ns = ns
    return state


def _provision_source() -> str:
    src = _cell_source(SERVICE_CELL_ID)
    marker_index = src.index(PROVISION_MARKER)
    return src[marker_index:]


def _exec_cell(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    pg_bindir: Path | None = None,
    **kwargs: Any,
) -> _Ns:
    """Exec the ENTIRE service cell (definitions + provisioning + prove).

    ``pg_bindir`` pre-seeds an installed PostgreSQL binary directory so the cell
    resolves ``pg_config``/pg binaries without an OS package install, keeping the
    hermetic focus on the exact command construction of both service paths.
    """
    state = _exec_definitions(tmp_path, monkeypatch, **kwargs)
    if pg_bindir is not None:
        state.pg_bindir = pg_bindir
        state.which_map["pg_config"] = str(pg_bindir / "pg_config")
    exec(compile(_provision_source(), "<service-bootstrap-cell:provision>", "exec"), state.ns)
    return state


def _make_bindir(tmp_path: Path) -> Path:
    bindir = tmp_path / "pgbin"
    bindir.mkdir()
    for name in ("pg_ctl", "initdb", "psql", "postgres"):
        (bindir / name).write_text("", encoding="utf-8")
    return bindir


def _run_cmd(state: _Ns, binary_name: str) -> list[dict[str, Any]]:
    return [c for c in state.run_calls if str(c["cmd"][0]).endswith(binary_name)]


def _user_of(state: _Ns, binary_name: str) -> list[Any]:
    return [c["kwargs"].get("user") for c in _run_cmd(state, binary_name)]


class TestSeamAndSource:
    def test_definitions_execute_and_cell_is_exact(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Gate H: the seam runs the exact definitions Cell 8 uses."""
        state = _exec_definitions(tmp_path, monkeypatch)
        assert callable(state.ns["_ensure_postgres"])
        assert callable(state.ns["_pg_service_user"])
        assert callable(state.ns["_prepare_postgres_paths"])
        assert callable(state.ns["_ensure_redis"])
        full = _cell_source(SERVICE_CELL_ID)
        assert full.startswith(_definitions_source())
        assert "shell=True" not in full

    def test_no_shell_true_in_any_executed_command(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert state.run_calls
        for call in state.run_calls:
            assert "shell" not in call["kwargs"], f"shell=True used: {call}"


class TestRootModeContract:
    """Gate B: effective uid == 0 must run PostgreSQL lifecycle unprivileged."""

    @pytest.fixture(autouse=True)
    def _env(self, tmp_path: Path, monkeypatch: Any) -> None:
        self._state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        self._state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        self._bindir = _make_bindir(tmp_path)
        self._state.ns["_ensure_postgres"](self._bindir)

    def test_postgres_service_user_is_selected(self) -> None:
        assert self._state.ns["_pg_service_user"]() == "postgres"

    def test_initdb_never_invoked_as_root(self) -> None:
        users = _user_of(self._state, "initdb")
        assert users == ["postgres"], f"initdb user(s): {users}"

    def test_pg_ctl_never_invoked_as_root(self) -> None:
        users = _user_of(self._state, "pg_ctl")
        assert users == ["postgres"], f"pg_ctl user(s): {users}"

    def test_psql_client_runs_from_notebook_process(self) -> None:
        users = _user_of(self._state, "psql")
        assert users and all(user is None for user in users)

    def test_data_path_ownership_preparation_occurs(self) -> None:
        data_dir = str(self._state.ns["PG_DATA_DIR"])
        log_path = str(self._state.ns["PG_LOG"])
        assert (data_dir, PG_UID, PG_GID) in self._state.chown_calls
        assert (log_path, PG_UID, PG_GID) in self._state.chown_calls
        assert (data_dir, 0o700) in self._state.chmod_calls
        assert (log_path, 0o600) in self._state.chmod_calls

    def test_private_service_paths_created(self) -> None:
        assert self._state.ns["SERVICES_ROOT"].is_dir()
        assert self._state.ns["PG_DATA_DIR"].is_dir()
        assert self._state.ns["PG_LOG"].is_file()

    def test_initdb_exact_argv_and_frozen_flags(self) -> None:
        calls = _run_cmd(self._state, "initdb")
        assert len(calls) == 1
        cmd = calls[0]["cmd"]
        assert cmd == [
            str(self._bindir / "initdb"),
            "-D",
            str(self._state.ns["PG_DATA_DIR"]),
            "-U",
            SALEOR_PG_USER,
            "-E",
            "UTF8",
            "--auth=trust",
        ]

    def test_pg_ctl_exact_argv_frozen_endpoint(self) -> None:
        calls = _run_cmd(self._state, "pg_ctl")
        assert len(calls) == 1
        cmd = calls[0]["cmd"]
        data_dir = str(self._state.ns["PG_DATA_DIR"])
        pg_opts = f"-p 5433 -h 127.0.0.1 -k {data_dir}"
        assert cmd == [
            str(self._bindir / "pg_ctl"),
            "-D",
            data_dir,
            "-l",
            str(self._state.ns["PG_LOG"]),
            "-o",
            pg_opts,
            "start",
        ]

    def test_frozen_tcp_db_contract_unchanged(self) -> None:
        psql_calls = _run_cmd(self._state, "psql")
        assert psql_calls
        probes = [c for c in psql_calls if str(c["cmd"][-1]).strip() == "SELECT 1"]
        assert probes, "final frozen connection probe missing"
        env = probes[-1]["kwargs"]["env"]
        assert env["PGHOST"] == SERVICE_HOST
        assert env["PGPORT"] == str(SALEOR_PG_PORT)
        assert env["PGUSER"] == SALEOR_PG_USER
        assert env["PGDATABASE"] == SALEOR_PG_DB
        assert env["PGPASSWORD"] == "saleor"


class TestNonRootContract:
    """Gate C: effective uid != 0 keeps the direct path with no privilege switch."""

    @pytest.fixture(autouse=True)
    def _env(self, tmp_path: Path, monkeypatch: Any) -> None:
        self._state = _exec_definitions(tmp_path, monkeypatch, euid=1000, postgres_user=True)
        self._state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        self._bindir = _make_bindir(tmp_path)
        self._state.ns["_ensure_postgres"](self._bindir)

    def test_no_privilege_switch_for_lifecycle(self) -> None:
        assert _user_of(self._state, "initdb") == [None]
        assert _user_of(self._state, "pg_ctl") == [None]

    def test_direct_initdb_pg_ctl_path_remains_supported(self) -> None:
        assert len(_run_cmd(self._state, "initdb")) == 1
        assert len(_run_cmd(self._state, "pg_ctl")) == 1

    def test_service_user_none_when_not_root(self) -> None:
        assert self._state.ns["_pg_service_user"]() is None

    def test_no_root_ownership_preparation(self) -> None:
        assert self._state.chown_calls == []

    def test_same_frozen_db_endpoint(self) -> None:
        cmd = _run_cmd(self._state, "pg_ctl")[0]["cmd"]
        assert "-p 5433 -h 127.0.0.1" in cmd[cmd.index("-o") + 1]


class TestMissingServiceUser:
    """Gate D: root + package binaries but no valid unprivileged account -> FAIL CLOSED."""

    def test_fails_closed_before_initdb(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=False)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        with pytest.raises(RuntimeError, match="postgres"):
            state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert not _run_cmd(state, "initdb"), "initdb must never run without a service account"
        assert not _run_cmd(state, "pg_ctl"), "pg_ctl must never run without a service account"

    def test_service_user_resolution_raises(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=False)
        with pytest.raises(RuntimeError, match="does not exist"):
            state.ns["_pg_service_user"]()

    def test_no_silent_fallback_to_root(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=False)
        with pytest.raises(RuntimeError, match="does not exist"):
            state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert not state.run_calls, "no OS command may run without a service account"
        assert not state.chown_calls, "no ownership preparation may run without a service account"


class TestPartialClusterState:
    """Gate E: fresh / initialized / incomplete private data dir behavior."""

    def test_fresh_data_dir_initdb_runs(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert len(_run_cmd(state, "initdb")) == 1
        assert state.ns["PG_DATA_DIR"].is_dir()

    def test_already_initialized_skips_initdb(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        data_dir = state.ns["PG_DATA_DIR"]
        data_dir.mkdir(parents=True)
        (data_dir / "PG_VERSION").write_text("14\n", encoding="utf-8")
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert not _run_cmd(state, "initdb"), "already-initialized dir must not re-initdb"
        assert len(_run_cmd(state, "pg_ctl")) == 1

    def test_incomplete_previous_dir_recreated(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        data_dir = state.ns["PG_DATA_DIR"]
        data_dir.mkdir(parents=True)
        stale = data_dir / "stale.txt"
        stale.write_text("junk\n", encoding="utf-8")
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert len(_run_cmd(state, "initdb")) == 1
        assert not stale.exists(), "incomplete previous data dir must be recreated"

    def test_recovery_limited_to_private_service_path(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        services = state.ns["SERVICES_ROOT"]
        services.mkdir(parents=True)
        unrelated = services / "unrelated.txt"
        unrelated.write_text("keep\n", encoding="utf-8")
        data_dir = state.ns["PG_DATA_DIR"]
        data_dir.mkdir(parents=True)
        (data_dir / "stale.txt").write_text("junk\n", encoding="utf-8")
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert unrelated.is_file(), "recovery must only touch the private PG data dir"


class TestServiceProofSemantics:
    """Gate F: pass/fail semantics of the service proof."""

    def test_port_open_but_frozen_credentials_fail(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(
            tmp_path, monkeypatch, euid=1000, postgres_user=True, port_open=True,
            db_probe_ok=False,
        )
        with pytest.raises(RuntimeError, match="not serving the frozen"):
            state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert not _run_cmd(state, "initdb")

    def test_postgres_starts_but_port_never_opens_fails(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=1000, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: False
        with pytest.raises(RuntimeError, match="failed to start"):
            state.ns["_ensure_postgres"](_make_bindir(tmp_path))

    def test_redis_starts_but_port_never_opens_fails(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=1000, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: False
        binary = tmp_path / "valkey-server"
        binary.write_text("", encoding="utf-8")
        with pytest.raises(RuntimeError, match="failed to start"):
            state.ns["_ensure_redis"](binary)

    def test_both_services_and_db_probe_succeed(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(
            tmp_path, monkeypatch, euid=0, postgres_user=True, db_probe_ok=True,
            role_present=True, db_present=True,
        )
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        bindir = _make_bindir(tmp_path)
        state.ns["_ensure_postgres"](bindir)
        redis = tmp_path / "valkey-server"
        redis.write_text("", encoding="utf-8")
        state.ns["_ensure_redis"](redis)
        assert len(_run_cmd(state, "initdb")) == 1
        assert len(_run_cmd(state, "pg_ctl")) == 1
        psql = _run_cmd(state, "psql")
        assert psql and psql[-1]["cmd"][-1].strip() == "SELECT 1"

    def test_role_and_db_created_when_absent(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(
            tmp_path, monkeypatch, euid=1000, postgres_user=True,
            role_present=False, db_present=False,
        )
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        sqls = [c["cmd"][-1].strip() for c in _run_cmd(state, "psql")]
        assert any(sql.startswith("CREATE ROLE saleor") for sql in sqls)
        assert any(sql == "CREATE DATABASE saleor OWNER saleor" for sql in sqls)


class _AptAssertions:
    """Shared helpers for the Redis OS-package fallback matrix."""

    @staticmethod
    def _apt_update_calls(state: _Ns) -> list[dict[str, Any]]:
        return [
            c for c in state.run_calls
            if str(c["cmd"][0]).endswith("apt-get") and str(c["cmd"][1]) == "update"
        ]

    @staticmethod
    def _apt_install_calls(state: _Ns) -> list[list[str]]:
        return [
            c["cmd"] for c in state.run_calls
            if str(c["cmd"][0]).endswith("apt-get") and str(c["cmd"][1]) == "install"
        ]

    @staticmethod
    def _apt_commands(state: _Ns) -> list[dict[str, Any]]:
        return [
            c for c in state.run_calls
            if str(c["cmd"][0]).endswith("apt-get") or str(c["cmd"][0]).endswith("apt-cache")
        ]


class TestRedisPackageFallback(_AptAssertions):
    """Gate R: per-candidate Redis OS package fallback (real Kaggle defect).

    The real Kaggle Ubuntu (Jammy-shaped) runtime exposes ``redis-server`` in its
    configured apt repositories but NOT ``valkey-server``; installing both in ONE
    apt-get transaction aborts the whole install with ``E: Unable to locate
    package valkey-server``. The cell must probe each candidate individually and
    install EXACTLY ONE package per apt-get command.
    """

    def test_jammy_shaped_installs_only_redis_server(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Gate C (MANDATORY): valkey unavailable + redis available -> PASS."""
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=True,
            pg_bindir=_make_bindir(tmp_path),
            apt_available={"redis-server"},
        )
        assert self._apt_install_calls(state) == [
            ["apt-get", "install", "-y", "redis-server"]
        ]
        assert len(self._apt_update_calls(state)) == 1
        assert state.redis_started
        out = capsys.readouterr().out
        assert "OS package valkey-server: UNAVAILABLE" in out
        assert "Selected Redis-compatible implementation: redis-server" in out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out

    def test_reverse_future_distro_prefers_valkey_only(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Gate D: both candidates available -> install valkey only and stop."""
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=True,
            pg_bindir=_make_bindir(tmp_path),
            apt_available={"valkey-server", "redis-server"},
        )
        assert self._apt_install_calls(state) == [
            ["apt-get", "install", "-y", "valkey-server"]
        ]
        assert "Selected Redis-compatible implementation: valkey-server" in (
            capsys.readouterr().out
        )

    def test_first_candidate_install_failure_falls_back(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Gate E: valkey install fails -> redis fallback still passes."""
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=True,
            pg_bindir=_make_bindir(tmp_path),
            apt_available={"valkey-server", "redis-server"},
            install_fail={"valkey-server"},
        )
        assert self._apt_install_calls(state) == [
            ["apt-get", "install", "-y", "valkey-server"],
            ["apt-get", "install", "-y", "redis-server"],
        ]
        out = capsys.readouterr().out
        assert "INSTALL FAILED" in out
        assert "Selected Redis-compatible implementation: redis-server" in out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out

    def test_neither_candidate_available_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Gate F: no candidate resolvable -> fail closed with diagnostics."""
        with pytest.raises(RuntimeError) as excinfo:
            _exec_cell(
                tmp_path, monkeypatch,
                euid=0, postgres_user=True,
                pg_port_open=True,
                pg_bindir=_make_bindir(tmp_path),
                apt_available=set(),
            )
        msg = str(excinfo.value)
        assert "no Redis-compatible server binary is available" in msg
        assert "candidates checked: valkey-server, redis-server" in msg
        assert "unavailable: valkey-server, redis-server" in msg
        assert "no pip" in msg
        assert "no in-process fake server fallback" in msg

    def test_apt_get_missing_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Gate G: apt-get absent -> fail closed before any apt command."""
        with pytest.raises(RuntimeError, match="apt-get not found"):
            _exec_cell(
                tmp_path, monkeypatch,
                euid=0, postgres_user=True,
                pg_port_open=True,
                pg_bindir=_make_bindir(tmp_path),
                apt_get_missing=True,
            )

    def test_apt_cache_missing_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Gate G: apt-cache absent -> every candidate probes as unavailable."""
        with pytest.raises(RuntimeError) as excinfo:
            _exec_cell(
                tmp_path, monkeypatch,
                euid=0, postgres_user=True,
                pg_port_open=True,
                pg_bindir=_make_bindir(tmp_path),
                apt_cache_missing=True,
            )
        assert "unavailable: valkey-server, redis-server" in str(excinfo.value)

    def test_apt_update_runs_at_most_once(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Gate H: apt metadata refresh is idempotent within one invocation."""
        state = _exec_definitions(tmp_path, monkeypatch, apt_available={"redis-server"})
        binary = state.ns["_provision_redis_server"]()
        assert binary is not None and binary.name == "redis-server"
        state.ns["_apt_update_once"]()
        assert len(self._apt_update_calls(state)) == 1


class TestRedisAlreadyInstalled(_AptAssertions):
    """Gate B: already-running Redis must never trigger any apt command."""

    def test_running_with_binary_needs_no_apt(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=True,
            pg_bindir=_make_bindir(tmp_path),
            redis_port_open=True,
            present_bins={"valkey-server": "/usr/bin/valkey-server"},
        )
        assert self._apt_commands(state) == []
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in capsys.readouterr().out

    def test_running_foreign_redis_without_binary_ok(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=True,
            pg_bindir=_make_bindir(tmp_path),
            redis_port_open=True,
        )
        assert self._apt_commands(state) == []
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in capsys.readouterr().out


class TestRedisServiceSemantics:
    """Gate I: start/version failure semantics stay fail-closed."""

    def test_version_command_failure_is_diagnostic(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, version_fail={"redis-server"})
        binary = tmp_path / "redis-server"
        binary.write_text("", encoding="utf-8")
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        with pytest.raises(RuntimeError, match="server version command failed"):
            state.ns["_ensure_redis"](binary)

    def test_start_command_failure_propagates(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, start_fail={"valkey-server"})
        binary = tmp_path / "valkey-server"
        binary.write_text("", encoding="utf-8")
        with pytest.raises(RuntimeError, match="command failed"):
            state.ns["_ensure_redis"](binary)
        assert not state.redis_started

    def test_none_binary_fails_closed(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch)
        with pytest.raises(RuntimeError, match="no Redis-compatible server binary"):
            state.ns["_ensure_redis"](None)


class TestFullCellEndToEnd:
    """Gate J: the whole cell runs green with PG lifecycle + Redis fallback."""

    def test_pg_lifecycle_and_redis_fallback_green(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = _exec_cell(
            tmp_path, monkeypatch,
            euid=0, postgres_user=True,
            pg_port_open=False,
            pg_bindir=_make_bindir(tmp_path),
            apt_available={"redis-server"},
        )
        assert _user_of(state, "initdb") == ["postgres"]
        assert _user_of(state, "pg_ctl") == ["postgres"]
        assert state.pg_started and state.redis_started
        out = capsys.readouterr().out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out
        assert "implementation=redis-server" in out
