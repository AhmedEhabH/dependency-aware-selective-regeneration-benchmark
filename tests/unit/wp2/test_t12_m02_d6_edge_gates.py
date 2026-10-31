"""T12 M02-D6 — edge-matrix STOP gates (hermetic; no live Docker/WSL).

Mission: T12_M02_FAIR_F2P_PREREG_20261031, atomic task 6.

Covers the runtime edge rows that are currently unit-untested at the
orchestrator-verdict level:

  * RUNTIME fixture stopped after external SIGINT      -> PG_FIXTURE_NOT_RUNNING typed STOP
  * RUNTIME docker daemon unreachable / pinned image    -> typed STOP
  * RUNTIME internal network missing                   -> typed STOP
  * FROZEN matrix/plan byte drift at preflight          -> typed STOP

These are read-only admission gates; the fixture is never started.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / rel)
    m = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


identity = _load("t12_m02_d3r2_identity.py", "t12_m02_d3r2_identity")
_orch = _load("t12_m02_d3r2_orchestrator.py", "t12_m02_d3r2_orchestrator")
_exe = _load("t12_m02_execute_f2p.py", "t12_m02_execute_f2p")
_adapt = _load("t12_m02_arm_adapter.py", "t12_m02_arm_adapter")


class _Args:
    worktree = "."
    source_repo = "."
    matrix = "matrix.csv"
    plan = "plan.json"
    scopes_dir = "scopes"
    classification = "cls.json"
    test_authority = "ta.json"
    rd8_decision = None
    authorization = None
    worktree_git_trust = None


class TestPreflightRuntimeStopGates(unittest.TestCase):
    def _preflight(self, *, docker: dict, matrix_ok=True, plan_ok=True,
                   root: Path | None = None):
        root = root or Path(tempfile.mkdtemp())
        (root / "matrix.csv").write_text("arm_id,patch_sha256\n", encoding="utf-8")
        (root / "plan.json").write_text("{}", encoding="utf-8")

        class P:
            def __init__(self):
                self._docker = docker

            def host_python_kind(self): return "windows"
            def windows_executor(self): return True

            def distro_present(self):
                return {"probe": "wsl -l -q", "present": True}

            def root_reachable(self):
                return {"probe": "id -u", "reachable": True, "uid": "0"}

            def measure_clocks(self):
                return {"status": "MEASURED", "median_skew_s": 0.01,
                        "verdict": "PASS", "n_samples": 3}

            def docker_preflight_reads(self):
                return self._docker

        p = P()
        args = _Args()
        args.worktree = str(root)
        args.matrix = str(root / "matrix.csv")
        args.plan = str(root / "plan.json")
        with (
            mock.patch.object(_orch._identity, "PlatformProbe", return_value=p),
            mock.patch.object(_orch._adapt, "check_matrix_file",
                              return_value=(matrix_ok, "m" * 64)),
            mock.patch.object(_orch._exe, "_plan_ok", return_value=(plan_ok, "OK")),
            mock.patch.object(_orch._exe, "validate_rd8_decision",
                              return_value={"status": "RD8_PENDING", "present": False}),
            mock.patch.object(_orch._exe, "validate_authorization",
                              return_value={"status": "NOT_AUTHORIZED", "present": False}),
            mock.patch.object(_orch._exe._driver, "engine_scripts_pin_status",
                              return_value={}),
            mock.patch.object(_orch._identity, "linux_worktree_gate",
                              return_value={"pass": True, "reasons": []}),
            mock.patch.object(_orch._identity, "linux_worktree_ownership",
                              return_value={"stat_ok": True, "is_dir": True,
                                            "owner": "root", "uid": "0"}),
            mock.patch.object(_orch, "baseline",
                              return_value={"schema": "t12_m02_d3r2_baseline_v1",
                                            "branch": "test",
                                            "head": _adapt.FROZEN_WORKTREE_HEAD,
                                            "recorded_at_utc": "2026-10-31T00:00:00Z"}),
        ):
            return _orch.preflight(args, root / "out")

    def _ok_docker(self):
        return {
            "server_ok": True, "server_version": "29.1.3",
            "pinned_image": {"present": True, "id": identity.PINNED_PY312_OCI_ID},
            "pg_fixture": {"name": identity.PG_FIXTURE, "status": "running",
                           "image_matches": True, "image": identity.PG_FIXTURE_IMAGE_ID},
            "network": {"name": identity.RUN_NETWORK, "internal": True, "driver": "bridge"},
        }

    def test_pg_fixture_stopped_is_typed_stop(self):
        """RUNTIME,PG stopped after SIGINT -> STOP_INFRASTRUCTURE (never an
        automatic restart; operator must start it in the exclusive window)."""
        docker = self._ok_docker()
        docker["pg_fixture"] = {"name": identity.PG_FIXTURE, "status": "exited",
                               "image_matches": True, "image": identity.PG_FIXTURE_IMAGE_ID}
        res = self._preflight(docker=docker)
        self.assertEqual(res["verdict"], "STOP")
        self.assertIn("PG_FIXTURE_NOT_RUNNING", res["hard_stops"])

    def test_docker_daemon_unreachable_is_typed_stop(self):
        docker = self._ok_docker()
        docker["server_ok"] = False
        res = self._preflight(docker=docker)
        self.assertEqual(res["verdict"], "STOP")
        self.assertIn("DOCKER_SERVER_UNREACHABLE", res["hard_stops"])

    def test_pinned_image_missing_is_typed_stop(self):
        docker = self._ok_docker()
        docker["pinned_image"] = {"present": False, "id": "sha256:0" * 8}
        res = self._preflight(docker=docker)
        self.assertEqual(res["verdict"], "STOP")
        self.assertIn("PINNED_IMAGE_MISSING", res["hard_stops"])

    def test_internal_network_missing_is_typed_stop(self):
        docker = self._ok_docker()
        docker["network"] = {"name": identity.RUN_NETWORK, "internal": False, "driver": "bridge"}
        res = self._preflight(docker=docker)
        self.assertEqual(res["verdict"], "STOP")
        self.assertIn("INTERNAL_NETWORK_MISSING", res["hard_stops"])

    def test_matrix_hash_drift_is_typed_stop(self):
        res = self._preflight(docker=self._ok_docker(), matrix_ok=False)
        self.assertEqual(res["verdict"], "STOP")
        self.assertTrue(any(s.startswith("MATRIX_HASH_MISMATCH") for s in res["hard_stops"]))

    def test_readonly_preflight_still_not_authorized(self):
        """Even a fully green engineering gate stays NOT_AUTHORIZED (no RD-9)."""
        res = self._preflight(docker=self._ok_docker())
        self.assertEqual(res["admission"]["status"], "NOT_AUTHORIZED")
        self.assertFalse(res["authorization_state"]["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
