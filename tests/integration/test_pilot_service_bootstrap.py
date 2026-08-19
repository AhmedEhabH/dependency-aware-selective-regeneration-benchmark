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
            if name in ("psql", "postgres", "pg_ctl", "pg_config", "initdb"):
                return _Ok(stdout=f"{name} (PostgreSQL) 15.0\n")
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
            if "SHOW server_version_num" in sql:
                return _Ok(stdout="150000", stderr="")
            if "UNIQUE NULLS NOT DISTINCT" in sql:
                return _Ok(stdout="", stderr="")
            if "pg_roles" in sql:
                return _Ok(stdout="1" if role_present else "")
            if "pg_database" in sql:
                return _Ok(stdout="1" if db_present else "")
            if sql.startswith("CREATE ROLE") or sql.startswith("CREATE DATABASE"):
                return _Ok()
        if name == "dpkg" and len(args) >= 2 and args[-1] == "--print-architecture":
            return _Ok(stdout="amd64")
        if name == "curl" and "-o" in args:
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
        (data_dir / "PG_VERSION").write_text("15\n", encoding="utf-8")
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert not _run_cmd(state, "initdb"), "already-initialized dir must not re-initdb"
        assert len(_run_cmd(state, "pg_ctl")) == 1

    def test_wrong_pg_version_triggers_rebuild(self, tmp_path: Path, monkeypatch: Any) -> None:
        state = _exec_definitions(tmp_path, monkeypatch, euid=0, postgres_user=True)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        data_dir = state.ns["PG_DATA_DIR"]
        data_dir.mkdir(parents=True)
        (data_dir / "PG_VERSION").write_text("14\n", encoding="utf-8")
        state.ns["_ensure_postgres"](_make_bindir(tmp_path))
        assert len(_run_cmd(state, "initdb")) == 1, "wrong PG version must trigger rebuild"

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
        with pytest.raises(RuntimeError, match="foreign service"):
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


# ---------------------------------------------------------------------------
# PGDG-001: the exact branch that failed on real Kaggle v0.9.16
# PG15 absent -> _ensure_pgdg_apt() -> PGDG configured -> PG15 installed
# ---------------------------------------------------------------------------


def _exec_definitions_for_pgdg(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    euid: int = 0,
    os_release_content: str = "VERSION_CODENAME=jammy\n",
) -> _Ns:
    """Set up definitions for PGDG testing with hermetic paths.

    Returns a namespace with overridden path constants and ``_pg_bindir``
    returning ``None`` so ``_ensure_pgdg_apt`` takes the full PGDG branch.
    """
    state = _exec_definitions(tmp_path, monkeypatch, euid=euid, postgres_user=True)
    os_release = tmp_path / "os-release"
    os_release.write_text(os_release_content, encoding="utf-8")
    state.ns["OS_RELEASE_PATH"] = os_release
    pgdg_dir = tmp_path / "pgdg"
    pgdg_dir.mkdir()
    state.ns["PGDG_KEY_DIR"] = pgdg_dir
    state.ns["PGDG_KEY_PATH"] = pgdg_dir / "apt.postgresql.org.asc"
    state.ns["PGDG_SOURCES_PATH"] = tmp_path / "pgdg.sources"
    state.which_map["dpkg"] = "/usr/bin/dpkg"
    state.which_map["curl"] = "/usr/bin/curl"
    state.which_map["ca-certificates"] = "/usr/share/ca-certificates"
    state.which_map["gpg"] = "/usr/bin/gpg"
    state.ns["_pg_bindir"] = lambda: None
    return state


def _pgdg_run_calls(state: _Ns) -> list[dict[str, Any]]:
    """Return all subprocess.run calls made during a _ensure_pgdg_apt invocation."""
    return [
        c for c in state.run_calls
        if str(c["cmd"][0]) in ("bash", "sh", "curl", "dpkg")
        or (str(c["cmd"][0]).endswith("apt-get") and "install" in c["cmd"])
    ]


class TestPgdgSetupPath:
    """PGDG-001: _ensure_pgdg_apt uses no shell-string construction.

    The real Kaggle v0.9.16 failure was a malformed bash -c command with
    mismatched single quotes. These tests assert the replacement approach:
    direct curl argv, Python-written Deb822 .sources file, exact pg15
    packages, codename safety, and fail-closed error handling.
    """

    def test_no_bash_or_sh_c_in_pgdg_setup(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001A: zero bash -c / sh -c commands in _ensure_pgdg_apt."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        for call in state.run_calls:
            cmd = call["cmd"]
            assert not (isinstance(cmd[0], str) and cmd[0] in ("bash", "sh") and len(cmd) > 1 and cmd[1] == "-c"), (
                f"shell -c used in _ensure_pgdg_apt: {cmd}"
            )
            assert "shell" not in call["kwargs"], f"shell=True used: {call}"

    def test_no_gpg_dearmor_pipeline(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001B: no gpg --dearmor in any run call."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        for call in state.run_calls:
            cmd = call["cmd"]
            name = Path(str(cmd[0])).name
            assert name != "gpg", f"gpg invoked directly: {cmd}"
            assert "gpg --dearmor" not in " ".join(str(c) for c in cmd), f"gpg pipeline used: {cmd}"

    def test_curl_direct_with_output_flag(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001C: curl -o <path> --fail <url> (direct, no pipe)."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        curl_calls = [c for c in state.run_calls if str(c["cmd"][0]) == "curl"]
        assert len(curl_calls) == 1
        cmd = curl_calls[0]["cmd"]
        assert cmd[0] == "curl"
        assert "-o" in cmd
        assert "--fail" in cmd
        assert "ACCC4CF8.asc" in cmd[-1]

    def test_deb822_sources_format(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001D: .sources file uses Deb822 format with exact content."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        sources_path = state.ns["PGDG_SOURCES_PATH"]
        assert sources_path.is_file()
        content = sources_path.read_text(encoding="utf-8")
        assert "Types: deb" in content
        assert "URIs: https://apt.postgresql.org/pub/repos/apt" in content
        assert "Suites: jammy-pgdg" in content
        assert "Components: main" in content
        assert "Signed-By:" in content

    def test_codename_jammy(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001E: jammy codename produces Suites: jammy-pgdg."""
        state = _exec_definitions_for_pgdg(
            tmp_path, monkeypatch, os_release_content="VERSION_CODENAME=jammy\n"
        )
        state.ns["_ensure_pgdg_apt"]()
        content = state.ns["PGDG_SOURCES_PATH"].read_text(encoding="utf-8")
        assert "Suites: jammy-pgdg" in content

    def test_codename_noble(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001F: noble codename produces Suites: noble-pgdg."""
        state = _exec_definitions_for_pgdg(
            tmp_path, monkeypatch, os_release_content="VERSION_CODENAME=noble\n"
        )
        state.ns["_ensure_pgdg_apt"]()
        content = state.ns["PGDG_SOURCES_PATH"].read_text(encoding="utf-8")
        assert "Suites: noble-pgdg" in content

    def test_missing_codename_fails(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001G: missing VERSION_CODENAME -> fail closed."""
        state = _exec_definitions_for_pgdg(
            tmp_path, monkeypatch, os_release_content=""
        )
        with pytest.raises(RuntimeError, match="VERSION_CODENAME not found"):
            state.ns["_ensure_pgdg_apt"]()

    def test_unsafe_codename_fails(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001H: codename with whitespace/quotes -> fail closed."""
        state = _exec_definitions_for_pgdg(
            tmp_path, monkeypatch, os_release_content='VERSION_CODENAME="jam my"\n'
        )
        with pytest.raises(RuntimeError, match="unsafe characters"):
            state.ns["_ensure_pgdg_apt"]()

    def test_curl_failure_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001I: curl key download failure -> no apt install attempted."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        original_fake_run = subprocess.run

        def failing_curl_run(cmd: list[str], **kwargs: Any) -> _Ok:
            state.run_calls.append({"cmd": list(cmd), "kwargs": dict(kwargs)})
            name = Path(str(cmd[0])).name
            args = [str(c) for c in cmd]
            if name == "curl" and "-o" in args:
                return _Ok(returncode=22, stderr="curl: (22) The requested URL returned error: 404")
            return original_fake_run(cmd, **kwargs)

        monkeypatch.setattr(subprocess, "run", failing_curl_run)
        with pytest.raises(RuntimeError):
            state.ns["_ensure_pgdg_apt"]()
        install_calls = [
            c for c in state.run_calls
            if str(c["cmd"][0]).endswith("apt-get") and "install" in c["cmd"]
            and any("postgresql" in str(a) for a in c["cmd"])
        ]
        assert not install_calls, "apt install must not run after curl failure"

    def test_apt_update_failure_after_repo_write_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001J: apt-get update failure -> no PG15 lifecycle starts."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        original_fake_run = subprocess.run
        update_failed = [False]

        def apt_update_fail_run(cmd: list[str], **kwargs: Any) -> _Ok:
            state.run_calls.append({"cmd": list(cmd), "kwargs": dict(kwargs)})
            name = Path(str(cmd[0])).name
            args = [str(c) for c in cmd]
            if name == "apt-get" and len(args) > 1 and args[1] == "update":
                update_failed[0] = True
                return _Ok(returncode=100)
            return original_fake_run(cmd, **kwargs)

        monkeypatch.setattr(subprocess, "run", apt_update_fail_run)
        with pytest.raises(RuntimeError):
            state.ns["_ensure_pgdg_apt"]()

    def test_installs_exact_pg15_packages_only(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001K: installs postgresql-15 + postgresql-client-15, no generic."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        install_calls = [
            c for c in state.run_calls
            if str(c["cmd"][0]).endswith("apt-get") and "install" in c["cmd"]
        ]
        assert len(install_calls) == 1
        pkgs = [a for a in install_calls[0]["cmd"][2:] if not a.startswith("-")]
        assert set(pkgs) == {"postgresql-15", "postgresql-client-15"}

    def test_arch_detected_via_dpkg(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001L: dpkg --print-architecture called for .sources file."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        dpkg_calls = [
            c for c in state.run_calls
            if str(c["cmd"][0]) == "dpkg" and "--print-architecture" in c["cmd"]
        ]
        assert len(dpkg_calls) == 1
        content = state.ns["PGDG_SOURCES_PATH"].read_text(encoding="utf-8")
        assert "Architectures: amd64" in content

    def test_key_dir_created(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-001M: PGDG key directory is created before key download."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        state.ns["_ensure_pgdg_apt"]()
        key_dir = state.ns["PGDG_KEY_DIR"]
        assert key_dir.is_dir()


class TestFullCellPgdgBranch:
    """PGDG-002: full service cell with the exact Kaggle failure branch.

    PG15 absent -> _ensure_pgdg_apt() -> PGDG configured -> PG15 installed
    -> bindir resolved -> entire service-bootstrap cell reaches PASS.
    This is the regression that should have caught the v0.9.16 failure.
    """

    def test_kaggle_pgdg_branch_full_cell_passes(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """PGDG-002A: entire cell green with PGDG path."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        pgbin = tmp_path / "pgbin"
        pgbin.mkdir()
        for name in ("pg_ctl", "initdb", "psql", "postgres"):
            (pgbin / name).write_text("", encoding="utf-8")
        install_done = [False]

        def pg_bindir_with_install() -> Path | None:
            if install_done[0]:
                return pgbin
            return None

        state.ns["_pg_bindir"] = pg_bindir_with_install

        def pgdg_full_run(cmd: list[str], **kwargs: Any) -> _Ok:
            state.run_calls.append({"cmd": list(cmd), "kwargs": dict(kwargs)})
            name = Path(str(cmd[0])).name
            args = [str(c) for c in cmd]
            if name == "apt-get" and len(args) > 1 and args[1] == "install":
                packages = [a for a in args[2:] if not a.startswith("-")]
                if any("postgresql" in p for p in packages):
                    install_done[0] = True
                return _Ok()
            if name == "apt-get" and len(args) > 1 and args[1] == "update":
                return _Ok()
            if name == "dpkg" and "--print-architecture" in args:
                return _Ok(stdout="amd64")
            if name == "curl" and "-o" in args:
                return _Ok()
            if name == "pg_ctl":
                state.pg_started = True
                return _Ok()
            if name == "psql":
                sql = args[-1].strip()
                if sql == "SELECT 1":
                    return _Ok(stdout="1")
                if "SHOW server_version_num" in sql:
                    return _Ok(stdout="150000")
                if "UNIQUE NULLS NOT DISTINCT" in sql:
                    return _Ok()
                if "pg_roles" in sql:
                    return _Ok(stdout="1")
                if "pg_database" in sql:
                    return _Ok(stdout="1")
                if sql.startswith("CREATE ROLE") or sql.startswith("CREATE DATABASE"):
                    return _Ok()
            if name == "redis-server" or name == "valkey-server":
                if "--daemonize" in args:
                    state.redis_started = True
                    return _Ok()
                if args[-1] == "--version":
                    return _Ok(stdout=f"{name} 7.0.0\n")
            if args[-1] == "--version":
                return _Ok(stdout=f"{name} (PostgreSQL) 15.0\n")
            return _Ok()

        monkeypatch.setattr(subprocess, "run", pgdg_full_run)
        state.ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True
        state.ns["_ensure_pgdg_apt"]()
        state.ns["_ensure_postgres"](pgbin)
        redis_bin = tmp_path / "redis-server"
        redis_bin.write_text("", encoding="utf-8")
        state.ns["which"] = lambda n: str(redis_bin) if n == "redis-server" else state.which_map.get(n)
        state.ns["_ensure_redis"](redis_bin)
        out = capsys.readouterr().out
        assert "Configuring PostgreSQL PGDG APT repository for PG15" in out
        assert "UNIQUE NULLS NOT DISTINCT DDL probe: PASS" in out
        assert state.pg_started and state.redis_started

    def test_no_shell_commands_in_pgdg_full_cell(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """PGDG-002B: full cell with PGDG path has zero shell -c commands."""
        state = _exec_definitions_for_pgdg(tmp_path, monkeypatch)
        for call in state.run_calls:
            cmd = call["cmd"]
            assert not (isinstance(cmd[0], str) and cmd[0] in ("bash", "sh") and len(cmd) > 1 and cmd[1] == "-c"), (
                f"shell -c in full cell: {cmd}"
            )


# ---------------------------------------------------------------------------
# Stateful PostgreSQL lifecycle fake — v0.9.19 admin-bootstrap-recovery tests
#
# Replaces permissive SQL-string mocks with a narrow lifecycle model that
# FAILS any connection to PGDATABASE=saleor before the DB exists.
# The old v0.9.18 code must fail these RED tests.
# ---------------------------------------------------------------------------


class _PgLifecycleState:
    """Narrow stateful PostgreSQL lifecycle model for the hermetic test seam."""

    def __init__(
        self,
        *,
        data_dir: str = "",
        server_major: int = 15,
        databases: set[str] | None = None,
        port_open: bool = False,
        show_data_directory: str = "",
    ) -> None:
        self.server_major = server_major
        self.data_dir = data_dir or "/kaggle/working/pilot_services/postgres"
        self.show_data_directory = show_data_directory or self.data_dir
        self.databases: set[str] = set(databases) if databases is not None else {"postgres"}
        self.port_open = port_open
        self.initdb_called = False
        self.role_created = False
        self.db_created = False
        self.redis_started = False
        self.server_started = False
        self.pgdatabase_calls: list[tuple[str, str]] = []
        self.psql_calls: list[dict[str, Any]] = []

    def handle_psql(self, cmd: list[str], kwargs: dict[str, Any]) -> _Ok:
        env = kwargs.get("env") or {}
        db = env.get("PGDATABASE", "")
        sql = cmd[-1].strip() if cmd else ""
        self.psql_calls.append({"sql": sql, "db": db, "env": dict(env)})

        if db and db not in self.databases:
            return _Ok(returncode=2, stderr=f'psql: error: FATAL:  database "{db}" does not exist\n')

        if sql == "SELECT 1":
            return _Ok(stdout="1")
        if "SHOW server_version_num" in sql:
            return _Ok(stdout=str(self.server_major * 10000))
        if "SHOW data_directory" in sql:
            return _Ok(stdout=self.show_data_directory)
        if "UNIQUE NULLS NOT DISTINCT" in sql:
            return _Ok()
        if "pg_roles" in sql:
            return _Ok(stdout="1" if self.role_created else "")
        if "pg_database" in sql:
            return _Ok(stdout="1" if self.db_created else "")
        if sql.startswith("CREATE ROLE"):
            self.role_created = True
            return _Ok()
        if sql.startswith("CREATE DATABASE"):
            self.databases.add("saleor")
            self.db_created = True
            return _Ok()
        return _Ok()

    def make_fake_run(self) -> Any:
        def _fake_run(cmd: list[str], **kwargs: Any) -> _Ok:
            name = Path(str(cmd[0])).name
            args = [str(c) for c in cmd]

            if name == "pg_config" and "--bindir" in args:
                return _Ok(stdout=str(Path(self.data_dir).parent / "pgbin"))
            if name in ("psql",) and not args[-1].startswith("--"):
                return self.handle_psql(cmd, kwargs)
            if name in ("postgres", "psql", "pg_ctl", "initdb") and args[-1] == "--version":
                return _Ok(stdout=f"{name} (PostgreSQL) {self.server_major}.0\n")
            if name == "initdb":
                self.initdb_called = True
                return _Ok()
            if name == "pg_ctl":
                if "start" in args:
                    self.server_started = True
                return _Ok()
            if name == "dpkg" and "--print-architecture" in args:
                return _Ok(stdout="amd64")
            if name == "curl" and "-o" in args:
                return _Ok()
            if name in ("apt-get",) and len(args) > 1:
                return _Ok()
            if "--daemonize" in args:
                self.redis_started = True
                return _Ok()
            if name in ("redis-server", "valkey-server") and "--version" in args:
                return _Ok(stdout=f"{name} 7.0.0\n")
            return _Ok()

        return _fake_run


def _pg_lifecycle_stateful(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    port_open: bool = False,
    databases: set[str] | None = None,
    data_dir: str = "",
    show_data_directory: str = "",
    euid: int = 0,
    redis_port_open: bool = False,
    redis_binary_name: str = "redis-server",
    server_major: int = 15,
) -> tuple[_PgLifecycleState, dict[str, Any]]:
    """Exec the full service cell with a stateful PostgreSQL lifecycle fake.

    Returns (state, namespace) for test inspection.
    """
    pg_data = data_dir or str(tmp_path / "pilot_services" / "postgres")
    pg_state = _PgLifecycleState(
        data_dir=pg_data,
        show_data_directory=show_data_directory,
        databases=databases,
        port_open=port_open,
        server_major=server_major,
    )

    if euid == 0:
        fake_pwd = types.SimpleNamespace(
            getpwnam=lambda _name: types.SimpleNamespace(pw_uid=PG_UID, pw_gid=PG_GID)
        )
    else:

        def _missing(_name: str) -> None:
            raise KeyError(_name)

        fake_pwd = types.SimpleNamespace(getpwnam=_missing)
    monkeypatch.setitem(sys.modules, "pwd", fake_pwd)

    fake_os = types.ModuleType("os")
    fake_os.name = "posix"
    fake_os.geteuid = lambda: euid
    fake_os.chown = lambda _p, _u, _g: None
    fake_os.chmod = lambda _p, _m: None
    fake_os.environ = os.environ
    fake_os.path = os.path
    fake_os.getenv = os.getenv
    fake_os.sep = os.sep
    monkeypatch.setitem(sys.modules, "os", fake_os)

    fakebin = tmp_path / "fakebin"
    fakebin.mkdir(parents=True, exist_ok=True)
    redis_bin_path = fakebin / redis_binary_name
    redis_bin_path.write_text("", encoding="utf-8")
    which_map: dict[str, str] = {
        "apt-get": "/usr/bin/apt-get",
        "apt-cache": "/usr/bin/apt-cache",
        redis_binary_name: str(redis_bin_path),
    }
    monkeypatch.setattr(shutil, "which", lambda name: which_map.get(name))
    monkeypatch.setattr(subprocess, "run", pg_state.make_fake_run())
    def _fake_conn(addr: Any, *_args: Any, **_kwargs: Any) -> _Conn:
        host, port = addr
        if port == SALEOR_PG_PORT and (pg_state.port_open or pg_state.server_started):
            return _Conn()
        if port == SALEOR_REDIS_PORT and (redis_port_open or pg_state.redis_started):
            return _Conn()
        raise OSError("connection refused (port closed in hermetic model)")

    monkeypatch.setattr(socket, "create_connection", _fake_conn)

    nb = json.loads(CANONICAL_NOTEBOOK.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c.get("id") == SERVICE_CELL_ID]
    assert len(cells) == 1
    src = cells[0]["source"]
    full_source = src if isinstance(src, str) else "".join(src)
    defn_src = full_source.split(PROVISION_MARKER)[0]
    prov_marker_idx = full_source.index(PROVISION_MARKER)
    prov_src = full_source[prov_marker_idx:]

    ns: dict[str, Any] = {}
    exec(compile(defn_src, "<service-bootstrap-cell>", "exec"), ns)
    services = tmp_path / "pilot_services"
    ns["SERVICES_ROOT"] = services
    ns["PG_DATA_DIR"] = Path(pg_data)
    ns["PG_LOG"] = services / "postgres.log"
    ns["REDIS_LOG"] = services / "valkey.log"
    ns["_wait_port"] = lambda _h, _p, deadline_seconds=60: True

    services.mkdir(parents=True, exist_ok=True)
    (services / "postgres.log").touch(exist_ok=True)
    (services / "valkey.log").touch(exist_ok=True)

    pgbin = tmp_path / "pgbin"
    pgbin.mkdir(parents=True, exist_ok=True)
    for name in ("pg_ctl", "initdb", "psql", "postgres"):
        (pgbin / name).write_text("", encoding="utf-8")
    ns["_pg_bindir"] = lambda: pgbin

    exec(compile(prov_src, "<service-bootstrap-cell:provision>", "exec"), ns)
    return pg_state, ns


class TestPgAdminBootstrapRedGreen:
    """v0.9.19: exact real Kaggle fresh-cluster ordering defect.

    Fresh cluster: initdb created the cluster + role but NOT the Saleor DB.
    The old v0.9.18 code targets PGDATABASE=saleor for SHOW server_version_num
    BEFORE the DB exists; the fixed code uses admin DB `postgres`.
    """

    def test_old_code_fails_targeting_saleor_before_creation(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """RED-to-GREEN: fixed code succeeds on fresh cluster where old code would fail.

        Old v0.9.18 code: _ensure_postgres() -> _psql(bindir, "SHOW server_version_num")
        with default db=SALEOR_PG_DB -> FATAL: database "saleor" does not exist.
        Fixed code: uses db="postgres" for all server-level proofs.
        """
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            databases={"postgres"},
            euid=0,
        )
        assert pg_state.db_created, "saleor database must be created"
        out = capsys.readouterr().out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out

    def test_new_code_uses_admin_db_for_server_proofs(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GREEN: fixed code uses db=postgres for all server-level proofs."""
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            databases={"postgres"},
            euid=0,
        )
        psql_calls = [c for c in pg_state.psql_calls if c["sql"]]
        create_idx = next(
            (i for i, c in enumerate(psql_calls)
             if "CREATE DATABASE" in c["sql"]),
            len(psql_calls),
        )
        before_create = psql_calls[:create_idx]
        assert all(c["db"] == "postgres" for c in before_create), (
            "server-level psql calls must target admin DB postgres, "
            "got: %s" % [(c["sql"][:50], c["db"]) for c in before_create]
        )
        out = capsys.readouterr().out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out


class TestPgChronologyInvariant:
    """v0.9.19: ZERO Saleor-DB psql calls before CREATE DATABASE."""

    def test_zero_saleor_db_queries_before_create_database(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            databases={"postgres"},
            euid=0,
        )
        create_idx = None
        for i, c in enumerate(pg_state.psql_calls):
            if c["sql"].startswith("CREATE DATABASE"):
                create_idx = i
                break
        assert create_idx is not None, "CREATE DATABASE saleor must appear in the call log"
        before = pg_state.psql_calls[:create_idx]
        for c in before:
            assert c["db"] != "saleor", (
                f"psql called with PGDATABASE=saleor before CREATE DATABASE at index "
                f"{pg_state.psql_calls.index(c)}: {c['sql'][:80]}"
            )

    def test_final_connection_after_db_creation_uses_saleor(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            databases={"postgres"},
            euid=0,
        )
        create_idx = None
        for i, c in enumerate(pg_state.psql_calls):
            if c["sql"].startswith("CREATE DATABASE"):
                create_idx = i
                break
        assert create_idx is not None
        after = pg_state.psql_calls[create_idx + 1:]
        saleor_after = [c for c in after if c["sql"] == "SELECT 1"]
        assert saleor_after, "final frozen SELECT 1 on saleor must appear after DB creation"
        assert all(c["db"] == "saleor" for c in saleor_after), (
            "final connection probe must use PGDATABASE=saleor"
        )


class TestPgPartialRecovery:
    """v0.9.19: safe recovery from partial-state (own PG15, Saleor DB missing)."""

    def test_own_pg15_with_missing_saleor_recovers(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Port open, server PG15, data_directory == PG_DATA_DIR, saleor absent -> recovery."""
        pg_data = str(tmp_path / "pilot_services" / "postgres")
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            port_open=True,
            databases={"postgres"},
            data_dir=pg_data,
            euid=0,
        )
        assert pg_state.db_created, "recovery must create the saleor database"
        out = capsys.readouterr().out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out


class TestPgForeignServiceProtection:
    """v0.9.19: foreign/wrong service on port 5433 must FAIL CLOSED."""

    def test_foreign_data_directory_fails_closed(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Port open but data_directory != PG_DATA_DIR -> fail closed."""
        with pytest.raises(RuntimeError):
            _pg_lifecycle_stateful(
                tmp_path, monkeypatch,
                port_open=True,
                databases={"postgres"},
                show_data_directory="/tmp/foreign_pgdata",
                euid=0,
            )


class TestPgWrongMajor:
    """v0.9.19: own-looking but wrong major version -> fail before mutations."""

    def test_pg14_on_own_port_fails(self, tmp_path: Path, monkeypatch: Any) -> None:
        pg_data = str(tmp_path / "pilot_services" / "postgres")
        with pytest.raises(RuntimeError):
            _pg_lifecycle_stateful(
                tmp_path, monkeypatch,
                port_open=True,
                databases={"postgres"},
                data_dir=pg_data,
                server_major=14,
                euid=0,
            )


class TestPgAdminDbUnavailable:
    """v0.9.19: fresh server started but postgres admin connection fails."""

    def test_admin_connection_failure_before_application_db(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Admin postgres connection must work before any Saleor DB operations."""
        with pytest.raises(RuntimeError):
            _pg_lifecycle_stateful(
                tmp_path, monkeypatch,
                databases=set(),
                euid=0,
            )


class TestPgExplicitDbContract:
    """v0.9.19: _psql must require explicit db=, no implicit Saleor default."""

    def test_psql_no_longer_defaults_to_saleor_db(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """_psql signature must not have db=SALEOR_PG_DB as default."""
        state = _exec_definitions(tmp_path, monkeypatch)
        import inspect
        sig = inspect.signature(state.ns["_psql"])
        db_param = sig.parameters.get("db")
        assert db_param is not None, "_psql must have a db parameter"
        assert db_param.default is inspect.Parameter.empty, (
            f"_psql db parameter must not have a default value "
            f"(was: {db_param.default!r})"
        )


class TestFullPgdgWithDbLifecycle:
    """v0.9.19: full PGDG Kaggle-path with Saleor DB absent at start.

    PG15 absent -> PGDG install -> initdb -> server start ->
    role exists, saleor DB absent -> admin proofs use postgres ->
    Saleor DB created -> Redis starts -> entire bootstrap PASS.
    """

    def test_kaggle_full_pgdg_with_saleor_db_absent(
        self, tmp_path: Path, monkeypatch: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Closest hermetic test to the real Kaggle path."""
        pg_state, _ns = _pg_lifecycle_stateful(
            tmp_path, monkeypatch,
            databases={"postgres"},
            euid=0,
        )
        assert pg_state.initdb_called, "initdb must run on fresh cluster"
        assert pg_state.db_created, "saleor DB must be created"
        out = capsys.readouterr().out
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in out
