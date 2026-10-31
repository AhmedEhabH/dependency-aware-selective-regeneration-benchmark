"""T12 M02-D5 — RED/GREEN admission-contract repair tests (offline; test
doubles only, never WSL/Docker/DB/the engine).

Two verified execution-admission defects are proven RED first and repaired to
GREEN:

Defect A — Worktrees JSON contract
----------------------------------
``scripts/t12_m02_d3r2_orchestrator.py`` dry-run treats ``--worktrees-json``
as a JSON FILE PATH (via the shared execution planner), but ``run()`` used
``json.loads(args.worktrees_json)`` — i.e. INLINE JSON.  The repaired contract:
BOTH modes read an existing JSON file; run-mode additionally requires all four
pilot arms and valid per-arm absolute Linux worktree paths, and FAILS CLOSED
(typed hard stop) on missing / malformed / inconsistent inputs.  Proposed
paths are NEVER silently substituted during live execution.

Defect B — False READY preflight
--------------------------------
The recovered PREFLIGHT.json reported ``verdict = READY`` and
``hard_stops = []`` although
``platform.linux_worktree_reality[0].pass = false`` (dubious Git ownership,
unreadable Git status, unverified tree OID, unreadable staged diff).
Repaired admission logic:
  * ANY failed Linux worktree identity gate produces a typed hard STOP
    (``LINUX_WORKTREE_GATE_FAILED:...``);
  * unreadable Git status / staged diff are NEVER evidence of a clean tree
    (``clean`` is false unless status AND staged-diff were READABLE and empty,
    and the measured tree OID equals the frozen expected value);
  * a NARROW per-invocation ``git -c safe.directory=<exact path>`` override is
    applied ONLY when explicitly requested with the exact frozen path AND the
    WSL ``stat`` ownership probe verified the path dir; the identity gate
    (tree OID == frozen, readable+clean status) still must pass.  Never
    global ``safe.directory``, never wildcard, never chown, no config writes.
"""

from __future__ import annotations

import contextlib
import datetime
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
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
WORKTREES_EXAMPLE = {
    "NEG": "/root/scratch/arm_NEG/wt_t",
    "FULL_REFERENCE": "/root/m19b_r3_20261024/wt_t",
    "RM_CSS": "/root/scratch/arm_RM_CSS/wt_t",
    "SIP": "/root/scratch/arm_SIP/wt_t",
}


class FakeCmd:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err
        self.ok = rc == 0


class FakeRunner:
    """Scripted runner: substring/callable matches on raw argv."""

    def __init__(self, script=None):
        self.script = script or {}
        self.calls = []

    def __call__(self, argv, input_text=None, tp_timeout=60, cwd=None):
        self.calls.append((list(argv), input_text, tp_timeout))
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
        "path": linux_path,
        "probe": "wsl",
        "exists": True,
        "is_dir": True,
        "is_file": False,
        "returncode": 0,
        "stderr_tail": "",
    }
    p.distro_present = lambda: {"present": True}
    p.root_reachable = lambda: {"reachable": True, "uid": "0"}
    p.measure_clocks = lambda: {"status": "MEASURED", "median_skew_s": 0.01, "verdict": "PASS", "n_samples": 3}
    p.docker_preflight_reads = lambda: {
        "server_ok": True,
        "server_version": "29.1.3",
        "pinned_image": {"present": True, "id": identity.PINNED_PY312_OCI_ID},
        "pg_fixture": {"status": "running", "image_matches": True, "image": identity.PG_FIXTURE_IMAGE_ID},
        "network": {"internal": True, "driver": "bridge"},
    }
    return p


def _gate_ok_script():
    return {
        "rev-parse": FakeCmd(0, FROZEN_OID + "\n", ""),
        "status": FakeCmd(0, "", ""),
        "diff": FakeCmd(0, "", ""),
        "stat": FakeCmd(0, "root|0|0|directory|755\n", ""),
    }


def _dubious_ownership_script(**trust_results):
    """Scripted WSL runner reproducing the real frozen-machine failure: without
    a per-invocation trust override git refuses with dubious ownership; WITH
    the override the read-only probes succeed (identity still must match)."""
    trust = dict(trust_results or {})
    trust.setdefault("rev_parse", FakeCmd(0, FROZEN_OID + "\n", ""))
    trust.setdefault("status", FakeCmd(0, "", ""))
    trust.setdefault("diff", FakeCmd(0, "", ""))

    def is_trusted(argv):
        return any("safe.directory=" in a for a in argv)

    return {
        "rev-parse": lambda argv: (
            trust["rev_parse"]
            if is_trusted(argv)
            else FakeCmd(128, "", "fatal: detected dubious ownership in repository at '/root/m19b_r3_20261024/wt_t'\n")
        ),
        "status": lambda argv: (
            trust["status"]
            if is_trusted(argv)
            else FakeCmd(128, "", "fatal: detected dubious ownership in repository at '/root/m19b_r3_20261024/wt_t'\n")
        ),
        "diff": lambda argv: trust["diff"] if is_trusted(argv) else FakeCmd(129, "", "git diff usage text ..."),
        "stat": FakeCmd(0, "root|0|0|directory|755\n", ""),
        "-l": FakeCmd(0, "", ""),
        "id": FakeCmd(0, "0\n", ""),
        "date": FakeCmd(0, "0.0\n", ""),
    }


# ---------------------------------------------------------------------------
# Defect A — Worktrees JSON contract (file path in BOTH modes)
# ---------------------------------------------------------------------------
class TestWorktreesJsonContract(unittest.TestCase):
    """run() must read --worktrees-json as a JSON FILE (same contract as
    dry-run), resolve all four pilot arms, and fail closed (typed hard stop)
    on every missing/malformed/inconsistent input — never inline JSON, never
    a silently proposed path."""

    def _run_args(self, root: Path, worktrees_json_path: str | None, td: Path) -> object:
        now = datetime.datetime.now(datetime.UTC)
        start = now - datetime.timedelta(hours=1)
        end = now + datetime.timedelta(hours=4)
        auth = {
            "schema": "t12_m02_execution_authorization_v1",
            "grant": "RD9_F2P_PILOT",
            "authorized_arms": list(_orch.PILOT_ARMS),
            "exclusivity_window": {"start_utc": start.isoformat(), "end_utc": end.isoformat()},
            "max_wall_s": 3600,
            "recorded_by": "test-operator",
        }
        rd8 = {
            "schema": "t12_m02_rd8_pilot_decision_v1",
            "decision": "ADOPT_PILOT_ONLY",
            "signed_by": "test-operator",
            "signed_at_utc": now.isoformat(),
            "classification_sha256": _exe.DERIVED_CLASSIFICATION_SHA256,
            "test_authority_sha256": _exe.DERIVED_TEST_AUTHORITY_SHA256,
        }
        budget = {"benchmark_api_model_usd": 0.0, "request_count": 0}
        for name, payload in (("rd8.json", rd8), ("auth.json", auth), ("budget.json", budget)):
            (root / name).write_text(json.dumps(payload), encoding="utf-8")

        class _Args:
            pass

        args = _Args()
        args.worktree = str(root)
        args.source_repo = str(root)
        args.matrix = str(root / "matrix.csv")
        args.plan = str(root / "plan.json")
        args.scopes_dir = str(root / "scopes")
        args.classification = str(root / "cls.json")
        args.test_authority = str(root / "ta.json")
        args.worktrees_json = worktrees_json_path
        args.worker_path = None
        args.rd8_decision = str(root / "rd8.json")
        args.authorization = str(root / "auth.json")
        args.budget_json = str(root / "budget.json")
        args.wall_max_s = 120.0
        args.autorun_in_d3_flag = "NEVER_IN_D3"
        args.worktree_git_trust = None
        return args

    def _write_valid_worktrees(self, root: Path, mapping=WORKTREES_EXAMPLE) -> str:
        p = root / "worktrees.json"
        p.write_text(json.dumps(mapping), encoding="utf-8")
        return str(p)

    def test_run_resolves_worktrees_from_file_path(self):
        """RED: old run() parsed ``json.loads(args.worktrees_json)`` (INLINE
        JSON), which crashes on a file path.  GREEN: run() reads the FILE and
        forwards the resolved four-arm mapping to run_arms_physical()."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = self._run_args(root, self._write_valid_worktrees(root), root)
            captured: dict[str, object] = {}

            def spy_run_arms_physical(**kwargs):
                captured["worktrees"] = kwargs.get("worktrees")
                return {
                    "schema": _orch.ORCH_SCHEMA_RUN,
                    "mode": "RUN",
                    "overall": "PASS",
                    "arms": [],
                    "generated_at_utc": "2026-10-31T00:00:00Z",
                }

            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical", side_effect=spy_run_arms_physical),
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        self.assertEqual(
            captured.get("worktrees"),
            WORKTREES_EXAMPLE,
            "run() must resolve the mapping from the FILE, never crash with an inline-parse of the path string",
        )
        self.assertTrue(str(res.get("outcome", "")).startswith("STOP") is False or res.get("overall") == "PASS")

    def test_run_missing_worktrees_file_fails_closed(self):
        """RED: old run() aborts with an uncaught JSONDecodeError.  GREEN:
        a typed hard stop, and run_arms_physical is NEVER called."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = self._run_args(root, str(root / "no_such_worktrees.json"), root)
            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical") as rap,
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        rap.assert_not_called()
        self.assertIn(
            "WORKTREES_JSON_FILE_MISSING", " ".join(res["hard_stops"]), "missing file must be a typed hard stop"
        )
        self.assertNotEqual([s for s in res["hard_stops"] if s.startswith("WORKTREES_JSON")], [])

    def test_run_malformed_worktrees_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = root / "worktrees.json"
            bad.write_text("{not json!!", encoding="utf-8")
            args = self._run_args(root, str(bad), root)
            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical") as rap,
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        rap.assert_not_called()
        self.assertTrue(any(s.startswith("WORKTREES_JSON_MALFORMED") for s in res["hard_stops"]))

    def test_run_missing_arm_in_worktrees_file_fails_closed(self):
        mapping = dict(WORKTREES_EXAMPLE)
        del mapping["SIP"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = self._run_args(root, self._write_valid_worktrees(root, mapping), root)
            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical") as rap,
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        rap.assert_not_called()
        self.assertTrue(any(s.startswith("WORKTREES_MISSING_ARMS") for s in res["hard_stops"]))

    def test_run_invalid_path_value_fails_closed(self):
        mapping = dict(WORKTREES_EXAMPLE)
        mapping["SIP"] = r"C:\windows\path\wt_t"  # not a Linux absolute path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = self._run_args(root, self._write_valid_worktrees(root, mapping), root)
            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical") as rap,
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        rap.assert_not_called()
        self.assertTrue(any(s.startswith("WORKTREES_PATH_INVALID") for s in res["hard_stops"]))

    def test_run_duplicate_worktree_path_fails_closed(self):
        mapping = dict(WORKTREES_EXAMPLE)
        mapping["SIP"] = mapping["NEG"]  # shared path -> no per-arm isolation
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = self._run_args(root, self._write_valid_worktrees(root, mapping), root)
            with (
                mock.patch.object(_orch, "matrix_pins", return_value={}),
                mock.patch.object(_orch, "run_arms_physical") as rap,
                mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}),
            ):
                res = _orch.run(args, root / "out")
        rap.assert_not_called()
        self.assertTrue(any(s.startswith("WORKTREES_DUPLICATE_PATHS") for s in res["hard_stops"]))


# ---------------------------------------------------------------------------
# Defect B — False READY preflight (failed worktree gate -> typed hard STOP)
# ---------------------------------------------------------------------------
class TestWorktreeGateCleanEvidence(unittest.TestCase):
    """Unreadable Git status / staged diff must NEVER be recorded as proof of
    a clean tree, and the tree OID must be measured and match the frozen value.

    These tests exercise the REAL ``linux_worktree_gate`` with scripted WSL
    runners reproducing the recovered PREFLIGHT failure mode (dubious
    ownership, unverifiable OID, unreadable status and staged diff)."""

    def test_unreadable_status_never_treated_as_clean(self):
        """RED: the gate reported ``clean: true`` although status was
        UNREADABLE (the recovered PREFLIGHT shows exactly this).  GREEN:
        clean is false whenever any git evidence could not be read."""
        probe = make_probe(FakeRunner(_dubious_ownership_script()))
        gate = identity.linux_worktree_gate(probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID)
        self.assertFalse(gate["pass"])
        self.assertTrue(any("WORKTREE_STATUS_UNREADABLE" in r for r in gate["reasons"]))
        self.assertFalse(gate["clean"], "unreadable status must NEVER prove a clean tree")

    def test_unreadable_staged_diff_never_treated_as_clean(self):
        probe = make_probe(FakeRunner(_dubious_ownership_script()))
        gate = identity.linux_worktree_gate(probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID)
        self.assertTrue(any("WORKTREE_STAGED_DIFF_UNREADABLE" in r for r in gate["reasons"]))
        self.assertFalse(gate["clean"], "unreadable staged diff must NEVER prove a clean tree")

    def test_tree_oid_must_be_measured_and_match(self):
        probe = make_probe(FakeRunner(_dubious_ownership_script()))
        gate = identity.linux_worktree_gate(probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID)
        self.assertIsNone(gate["tree_oid"])
        self.assertFalse(gate["tree_matches"])
        self.assertTrue(any("WORKTREE_OID_MISMATCH" in r for r in gate["reasons"]))
        # with WRONG frozen expectation the gate must fail too
        wrong = identity.linux_worktree_gate(
            make_probe(FakeRunner(_gate_ok_script())), "/root/m19b_r3_20261024/wt_t", "c" * 40
        )
        self.assertFalse(wrong["pass"])

    def test_match_without_dubious_ownership_gate_passes(self):
        probe = make_probe(FakeRunner(_gate_ok_script()))
        gate = identity.linux_worktree_gate(probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID)
        self.assertTrue(gate["pass"])
        self.assertTrue(gate["clean"])
        self.assertEqual(gate["tree_oid"], FROZEN_OID)


class TestWorktreeOwnershipProbe(unittest.TestCase):
    def test_stat_probe_typed_bools_and_owner(self):
        probe = make_probe(FakeRunner({"stat": FakeCmd(0, "root|0|0|directory|755\n", "")}))
        own = identity.linux_worktree_ownership(probe, "/root/m19b_r3_20261024/wt_t")
        self.assertIs(own["stat_ok"], True, "stat_ok must be a bool, not a string")
        self.assertIs(own["is_dir"], True)
        self.assertEqual(own["owner"], "root")
        self.assertEqual(own["uid"], "0")
        self.assertEqual(own["mode"], "755")

    def test_stat_probe_failure_is_false(self):
        probe = make_probe(FakeRunner({"stat": FakeCmd(1, "", "cannot statx")}))
        own = identity.linux_worktree_ownership(probe, "/root/m19b_r3_20261024/wt_t")
        self.assertIs(own["stat_ok"], False)
        self.assertIs(own["is_dir"], False)


class TestNarrowGitTrustOverride(unittest.TestCase):
    """D5 remediation evidence: a narrowly scoped per-invocation
    ``git -c safe.directory=<exact path>`` override may be used ONLY to let
    the read-only git probes run; the identity gate still requires the
    measured tree OID to match the frozen value and a readable, empty status
    and staged diff.  Never global, never wildcard, no config writes."""

    def test_trust_override_reads_verified_identity(self):
        probe = make_probe(FakeRunner(_dubious_ownership_script()))
        gate = identity.linux_worktree_gate(
            probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID, git_trust_path="/root/m19b_r3_20261024/wt_t"
        )
        self.assertTrue(gate["pass"], "verified identity under narrow trust must pass")
        self.assertEqual(gate["tree_oid"], FROZEN_OID)
        self.assertTrue(gate["clean"])

    def test_trust_override_exact_path_only(self):
        runner = FakeRunner(_dubious_ownership_script())
        probe = make_probe(runner)
        identity.linux_worktree_gate(
            probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID, git_trust_path="/root/m19b_r3_20261024/wt_t"
        )
        # every argv actually issued to the runner (recording happens first)
        trust_argv = [c[0] for c in runner.calls if any(x == "git" or isinstance(x, str) and "-C" in x for x in c[0])]
        self.assertTrue(trust_argv, "git probes must have been issued")
        for argv in trust_argv:
            joined = " ".join(argv)
            self.assertIn("safe.directory=/root/m19b_r3_20261024/wt_t", joined)
            self.assertNotIn("--global", joined)
            self.assertNotIn("safe.directory=*", joined)

    def test_trust_override_does_not_weaken_identity(self):
        script = _dubious_ownership_script(rev_parse=FakeCmd(0, "c" * 40 + "\n", ""))  # WRONG tree OID
        probe = make_probe(FakeRunner(script))
        gate = identity.linux_worktree_gate(
            probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID, git_trust_path="/root/m19b_r3_20261024/wt_t"
        )
        self.assertFalse(gate["pass"], "wrong tree OID stays STOP even under trust")
        self.assertTrue(any("WORKTREE_OID_MISMATCH" in r for r in gate["reasons"]))

    def test_trust_override_dirty_tree_stays_stop(self):
        script = _dubious_ownership_script(status=FakeCmd(0, " M saleor/app/x.py\n", ""))
        probe = make_probe(FakeRunner(script))
        gate = identity.linux_worktree_gate(
            probe, "/root/m19b_r3_20261024/wt_t", FROZEN_OID, git_trust_path="/root/m19b_r3_20261024/wt_t"
        )
        self.assertFalse(gate["pass"])
        self.assertTrue(any("WORKTREE_NOT_CLEAN" in r for r in gate["reasons"]))


class TestPreflightAdmission(unittest.TestCase):
    """preflight() must NEVER return READY while a Linux worktree identity gate
    failed; the typed hard stop is LINUX_WORKTREE_GATE_FAILED.  The narrow
    per-invocation trust override is applied only after the exact path and its
    WSL ownership were verified."""

    def _preflight_args(self, root: Path, *, git_trust=None) -> object:
        class _Args:
            pass

        args = _Args()
        args.worktree = str(root)
        args.source_repo = str(root)
        args.matrix = str(root / "matrix.csv")
        args.plan = str(root / "plan.json")
        args.scopes_dir = str(root / "scopes")
        args.classification = str(root / "cls.json")
        args.test_authority = str(root / "ta.json")
        args.rd8_decision = None
        args.authorization = None
        args.worktree_git_trust = git_trust
        return args

    @contextlib.contextmanager
    def _patch_gates(self, probe):
        # NOTE: patch the module objects the ORCHESTRATOR actually holds
        # (_orch._exe / _orch._adapt / _orch._identity), because re-loading
        # the scripts here creates fresh copies in this test's namespace.
        patches = [
            mock.patch.object(
                _orch,
                "baseline",
                return_value={
                    "schema": "t12_m02_d3r2_baseline_v1",
                    "branch": "test",
                    "head": _adapt.FROZEN_WORKTREE_HEAD,
                    "recorded_at_utc": "2026-10-31T00:00:00Z",
                },
            ),
            mock.patch.object(_orch._exe, "_git", return_value=FakeCmd(0, _adapt.FROZEN_WORKTREE_HEAD + "\n", "")),
            mock.patch.object(_orch._adapt, "check_matrix_file", return_value=(True, "a" * 64)),
            mock.patch.object(_orch._exe, "_plan_ok", return_value=(True, "OK")),
            mock.patch.object(_orch._exe._driver, "engine_scripts_pin_status", return_value={}),
            mock.patch.object(_orch._identity, "PlatformProbe", return_value=probe),
            # create=True keeps the RED phase defect-faithful: the old code
            # has no ownership probe, and adding it is part of the fix.
            mock.patch.object(
                _orch._identity,
                "linux_worktree_ownership",
                create=True,
                return_value={
                    "path": identity.WORKTREE_PATTERN_LINUX,
                    "stat_ok": True,
                    "is_dir": True,
                    "owner": "root",
                    "uid": "0",
                    "gid": "0",
                    "mode": "755",
                },
            ),
        ]
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            yield

    def test_preflight_failed_gate_is_typed_hard_stop(self):
        """RED: the recovered PREFLIGHT was READY with hard_stops=[] although
        the worktree gate failed.  GREEN: verdict STOP + typed stop."""
        failing_reality = {
            "pass": False,
            "reasons": [
                "WORKTREE_OID_UNVERIFIABLE:fatal: detected dubious "
                "ownership in repository at '/root/m19b_r3_20261024/wt_t'",
                "WORKTREE_STATUS_UNREADABLE:fatal: ...",
            ],
            "tree_oid": None,
            "tree_matches": False,
            "basename_ok": True,
            "clean": False,
            "wt_linux": identity.WORKTREE_PATTERN_LINUX,
            "expected_tree_oid": FROZEN_OID,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "matrix.csv").write_text("arm_id,patch_sha256\n", encoding="utf-8")
            (root / "plan.json").write_text("{}", encoding="utf-8")
            args = self._preflight_args(root)
            probe = make_probe(FakeRunner({}))
            with (
                mock.patch.object(_orch._identity, "linux_worktree_gate", return_value=failing_reality),
                self._patch_gates(probe),
            ):
                res = _orch.preflight(args, root / "out")
        self.assertEqual(res["verdict"], "STOP", "a failed worktree identity gate must STOP, never READY")
        stops = res["hard_stops"]
        self.assertTrue(
            any(s.startswith("LINUX_WORKTREE_GATE_FAILED") for s in stops), f"typed hard stop missing; got {stops}"
        )

    def test_preflight_ready_requires_passing_gate(self):
        ok_reality = {
            "pass": True,
            "reasons": [],
            "tree_oid": FROZEN_OID,
            "tree_matches": True,
            "basename_ok": True,
            "clean": True,
            "wt_linux": identity.WORKTREE_PATTERN_LINUX,
            "expected_tree_oid": FROZEN_OID,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "matrix.csv").write_text("arm_id,patch_sha256\n", encoding="utf-8")
            (root / "plan.json").write_text("{}", encoding="utf-8")
            args = self._preflight_args(root)
            probe = make_probe(FakeRunner({}))
            with (
                mock.patch.object(_orch._identity, "linux_worktree_gate", return_value=ok_reality),
                self._patch_gates(probe),
            ):
                res = _orch.preflight(args, root / "out")
        self.assertEqual(res["verdict"], "READY")
        self.assertEqual(res["hard_stops"], [])
        reality = res["platform"]["linux_worktree_reality"][0]
        self.assertTrue(reality["pass"])
        self.assertFalse(reality["git_trust_override"]["applied"], "no override needed when the gate passes")

    def test_preflight_narrow_trust_after_verified_ownership(self):
        """With --worktree-git-trust set to the exact frozen path and a
        verified WSL ownership probe, the gate re-runs under the per-invocation
        override; READY is possible only when the identity gate then passes."""
        base_fail = {
            "pass": False,
            "reasons": [
                "WORKTREE_OID_UNVERIFIABLE:fatal: detected dubious "
                "ownership in repository at '/root/m19b_r3_20261024/wt_t'",
                "WORKTREE_STATUS_UNREADABLE:fatal: ...",
            ],
            "tree_oid": None,
            "tree_matches": False,
            "basename_ok": True,
            "clean": False,
            "wt_linux": identity.WORKTREE_PATTERN_LINUX,
            "expected_tree_oid": FROZEN_OID,
        }
        trusted_ok = {
            "pass": True,
            "reasons": [],
            "tree_oid": FROZEN_OID,
            "tree_matches": True,
            "basename_ok": True,
            "clean": True,
            "wt_linux": identity.WORKTREE_PATTERN_LINUX,
            "expected_tree_oid": FROZEN_OID,
        }
        calls: list[dict[str, object]] = []

        def fake_gate(probe_, wt, oid, git_trust_path=None):
            calls.append({"wt": wt, "trust": git_trust_path})
            return trusted_ok if git_trust_path else base_fail

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "matrix.csv").write_text("arm_id,patch_sha256\n", encoding="utf-8")
            (root / "plan.json").write_text("{}", encoding="utf-8")
            args = self._preflight_args(root, git_trust=identity.WORKTREE_PATTERN_LINUX)
            probe = make_probe(FakeRunner({}))
            with (
                mock.patch.object(_orch._identity, "linux_worktree_gate", side_effect=fake_gate),
                self._patch_gates(probe),
            ):
                res = _orch.preflight(args, root / "out")
        self.assertEqual(res["verdict"], "READY")
        # the trusted re-gate ran with the exact per-invocation path
        trusted_call = [c for c in calls if c["trust"] is not None]
        self.assertEqual(len(trusted_call), 1)
        self.assertEqual(trusted_call[0]["trust"], identity.WORKTREE_PATTERN_LINUX)
        reality = res["platform"]["linux_worktree_reality"][0]
        self.assertTrue(reality["git_trust_override"]["applied"])
        self.assertTrue(reality["git_trust_override"]["per_invocation_only"])
        self.assertFalse(reality["git_trust_override"]["global_safe_directory"])
        self.assertFalse(reality["git_trust_override"]["wildcard"])
        self.assertEqual(reality["ownership"]["owner"], "root")

    def test_preflight_trust_wrong_path_fails_closed(self):
        """A trust path that is NOT the exact frozen worktree path must never
        be applied; the failed gate stays a typed hard STOP."""
        base_fail = {
            "pass": False,
            "reasons": ["WORKTREE_STATUS_UNREADABLE:fatal: ..."],
            "tree_oid": None,
            "tree_matches": False,
            "basename_ok": True,
            "clean": False,
            "wt_linux": identity.WORKTREE_PATTERN_LINUX,
            "expected_tree_oid": FROZEN_OID,
        }
        calls: list[dict[str, object]] = []

        def fake_gate(probe_, wt, oid, git_trust_path=None):
            calls.append({"trust": git_trust_path})
            return base_fail

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "matrix.csv").write_text("arm_id,patch_sha256\n", encoding="utf-8")
            (root / "plan.json").write_text("{}", encoding="utf-8")
            args = self._preflight_args(root, git_trust="/some/other/path")
            probe = make_probe(FakeRunner({}))
            with (
                mock.patch.object(_orch._identity, "linux_worktree_gate", side_effect=fake_gate),
                self._patch_gates(probe),
            ):
                res = _orch.preflight(args, root / "out")
        self.assertEqual(res["verdict"], "STOP")
        self.assertTrue(any(s.startswith("LINUX_WORKTREE_GATE_FAILED") for s in res["hard_stops"]))
        self.assertTrue(all(c["trust"] is None for c in calls), "trust override must NOT be applied for a wrong path")


if __name__ == "__main__":
    unittest.main()
