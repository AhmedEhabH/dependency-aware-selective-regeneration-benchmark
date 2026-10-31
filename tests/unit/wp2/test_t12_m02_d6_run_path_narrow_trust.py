"""T12 M02-D6 — run-path narrow git-trust admission (RED/GREEN, hermetic).

Mission: T12_M02_FAIR_F2P_PREREG_20261031, atomic task 3
(``run_arms_physical`` pre/post Linux worktree gates vs D5 narrow trust).

Demonstrated STOP-gate defect (verified live on 2026-10-31 WSL):
``/root/m19b_r3_20261024/wt_t`` — the frozen D5 baseline FULL_REFERENCE
worktree — is rejected by git 2.43 as ``dubious ownership`` UNLESS the
narrow per-invocation ``-c safe.directory=<exact path>`` override is used.
D5 wired that override into the ORCHESTRATOR PREFLIGHT only.  The run path
(``run_arms_physical`` pre/post gates AND the worker's own step-0 gate) has
NO plumbing for the operator's narrow trust, so a real pilot on this
machine would STOP with WORKTREE_GATE_FAILED with no compliant remedy.

Repaired contract (narrow, cannot weaken identity checks):
  * an operator-supplied exact Linux worktree path may be applied per arm
    ONLY when it exactly equals the arm's resolved ``wt_linux`` AND the WSL
    ``stat`` probe verified the path is a directory (ownership evidence);
  * implemented as one shared helper ``resolve_worktree_git_trust`` so the
    orchestrator pre/post gates and the worker gate behave identically;
  * never global/wildcard ``safe.directory``, never ``--global``, never
    chown, no config writes; the identity gate (tree OID == frozen, status
    AND staged-diff readable AND empty) is still fully enforced.

No live WSL/Docker/DB operations here — scripted runners only.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / rel)
    m = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


identity = _load_module("t12_m02_d3r2_identity.py", "t12_m02_d3r2_identity")
_orch = _load_module("t12_m02_d3r2_orchestrator.py", "t12_m02_d3r2_orchestrator")
_exe = _load_module("t12_m02_execute_f2p.py", "t12_m02_execute_f2p")
_adapt = _load_module("t12_m02_arm_adapter.py", "t12_m02_arm_adapter")

FROZEN_OID = "b555542a98f62636173c6c82db80d380c083f180"
NEG_OID = "65cd0b6e07e73c102ae600fea0fabea827b7fe29"


class FakeCmd:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err
        self.ok = rc == 0


class FakeRunner:
    def __init__(self, script=None):
        self.script = script or {}
        self.calls = []

    def __call__(self, argv, input_text=None, tp_timeout=60, cwd=None):
        self.calls.append((list(argv), input_text))
        for pattern, result in self.script.items():
            if isinstance(pattern, str):
                if any(pattern in a for a in argv):
                    return result(argv) if callable(result) else result
            elif callable(pattern) and pattern(argv):
                return result(argv) if callable(result) else result
        return FakeCmd(127, "", f"unscripted: {argv!r}")


def make_probe(runner):
    p = identity.PlatformProbe(runner)
    p.host_python_kind = lambda: "windows"
    p.windows_executor = lambda: True
    p.linux_path_type = lambda linux_path: {
        "path": linux_path, "probe": "wsl", "exists": True, "is_dir": True,
        "is_file": False, "returncode": 0, "stderr_tail": "",
    }
    return p


def _dubious_script(oid: str = FROZEN_OID):
    """git probes fail as 'dubious ownership' unless the argv carries the
    narrow per-invocation ``-c safe.directory=<exact path>`` override."""
    def is_trusted(argv):
        return any("safe.directory=" in a for a in argv)

    def _rev(argv):
        return (FakeCmd(0, oid + "\n", "") if is_trusted(argv)
                else FakeCmd(128, "", "fatal: detected dubious ownership in repository at '/root/…/wt_t'"))

    def _status(argv):
        return (FakeCmd(0, "", "") if is_trusted(argv)
                else FakeCmd(128, "", "fatal: detected dubious ownership in repository at '/root/…/wt_t'"))

    def _diff(argv):
        return (FakeCmd(0, "", "") if is_trusted(argv)
                else FakeCmd(129, "", "git diff usage text …"))

    return {
        "rev-parse": lambda argv: _rev(argv),
        "status": lambda argv: _status(argv),
        "diff": lambda argv: _diff(argv),
        "stat": FakeCmd(0, "root|0|0|directory|755\n", ""),
    }


WT_NEG = "/root/t12_m02_d3r2_scratch_20261028/arm_NEG/wt_t"
WT_FULL = "/root/m19b_r3_20261024/wt_t"


class TestResolveWorktreeGitTrustHelper(unittest.TestCase):
    """GREEN contract for the shared helper: operator trust is applied ONLY
    for the exact arm worktree path after a stat-verified directory."""

    def test_helper_returns_exact_path_only_when_matching_and_verified(self):
        probe = make_probe(FakeRunner({"stat": FakeCmd(0, "root|0|0|directory|755\n", "")}))
        trust = identity.resolve_worktree_git_trust(probe, WT_FULL, WT_FULL)
        self.assertEqual(trust, WT_FULL, "exact path + verified dir is admissible")

    def test_helper_wrong_operator_path_never_applied(self):
        probe = make_probe(FakeRunner({}))
        trust = identity.resolve_worktree_git_trust(probe, "/some/other/path", WT_FULL)
        self.assertIsNone(trust)

    def test_helper_absent_operator_trust_is_none(self):
        probe = make_probe(FakeRunner({}))
        self.assertIsNone(identity.resolve_worktree_git_trust(probe, None, WT_FULL))
        self.assertIsNone(identity.resolve_worktree_git_trust(probe, "", WT_FULL))

    def test_helper_unverified_path_never_applied(self):
        probe = make_probe(FakeRunner({"stat": FakeCmd(1, "", "cannot statx")}))
        trust = identity.resolve_worktree_git_trust(probe, WT_FULL, WT_FULL)
        self.assertIsNone(trust, "unverified path/ownership must not be trusted")


class TestRunArmsPhysicalNarrowTrust(unittest.TestCase):
    """GREEN: run_arms_physical forwards the operator's exact-path trust to
    the pre/post gates; a different path is never applied; identity checks
    still bind (wrong OID stays STOP even when trusted)."""

    def _matrix_for(self, arm_id: str, oid: str) -> dict:
        arm = next(a for a in _adapt.load_arms() if a["arm_id"] == arm_id)
        keys = ("arm_id", "effective_tree_oid", "scope_hash",
                "patch_sha256", "patch_bytes", "test_contract_hash")
        return {arm_id: {k: v for k, v in arm.items() if k in keys}}

    def _spawner_ok(self, pid_by_arm, d=None):
        d = d or {}

        def spawner(worker_path, witness_input, arm_dir):
            import json
            arm = json.loads(witness_input.read_text(encoding="utf-8"))["arm"]
            arm_dir = Path(arm_dir)
            arm_dir.mkdir(exist_ok=True)
            from tests.unit.wp2.test_t12_m02_d3r2_contract import _fake_receipt_dir, _witness
            (arm_dir / "witness.json").write_text(
                json.dumps(_witness(arm, pid_by_arm[arm], "2026-11-02T09:00:00.000Z",
                                    f"{arm}n" + "x" * 16, 100)), encoding="utf-8")
            st = {"status": "CONTROL_EXPECTED" if arm == "NEG" else "PASS",
                  "control_outcome": "CONTROL_EXPECTED" if arm == "NEG" else "OUTCOME_DATA"}
            (arm_dir / "worker_stage.json").write_text(json.dumps(st), encoding="utf-8")
            _fake_receipt_dir(arm_dir, arm)
            from tests.unit.wp2.test_t12_m02_d3r2_contract import _FakeProc
            return _FakeProc(pid_by_arm[arm], 0), "TEST_SPAWNER"

        return spawner

    def test_run_gates_pass_under_operator_exact_trust(self):
        probe = make_probe(FakeRunner(_dubious_script()))
        matrix = self._matrix_for("FULL_REFERENCE", FROZEN_OID)
        with tempfile.TemporaryDirectory() as td:
            res = _orch.run_arms_physical(
                out_root=Path(td) / "out", arms=["FULL_REFERENCE"], worktree=Path("frozen"),
                source_repo=Path("repo"), scope_dir=Path("scopes"),
                classification=Path("cls.json"), test_authority=Path("ta.json"),
                matrix=matrix, worktrees={"FULL_REFERENCE": WT_FULL},
                db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
                docker_events=False, deadline_utc=None,
                spawner=self._spawner_ok({"FULL_REFERENCE": 7001}), probe=probe,
                git_trust_path=WT_FULL,
            )
        self.assertEqual(res["overall"], "PASS")
        stage = res["arms"][0]
        pre = stage["stages"]["worktree_gate_pre"]
        post = stage["stages"]["worktree_gate_post"]
        self.assertTrue(pre["pass"])
        self.assertTrue(post["pass"])
        # the per-arm git probes must have carried the narrow exact override
        for g in (pre, post):
            self.assertEqual(g.get("git_trust_applied"), WT_FULL)

    def test_run_stops_without_trust_on_dubious_ownership(self):
        """No operator trust: identical probes fail -> typed STOP before any
        side effect (fail-closed)."""
        probe = make_probe(FakeRunner(_dubious_script()))
        matrix = self._matrix_for("FULL_REFERENCE", FROZEN_OID)
        with tempfile.TemporaryDirectory() as td:
            res = _orch.run_arms_physical(
                out_root=Path(td) / "out", arms=["FULL_REFERENCE"], worktree=Path("frozen"),
                source_repo=Path("repo"), scope_dir=Path("scopes"),
                classification=Path("cls.json"), test_authority=Path("ta.json"),
                matrix=matrix, worktrees={"FULL_REFERENCE": WT_FULL},
                db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
                docker_events=False, deadline_utc=None,
                spawner=self._spawner_ok({}), probe=probe,
            )
        stage = res["arms"][0]
        self.assertIn("WORKTREE_GATE_FAILED", stage.get("reason", ""))
        self.assertFalse((Path(str(res["generated_at_utc"])) if False else True) and
                          stage.get("executed", False))

    def test_run_trust_wrong_path_never_applied(self):
        """An operator trust for a DIFFERENT path must not be applied; the
        dubious-ownership gate stays a typed STOP."""
        probe = make_probe(FakeRunner(_dubious_script()))
        matrix = self._matrix_for("FULL_REFERENCE", FROZEN_OID)
        with tempfile.TemporaryDirectory() as td:
            res = _orch.run_arms_physical(
                out_root=Path(td) / "out", arms=["FULL_REFERENCE"], worktree=Path("frozen"),
                source_repo=Path("repo"), scope_dir=Path("scopes"),
                classification=Path("cls.json"), test_authority=Path("ta.json"),
                matrix=matrix, worktrees={"FULL_REFERENCE": WT_FULL},
                db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
                docker_events=False, deadline_utc=None,
                spawner=self._spawner_ok({}), probe=probe,
                git_trust_path="/some/other/path",
            )
        stage = res["arms"][0]
        self.assertIn("WORKTREE_GATE_FAILED", stage.get("reason", ""))
        pre = stage["stages"]["worktree_gate_pre"]
        self.assertIsNone(pre.get("git_trust_applied"))

    def test_run_trust_does_not_weaken_identity(self):
        """Even under exact-path trust a WRONG tree OID remaining is STOP."""
        probe = make_probe(FakeRunner(_dubious_script(oid="c" * 40)))
        matrix = self._matrix_for("FULL_REFERENCE", FROZEN_OID)
        with tempfile.TemporaryDirectory() as td:
            res = _orch.run_arms_physical(
                out_root=Path(td) / "out", arms=["FULL_REFERENCE"], worktree=Path("frozen"),
                source_repo=Path("repo"), scope_dir=Path("scopes"),
                classification=Path("cls.json"), test_authority=Path("ta.json"),
                matrix=matrix, worktrees={"FULL_REFERENCE": WT_FULL},
                db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
                docker_events=False, deadline_utc=None,
                spawner=self._spawner_ok({}), probe=probe,
                git_trust_path=WT_FULL,
            )
        stage = res["arms"][0]
        self.assertIn("WORKTREE_GATE_FAILED", stage.get("reason", ""))
        pre = stage["stages"]["worktree_gate_pre"]
        # the trust override was applied, yet a WRONG tree OID still fails
        self.assertEqual(pre.get("git_trust_applied"), WT_FULL)
        self.assertFalse(pre["pass"])
        self.assertTrue(any("WORKTREE_OID_MISMATCH" in r for r in pre["reasons"]))


class TestWorkerGateNarrowTrust(unittest.TestCase):
    """GREEN: the worker's own step-0 gate applies the exact-path trust when
    the orchestrator forwarded it in the witness input."""

    def test_worker_gate_forwards_exact_trust_from_witness(self):
        # Build a minimal worker witness carrying the operator trust.
        import json
        gate_kwargs: list[dict] = []

        def fake_gate(probe_, wt, oid, git_trust_path=None):
            gate_kwargs.append({"wt": wt, "trust": git_trust_path})
            return {"pass": False, "reasons": ["WORKTREE_GATE_FAILED_PRE:synthetic-STOP"],
                    "tree_oid": None, "tree_matches": False, "basename_ok": True,
                    "clean": False, "wt_linux": wt, "expected_tree_oid": oid}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wi = {
                "schema": _orch.WITHER_SCHEMA, "arm": "NEG", "arm_dir": str(root), "nonce": "n" * 16,
                "worktree": str(root / "frozen"), "source_repo": str(root / "repo"),
                "scopes_dir": str(root / "scopes"), "classification": str(root / "c.json"),
                "test_authority": str(root / "t.json"),
                "worktree_linux": WT_NEG, "effective_tree_oid": NEG_OID,
                "scope_hash": "s" * 64, "patch_sha256": "p" * 64, "patch_bytes": 0,
                "materializer_rel": "x.py", "execution_id": "EXE",
                "scratch_linux_base": "/results", "docker_events": False,
                "events_until_utc": None,
                "db_scan_cmd_env_digest": identity.argv_digest([""]),
                "git_trust_path": WT_NEG,
            }
            wi_path = root / "witness_input.json"
            wi_path.write_text(json.dumps(wi), encoding="utf-8")
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location(
                "t12_m02_d3r2_worker_dyn", _SCRIPTS / "t12_m02_d3r2_worker.py")
            wmod = _ilu.module_from_spec(spec)
            assert spec and spec.loader
            sys.modules["t12_m02_d3r2_worker_dyn"] = wmod
            spec.loader.exec_module(wmod)
            (root / "out").mkdir(parents=True, exist_ok=True)
            with (
                mock.patch.object(wmod._identity, "resolve_worktree_git_trust",
                                  return_value=WT_NEG),
                mock.patch.object(wmod._identity, "linux_worktree_gate",
                                  side_effect=fake_gate),
            ):
                wmod.run_arm(wi_path, root / "out")
        # the worker gate MUST have been called with the exact trust path
        self.assertEqual(len(gate_kwargs), 1)
        self.assertEqual(gate_kwargs[0]["wt"], WT_NEG)
        self.assertEqual(gate_kwargs[0]["trust"], WT_NEG)


if __name__ == "__main__":
    unittest.main()
