"""T12 M02-D6 — run-time NEG failure identity (RED/GREEN, hermetic).

Mission: T12_M02_FAIR_F2P_PREREG_20261031, atomic task 2.

Documented scientific validation gap (prereg 02_GROUND_TRUTH.md): "The
current runner code accepts any XML ``FAILURE`` for NEG.  A failing database
connection, unrelated validation exception, or wrong testcase may still look
like a 'successful' NEG control if only failure type is checked."  The
offline scorer enforces the fingerprint at SCORING time; the run-time worker
must ALSO verify, BEFORE SIP proceeds, that each of the 9 canonical NEG
JUnit XMLs (a) carries the exact frozen testcase identity for its r/f slot
and (b) contains the frozen bug-specific failure signature — otherwise the
edge-matrix mandatory outcome is ``CONTROL_INVALID`` (stop before SIP).

Frozen authority: the R7 historical NEG XMLs (M19B_R7_F2P_PILOT
20261027T082605801327Z_f32b72b6) show, for every slot:
  f0/f1: django.core.exceptions.ValidationError:{'tokenTargetUrl':['Field required.']}
  f2:    Failed: DID NOT RAISE <class 'django.core.exceptions.ValidationError'>
The common bug-specific substring present in ALL 9 slots is
``ValidationError`` (12 chars).  An unrelated traceback (e.g. an SQL
connection error) must NOT satisfy the negative control.

Repaired contract (fail-closed, never redefines control success):
  * the NEG arm REQUIRES an operator-supplied frozen failure fingerprint
    (witness ``expected_negative_failure_substring``); absence is a typed
    STOP before any side effect (``NEG_FINGERPRINT_UNCONFIGURED``);
  * each canonical NEG JUnit XML must have exactly the frozen testcase
    (classname + name of the slot's node) and exactly one ``<failure>``
    whose message/text contains the fingerprint; any mismatch =
    ``CONTROL_INVALID`` (worker stage FAIL, never CONTROL_EXPECTED).
"""

from __future__ import annotations

import importlib.util
import json
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
_worker = _load("t12_m02_d3r2_worker.py", "t12_m02_d3r2_worker")
_receipts = _load("t12_m02_receipts.py", "t12_m02_receipts")

NEG_OID = next(a for a in _adapt.load_arms() if a["arm_id"] == "NEG")["effective_tree_oid"]
FROZEN_FINGERPRINT = "django.core.exceptions.ValidationError"
NODES = _adapt.F2P_NODES  # frozen 3 nodes


def _xml(rep: int, node: int, *, body: str) -> str:
    """Native engine JUnit XML for slot r{rep}f{node} of arm NEG."""
    return f"{_exe.TID}_NEG_r{rep}_f{node}.xml", body


def _neg_body(rep: int, node: int, *, wrong_node: bool = False, fingerprint: str | None = None,
              unrelated: bool = False, error_kind: bool = False) -> str:
    """Fixture NEG JUnit body: frozen-correct by default; adversarial toggle
    flags produce RED failure modes (wrong testcase / unrelated traceback /
    ERROR element / wrong fingerprint)."""
    mod_path, testname = (NODES[(node + 1) % 3] if wrong_node else NODES[node]).split("::", 1)
    classname = mod_path.removesuffix(".py").replace("/", ".")
    if unrelated:
        msg = "psycopg2.OperationalError: connection refused (unrelated traceback)"
    elif fingerprint is not None:
        msg = fingerprint
    else:
        msg = FROZEN_FINGERPRINT + ": {'tokenTargetUrl': ['Field required.']}"
    if error_kind:
        return (
            f'<?xml version="1.0" encoding="utf-8"?><testsuite name="pytest" tests="1" errors="1" failures="0">'
            f'<testcase classname="{classname}" name="{testname}" time="0.01">'
            f'<error message="{msg}"/></testcase></testsuite>')

    return (f'<?xml version="1.0" encoding="utf-8"?><testsuite name="pytest" tests="1" failures="1" errors="0">'
            f'<testcase classname="{classname}" name="{testname}" time="0.01">'
            f'<failure message="{msg}">{msg}</failure></testcase></testsuite>')


class _FakeCompleted:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


class FakeHarness:
    def __init__(self, bodies: list[str]):
        self.bodies = bodies

    def target_manifests(self, target):
        return {}

    def lock_install_script(self, wt_linux, manifests):
        return ("echo NO_LOCKED_DEV_GROUP", "install", {"ok": True})

    def run_state_v3(self, **kw):
        raw = Path(kw["raw_junit_dir"])
        raw.mkdir(parents=True, exist_ok=True)
        names = []
        idx = 0
        for rep in range(_exe.PILOT_REPS):
            for node in range(_exe.PILOT_NODE_COUNT):
                fname, body = _xml(rep, node, body=self.bodies[idx])
                (raw / fname).write_text(body, encoding="utf-8")
                names.append(fname)
                idx += 1
        return {"db_name": "opws_m3b_7e42fc67_093142_" + "a" * 12,
                "db_cleanup": "DROPPED_AFTER_JUNIT_PARSE",
                "junit_files": names, "error": None}


class _FakeIsolated:
    def __init__(self, **kw):
        pass

    def validate(self):
        pass


def run_neg_worker(fingerprint: str | None, bodies: list[str]) -> dict:
    """Run the REAL worker.run_arm for arm NEG with injected fixtures."""
    out = Path(tempfile.mkdtemp()) / "out"
    out.mkdir(parents=True, exist_ok=True)
    cfg = {
        "schema": _worker.WORKER_SCHEMA, "arm": "NEG",
        "arm_dir": str(out / "arm_NEG"), "nonce": "n" * 32,
        "worktree": str(out), "source_repo": str(out),
        "scopes_dir": str(out), "classification": str(out / "c.json"),
        "test_authority": str(out / "t.json"),
        "worktree_linux": "/root/t12_m02_d3r2_scratch_20261028/arm_NEG/wt_t",
        "effective_tree_oid": NEG_OID, "scope_hash": "S" * 64,
        "patch_sha256": "P" * 64, "patch_bytes": 0,
        "materializer_rel": "scripts/opws_phase3b_patch_materialize.py",
        "execution_id": "M02E-D6-NEG", "scratch_linux_base": "/results",
        "docker_events": False, "events_until_utc": None,
        "git_trust_path": None,
        "expected_negative_failure_substring": fingerprint,
    }
    wi = out / "witness_input.json"
    wi.write_text(json.dumps(cfg), encoding="utf-8")

    def fake_load_frozen(worktree: Path, rel: str, name: str):
        if rel == _exe.HARNESS_REL:
            return FakeHarness(bodies)
        return type("_Iso", (), {"OpwsIsolatedRuntime": _FakeIsolated})

    def fake_subprocess_run(argv, **kw):
        if "--out-dir" in argv:
            odir = Path(argv[argv.index("--out-dir") + 1])
            odir.mkdir(parents=True, exist_ok=True)
            (odir / "record.json").write_text(json.dumps({
                "scope_hash": cfg["scope_hash"],
                "reference_patch_sha256": cfg["patch_sha256"]}), encoding="utf-8")
        return _FakeCompleted()

    with (
        mock.patch.object(_worker, "_load_frozen", side_effect=fake_load_frozen),
        mock.patch.object(_worker.subprocess, "run", side_effect=fake_subprocess_run),
        mock.patch.object(_worker._identity, "linux_worktree_gate",
                          return_value={"pass": True, "reasons": []}),
        mock.patch.object(_worker._identity, "windows_os_process_start",
                          return_value={"status": "NOT_MEASURED"}),
    ):
        stage = _worker.run_arm(wi, out, db_scan_cmd_env="true")
    return stage


def _correct_bodies() -> list[str]:
    return [_neg_body(r, n) for r in range(3) for n in range(3)]


class TestNegFingerprintConfigRequired(unittest.TestCase):
    def test_neg_without_fingerprint_stops_before_side_effects(self):
        """RED: old worker accepted any XML FAILURE for NEG.  GREEN: NEG with
        NO frozen fingerprint is a typed STOP (rejection if unavailable)."""
        stage = run_neg_worker(fingerprint=None, bodies=_correct_bodies())
        self.assertNotEqual(stage["status"], "CONTROL_EXPECTED",
                            "NEG control must NEVER pass without a frozen fingerprint")
        reason = stage.get("reason", "")
        self.assertIn("NEG_FINGERPRINT_UNCONFIGURED", reason)


class TestNegControlIdentityVerification(unittest.TestCase):
    def test_neg_correct_fingerprint_and_identity_passes_control(self):
        stage = run_neg_worker(fingerprint=FROZEN_FINGERPRINT, bodies=_correct_bodies())
        self.assertEqual(stage["status"], "CONTROL_EXPECTED")
        self.assertEqual(stage["control_outcome"], "CONTROL_EXPECTED")

    def test_neg_unrelated_traceback_is_control_invalid(self):
        """A DB-connection-style failure must NOT satisfy the negative control
        (edge-matrix TRUTH row: NEG XML FAILURE but unrelated traceback ->
        CONTROL_INVALID)."""
        bodies = [_neg_body(r, n, unrelated=True) for r in range(3) for n in range(3)]
        stage = run_neg_worker(fingerprint=FROZEN_FINGERPRINT, bodies=bodies)
        self.assertNotEqual(stage["status"], "CONTROL_EXPECTED")
        self.assertIn("CONTROL_INVALID", stage.get("reason", ""))

    def test_neg_wrong_testcase_identity_is_control_invalid(self):
        """Edge-matrix JUNIT row: wrong test name even with PASS/FAILURE XML ->
        STOP_JUNIT_IDENTITY (here CONTROL_INVALID before SIP)."""
        bodies = [_neg_body(r, n, wrong_node=True) for r in range(3) for n in range(3)]
        stage = run_neg_worker(fingerprint=FROZEN_FINGERPRINT, bodies=bodies)
        self.assertNotEqual(stage["status"], "CONTROL_EXPECTED")
        self.assertIn("CONTROL_INVALID", stage.get("reason", ""))

    def test_neg_error_kind_never_counted_as_failure(self):
        """Edge-matrix TRUTH row: NEG ERROR / infrastructure failure ->
        CONTROL_INVALID, never counted as the negative control passing."""
        bodies = [_neg_body(r, n, error_kind=True) for r in range(3) for n in range(3)]
        stage = run_neg_worker(fingerprint=FROZEN_FINGERPRINT, bodies=bodies)
        self.assertNotEqual(stage["status"], "CONTROL_EXPECTED")
        reason = stage.get("reason", "")
        self.assertTrue("CONTROL_MISMATCH" in reason or "CONTROL_INVALID" in reason,
                        "ERROR XML must never be a passing negative control; got: "
                        + reason)

    def test_neg_wrong_fingerprint_value_is_control_invalid(self):
        """A different validated string that the XML does not contain must
        fail closed (the scorer's CONTROL_INVALID check mirrored at run time)."""
        bodies = _correct_bodies()
        stage = run_neg_worker(fingerprint="AssertionError: boom", bodies=bodies)
        self.assertNotEqual(stage["status"], "CONTROL_EXPECTED")
        self.assertIn("CONTROL_INVALID", stage.get("reason", ""))


if __name__ == "__main__":
    unittest.main()
