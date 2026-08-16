"""PILOT-EXEC-01: repository environment provisioning closure.

Strong test matrix for ``scripts/pilot_kaggle_repo_envs.py``
(``_workspace/active/PILOT-EXEC-01-KAGGLE-ENV-PROVISIONING-CLOSURE/``):

- Gate B: exact observed ``ensurepip`` regression is impossible (venv always
  created with ``--without-pip``; never ``-m ensurepip``; failing venv step
  fails closed with the command tail);
- Gate C: repository dependencies are NEVER installed into the benchmark/model
  interpreter; host pip ``--python <target>`` manages the isolated target env
  only, and the capability check fails closed when unsupported;
- Gate D: the latent identical bug in the tools/uv env is closed (uv lands in a
  dedicated no-pip venv via host pip ``--python``, never via target-env pip);
- Gate E: partial-state matrix (absent / valid+marker reuse / interpreter
  present but marker missing / marker identity or dependency-hash mismatch /
  health probe failure) and safe rebuild that removes ONLY the specific private
  env dir;
- Gate G: completion markers record schema/repo id/source tag/python major/minor
  and dependency file + SHA-256; valid envs are reused without re-running
  installs; Saleor pins Python 3.12 with ``UV_PYTHON_DOWNLOADS=never`` and
  ``uv sync --locked`` from the exact ``uv.lock``;
- Gate J: visible START/END/elapsed provisioning output; no secret values in
  the provisioning log; OS prerequisite install is one apt transaction (all
  three are mandatory) and fails once listing every missing package;
- Gate K: direct real-venv integration on the developer platform (no source
  string faking): a real ``--without-pip`` venv is created and has no pip.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
HELPER_PATH = SCRIPTS_DIR / "pilot_kaggle_repo_envs.py"

SOURCE_TAG = "v0.9.10-pilot-exec-ready"


def _load_helper() -> Any:
    spec = importlib.util.spec_from_file_location(
        "pilot_kaggle_repo_envs_test_helper",
        str(HELPER_PATH),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def helper() -> Any:
    return _load_helper()


def _touch(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _FakeRunner:
    """Deterministic ``run_command`` stand-in.

    Records every invocation (argv/cwd/env) and answers version/import probes
    from the argv so the provisioning decision logic runs without subprocesses.
    Simulates the real side-effect of ``uv venv`` (creating ``.venv/bin/python``)
    so post-sync health probes see a concrete interpreter file.
    """

    def __init__(
        self,
        helper: Any,
        *,
        fail_on: Callable[[list[str]], bool] | None = None,
    ) -> None:
        self.helper = helper
        self.calls: list[dict[str, Any]] = []
        self.fail_on = fail_on

    def __call__(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        log: Any = None,
        label: str = "",
        heartbeat: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        args = [str(a) for a in argv]
        self.calls.append(
            {
                "argv": args,
                "cwd": str(cwd) if cwd else None,
                "env": dict(env or {}),
            }
        )
        if self.fail_on is not None and self.fail_on(args):
            raise self.helper.ProvisioningError(
                f"simulated command failure: {' '.join(args)}",
                command=args,
                exit_code=1,
                tail="simulated stderr",
            )
        if len(args) >= 3 and args[1] == "-m" and "venv" in args:
            _touch(Path(args[-1]) / "bin" / "python")
        if "pip" in args and "install" in args and "--python" in args and "uv" in args:
            target = Path(args[args.index("--python") + 1])
            _touch(target.parent / "uv")
        if len(args) >= 3 and args[0].endswith("uv") and args[1] == "venv" and cwd is not None:
            _touch(Path(cwd) / ".venv" / "bin" / "python")
        if len(args) >= 3 and args[1] == "-c" and "sys.version_info" in args[2]:
            return self._result(args, self._version_for(args[0]))
        joined = " ".join(args)
        if "-c" in args and "sys.prefix == sys.base_prefix" in joined:
            return self._result(args, "1")
        if "-c" in args and "django.get_version()" in joined:
            return self._result(args, "5.0.0")
        if "-c" in args and "import cms" in joined:
            return self._result(args, "")
        if "-c" in args and "import saleor" in joined:
            # Fail-closed: the Saleor health probe must run from the working
            # copy root (pinned [tool.uv] package=false never installs the root
            # project into site-packages). Blindly succeeding without checking
            # cwd is exactly the gap that let v0.9.10 pass locally.
            if cwd is None or not (Path(cwd) / "saleor" / "__init__.py").is_file():
                raise self.helper.ProvisioningError(
                    "simulated import saleor probe ran without cwd=saleor work dir "
                    "(module only visible from the repository root)",
                    command=args,
                    exit_code=1,
                    tail="ModuleNotFoundError: No module named 'saleor'",
                )
            return self._result(args, "")
        if joined.endswith("uv --version"):
            return self._result(args, "uv 0.5.14")
        return self._result(args, "")

    @staticmethod
    def _version_for(interpreter: str) -> str:
        return "3.12.0" if "saleor" in interpreter else "3.11.5"

    @staticmethod
    def _result(args: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr="")


class TestGateBEnsurepipRegression:
    """Exact observed Kaggle failure: ``-m venv`` -> ensurepip exited 1."""

    def test_exact_observed_ensurepip_failure_is_impossible(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        env_dir = tmp_path / "djangocms"
        _touch(env_dir / "bin" / "python")
        runner = _FakeRunner(helper, fail_on=lambda argv: "venv" in argv and "--without-pip" not in argv)
        monkeypatch.setattr(helper, "run_command", runner)
        interp = helper.create_no_pip_venv(str(Path("/usr/bin/python3")), env_dir)
        assert str(interp).endswith("python")
        venv_cmds = [c["argv"] for c in runner.calls if "venv" in c["argv"] and "-m" in c["argv"]]
        assert len(venv_cmds) == 1
        assert venv_cmds[0][0] == str(Path("/usr/bin/python3"))
        assert venv_cmds[0][1:3] == ["-m", "venv"]
        assert "--without-pip" in venv_cmds[0]
        assert "--upgrade" not in venv_cmds[0]
        assert "--default-pip" not in venv_cmds[0]
        all_args = [a for c in runner.calls for a in c["argv"]]
        assert "ensurepip" not in all_args

    def test_bare_venv_old_command_shape_would_fail_closed(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper, fail_on=lambda argv: "venv" in argv)
        monkeypatch.setattr(helper, "run_command", runner)
        with pytest.raises(helper.ProvisioningError) as excinfo:
            helper.create_no_pip_venv("/usr/bin/python3", tmp_path / "djangocms")
        assert "simulated command failure" in str(excinfo.value)
        assert excinfo.value.tail is not None
        assert excinfo.value.exit_code == 1

    def test_no_pip_ever_runs_inside_the_target_env(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        env_dir = tmp_path / "djangocms"
        _touch(env_dir / "bin" / "python")
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        helper.create_no_pip_venv("/usr/bin/python3", env_dir)
        target_python = str(env_dir / "bin" / "python")
        for call in runner.calls:
            argv = call["argv"]
            if "pip" in argv:
                assert argv[0] != target_python, f"target-env pip invoked: {argv}"
                assert "--python" in argv


class TestGateCLatestNoHostEnvInstall:
    def test_dependency_install_never_targets_the_benchmark_interpreter(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        tools_env = tmp_path / "pilot_envs" / "tools"
        _touch(tools_env / "bin" / "python")
        _touch(tools_env / "bin" / "uv")
        helper.provision_uv_tool(sys.executable, tools_env, source_tag=SOURCE_TAG)
        installs = [c for c in runner.calls if "pip" in c["argv"] and "install" in c["argv"]]
        assert installs
        for call in installs:
            assert "--python" in call["argv"]
            idx = call["argv"].index("--python")
            target = Path(call["argv"][idx + 1])
            assert target.is_relative_to(tools_env)
            assert call["argv"][0] == sys.executable

    def test_host_pip_without_python_support_fails_closed(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper, fail_on=lambda argv: "pip" in argv)
        monkeypatch.setattr(helper, "run_command", runner)
        tools_env = tmp_path / "tools"
        _touch(tools_env / "bin" / "python")
        with pytest.raises(helper.ProvisioningError, match="pip --python"):
            helper.host_pip_target_ok(sys.executable, tools_env / "bin" / "python")


class TestGateDLatentToolsEnvBug:
    def test_provision_uv_tool_uses_same_no_pip_venv(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        tools_env = tmp_path / "tools"
        _touch(tools_env / "bin" / "python")
        _touch(tools_env / "bin" / "uv")
        evidence = helper.provision_uv_tool(sys.executable, tools_env, source_tag=SOURCE_TAG)
        assert evidence["reused"] is False
        venv_cmds = [c["argv"] for c in runner.calls if "venv" in c["argv"] and "-m" in c["argv"]]
        assert len(venv_cmds) == 1
        assert "--without-pip" in venv_cmds[0]
        pip_installs = [c["argv"] for c in runner.calls if "pip" in c["argv"] and "install" in c["argv"]]
        assert len(pip_installs) == 1
        assert pip_installs[0][0] == sys.executable
        assert "--python" in pip_installs[0]
        target = pip_installs[0][pip_installs[0].index("--python") + 1]
        assert target == str(tools_env / "bin" / "python")
        assert evidence["bin"] == str(tools_env / "bin" / "uv")
        assert (tools_env / ".pilot_env_ready.json").is_file()

    def test_latent_target_env_pip_command_shape_is_gone(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        tools_env = tmp_path / "tools"
        _touch(tools_env / "bin" / "python")
        _touch(tools_env / "bin" / "uv")
        helper.provision_uv_tool(sys.executable, tools_env, source_tag=SOURCE_TAG)
        target_python = str(tools_env / "bin" / "python")
        for call in runner.calls:
            argv = call["argv"]
            assert not (argv[0] == target_python and "pip" in argv), f"old buggy shape: {argv}"


class TestGateEPartialStateMatrix:
    def _expected(self, dep_sha: str = "a" * 64) -> dict[str, Any]:
        return {
            "schema": "pilot_repo_environment.v1",
            "repo_id": "djangocms",
            "source_tag": SOURCE_TAG,
            "python_major_minor": [3, 11],
            "dependency_file": "test_requirements/django-5.0.txt",
            "dependency_sha256": dep_sha,
        }

    def test_rebuild_decision_matrix(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        env_dir = tmp_path / "djangocms"
        expected = self._expected()
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "env path absent"
        _touch(env_dir / "bin" / "python")
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "completion marker missing"
        helper._write_marker(env_dir, dict(expected))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) is None
        helper._write_marker(env_dir, dict(expected, schema="pilot_repo_environment.v0"))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "marker schema mismatch"
        helper._write_marker(env_dir, dict(expected, repo_id="saleor"))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "marker repo_id mismatch"
        helper._write_marker(env_dir, dict(expected, source_tag="v0.9.8-pilot-exec-ready"))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "marker source_tag mismatch"
        helper._write_marker(env_dir, dict(expected, python_major_minor=[3, 12]))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "marker python_major_minor mismatch"
        helper._write_marker(env_dir, dict(expected, dependency_sha256="b" * 64))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "marker dependency_sha256 mismatch"
        helper._write_marker(env_dir, dict(expected))
        (env_dir / "bin" / "python").unlink()
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) == "interpreter missing"
        _touch(env_dir / "bin" / "python")
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: False) == "health probe failed"

    def test_rebuild_removes_only_the_incomplete_private_env(self, helper: Any, tmp_path: Path) -> None:
        root = tmp_path / "pilot_envs"
        target = root / "djangocms"
        sibling = root / "unrelated"
        _touch(target / "bin" / "python")
        (target / "stale.json").write_text("{}", encoding="utf-8")
        _touch(sibling / "precious.txt", "keep")
        helper._remove_private_env(target)
        assert not target.exists()
        assert sibling.is_dir()
        assert (sibling / "precious.txt").read_text(encoding="utf-8") == "keep"
        assert root.is_dir()

    def test_provision_djangocms_rebuilds_partial_and_reuses_valid(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        djangocms_root = tmp_path / "repositories" / "djangocms"
        _touch(djangocms_root / "test_requirements" / "django-5.0.txt", "# frozen\n")
        env_dir = tmp_path / "pilot_envs" / "djangocms"
        _touch(env_dir / "bin" / "python")
        uv_bin = Path("uv")
        first = helper.provision_djangocms(
            sys.executable, env_dir, djangocms_root, uv_bin=uv_bin, source_tag=SOURCE_TAG
        )
        assert first["reused"] is False
        assert first["dependency_file"] == "test_requirements/django-5.0.txt"
        assert first["django_version"] == "5.0.0"
        assert (env_dir / helper.MARKER_NAME).is_file()
        marker = helper._read_marker(env_dir)
        assert marker is not None
        assert marker["schema"] == helper.MARKER_SCHEMA
        assert marker["repo_id"] == "djangocms"
        assert marker["source_tag"] == SOURCE_TAG
        assert marker["python_major_minor"] == [3, 11]
        assert marker["dependency_file"] == "test_requirements/django-5.0.txt"
        assert len(marker["dependency_sha256"]) == 64
        uv_pip = [c for c in runner.calls if c["argv"][0] == "uv" and "pip" in c["argv"]]
        assert len(uv_pip) == 1
        req_idx = uv_pip[0]["argv"].index("-r")
        assert uv_pip[0]["argv"][req_idx + 1] == "test_requirements/django-5.0.txt"
        assert uv_pip[0]["cwd"] == str(djangocms_root)
        runner.calls.clear()
        second = helper.provision_djangocms(
            sys.executable, env_dir, djangocms_root, uv_bin=uv_bin, source_tag=SOURCE_TAG
        )
        assert second["reused"] is True
        for call in runner.calls:
            assert "venv" not in call["argv"]
            assert "pip" not in call["argv"]
            assert "uv" not in call["argv"]

    def test_provision_djangocms_missing_exact_requirements_file_fails_closed(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        djangocms_root = tmp_path / "repositories" / "djangocms"
        djangocms_root.mkdir(parents=True)
        env_dir = tmp_path / "pilot_envs" / "djangocms"
        with pytest.raises(helper.ProvisioningError, match="test_requirements/django-5.0.txt"):
            helper.provision_djangocms(
                sys.executable, env_dir, djangocms_root, uv_bin=Path("uv"), source_tag=SOURCE_TAG
            )


class TestGateGSaleorLockedEnvironment:
    def test_provision_saleor_pins_312_no_download(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_service_reachable", lambda _url, *, timeout=5.0: True)
        source = tmp_path / "repositories" / "saleor"
        _touch(source / "uv.lock", "lock")
        _touch(source / "pyproject.toml", "")
        _touch(source / "saleor" / "__init__.py", "")
        work = tmp_path / "pilot_envs" / "saleor"
        py312 = tmp_path / "python3.12"
        _touch(py312)
        evidence = helper.provision_saleor(
            work,
            source,
            uv_bin=Path("uv"),
            source_tag=SOURCE_TAG,
            python_312=py312,
        )
        assert evidence["reused"] is False
        assert evidence["python_minor"] == [3, 12]
        uv_venv = [c for c in runner.calls if c["argv"][0] == "uv" and c["argv"][1] == "venv"]
        assert len(uv_venv) == 1
        assert "--python" in uv_venv[0]["argv"]
        assert uv_venv[0]["argv"][uv_venv[0]["argv"].index("--python") + 1] == str(py312)
        uv_sync = [c for c in runner.calls if c["argv"][0] == "uv" and c["argv"][1] == "sync"]
        assert len(uv_sync) == 1
        assert "--locked" in uv_sync[0]["argv"]
        assert uv_sync[0]["cwd"] == str(work)
        for call in uv_venv + uv_sync:
            assert call["env"].get("UV_PYTHON_DOWNLOADS") == "never"
        saleor_imports = [c for c in runner.calls if c["argv"][1] == "-c" and "import saleor" in " ".join(c["argv"])]
        assert len(saleor_imports) == 1
        assert saleor_imports[0]["cwd"] == str(work)
        assert evidence["services"]["postgresql"]["reachable"] is True
        marker = helper._read_marker(work)
        assert marker is not None
        assert marker["python_major_minor"] == [3, 12]
        assert marker["dependency_file"] == "uv.lock"
        assert marker["dependency_sha256"] == helper._sha256_file(source / "uv.lock")

    def test_provision_saleor_reuses_valid_locked_env(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_service_reachable", lambda _url, *, timeout=5.0: True)
        source = tmp_path / "repositories" / "saleor"
        _touch(source / "uv.lock", "lock")
        _touch(source / "pyproject.toml", "")
        _touch(source / "saleor" / "__init__.py", "")
        work = tmp_path / "pilot_envs" / "saleor"
        py312 = tmp_path / "python3.12"
        _touch(py312)
        helper.provision_saleor(
            work, source, uv_bin=Path("uv"), source_tag=SOURCE_TAG, python_312=py312
        )
        runner.calls.clear()
        evidence = helper.provision_saleor(
            work, source, uv_bin=Path("uv"), source_tag=SOURCE_TAG, python_312=py312
        )
        assert evidence["reused"] is True
        for call in runner.calls:
            assert "venv" not in call["argv"]
            assert "sync" not in call["argv"]
            assert "uv" not in call["argv"]
        saleor_imports = [c for c in runner.calls if c["argv"][1] == "-c" and "import saleor" in " ".join(c["argv"])]
        assert len(saleor_imports) == 1
        assert saleor_imports[0]["cwd"] == str(work)

    def test_saleor_without_python_312_fails_closed(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_find_python_312", lambda: None)
        source = tmp_path / "repositories" / "saleor"
        _touch(source / "uv.lock", "lock")
        _touch(source / "pyproject.toml", "")
        _touch(source / "saleor" / "__init__.py", "")
        with pytest.raises(helper.ProvisioningError, match="refusing to silently download"):
            helper.provision_saleor(
                tmp_path / "pilot_envs" / "saleor",
                source,
                uv_bin=Path("uv"),
                source_tag=SOURCE_TAG,
            )

    def test_saleor_requires_services_fail_closed(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_service_reachable", lambda _url, *, timeout=5.0: False)
        source = tmp_path / "repositories" / "saleor"
        _touch(source / "uv.lock", "lock")
        _touch(source / "pyproject.toml", "")
        _touch(source / "saleor" / "__init__.py", "")
        py312 = tmp_path / "python3.12"
        _touch(py312)
        with pytest.raises(helper.ProvisioningError, match="PostgreSQL/Redis"):
            helper.provision_saleor(
                tmp_path / "pilot_envs" / "saleor",
                source,
                uv_bin=Path("uv"),
                source_tag=SOURCE_TAG,
                python_312=py312,
            )


class TestSaleorSourceVisibilityProbe:
    """PILOT-EXEC-01 SALEOR SOURCE VISIBILITY FIX.

    v0.9.10 failed on REAL Kaggle at ``import saleor`` (exit 1,
    ModuleNotFoundError) AFTER ``uv sync --locked`` passed, because the pinned
    Saleor ``pyproject.toml`` sets ``[tool.uv] package = false`` (uv installs
    the locked dependencies but never the root project into site-packages) and
    the new health probe ran ``<venv>/bin/python -c "import saleor"`` from an
    unrelated cwd. Saleor is a flat application repository; the frozen
    downstream preflight already runs Saleor commands with ``cwd = pristine
    staged repository root``, so the probe must test the same topology by
    running from the working copy root.
    """

    def test_real_subprocess_import_saleor_requires_repo_root_cwd(
        self, helper: Any, tmp_path: Path
    ) -> None:
        """Gate B - exact real source-visibility regression with a real Python.

        Creates ``work/saleor/__init__.py`` and proves ``import saleor`` is NOT
        discoverable from an unrelated cwd but IS discoverable with
        ``cwd=work``, then that ``_saleor_probe(..., work_dir=work)`` passes and
        fails from an unrelated cwd. This runs a real subprocess, not
        ``_FakeRunner``.
        """
        work = tmp_path / "work"
        (work / "saleor").mkdir(parents=True)
        (work / "saleor" / "__init__.py").write_text("", encoding="utf-8")
        unrelated = tmp_path / "unrelated"
        unrelated.mkdir()

        not_visible = subprocess.run(
            [sys.executable, "-c", "import saleor"],
            cwd=str(unrelated),
            capture_output=True,
            text=True,
        )
        assert not_visible.returncode != 0, (
            "import saleor must NOT resolve from an unrelated cwd "
            "(no site-packages install; package=false)"
        )
        assert "ModuleNotFoundError" in (not_visible.stderr or "")

        visible = subprocess.run(
            [sys.executable, "-c", "import saleor"],
            cwd=str(work),
            capture_output=True,
            text=True,
        )
        assert visible.returncode == 0, (
            "import saleor must resolve from the Saleor working copy root "
            f"(cwd={work}):\n{visible.stderr}"
        )

        assert helper._saleor_probe(sys.executable, work_dir=work) is True
        assert helper._saleor_probe(sys.executable, work_dir=unrelated) is False

    def test_pinned_saleor_pyproject_declares_package_false(self) -> None:
        """Gate C - the exact bundled/pinned Saleor pyproject contract.

        ``[tool.uv] package = false`` means uv deliberately does NOT install the
        root project into site-packages, which is why the health probe must
        expose the source via the repository-root cwd (as the frozen downstream
        preflight does) instead of expecting a site-packages module.
        """
        pyproject = (
            PROJECT_DIR
            / "dist"
            / "pilot-kaggle-upload"
            / "data"
            / "repositories"
            / "saleor"
            / "pyproject.toml"
        )
        if not pyproject.is_file():
            pytest.skip(
                "bundled Saleor snapshot not materialized; run the Pilot bundle builder first"
            )
        text = pyproject.read_text(encoding="utf-8")
        assert "[tool.uv]" in text
        tool_uv = text.split("[tool.uv]", 1)[1]
        next_section = re.search(r"^\s*\[", tool_uv, re.M)
        if next_section is not None:
            tool_uv = tool_uv[: next_section.start()]
        assert re.search(r"^\s*package\s*=\s*false\s*$", tool_uv, re.M), (
            "pinned Saleor pyproject must keep [tool.uv] package = false; the "
            "root project is therefore never installed into site-packages"
        )
        assert re.search(r"^\s*package\s*=\s*true\s*$", tool_uv, re.M) is None

    def test_missing_saleor_source_fails_closed_after_sync(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Gate G - a genuinely missing source package is never hidden.

        If the staged working copy has no ``saleor/`` package after copy+sync,
        the repository-root probe must FAIL and abort provisioning (fail closed).
        """
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        source = tmp_path / "repositories" / "saleor"
        _touch(source / "uv.lock", "lock")
        _touch(source / "pyproject.toml", "")
        py312 = tmp_path / "python3.12"
        _touch(py312)
        with pytest.raises(
            helper.ProvisioningError, match="Saleor health probe failed after uv sync --locked"
        ):
            helper.provision_saleor(
                tmp_path / "pilot_envs" / "saleor",
                source,
                uv_bin=Path("uv"),
                source_tag=SOURCE_TAG,
                python_312=py312,
            )
        saleor_imports = [c for c in runner.calls if c["argv"][1] == "-c" and "import saleor" in " ".join(c["argv"])]
        assert len(saleor_imports) >= 1
        for call in saleor_imports:
            assert call["cwd"] is not None

    def test_no_semantic_drift(self, helper: Any) -> None:
        """Gate I - the fix only changes probe topology, not runtime semantics."""
        source = HELPER_PATH.read_text(encoding="utf-8")
        assert "uv sync --locked" in source
        assert "UV_PYTHON_DOWNLOADS" in source
        assert 'UV_PYTHON_DOWNLOADS"] = "never"' in source
        assert "package = true" not in source
        assert "package = false" not in source.replace(
            "The pinned Saleor ``pyproject.toml`` sets ``[tool.uv] package = false``",
            "",
        )
        assert '"--editable"' not in source
        assert '"-e",' not in source
        assert "PYTHONPATH" not in source


class TestGateJProvisioningLogAndOsPrereqs:
    def test_log_records_start_end_elapsed(self, helper: Any, tmp_path: Path) -> None:
        log = helper.ProvisioningLog(tmp_path / "provision.log")
        try:
            helper.run_command([sys.executable, "-c", "pass"], log=log, label="probe")
        finally:
            log.close()
        text = (tmp_path / "provision.log").read_text(encoding="utf-8")
        assert "START probe" in text
        assert "END probe elapsed=" in text

    def test_failed_command_tail_recorded(self, helper: Any, tmp_path: Path) -> None:
        log = helper.ProvisioningLog(tmp_path / "provision.log")
        try:
            with pytest.raises(helper.ProvisioningError) as excinfo:
                helper.run_command(
                    [
                        sys.executable,
                        "-c",
                        "import sys; sys.stderr.write('root cause line\\n'); raise SystemExit(7)",
                    ],
                    log=log,
                    label="stage",
                )
        finally:
            log.close()
        assert excinfo.value.exit_code == 7
        text = (tmp_path / "provision.log").read_text(encoding="utf-8")
        assert "END stage FAILED" in text
        assert "exit=7" in text
        assert "root cause line" in text

    def test_log_never_records_secret_values(self, helper: Any, tmp_path: Path) -> None:
        assert helper._sanitize("HF_TOKEN=super-secret-token") == "HF_TOKEN=***"
        assert helper._sanitize("SECRET_KEY=ci-secret") == "SECRET_KEY=***"
        assert helper._sanitize("PGPASSWORD=hunter2") == "PGPASSWORD=***"
        log = helper.ProvisioningLog(tmp_path / "provision.log")
        try:
            with pytest.raises(helper.ProvisioningError):
                helper.run_command(
                    [
                        sys.executable,
                        "-c",
                        "import sys; print('HF_TOKEN=super-secret-token', file=sys.stderr); raise SystemExit(1)",
                    ],
                    log=log,
                    label="stage",
                )
        finally:
            log.close()
        text = (tmp_path / "provision.log").read_text(encoding="utf-8")
        assert "super-secret-token" not in text
        assert "HF_TOKEN=***" in text

    def test_os_prerequisites_absent_apt_fails_closed_listing_all(self, helper: Any, monkeypatch: Any) -> None:
        monkeypatch.setattr(helper, "_apt_get_available", lambda: False)
        monkeypatch.setattr(helper, "_probe_os_packages", lambda packages: list(packages))
        with pytest.raises(helper.ProvisioningError) as excinfo:
            helper.ensure_os_prerequisites()
        for package in ("gettext", "gcc", "libpq-dev"):
            assert package in str(excinfo.value)

    def test_os_prerequisites_are_installed_in_one_apt_transaction(
        self, helper: Any, tmp_path: Path, monkeypatch: Any
    ) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_apt_get_available", lambda: True)
        calls = {"probes": 0}

        def _probe(packages: tuple[str, ...]) -> list[str]:
            calls["probes"] += 1
            return list(packages) if calls["probes"] == 1 else []

        monkeypatch.setattr(helper, "_probe_os_packages", _probe)
        result = helper.ensure_os_prerequisites()
        assert result["installed"] is True
        assert calls["probes"] == 2
        apt_installs = [
            c["argv"]
            for c in runner.calls
            if c["argv"][0] == "apt-get" and "install" in c["argv"]
        ]
        assert len(apt_installs) == 1
        cmd = apt_installs[0]
        assert "-y" in cmd
        for package in ("gettext", "gcc", "libpq-dev"):
            assert package in cmd
        assert "valkey-server" not in cmd and "redis-server" not in cmd

    def test_os_prerequisites_already_present_skips_install(self, helper: Any, monkeypatch: Any) -> None:
        monkeypatch.setattr(helper, "_probe_os_packages", lambda packages: [])
        result = helper.ensure_os_prerequisites()
        assert result["already_present"] is True
        assert result["installed"] is False


class TestGateKDirectRealVenvIntegration:
    def test_real_no_pip_venv_created_and_has_no_pip(self, helper: Any, tmp_path: Path) -> None:
        env_dir = tmp_path / "real-env"
        interp = helper.create_no_pip_venv(sys.executable, env_dir)
        assert interp.is_file()
        version = subprocess.run(
            [str(interp), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            capture_output=True,
            text=True,
        )
        assert version.returncode == 0
        assert version.stdout.strip() == f"{sys.version_info.major}.{sys.version_info.minor}"
        isolated = subprocess.run(
            [str(interp), "-c", "import sys; print(0 if sys.prefix == sys.base_prefix else 1)"],
            capture_output=True,
            text=True,
        )
        assert isolated.stdout.strip() == "1"
        pip_probe = subprocess.run(
            [str(interp), "-m", "pip", "--version"],
            capture_output=True,
            text=True,
        )
        assert pip_probe.returncode != 0, "venv must NOT bootstrap pip (--without-pip)"

    def test_real_marker_decision_on_real_venv(self, helper: Any, tmp_path: Path) -> None:
        env_dir = tmp_path / "real-env"
        interp = helper.create_no_pip_venv(sys.executable, env_dir)
        expected = {
            "schema": helper.MARKER_SCHEMA,
            "repo_id": "djangocms",
            "source_tag": SOURCE_TAG,
            "python_major_minor": [sys.version_info.major, sys.version_info.minor],
            "dependency_file": "test_requirements/django-5.0.txt",
            "dependency_sha256": "a" * 64,
        }
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) is not None
        helper._write_marker(env_dir, dict(expected))
        assert helper._needs_rebuild(env_dir, expected, probe=lambda _i: True) is None
        changed = dict(expected, dependency_sha256="b" * 64)
        assert helper._needs_rebuild(env_dir, changed, probe=lambda _i: True) == (
            "marker dependency_sha256 mismatch"
        )
        assert str(helper._interpreter_for(env_dir)) == str(interp)


class TestEndToEndProvisioning:
    def test_provision_repository_envs_end_to_end(self, helper: Any, tmp_path: Path, monkeypatch: Any) -> None:
        runner = _FakeRunner(helper)
        monkeypatch.setattr(helper, "run_command", runner)
        monkeypatch.setattr(helper, "_service_reachable", lambda _url, *, timeout=5.0: True)
        monkeypatch.setattr(helper, "_probe_os_packages", lambda packages: [])
        py312 = tmp_path / "python3.12"
        _touch(py312)
        monkeypatch.setattr(helper, "_find_python_312", lambda: py312)
        data_repositories = tmp_path / "repositories"
        djangocms_root = data_repositories / "djangocms"
        _touch(djangocms_root / "test_requirements" / "django-5.0.txt", "# frozen\n")
        saleor_source = data_repositories / "saleor"
        _touch(saleor_source / "uv.lock", "lock")
        _touch(saleor_source / "pyproject.toml", "")
        _touch(saleor_source / "saleor" / "__init__.py", "")
        pilot_envs = tmp_path / "pilot_envs"
        _touch(pilot_envs / "tools" / "bin" / "python")
        _touch(pilot_envs / "tools" / "bin" / "uv")
        log_path = tmp_path / "provision.log"
        evidence = helper.provision_repository_envs(
            host_python=sys.executable,
            pilot_envs_root=pilot_envs,
            data_repositories_dir=data_repositories,
            source_tag=SOURCE_TAG,
            log_path=log_path,
        )
        assert set(evidence["repositories"]) == {"djangocms", "saleor"}
        assert evidence["djangocms"]["python"].startswith(str(pilot_envs / "djangocms"))
        assert evidence["saleor"]["python"].startswith(str(pilot_envs / "saleor" / ".venv"))
        assert evidence["uv"]["bin"].startswith(str(pilot_envs / "tools"))
        assert evidence["uv"]["version"]
        log_text = log_path.read_text(encoding="utf-8")
        assert "PILOT REPOSITORY ENVIRONMENT PROVISIONING" in log_text
        assert "PASSED" in log_text
